# EC551 Program 1: Logic Synthesis Engine

Ritwick and Lohit

A Python command-line tool that reads a Boolean function, runs the assignment's 12 operations on it, and writes the minimized circuit as structural Verilog with pin constraints for the Nexys A7 (Nexys 4 DDR) board.

## Architecture

```
expression / .pla / .blif
        |
    parsers/       text -> gate netlist or truth table
        |
    core/          one BooleanFunction per output: ON set and don't-care set stored as int bitmasks
        |
        +-- ops/       ops 1-12: canonical forms, Quine-McCluskey primes, minimum cover, hazards, cost
        +-- verilog/   minimized SOP -> gate-level Verilog (.v) + Nexys A7 pin constraints (.xdc)
```

| Op | Output | Op | Output |
|---|---|---|---|
| 1, 2 | Canonical SOP, POS | 7 | Prime implicants |
| 3, 4 | Inverse canonical SOP, POS | 8 | Essential prime implicants |
| 5, 6 | Minimized SOP, POS and literals saved | 9, 10 | ON-set minterms, OFF-set maxterms |
| 11 | Static hazards and a hazard-free SOP | 12 | Gate count and delay of each form |

## Folder layout

```
logicsyn/
  cli.py, __main__.py   command line and interactive prompt
  parsers/              expr.py, pla.py, blif.py
  core/                 truth tables, cubes, netlists, output formatting
  ops/                  canonical.py, qm.py, cover.py, minimize.py, hazards.py, cost.py, reports.py
  verilog/              emit.py (Verilog), nexys.py (XDC)
examples/               sample inputs in all three formats
tests/                  pytest suite
PLAN.md                 design decisions and milestones
```

## 1. Clone

Needs Python 3.10 or newer and no other packages. Use `python3` if `python` is Python 2.

```
git clone https://github.com/ritwick-arch/EC-551-Lab-Project-1-Ritwick-and-Lohit.git
cd EC-551-Lab-Project-1-Ritwick-and-Lohit
python --version
```

Optional tests (the Verilator and Yosys checks skip when those tools are not installed):

```
python -m pip install pytest
python -m pytest
```

## 2. Run an expression

```
python -m logicsyn -e "F(a,b,c) = bc + ac'"           # all 12 ops
python -m logicsyn -e "F(a,b,c) = bc + ac'" --op 5    # just op 5
```

```
Op 5  Minimized SOP
      F = bc + ac'
      Literals: 12 -> 4
      Saved: 8 (67%)
```

- Syntax: NOT `'` `!` `~`; AND by juxtaposition, `*` or `&`; OR `+` `|`; XOR `^`; lists `m(...)`, `M(...)`, `d(...)`. The header `F(a,b,c)` sets the input order, first input = MSB.
- Files: `python -m logicsyn examples/two_outputs.pla` (`.pla`, `.blif`, anything else is read as one expression).
- No arguments opens an interactive prompt (`help` lists its commands).
- `-o report.txt` saves the report; `--full` stops long lines being shortened.

## 3. Generate Verilog and constraints

```
python -m logicsyn -e "F(a,b,c) = bc + ac'" --fpga out/F
```

This writes `out/F/F_sop.v` and `out/F/F_sop.xdc` (`--verilog FILE` writes only the Verilog):

```verilog
module F_sop (input a, b, c, output F);
  wire c_n, t0, t1;
  not g0 (c_n, c);
  and g1 (t0, b, c);
  and g2 (t1, a, c_n);
  or  g3 (F, t0, t1);
endmodule
```

Pin mapping: the last input goes on SW0, the one before it on SW1, and so on, so the switches read as the minterm number. Output k goes on LED k. Up to 16 inputs and 16 outputs.

## 4. Program the Nexys A7 in Vivado

1. Create Project, then RTL Project.
2. Add Sources: `out/F/F_sop.v`.
3. Add Constraints: `out/F/F_sop.xdc` (instead of the master XDC).
4. Part: `xc7a100tcsg324-1`, then Finish.
5. Generate Bitstream.
6. Open Hardware Manager, then Open Target, Auto Connect, Program Device.
7. Set SW2 SW1 SW0 = a b c. LED0 lights for abc = 011, 100, 110 and 111 (minterms 3, 4, 6, 7).

## AI usage

We used Claude (Anthropic) as a coding assistant for design discussion, parts of the code and tests, and this README. 
