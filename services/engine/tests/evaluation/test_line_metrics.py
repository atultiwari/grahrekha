import cv2
import numpy as np
import pytest

from grahrekha_engine.evaluation.line_metrics import tolerant_scores


def _mask(lines: list[list[tuple[int, int]]], width: int = 7) -> np.ndarray:
    m = np.zeros((400, 400), np.uint8)
    for pts in lines:
        cv2.polylines(m, [np.array(pts, np.int32)], False, 255, width)
    return m > 0


def test_identical_lines_score_perfectly() -> None:
    gt = _mask([[(50, 200), (350, 200)]])
    s = tolerant_scores(gt, gt, tolerance_px=3)
    assert s.precision == pytest.approx(1.0) and s.recall == pytest.approx(1.0)


def test_small_offset_within_tolerance_still_counts() -> None:
    gt = _mask([[(50, 200), (350, 200)]])
    pred = _mask([[(50, 205), (350, 205)]], width=1)
    assert tolerant_scores(pred, gt, tolerance_px=8).f1 == pytest.approx(1.0, abs=0.02)
    assert tolerant_scores(pred, gt, tolerance_px=1).f1 < 0.2


def test_missing_line_lowers_recall_not_precision() -> None:
    gt = _mask([[(50, 100), (350, 100)], [(50, 300), (350, 300)]])
    pred = _mask([[(50, 100), (350, 100)]], width=1)
    s = tolerant_scores(pred, gt, tolerance_px=4)
    assert s.precision == pytest.approx(1.0, abs=0.02)
    assert s.recall == pytest.approx(0.5, abs=0.05)


def test_spurious_line_lowers_precision_not_recall() -> None:
    gt = _mask([[(50, 100), (350, 100)]])
    pred = _mask([[(50, 100), (350, 100)], [(50, 300), (350, 300)]], width=1)
    s = tolerant_scores(pred, gt, tolerance_px=4)
    assert s.recall == pytest.approx(1.0, abs=0.02)
    assert s.precision == pytest.approx(0.5, abs=0.05)


def test_empty_prediction_and_empty_truth() -> None:
    gt = _mask([[(50, 100), (350, 100)]])
    empty = np.zeros_like(gt)
    assert tolerant_scores(empty, gt, tolerance_px=4).recall == 0.0
    assert tolerant_scores(empty, empty, tolerance_px=4).f1 == 1.0
