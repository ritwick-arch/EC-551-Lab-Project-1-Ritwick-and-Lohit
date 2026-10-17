
from logicsyn.core.cube import Cube
from logicsyn.core.function import BooleanFunction


def essentials(f: BooleanFunction, primes: list[Cube]) -> list[Cube]:
    result = set()

    for m in range(1 << f.n):
        if not (f.on & (1 << m)):
            continue

        covering = [p for p in primes if p.contains(m)]

        if len(covering) == 1:
            result.add(covering[0])

    return sorted(result)


def min_cover(
    f: BooleanFunction,
    primes: list[Cube]
) -> tuple[list[Cube], bool]:

    # Cost: fewest literals, then fewest terms.
    def cost(cover):
        return (
            sum(p.literals for p in cover),
            len(cover)
        )

    selected = essentials(f, primes)

    remaining = {
        m for m in range(1 << f.n)
        if (f.on & (1 << m))
        and not any(p.contains(m) for p in selected)
    }

    if not remaining:
        return selected, True

    candidates = sorted(
        set(primes) - set(selected)
    )

    # Remove candidates covering no remaining minterms.
    candidates = [
        p for p in candidates
        if any(p.contains(m) for m in remaining)
    ]

    # Dominance reduction.
    def reduce_chart(candidates, remaining):
        changed = True

        while changed:
            changed = False

            # Row dominance: discard a more costly subset.
            for p in candidates:
                p_cover = {m for m in remaining if p.contains(m)}

                for q in candidates:
                    if p == q:
                        continue

                    q_cover = {
                        m for m in remaining if q.contains(m)
                    }

                    if (
                        p_cover <= q_cover
                        and (
                            p.literals > q.literals
                            or (
                                p.literals == q.literals
                                and p > q
                            )
                        )
                    ):
                        candidates.remove(p)
                        changed = True
                        break

                if changed:
                    break

            if changed:
                continue

            # Column dominance: discard easier requirements.
            for m in sorted(remaining):
                options_m = {
                    p for p in candidates if p.contains(m)
                }

                for other in sorted(remaining):
                    if m == other:
                        continue

                    options_other = {
                        p for p in candidates
                        if p.contains(other)
                    }

                    if (
                        options_other < options_m
                        or (
                            options_other == options_m
                            and other < m
                        )
                    ):
                        remaining.remove(m)
                        changed = True
                        break

                if changed:
                    break

        return candidates, remaining

    candidates, remaining = reduce_chart(
        candidates, remaining
    )

    if not remaining:
        return selected, True

    for m in remaining:
        if not any(p.contains(m) for p in candidates):
            raise ValueError("No valid cover found")

    # Greedy upper bound and fallback.
    def greedy():
        uncovered = set(remaining)
        chosen = []

        while uncovered:
            options = [
                p for p in candidates
                if p not in chosen
                and any(p.contains(m) for m in uncovered)
            ]

            if not options:
                raise ValueError("No valid cover found")

            best = min(
                options,
                key=lambda p: (
                    p.literals / sum(
                        p.contains(m) for m in uncovered
                    ),
                    p.literals,
                    p
                )
            )

            chosen.append(best)
            uncovered = {
                m for m in uncovered
                if not best.contains(m)
            }

        # Remove any redundant selected candidates.
        for p in list(chosen):
            trial = [q for q in chosen if q != p]

            if all(
                any(q.contains(m) for q in trial)
                for m in remaining
            ):
                chosen.remove(p)

        return sorted(chosen)

    best = greedy()
    best_cost = cost(selected + best)

    # Large problems use the greedy heuristic.
    if len(candidates) > 24:
        return sorted(selected + best), False

    # Exact branch-and-bound.
    def search(chosen, uncovered):
        nonlocal best, best_cost

        if not uncovered:
            trial = sorted(chosen)
            trial_cost = cost(selected + trial)

            if trial_cost < best_cost:
                best = trial
                best_cost = trial_cost
            return

        current_cost = cost(selected + chosen)

        if current_cost >= best_cost:
            return

        # Branch on the most constrained minterm.
        m = min(
            uncovered,
            key=lambda x: (
                sum(
                    p.contains(x)
                    for p in candidates
                    if p not in chosen
                ),
                x
            )
        )

        options = sorted(
            (
                p for p in candidates
                if p.contains(m) and p not in chosen
            ),
            key=lambda p: (p.literals, p)
        )

        for p in options:
            new_uncovered = {
                x for x in uncovered
                if not p.contains(x)
            }

            search(chosen + [p], new_uncovered)

    search([], set(remaining))

    return sorted(selected + best), True
