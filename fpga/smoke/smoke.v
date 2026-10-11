// Lab smoke test: LED0 = a'b' + bc' + ac with a, b, c on SW2, SW1, SW0, so it is off only for 011 and 100.
module F_sop (input a, input b, input c, output F);
  wire a_n, b_n, c_n, t0, t1, t2;
  not g0 (a_n, a);
  not g1 (b_n, b);
  not g2 (c_n, c);
  and g3 (t0, a_n, b_n);
  and g4 (t1, b, c_n);
  and g5 (t2, a, c);
  or  g6 (F, t0, t1, t2);
endmodule

module top (input [2:0] sw, output [0:0] led);
  F_sop u0 (.a(sw[2]), .b(sw[1]), .c(sw[0]), .F(led[0]));
endmodule
