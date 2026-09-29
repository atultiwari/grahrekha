from pathlib import Path

from grahrekha_engine.astro.features import astro_features
from grahrekha_engine.rules.engine import evaluate_rules
from grahrekha_engine.rules.lint import lint_rules
from grahrekha_engine.rules.model import Rule, Tier, load_feature_tiers, load_rules
from tests.astro.test_features import _chart

RULES_DIR = Path(__file__).resolve().parents[4] / "rules"
TIERS: dict[str, Tier] = {"planets.Sun.house": "reliable"}
EXACT = {"==": [{"var": "time_confidence"}, "exact"]}
MOON_CERTAIN = {"==": [{"var": "moon_nakshatra_uncertain"}, False]}


def _astro_rule(when: dict[str, object], **overrides: object) -> Rule:
    base: dict[str, object] = {
        "id": "astro.test.rule",
        "tradition": "vedic",
        "engine": "astro",
        "domain": "career_work",
        "when": when,
        "statement": {"en": "You work steadily towards recognition."},
        "polarity": "positive",
        "strength": 2,
        "source": {"work": "Brihat Jataka, tr. N. Chidambaram Iyer (1885)", "locator": "XX.3"},
    }
    return Rule.model_validate(base | overrides)


def test_astro_rules_are_linted_against_astro_features() -> None:
    ok = _astro_rule({"and": [EXACT, {"==": [{"var": "planets.Sun.house"}, 10]}]})
    assert lint_rules([ok], TIERS) == []
    palm_var = _astro_rule({"and": [EXACT, {"==": [{"var": "lines.heart.present"}, True]}]})
    assert any("unknown feature" in p for p in lint_rules([palm_var], TIERS))


def test_house_rules_must_require_an_exact_birth_time() -> None:
    bad = _astro_rule({"==": [{"var": "planets.Sun.house"}, 10]})
    assert any("time_confidence" in p for p in lint_rules([bad], TIERS))
    bad_lordship = _astro_rule({"in": [5, {"var": "mahadasha.houses_ruled"}]})
    problems = lint_rules([bad_lordship], TIERS)
    assert any("time_confidence" in p for p in problems)
    assert any("moon_nakshatra_uncertain" in p for p in problems)


def test_dasha_rules_must_require_a_certain_moon() -> None:
    bad = _astro_rule({"==": [{"var": "mahadasha.lord"}, "Jupiter"]})
    assert any("moon_nakshatra_uncertain" in p for p in lint_rules([bad], TIERS))
    ok = _astro_rule({"and": [MOON_CERTAIN, {"==": [{"var": "mahadasha.lord"}, "Jupiter"]}]})
    assert lint_rules([ok], TIERS) == []


def test_astro_rules_fire_on_astro_features() -> None:
    rule = _astro_rule({"and": [EXACT, {"==": [{"var": "planets.Sun.house"}, 10]}]})
    features = astro_features(_chart("Leo", {"Sun": 10}, md="Mars", ad="Saturn"))
    assert [f.id for f in evaluate_rules(features, [rule])] == ["astro.test.rule"]
    unknown_time = astro_features(_chart(None, {"Sun": 10}, md="Mars", ad="Saturn"))
    assert evaluate_rules(unknown_time, [rule]) == []


def test_real_astro_rule_base_passes_lint() -> None:
    rules = load_rules(RULES_DIR / "astro")
    assert rules, "rules/astro should not be empty"
    assert all(r.engine == "astro" and r.tradition == "vedic" for r in rules)
    assert lint_rules(rules, load_feature_tiers(RULES_DIR / "feature-tiers.yaml")) == []
