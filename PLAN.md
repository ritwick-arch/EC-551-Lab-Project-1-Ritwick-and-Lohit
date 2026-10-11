# Program 1 Plan: Logic Synthesis Engine

**EC551, Fall 2026 · Ritwick & Lohit · Due Fri 10/23, 11:59 PM**: a public GitHub link sent to Prof. Densmore, followed by a live demo.

**Status (Sun 10/11):** the repo is set up and decision steps A–D are settled. Steps E–F are in progress, and no code has been written yet.

**How we work:** settle the decisions first, then build one milestone at a time. Work goes to `main` through PRs that the other person reviews.

## 1. What we hand in

From the assignment (Rev 1.0):

| Area | Requirement | Our plan |
|---|---|---|
| Interface | at least one of: file, command line, GUI | file argument + interactive prompt |
| Algebraic input | SOP required; POS and multi-level optional | expression parser (SOP, POS, multi-level) |
| Circuit input | graph-based circuit, any format | BLIF (Espresso PLA as well) |
| Ops 1–4 | canonical SOP, canonical POS, canonical SOP of F', canonical POS of F' | `Σm`/`ΠM` lists + written-out expressions |
| Ops 5–6 | literal-minimized SOP / POS, with literals saved vs. canonical | Quine–McCluskey + exact cover |
| Ops 7–8 | number of prime implicants (PIs) / essential prime implicants (EPIs) | from the QM prime table |
| Ops 9–10 | number of ON-set minterms / OFF-set maxterms | from the truth table |
| Ops 11–12 | two custom commands | 11: static-hazard detection + hazard-free cover · 12: gate count + delay estimate |
| Verilog | structural `.v` from primitive gates for the minimized circuit | generator using `and` / `or` / `not` instances |
| FPGA | synthesize the generated Verilog and run it on the board; hand-written wrappers allowed | Basys 3: switches → inputs, LEDs → outputs |
| Repo | public; well-structured, commented code; README with architecture, folder layout, build/run/usage steps | see §4 and M5 |
| AI policy | cite AI use in the README or code headers; be ready to explain and defend all of it | AI-usage log from day 1 |
| Demo | run all the ops on our own test cases; walk through the code and key decisions; show the generated Verilog running live on the FPGA | demo script + rehearsal (M5) |

## 2. Already decided (9/28)

- **Language and interface:** Python 3 (3.12 on SCC), command line only, no GUI.
- **Input formats:** EQN-style expressions, Espresso PLA and BLIF. No JSON.
- **Custom ops:**
  - Op 11: static-hazard detection plus a hazard-free cover.
  - Op 12: gate count plus delay estimate.
- **Board and tools:**
  - Board: Basys 3 (xc7a35tcpg236-1).
  - Vivado exists only on the lab machines, so we ship a batch `build.tcl`.
  - SCC has Yosys 0.48 and Verilator 4.108 for checking the generated Verilog.

## 3. Open decisions (settle by Mon 10/12)

Each item is a recommendation. Tick it once both of us agree, or edit it.

### A. Core representation (decided 10/11)

- [x] **A1 Storage:** each output is a truth table made of an ON bitset and a don't-care bitset, one bit per minterm, stored as Python ints. The limit is 16 inputs, which matches the 16 switches.
- [x] **A2 Variable order:**
  - The first variable is the most significant bit, so `m6` of `(a,b,c)` is `abc'` and the switches read as the minterm number.
  - The order comes from the `F(a,b,c)` header, `.ilb` or `.inputs`. If none is given, it is alphabetical (`x2` before `x10`).
- [x] **A3 Multiple outputs:** every op runs on each output by itself. The Verilog shares identical AND gates and input inverters between outputs.
- [x] **A4 Don't-cares:** supported through `d(...)`, PLA `-` outputs and `.type fd`.
  - Ops 1–4 list them separately as `+ d(...)`.
  - Ops 9–10 leave them out of the counts.
  - Minimization uses them.
  - A minterm given as both ON and don't-care counts as a don't-care.
  - Example: `F(a,b,c) = m(1,3,5) + d(7)` minimizes to `c` (9 → 1 literal). Without the don't-care it is `a'c + b'c` (4 literals).
