# pyright: strict
"""Gaussian-prime reachability: the component reachable from 1+i with bounded steps,
organized as a symmetric shortest-path (geodesic) tree."""

from __future__ import annotations

import heapq
import math
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

Pt = tuple[int, int]
Bools = npt.NDArray[np.bool_]

# The four associates of 1+i; together they are the (symmetric) root set.
ROOTS: tuple[Pt, ...] = ((1, 1), (-1, 1), (-1, -1), (1, -1))
CACHE = Path(__file__).with_name(".cache")


def sieve(n: int) -> Bools:
    s = np.ones(n + 1, dtype=np.bool_)
    s[:2] = False
    for p in range(2, math.isqrt(n) + 1):
        if s[p]:
            s[p * p :: p] = False
    return s


def is_gaussian_prime(a: int, b: int, isp: Bools) -> bool:
    """a+bi is prime iff its norm is a rational prime, or it is an associate of a
    rational prime p = 3 mod 4. `isp` must cover a*a + b*b."""
    a, b = abs(a), abs(b)
    if a == 0 or b == 0:
        n = a + b
        return bool(isp[n]) and n % 4 == 3
    return bool(isp[a * a + b * b])


@dataclass(frozen=True, slots=True)
class Tree:
    """Shortest-path tree of the component of 1+i under steps of length <= sqrt(k2)."""

    k2: int
    nodes: list[Pt]  # sorted by geodesic distance, so every parent precedes its children
    dist: dict[Pt, float]  # Euclidean geodesic distance from the nearest root
    parent: dict[Pt, Pt | None]
    size: dict[Pt, int]  # nodes in the subtree, including itself
    root: dict[Pt, Pt]  # which associate of 1+i the node descends from


def _apply(g: int, x: int, y: int) -> Pt:
    """Symmetry g in 0..7: g%4 quarter turns, then a swap of x and y if g >= 4."""
    for _ in range(g % 4):
        x, y = -y, x
    return (y, x) if g >= 4 else (x, y)


def _inverse(g: int, x: int, y: int) -> Pt:
    if g >= 4:
        x, y = y, x
    for _ in range(g % 4):
        x, y = y, -x
    return x, y


def _canon(p: Pt) -> tuple[Pt, int]:
    """Map p into the octant 0 <= y <= x and return the symmetry used."""
    for g in range(8):
        c = _apply(g, *p)
        if 0 <= c[1] <= c[0]:
            return c, g
    raise AssertionError(p)


def _steps(k2: int) -> list[tuple[int, int, float]]:
    k = math.isqrt(k2)
    return [(dx, dy, math.hypot(dx, dy)) for dx in range(-k, k + 1) for dy in range(-k, k + 1)
            if 0 < dx * dx + dy * dy <= k2]


def build(k2: int, limit: int = 1200) -> Tree:
    """Dijkstra from the four roots over Gaussian primes joined by steps <= sqrt(k2).

    Raises if the component reaches `limit` in either coordinate (it might be infinite).
    Parents are chosen in the canonical octant and mapped back, so the tree has the full
    8-fold symmetry of the Gaussian integers. Results are cached on disk."""
    cached = CACHE / f"tree-k2-{k2}.pickle"
    if cached.exists():
        tree = pickle.loads(cached.read_bytes())
        assert isinstance(tree, Tree)
        return tree
    steps = _steps(k2)
    isp = sieve(2 * (limit + math.isqrt(k2) + 1) ** 2)
    dist: dict[Pt, float] = {r: 0.0 for r in ROOTS}
    heap: list[tuple[float, Pt]] = [(0.0, r) for r in ROOTS]
    done: set[Pt] = set()
    while heap:
        d, (x, y) = heapq.heappop(heap)
        if (x, y) in done:
            continue
        done.add((x, y))
        for dx, dy, w in steps:
            q = (x + dx, y + dy)
            if q in done or d + w >= dist.get(q, math.inf) - 1e-9:
                continue
            if not is_gaussian_prime(*q, isp):
                continue
            if max(abs(q[0]), abs(q[1])) > limit:
                raise RuntimeError(f"component for k2={k2} escapes |coord| <= {limit}")
            dist[q] = d + w
            heapq.heappush(heap, (d + w, q))
    nodes = sorted(done, key=lambda p: (dist[p], p))

    def canonical_parent(c: Pt) -> Pt | None:
        if c in ROOTS:
            return None
        # among neighbours on a shortest path, prefer the shortest step, then lexicographic
        best = min((w, dx, dy) for dx, dy, w in steps
                   if (q := (c[0] + dx, c[1] + dy)) in dist and abs(dist[q] + w - dist[c]) < 1e-7)
        return (c[0] + best[1], c[1] + best[2])

    parent: dict[Pt, Pt | None] = {}
    for p in nodes:
        c, g = _canon(p)
        pc = canonical_parent(c)
        parent[p] = None if pc is None else _inverse(g, *pc)
    size = {p: 1 for p in nodes}
    for p in reversed(nodes):
        if (q := parent[p]) is not None:
            size[q] += size[p]
    root: dict[Pt, Pt] = {}
    for p in nodes:
        q = parent[p]
        root[p] = p if q is None else root[q]
    tree = Tree(k2, nodes, dist, parent, size, root)
    CACHE.mkdir(exist_ok=True)
    cached.write_bytes(pickle.dumps(tree))
    return tree


@dataclass(frozen=True, slots=True)
class Rings:
    ring: dict[Pt, int]  # index into the step bounds of the first bound that reaches the prime
    parent: dict[Pt, Pt | None]
    nodes: list[Pt]  # ring-then-distance order, parents first
    size: dict[Pt, int]


def nested(k2s: list[int]) -> Rings:
    """Growth rings: every prime takes its parent from the smallest step bound that
    reaches it, so each ring's branches need exactly that ring's longer steps."""
    trees = [build(k2) for k2 in k2s]
    ring: dict[Pt, int] = {}
    parent: dict[Pt, Pt | None] = {}
    for i, t in enumerate(trees):
        for p in t.nodes:
            if p not in ring:
                ring[p] = i
                parent[p] = t.parent[p]
    order = sorted(ring, key=lambda p: (ring[p], trees[ring[p]].dist[p], p))
    size = {p: 1 for p in order}
    for p in reversed(order):
        if (q := parent[p]) is not None:
            size[q] += size[p]
    return Rings(ring, parent, order, size)
