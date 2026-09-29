"""Rule base lint, run in CI (D-008, D-009, D-015). Returns human-readable problems."""

import re
from collections import Counter
from typing import Any, get_args, get_origin

from pydantic import BaseModel

from grahrekha_engine.contracts.palm import PalmFeaturesV1
from grahrekha_engine.rules.jsonlogic import referenced_vars
from grahrekha_engine.rules.model import Rule, Tier

# D-009: never make health, lifespan, disease, fertility or accident claims.
BANNED = re.compile(
    r"\b(health\w*|illness|disease\w*|sick\w*|lifespan|life\s*span|long life|short life|"
    r"longevity|death|die|dies|dying|fatal\w*|cancer|stroke|surgery|pregnan\w*|fertil\w*|"
    r"infertil\w*|childless|accident\w*|constitution|vital organs?|digestion|stomach)\b",
    re.IGNORECASE,
)


def _paths(model: type[BaseModel], prefix: str = "") -> set[str]:
    paths: set[str] = set()
    for name, field in model.model_fields.items():
        annotation: Any = field.annotation
        paths.add(prefix + name)
        if get_origin(annotation) is dict:
            key_type, value_type = get_args(annotation)
            if isinstance(value_type, type) and issubclass(value_type, BaseModel):
                for key in get_args(key_type):
                    paths |= _paths(value_type, f"{prefix}{name}.{key}.")
        elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
            paths |= _paths(annotation, f"{prefix}{name}.")
    return paths


FEATURE_PATHS = _paths(PalmFeaturesV1)


def lint_rules(rules: list[Rule], tiers: dict[str, Tier]) -> list[str]:
    problems: list[str] = []
    for rule_id, count in Counter(r.id for r in rules).items():
        if count > 1:
            problems.append(f"{rule_id}: duplicate id")
    for rule in rules:
        where = rule.id
        for lang, text in rule.statement.items():
            if match := BANNED.search(text):
                problems.append(
                    f"{where}: banned term {match.group(0)!r} in statement.{lang} (D-009)"
                )
        if not rule.source.work.strip() or not rule.source.locator.strip():
            problems.append(f"{where}: source.work and source.locator are required")

        used = referenced_vars(rule.when)
        for path in sorted(used - FEATURE_PATHS):
            problems.append(f"{where}: unknown feature {path!r}")
        for path in sorted(p for p in used if p.endswith("_zone")):
            if f"{path}_certain" not in used:
                problems.append(
                    f"{where}: uses {path} without {path}_certain (zones must be certain)"
                )

        if rule.review.status == "approved":
            if not rule.review.reviewer:
                problems.append(f"{where}: approved rules need a reviewer")
            if rule.validity_blocker:
                problems.append(f"{where}: cannot be approved with a validity blocker")
            for path in sorted(used):
                if tiers.get(path, "experimental") == "experimental":
                    problems.append(
                        f"{where}: approved rule uses experimental feature {path!r} (D-015)"
                    )
    return problems
