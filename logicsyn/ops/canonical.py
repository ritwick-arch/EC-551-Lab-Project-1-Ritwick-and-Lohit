"""Ops 1-4 (canonical forms) and ops 9-10 (ON-set and OFF-set counts)."""
from ..core.bits import minterms
from ..core.cube import Cube
from ..core.format import format_pos, format_sop

_PAD = " " * 6


def _canonical(title, f, name, sop, tt):
    """One canonical form; tt holds the minterms (SOP) or maxterms (POS) it lists."""
    idx = minterms(tt)
    cubes = [Cube.minterm(m, f.n) for m in idx]
    expr = format_sop(cubes, f.inputs) if sop else format_pos(cubes, f.inputs)
    head = f"{name} = {'Σm' if sop else 'ΠM'}({','.join(map(str, idx))})"
    if f.dc:
        head += f"   don't-cares: {','.join(map(str, minterms(f.dc)))}"
    return f"{title}\n{_PAD}{head}\n{_PAD}{' ' * len(name)} = {expr}"


def op1(f):
    return _canonical("Op 1  Canonical SOP", f, f.name, True, f.on)


def op2(f):
    return _canonical("Op 2  Canonical POS", f, f.name, False, f.off)


def op3(f):
    return _canonical("Op 3  Inverse canonical SOP", f, f.name + "'", True, f.off)


def op4(f):
    return _canonical("Op 4  Inverse canonical POS", f, f.name + "'", False, f.on)


def op9(f):
    return f"Op 9  ON-set minterms of {f.name}: {f.on.bit_count()}"


def op10(f):
    return f"Op 10 OFF-set maxterms of {f.name}: {f.off.bit_count()}"
