from pathlib import Path

import pytest

EXAMPLE_PALM = (
    Path(__file__).resolve().parents[1] / "models/weights/M2-palm-line-reader/example1_input.png"
)


@pytest.fixture(scope="session")
def example_palm_bytes() -> bytes:
    if not EXAMPLE_PALM.exists():
        pytest.skip("run scripts/fetch-data.sh --only M1,M2")
    return EXAMPLE_PALM.read_bytes()


EPHEMERIS = Path(__file__).resolve().parents[1] / "models/weights/A1-de421/de421.bsp"


@pytest.fixture(scope="session")
def ephemeris_path() -> Path:
    if not EPHEMERIS.exists():
        pytest.skip("run scripts/fetch-data.sh --only A1")
    return EPHEMERIS
