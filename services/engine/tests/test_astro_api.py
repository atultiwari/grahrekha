from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.main import create_app

SECRET = "astro-secret"
HEADERS = {"X-Engine-Secret": SECRET}
BODY = {
    "birth": {
        "birth_date": "1996-07-04",
        "birth_time": "09:10:00",
        "time_confidence": "exact",
        "latitude": 18.404,
        "longitude": 75.195,
    },
    "reference_date": "2026-09-30",
}


def test_requires_the_secret() -> None:
    assert (
        TestClient(create_app(Settings(shared_secret=SECRET)))
        .post("/v1/astro/chart", json=BODY)
        .status_code
        == 401
    )


def test_invalid_birth_data_is_422() -> None:
    bad = {
        "birth": {
            "birth_date": "1996-07-04",
            "time_confidence": "exact",
            "latitude": 18.4,
            "longitude": 75.2,
        },
        "reference_date": "2026-09-30",
    }
    client = TestClient(create_app(Settings(shared_secret=SECRET)))
    assert client.post("/v1/astro/chart", headers=HEADERS, json=bad).status_code == 422


def test_missing_ephemeris_is_503(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(shared_secret=SECRET, models_dir=tmp_path)))
    response = client.post("/v1/astro/chart", headers=HEADERS, json=BODY)
    assert response.status_code == 503
    assert "ephemeris" in response.json()["detail"]


@pytest.mark.models
def test_returns_a_chart(ephemeris_path: Path) -> None:
    client = TestClient(create_app(Settings(shared_secret=SECRET)))
    response = client.post("/v1/astro/chart", headers=HEADERS, json=BODY)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema_version"] == "astro_chart.v1"
    assert body["lagna_sign"] == "Leo" and body["current_mahadasha"] == "Jupiter"
