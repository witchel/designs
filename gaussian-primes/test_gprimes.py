# pyright: strict
"""Known Gaussian-moat facts and tree invariants."""

import math

import pytest

import gprimes as gp


def test_small_gaussian_primes() -> None:
    isp = gp.sieve(100)
    assert gp.is_gaussian_prime(1, 1, isp)  # norm 2
    assert gp.is_gaussian_prime(3, 0, isp)  # 3 = 3 mod 4 stays prime
    assert gp.is_gaussian_prime(0, -7, isp)
    assert not gp.is_gaussian_prime(5, 0, isp)  # 5 = (2+i)(2-i)
    assert not gp.is_gaussian_prime(2, 0, isp)  # 2 = -i(1+i)^2
    assert gp.is_gaussian_prime(2, 1, isp)


@pytest.mark.parametrize(("k2", "count"), [(2, 100), (4, 720), (8, 2996)])
def test_component_sizes(k2: int, count: int) -> None:
    assert len(gp.build(k2).nodes) == count


@pytest.mark.parametrize("k2", [2, 4, 8])
def test_tree_is_symmetric_shortest_path_tree(k2: int) -> None:
    t = gp.build(k2)
    for p in t.nodes:
        q = t.parent[p]
        if q is None:
            assert p in gp.ROOTS
            continue
        step = math.dist(p, q)
        assert step <= math.sqrt(k2) + 1e-9
        assert abs(t.dist[q] + step - t.dist[p]) < 1e-6
        # parent(h p) = h parent(p) for every symmetry h, except on a mirror axis, where a
        # prime can have two mirror-image parents and the tree must pick one
        if p[0] == 0 or p[1] == 0 or abs(p[0]) == abs(p[1]):
            continue
        for g in range(8):
            assert t.parent[gp._apply(g, *p)] == gp._apply(g, *q)  # pyright: ignore[reportPrivateUsage]
    assert sum(t.size[r] for r in gp.ROOTS) == len(t.nodes)


def test_nested_rings_cover_the_largest_component() -> None:
    r = gp.nested([2, 4, 8])
    assert len(r.nodes) == 2996
    assert sum(1 for p in r.nodes if r.ring[p] == 0) == 100
