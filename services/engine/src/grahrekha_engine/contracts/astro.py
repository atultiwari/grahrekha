"""Astrology contracts (docs/ARCHITECTURE.md §5). Independent of palm contracts (D-001)."""

from datetime import date, time
from typing import Literal

from pydantic import Field, model_validator

from grahrekha_engine.contracts import Contract

Planet = Literal["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
Sign = Literal[
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
TimeConfidence = Literal["exact", "approximate", "unknown"]


class BirthDataV1(Contract):
    birth_date: date
    birth_time: time | None = None  # None when unknown
    time_confidence: TimeConfidence = "unknown"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str | None = None  # IANA name; looked up offline from coordinates if absent

    @model_validator(mode="after")
    def _time_matches_confidence(self) -> "BirthDataV1":
        if self.birth_time is None and self.time_confidence != "unknown":
            raise ValueError("time_confidence must be 'unknown' when birth_time is missing")
        if self.birth_time is not None and self.time_confidence == "unknown":
            raise ValueError("give time_confidence 'exact' or 'approximate' with a birth_time")
        return self


class PlanetPositionV1(Contract):
    planet: Planet
    longitude: float  # sidereal, degrees 0-360
    sign: Sign
    degree_in_sign: float
    navamsa_sign: Sign  # D9
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    house: int | None = Field(default=None, ge=1, le=12)  # None when birth time is unknown
    retrograde: bool


class DashaPeriodV1(Contract):
    lord: Planet
    start: date
    end: date


class AstroChartV1(Contract):
    schema_version: Literal["astro_chart.v1"] = "astro_chart.v1"
    provider: str  # e.g. "jyotishganit-0.1.3"
    ayanamsa: str  # e.g. "true-chitrapaksha"
    timezone: str
    utc_offset_hours: float
    time_confidence: TimeConfidence
    # Lagna and houses depend on the exact time: None when the birth time is unknown.
    lagna_sign: Sign | None
    lagna_degree: float | None
    navamsa_lagna_sign: Sign | None  # D9 ascendant; changes every ~13 minutes of birth time
    planets: list[PlanetPositionV1]
    moon_nakshatra: str
    # True when the Moon's nakshatra could differ depending on the (unknown) time of day.
    moon_nakshatra_uncertain: bool
    mahadashas: list[DashaPeriodV1]
    current_mahadasha: Planet | None = None
    current_antardasha: Planet | None = None


class AstroRequestV1(Contract):
    birth: BirthDataV1
    # "Current" dasha is computed for this date (explicit, so results are reproducible).
    reference_date: date


class PlaceV1(Contract):
    geoname_id: int
    name: str
    region: str  # state / province; "" when unknown
    country: str  # ISO 3166-1 alpha-2
    latitude: float
    longitude: float
    timezone: str  # IANA name
    population: int


class PlacesResponseV1(Contract):
    schema_version: Literal["places_response.v1"] = "places_response.v1"
    attribution: str  # GeoNames data is CC BY 4.0: show this wherever results are shown
    places: list[PlaceV1]


# --- Features for astrology rules (rules/astro). Derived from AstroChartV1 by
# astro/features.py; keyed by planet so rules can say planets.Sun.house.


class AstroPlanetFeaturesV1(Contract):
    sign: Sign
    house: int | None = None  # None when the birth time is not exact
    navamsa_sign: Sign
    retrograde: bool


class DashaLordFeaturesV1(Contract):
    lord: Planet | None = None
    # Houses (from the lagna) whose signs this planet rules; [] for Rahu/Ketu or when the
    # birth time is unknown. Laghu Parashari judges a period by these (Jataka Chandrika).
    houses_ruled: list[int] = Field(default_factory=list)


class AstroFeaturesV1(Contract):
    schema_version: Literal["astro_features.v1"] = "astro_features.v1"
    time_confidence: TimeConfidence
    moon_nakshatra_uncertain: bool
    lagna_sign: Sign | None = None
    # Degrees from the lagna to the nearest sign boundary. The lagna moves ~1 deg per 4
    # minutes, so a small margin means a slightly wrong birth time changes every house.
    lagna_margin_deg: float | None = None
    planets: dict[Planet, AstroPlanetFeaturesV1]
    mahadasha: DashaLordFeaturesV1
    antardasha: DashaLordFeaturesV1
