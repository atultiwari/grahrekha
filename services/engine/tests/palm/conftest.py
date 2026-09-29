"""Fixtures for tests that need downloaded models and images.

These files are fetched by `scripts/fetch-data.sh --only M1,M2` (pinned + checksummed)
and are never committed. Tests using them are skipped locally if absent; CI fetches them.
"""

from pathlib import Path

import pytest

from grahrekha_engine.palm.image_io import RGBImage, decode_image

WEIGHTS = Path(__file__).resolve().parents[2] / "models" / "weights"
HAND_MODEL = WEIGHTS / "M1-mediapipe" / "hand_landmarker.task"
EXAMPLE_PALM = WEIGHTS / "M2-palm-line-reader" / "example1_input.png"


def _require(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"missing {path.name}; run scripts/fetch-data.sh --only M1,M2")
    return path


@pytest.fixture(scope="session")
def hand_model_path() -> Path:
    return _require(HAND_MODEL)


@pytest.fixture(scope="session")
def example_palm() -> RGBImage:
    return decode_image(_require(EXAMPLE_PALM).read_bytes())
