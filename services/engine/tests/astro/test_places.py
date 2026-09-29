from pathlib import Path

import pytest

from grahrekha_engine.astro.places import PlaceIndex

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def places() -> PlaceIndex:
    return PlaceIndex.load(FIXTURES / "cities.tsv", FIXTURES / "admin1.tsv")


def test_prefix_search_ranks_by_population(places: PlaceIndex) -> None:
    results = places.search("del")
    assert [r.name for r in results][:2] == ["Delhi", "Delhi Cantonment"]
    assert results[0].region == "Delhi" and results[0].country == "IN"
    assert results[0].timezone == "Asia/Kolkata"


def test_alternate_and_old_names_match(places: PlaceIndex) -> None:
    assert places.search("bangalore")[0].name == "Bengaluru"
    assert places.search("banaras")[0].name == "Varanasi"
    assert places.search("kashi")[0].region == "Uttar Pradesh"


def test_official_names_outrank_alternate_names(places: PlaceIndex) -> None:
    # Dili (East Timor) lists "Delhi" as an alternate name and outnumbers Delhi Cantonment.
    assert [r.name for r in places.search("del")] == ["Delhi", "Delhi Cantonment", "Dili"]
    assert [r.name for r in places.search("dili")] == ["Dili"]


def test_devanagari_names_match(places: PlaceIndex) -> None:
    assert places.search("दिल्ली")[0].name == "Delhi"
    assert places.search("लंदन")[0].name == "London"


def test_search_is_case_and_accent_insensitive(places: PlaceIndex) -> None:
    assert places.search("LONDRES")[0].name == "London"
    assert places.search("dÍli")[0].name == "Dili"


def test_limits_and_empty_queries(places: PlaceIndex) -> None:
    assert len(places.search("d", limit=1)) == 1
    assert places.search("  ") == []
    assert places.search("zzzz") == []
