# Program 1 Plan: Logic Synthesis Engine

**EC551, Fall 2026 · Ritwick & Lohit · Due Fri 10/23, 11:59 PM**: a public GitHub link sent to Prof. Densmore, followed by a live demo.

**Status (Tue 10/20):** M0–M3 are done. All 12 ops run from the CLI using Ritwick's implementation, adopted as is on 10/20. `--verilog` and `--fpga` write the structural Verilog and the Nexys A7 constraints. Next: the lab (M4), then the README.

**How we work:** settle the decisions first, then build one milestone at a time. Build only what the assignment asks for.

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
| FPGA | synthesize the generated Verilog and run it on the board; hand-written wrappers allowed | Nexys A7 (Nexys 4 DDR): switches → inputs, LEDs → outputs |
| Repo | public; well-structured, commented code; README with architecture, folder layout, build/run/usage steps | see §4 and M5 |
| AI policy | cite AI use in the README or code headers; be ready to explain and defend all of it | an "AI usage" section in the README |
| Demo | run all the ops on our own test cases; walk through the code and key decisions; show the generated Verilog running live on the FPGA | demo script + rehearsal (M5) |

## 2. Already decided (9/28)

- **Language and interface:** Python 3 (3.12 on SCC), command line only, no GUI.
- **Input formats:** EQN-style expressions, Espresso PLA and BLIF. No JSON.
- **Custom ops:**
  - Op 11: static-hazard detection plus a hazard-free cover.
  - Op 12: gate count plus delay estimate.
- **Board and tools:**
  - Board (corrected 10/20): Nexys A7 / Nexys 4 DDR (xc7a100tcsg324-1), not the Basys 3.
  - Vivado 2024.1 runs only on the lab's Windows machines. In the demo, a new Vivado project is created by hand from the generated `.v` and `.xdc`, so there is no build script.
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
  - When more than 24 candidate primes remain after the reductions, the cover search uses greedy instead. The output does not say so.
  - Speed is not a concern (decided 10/20). A random 8-input function takes about 27 s for `--all`.
  - When covers tie, one is printed, chosen the same way every run.
  - F = 0 and F = 1 print as `0` / `1`, and the Verilog ties the output to a constant.

### D. Custom ops (decided 10/11)

- [x] **D1 Op 11 checks both forms:**
  - Static-1 hazards in the minimized SOP: a pair of adjacent ON minterms (one input changes) that no single product term covers.
  - Static-0 hazards in the minimized POS: the same, using adjacent OFF minterms and sum terms.
  - Every hazard is reported along with the input that changes.
- [x] **D2 Hazard-free cover:**
  - For each hazard, add the term that covers both minterms, and show the extra literals.
  - Example: `ab' + bc` has a hazard at 101 ↔ 111. Adding `ac` fixes it.
  - Example: `a'b' + bc' + ac` has 3 hazards, and its hazard-free form needs all 6 primes (6 → 12 literals).
- [x] **D3 Op 12 delay model:** every inverter and 2-input gate costs 1 unit. A k-input gate counts as a balanced tree of ⌈log2 k⌉ levels.
- [x] **D4 Scope:**
  - Op 11 handles one input changing at a time. For two-level forms that is enough: once static-1 hazards are gone, static-0 and dynamic hazards can't occur in an SOP either.
  - Op 11 is a software result, because Vivado packs logic into LUTs and removes redundant terms like `ac`. A timing simulation in the lab is optional.
  - Op 12 builds one table comparing canonical SOP, minimized SOP, minimized POS and hazard-free SOP. AND and OR are counted as 2-input gates.

Op 12 for `m(0,1,2,5,6,7)`:

| | NOT | AND | OR | 2-input gates | literals | delay |
|---|---|---|---|---|---|---|
| canonical SOP | 3 | 12 | 5 | 17 | 18 | 6 |
| minimized SOP | 3 | 3 | 2 | 5 | 6 | 4 |
| minimized POS | 3 | 1 | 4 | 5 | 6 | 4 |
| hazard-free SOP | 3 | 6 | 5 | 11 | 12 | 5 |

