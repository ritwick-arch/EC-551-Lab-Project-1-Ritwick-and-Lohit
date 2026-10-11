"""Truth tables stored as Python ints, one bit per minterm."""
from functools import lru_cache

MAX_INPUTS = 16


def full_mask(n):
    return (1 << (1 << n)) - 1


@lru_cache(maxsize=None)
def var_tt(n, i):
    """Truth table of input i, which is bit n-1-i of every minterm index."""
    w = 1 << (n - 1 - i)
    block = ((1 << w) - 1) << w
    return block * (full_mask(n) // ((1 << (2 * w)) - 1))


def minterms(tt):
    return [m for m, bit in enumerate(bin(tt)[:1:-1]) if bit == "1"]
