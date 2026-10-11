"""Boolean functions as ON / don't-care truth tables, and the parsed design."""
from dataclasses import dataclass

from .bits import MAX_INPUTS, full_mask
from .netlist import Netlist


@dataclass
class BooleanFunction:
    name: str
    inputs: list[str]
    on: int
    dc: int = 0
    source: Netlist | None = None

    def __post_init__(self):
        if self.n > MAX_INPUTS:
            raise ValueError(f"{self.name} has {self.n} inputs; the limit is {MAX_INPUTS}")
        self.dc &= full_mask(self.n)
        self.on &= full_mask(self.n) & ~self.dc  # ON and don't-care at once counts as don't-care

    @property
    def n(self):
        return len(self.inputs)

    @property
    def off(self):
        return full_mask(self.n) & ~(self.on | self.dc)

    def complement(self):
        return BooleanFunction(self.name + "'", self.inputs, self.off, self.dc)


@dataclass
class Design:
    name: str
    inputs: list[str]
    functions: list[BooleanFunction]