- [x] **A5 Structure:** BLIF circuits and multi-level expressions are simulated to get their truth table. Their gate structure is also kept, so op 12 can compare the original circuit with the minimized one.

### B. Input syntax (decided 10/11)

- [x] **B1 Names:**
  - A name is one letter plus optional digits (`a`, `B`, `x1`, `x12`). Case matters, so `A` ≠ `a`.
  - Names written next to each other are ANDed, so `ab'c` and `x1x2'` read as in a textbook.
  - Longer names like `sel` only come in through BLIF/PLA files.
  - The tool echoes the inputs it found, so if `sel` is read as `s·e·l` the user can see it.
- [x] **B2 One function per expression file:**
  - For example `F(a,b,c) = ab' + c`. A bare expression is named `F`.
  - Nested expressions such as `(a+b)(c+d')` still count as multi-level input.
  - Designs with several outputs come only from PLA and BLIF files.
- [x] **B3 Operators:**
  - NOT: `'` `!` `~`
  - AND: `*` `&` `.` `·`, a space, or names side by side
  - OR: `+` `|`
  - XOR: `^` `⊕`
  - Constants `0` `1`, parentheses, and `#` comments.
  - Precedence: NOT > AND > XOR > OR, so `a + bc'` is `a + (b·c')`.
  - A `'` after a bracket complements the whole group: `(a+b)'`.
- [x] **B4 Minterm lists:**
  - `F(a,b,c) = m(1,3,5) + d(7)` or `F(a,b,c) = M(0,2,4) + d(7)`, with `Σ` and `Π` also accepted. The header is required.
  - Don't-cares can also follow an expression: `F(a,b,c,d) = ab + c'd + d(1,4)`.
  - `m`, `M`, `d` or `D` directly followed by brackets holding only numbers is a list. Anything else is variables, so `d(a+b)` is `d·(a+b)`.
  - An index too large for the variable count is an error, and `m` and `M` can't be mixed.
- [x] **B5 PLA:**
  - Directives: `.i .o .ilb .ob .p .e`.
  - Types: `.type f / fd`, with `fd` as the default (as in Espresso). Other types get a clear error.
  - Without `.ilb`/`.ob`, the inputs are named a, b, c, … and the outputs F0, F1, …
- [x] **B6 BLIF:** combinational only (`.model .inputs .outputs .names .end`). `.latch`, `.subckt` and `.gate` are rejected with the line number, and so are loops and undriven signals.

### C. Minimization (decided 10/11)

- [x] **C1 Primes (op 7):**
  - Found with Quine–McCluskey over ON ∪ DC: keep merging pairs that differ in one bit until nothing merges.
  - Op 7 counts the primes that cover at least one ON minterm. Primes that cover only don't-cares are listed on a separate line.
  - Example: `F(a,b,c) = m(0) + d(5,7)` has 1 prime (`a'b'c'`), plus `ac`, which covers only don't-cares.
- [x] **C2 Essential primes (op 8):** a prime is essential if it is the only prime covering some ON minterm. Don't-cares never make a prime essential.
- [x] **C3 Cover (ops 5–6):**
  1. Take the essential primes.
  2. Apply column dominance (drop minterms that get covered automatically) and row dominance (drop primes beaten by a prime at no more cost).
  3. Solve the rest exactly with branch-and-bound: branch on the minterm with the fewest covering primes, and prune any branch that can't beat the best cover so far.
  - Searching only primes is safe: any product term can be grown into a prime without adding literals.
- [x] **C4 Minimal** = fewest literals, with ties broken by fewest terms.
- [x] **C5 Literal count:** every appearance counts (`a'b + ab'` has 4).
  - Canonical SOP = #ON × n.
  - Canonical POS = #OFF × n.
  - Saved = canonical − minimized, also shown as a percentage.
  - Example: `m(0,1,2,5,6,7)` has 6 primes and 0 essential ones. It minimizes to 3 terms such as `a'b' + bc' + ac`, going from 18 to 6 literals (12 saved, 67%).