### E. Outputs (decided 10/11)

- [x] **E1 Report:**
  - Each op gets a numbered heading.
  - Ops 1–4 show both the `Σm(...)` / `ΠM(...)` list and the written-out expression, with don't-cares listed separately.
  - Long outputs are shortened unless `--full` is given.
  - `-o FILE` saves the report to a file.
- [x] **E2 Verilog:**
  - One module per design, with ports named after the variables.
  - Only the `not` / `and` / `or` primitives: one shared `not` per complemented input, one `and` per product term, and one `or` per output.
  - Named wires, plus a header comment saying where the module came from.
- [x] **E3 Nexys A7, only what the assignment asks for:**
  - Switches drive the inputs. SW0 is the last variable (the LSB), so the switches read as the minterm number.
  - One LED per output of the minimized circuit.
  - SW8 and SW9 are in a 1.8 V bank, so they use LVCMOS18; every other pin uses LVCMOS33.
- [x] **E4 Command line:**
  - One-shot: `python -m logicsyn FILE --all` (or `--op N`, repeatable), plus `--verilog OUT.v` and `--fpga DIR`. `-e "F(a,b,c) = ..."` passes an expression directly.
  - With no arguments it opens a `logicsyn>` prompt with `load`, `op N`, `all`, `verilog`, `fpga`, `help` and `quit`. Typing an expression at the prompt loads it.
  - The input format comes from the file extension: `.pla`, `.blif`, and anything else is read as an expression. `--format` overrides it.
  - With `--verilog` or `--fpga`, the report is printed only if `--op` or `--all` is also given.
- [x] **E5 Board build:**
  - `--fpga DIR` writes `<module>.v` and `<module>.xdc`. The XDC maps the module's own ports to the switches and LEDs, as in the prelab, so there is no wrapper.
  - In the lab: create a project for xc7a100tcsg324-1, add the two files, generate the bitstream, and program the board from the Hardware Manager.
  - The module is named after the design, with `_sop` added when that name is also a port name (Verilator rejects that clash).
- **Not doing:** 7-segment display, side-by-side comparison circuits, a self-test button, or a `--steps` mode.

### F. Process (decided 10/11)

