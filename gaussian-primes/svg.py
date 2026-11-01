# pyright: strict
"""SVG output for trees: OKLab color ramps, bucketed stroke paths, page assembly, and
rendering to PNG through Inkscape."""

from __future__ import annotations

import subprocess
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path

Pt = tuple[int, int]
XY = tuple[float, float]
Edge = tuple[Pt, Pt]  # (parent, child)
Lab = tuple[float, float, float]


# ---------------------------------------------------------------- color


def _to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_srgb(c: float) -> float:
    c = min(max(c, 0.0), 1.0)
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_oklab(h: str) -> Lab:
    r, g, b = (_to_linear(int(h[i : i + 2], 16) / 255) for i in (1, 3, 5))
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def oklab_to_hex(lab: Lab) -> str:
    L, a, b = lab
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
           -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
           -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    return "#" + "".join(f"{round(_to_srgb(v) * 255):02x}" for v in rgb)


def ramp(stops: list[str], t: float, steps: int = 0) -> str:
    """Color at t in [0, 1] along evenly spaced stops, interpolated in OKLab. A positive
    `steps` quantizes t so that strokes share colors and the SVG stays small."""
    t = min(max(t, 0.0), 1.0)
    if steps:
        t = round(t * steps) / steps
    t *= len(stops) - 1
    i = min(int(t), len(stops) - 2)
    u = t - i
    a, b = hex_to_oklab(stops[i]), hex_to_oklab(stops[i + 1])
    return oklab_to_hex((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u,
                         a[2] + (b[2] - a[2]) * u))


# ---------------------------------------------------------------- geometry


def straight(xf: Callable[[Pt], XY]) -> Callable[[Edge], str]:
    def seg(e: Edge) -> str:
        (x1, y1), (x2, y2) = xf(e[0]), xf(e[1])
        return f"M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}"

    return seg


def smooth(parent: dict[Pt, Pt | None], xf: Callable[[Pt], XY]) -> Callable[[Edge], str]:
    """Quadratic midpoint smoothing. Edge q->p runs from mid(g, q), bends through q, and
    ends at mid(q, p); a leaf adds a straight tail to p. Siblings leave their shared
    start point at different angles, so branches split like a plant's."""
    has_child = {q for q in parent.values() if q is not None}

    def mid(a: XY, b: XY) -> XY:
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

    def seg(e: Edge) -> str:
        q, p = e
        g = parent[q]
        Q, P = xf(q), xf(p)
        S = Q if g is None else mid(xf(g), Q)
        E = mid(Q, P)
        d = f"M{S[0]:.2f} {S[1]:.2f}Q{Q[0]:.2f} {Q[1]:.2f} {E[0]:.2f} {E[1]:.2f}"
        return d if p in has_child else d + f"L{P[0]:.2f} {P[1]:.2f}"

    return seg


def strokes(edges: Iterable[Edge], seg: Callable[[Edge], str], color: Callable[[Edge], str],
            width: Callable[[Edge], float], opacity: Callable[[Edge], float] | None = None,
            width_quantum: float = 0.05) -> str:
    """One <path> per (width, color, opacity) bucket, thin first so trunks sit on top."""
    buckets: defaultdict[tuple[float, str, float], list[str]] = defaultdict(list)
    for e in edges:
        w = round(width(e) / width_quantum) * width_quantum
        op = 1.0 if opacity is None else round(opacity(e), 2)
        buckets[(w, color(e), op)].append(seg(e))
    out: list[str] = []
    for w, c, op in sorted(buckets, key=lambda k: (k[0], k[2], k[1])):
        attr = "" if op >= 1 else f' stroke-opacity="{op}"'
        out.append(f'<path d="{"".join(buckets[(w, c, op)])}" stroke="{c}" '
                   f'stroke-width="{w:.2f}"{attr}/>')
    return "\n".join(out)


# ---------------------------------------------------------------- page


def caption(text: str, x: float, y: float, size: float, color: str) -> str:
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="monospace" font-size="{size}" '
            f'fill="{color}" stroke="none" text-anchor="middle" '
            f'letter-spacing="{size * 0.08:.2f}">{text}</text>')


def page(view: tuple[float, float, float, float], body: str, bg: str,
         glow: tuple[XY, float, str] | None = None, px_width: int = 4000) -> str:
    """A complete SVG. `glow` = (center, radius, color) adds a radial background
    gradient fading from color to bg."""
    x, y, w, h = view
    defs, fill = "", bg
    if glow is not None:
        (cx, cy), r, inner = glow
        defs = (f'<radialGradient id="bg" cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{inner}"/>'
                f'<stop offset="1" stop-color="{bg}"/></radialGradient>')
        fill = "url(#bg)"
    px_h = round(px_width * h / w)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{px_width}" height="{px_h}" '
            f'viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}">\n<defs>{defs}</defs>\n'
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}"/>\n'
            f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">\n{body}\n</g>\n'
            f'</svg>\n')


def save(svg: str, path: Path, px_width: int) -> None:
    """Write the SVG, render a print PNG of the same name with Inkscape, and a 1000px
    JPEG preview under previews/ with ImageMagick for the README gallery."""
    path.write_text(svg)
    png = path.with_suffix(".png")
    subprocess.run(["inkscape", str(path), "--export-type=png", f"--export-filename={png}",
                    f"--export-width={px_width}", "--export-background-opacity=1"],
                   check=True, capture_output=True)
    preview = path.parent / "previews" / path.with_suffix(".jpg").name
    preview.parent.mkdir(exist_ok=True)
    subprocess.run(["magick", str(png), "-resize", "1000x1000", "-quality", "88",
                    str(preview)], check=True, capture_output=True)
