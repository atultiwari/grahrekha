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


def test_heart_end_zone_uses_the_index_side_end() -> None:
    import numpy as np

    from grahrekha_ml.per_line_eval import heart_end_zone

    # Canonical left-palm layout: the index side is small x. Heart band y < 560.
    points = np.array([[720.0, 420.0], [520.0, 400.0], [440.0, 380.0]])
    assert heart_end_zone(points) == "between_index_middle"
    assert heart_end_zone(points[:2]) == "under_middle"
    assert heart_end_zone(np.empty((0, 2))) is None


def test_zone_agreement_and_confusions() -> None:
    from grahrekha_ml.per_line_eval import zone_agreement

    pairs = [
        ("between_index_middle", "between_index_middle"),
        ("between_index_middle", "under_middle"),
        ("under_middle", "under_middle"),
        ("under_index", "under_index"),
    ]
    agreement, confusions = zone_agreement(pairs)
    assert agreement == 0.75
    assert confusions == {("between_index_middle", "under_middle"): 1}
    assert zone_agreement([]) == (None, {})
