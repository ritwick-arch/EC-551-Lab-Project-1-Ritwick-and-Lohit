"""Text for product terms, SOP covers and POS covers."""
import re

_SIMPLE = re.compile(r"[A-Za-z][0-9]*")


def _sep(inputs):
    return "" if all(_SIMPLE.fullmatch(x) for x in inputs) else " "


def format_product(cube, inputs):
    parts = [inputs[i] + ("" if pos else "'") for i, pos in cube.lits(len(inputs))]
    return _sep(inputs).join(parts) or "1"


def format_clause(cube, inputs):
    """The sum term that is the complement of cube."""
    parts = [inputs[i] + ("'" if pos else "") for i, pos in cube.lits(len(inputs))]
    return "(" + "+".join(parts) + ")" if parts else "0"


def format_sop(cover, inputs):
    return " + ".join(format_product(c, inputs) for c in cover) or "0"


def format_pos(cover, inputs):
    """POS of F, given the cover of F'."""
    clauses = [format_clause(c, inputs) for c in cover]
    return "0" if "0" in clauses else "".join(clauses) or "1"
