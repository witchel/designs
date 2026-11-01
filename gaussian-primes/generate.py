# pyright: strict
"""Generate the Gaussian-prime reachability designs (SVG + PNG) in this directory.

Usage: uv run generate.py [design ...]   (default: all designs)
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable
from pathlib import Path

import gprimes as gp
import svg

HERE = Path(__file__).parent
INK = "#08080f"  # near-black shared with the Collatz shirt
Edge = svg.Edge


def flip(p: gp.Pt) -> svg.XY:
    return (p[0], -p[1])


def rings() -> None:
    """Shirt: components for steps <= sqrt2, 2, sqrt8 nested as three growth rings."""
    r = gp.nested([2, 4, 8])
    rmax = [max(math.hypot(*p) for p in r.ring if r.ring[p] == i) for i in range(3)]
    colors = [["#fff0a8", "#ffb000"], ["#ff4f8b", "#c2105a"], ["#3d8bff", "#5a2bd6"]]
    edges = [(q, p) for p in r.nodes if (q := r.parent[p]) is not None]

    def color(e: Edge) -> str:
        i = r.ring[e[1]]
        r0 = 0 if i == 0 else rmax[i - 1] * 0.6
        return svg.ramp(colors[i], (math.hypot(*e[1]) - r0) / (rmax[i] - r0), 24)

    def width(e: Edge) -> float:
        return 0.34 + 0.17 * r.size[e[1]] ** 0.42

    body = svg.strokes(edges, svg.smooth(r.parent, flip), color, width, width_quantum=0.04)
    R = rmax[2] + 6
    body += svg.caption("a+bi prime · steps ≤ √2, 2, √8", 0, R + 3, 3.4, "#3a3550")
    page = svg.page((-R, -R, 2 * R, 2 * R + 8), body, INK, ((0, 0), R, "#1a1030"))
    svg.save(page, HERE / "rings.svg", 4000)


def moat() -> None:
    """Shirt: the sqrt8 component lit up; every prime it cannot reach is a pink dot."""
    t = gp.build(8)
    R = max(math.hypot(*p) for p in t.nodes) + 8
    n = int(R)
    isp = gp.sieve(2 * n * n + 2)
    stranded = [(a, b) for a in range(-n, n + 1) for b in range(-n, n + 1)
                if math.hypot(a, b) <= R - 1 and (a, b) not in t.dist
                and gp.is_gaussian_prime(a, b, isp)]
    dmax = max(t.dist.values())
    stops = ["#d9fbff", "#2de2e6", "#3a86ff", "#5a2bd6"]
    edges = [(q, p) for p in t.nodes if (q := t.parent[p]) is not None]

    def color(e: Edge) -> str:
        return svg.ramp(stops, (t.dist[e[1]] / dmax) ** 0.9, 32)

    def width(e: Edge) -> float:
        return 0.3 + 0.2 * t.size[e[1]] ** 0.4

    dots = [f'<circle cx="{a}" cy="{-b}" r="0.42" fill="#ff2d78" stroke="none" '
            f'fill-opacity="{0.35 + 0.45 * math.hypot(a, b) / R:.2f}"/>' for a, b in stranded]
    body = "\n".join(dots) + "\n" + svg.strokes(edges, svg.smooth(t.parent, flip), color,
                                                width, width_quantum=0.04)
    body += svg.caption("gaussian primes · steps ≤ √8", 0, R + 4, 4.2, "#3a3550")
    page = svg.page((-R, -R, 2 * R, 2 * R + 9), body, INK, ((0, 0), R, "#10142a"))
    svg.save(page, HERE / "moat.svg", 4000)


def _delta(name: str, bg: str, stops: list[str], glow: str | None, faint: float) -> None:
    """Poster: the whole sqrt10 component (249,508 primes) as a river network."""
    t = gp.build(10)
    dmax = max(t.dist.values())
    edges = [(q, p) for p in t.nodes if (q := t.parent[p]) is not None]

    def color(e: Edge) -> str:
        return svg.ramp(stops, (t.dist[e[1]] / dmax) ** 0.8, 48)

    def width(e: Edge) -> float:
        return 0.35 + 0.075 * t.size[e[1]] ** 0.55

    def opacity(e: Edge) -> float:  # fade the twigs so the trunks read first
        s = t.size[e[1]]
        return faint if s < 3 else (faint + 1) / 2 if s < 12 else 1.0

    body = svg.strokes(edges, svg.straight(flip), color, width, opacity, width_quantum=0.15)
    R = max(math.hypot(*p) for p in t.nodes) + 30
    body += svg.caption("gaussian primes reachable from 1+i in steps ≤ √10", 0, R + 22, 26,
                        svg.ramp([bg, stops[-1]], 0.55))
    page = svg.page((-R, -R, 2 * R, 2 * R + 50), body, bg,
                    None if glow is None else ((0, 0), R, glow))
    svg.save(page, HERE / f"{name}.svg", 6000)


def delta() -> None:
    _delta("delta", INK, ["#fff1c1", "#ff8a3d", "#e0115f", "#5b1a9e", "#1b2a6b"], None, 0.35)


def delta_paper() -> None:
    _delta("delta-paper", "#f2ead9", ["#e8361e", "#c1121f", "#2b2d6e", "#2f6f9f"],
           "#fbf6ea", 0.45)


def tree() -> None:
    """Portrait poster: the quarter of the sqrt10 component rooted at 1+i, growing up."""
    t = gp.build(10)
    origin = (1, 1)
    mine = [p for p in t.nodes if t.root[p] == origin]
    # The branch fans across roughly 30..135 degrees, not around 1+i's own 45 degrees:
    # aim the middle of its angular spread straight up.
    angs = sorted(math.atan2(p[1], p[0]) for p in mine if math.hypot(*p) > 150)
    lo, hi = angs[len(angs) // 200], angs[-len(angs) // 200 - 1]
    rot = math.pi / 2 - (lo + hi) / 2
    c, s = math.cos(rot), math.sin(rot)

    def xf(p: gp.Pt) -> svg.XY:
        x, y = p[0] - origin[0], p[1] - origin[1]
        return (x * c - y * s, -(x * s + y * c))

    dmax = max(t.dist[p] for p in mine)
    stops = ["#fff6d8", "#ffc300", "#00b37a", "#0a5c66", "#0d2b3e"]
    edges = [(q, p) for p in mine if (q := t.parent[p]) is not None]

    def color(e: Edge) -> str:
        return svg.ramp(stops, (t.dist[e[1]] / dmax) ** 0.85, 48)

    def width(e: Edge) -> float:
        return 0.35 + 0.085 * t.size[e[1]] ** 0.55

    def opacity(e: Edge) -> float:
        n = t.size[e[1]]
        return 0.4 if n < 3 else 0.7 if n < 12 else 1.0

    body = svg.strokes(edges, svg.smooth(t.parent, xf), color, width, opacity,
                       width_quantum=0.15)
    pts = [xf(p) for p in mine]
    pad = 40
    x0, x1 = min(p[0] for p in pts) - pad, max(p[0] for p in pts) + pad
    y0, y1 = min(p[1] for p in pts) - pad, max(p[1] for p in pts) + pad
    H = max(y1 - y0, 4 / 3 * (x1 - x0))  # 3:4 portrait, e.g. 18x24 in
    W = H * 3 / 4
    body += svg.caption("1+i · steps ≤ √10", (x0 + x1) / 2, y1 + 5, 24, "#3d4a52")
    page = svg.page(((x0 + x1 - W) / 2, (y0 + y1 - H) / 2, W, H + 30), body, INK,
                    ((0, 0), H * 0.9, "#0f2028"))
    svg.save(page, HERE / "tree.svg", 4000)


DESIGNS: dict[str, Callable[[], None]] = {
    "rings": rings, "moat": moat, "delta": delta, "delta-paper": delta_paper, "tree": tree,
}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(DESIGNS):
        print(f"{name} ...", flush=True)
        DESIGNS[name]()
