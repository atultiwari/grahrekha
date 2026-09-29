import cv2
import numpy as np
import pytest

from grahrekha_engine.palm.segment.postprocess import PostprocessConfig, trace_line


def _canvas() -> np.ndarray:
    return np.zeros((1024, 1024), np.float32)


def _draw(
    prob: np.ndarray, pts: list[tuple[int, int]], value: float = 0.9, width: int = 9
) -> np.ndarray:
    out = prob.copy()
    cv2.polylines(out, [np.array(pts, np.int32)], False, value, width)
    return out


def test_empty_map_has_no_line() -> None:
    assert trace_line(_canvas()) is None


def test_traces_a_straight_line_with_correct_length_and_confidence() -> None:
    prob = _draw(_canvas(), [(200, 500), (800, 500)])
    trace = trace_line(prob)
    assert trace is not None
    assert len(trace.segments) == 1
    assert trace.length_px == pytest.approx(600, abs=15)
    assert trace.confidence == pytest.approx(0.9, abs=0.05)
    assert trace.gaps_px == []


def test_traces_a_curved_line_in_order() -> None:
    arc = [
        (int(500 + 300 * np.cos(t)), int(500 + 300 * np.sin(t))) for t in np.linspace(0, np.pi, 60)
    ]
    trace = trace_line(_draw(_canvas(), arc))
    assert trace is not None
    pts = trace.segments[0]
    # Ordered along the arc (not a pixel cloud): the angle around the centre is monotonic.
    angles = np.arctan2(pts[:, 1] - 500, pts[:, 0] - 500)
    steps = np.diff(angles)
    assert (steps >= -1e-6).all() or (steps <= 1e-6).all()
    assert trace.length_px == pytest.approx(np.pi * 300, rel=0.05)


def test_broken_line_keeps_segments_and_measures_the_gap() -> None:
    prob = _draw(_draw(_canvas(), [(100, 400), (450, 400)]), [(530, 400), (900, 400)])
    trace = trace_line(prob)
    assert trace is not None
    assert len(trace.segments) == 2
    assert trace.gaps_px == [pytest.approx(80, abs=15)]


def test_removes_specks_and_side_spurs() -> None:
    prob = _draw(_canvas(), [(200, 500), (800, 500)])
    prob = _draw(prob, [(500, 500), (500, 470)], width=5)  # short spur
    prob[100:104, 100:104] = 0.95  # speck
    trace = trace_line(prob)
    assert trace is not None
    assert len(trace.segments) == 1
    assert trace.length_px == pytest.approx(600, abs=20)


def test_distant_fragments_are_not_linked() -> None:
    config = PostprocessConfig(max_gap_px=100)
    prob = _draw(_draw(_canvas(), [(100, 200), (400, 200)]), [(600, 800), (900, 800)])
    trace = trace_line(prob, config)
    assert trace is not None
    assert len(trace.segments) == 1  # keeps the strongest/longest piece only
