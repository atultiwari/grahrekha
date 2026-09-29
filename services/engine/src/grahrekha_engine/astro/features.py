"""Rule-ready astrology features from a computed chart (rules/astro, D-001).

Houses and lordships depend on the lagna, so they are only filled when the birth time is
exact; rules that use them must also require time_confidence == "exact" (rules lint).
"""

from grahrekha_engine.contracts.astro import (
    AstroChartV1,
    AstroFeaturesV1,
    AstroPlanetFeaturesV1,
    DashaLordFeaturesV1,
    Planet,
    Sign,
)

SIGNS: tuple[Sign, ...] = (
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
)
# Classical sign rulership (Brihat Jataka I; Rahu and Ketu own no sign in this scheme).
SIGN_LORDS: dict[Sign, Planet] = dict(
    zip(
        SIGNS,
        (
            "Mars",
            "Venus",
            "Mercury",
            "Moon",
            "Sun",
            "Mercury",
            "Venus",
            "Mars",
            "Jupiter",
            "Saturn",
            "Saturn",
            "Jupiter",
        ),
        strict=True,
    )
)


def houses_ruled(planet: Planet | None, lagna: Sign | None) -> list[int]:
    """Houses counted from the lagna (1 = lagna) whose signs the planet rules."""
    if planet is None or lagna is None:
        return []
    start = SIGNS.index(lagna)
    return sorted(
        (SIGNS.index(sign) - start) % 12 + 1 for sign, lord in SIGN_LORDS.items() if lord == planet
    )


def _lagna_margin(chart: AstroChartV1) -> float | None:
    if chart.lagna_degree is None:
        return None
    return round(min(chart.lagna_degree, 30 - chart.lagna_degree), 4)


def astro_features(chart: AstroChartV1) -> AstroFeaturesV1:
    lagna = chart.lagna_sign if chart.time_confidence == "exact" else None
    planets = {
        p.planet: AstroPlanetFeaturesV1(
            sign=p.sign,
            house=p.house if lagna else None,
            navamsa_sign=p.navamsa_sign,
            retrograde=p.retrograde,
        )
        for p in chart.planets
    }
    return AstroFeaturesV1(
        time_confidence=chart.time_confidence,
        moon_nakshatra_uncertain=chart.moon_nakshatra_uncertain,
        lagna_sign=lagna,
        lagna_margin_deg=_lagna_margin(chart) if lagna else None,
        planets=planets,
        mahadasha=DashaLordFeaturesV1(
            lord=chart.current_mahadasha,
            houses_ruled=houses_ruled(chart.current_mahadasha, lagna),
        ),
        antardasha=DashaLordFeaturesV1(
            lord=chart.current_antardasha,
            houses_ruled=houses_ruled(chart.current_antardasha, lagna),
        ),
    )
