"""Versioned API contracts. Source of truth for the TypeScript types in packages/contracts.

Add a model here, list it in CONTRACTS, then run `pnpm contracts:gen` from the repo root.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HealthResponse(Contract):
    status: Literal["ok"]
    version: str


# (versioned name, model): names are part of the public contract; never reuse a name.
CONTRACTS: list[tuple[str, type[Contract]]] = [
    ("health_response.v1", HealthResponse),
]
