"""Quine-McCluskey prime implicant generation."""

from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction


def combine(a: Cube, b: Cube) -> Cube | None:
    if a.mask != b.mask:
        return None

    diff = a.value ^ b.value

    if diff == 0 or (diff & (diff - 1)) != 0:
        return None

    new_mask = a.mask & ~diff
    new_value = a.value & new_mask

    return Cube(new_mask, new_value)

def prime_implicants(minterms: list[int], n: int) -> list[Cube]:
    # Convert minterms into cubes
    current = {Cube.minterm(m, n) for m in minterms}
    primes = set()

    while current:
        used = set()
        next_round = set()

        # Try combining every pair of cubes
        for a in current:
            for b in current:
                result = combine(a, b)

                if result is not None:
                    used.add(a)
                    used.add(b)
                    next_round.add(result)

        # Cubes that could not combine are prime implicants
        primes.update(current - used)

        # Continue with the newly combined cubes
        current = next_round

    return sorted(primes)


def primes(f: BooleanFunction) -> list[Cube]:
    # Include ON-set and don't-care minterms
    all_bits = f.on | f.dc

    minterms = [
        m for m in range(1 << f.n)
        if all_bits & (1 << m)
    ]

    # Generate prime implicants
    candidates = prime_implicants(minterms, f.n)

    # Keep only primes covering at least one ON-set minterm
    result = [
        cube for cube in candidates
        if any(
            (f.on & (1 << m)) and cube.contains(m)
            for m in range(1 << f.n)
        )
    ]

    return result


def dc_only_primes(f: BooleanFunction) -> list[Cube]:
    # Generate all prime implicants from ON and DC minterms.
    all_bits = f.on | f.dc

    minterms = [
        m for m in range(1 << f.n)
        if all_bits & (1 << m)
    ]

    candidates = prime_implicants(minterms, f.n)

    # Keep primes that cover no ON-set minterms.
    return [
        cube for cube in candidates
        if not any(
            (f.on & (1 << m)) and cube.contains(m)
            for m in range(1 << f.n)
        )
    ]


