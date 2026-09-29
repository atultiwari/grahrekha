import pytest
from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.main import create_app


def test_healthz_is_public_and_reports_version() -> None:
    client = TestClient(create_app(Settings(shared_secret="s")))
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


def test_app_reads_secret_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENGINE_SHARED_SECRET", "from-env")
    client = TestClient(create_app())
    assert client.get("/v1/ping", headers={"X-Engine-Secret": "from-env"}).status_code == 200


def test_app_fails_fast_without_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENGINE_SHARED_SECRET", raising=False)
    with pytest.raises(ValueError):
        create_app()


def test_rules_dir_default_is_safe_outside_a_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    # Inside the container the package lives at /app/src/..., only 4 levels deep.
    import grahrekha_engine.config as config

    monkeypatch.setattr(config, "__file__", "/app/src/grahrekha_engine/config.py")
    assert config._repo_rules_dir().as_posix() == "rules"
