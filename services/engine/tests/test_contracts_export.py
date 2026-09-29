import json
from pathlib import Path

from grahrekha_engine.contracts import CONTRACTS, HealthResponse
from grahrekha_engine.contracts.export import export_schemas


def test_every_contract_has_a_stable_versioned_name() -> None:
    names = [name for name, _ in CONTRACTS]
    assert names == sorted(set(names)), "contract names must be unique and sorted"
    assert all("." in name for name in names), "names look like 'health_response.v1'"


def test_export_writes_one_json_schema_per_contract(tmp_path: Path) -> None:
    written = export_schemas(tmp_path)

    assert sorted(p.name for p in written) == sorted(f"{name}.json" for name, _ in CONTRACTS)
    schema = json.loads((tmp_path / "health_response.v1.json").read_text())
    assert schema["title"] == "HealthResponse"
    assert set(schema["required"]) == {"status", "version"}


def test_export_is_deterministic(tmp_path: Path) -> None:
    first = [p.read_text() for p in export_schemas(tmp_path / "a")]
    second = [p.read_text() for p in export_schemas(tmp_path / "b")]
    assert first == second


def test_healthz_response_matches_contract() -> None:
    HealthResponse.model_validate({"status": "ok", "version": "0.1.0"})
