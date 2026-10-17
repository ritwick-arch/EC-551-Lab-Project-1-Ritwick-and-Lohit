
from itertools import combinations

from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction

LIMIT = 100_000  # covers tried before falling back to greedy


def essentials(f: BooleanFunction, primes: list[Cube]) -> list[Cube]:
    essential = set()

    for m in range(1 << f.n):
        if not (f.on & (1 << m)):
            continue

        covering = [p for p in primes if p.contains(m)]

        if len(covering) == 1:
            essential.add(covering[0])

    return sorted(essential)


def _greedy(need: int, rest: dict[Cube, int]) -> list[Cube]:
    picked = []

    while need:
        # Take the prime covering the most uncovered minterms, then the one with fewer literals
        best = max(rest, key=lambda p: ((rest[p] & need).bit_count(), -p.literals))
        picked.append(best)
        need &= ~rest[best]

    return picked


def min_cover(f: BooleanFunction, primes: list[Cube]) -> tuple[list[Cube], bool]:
    # Essential primes are in every cover, so take them first
    chosen = essentials(f, primes)

    need = f.on
    for p in chosen:
        need &= ~p.tt(f.n)

    if not need:
        return chosen, True

    # ON minterms each remaining prime still covers
    rest = {p: p.tt(f.n) & need for p in primes if p.tt(f.n) & need}
    tried = 0

    # Try covers with 1 cube, then 2 cubes, etc.
    for size in range(1, len(rest) + 1):
        best = None

        for selection in combinations(rest, size):
            tried += 1
            if tried > LIMIT:
                return chosen + _greedy(need, rest), False

            covered = 0
            for cube in selection:
                covered |= rest[cube]

            # Among equal-size covers, minimize literals
            if covered == need:
                literals = sum(cube.literals for cube in selection)
                if best is None or literals < best[0]:
                    best = (literals, selection)

        if best:
            return chosen + list(best[1]), True

    raise ValueError("No valid cover found")
