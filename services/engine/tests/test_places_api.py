import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.main import create_app

SECRET = "places-secret"
HEADERS = {"X-Engine-Secret": SECRET}
FIXTURES = Path(__file__).parent / "astro" / "fixtures"


def _client(models_dir: Path) -> TestClient:
    return TestClient(create_app(Settings(shared_secret=SECRET, models_dir=models_dir)))


def _models_with_places(tmp_path: Path) -> Path:
    geonames = tmp_path / "A2-geonames"
    geonames.mkdir()
    shutil.copy(FIXTURES / "cities.tsv", geonames / "cities5000.txt")
    shutil.copy(FIXTURES / "admin1.tsv", geonames / "admin1CodesASCII.txt")
    return tmp_path


def test_requires_the_secret(tmp_path: Path) -> None:
    assert _client(tmp_path).get("/v1/places", params={"q": "del"}).status_code == 401


def test_search_returns_places(tmp_path: Path) -> None:
    client = _client(_models_with_places(tmp_path))
    response = client.get("/v1/places", headers=HEADERS, params={"q": "banaras"})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "places_response.v1"
    assert body["attribution"] == "GeoNames, geonames.org (CC BY 4.0)"
    place = body["places"][0]
    assert place["name"] == "Varanasi" and place["timezone"] == "Asia/Kolkata"
    assert {"latitude", "longitude", "region", "country", "population"} <= place.keys()


def test_limit_is_bounded(tmp_path: Path) -> None:
    client = _client(_models_with_places(tmp_path))
    ok = client.get("/v1/places", headers=HEADERS, params={"q": "de", "limit": 1})
    assert len(ok.json()["places"]) == 1
    assert (
        client.get("/v1/places", headers=HEADERS, params={"q": "de", "limit": 99}).status_code
        == 422
    )
    # One character matches a large share of ~500k names (slow); require two.
    assert client.get("/v1/places", headers=HEADERS, params={"q": "d"}).status_code == 422
    assert client.get("/v1/places", headers=HEADERS, params={"q": "x" * 101}).status_code == 422


def test_missing_data_is_503(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/v1/places", headers=HEADERS, params={"q": "del"})
    assert response.status_code == 503
    assert "A2" in response.json()["detail"]
