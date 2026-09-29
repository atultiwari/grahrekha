from datetime import date, time, timedelta
from itertools import pairwise
from pathlib import Path

import pytest

from grahrekha_engine.astro.chart import compute_chart, navamsa_sign
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
    assert chart.navamsa_lagna_sign is None
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


@pytest.mark.parametrize(
    ("longitude", "expected"),
    [
        (0.0, "Aries"),  # Aries (fire) navamsas start from Aries
        (3.34, "Taurus"),
        (29.99, "Sagittarius"),
        (30.0, "Capricorn"),  # Taurus (earth) starts from Capricorn
        (60.0, "Libra"),  # Gemini (air) starts from Libra
        (90.0, "Cancer"),  # Cancer (water) starts from Cancer
        (359.99, "Pisces"),
    ],
)
def test_navamsa_sign(longitude: float, expected: str) -> None:
    assert navamsa_sign(longitude) == expected


def test_navamsa_matches_jyotishganit_for_the_grahas(ephemeris_path: Path) -> None:
    chart = compute_chart(KARMALA, ephemeris_path, reference_date=date(2026, 9, 30))
    assert chart.navamsa_lagna_sign == "Aries"  # from jyotishganit's D9 for this chart
    by_planet = {p.planet: p.navamsa_sign for p in chart.planets}
    assert by_planet["Venus"] == "Gemini" and by_planet["Mars"] == "Cancer"
    assert all(p.navamsa_sign in SIGNS for p in chart.planets)


def test_birth_data_validation() -> None:
    with pytest.raises(ValueError):
        BirthDataV1(birth_date=date(2000, 1, 1), time_confidence="exact", latitude=0, longitude=0)
    with pytest.raises(ValueError):
        BirthDataV1(birth_date=date(2000, 1, 1), birth_time=time(1, 0), latitude=0, longitude=0)


# Reference: Swiss Ephemeris 2.10.03 (Moshier), sidereal mean lunar node, True Citra
# ayanamsa; computed 2026-09-30 in adapters-agpl/ (validate_astro.py). Plain numbers.
@pytest.mark.parametrize(
    ("birth", "swiss_rahu"),
    [
        (
            BirthDataV1(
                birth_date=date(1930, 3, 15),
                birth_time=time(12, 0),
                time_confidence="exact",
                latitude=28.61,
                longitude=77.21,
            ),
            12.1887,
        ),  # Delhi, 06:30 UTC
        (
            BirthDataV1(
                birth_date=date(2020, 6, 1),
                birth_time=time(6, 30),
                time_confidence="exact",
                latitude=51.51,
                longitude=-0.13,
            ),
            66.0525,
        ),  # London (BST), 05:30 UTC
    ],
)
def test_rahu_is_corrected_for_precession(
    ephemeris_path: Path, birth: BirthDataV1, swiss_rahu: float
) -> None:
    # jyotishganit 0.1.3 subtracts a J2000 ayanamsa from an of-date mean node, so its
    # Rahu drifts by precession (~1.4 deg/century from 2000). We correct it.
    chart = compute_chart(birth, ephemeris_path, reference_date=date(2026, 9, 30))
    rahu = next(p for p in chart.planets if p.planet == "Rahu")
    ketu = next(p for p in chart.planets if p.planet == "Ketu")
    assert abs(((rahu.longitude - swiss_rahu) + 180) % 360 - 180) < 0.02
    assert SIGNS[int(rahu.longitude // 30)] == rahu.sign
    assert abs(((rahu.longitude - ketu.longitude) % 360) - 180) < 1e-6
