import pytest

from grahrekha_engine.rules.jsonlogic import JsonLogicError, evaluate, referenced_vars

DATA = {
    "lines": {"heart": {"length": 0.6, "end_zone": "under_index", "present": True}},
    "joined": None,
}


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ({"==": [{"var": "lines.heart.end_zone"}, "under_index"]}, True),
        ({"!=": [{"var": "lines.heart.end_zone"}, "under_index"]}, False),
        ({"<": [{"var": "lines.heart.length"}, 0.7]}, True),
        ({">=": [{"var": "lines.heart.length"}, 0.7]}, False),
        ({"<=": [0.5, {"var": "lines.heart.length"}, 0.7]}, True),  # between
        ({"in": [{"var": "lines.heart.end_zone"}, ["under_index", "under_middle"]]}, True),
        (
            {"and": [{"var": "lines.heart.present"}, {"<": [{"var": "lines.heart.length"}, 1]}]},
            True,
        ),
        ({"or": [False, {"==": [1, 2]}]}, False),
        ({"!": [{"var": "lines.heart.present"}]}, False),
        ({"==": [{"var": "joined"}, True]}, False),  # None never equals True
    ],
)
def test_supported_operators(rule: dict[str, object], expected: bool) -> None:
    assert evaluate(rule, DATA) is expected


def test_comparisons_with_missing_values_are_false_not_errors() -> None:
    assert evaluate({"<": [{"var": "lines.fate.length"}, 1]}, DATA) is False
    assert evaluate({">": [{"var": "joined"}, 0]}, DATA) is False


def test_unknown_operators_are_rejected() -> None:
    with pytest.raises(JsonLogicError, match="unsupported"):
        evaluate({"eval": ["__import__('os')"]}, DATA)


def test_lists_the_feature_paths_a_rule_reads() -> None:
    rule = {"and": [{"==": [{"var": "a.b"}, 1]}, {"<": [{"var": "c"}, {"var": "d.e"}]}]}
    assert referenced_vars(rule) == {"a.b", "c", "d.e"}