- [x] **C6 Minimized POS:** minimize F' as an SOP (same don't-cares), then apply De Morgan. For example, `a'b + ab'` → F' = `a'b' + ab` → `(a+b)(a'+b')`.
- [x] **C7 Limits and ties:**
  - Above a size limit, the cover search falls back to greedy and the output labels the result "heuristic".
  - When covers tie, one is printed, chosen the same way every run.
  - F = 0 and F = 1 print as `0` / `1`, and the Verilog ties the output to a constant.

### D. Custom ops (decided 10/11)

- [x] **D1 Op 11 checks both forms:**
  - Static-1 hazards in the minimized SOP: a pair of adjacent ON minterms (one input changes) that no single product term covers.
  - Static-0 hazards in the minimized POS: the same, using adjacent OFF minterms and sum terms.
  - Every hazard is reported along with the input that changes.
- [x] **D2 Hazard-free cover:**
  - Re-run the C3 cover solver so that every adjacent pair falls inside one term. This gives the cheapest hazard-free form, and the extra cost is shown.
  - Example: `ab' + bc` has a hazard at 101 ↔ 111. Adding `ac` fixes it.
  - Example: `a'b' + bc' + ac` has 3 hazards, and its hazard-free form needs all 6 primes (6 → 12 literals).
- [x] **D3 Op 12 delay model:** every inverter and 2-input gate costs 1 unit. A k-input gate counts as a balanced tree of ⌈log2 k⌉ levels.
- [x] **D4 Scope:**
  - Op 11 handles one input changing at a time. For two-level forms that is enough: once static-1 hazards are gone, static-0 and dynamic hazards can't occur in an SOP either.
  - Op 11 is a software result, because Vivado packs logic into LUTs and removes redundant terms like `ac`. A timing simulation in the lab is optional.
  - Op 12 builds one table comparing canonical SOP, minimized SOP, minimized POS, hazard-free SOP, and the original structure (BLIF or nested expression) when there is one.

Op 12 for `m(0,1,2,5,6,7)`:

| | NOT | AND | OR | 2-input gates | literals | delay |
|---|---|---|---|---|---|---|
| canonical SOP | 3 | 6 | 1 | 17 | 18 | 6 |
| minimized SOP | 3 | 3 | 1 | 5 | 6 | 4 |
| minimized POS | 3 | 1 | 2 | 5 | 6 | 4 |
| hazard-free SOP | 3 | 6 | 1 | 11 | 12 | 5 |

### E. Outputs

- [ ] **Text:**
  - Ops 1–4 show both the `Σm(...)` / `ΠM(...)` list and the written-out expression.
  - Long outputs are truncated unless `--full` is given.
  - `-o FILE` saves the report to a file.
- [ ] **Verilog:**
  - One module per design, with ports named after the variables.
  - Only the `not` / `and` / `or` primitives, with named wires.
  - A header comment records where the module came from.
- [ ] **Basys 3 inputs:** SW0 is the last variable (the LSB), so the switches read as the minterm number. The 7-segment display shows that number.
- [ ] **Basys 3 outputs:**
  - LED0 = minimized SOP, LED1 = minimized POS, LED2 = canonical, LED15 = all three agree.
  - For multi-output functions, one LED per output.
- [ ] **CLI:**
  - One-shot: `python -m logicsyn FILE --op N | --all`, plus `--verilog OUT.v` and `--fpga DIR`.
  - With no file it opens an interactive prompt with the commands `load`, `op N`, `all`, `verilog`, `fpga`, `help` and `quit`.
  - The input format comes from the file extension: `.pla`, `.blif`, and anything else is read as an expression. `--format` overrides it.

### F. Process

- [ ] **Branches:**
  - `main` always works.
  - Day-to-day work goes on `Lohit` and `Ritwick`.
  - Merge by PR, reviewed by the other person, so that both of us can explain all of the code at the demo.
