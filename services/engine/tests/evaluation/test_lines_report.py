import numpy as np

from grahrekha_engine.evaluation.line_metrics import LineScores
from grahrekha_engine.evaluation.lines_eval import TOLERANCES, ImageResult, _raster_traces, report
from grahrekha_engine.palm.rectify import rectify
from grahrekha_engine.palm.segment.postprocess import LineTrace
from tests.palm.synthetic import detection, right_palm_points


def _scores(p: float, r: float) -> dict[float, LineScores]:
    return {t: LineScores(p, r) for t in TOLERANCES}


def test_report_averages_only_gate_passing_images() -> None:
    results = [
        ImageResult("a", True, _scores(1.0, 0.5), _scores(0.8, 0.6), _scores(0.7, 0.9), 3, True),
        ImageResult("b", True, _scores(0.5, 0.5), _scores(0.6, 0.8), _scores(0.5, 0.7), 2, False),
        ImageResult("c", False, {}, {}, {}, 0, False),
    ]
    text = report(results)
    assert "Images: 3; passed the quality gate: 2" in text
    # F1 is the mean of per-image F1 scores (0.686), not F1 of the mean P/R (0.700).
    assert "| traced lines | 2.5% of palm length | 0.700 | 0.700 | 0.686 |" in text
    assert "Lines traced per palm: 0: 0, 1: 0, 2: 1, 3: 1" in text
    assert "Fate line reported: 1/2" in text


def test_traces_are_rasterised_back_into_original_image_coordinates() -> None:
    rect = rectify(np.zeros((1000, 1000, 3), np.uint8), detection(right_palm_points()))
    wrist_canonical = rect.to_canonical(right_palm_points()[[0]])[0]
    mcp_canonical = rect.to_canonical(right_palm_points()[[9]])[0]
    trace = LineTrace(
        segments=[np.array([wrist_canonical, mcp_canonical])], confidence=1.0, length_px=1.0
    )

    mask = _raster_traces([trace], rect, (1000, 1000))
    wx, wy = right_palm_points()[0].round().astype(int)
    assert mask[wy - 2 : wy + 3, wx - 2 : wx + 3].any()  # the line starts at the original wrist
