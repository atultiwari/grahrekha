"""Rule evaluation contracts."""

from typing import Literal

from grahrekha_engine.contracts import Contract
from grahrekha_engine.contracts.palm import PalmFeaturesV1


class SourceV1(Contract):
    work: str
    locator: str
    edition: str | None = None
    quote: str | None = None


class FiredRuleV1(Contract):
    id: str
    domain: str
    polarity: Literal["positive", "neutral", "caution"]
    strength: int
    statement: dict[str, str]
    source: SourceV1
    status: Literal["extracted", "reviewed", "approved", "rejected"]
    mapping_note: str | None = None
    validity_blocker: str | None = None


class RulesRequestV1(Contract):
    features: PalmFeaturesV1
    # Lab only: also fire rules not yet approved by a reviewer (D-008). Never in production.
    include_unreviewed: bool = False


class RulesResponseV1(Contract):
    rulebase_version: str
    fired: list[FiredRuleV1]