- [ ] **Tests:** pytest on SCC. Every result is re-checked against the truth table (§6).
- [ ] **Work split:** see the owners in §5 (proposal).

## 4. Proposed architecture

```
expression / .pla / .blif
        │
        ▼  parse
Design: one BooleanFunction per output (ON / DC bitsets)
        + the original Netlist (BLIF only, used by op 12)
        │
        ▼  ops
  1–4, 9, 10   canonical forms, counts
  5–8          QM primes → essential primes → minimum cover
  11           hazards + hazard-free cover
  12           gate count / delay
        │
        ▼  minimized cover
Netlist (and / or / not) ─┬─> structural Verilog (.v)
                          └─> Basys 3 top + XDC + build.tcl ─> Vivado (lab)
```

Program 2 maps this same `Netlist` onto LUTs, so it has to stay a clean, reusable gate graph.

```
logicsyn/            Python package, run with: python -m logicsyn
  cli.py             one-shot commands + interactive prompt
  core/              bitsets, cubes, BooleanFunction, Netlist
  parsers/           expr.py, pla.py, blif.py
  ops/               canonical.py, qm.py, cover.py, hazards.py, cost.py
  verilog/           emit.py (structural .v), basys3.py (wrapper + XDC)
fpga/                build.tcl; generated/ (git-ignored)
examples/            demo inputs (.eqn, .pla, .blif)
tests/               pytest
docs/AI_USAGE.md     running AI-usage log for the README citation
```

## 5. Schedule and to-do list

| Dates | Milestone | Done when |
|---|---|---|
| Sun 10/11 – Mon 10/12 | **M0** Decide and set up | §3 is ticked, owners are agreed, the skeleton exists and pytest runs on SCC |
| Tue 10/13 – Thu 10/15 | **M1** Front end and basic ops | all three parsers and ops 1–4, 9, 10 run from the CLI |
| Tue 10/13 – Sat 10/17 | **M2** Minimization (in parallel with M1) | ops 5–8 pass the test suite |
| by Thu 10/15 | **Lab smoke test** | a hand-written gate-level module, built with `build.tcl`, runs on a Basys 3 |
| Fri 10/16 – Mon 10/19 | **M3** Custom ops and Verilog | ops 11–12 work; generated Verilog passes the SCC checks; wrapper and XDC are ready |
| Mon 10/19 – Wed 10/21 | **M4** FPGA | 3–4 generated designs are verified on the board |
| Wed 10/21 – Thu 10/22 | **M5** README and demo prep | README is complete, demo script is written, rehearsal is done |
| Fri 10/23 | **Submit** | everything is merged to `main`, the repo is public, and the link is sent before 11:59 PM |

Owners are a proposal (L = Lohit, R = Ritwick). Swap freely.

### M0 · Decide and set up (Sun 10/11 – Mon 10/12)
- [x] Create the repo with the `main` and `Lohit` branches
- [ ] Settle the open decisions in §3 (both)
- [ ] Agree the work split and create the `Ritwick` branch (both)
- [ ] Write down the shared interfaces both tracks code against: `Cube`, `BooleanFunction`, `Netlist` (both)
- [ ] Package skeleton, `.gitignore`, pytest running on SCC (L)
- [ ] Start `docs/AI_USAGE.md` (both)
- [ ] Find the lab hours and the Vivado version on the lab machines (R)

### M1 · Front end and basic ops (Tue 10/13 – Thu 10/15), owner L
- [ ] Core: bitset helpers, `Cube`, `BooleanFunction` (ON/DC/OFF, complement), `Design`
- [ ] `Netlist`: gate graph, topological order, simulation to a truth table
- [ ] Expression parser: SOP, POS, multi-level, `m()` / `M()` / `d()` lists, `F(a,b,c)` headers
- [ ] PLA parser
- [ ] BLIF parser
- [ ] Ops 1–4 and 9–10
- [ ] CLI: `--op` / `--all`, `-o FILE`, interactive prompt
- [ ] Example inputs in `examples/`; tests for the parsers and ops

