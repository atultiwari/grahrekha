import pytest
from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.main import create_app

SECRET = "test-secret-value"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(shared_secret=SECRET)))


def test_protected_route_rejects_missing_secret(client: TestClient) -> None:
    assert client.get("/v1/ping").status_code == 401


def test_protected_route_rejects_wrong_secret(client: TestClient) -> None:
    response = client.get("/v1/ping", headers={"X-Engine-Secret": "wrong"})
    assert response.status_code == 401


def test_protected_route_accepts_correct_secret(client: TestClient) -> None:
    response = client.get("/v1/ping", headers={"X-Engine-Secret": SECRET})
    assert response.status_code == 200
    assert response.json() == {"pong": True}


def test_secret_must_be_configured() -> None:
    with pytest.raises(ValueError, match="shared_secret"):
        Settings(shared_secret="")
