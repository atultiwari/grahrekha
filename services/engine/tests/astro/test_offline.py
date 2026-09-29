from pathlib import Path

import pytest

from grahrekha_engine.astro.offline import SPICA_HIP, configure_offline, spica_star

pytestmark = pytest.mark.models


def test_spica_is_built_from_the_frozen_hipparcos_row() -> None:
    star = spica_star()
    assert SPICA_HIP == 65474
    assert star.ra.hours == pytest.approx(201.29835230 / 15)
    assert star.dec.degrees == pytest.approx(-11.16124491)


def test_charts_compute_without_any_network_access(
    ephemeris_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import skyfield.iokit

    def no_network(*_: object, **__: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(skyfield.iokit, "download", no_network)
    monkeypatch.chdir(tmp_path)  # jyotishganit would otherwise write downloads here
    configure_offline(ephemeris_path)

    from datetime import datetime

    from jyotishganit import calculate_birth_chart

    chart = calculate_birth_chart(
        birth_date=datetime(1996, 7, 4, 9, 10),
        latitude=18.404,
        longitude=75.195,
        timezone_offset=5.5,
    )
    # README example of jyotishganit (Karmala, 4 July 1996, 09:10 IST).
    assert chart.d1_chart.houses[0].sign == "Leo"
    assert chart.d1_chart.planets[1].sign == "Aquarius"
    assert chart.panchanga.nakshatra == "Dhanishta"
    assert list(tmp_path.iterdir()) == []  # nothing downloaded into the working directory


def test_missing_ephemeris_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="de421"):
        configure_offline(tmp_path / "de421.bsp")
