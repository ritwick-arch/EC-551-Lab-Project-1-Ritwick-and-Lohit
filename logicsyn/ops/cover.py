
from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction


def essentials(f: BooleanFunction, primes: list[Cube]) -> list[Cube]:
    essential = set()

    for m in range(1 << f.n):
        if not (f.on & (1 << m)):
            continue

        covering = [p for p in primes if p.contains(m)]

        if len(covering) == 1:
            essential.add(covering[0])

    return sorted(essential)


from itertools import combinations


def min_cover(f: BooleanFunction, primes: list[Cube]) -> list[Cube]:
    # Find every ON-set minterm
    minterms = [
        m for m in range(1 << f.n)
        if f.on & (1 << m)
    ]

    if not minterms:
        return []

    # Try covers with 1 cube, then 2 cubes, etc.
    for size in range(1, len(primes) + 1):
        valid_covers = []

        for selection in combinations(primes, size):
            # Check whether every ON-set minterm is covered
            if all(
                any(cube.contains(m) for cube in selection)
                for m in minterms
            ):
                valid_covers.append(selection)

        if valid_covers:
            # Among equal-size covers, minimize literals
            best = min(
                valid_covers,
                key=lambda cover: sum(
                    cube.literals for cube in cover
                )
            )
            return list(best)

    raise ValueError("No valid cover found")
