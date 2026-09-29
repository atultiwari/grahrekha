from grahrekha_ml.sampling import stratified_sample


def _items() -> list[dict[str, str]]:
    return [{"id": f"{s}-{i}", "skin": s} for s in ("fair", "medium", "dark") for i in range(20)]


def test_sample_is_deterministic_for_a_seed() -> None:
    a = stratified_sample(_items(), key=lambda x: x["skin"], n=12, seed=7)
    b = stratified_sample(_items(), key=lambda x: x["skin"], n=12, seed=7)
    assert a == b
    assert a != stratified_sample(_items(), key=lambda x: x["skin"], n=12, seed=8)


def test_sample_balances_strata() -> None:
    picked = stratified_sample(_items(), key=lambda x: x["skin"], n=12, seed=1)
    counts = {s: sum(1 for p in picked if p["skin"] == s) for s in ("fair", "medium", "dark")}
    assert counts == {"fair": 4, "medium": 4, "dark": 4}


def test_small_strata_are_exhausted_and_remainder_redistributed() -> None:
    items = [{"id": "r1", "skin": "rare"}] + [{"id": f"c{i}", "skin": "common"} for i in range(30)]
    picked = stratified_sample(items, key=lambda x: x["skin"], n=10, seed=3)
    assert len(picked) == 10
    assert {"id": "r1", "skin": "rare"} in picked


def test_n_larger_than_population_returns_everything_once() -> None:
    items = _items()[:5]
    picked = stratified_sample(items, key=lambda x: x["skin"], n=50, seed=0)
    assert sorted(p["id"] for p in picked) == sorted(i["id"] for i in items)
