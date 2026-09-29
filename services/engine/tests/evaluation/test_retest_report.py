from grahrekha_engine.contracts.palm import HandGeometryV1, LineFeaturesV1, PalmFeaturesV1
from grahrekha_engine.evaluation.retest_eval import pair_agreement, report, zone_coverage


def _features(heart_zone: str, certain: bool, shape: str = "square") -> PalmFeaturesV1:
    geometry = HandGeometryV1(
        palm_length_width_ratio=1.4,
        finger_to_palm_ratio=0.8,
        palm_shape=shape,
        finger_length="short",
        element="earth",
        digit_ratio_2d4d=0.98,
        index_vs_ring="equal",
        thumb_opening_deg=50.0,
    )
    lines = {n: LineFeaturesV1(name=n, present=False) for n in ("heart", "head", "life", "fate")}
    lines["heart"] = LineFeaturesV1(
        name="heart",
        present=True,
        length=0.9,
        start_zone="percussion",
        end_zone=heart_zone,
        start_zone_certain=True,
        end_zone_certain=certain,
    )
    return PalmFeaturesV1(
        hand="left", mirrored=False, hand_geometry=geometry, lines=lines, pipeline={}
    )


def test_pair_agreement() -> None:
    assert pair_agreement(["a", "a", "a"]) == 1.0
    assert pair_agreement(["a", "a", "b"]) == 1 / 3
    assert pair_agreement(["a"]) == 1.0


def test_zone_coverage_counts_certain_endpoints_of_present_lines() -> None:
    groups = {"g": [_features("under_index", True), _features("under_index", False)]}
    assert zone_coverage(groups) == 3 / 4  # 4 heart endpoints, 3 certain


def test_report_treats_uncertain_zones_as_uncertain_and_scores_agreement() -> None:
    groups = {
        "stable": [_features("under_index", True), _features("under_index", True)],
        "flippy": [
            _features("under_index", True, "square"),
            _features("under_index", True, "long"),
        ],
    }
    text = report(groups, latencies=[0.4, 0.5], rejected=1)
    assert "photos rejected by the gate: 1" in text
    assert "| heart.end_zone | 1.00 |" in text
    assert "| palm_shape | 0.50 |" in text
    assert "p95" in text
