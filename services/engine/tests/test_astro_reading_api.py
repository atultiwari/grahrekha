from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.main import create_app

SECRET = "reading-secret"
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


def test_reading_requires_the_secret() -> None:
    client = TestClient(create_app(Settings(shared_secret=SECRET)))
    assert client.post("/v1/astro/reading", json=BODY).status_code == 401


def test_production_mode_fires_only_approved_rules(ephemeris_path) -> None:  # type: ignore[no-untyped-def]
    settings = Settings(shared_secret=SECRET, models_dir=ephemeris_path.parents[1])
    client = TestClient(create_app(settings))
    body = client.post("/v1/astro/reading", headers=HEADERS, json=BODY).json()
    assert body["schema_version"] == "astro_reading.v1"
    assert body["chart"]["lagna_sign"] == "Leo"
    assert body["features"]["mahadasha"]["houses_ruled"] == [5, 8]
    assert body["rules"]["fired"] == []  # nothing is approved yet (D-008)


def test_lab_mode_fires_unreviewed_rules(ephemeris_path) -> None:  # type: ignore[no-untyped-def]
    settings = Settings(shared_secret=SECRET, models_dir=ephemeris_path.parents[1])
    client = TestClient(create_app(settings))
    safe_lagna = BODY | {"birth": BODY["birth"] | {"birth_time": "09:30:00"}}  # type: ignore[operator]
    body = client.post(
        "/v1/astro/reading", headers=HEADERS, json=safe_lagna | {"include_unreviewed": True}
    ).json()
    fired = {rule["id"] for rule in body["rules"]["fired"]}
    assert "astro.jc.mahadasha_lord_rules_trikona" in fired
    assert all(rule["status"] == "extracted" for rule in body["rules"]["fired"])
