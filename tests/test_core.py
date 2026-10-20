import random

import pytest

from logicsyn.core.bits import minterms, var_tt
from logicsyn.core.cube import Cube
from logicsyn.core.format import format_pos, format_sop
from logicsyn.core.function import BooleanFunction
from logicsyn.core.netlist import Netlist, sop_netlist


def test_first_input_is_msb():
    assert minterms(var_tt(3, 0)) == [4, 5, 6, 7]
    assert minterms(var_tt(3, 2)) == [1, 3, 5, 7]


def test_cube():
    c = Cube.from_pattern("1-0")
    assert c.pattern(3) == "1-0"
    assert c.literals == 2
    assert minterms(c.tt(3)) == [4, 6]
    assert [m for m in range(8) if c.contains(m)] == [4, 6]
    assert Cube.minterm(5, 3).pattern(3) == "101"


def test_dont_care_wins_and_complement():
    f = BooleanFunction("F", ["a", "b", "c"], on=0b10101010, dc=0b10000000)
    assert minterms(f.on) == [1, 3, 5]
    assert minterms(f.off) == [0, 2, 4, 6]
    g = f.complement()
    assert (g.name, g.on, g.dc) == ("F'", f.off, f.dc)


def test_input_limit():
    with pytest.raises(ValueError, match="limit"):
        BooleanFunction("F", [f"x{i}" for i in range(17)], 0)


def test_format():
    ins = ["a", "b", "c"]
    cover = [Cube.from_pattern("00-"), Cube.from_pattern("-10")]
    assert format_sop(cover, ins) == "a'b' + bc'"
    assert format_pos(cover, ins) == "(a+b)(b'+c)"
    assert (format_sop([], ins), format_pos([], ins)) == ("0", "1")
    assert (format_sop([Cube(0, 0)], ins), format_pos([Cube(0, 0)], ins)) == ("1", "0")
    assert format_sop([Cube.from_pattern("10")], ["sel", "en"]) == "sel en'"


def test_netlist_shares_gates_and_simulates():
    net = Netlist(["a", "b"], ["F"])
    na = net.gate("NOT", ["a"])
    assert net.gate("NOT", ["a"]) == na
    net.add("F", "AND", [na, "b"])
    assert minterms(net.simulate()["F"]) == [1]


def test_netlist_errors():
    loop = Netlist(["a"], ["x"])
    loop.add("x", "AND", ["a", "y"])
    loop.add("y", "NOT", ["x"])
    with pytest.raises(ValueError, match="loop"):
        loop.simulate()
    undriven = Netlist(["a"], ["x"])
    undriven.add("x", "OR", ["a", "z"])
    with pytest.raises(ValueError, match="never driven"):
        undriven.simulate()
    with pytest.raises(ValueError, match="driven twice"):
        undriven.add("x", "BUF", ["a"])


def _ops(net):
    return sorted(node.op for node in net.topo_order())


def test_sop_netlist_shares_inverters_and_terms():
    covers = {"F": [Cube.from_pattern("-11"), Cube.from_pattern("1-0")],
              "G": [Cube.from_pattern("-11"), Cube.from_pattern("000")]}
    net = sop_netlist(covers, ["a", "b", "c"])
    assert _ops(net) == ["AND", "AND", "AND", "NOT", "NOT", "NOT", "OR", "OR"]
    assert net.simulate() == {"F": sum(1 << m for m in (3, 4, 6, 7)), "G": sum(1 << m for m in (0, 3, 7))}


@pytest.mark.parametrize("patterns, ops", [
    ([], ["CONST0"]),
    (["--", "1-"], ["CONST1"]),
    (["1-"], ["BUF"]),
    (["-0"], ["NOT"]),
    (["10"], ["AND", "NOT"]),
    (["1-", "01"], ["AND", "NOT", "OR"]),
])
def test_sop_netlist_edge_cases(patterns, ops):
    cover = [Cube.from_pattern(p) for p in patterns]
    net = sop_netlist({"F": cover}, ["a", "b"])
    assert _ops(net) == ops
    assert net.simulate()["F"] == sum(1 << m for m in range(4) if any(c.contains(m) for c in cover))


@pytest.mark.parametrize("seed", range(10))
def test_sop_netlist_matches_random_covers(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 5)
    covers = {f"F{k}": [Cube.from_pattern("".join(rng.choice("01-") for _ in range(n)))
                        for _ in range(rng.randint(0, 4))] for k in range(3)}
    sim = sop_netlist(covers, [f"x{i}" for i in range(n)]).simulate()
    for out, cover in covers.items():
        assert sim[out] == sum(1 << m for m in range(1 << n) if any(c.contains(m) for c in cover))
