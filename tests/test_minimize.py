
from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction
from logicsyn.ops.qm import primes
from logicsyn.ops.cover import essentials, min_cover
from logicsyn.ops.minimize import minimize_sop, minimize_pos
from logicsyn.ops.hazards import static1_hazards, hazard_free_cover
from logicsyn.ops.cost import estimate_cost
from logicsyn.ops.qm import dc_only_primes

from itertools import combinations


def make_function(ms, dc=None):
    dc = dc or []
    return BooleanFunction(
        "F",
        ["a", "b", "c"],
        sum(1 << m for m in ms),
        sum(1 << m for m in dc)
    )


def test_prime_implicants():
    f = make_function([0, 1, 2, 3])
    assert [p.pattern(3) for p in primes(f)] == ["0--"]


def test_dont_cares():
    f = make_function([0, 1], [2, 3])
    assert [p.pattern(3) for p in primes(f)] == ["0--"]


def test_essentials():
    f = make_function([0, 1, 2, 3])
    ps = primes(f)
    assert [p.pattern(3) for p in essentials(f, ps)] == ["0--"]


def test_minimum_cover():
    f = make_function([0, 1, 2, 5, 6, 7])
    cover, exact = min_cover(f, primes(f))
    assert exact is True
    assert len(cover) == 3
    assert all(
        any(c.contains(m) for c in cover)
        for m in [0, 1, 2, 5, 6, 7]
    )


def test_constant_functions():
    zero = make_function([])
    one = make_function(list(range(8)))

    assert minimize_sop(zero) == []
    assert [c.pattern(3) for c in minimize_sop(one)] == ["---"]
    assert minimize_pos(one) == []


def test_hazard_detection_and_fix():
    f = make_function([1, 3, 6, 7])
    cover = [
        Cube.from_pattern("11-"),
        Cube.from_pattern("0-1")
    ]

    assert static1_hazards(f, cover) == [(3, 7)]

    fixed = hazard_free_cover(f, cover)
    assert static1_hazards(f, fixed) == []
    assert Cube.from_pattern("-11") in fixed



def test_cost_estimation():
    cover = [
        Cube.from_pattern("11-"),
        Cube.from_pattern("0-1"),
        Cube.from_pattern("-11")
    ]

    result = estimate_cost(cover)

    assert result["terms"] == 3
    assert result["literals"] == 6
    assert result["not_gates"] == 1
    assert result["and_gates"] == 3
    assert result["or_gates"] == 2
    assert result["two_input_gates"] == 5
    assert result["delay"] == 4



def test_min_cover_brute_force():
    # Compare our solver against an independent exhaustive search.
    cases = [
        ([0, 1, 2, 3], []),
        ([0, 1, 2, 5, 6, 7], []),
        ([1, 3, 5], [7]),
        ([0, 2, 5, 7, 8, 10, 13, 15], []),
    ]

    for on, dc in cases:
        n = max(on + dc).bit_length()
        f = BooleanFunction(
            "F",
            [f"x{i}" for i in range(n)],
            sum(1 << m for m in on),
            sum(1 << m for m in dc)
        )

        ps = primes(f)
        result, exact = min_cover(f, ps)

        actual_cost = (
            sum(p.literals for p in result),
            len(result)
        )

        # Independently find the smallest possible cost.
        best_cost = None

        for size in range(1, len(ps) + 1):
            for subset in combinations(ps, size):
                if all(
                    any(p.contains(m) for p in subset)
                    for m in on
                ):
                    cost = (
                        sum(p.literals for p in subset),
                        len(subset)
                    )

                    if best_cost is None or cost < best_cost:
                        best_cost = cost

        assert exact is True
        assert actual_cost == best_cost
        assert all(
            any(p.contains(m) for p in result)
            for m in on
        )

def test_dc_only_primes():
    f = BooleanFunction(
        "F",
        ["a", "b", "c"],
        1 << 0,
        (1 << 5) | (1 << 7)
    )

    result = dc_only_primes(f)

    assert [p.pattern(3) for p in result] == ["1-1"]

