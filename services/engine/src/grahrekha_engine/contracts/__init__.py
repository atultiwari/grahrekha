"""Versioned API contracts. Source of truth for the TypeScript types in packages/contracts.

Add a model here, list it in CONTRACTS, then run `pnpm contracts:gen` from the repo root.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    # Serialization-mode JSON Schema marks defaulted fields as required: responses always
    # include them, so generated TypeScript types need not treat them as optional.
    model_config = ConfigDict(
        extra="forbid", frozen=True, json_schema_serialization_defaults_required=True
    )


class HealthResponse(Contract):
    status: Literal["ok"]
    version: str


def _contracts() -> list[tuple[str, type[Contract]]]:
    from grahrekha_engine.contracts.palm import PalmAnalysisV1
    from grahrekha_engine.contracts.rules import RulesRequestV1, RulesResponseV1

    return [
        ("health_response.v1", HealthResponse),
        ("palm_analysis.v1", PalmAnalysisV1),
        ("rules_request.v1", RulesRequestV1),
        ("rules_response.v1", RulesResponseV1),
    ]


# (versioned name, model): names are part of the public contract; never reuse a name.
CONTRACTS: list[tuple[str, type[Contract]]] = _contracts()
