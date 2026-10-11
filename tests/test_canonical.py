import random

import pytest

from logicsyn.core.function import BooleanFunction
from logicsyn.ops import OPS
from logicsyn.parsers.expr import parse_expr

DEMO = parse_expr("F(a,b,c) = m(1,3,5) + d(7)").functions[0]


def test_demo_text():
    assert OPS[1](DEMO) == ("Op 1  Canonical SOP\n"
                            "      F = Σm(1,3,5)   don't-cares: 7\n"
                            "        = a'b'c + a'bc + ab'c")
    assert OPS[2](DEMO).endswith("F = ΠM(0,2,4,6)   don't-cares: 7\n"
                                 "        = (a+b+c)(a+b'+c)(a'+b+c)(a'+b'+c)")
    assert OPS[3](DEMO).endswith("F' = Σm(0,2,4,6)   don't-cares: 7\n"
                                 "         = a'b'c' + a'bc' + ab'c' + abc'")
    assert OPS[4](DEMO).endswith("F' = ΠM(1,3,5)   don't-cares: 7\n"
                                 "         = (a+b+c')(a+b'+c')(a'+b+c')")
    assert OPS[9](DEMO) == "Op 9  ON-set minterms of F: 3"
    assert OPS[10](DEMO) == "Op 10 OFF-set maxterms of F: 4"


@pytest.mark.parametrize("seed", range(20))
def test_canonical_forms_match_truth_table(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 5)
    dc = rng.getrandbits(1 << n) & rng.getrandbits(1 << n)
    f = BooleanFunction("F", [chr(97 + i) for i in range(n)], rng.getrandbits(1 << n), dc)

    def parsed(op):
        expr = OPS[op](f).splitlines()[-1].split("= ", 1)[1]
        return parse_expr(f"F({','.join(f.inputs)}) = {expr}").functions[0].on

    assert parsed(1) == f.on
    assert parsed(2) == f.on | f.dc
    assert parsed(3) == f.off
    assert parsed(4) == f.off | f.dc
    assert int(OPS[9](f).split(": ")[1]) == f.on.bit_count()
    assert int(OPS[10](f).split(": ")[1]) == f.off.bit_count()
