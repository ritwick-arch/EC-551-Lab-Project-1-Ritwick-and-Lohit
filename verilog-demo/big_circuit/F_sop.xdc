## F_sop on the Nexys A7 (xc7a100tcsg324-1): last input on SW0, output k on LED k
set_property -dict { PACKAGE_PIN T18  IOSTANDARD LVCMOS33 } [get_ports { a }]; # SW5
set_property -dict { PACKAGE_PIN R17  IOSTANDARD LVCMOS33 } [get_ports { b }]; # SW4
set_property -dict { PACKAGE_PIN R15  IOSTANDARD LVCMOS33 } [get_ports { c }]; # SW3
set_property -dict { PACKAGE_PIN M13  IOSTANDARD LVCMOS33 } [get_ports { d }]; # SW2
set_property -dict { PACKAGE_PIN L16  IOSTANDARD LVCMOS33 } [get_ports { e }]; # SW1
set_property -dict { PACKAGE_PIN J15  IOSTANDARD LVCMOS33 } [get_ports { f }]; # SW0
set_property -dict { PACKAGE_PIN H17  IOSTANDARD LVCMOS33 } [get_ports { F }]; # LED0
