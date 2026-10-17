
from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction


def static1_hazards(
    f: BooleanFunction,
    cover: list[Cube]
) -> list[tuple[int, int]]:
    hazards = []

    on_minterms = [
        m for m in range(1 << f.n)
        if f.on & (1 << m)
    ]

    for i, a in enumerate(on_minterms):
        for b in on_minterms[i + 1:]:
            diff = a ^ b

            # Adjacent if exactly one bit differs
            if diff.bit_count() != 1:
                continue

            # A shared cube prevents the static-1 hazard
            if not any(
                cube.contains(a) and cube.contains(b)
                for cube in cover
            ):
                hazards.append((a, b))

    return hazards

def hazard_free_cover(
    f: BooleanFunction,
    cover: list[Cube]
) -> list[Cube]:
    # Make a copy so we do not modify the original cover
    result = list(cover)

    # Find all adjacent ON-set minterms without shared coverage
    hazards = static1_hazards(f, result)

    for a, b in hazards:
        # Find the bit that differs between the two minterms
        diff = a ^ b

        # Remove the differing bit to create a consensus cube
        mask = ((1 << f.n) - 1) & ~diff
        value = a & mask

        consensus = Cube(mask, value)

        # Add the consensus cube if it is not already present
        if consensus not in result:
            result.append(consensus)

    return result

def static0_hazards(
    f: BooleanFunction,
    pos_cover: list[Cube]
) -> list[tuple[int, int]]:
    # Static-0 hazards of F are static-1 hazards of F'.
    return static1_hazards(f.complement(), pos_cover)
