
from logicsyn.core.cube import Cube


def estimate_cost(cover: list[Cube]) -> dict:
    # Number of product terms in SOP
    num_terms = len(cover)

    # Total number of literals
    literals = sum(cube.literals for cube in cover)

    # AND gate needed for each term with 2+ literals
    and_gates = sum(
        1 for cube in cover if cube.literals >= 2
    )

    # OR gate needed when there are multiple terms
    or_gates = 1 if num_terms >= 2 else 0

    # Simple estimate of logical depth
    if num_terms == 0:
        depth = 0
    elif num_terms == 1:
        depth = 1 if cover[0].literals >= 2 else 0
    else:
        depth = 2 if and_gates > 0 else 1

    return {
        "terms": num_terms,
        "literals": literals,
        "and_gates": and_gates,
        "or_gates": or_gates,
        "total_gates": and_gates + or_gates,
        "depth": depth,
    }
