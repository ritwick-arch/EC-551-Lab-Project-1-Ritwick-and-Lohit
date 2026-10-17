"""Ops 5-8, 11 and 12: report text for the minimization, hazard and cost code."""
from ..core.bits import minterms
from ..core.cube import Cube
from ..core.format import format_pos, format_sop
from .cost import estimate_cost
from .cover import essentials
from .hazards import hazard_free_cover, static1_hazards
from .minimize import minimize_pos, minimize_sop
from .qm import primes

_PAD = " " * 6


def _literals(cover):
    return sum(c.literals for c in cover)


def _minimized(title, f, cover, expr, canonical):
    used = _literals(cover)
    return (f"{title}\n{_PAD}{f.name} = {expr}\n"
            f"{_PAD}literals: {canonical} canonical, {used} minimized, {canonical - used} saved")


def op5(f):
    cover = minimize_sop(f)
    return _minimized("Op 5  Minimized SOP", f, cover, format_sop(cover, f.inputs), f.on.bit_count() * f.n)


def op6(f):
    cover = minimize_pos(f)
    return _minimized("Op 6  Minimized POS", f, cover, format_pos(cover, f.inputs), f.off.bit_count() * f.n)


def op7(f):
    return f"Op 7  Prime implicants of {f.name}: {len(primes(f))}"


def op8(f):
    return f"Op 8  Essential prime implicants of {f.name}: {len(essentials(f, primes(f)))}"


def op11(f):
    cover = minimize_sop(f)
    hazards = static1_hazards(f, cover)
    lines = [f"Op 11 Static-1 hazards in the minimized SOP of {f.name}: {len(hazards)}"]
    if hazards:
        n = f.n
        lines.append(_PAD + ", ".join(f"{a:0{n}b} <-> {b:0{n}b} ({f.inputs[n - (a ^ b).bit_length()]} changes)"
                                      for a, b in hazards))
        fixed = hazard_free_cover(f, cover)
        lines.append(f"{_PAD}hazard-free: {f.name} = {format_sop(fixed, f.inputs)}"
                     f"   (+{_literals(fixed) - _literals(cover)} literals)")
    return "\n".join(lines)


def op12(f):
    rows = [("canonical SOP", [Cube.minterm(m, f.n) for m in minterms(f.on)]), ("minimized SOP", minimize_sop(f))]
    lines = [f"Op 12 Gate count and depth of {f.name} (two-level, inverters not counted)",
             f"{_PAD}{'':15}{'terms':>7}{'literals':>10}{'AND':>5}{'OR':>4}{'gates':>7}{'depth':>7}"]
    for label, cover in rows:
        c = estimate_cost(cover)
        lines.append(f"{_PAD}{label:15}{c['terms']:>7}{c['literals']:>10}{c['and_gates']:>5}"
                     f"{c['or_gates']:>4}{c['total_gates']:>7}{c['depth']:>7}")
    return "\n".join(lines)
