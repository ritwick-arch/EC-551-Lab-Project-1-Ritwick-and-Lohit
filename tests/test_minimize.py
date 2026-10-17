
import random

from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction
from logicsyn.ops.qm import primes
from logicsyn.ops.cover import essentials, min_cover
from logicsyn.ops.minimize import minimize_sop, minimize_pos
from logicsyn.ops.hazards import static1_hazards, hazard_free_cover
from logicsyn.ops.cost import estimate_cost
from logicsyn.ops import OPS


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
    assert exact and len(cover) == 3
    assert all(
        any(c.contains(m) for c in cover)
        for m in [0, 1, 2, 5, 6, 7]
    )


def test_constant_functions():
    zero = make_function([])
    one = make_function(list(range(8)))

    assert minimize_sop(zero) == ([], True)
    assert [c.pattern(3) for c in minimize_sop(one)[0]] == ["---"]
    assert minimize_pos(one) == ([], True)


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


def covers_exactly(f, cover):
    tt = 0
    for c in cover:
        tt |= c.tt(f.n)
    return tt & f.on == f.on and tt & f.off == 0


def test_greedy_fallback(monkeypatch):
    monkeypatch.setattr("logicsyn.ops.cover.LIMIT", 0)
    f = make_function([0, 1, 2, 5, 6, 7])
    cover, exact = minimize_sop(f)
    assert not exact and covers_exactly(f, cover)
    assert "heuristic" in OPS[5](f).splitlines()[0]


def test_larger_functions_finish():
    names = [f"x{i}" for i in range(8)]
    parity = BooleanFunction("F", names[:6], sum(1 << m for m in range(64) if bin(m).count("1") % 2))
    greater = BooleanFunction("F", names, sum(1 << m for m in range(256) if m >> 4 > m & 15))
    assert minimize_sop(parity)[1] and len(minimize_sop(parity)[0]) == 32
    assert minimize_sop(greater)[1] and len(minimize_sop(greater)[0]) == 15
    rng = random.Random(0)
    for n in (6, 8):
        f = BooleanFunction("F", names[:n], rng.getrandbits(1 << n))
        assert covers_exactly(f, minimize_sop(f)[0]) and covers_exactly(f.complement(), minimize_pos(f)[0])
