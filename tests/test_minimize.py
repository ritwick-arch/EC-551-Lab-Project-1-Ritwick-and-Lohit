
from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction
from logicsyn.ops.qm import primes
from logicsyn.ops.cover import essentials, min_cover
from logicsyn.ops.minimize import minimize_sop, minimize_pos
from logicsyn.ops.hazards import static1_hazards, hazard_free_cover
from logicsyn.ops.cost import estimate_cost


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
    cover = min_cover(f, primes(f))
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

    assert result["total_gates"] == 4
    assert result["literals"] == 6
    assert result["depth"] == 2
