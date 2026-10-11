"""Gate-level netlists that can be ordered and simulated."""
from dataclasses import dataclass
from functools import reduce
from operator import and_, or_, xor

from .bits import full_mask, var_tt

_EVAL = {
    "NOT": lambda ins, full: full & ~ins[0],
    "AND": lambda ins, full: reduce(and_, ins, full),
    "OR": lambda ins, full: reduce(or_, ins, 0),
    "XOR": lambda ins, full: reduce(xor, ins, 0),
    "BUF": lambda ins, full: ins[0],
    "CONST0": lambda ins, full: 0,
    "CONST1": lambda ins, full: full,
}
GATES = tuple(_EVAL)


@dataclass
class Node:
    name: str
    op: str
    fanins: list[str]


class Netlist:
    def __init__(self, inputs, outputs=()):
        self.inputs = list(inputs)
        self.outputs = list(outputs)
        self.nodes = {}
        self._shared = {}

    def add(self, name, op, fanins):
        if op not in _EVAL:
            raise ValueError(f"unknown gate type {op}")
        if name in self.nodes or name in self.inputs:
            raise ValueError(f"signal {name} is driven twice")
        self.nodes[name] = Node(name, op, list(fanins))
        self._shared.setdefault((op, tuple(sorted(fanins))), name)
        return name

    def gate(self, op, fanins):
        """Add an auto-named gate, or reuse an identical one."""
        key = (op, tuple(sorted(fanins)))
        if key not in self._shared:
            self.add(f"#{len(self.nodes)}", op, fanins)
        return self._shared[key]

    def topo_order(self):
        """Nodes that drive the outputs, each listed after its fanins."""
        order, state, inputs = [], {}, set(self.inputs)
        for root in self.outputs:
            if root in inputs or root in state:
                continue
            self._driven(root)
            state[root] = 1
            stack = [(root, iter(self.nodes[root].fanins))]
            while stack:
                name, fanins = stack[-1]
                for x in fanins:
                    if x in inputs or state.get(x) == 2:
                        continue
                    if state.get(x) == 1:
                        raise ValueError(f"combinational loop through {x}")
                    self._driven(x)
                    state[x] = 1
                    stack.append((x, iter(self.nodes[x].fanins)))
                    break
                else:
                    stack.pop()
                    state[name] = 2
                    order.append(self.nodes[name])
        return order

    def _driven(self, name):
        if name not in self.nodes:
            raise ValueError(f"signal {name} is never driven")

    def simulate(self):
        """Truth table of every output."""
        n = len(self.inputs)
        full = full_mask(n)
        val = {x: var_tt(n, i) for i, x in enumerate(self.inputs)}
        for node in self.topo_order():
            val[node.name] = _EVAL[node.op]([val[x] for x in node.fanins], full)
        return {x: val[x] for x in self.outputs}