- [x] **F1 Work split** (needs Ritwick's OK):
  - Lohit: core, parsers, command line, ops 1–4 and 9–10, Verilog and board files.
  - Ritwick: minimization (ops 5–8) and ops 11–12.
  - Both: README and demo prep.
- [x] **F2 Branches:**
  - Lohit works on `Lohit`. Ritwick works on `Ritwick`, branched from `Lohit` once the shared core exists.
  - Commit and push small changes often.
  - `main` stays untouched until everything works. Then it is merged once, through a pull request, before the repo goes public.
- [x] **F3 AI citation:** a short "AI usage" section in the README saying which tools were used and for what.
- [x] **F4 Tests:**
  - pytest checks every op against the truth table (§6).
  - Verilator lints and simulates the generated Verilog on SCC before lab time.
- [x] **F5 Code style:**
  - Comments are minimal: one sentence at most, and only where the code isn't obvious.
  - Notes on what each file does go in `docs/`, which is git-ignored and stays local.

## 4. Proposed architecture

```
expression / .pla / .blif
        │
        ▼  parse
Design: one BooleanFunction per output (ON / DC bitsets)
        + the original Netlist (BLIF or nested expression, used by op 12)
        │
        ▼  ops
  1–4, 9, 10   canonical forms, counts
  5–8          QM primes → essential primes → minimum cover
  11           hazards + hazard-free cover
  12           gate count / delay
        │
        ▼  minimized cover
Netlist (and / or / not) ─┬─> structural Verilog (.v)
                          └─> Nexys A7 XDC ─> Vivado project (lab)
```

Program 2 maps this same `Netlist` onto LUTs, so it has to stay a clean, reusable gate graph.

```
logicsyn/            Python package, run with: python -m logicsyn
  cli.py             one-shot commands + interactive prompt
  core/              bitsets, cubes, BooleanFunction, Netlist
  parsers/           expr.py, pla.py, blif.py
  ops/               canonical.py, qm.py, cover.py, hazards.py, cost.py
  verilog/           emit.py (structural .v), nexys.py (Nexys A7 XDC)
examples/            demo inputs (.eqn, .pla, .blif)
out/                 generated Verilog and board files (git-ignored)
tests/               pytest
docs/                local notes on what each file does (git-ignored)
```

### Shared interfaces (M0, for Ritwick to review)

Everything both tracks import lives in `logicsyn/core/`. Lohit writes it first (Tue 10/13), and the ops code against these names. Python 3.10+, standard library only (pytest for tests).

**Conventions**
- A truth table is an `int` with bit `m` set when minterm `m` is in the set (A1).
- Input `i` (0 = first) is bit `n-1-i` of a minterm index, so the first input is the MSB (A2).
- A cover is a `list[Cube]`. A POS is stored as the cover of F' (C6); `format_pos` prints it as a product of sums.

```python
# core/bits.py
MAX_INPUTS = 16
def full_mask(n: int) -> int: ...            # all 2**n minterm bits set
def var_tt(n: int, i: int) -> int: ...       # truth table of input i
def minterms(tt: int) -> list[int]: ...      # set bits, ascending

# core/cube.py
class Cube(NamedTuple):
    mask: int    # bit set = variable appears in the term
    value: int   # polarity of those variables: 1 = x, 0 = x'
    def contains(self, m: int) -> bool: ...  # (m & mask) == value
    literals: int                            # property: mask.bit_count()
    def tt(self, n: int) -> int: ...         # truth table of the term
    def from_pattern(p: str) -> "Cube": ...  # classmethod: "1-0" -> a c'
    def minterm(m: int, n: int) -> "Cube": ...   # classmethod: all n literals
    def lits(self, n: int) -> list[tuple[int, bool]]: ...   # (input index, positive?)
    def pattern(self, n: int) -> str: ...

# core/function.py
@dataclass
class BooleanFunction:
    name: str
    inputs: list[str]                 # order fixes the bit numbering
    on: int                           # ON-set truth table
    dc: int = 0                       # don't-care truth table, disjoint from on
    source: "Netlist | None" = None   # original structure (A5), kept for reference
    n: int                            # property: len(inputs)
    off: int                          # property: full_mask(n) & ~(on | dc)
    def complement(self) -> "BooleanFunction": ...   # ON and OFF swapped, same DC

@dataclass
class Design:                         # what every parser returns
    name: str
    inputs: list[str]
    functions: list[BooleanFunction]  # one per output (A3)

# core/netlist.py
GATES = ("NOT", "AND", "OR", "XOR", "BUF", "CONST0", "CONST1")
@dataclass
class Node:
    name: str
    op: str                           # one of GATES
    fanins: list[str]                 # input or node names
class Netlist:
    inputs: list[str]
    outputs: list[str]
    nodes: dict[str, Node]
    def add(self, name: str, op: str, fanins: list[str]) -> str: ...
    def gate(self, op: str, fanins: list[str]) -> str: ...  # auto-named, reuses an identical gate
    def topo_order(self) -> list[Node]: ...       # raises on loops and undriven signals
    def simulate(self) -> dict[str, int]: ...     # output name -> truth table
def sop_netlist(covers: dict[str, list[Cube]], inputs: list[str]) -> Netlist: ...   # M3, shares inverters and AND gates
def pos_netlist(covers: dict[str, list[Cube]], inputs: list[str]) -> Netlist: ...   # M3, covers of F'

# core/format.py
def format_sop(cover: list[Cube], inputs: list[str]) -> str: ...   # "a'b + c", or "0"
def format_pos(cover: list[Cube], inputs: list[str]) -> str: ...   # cover of F' -> "(a + b')(c)", or "1"

# ops/__init__.py
OPS: dict[int, Callable[[BooleanFunction], str]]   # op number -> report text; the CLI calls it per output

# ops/qm.py, ops/cover.py, ops/minimize.py (Ritwick)
def primes(f: BooleanFunction) -> list[Cube]: ...                  # primes of ON ∪ DC that cover an ON minterm
def dc_only_primes(f: BooleanFunction) -> list[Cube]: ...
def essentials(f: BooleanFunction, primes: list[Cube]) -> list[Cube]: ...
def min_cover(f: BooleanFunction, primes: list[Cube]) -> tuple[list[Cube], bool]: ...   # (cover, exact)
def minimize_sop(f: BooleanFunction) -> list[Cube]: ...            # used by the Verilog emitter
def minimize_pos(f: BooleanFunction) -> list[Cube]: ...            # cover of F'

# ops/hazards.py, ops/cost.py (Ritwick)
def static1_hazards(f: BooleanFunction, cover: list[Cube]) -> list[tuple[int, int]]: ...   # adjacent ON minterm pairs
def static0_hazards(f: BooleanFunction, pos_cover: list[Cube]) -> list[tuple[int, int]]: ...
def hazard_free_cover(f: BooleanFunction, cover: list[Cube]) -> list[Cube]: ...
def estimate_cost(cover: list[Cube], form: str = "sop") -> dict: ...   # gate counts and delay
```

BLIF `.names` blocks are expanded into NOT/AND/OR gates while parsing, so a `Netlist` only ever holds the gates in `GATES`.

## 5. Schedule and to-do list

| Dates | Milestone | Done when |
|---|---|---|
| Sun 10/11 – Mon 10/12 | **M0** Decide and set up | §3 is ticked, Ritwick has agreed to the split, the skeleton exists and pytest runs on SCC |
| Tue 10/13 – Thu 10/15 | **M1** Front end and basic ops | all three parsers and ops 1–4, 9, 10 run from the CLI |
| Tue 10/13 – Sun 10/18 | **M2** Minimization (in parallel with M1) | ops 5–8 and 11–12 run from the CLI and pass the test suite |
| Tue 10/20 – Wed 10/21 | **M3** Verilog | generated Verilog passes the SCC checks; the XDC is ready |
| Wed 10/21 – Thu 10/22 | **M4** FPGA | 3–4 generated designs are verified on the board |
| Thu 10/22 | **M5** README and demo prep | README is complete, demo script is written, rehearsal is done |
| Fri 10/23 | **Submit** | the work is merged into `main` through one pull request, the repo is public, and the link is sent before 11:59 PM |

Owners follow the F1 split (L = Lohit, R = Ritwick), pending Ritwick's OK.

### M0 · Decide and set up (Sun 10/11 – Mon 10/12)
- [x] Create the repo with the `main` and `Lohit` branches
- [x] Settle the design decisions in §3
- [x] Get Ritwick's OK on the split (F1); Ritwick branches `Ritwick` off `Lohit` once the core exists
- [x] Write down the shared interfaces both tracks code against: `Cube`, `BooleanFunction`, `Netlist` (see §4)
- [x] Ritwick reviews the interfaces in §4
- [x] Package skeleton, `.gitignore` (including `docs/`), pytest running on SCC (L)
- [ ] Find the lab hours and the Vivado version on the lab machines (R)

### M1 · Front end and basic ops (Tue 10/13 – Thu 10/15), owner L, done Sun 10/11
- [x] Core: bitset helpers, `Cube`, `BooleanFunction` (ON/DC/OFF, complement), `Design`
- [x] `Netlist`: gate graph, topological order, simulation to a truth table
- [x] Expression parser: SOP, POS, multi-level, `m()` / `M()` / `d()` lists, `F(a,b,c)` headers
- [x] PLA parser
- [x] BLIF parser
- [x] Ops 1–4 and 9–10
- [x] CLI: `--op` / `--all`, `-o FILE`, interactive prompt
- [x] Example inputs in `examples/`; tests for the parsers and ops

### M2 · Minimization (Tue 10/13 – Sun 10/18), owner R, done 10/17, adopted as is on 10/20
- [x] Quine–McCluskey primes with don't-cares → op 7 (R)
- [x] Essential primes → op 8 (R)
- [x] Cover solver: essential primes, dominance, branch-and-bound, greedy fallback (R)
- [x] Minimized SOP and POS, hazards, gate cost and delay (R)
- [x] Report text for ops 5–8, 11 and 12, registered in `OPS` (R)
- [x] Edge cases: F = 0, F = 1, every minterm a don't-care, one variable
- [x] Tests: the cover equals the function, PI/EPI counts match known answers, and minimality is confirmed by brute force for ≤ 4 inputs

### M3 · Verilog (Tue 10/20), owner L, done 10/20
- [x] Minimized cover → `Netlist` of `and` / `or` / `not`, sharing product terms across outputs (L)
- [x] Structural Verilog emitter (L)
- [x] SCC check: Verilator lint, plus Yosys reading the `.v` back and printing its truth table for comparison (L)
- [x] Generator for the Nexys A7 XDC; the hand-written Basys 3 smoke test was removed (L)

### M4 · FPGA (Wed 10/21 – Thu 10/22), both
- [ ] Pick the demo designs: an SOP expression, one with don't-cares, a multi-output PLA and a BLIF circuit
- [ ] Generate, build and program each one, and check every switch setting against the truth table
- [x] 10/20: the generated `two_outputs.v` + `.xdc` build to a bitstream in Vivado (Lohit, own machine)
- [ ] Keep the bitstreams as a backup

### M5 · README and demo prep (Thu 10/22), both
- [ ] README: description, architecture, folder layout, step-by-step build/run/usage (SCC + lab), examples, and an "AI usage" section
- [ ] A final pass over the comments: one sentence each, only where needed
- [ ] A demo script that runs all 12 ops on our own test cases
- [ ] Rehearse the code walkthrough, with each person explaining the other's modules
- [ ] Combine `Ritwick` and `Lohit`, then merge into `main` through one pull request that the other person reviews

### Submit (Fri 10/23)
- [ ] Make the repo public (it's private now; Ritwick owns it)
- [ ] Send the link to Prof. Densmore before 11:59 PM
- [ ] Book a demo slot once the sign-up sheet is posted

## 6. Testing

- **The truth table is the reference.** Every result is evaluated on all 2^n inputs and must match the ON-set, ignoring don't-cares. This covers the canonical forms, minimized covers, the hazard-free cover, the netlist and the Verilog.
- **Known answers.** For example, `F(a,b,c) = m(0,1,2,5,6,7)` has 6 PIs and 0 EPIs. Its minimum is 3 terms with 6 literals, which saves 12 of the 18 canonical literals. We'll add the usual textbook 4-variable problems as well.
- **Brute-force minimality** for ≤ 4 inputs, plus seeded random functions up to 10 inputs, with and without don't-cares.
- **Verilog on SCC:** Verilator lint, plus Yosys evaluating every input of the written `.v` (`eval -table`) and comparing against the truth table.

## 7. If we fall behind

**Must have:**
- SOP expression input and BLIF circuit input
- all 12 ops
- structural Verilog
- the FPGA demo
- the README with the AI citation

**Cut:** the original-structure row in op 12.

## 8. Risks

| Risk | Mitigation |
|---|---|
| 12 days left and nothing built | parallel tracks from Tue 10/13; the cut list in §7 |
| Vivado only runs in the lab | check the generated files on SCC first (Verilator, Yosys); build them on the first lab visit; keep the bitstreams |
| Exact cover too slow on large functions | accepted on 10/20; demo with small functions |
| Both of us must defend every line | each reviews the other's code before the final merge; walkthrough rehearsal in M5 |
| The two tracks drift apart | agree the shared interfaces in M0; Ritwick builds on the core from `Lohit`; tests run on both branches |
