import random
from itertools import combinations

import pytest

from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction
from logicsyn.ops import OPS
from logicsyn.parsers.expr import parse_expr

HAZARD = parse_expr("F(a,b,c) = ab' + bc").functions[0]


def test_demo_text():
    assert OPS[5](HAZARD) == ("Op 5  Minimized SOP\n"
                              "      F = bc + ab'\n"
                              "      literals: 12 canonical, 4 minimized, 8 saved")
    assert OPS[6](HAZARD) == ("Op 6  Minimized POS\n"
                              "      F = (b'+c)(a+b)\n"
                              "      literals: 12 canonical, 4 minimized, 8 saved")
    assert OPS[7](HAZARD) == "Op 7  Prime implicants of F: 3"
    assert OPS[8](HAZARD) == "Op 8  Essential prime implicants of F: 2"
    assert OPS[11](HAZARD) == ("Op 11 Static-1 hazards in the minimized SOP of F: 1\n"
                               "      101 <-> 111 (b changes)\n"
                               "      hazard-free: F = bc + ab' + ac   (+2 literals)")
    assert OPS[12](HAZARD).splitlines()[2:] == [
        "      canonical SOP        4        12    4   1      5      2",
        "      minimized SOP        2         4    2   1      3      2"]


def test_counts_for_cyclic_function():
    f = parse_expr("F(a,b,c) = m(0,1,2,5,6,7)").functions[0]
    assert OPS[7](f).endswith(": 6") and OPS[8](f).endswith(": 0")
    assert OPS[5](f).endswith("literals: 18 canonical, 6 minimized, 12 saved")
    assert OPS[11](f).splitlines()[0].endswith(": 3")


@pytest.mark.parametrize("on, dc, sop, pos", [
    (0b0000, 0b0000, "0", "0"),
    (0b1111, 0b0000, "1", "1"),
    (0b0000, 0b1111, "0", "1"),
])
def test_constants(on, dc, sop, pos):
    f = BooleanFunction("F", ["a", "b"], on, dc)
    assert OPS[5](f).splitlines()[1] == f"      F = {sop}"
    assert OPS[6](f).splitlines()[1] == f"      F = {pos}"
    assert OPS[11](f).endswith(": 0")


def test_one_variable():
    f = parse_expr("F(a) = a'").functions[0]
    assert OPS[5](f).splitlines()[1:] == ["      F = a'", "      literals: 1 canonical, 1 minimized, 0 saved"]
    assert OPS[6](f).splitlines()[1] == "      F = (a')"


def _cover_tt(cover, n):
    t = 0
    for c in cover:
        t |= c.tt(n)
    return t


def _brute_minimum(f):
    """(terms, literals) of the smallest cover, searched over primes found by brute force."""
    n, care = f.n, f.on | f.dc
    cubes = [Cube(mask, v) for mask in range(1 << n) for v in range(1 << n) if v & ~mask == 0]
    imps = [c for c in cubes if c.tt(n) & ~care == 0]
    primes = [c for c in imps if c.tt(n) & f.on
              and not any(d != c and d.tt(n) & c.tt(n) == c.tt(n) for d in imps)]
    for k in range(len(primes) + 1):
        sizes = [sum(c.literals for c in s) for s in combinations(primes, k)
                 if f.on & ~_cover_tt(s, n) == 0]
        if sizes:
            return k, min(sizes)


@pytest.mark.parametrize("seed", range(30))
def test_minimized_forms_match_and_are_minimal(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 4)
    dc = rng.getrandbits(1 << n) & rng.getrandbits(1 << n)
    f = BooleanFunction("F", [chr(97 + i) for i in range(n)], rng.getrandbits(1 << n), dc)

    def parsed(op):
        expr = OPS[op](f).splitlines()[1].split("= ", 1)[1]
        return parse_expr(f"F({','.join(f.inputs)}) = {expr}").functions[0].on

    for op in (5, 6):
        got = parsed(op)
        assert got & f.on == f.on and got & f.off == 0
    terms, literals = _brute_minimum(f)
    assert OPS[5](f).splitlines()[1].count("+") + 1 == max(terms, 1)
    assert f", {literals} minimized," in OPS[5](f)
