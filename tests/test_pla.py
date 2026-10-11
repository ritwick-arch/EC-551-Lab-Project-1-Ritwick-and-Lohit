import re

import pytest

from logicsyn.core.bits import minterms
from logicsyn.parsers.pla import parse_pla

SAMPLE = """\
# two outputs, one don't-care
.i 3
.o 2
.ilb a b c
.ob F G
.type fd
.p 3
1-0 10
-11 11
000 -1
.e
"""


def test_sample():
    d = parse_pla(SAMPLE, "sample")
    f, g = d.functions
    assert d.inputs == ["a", "b", "c"]
    assert (f.name, minterms(f.on), minterms(f.dc)) == ("F", [3, 4, 6, 7], [0])
    assert (g.name, minterms(g.on), minterms(g.dc)) == ("G", [0, 3, 7], [])


def test_type_f_and_default_names():
    d = parse_pla(".i 2\n.o 1\n.type f\n1- 1\n01 -\n")
    f = d.functions[0]
    assert (d.inputs, f.name) == (["a", "b"], "F0")
    assert (minterms(f.on), f.dc) == ([2, 3], 0)


@pytest.mark.parametrize("text, msg", [
    (".i 2\n.o 1\n.type fr\n", "only .type f and fd"),
    (".i 2\n.o 1\n1 1\n", "expected 2 input and 1 output"),
    (".i 2\n.o 1\n1x 1\n", "bad cube character"),
    (".o 1\n1 1\n", "needs .i and .o"),
    (".i 2\n.o 1\n.ilb a\n", ".ilb and .ob"),
    (".i 2\n.o 1\n.phase 1\n", "not supported"),
])
def test_errors(text, msg):
    with pytest.raises(ValueError, match=re.escape(msg)):
        parse_pla(text)
