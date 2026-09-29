"""Birth chart + Vimshottari dasha via jyotishganit (MIT), offline (docs/ARCHITECTURE.md §5).

Reproducible by design:
- the "current" dasha is computed for an explicit reference date, not the system clock;
- the timezone offset is the historical one for the birth date (timezones.py);
- when the birth time is unknown, lagna and houses are withheld (they change every ~2
  hours), and the Moon's nakshatra is flagged if it differs between 00:00 and 23:59.
"""

from datetime import date, datetime, time
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

from grahrekha_engine.astro.offline import configure_offline
from grahrekha_engine.astro.timezones import timezone_for, utc_offset_hours
from grahrekha_engine.contracts.astro import (
    AstroChartV1,
    BirthDataV1,
    DashaPeriodV1,
    Planet,
    PlanetPositionV1,
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
NOON = time(12, 0)


def _jyotishganit_chart(when: datetime, birth: BirthDataV1, offset: float) -> Any:
    from jyotishganit import calculate_birth_chart

    return calculate_birth_chart(
        birth_date=when, latitude=birth.latitude, longitude=birth.longitude, timezone_offset=offset
    )


def _planets(raw: Any, include_houses: bool) -> list[PlanetPositionV1]:
    positions = []
    for p in raw.d1_chart.planets:
        sign = cast(Sign, p.sign)
        degree = float(p.sign_degrees)
        positions.append(
            PlanetPositionV1(
                planet=cast(Planet, p.celestial_body),
                longitude=round(SIGNS.index(sign) * 30 + degree, 4),
                sign=sign,
                degree_in_sign=round(degree, 4),
                nakshatra=str(p.nakshatra),
                pada=int(p.pada),
                house=int(p.house) if include_houses else None,
                retrograde=p.motion_type == "retrograde" or p.celestial_body in ("Rahu", "Ketu"),
            )
        )
    return positions


def _dashas(raw: Any, reference: date) -> tuple[list[DashaPeriodV1], Planet | None, Planet | None]:
    mahadashas = raw.dashas.all["mahadashas"]
    periods, current_md, current_ad = [], None, None
    for lord, period in mahadashas.items():
        start, end = period["start"].date(), period["end"].date()
        periods.append(DashaPeriodV1(lord=cast(Planet, lord), start=start, end=end))
        if start <= reference < end:
            current_md = cast(Planet, lord)
            for sub_lord, sub in period["antardashas"].items():
                if sub["start"].date() <= reference < sub["end"].date():
                    current_ad = cast(Planet, sub_lord)
    return periods, current_md, current_ad


def compute_chart(birth: BirthDataV1, ephemeris_path: Path, reference_date: date) -> AstroChartV1:
    configure_offline(ephemeris_path)
    zone = birth.timezone or timezone_for(birth.latitude, birth.longitude)
    known_time = birth.birth_time is not None
    local_time = birth.birth_time or NOON
    offset = utc_offset_hours(birth.birth_date, local_time, zone)
    raw = _jyotishganit_chart(datetime.combine(birth.birth_date, local_time), birth, offset)

    moon_uncertain = False
    if not known_time:
        early = _jyotishganit_chart(datetime.combine(birth.birth_date, time(0, 0)), birth, offset)
        late = _jyotishganit_chart(datetime.combine(birth.birth_date, time(23, 59)), birth, offset)
        moon_uncertain = early.panchanga.nakshatra != late.panchanga.nakshatra

    periods, current_md, current_ad = _dashas(raw, reference_date)
    lagna = raw.d1_chart.houses[0]
    return AstroChartV1(
        provider=f"jyotishganit-{version('jyotishganit')}",
        ayanamsa="true-chitrapaksha",
        timezone=zone,
        utc_offset_hours=offset,
        time_confidence=birth.time_confidence,
        lagna_sign=cast(Sign, lagna.sign) if known_time else None,
        lagna_degree=round(float(lagna.sign_degrees), 4) if known_time else None,
        planets=_planets(raw, include_houses=known_time),
        moon_nakshatra=str(raw.panchanga.nakshatra),
        moon_nakshatra_uncertain=moon_uncertain,
        mahadashas=periods,
        current_mahadasha=current_md,
        current_antardasha=current_ad,
    )
