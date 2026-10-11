# Usage: vivado -mode batch -source build.tcl, then program smoke.bit from the Hardware Manager.
cd [file dirname [file normalize [info script]]]
read_verilog smoke.v
read_xdc basys3.xdc
synth_design -top top -part xc7a35tcpg236-1
opt_design
place_design
route_design
write_bitstream -force smoke.bit
