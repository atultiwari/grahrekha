from datetime import date

from grahrekha_engine.astro.features import SIGN_LORDS, astro_features, houses_ruled
from grahrekha_engine.contracts.astro import AstroChartV1, DashaPeriodV1, PlanetPositionV1

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _chart(lagna: str | None, houses: dict[str, int | None], md: str, ad: str) -> AstroChartV1:
    planets = [
        PlanetPositionV1(
            planet=name,
            longitude=10.0,
            sign="Aries",
            degree_in_sign=10.0,
            navamsa_sign="Aries",
            nakshatra="Ashwini",
            pada=1,
            house=houses.get(name),
            retrograde=False,
        )
        for name in PLANETS
    ]
    return AstroChartV1(
        provider="test",
        ayanamsa="true-chitrapaksha",
        timezone="Asia/Kolkata",
        utc_offset_hours=5.5,
        time_confidence="exact" if lagna else "unknown",
        lagna_sign=lagna,
        lagna_degree=1.0 if lagna else None,
        navamsa_lagna_sign="Aries" if lagna else None,
        planets=planets,
        moon_nakshatra="Ashwini",
        moon_nakshatra_uncertain=False,
        mahadashas=[DashaPeriodV1(lord=md, start=date(2020, 1, 1), end=date(2036, 1, 1))],
        current_mahadasha=md,
        current_antardasha=ad,
    )


def test_sign_lords_cover_the_zodiac() -> None:
    assert len(SIGN_LORDS) == 12
    assert SIGN_LORDS["Leo"] == "Sun" and SIGN_LORDS["Pisces"] == "Jupiter"


def test_houses_ruled_counts_from_the_lagna() -> None:
    # Leo lagna: Mars rules Aries (9th) and Scorpio (4th); Saturn rules 6th and 7th.
    assert houses_ruled("Mars", "Leo") == [4, 9]
    assert houses_ruled("Saturn", "Leo") == [6, 7]
    assert houses_ruled("Sun", "Leo") == [1]
    assert houses_ruled("Rahu", "Leo") == []  # the nodes own no signs here
    assert houses_ruled("Mars", None) == []  # unknown birth time: no lordship


def test_features_key_planets_by_name_and_describe_the_dasha() -> None:
    chart = _chart("Leo", {"Sun": 10, "Moon": 4}, md="Mars", ad="Saturn")
    features = astro_features(chart)
    assert features.planets["Sun"].house == 10 and features.planets["Moon"].house == 4
    assert features.mahadasha.lord == "Mars" and features.mahadasha.houses_ruled == [4, 9]
    assert features.antardasha.houses_ruled == [6, 7]
    assert features.time_confidence == "exact" and features.lagna_sign == "Leo"


def test_unknown_time_leaves_houses_and_lordship_empty() -> None:
    features = astro_features(_chart(None, {}, md="Venus", ad="Sun"))
    assert features.planets["Sun"].house is None
    assert features.mahadasha.lord == "Venus" and features.mahadasha.houses_ruled == []
