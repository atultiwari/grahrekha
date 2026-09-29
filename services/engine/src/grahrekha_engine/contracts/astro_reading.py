"""Astrology reading: chart + rule-ready features + fired rules (rules/astro)."""

from typing import Literal

from grahrekha_engine.contracts import Contract
from grahrekha_engine.contracts.astro import AstroChartV1, AstroFeaturesV1, AstroRequestV1
from grahrekha_engine.contracts.rules import RulesResponseV1


class AstroReadingRequestV1(AstroRequestV1):
    # Lab only: also fire rules not yet approved by a reviewer (D-008). Never in production.
    include_unreviewed: bool = False


class AstroReadingV1(Contract):
    schema_version: Literal["astro_reading.v1"] = "astro_reading.v1"
    chart: AstroChartV1
    features: AstroFeaturesV1
    rules: RulesResponseV1
