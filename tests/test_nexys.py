import pytest

from logicsyn.core.function import BooleanFunction, Design
from logicsyn.parsers import load_file, parse_expr
from logicsyn.verilog.emit import verilog_module
from logicsyn.verilog.nexys import constraints, write_board_files

from test_verilog import EXAMPLES


def test_two_outputs_constraints():
    assert constraints(verilog_module(load_file(EXAMPLES / "two_outputs.pla"))) == """\
## two_outputs on the Nexys A7 (xc7a100tcsg324-1): last input on SW0, output k on LED k
set_property -dict { PACKAGE_PIN M13  IOSTANDARD LVCMOS33 } [get_ports { a }]; # SW2
set_property -dict { PACKAGE_PIN L16  IOSTANDARD LVCMOS33 } [get_ports { b }]; # SW1
set_property -dict { PACKAGE_PIN J15  IOSTANDARD LVCMOS33 } [get_ports { c }]; # SW0
set_property -dict { PACKAGE_PIN H17  IOSTANDARD LVCMOS33 } [get_ports { F }]; # LED0
set_property -dict { PACKAGE_PIN K15  IOSTANDARD LVCMOS33 } [get_ports { G }]; # LED1
"""


def test_switches_8_and_9_are_1v8():
    xdc = constraints(verilog_module(parse_expr("F(a,b,c,d,e,f,g,h,i,j) = abcdefghij")))
    assert "PACKAGE_PIN T8   IOSTANDARD LVCMOS18 } [get_ports { b }]; # SW8" in xdc
    assert "PACKAGE_PIN U8   IOSTANDARD LVCMOS18 } [get_ports { a }]; # SW9" in xdc
    assert xdc.count("LVCMOS18") == 2


def test_too_many_outputs():
    fs = [BooleanFunction(f"F{k}", ["a"], 1) for k in range(17)]
    with pytest.raises(ValueError, match="16 LEDs"):
        constraints(verilog_module(Design("wide", ["a"], fs)))


def test_write_board_files(tmp_path):
    v, c = write_board_files(parse_expr("F(a,b) = ab'"), tmp_path / "board")
    assert (v.name, c.name) == ("F_sop.v", "F_sop.xdc")
    assert "module F_sop (input a, b, output F);" in v.read_text()
    assert "[get_ports { F }]; # LED0" in c.read_text()
