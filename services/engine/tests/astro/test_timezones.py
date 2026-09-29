from datetime import date, time

import pytest

from grahrekha_engine.astro.timezones import TimezoneError, timezone_for, utc_offset_hours


def test_finds_the_timezone_offline_from_coordinates() -> None:
    assert timezone_for(28.61, 77.21) == "Asia/Kolkata"  # New Delhi
    assert timezone_for(51.51, -0.13) == "Europe/London"


def test_india_war_time_1942_to_1945() -> None:
    # India observed UTC+6:30 during the Second World War; a naive +5:30 is an hour off.
    assert utc_offset_hours(date(1943, 6, 1), time(12, 0), "Asia/Kolkata") == 6.5
    assert utc_offset_hours(date(1996, 7, 4), time(9, 10), "Asia/Kolkata") == 5.5


def test_daylight_saving_is_applied() -> None:
    assert utc_offset_hours(date(2020, 7, 1), time(12, 0), "America/New_York") == -4.0
    assert utc_offset_hours(date(2020, 1, 15), time(12, 0), "America/New_York") == -5.0


def test_unknown_timezone_name_is_rejected() -> None:
    with pytest.raises(TimezoneError):
        utc_offset_hours(date(2020, 1, 1), time(0, 0), "Mars/Olympus_Mons")


def test_open_ocean_gets_a_nautical_zone() -> None:
    assert timezone_for(-40.0, -120.0).startswith("Etc/GMT")


def test_invalid_coordinates_are_rejected() -> None:
    with pytest.raises(TimezoneError):
        timezone_for(95.0, 10.0)
