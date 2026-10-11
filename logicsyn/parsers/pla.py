"""Parser for Espresso PLA files of type f or fd."""
from ..core.bits import MAX_INPUTS
from ..core.cube import Cube
from ..core.function import BooleanFunction, Design


def parse_pla(text, name="pla"):
    n = m = ilb = ob = None
    kind, rows = "fd", []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if not line.startswith("."):
            rows.append((lineno, "".join(line.split())))
            continue
        key, *args = line.split()
        if key in (".e", ".end"):
            break
        if key in (".i", ".o", ".p"):
            if len(args) != 1 or not args[0].isdigit():
                raise ValueError(f"line {lineno}: {key} needs one number")
            if key == ".i":
                n = int(args[0])
            elif key == ".o":
                m = int(args[0])
        elif key == ".ilb":
            ilb = args
        elif key == ".ob":
            ob = args
        elif key == ".type":
            if args not in (["f"], ["fd"]):
                raise ValueError(f"line {lineno}: only .type f and fd are supported")
            kind = args[0]
        else:
            raise ValueError(f"line {lineno}: {key} is not supported")

    if n is None or m is None:
        raise ValueError("a PLA file needs .i and .o")
    if n > MAX_INPUTS:
        raise ValueError(f"{n} inputs; the limit is {MAX_INPUTS}")
    inputs = ilb or [chr(ord("a") + i) for i in range(n)]
    outputs = ob or [f"F{k}" for k in range(m)]
    if len(inputs) != n or len(outputs) != m:
        raise ValueError(".ilb and .ob must name exactly .i inputs and .o outputs")
    if len(set(inputs + outputs)) != n + m:
        raise ValueError("input and output names must all be different")

    on, dc = [0] * m, [0] * m
    for lineno, row in rows:
        if len(row) != n + m:
            raise ValueError(f"line {lineno}: expected {n} input and {m} output characters")
        try:
            t = Cube.from_pattern(row[:n]).tt(n)
        except ValueError as e:
            raise ValueError(f"line {lineno}: {e}") from None
        for k, ch in enumerate(row[n:]):
            if ch == "1":
                on[k] |= t
            elif ch == "-" and kind == "fd":
                dc[k] |= t
            elif ch not in "0-~":
                raise ValueError(f"line {lineno}: bad output character {ch!r}")
    return Design(name, inputs, [BooleanFunction(o, inputs, on[k], dc[k]) for k, o in enumerate(outputs)])
