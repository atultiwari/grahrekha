"""Run jyotishganit fully offline (D-016).

jyotishganit 0.1.3 has two runtime downloads we avoid:
- the DE421 ephemeris into a per-OS data folder: we point its loader at our pinned file
  (scripts/fetch-data.sh --only A1, checksum-verified);
- the entire 50 MB Hipparcos catalogue, saved into the *current working directory*, only
  to read one star (Spica, for the True Chitra Paksha ayanamsa): we build Spica from its
  frozen catalogue row instead.
"""

from pathlib import Path

from skyfield.api import Loader, Star

# Hipparcos main catalogue (ESA 1997; CDS I/239), HIP 65474 = Spica (alpha Virginis).
# Fetched from VizieR on 2026-09-30. Positions are ICRS at epoch J1991.25, exactly the
# fields skyfield.data.hipparcos.load_dataframe reads.
SPICA_HIP = 65474
_SPICA_RA_DEG = 201.29835230
_SPICA_DEC_DEG = -11.16124491
_SPICA_PARALLAX_MAS = 12.44
_SPICA_PM_RA_MAS_PER_YEAR = -42.50
_SPICA_PM_DEC_MAS_PER_YEAR = -31.73
_HIPPARCOS_EPOCH_YEAR = 1991.25


def spica_star() -> Star:
    """Spica built exactly as skyfield's Star.from_dataframe builds a Hipparcos row."""
    return Star(
        ra_hours=_SPICA_RA_DEG / 15.0,
        dec_degrees=_SPICA_DEC_DEG,
        ra_mas_per_year=_SPICA_PM_RA_MAS_PER_YEAR,
        dec_mas_per_year=_SPICA_PM_DEC_MAS_PER_YEAR,
        parallax_mas=_SPICA_PARALLAX_MAS,
        epoch=1721045.0 + _HIPPARCOS_EPOCH_YEAR * 365.25,
    )


def configure_offline(ephemeris_path: Path) -> None:
    """Point jyotishganit at local data and remove its catalogue download. Idempotent."""
    if not ephemeris_path.exists():
        raise FileNotFoundError(f"missing ephemeris {ephemeris_path} (fetch-data.sh --only A1)")
    import jyotishganit.components.panchanga as panchanga
    import jyotishganit.core.astronomical as astronomical

    astronomical.loader = Loader(str(ephemeris_path.parent), verbose=False)
    astronomical._ts = None  # re-initialise from our loader on next use
    astronomical._eph = None
    astronomical._get_spica = spica_star
    panchanga.get_spica_star_object = spica_star
