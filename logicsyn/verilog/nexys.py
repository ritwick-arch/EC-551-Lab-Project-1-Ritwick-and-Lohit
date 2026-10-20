"""Nexys A7 (Nexys 4 DDR) constraints: inputs on the slide switches, outputs on the LEDs."""
from pathlib import Path

from .emit import verilog_module

# Package pins from the course's Nexys4DDR_Master.xdc; the index is the switch or LED number.
SWITCHES = "J15 L16 M13 R15 R17 T18 U18 R13 T8 U8 R16 T13 H6 U12 U11 V10".split()
LEDS = "H17 K15 J13 N14 R18 V17 U17 U16 V16 T15 U14 T16 V15 V14 V12 V11".split()
_LVCMOS18 = {8, 9}  # SW8 and SW9 sit in a 1.8 V bank


def _pin(pin, port, standard, label):
    return f"set_property -dict {{ PACKAGE_PIN {pin:<4} IOSTANDARD {standard} }} [get_ports {{ {port} }}]; # {label}"


def constraints(module):
    """XDC with the last input on SW0, so the switches read as the minterm number, and output k on LED k."""
    n, m = len(module.inputs), len(module.outputs)
    if n > len(SWITCHES) or m > len(LEDS):
        raise ValueError(f"the Nexys A7 has {len(SWITCHES)} switches and {len(LEDS)} LEDs; "
                         f"{module.name} needs {n} inputs and {m} outputs")
    lines = [f"## {module.name} on the Nexys A7 (xc7a100tcsg324-1): last input on SW0, output k on LED k"]
    for i, port in enumerate(module.inputs):
        sw = n - 1 - i
        lines.append(_pin(SWITCHES[sw], port, "LVCMOS18" if sw in _LVCMOS18 else "LVCMOS33", f"SW{sw}"))
    lines += [_pin(LEDS[k], port, "LVCMOS33", f"LED{k}") for k, port in enumerate(module.outputs)]
    return "\n".join(lines) + "\n"


def write_board_files(design, outdir, source=None):
    """Write <module>.v and <module>.xdc into outdir and return their paths."""
    module = verilog_module(design, source)
    xdc = constraints(module)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    v, c = out / f"{module.name}.v", out / f"{module.name}.xdc"
    v.write_text(module.text, encoding="utf-8")
    c.write_text(xdc, encoding="utf-8")
    return v, c