### M2 · Minimization (Tue 10/13 – Sat 10/17), owner R
- [ ] Quine–McCluskey primes with don't-cares → op 7
- [ ] Essential primes → op 8
- [ ] Cover solver: essential primes, dominance, branch-and-bound, greedy fallback
- [ ] Op 5 (minimized SOP + literals saved) and op 6 (minimized POS via F' + literals saved)
- [ ] Edge cases: F = 0, F = 1, every minterm a don't-care, one variable
- [ ] Tests: the cover equals the function, PI/EPI counts match known answers, and minimality is confirmed by brute force for ≤ 4 inputs

### Lab smoke test (by Thu 10/15), both
- [ ] Hand-written 3-input gate-level module + Basys 3 wrapper + XDC
- [ ] Run `build.tcl` in batch mode on a lab machine, program the board, check the switches and LEDs

### M3 · Custom ops and Verilog (Fri 10/16 – Mon 10/19)
- [ ] Op 11: hazard report + hazard-free cover (R)
- [ ] Op 12: gate count / delay comparison table (R)
- [ ] Minimized cover → `Netlist` of `and` / `or` / `not`, sharing product terms across outputs (L)
- [ ] Structural Verilog emitter (L)
- [ ] SCC check: Verilator lint + an exhaustive testbench compared against the truth table (L)
- [ ] Basys 3 wrapper and XDC generator, `fpga/build.tcl` (L)

### M4 · FPGA (Mon 10/19 – Wed 10/21), both
- [ ] Pick the demo designs: an SOP expression, one with don't-cares, a multi-output PLA and a BLIF circuit
- [ ] Generate, build and program each one, and check every switch setting against the truth table
- [ ] Keep the bitstreams and photos as a backup

### M5 · README and demo prep (Wed 10/21 – Thu 10/22), both
- [ ] README: description, architecture, folder layout, step-by-step build/run/usage (SCC + lab), examples, AI-usage citation
- [ ] A pass over the comments and module docstrings
- [ ] A demo script that runs all 12 ops on our own test cases
- [ ] Rehearse the code walkthrough, with each person explaining the other's modules
- [ ] Merge to `main` and tag `v1.0`

### Submit (Fri 10/23)
- [ ] Make the repo public (it's private now; Ritwick owns it)
- [ ] Send the link to Prof. Densmore before 11:59 PM
- [ ] Book a demo slot once the sign-up sheet is posted

## 6. Testing

- **The truth table is the reference.** Every result is evaluated on all 2^n inputs and must match the ON-set, ignoring don't-cares. This covers the canonical forms, minimized covers, the hazard-free cover, the netlist and the Verilog.
- **Known answers.** For example, `F(a,b,c) = m(0,1,2,5,6,7)` has 6 PIs and 0 EPIs. Its minimum is 3 terms with 6 literals, which saves 12 of the 18 canonical literals. We'll add the usual textbook 4-variable problems as well.
- **Brute-force minimality** for ≤ 4 inputs, plus seeded random functions up to 10 inputs, with and without don't-cares.
- **Verilog on SCC:** Verilator lint and an exhaustive simulation, with Yosys as a second check.

## 7. If we fall behind

**Must have:**
- SOP expression input and BLIF circuit input
- all 12 ops
- structural Verilog
- the FPGA demo
- the README with the AI citation

**Cut in this order:**
1. The 7-segment display.
2. The POS side of op 11.
3. The original-circuit column in op 12.
4. PLA input altogether.

## 8. Risks

| Risk | Mitigation |
|---|---|
| 12 days left and nothing built | parallel tracks from Tue 10/13; the cut list in §7 |
| Vivado only runs in the lab | lab smoke test by Thu 10/15; keep the bitstreams |
| Exact cover too slow on large functions | greedy fallback, labelled in the output; demo with ≤ 10 inputs |
| Both of us must defend every line | partner-reviewed PRs, walkthrough rehearsal, AI-usage log |
| The two tracks drift apart | agree the shared interfaces in M0; `main` must always pass the tests |
