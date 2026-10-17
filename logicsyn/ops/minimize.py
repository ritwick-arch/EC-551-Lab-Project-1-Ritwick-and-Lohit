
from logicsyn.core.function import BooleanFunction
from logicsyn.core.cube import Cube
from logicsyn.ops.qm import primes
from logicsyn.ops.cover import min_cover


def minimize_sop(f: BooleanFunction) -> list[Cube]:
    # No ON-set minterms: function is always 0
    if f.on == 0:
        return []

    # Generate prime implicants
    prime_list = primes(f)

    # Select a minimum cover
    return min_cover(f, prime_list)


def minimize_pos(f: BooleanFunction) -> list[Cube]:
    # Minimize the complement's SOP.
    # Its product terms become the POS clauses of F.
    return minimize_sop(f.complement())
