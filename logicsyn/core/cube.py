"""Product terms (cubes) whose bits line up with minterm indices."""
from typing import NamedTuple

from .bits import full_mask, var_tt


class Cube(NamedTuple):
    mask: int   # bit set = the variable appears in the term
    value: int  # polarity of those variables: 1 = x, 0 = x'

    @classmethod
    def minterm(cls, m, n):
        return cls((1 << n) - 1, m)

    @classmethod
    def from_pattern(cls, p):
        mask = value = 0
        for ch in p:
            if ch not in "01-":
                raise ValueError(f"bad cube character {ch!r} in {p!r}")
            mask = mask << 1 | (ch != "-")
            value = value << 1 | (ch == "1")
        return cls(mask, value)

    @property
    def literals(self):
        return self.mask.bit_count()

    def contains(self, m):
        return (m & self.mask) == self.value

    def lits(self, n):
        """(input index, is positive) for each literal, first input first."""
        return [(i, bool(self.value >> (n - 1 - i) & 1))
                for i in range(n) if self.mask >> (n - 1 - i) & 1]

    def pattern(self, n):
        return "".join("-" if not self.mask >> (n - 1 - i) & 1
                       else "1" if self.value >> (n - 1 - i) & 1 else "0"
                       for i in range(n))

    def tt(self, n):
        t = full_mask(n)
        for i, pos in self.lits(n):
            t &= var_tt(n, i) if pos else ~var_tt(n, i)
        return t
