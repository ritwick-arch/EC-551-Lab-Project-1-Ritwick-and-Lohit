"""Command line: one-shot runs and the interactive prompt."""
import argparse
import sys
from pathlib import Path

from .ops import OPS
from .parsers import PARSERS, load_file, parse_expr

LIMIT = 200
HELP = """\
commands:
  load FILE      load an expression, .pla or .blif file
  op N [N ...]   run ops 1-12 on every output
  all            run all 12 ops
  help           show this list
  quit           leave
anything else is read as an expression, e.g.  F(a,b,c) = m(1,3,5) + d(7)"""


def describe(design):
    outputs = ", ".join(f.name for f in design.functions)
    return f"Loaded {design.name}: inputs {', '.join(design.inputs) or '(none)'}; outputs {outputs}"


def report(design, ops):
    parts = []
    for f in design.functions:
        parts += [OPS[k](f) if k in OPS else f"Op {k}  not implemented yet" for k in ops]
    return "\n\n".join(parts)


def shorten(text):
    """Cut very long lines at a term boundary."""
    lines, cut = [], False
    for line in text.splitlines():
        if len(line) > LIMIT:
            i = max(line.rfind(" + ", 0, LIMIT), line.rfind(")(", 0, LIMIT) + 1)
            line = line[:i if i > 0 else LIMIT] + " ..."
            cut = True
        lines.append(line)
    if cut:
        lines.append("(long lines shortened; run with --full to see everything)")
    return "\n".join(lines)


def _op_numbers(text):
    words = text.split()
    if not words or not all(w.isdigit() and 1 <= int(w) <= 12 for w in words):
        raise ValueError("usage: op N [N ...] with N from 1 to 12")
    return [int(w) for w in words]


def interactive():
    print("logicsyn: type 'help' for commands")
    design = None
    while True:
        try:
            line = input("logicsyn> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        cmd, _, rest = line.partition(" ")
        try:
            if not line:
                continue
            if cmd in ("quit", "exit"):
                return 0
            if cmd == "help":
                print(HELP)
            elif cmd == "load":
                design = load_file(rest.strip())
                print(describe(design))
            elif cmd in ("op", "all"):
                if design is None:
                    raise ValueError("load a function first")
                print(shorten(report(design, list(range(1, 13)) if cmd == "all" else _op_numbers(rest))))
            else:
                design = parse_expr(line)
                print(describe(design))
        except (OSError, ValueError) as e:
            print(f"error: {e}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="logicsyn", description="EC551 logic synthesis engine.")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("file", nargs="?", help="input file: .pla, .blif, or anything else as one expression")
    src.add_argument("-e", "--expr", help="an expression to use instead of a file")
    ap.add_argument("--format", choices=sorted(PARSERS), help="override the format picked from the extension")
    ap.add_argument("--op", type=int, action="append", choices=range(1, 13), metavar="N",
                    help="run op N (repeatable)")
    ap.add_argument("--all", action="store_true", help="run all 12 ops (the default)")
    ap.add_argument("-o", "--output", help="also save the report to this file")
    ap.add_argument("--full", action="store_true", help="don't shorten long lines")
    args = ap.parse_args(argv)
    if args.file is None and args.expr is None:
        return interactive()
    try:
        design = parse_expr(args.expr) if args.expr is not None else load_file(args.file, args.format)
    except (OSError, ValueError) as e:
        sys.exit(f"error: {e}")
    ops = list(range(1, 13)) if args.all or not args.op else args.op
    text = describe(design) + "\n\n" + report(design, ops)
    if not args.full:
        text = shorten(text)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0
