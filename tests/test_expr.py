import re

import pytest

from logicsyn.core.bits import minterms
from logicsyn.parsers.expr import parse_expr
from util import table


def one(text):
    design = parse_expr(text)
    assert len(design.functions) == 1
    return design.functions[0]


@pytest.mark.parametrize("text, fn", [
    ("F(a,b,c) = ab' + c", lambda a, b, c: a and not b or c),
    ("F(a,b,c) = a + bc'", lambda a, b, c: a or b and not c),
    ("F(a,b,c) = (a + b)'c", lambda a, b, c: not (a or b) and c),
    ("F(a,b,c) = !a*b | c", lambda a, b, c: not a and b or c),
    ("F(a,b,c) = a & ~b . c", lambda a, b, c: a and not b and c),
    ("F(a,b,c) = a ^ bc", lambda a, b, c: a ^ (b and c)),
    ("F(a,b,c) = a ⊕ b·c", lambda a, b, c: a ^ (b and c)),
    ("F(a,b,c) = (a+b)(a'+c)", lambda a, b, c: (a or b) and (not a or c)),
    ("F(a,b,c) = a b' c + 0", lambda a, b, c: a and not b and c),
    ("F(a,b,c) = a'' + 1", lambda a, b, c: True),
])
def test_operators_and_precedence(text, fn):
    assert one(text).on == table(3, fn)


def test_names_and_input_order():
    f = one("x1x2' + x10")
    assert f.inputs == ["x1", "x2", "x10"]
    assert f.on == table(3, lambda x1, x2, x10: x1 and not x2 or x10)
    assert one("b + a").inputs == ["a", "b"]
    assert one("F(c,b,a) = a").on == table(3, lambda c, b, a: a)
    assert one("Y = A B + a").inputs == ["A", "B", "a"]


def test_lists():
    f = one("F(a,b,c) = m(1,3,5) + d(7)")
    assert (minterms(f.on), minterms(f.dc)) == ([1, 3, 5], [7])
    assert one("F(a,b,c) = Σm(1,3,5)").on == f.on
    g = one("F(a,b,c) = M(0,2,4) + d(7)")
    assert (minterms(g.on), minterms(g.dc)) == ([1, 3, 5, 6], [7])
    assert one("F(a,b,c) = ΠM(0,2,4)").on == one("F(a,b,c) = M(0,2,4)").on
    assert f.source is None


def test_dont_cares_after_expression_and_variable_d():
    f = one("F(a,b,c,d) = ab + c'd + d(1,4)")
    assert minterms(f.dc) == [1, 4]
    assert f.on == table(4, lambda a, b, c, d: a and b or not c and d) & ~f.dc
    assert one("F(a,b,c,d) = d(a + b)").on == table(4, lambda a, b, c, d: d and (a or b))


def test_structure_is_kept():
    f = one("F(a,b,c) = ab + a'c")
    assert sorted(node.op for node in f.source.nodes.values()) == ["AND", "AND", "NOT", "OR"]


def test_comments_and_line_breaks():
    f = one("# demo\nF(a,b) = a'b  # first term\n  + ab'\n;")
    assert f.on == table(2, lambda a, b: a ^ b)


@pytest.mark.parametrize("text, msg", [
    ("F = m(1,3)", "header"),
    ("F = ab + d(1)", "header"),
    ("F(a,b) = m(4)", "too large"),
    ("F(a) = a + b", "not listed in the header"),
    ("F = a; G = b", "one function"),
    ("F = a + $", "unexpected character"),
    ("F = (a + b", "expected ')'"),
    ("Fx(a) = a", "left side"),
    ("F(a,b,c) = a m(1)", "whole right side"),
])
def test_errors(text, msg):
    with pytest.raises(ValueError, match=re.escape(msg)):
        parse_expr(text)
