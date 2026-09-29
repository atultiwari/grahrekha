from grahrekha_engine.evaluation.multiphoto_eval import report


def test_report_shows_single_vs_aggregated_agreement() -> None:
    text = report(
        {"heart.present": 0.8, "palm_shape": 0.4},
        {"heart.present": 1.0, "palm_shape": 0.6},
        (0.3, 0.4),
        20,
    )
    assert "Hands compared: 20" in text
    assert "| heart.present | 0.80 | 1.00 |" in text
    assert "1 photo 0.60 → 3 photos 0.80" in text
    assert "Zone coverage (certain endpoints): 1 photo 0.30, 3 photos 0.40" in text
