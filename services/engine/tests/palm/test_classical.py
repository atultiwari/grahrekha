import cv2
import numpy as np

from grahrekha_engine.palm.rectify import CANONICAL_SIZE
from grahrekha_engine.palm.segment.classical import detect_fate_line, ridge_map

RNG = np.random.default_rng(1)


def _skin(noise: float = 6.0) -> np.ndarray:
    base = np.full((CANONICAL_SIZE, CANONICAL_SIZE, 3), (200, 160, 140), np.float64)
    base += RNG.normal(0, noise, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def _with_crease(image: np.ndarray, pts: list[tuple[int, int]], width: int = 5) -> np.ndarray:
    out = image.copy()
    cv2.polylines(out, [np.array(pts, np.int32)], False, (120, 85, 70), width)
    return cv2.GaussianBlur(out, (0, 0), 1.2)


def test_ridge_map_highlights_dark_creases() -> None:
    image = _with_crease(_skin(), [(300, 500), (700, 500)])
    ridge = ridge_map(image)
    assert ridge.shape == (CANONICAL_SIZE, CANONICAL_SIZE)
    assert ridge[495:506, 400:600].max() > 5 * np.median(ridge[200:260, 400:600])


def test_detects_a_vertical_fate_line_along_the_crease() -> None:
    crease = [(505, 850), (500, 700), (495, 550), (490, 430)]
    trace = detect_fate_line(_with_crease(_skin(), crease))
    assert trace is not None
    xs = trace.segments[0][:, 0]
    assert np.abs(xs - 497).max() < 20  # follows the crease, not the noise
    assert trace.length_px > 300


def test_no_fate_line_on_plain_skin() -> None:
    assert detect_fate_line(_skin()) is None
