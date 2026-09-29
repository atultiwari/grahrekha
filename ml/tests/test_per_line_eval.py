from grahrekha_ml.per_line_eval import LineTally, summarise


def test_summary_aggregates_recall_precision_and_presence_errors() -> None:
    tallies = {
        "heart": [LineTally(True, True, 0.9, 0.8), LineTally(True, False, 0.0, 0.0)],
        "fate": [LineTally(False, True, 0.0, 0.0), LineTally(False, False, 0.0, 0.0)],
    }
    rows = {r.line: r for r in summarise(tallies)}
    assert rows["heart"].truth_present == 2
    assert rows["heart"].missed == 1
    assert rows["heart"].recall == 0.45  # mean over palms where the line exists
    assert rows["heart"].precision == 0.8  # mean over palms where both exist
    assert rows["fate"].false_alarms == 1
    assert rows["fate"].recall is None  # no ground-truth fate lines
