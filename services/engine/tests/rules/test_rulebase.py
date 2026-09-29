from pathlib import Path

import pytest

from grahrekha_engine.contracts.palm import HandGeometryV1, LineFeaturesV1, PalmFeaturesV1
from grahrekha_engine.rules.engine import evaluate_rules
from grahrekha_engine.rules.lint import lint_rules
from grahrekha_engine.rules.model import (
    Rule,
    Tier,
    load_feature_tiers,
    load_rules,
    rulebase_version,
)

RULES_DIR = Path(__file__).resolve().parents[4] / "rules"


def _rule(**overrides: object) -> Rule:
    base: dict[str, object] = {
        "id": "palm.test.rule",
        "tradition": "western",
        "engine": "palm",
        "domain": "love_relationships",
        "when": {"==": [{"var": "lines.heart.present"}, True]},
        "statement": {"en": "You value loyalty."},
        "polarity": "positive",
        "strength": 2,
        "source": {"work": "Cheiro, Palmistry for All (1916)", "locator": "Chapter VII"},
        "review": {"status": "extracted"},
    }
    return Rule.model_validate(base | overrides)


def _features(
    heart_len: float = 0.6, end: str = "under_index", certain: bool = True
) -> PalmFeaturesV1:
    geometry = HandGeometryV1(
        palm_length_width_ratio=1.5,
        finger_to_palm_ratio=0.8,
        palm_shape="medium",
        finger_length="medium",
        element="mixed",
        digit_ratio_2d4d=0.98,
        index_vs_ring="equal",
        thumb_opening_deg=50.0,
    )
    lines = {n: LineFeaturesV1(name=n, present=False) for n in ("heart", "head", "life", "fate")}
    lines["heart"] = LineFeaturesV1(
        name="heart",
        present=True,
        length=heart_len,
        end_zone=end,
        end_zone_certain=certain,
    )
    return PalmFeaturesV1(
        hand="left", mirrored=False, hand_geometry=geometry, lines=lines, pipeline={}
    )


TIERS: dict[str, Tier] = {
    "lines.heart.present": "reliable",
    "lines.heart.end_zone": "reliable",
    "lines.heart.end_zone_certain": "reliable",
    "lines.heart.length": "reliable",
}


def test_real_rule_base_passes_lint() -> None:
    rules = load_rules(RULES_DIR / "palm")
    assert rules, "rule base should not be empty"
    assert lint_rules(rules, load_feature_tiers(RULES_DIR / "feature-tiers.yaml")) == []


def test_lint_rejects_health_and_lifespan_claims() -> None:
    bad = _rule(statement={"en": "This line shows a long life and good health."})
    problems = lint_rules([bad], TIERS)
    assert any("banned" in p for p in problems)


def test_lint_rejects_unknown_features() -> None:
    bad = _rule(when={"==": [{"var": "lines.heart.colour"}, "red"]})
    assert any("unknown feature" in p for p in lint_rules([bad], TIERS))


def test_lint_requires_zone_certainty_alongside_zones() -> None:
    bad = _rule(when={"==": [{"var": "lines.heart.end_zone"}, "under_index"]})
    assert any("certain" in p for p in lint_rules([bad], TIERS))


def test_lint_blocks_approval_of_experimental_or_blocked_rules() -> None:
    experimental = _rule(
        when={"==": [{"var": "head_life_joined"}, True]},
        review={"status": "approved", "reviewer": "owner"},
    )
    blocked = _rule(
        validity_blocker="segmenter truncates the line",
        review={"status": "approved", "reviewer": "owner"},
    )
    problems = lint_rules([experimental, blocked], TIERS)
    assert any("experimental" in p for p in problems)
    assert any("validity blocker" in p for p in problems)


def test_lint_rejects_duplicate_ids_and_missing_reviewer_on_approval() -> None:
    a, b = _rule(), _rule()
    no_reviewer = _rule(id="palm.test.other", review={"status": "approved"})
    problems = lint_rules([a, b, no_reviewer], TIERS)
    assert any("duplicate" in p for p in problems)
    assert any("reviewer" in p for p in problems)


def test_evaluation_fires_matching_rules_with_citations() -> None:
    rule = _rule(
        when={
            "and": [
                {"==": [{"var": "lines.heart.end_zone"}, "under_index"]},
                {"==": [{"var": "lines.heart.end_zone_certain"}, True]},
            ]
        }
    )
    fired = evaluate_rules(_features(), [rule])
    assert [f.id for f in fired] == ["palm.test.rule"]
    assert fired[0].source.locator == "Chapter VII"
    assert evaluate_rules(_features(certain=False), [rule]) == []  # uncertain zone: no reading


def test_mutually_exclusive_rules_keep_the_stronger() -> None:
    weak = _rule(id="palm.test.weak", strength=1, excludes=["palm.test.strong"])
    strong = _rule(id="palm.test.strong", strength=3)
    assert [f.id for f in evaluate_rules(_features(), [weak, strong])] == ["palm.test.strong"]


def test_evaluation_is_deterministic_and_versioned() -> None:
    rules = load_rules(RULES_DIR / "palm")
    assert evaluate_rules(_features(), rules) == evaluate_rules(_features(), rules)
    assert len(rulebase_version(RULES_DIR)) == 12


@pytest.mark.parametrize("status", ["approved", "reviewed"])
def test_status_filter(status: str) -> None:
    rule = _rule(review={"status": "extracted"})
    assert evaluate_rules(_features(), [rule], statuses={status}) == []  # type: ignore[arg-type]
