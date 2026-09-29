"""Evaluate rules against features: deterministic selection with citations."""

from grahrekha_engine.contracts.palm import PalmFeaturesV1
from grahrekha_engine.contracts.rules import FiredRuleV1, SourceV1
from grahrekha_engine.rules.jsonlogic import evaluate
from grahrekha_engine.rules.model import Rule, Status


def evaluate_rules(
    features: PalmFeaturesV1, rules: list[Rule], statuses: set[Status] | None = None
) -> list[FiredRuleV1]:
    """Rules whose condition holds, minus those excluded by a stronger fired rule.

    `statuses` limits which review states may fire (production: {"approved"}).
    Output order: domain, then strength (desc), then id, so results are stable.
    """
    data = features.model_dump()
    allowed = statuses or {"extracted", "reviewed", "approved"}
    matched = [r for r in rules if r.review.status in allowed and bool(evaluate(r.when, data))]
    by_id = {r.id: r for r in matched}
    dropped: set[str] = set()
    for rule in sorted(matched, key=lambda r: (-r.strength, r.id)):
        if rule.id in dropped:
            continue
        for excluded_id in rule.excludes:
            if excluded_id in by_id and by_id[excluded_id].strength <= rule.strength:
                dropped.add(excluded_id)
        for candidate in matched:  # exclusions declared on either side
            if rule.id in candidate.excludes and candidate.strength < rule.strength:
                dropped.add(candidate.id)
    kept = sorted(
        (r for r in matched if r.id not in dropped), key=lambda r: (r.domain, -r.strength, r.id)
    )
    return [
        FiredRuleV1(
            id=r.id,
            domain=r.domain,
            polarity=r.polarity,
            strength=r.strength,
            statement=dict(r.statement),
            source=SourceV1.model_validate(r.source.model_dump()),
            status=r.review.status,
            mapping_note=r.mapping_note,
            validity_blocker=r.validity_blocker,
        )
        for r in kept
    ]
