"""Rule base model and loading (docs/ARCHITECTURE.md §6, D-008, D-015)."""

import hashlib
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

Tier = Literal["reliable", "moderate", "experimental"]
Status = Literal["extracted", "reviewed", "approved", "rejected"]


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(_Frozen):
    work: str
    locator: str
    edition: str | None = None
    quote: str | None = None  # short public-domain extract supporting the rule


class Review(_Frozen):
    status: Status = "extracted"
    reviewer: str | None = None
    notes: str = ""


class Rule(_Frozen):
    id: str = Field(pattern=r"^[a-z]+(\.[a-z0-9_]+)+$")
    tradition: Literal["western", "vedic", "chinese"]
    engine: Literal["palm", "astro"]
    domain: Literal[
        "personality_temperament",
        "mind_learning",
        "love_relationships",
        "career_work",
        "money_resources",
        "vitality_energy",
        "life_path_timing",
        "measured_facts",
    ]
    when: dict[str, Any]
    statement: dict[Literal["en", "hi"], str]
    polarity: Literal["positive", "neutral", "caution"]
    strength: int = Field(ge=1, le=3)
    excludes: list[str] = Field(default_factory=list)
    source: Source
    mapping_note: str | None = None  # how the author's terms map onto our features
    validity_blocker: str | None = None  # known measurement artefact; blocks approval
    review: Review = Review()


def load_rules(directory: Path) -> list[Rule]:
    """Load every *.yaml file (a list of rules each) under directory, sorted by path."""
    rules: list[Rule] = []
    for path in sorted(directory.rglob("*.yaml")):
        entries = yaml.safe_load(path.read_text()) or []
        rules.extend(Rule.model_validate(entry) for entry in entries)
    return rules


def load_feature_tiers(path: Path) -> dict[str, Tier]:
    raw: dict[str, list[str]] = yaml.safe_load(path.read_text())
    return {feature: tier for tier, features in raw.items() for feature in features}  # type: ignore[misc]


def rulebase_version(rules_root: Path) -> str:
    """Content hash of every rule file: changes whenever any rule text changes."""
    digest = hashlib.sha256()
    for path in sorted(rules_root.rglob("*.yaml")):
        digest.update(path.relative_to(rules_root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]
