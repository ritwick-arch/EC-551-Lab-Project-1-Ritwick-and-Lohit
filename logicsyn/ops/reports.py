
"""Reports for minimized forms and prime implicants."""

from ..core.bits import minterms
from ..core.format import format_sop, format_pos
from .qm import primes, dc_only_primes
from .cover import essentials, min_cover
from .minimize import minimize_sop, minimize_pos
from .hazards import (
    static1_hazards,
    static0_hazards,
    hazard_free_cover,
)
from ..core.cube import Cube
from .cost import estimate_cost

_PAD = " " * 6


def op5(f):
    cover = minimize_sop(f)
    expr = format_sop(cover, f.inputs)

    canonical = f.on.bit_count() * f.n
    minimized = sum(c.literals for c in cover)
    saved = canonical - minimized
    percent = 100 * saved / canonical if canonical else 0

    return (
        f"Op 5  Minimized SOP\n"
        f"{_PAD}{f.name} = {expr}\n"
        f"{_PAD}Literals: {canonical} -> {minimized}\n"
        f"{_PAD}Saved: {saved} ({percent:.0f}%)"
    )


def op6(f):
    cover = minimize_pos(f)
    expr = format_pos(cover, f.inputs)

    canonical = f.off.bit_count() * f.n
    minimized = sum(c.literals for c in cover)
    saved = canonical - minimized
    percent = 100 * saved / canonical if canonical else 0

    return (
        f"Op 6  Minimized POS\n"
        f"{_PAD}{f.name} = {expr}\n"
        f"{_PAD}Literals: {canonical} -> {minimized}\n"
        f"{_PAD}Saved: {saved} ({percent:.0f}%)"
    )


def op7(f):
    ps = primes(f)
    dc_ps = dc_only_primes(f)

    patterns = ", ".join(p.pattern(f.n) for p in ps) or "none"
    dc_patterns = ", ".join(
        p.pattern(f.n) for p in dc_ps
    ) or "none"

    return (
        f"Op 7  Prime implicants of {f.name}: {len(ps)}\n"
        f"{_PAD}Primes: {patterns}\n"
        f"{_PAD}Don't-care-only primes: {dc_patterns}"
    )


def op8(f):
    ps = primes(f)
    ep = essentials(f, ps)

    patterns = ", ".join(
        p.pattern(f.n) for p in ep
    ) or "none"

    return (
        f"Op 8  Essential prime implicants of {f.name}: {len(ep)}\n"
        f"{_PAD}Essentials: {patterns}"
    )

def op11(f):
    sop = minimize_sop(f)
    pos = minimize_pos(f)

    hazards1 = static1_hazards(f, sop)
    hazards0 = static0_hazards(f, pos)

    fixed_sop = hazard_free_cover(f, sop)

    def describe(hazards):
        if not hazards:
            return "none"

        lines = []

        for a, b in hazards:
            diff = a ^ b
            bit_position = diff.bit_length() - 1
            variable = f.inputs[f.n - 1 - bit_position]
            lines.append(f"{a} <-> {b} (input {variable})")

        return ", ".join(lines)

    original_literals = sum(c.literals for c in sop)
    fixed_literals = sum(c.literals for c in fixed_sop)

    return (
        f"Op 11 Static hazard analysis\n"
        f"{_PAD}Static-1 hazards: {describe(hazards1)}\n"
        f"{_PAD}Static-0 hazards: {describe(hazards0)}\n"
        f"{_PAD}Hazard-free SOP: "
        f"{format_sop(fixed_sop, f.inputs)}\n"
        f"{_PAD}Extra literals: "
        f"{fixed_literals - original_literals}"
    )


def op12(f):
    canonical_sop = [
        Cube.minterm(m, f.n)
        for m in minterms(f.on)
    ]

    sop = minimize_sop(f)
    pos = minimize_pos(f)
    hazard_free = hazard_free_cover(f, sop)

    cases = [
        ("Canonical SOP", canonical_sop, "sop"),
        ("Minimized SOP", sop, "sop"),
        ("Minimized POS", pos, "pos"),
        ("Hazard-free SOP", hazard_free, "sop"),
    ]

    lines = [
        "Op 12 Gate count and delay estimate",
        f"{'Form':<19} {'NOT':>4} {'AND':>4} "
        f"{'OR':>4} {'2-input':>8} "
        f"{'Literals':>9} {'Delay':>6}"
    ]

    for name, cover, form in cases:
        c = estimate_cost(cover, form)

        lines.append(
            f"{name:<19} "
            f"{c['not_gates']:>4} "
            f"{c['and_gates']:>4} "
            f"{c['or_gates']:>4} "
            f"{c['two_input_gates']:>8} "
            f"{c['literals']:>9} "
            f"{c['delay']:>6}"
        )

    return "\n".join(lines)

