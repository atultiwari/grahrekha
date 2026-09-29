from datetime import date, time, timedelta
from itertools import pairwise
from pathlib import Path

import pytest

from grahrekha_engine.astro.chart import compute_chart
from grahrekha_engine.contracts.astro import BirthDataV1

pytestmark = pytest.mark.models
SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]
KARMALA = BirthDataV1(
    birth_date=date(1996, 7, 4),
    birth_time=time(9, 10),
    time_confidence="exact",
    latitude=18.404,
    longitude=75.195,
)


def test_known_chart_matches_the_reference(ephemeris_path: Path) -> None:
    chart = compute_chart(KARMALA, ephemeris_path, reference_date=date(2026, 9, 30))
    assert chart.timezone == "Asia/Kolkata" and chart.utc_offset_hours == 5.5
    assert chart.lagna_sign == "Leo"
    moon = next(p for p in chart.planets if p.planet == "Moon")
    assert moon.sign == "Aquarius"
    assert chart.moon_nakshatra == "Dhanishta"
    assert chart.current_mahadasha == "Jupiter"  # 2017-06-21 .. 2033-06-22 (jyotishganit README)
    assert chart.provider.startswith("jyotishganit") and chart.ayanamsa == "true-chitrapaksha"


def test_planets_are_consistent(ephemeris_path: Path) -> None:
    chart = compute_chart(KARMALA, ephemeris_path, reference_date=date(2026, 9, 30))
    assert {p.planet for p in chart.planets} == {
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
        "Rahu",
        "Ketu",
    }
    for p in chart.planets:
        assert 0 <= p.longitude < 360
        assert SIGNS[int(p.longitude // 30)] == p.sign
        assert p.house is not None
    rahu = next(p for p in chart.planets if p.planet == "Rahu")
    ketu = next(p for p in chart.planets if p.planet == "Ketu")
    assert abs(((rahu.longitude - ketu.longitude) % 360) - 180) < 0.01  # always opposite


def test_mahadashas_are_contiguous_and_span_the_120_year_cycle(ephemeris_path: Path) -> None:
    periods = compute_chart(KARMALA, ephemeris_path, reference_date=date(2026, 9, 30)).mahadashas
    for earlier, later in pairwise(periods):
        assert abs((later.start - earlier.end).days) <= 1
    assert periods[0].start <= KARMALA.birth_date
    assert (periods[-1].end - periods[0].start) >= timedelta(days=int(119 * 365.25))


def test_unknown_birth_time_withholds_lagna_and_houses(ephemeris_path: Path) -> None:
    birth = BirthDataV1(birth_date=date(1996, 7, 4), latitude=18.404, longitude=75.195)
    chart = compute_chart(birth, ephemeris_path, reference_date=date(2026, 9, 30))
    assert chart.time_confidence == "unknown"
    assert chart.lagna_sign is None and chart.lagna_degree is None
    assert all(p.house is None for p in chart.planets)
    assert isinstance(chart.moon_nakshatra_uncertain, bool)


def test_wartime_india_uses_the_historical_offset(ephemeris_path: Path) -> None:
    birth = BirthDataV1(
        birth_date=date(1943, 6, 1),
        birth_time=time(12, 0),
        time_confidence="exact",
        latitude=22.57,
        longitude=88.36,
    )  # Kolkata
    assert (
        compute_chart(birth, ephemeris_path, reference_date=date(2026, 9, 30)).utc_offset_hours
        == 6.5
    )


def test_birth_data_validation() -> None:
    with pytest.raises(ValueError):
        BirthDataV1(birth_date=date(2000, 1, 1), time_confidence="exact", latitude=0, longitude=0)
    with pytest.raises(ValueError):
        BirthDataV1(birth_date=date(2000, 1, 1), birth_time=time(1, 0), latitude=0, longitude=0)
