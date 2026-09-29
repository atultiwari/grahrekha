"""Deterministic stratified sampling for frozen evaluation splits."""

import random
from collections import defaultdict
from collections.abc import Callable, Hashable, Sequence


def stratified_sample[T](
    items: Sequence[T], key: Callable[[T], Hashable], n: int, seed: int
) -> list[T]:
    """Pick up to n items spread as evenly as possible across strata.

    Strata smaller than their share are taken whole; the leftover quota is handed to
    the remaining strata round-robin. The result is deterministic for a given seed
    and input order, and is returned in stratum-then-pick order.
    """
    rng = random.Random(seed)
    strata: dict[Hashable, list[T]] = defaultdict(list)
    for item in items:
        strata[key(item)].append(item)
    pools = {k: rng.sample(v, len(v)) for k, v in sorted(strata.items(), key=lambda kv: str(kv[0]))}

    quota = dict.fromkeys(pools, 0)
    remaining = min(n, len(items))
    while remaining > 0:
        open_strata = [k for k in pools if quota[k] < len(pools[k])]
        for k in open_strata:
            if remaining == 0:
                break
            quota[k] += 1
            remaining -= 1
    return [item for k, pool in pools.items() for item in pool[: quota[k]]]
