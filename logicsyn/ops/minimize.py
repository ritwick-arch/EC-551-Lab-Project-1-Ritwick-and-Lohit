
from logicsyn.core.function import BooleanFunction
from logicsyn.core.cube import Cube
from logicsyn.ops.qm import primes
from logicsyn.ops.cover import min_cover


def minimize_sop(f: BooleanFunction) -> list[Cube]:
    # Return no cubes when the function is always zero.
    if f.on == 0:
        return []

    # Generate the prime implicants.
    prime_list = primes(f)

    # Get the cover and whether the solution is exact.
    cover, exact = min_cover(f, prime_list)

    return cover


def minimize_pos(f: BooleanFunction) -> list[Cube]:
    # Minimize the complement to obtain POS clauses.
    return minimize_sop(f.complement())
