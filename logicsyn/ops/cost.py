
"""Gate counts and unit-delay estimates for two-level SOP/POS."""

from math import ceil, log2
from logicsyn.core.cube import Cube


def estimate_cost(
    cover: list[Cube],
    form: str = "sop",
    n: int | None = None
) -> dict:
    if form not in ("sop", "pos"):
        raise ValueError("form must be 'sop' or 'pos'")

    terms = len(cover)
    literals = sum(c.literals for c in cover)

    # A constant expression needs no gates.
    if terms == 0 or any(c.literals == 0 for c in cover):
        return {
            "terms": terms,
            "literals": literals,
            "not_gates": 0,
            "and_gates": 0,
            "or_gates": 0,
            "two_input_gates": 0,
            "delay": 0,
        }

    # SOP: a zero bit means a complemented input.
    # POS cubes represent F', so polarity is reversed.
    inverted_bits = 0

    for cube in cover:
        if form == "sop":
            inverted_bits |= cube.mask & ~cube.value
        else:
            inverted_bits |= cube.mask & cube.value

    not_gates = inverted_bits.bit_count()

    inner_gates = sum(
        max(0, c.literals - 1) for c in cover
    )
    outer_gates = max(0, terms - 1)

    if form == "sop":
        and_gates = inner_gates
        or_gates = outer_gates
    else:
        or_gates = inner_gates
        and_gates = outer_gates

    # Each gate is a balanced tree of two-input gates.
    def levels(k):
        return ceil(log2(k)) if k > 1 else 0

    term_delays = []

    for cube in cover:
        if form == "sop":
            has_inverted_input = bool(
                cube.mask & ~cube.value
            )
        else:
            has_inverted_input = bool(
                cube.mask & cube.value
            )

        inversion_delay = 1 if has_inverted_input else 0

        term_delays.append(
            inversion_delay + levels(cube.literals)
        )

    delay = max(term_delays) + levels(terms)

    return {
        "terms": terms,
        "literals": literals,
        "not_gates": not_gates,
        "and_gates": and_gates,
        "or_gates": or_gates,
        "two_input_gates": and_gates + or_gates,
        "delay": delay,
    }
