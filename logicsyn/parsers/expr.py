"""Parser for one Boolean function per file: an expression or a minterm list."""
import re

from ..core.bits import MAX_INPUTS, full_mask
from ..core.function import BooleanFunction, Design
from ..core.netlist import Netlist

_TOKEN = re.compile(r"""
    (?P<space>\s+)
  | (?P<list>(?:[mMdD]|[Σ∑]m?|[Π∏]M?)\(\s*(?:\d+\s*(?:,\s*\d+\s*)*)?\))
  | (?P<name>[A-Za-z][0-9]*)
  | (?P<const>[01])
  | (?P<op>[()'!~*&.·+|^⊕=;,])
""", re.VERBOSE)


def _line(text, pos):
    return f"line {text.count(chr(10), 0, pos) + 1}: "


def _tokenize(text):
    toks, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"{_line(text, pos)}unexpected character {text[pos]!r}")
        if m.lastgroup != "space":
            toks.append((m.lastgroup, m.group(), pos))
        pos = m.end()
    return toks


class _Parser:
    """Recursive descent with precedence NOT > AND > XOR > OR."""

    def __init__(self, text, toks):
        self.text, self.toks, self.i = text, toks, 0
        self.names = set()

    def error(self, msg):
        pos = self.toks[self.i][2] if self.i < len(self.toks) else len(self.text)
        return ValueError(_line(self.text, pos) + msg)

    def at(self, *ops):
        return self.i < len(self.toks) and self.toks[self.i][1] in ops

    def chain(self, ops, sub, kind):
        items = [sub()]
        while self.at(*ops):
            self.i += 1
            items.append(sub())
        return items[0] if len(items) == 1 else (kind, items)

    def expr(self):
        return self.chain(("+", "|"), self.xor, "OR")

    def xor(self):
        return self.chain(("^", "⊕"), self.product, "XOR")

    def product(self):
        items = [self.unary()]
        while True:
            if self.at("*", "&", ".", "·"):
                self.i += 1
            elif not self.starts_operand():
                break
            items.append(self.unary())
        return items[0] if len(items) == 1 else ("AND", items)

    def starts_operand(self):
        if self.i >= len(self.toks):
            return False
        kind, text, _ = self.toks[self.i]
        return kind in ("name", "const") or text in ("(", "!", "~")

    def unary(self):
        if self.at("!", "~"):
            self.i += 1
            return ("NOT", self.unary())
        node = self.primary()
        while self.at("'"):
            self.i += 1
            node = ("NOT", node)
        return node

    def primary(self):
        if self.i >= len(self.toks):
            raise self.error("the expression ends too early")
        kind, text, _ = self.toks[self.i]
        self.i += 1
        if kind == "name":
            self.names.add(text)
            return ("VAR", text)
        if kind == "const":
            return ("CONST", int(text))
        if text == "(":
            node = self.expr()
            if not self.at(")"):
                raise self.error("expected ')'")
            self.i += 1
            return node
        self.i -= 1
        raise self.unexpected()

    def unexpected(self):
        kind, text, _ = self.toks[self.i]
        if kind == "list":
            return self.error("a list must be the whole right side, with d(...) last")
        return self.error(f"unexpected {text!r}")


def _split_header(toks):
    """Return (function name, header inputs or None, right-side tokens)."""
    eq = next((k for k, t in enumerate(toks) if t[1] == "="), None)
    if eq is None:
        return "F", None, toks
    lhs, rhs = toks[:eq], toks[eq + 1:]
    words = [t[1] for t in lhs]
    if len(lhs) == 1 and lhs[0][0] == "name":
        return words[0], None, rhs
    names = words[2:-1:2]
    if (len(lhs) >= 3 and lhs[0][0] == "name" and all(t[0] == "name" for t in lhs[2:-1:2])
            and "".join(words) == f"{words[0]}({','.join(names)})"):
        if len(set(names)) != len(names):
            raise ValueError("an input is listed twice in the header")
        return words[0], names, rhs
    raise ValueError("the left side must look like F or F(a,b,c)")


def _bits(tok, n, what):
    idx = [int(x) for x in re.findall(r"\d+", tok[tok.index("("):])]
    bad = [m for m in idx if m >= 1 << n]
    if bad:
        raise ValueError(f"{what} {bad[0]} is too large for {n} inputs")
    return sum(1 << m for m in set(idx))


def _build(net, node, out=None):
    """Add the gates for one syntax-tree node; the root gets the name `out`."""
    kind, arg = node
    if kind == "VAR":
        return net.add(out, "BUF", [arg]) if out else arg
    if kind == "CONST":
        op, fanins = ("CONST1" if arg else "CONST0"), []
    elif kind == "NOT":
        op, fanins = "NOT", [_build(net, arg)]
    else:
        op, fanins = kind, [_build(net, x) for x in arg]
    return net.add(out, op, fanins) if out else net.gate(op, fanins)


def _natural(name):
    return name[0], int(name[1:]) if len(name) > 1 else -1


def parse_expr(text, name=None):
    text = re.sub(r"#[^\n]*", "", text)
    toks = _tokenize(text)
    if toks and toks[-1][1] == ";":
        toks.pop()
    if any(t[1] == ";" for t in toks) or sum(t[1] == "=" for t in toks) > 1:
        raise ValueError("an expression file holds one function; use PLA or BLIF for several outputs")
    fname, header, toks = _split_header(toks)

    dc_tok = None
    if len(toks) >= 2 and toks[-1][0] == "list" and toks[-1][1][0] in "dD" and toks[-2][1] == "+":
        dc_tok, toks = toks[-1][1], toks[:-2]
    if (dc_tok or (toks and toks[0][0] == "list")) and header is None:
        raise ValueError("a list needs a header like F(a,b,c) = m(1,3)")

    if len(toks) == 1 and toks[0][0] == "list" and toks[0][1][0] not in "dD":
        n = len(header)
        kind = toks[0][1][0]
        idx = _bits(toks[0][1], n, "minterm" if kind in "mΣ∑" else "maxterm")
        on = idx if kind in "mΣ∑" else full_mask(n) & ~idx
        dc = _bits(dc_tok, n, "don't-care") if dc_tok else 0
        return Design(name or fname, header, [BooleanFunction(fname, header, on, dc)])

    p = _Parser(text, toks)
    tree = p.expr()
    if p.i != len(toks):
        raise p.unexpected()
    if header is not None:
        unknown = sorted(p.names - set(header))
        if unknown:
            raise ValueError(f"{', '.join(unknown)} not listed in the header")
        inputs = header
    else:
        inputs = sorted(p.names, key=_natural)
    if len(inputs) > MAX_INPUTS:
        raise ValueError(f"{len(inputs)} inputs; the limit is {MAX_INPUTS}")
    if fname in inputs:
        raise ValueError(f"{fname} is both the function name and an input")

    net = Netlist(inputs, [fname])
    _build(net, tree, fname)
    dc = _bits(dc_tok, len(inputs), "don't-care") if dc_tok else 0
    f = BooleanFunction(fname, inputs, net.simulate()[fname], dc, source=net)
    return Design(name or fname, inputs, [f])
