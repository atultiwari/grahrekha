from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.main import create_app
from tests.rules.test_rulebase import RULES_DIR, _features

SECRET = "rules-secret"
HEADERS = {"X-Engine-Secret": SECRET}


def _client() -> TestClient:
    return TestClient(create_app(Settings(shared_secret=SECRET, rules_dir=RULES_DIR)))


def _body(include_unreviewed: bool) -> dict[str, object]:
    return {
        "features": _features(heart_len=0.8).model_dump(),
        "include_unreviewed": include_unreviewed,
    }


def test_production_mode_returns_only_approved_rules() -> None:
    response = _client().post("/v1/rules/evaluate", headers=HEADERS, json=_body(False))
    assert response.status_code == 200
    body = response.json()
    assert body["fired"] == []  # nothing is approved yet (Phase 1)
    assert len(body["rulebase_version"]) == 12


def test_lab_mode_includes_unreviewed_rules_with_citations() -> None:
    body = _client().post("/v1/rules/evaluate", headers=HEADERS, json=_body(True)).json()
    ids = [r["id"] for r in body["fired"]]
    assert "palm.heart.very_long" in ids
    fired = next(r for r in body["fired"] if r["id"] == "palm.heart.very_long")
    assert fired["source"]["work"].startswith("Cheiro")
    assert fired["status"] == "extracted"


def test_requires_the_secret_and_valid_features() -> None:
    assert _client().post("/v1/rules/evaluate", json=_body(True)).status_code == 401
    bad = {"features": {"schema_version": "palm_features.v1"}}
    assert _client().post("/v1/rules/evaluate", headers=HEADERS, json=bad).status_code == 422
