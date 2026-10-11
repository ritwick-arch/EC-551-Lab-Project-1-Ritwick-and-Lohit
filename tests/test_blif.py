import re

import pytest

from logicsyn.parsers.blif import parse_blif
from util import table

SAMPLE = """\
.model demo
.inputs a b c
.outputs F
.names a b t   # t = ab
11 1
.names t c F   # F = t + c
1- 1
-1 1
.end
"""


def test_sample():
    d = parse_blif(SAMPLE)
    f = d.functions[0]
    assert (d.name, d.inputs, f.name) == ("demo", ["a", "b", "c"], "F")
    assert f.on == table(3, lambda a, b, c: a and b or c)
    assert sorted(node.op for node in f.source.nodes.values()) == ["AND", "OR"]


def test_off_set_rows_and_constants():
    d = parse_blif(".inputs a b\n.outputs F G one zero\n.names a b F\n11 0\n"
                   ".names a G\n0 1\n.names one\n1\n.names zero\n")
    f, g, one, zero = d.functions
    assert f.on == table(2, lambda a, b: not (a and b))
    assert g.on == table(2, lambda a, b: not a)
    assert (one.on, zero.on) == (0b1111, 0)


def test_continuation_lines():
    d = parse_blif(".inputs a \\\n  b\n.outputs F\n.names a b F\n1- 1\n-1 1\n")
    assert d.functions[0].on == table(2, lambda a, b: a or b)


@pytest.mark.parametrize("text, msg", [
    (".inputs a\n.outputs q\n.latch a q 0\n", "line 3: .latch is not supported"),
    (".inputs a\n.outputs F\n.names a F\n1 1\n0 0\n", "all 1 or all 0"),
    (".inputs a\n.outputs F\n.names a x F\n11 1\n", "never driven"),
    (".inputs a\n.outputs F\n.names a G F\n11 1\n.names F G\n1 1\n", "loop"),
    (".inputs a\n.outputs F\n.names a F\n1 1\n.names a F\n0 1\n", "line 5: signal F is driven twice"),
    (".inputs a\n.outputs F\n.names a F\n12 1\n", "line 4"),
])
def test_errors(text, msg):
    with pytest.raises(ValueError, match=re.escape(msg)):
        parse_blif(text)
