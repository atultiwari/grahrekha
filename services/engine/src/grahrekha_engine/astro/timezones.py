"""Offline timezone resolution with historical UTC offsets.

Coordinates -> IANA zone via timezonefinder (bundled data, no network: D-016). Offsets come
from the IANA database via zoneinfo, so historical rules (e.g. India's UTC+6:30 war time in
1942-45, daylight saving elsewhere) are applied for the actual birth date.
"""

from datetime import date, datetime, time
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from timezonefinder import TimezoneFinder


class TimezoneError(ValueError):
    """Cannot determine a timezone. Message is safe to show to users."""


@lru_cache(maxsize=1)
def _finder() -> TimezoneFinder:
    return TimezoneFinder()


def timezone_for(latitude: float, longitude: float) -> str:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise TimezoneError("coordinates are out of range")
    name = _finder().timezone_at(lat=latitude, lng=longitude)
    if name is None:
        raise TimezoneError("no timezone found for this place")
    return str(name)


def utc_offset_hours(birth_date: date, birth_time: time, timezone: str) -> float:
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise TimezoneError(f"unknown timezone: {timezone}") from error
    offset = datetime.combine(birth_date, birth_time, tzinfo=zone).utcoffset()
    if offset is None:  # pragma: no cover - zoneinfo always returns an offset
        raise TimezoneError(f"no UTC offset for {timezone}")
    return offset.total_seconds() / 3600
