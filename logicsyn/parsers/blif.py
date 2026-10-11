"""Parser for combinational BLIF (.model, .inputs, .outputs, .names, .end)."""
from ..core.bits import MAX_INPUTS
from ..core.function import BooleanFunction, Design
from ..core.netlist import Netlist

_FLIP = {"BUF": "NOT", "NOT": "BUF", "CONST0": "CONST1", "CONST1": "CONST0"}


def _lines(text):
    """Yield (line number, words), dropping comments and joining '\\' continuations."""
    words, start = [], None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].rstrip()
        more = line.endswith("\\")
        start = start or lineno
        words += (line[:-1] if more else line).split()
        if not more:
            if words:
                yield start, words
            words, start = [], None
    if words:
        yield start, words


def _add_cover(net, ins, out, rows):
    """Turn one .names block into NOT/AND/OR gates driving `out`."""
    terms, polarity = [], None
    for lineno, words in rows:
        if len(words) != (2 if ins else 1) or (ins and len(words[0]) != len(ins)):
            raise ValueError(f"line {lineno}: expected {len(ins)} input characters and one output bit")
        pattern, bit = (words[0], words[1]) if ins else ("", words[0])
        if bit not in ("0", "1") or polarity not in (None, bit):
            raise ValueError(f"line {lineno}: the output column must be all 1 or all 0")
        polarity = bit
        if set(pattern) - set("01-"):
            raise ValueError(f"line {lineno}: bad cover row {pattern!r}")
        terms.append([(x, ch == "1") for x, ch in zip(ins, pattern) if ch != "-"])

    def sig(x, pos):
        return x if pos else net.gate("NOT", [x])

    if not terms:
        op, fanins = "CONST0", []
    elif not all(terms):
        op, fanins = "CONST1", []
    elif len(terms) == 1 and len(terms[0]) == 1:
        x, pos = terms[0][0]
        op, fanins = ("BUF" if pos else "NOT"), [x]
    elif len(terms) == 1:
        op, fanins = "AND", [sig(*lit) for lit in terms[0]]
    else:
        op, fanins = "OR", [sig(*t[0]) if len(t) == 1 else net.gate("AND", [sig(*lit) for lit in t])
                            for t in terms]
    if polarity == "0":
        op, fanins = (_FLIP[op], fanins) if op in _FLIP else ("NOT", [net.gate(op, fanins)])
    net.add(out, op, fanins)


def parse_blif(text, name="blif"):
    model, inputs, outputs, blocks = name, [], [], []
    for lineno, words in _lines(text):
        key = words[0]
        if key == ".model":
            model = words[1] if len(words) > 1 else model
        elif key == ".inputs":
            inputs += words[1:]
        elif key == ".outputs":
            outputs += words[1:]
        elif key == ".names":
            if len(words) < 2:
                raise ValueError(f"line {lineno}: .names needs an output signal")
            blocks.append((lineno, words[1:-1], words[-1], []))
        elif key == ".end":
            break
        elif key.startswith("."):
            raise ValueError(f"line {lineno}: {key} is not supported (combinational .names only)")
        elif blocks:
            blocks[-1][3].append((lineno, words))
        else:
            raise ValueError(f"line {lineno}: cover row outside a .names block")

    if len(inputs) > MAX_INPUTS:
        raise ValueError(f"{len(inputs)} inputs; the limit is {MAX_INPUTS}")
    if len(set(inputs)) != len(inputs):
        raise ValueError("an input is listed twice")
    net = Netlist(inputs, outputs)
    for lineno, ins, out, rows in blocks:
        try:
            _add_cover(net, ins, out, rows)
        except ValueError as e:
            msg = str(e)
            raise ValueError(msg if msg.startswith("line") else f"line {lineno}: {msg}") from None
    tts = net.simulate()
    return Design(model, inputs, [BooleanFunction(o, inputs, tts[o], source=net) for o in outputs])
