"""Birth chart + Vimshottari dasha via jyotishganit (MIT), offline (docs/ARCHITECTURE.md §5).

Reproducible by design:
- the "current" dasha is computed for an explicit reference date, not the system clock;
- the timezone offset is the historical one for the birth date (timezones.py);
- when the birth time is unknown, lagna and houses are withheld (they change every ~2
  hours), and the Moon's nakshatra is flagged if it differs between 00:00 and 23:59.
"""

from datetime import UTC, date, datetime, time, timedelta
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
J2000_JD = 2451545.0


def navamsa_sign(longitude: float) -> Sign:
    """D9 sign. Consecutive 3deg20' parts run through the zodiac, so each sign's nine start
    from Aries (fire), Capricorn (earth), Libra (air) or Cancer (water)."""
    return SIGNS[int((longitude % 360) * 9 // 30) % 12]  # x9 first: exact at boundaries


def precession_since_j2000_deg(moment_utc: datetime) -> float:
    """General precession in longitude from J2000 to the given date (IAU 2006, degrees)."""
    julian_day = moment_utc.timestamp() / 86400.0 + 2440587.5
    t = (julian_day - J2000_JD) / 36525.0
    arcsec = 5028.796195 * t + 1.1054348 * t**2 + 0.00007964 * t**3
    return arcsec / 3600.0


def _corrected_node(
    raw_planet: Any, precession: float, lagna_sign_index: int | None
) -> dict[str, Any]:
    """Rahu/Ketu fix for jyotishganit 0.1.3.

    It subtracts a J2000-referred ayanamsa (consistent with its J2000-frame planets) from a
    mean node referred to the equinox OF DATE, so its nodes drift by the precession since
    2000 (~1.4 deg/century; 0.3 deg for 1980 births). Validated against Swiss Ephemeris in
    docs/eval/astro-validation.md. Remove if upstream fixes it.
    """
    from jyotishganit.core.astronomical import lon_to_nakshatra

    raw_lon = SIGNS.index(raw_planet.sign) * 30 + float(raw_planet.sign_degrees)
    lon = (raw_lon - precession) % 360
    sign_index = int(lon // 30)
    nakshatra, pada, _ = lon_to_nakshatra(lon)
    house = None if lagna_sign_index is None else (sign_index - lagna_sign_index) % 12 + 1
    return {
        "lon": lon,
        "sign": SIGNS[sign_index],
        "nakshatra": nakshatra,
        "pada": pada,
        "house": house,
    }


def _jyotishganit_chart(when: datetime, birth: BirthDataV1, offset: float) -> Any:
    from jyotishganit import calculate_birth_chart

    return calculate_birth_chart(
        birth_date=when, latitude=birth.latitude, longitude=birth.longitude, timezone_offset=offset
    )


def _planets(raw: Any, include_houses: bool, moment_utc: datetime) -> list[PlanetPositionV1]:
    precession = precession_since_j2000_deg(moment_utc)
    lagna_index = SIGNS.index(raw.d1_chart.houses[0].sign) if include_houses else None
    positions = []
    for p in raw.d1_chart.planets:
        if p.celestial_body in ("Rahu", "Ketu"):
            fixed = _corrected_node(p, precession, lagna_index)
            longitude, sign = fixed["lon"], cast(Sign, fixed["sign"])
            nakshatra, pada, house = fixed["nakshatra"], fixed["pada"], fixed["house"]
        else:
            sign = cast(Sign, p.sign)
            longitude = SIGNS.index(sign) * 30 + float(p.sign_degrees)
            nakshatra, pada = p.nakshatra, p.pada
            house = int(p.house) if include_houses else None
        positions.append(
            PlanetPositionV1(
                planet=cast(Planet, p.celestial_body),
                longitude=round(longitude, 4),
                sign=sign,
                degree_in_sign=round(longitude % 30, 4),
                navamsa_sign=navamsa_sign(longitude),
                nakshatra=str(nakshatra),
                pada=int(pada),
                house=house,
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
    moment_utc = (datetime.combine(birth.birth_date, local_time) - timedelta(hours=offset)).replace(
        tzinfo=UTC
    )
    raw = _jyotishganit_chart(datetime.combine(birth.birth_date, local_time), birth, offset)

    moon_uncertain = False
    if not known_time:
        early = _jyotishganit_chart(datetime.combine(birth.birth_date, time(0, 0)), birth, offset)
        late = _jyotishganit_chart(datetime.combine(birth.birth_date, time(23, 59)), birth, offset)
        moon_uncertain = early.panchanga.nakshatra != late.panchanga.nakshatra

    periods, current_md, current_ad = _dashas(raw, reference_date)
    lagna = raw.d1_chart.houses[0]
    lagna_longitude = SIGNS.index(lagna.sign) * 30 + float(lagna.sign_degrees)
    return AstroChartV1(
        provider=f"jyotishganit-{version('jyotishganit')}",
        ayanamsa="true-chitrapaksha",
        timezone=zone,
        utc_offset_hours=offset,
        time_confidence=birth.time_confidence,
        lagna_sign=cast(Sign, lagna.sign) if known_time else None,
        lagna_degree=round(float(lagna.sign_degrees), 4) if known_time else None,
        navamsa_lagna_sign=navamsa_sign(lagna_longitude) if known_time else None,
        planets=_planets(raw, include_houses=known_time, moment_utc=moment_utc),
        moon_nakshatra=str(raw.panchanga.nakshatra),
        moon_nakshatra_uncertain=moon_uncertain,
        mahadashas=periods,
        current_mahadasha=current_md,
        current_antardasha=current_ad,
    )
