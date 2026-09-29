from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest

from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.landmarks import HandLandmarkDetector
from grahrekha_engine.palm.rectify import CANONICAL_SIZE, rectify
from grahrekha_engine.palm.segment.v0 import (
    INPUT_SIZE,
    LINE_CLASSES,
    PalmLineReaderV0,
    model_crop_transform,
)
from tests.palm.synthetic import detection, right_palm_points, rotate

WEIGHTS = (
    Path(__file__).resolve().parents[2] / "models/weights/M2-palm-line-reader/student_fp16.onnx"
)


def _apply(a: np.ndarray, pts: np.ndarray) -> np.ndarray:
    result: np.ndarray = pts @ a[:, :2].T + a[:, 2]
    return result


@pytest.mark.parametrize("degrees", [0, 40, 95, 180, -70])
def test_crop_puts_hand_upright_and_inside_the_input(degrees: float) -> None:
    pts = rotate(right_palm_points(), degrees)
    crop = _apply(model_crop_transform(detection(pts, "left"), margin_ratio=0.25), pts)

    assert abs(crop[9, 0] - crop[0, 0]) < 1e-6  # middle MCP straight above the wrist
    assert crop[9, 1] < crop[0, 1]
    assert (crop >= 0).all() and (crop <= INPUT_SIZE).all()


def test_mirrors_when_mediapipe_label_is_not_left() -> None:
    # The v0 model was trained with every hand flipped to MediaPipe's "Left" label.
    pts = right_palm_points()
    as_left = model_crop_transform(detection(pts, "left"), margin_ratio=0.25)
    as_right = model_crop_transform(detection(pts, "right"), margin_ratio=0.25)
    assert np.linalg.det(as_left[:, :2]) > 0
    assert np.linalg.det(as_right[:, :2]) < 0


def test_line_classes_match_the_model_contract() -> None:
    assert LINE_CLASSES == ("heart", "head", "life")


@pytest.mark.models
class TestModel:
    @pytest.fixture(scope="class")
    def model(self) -> PalmLineReaderV0:
        if not WEIGHTS.exists():
            pytest.skip("run scripts/fetch-data.sh --only M2")
        return PalmLineReaderV0(WEIGHTS)

    @pytest.fixture(scope="class")
    def detector(self, hand_model_path: Path) -> Iterator[HandLandmarkDetector]:
        with HandLandmarkDetector(hand_model_path) as d:
            yield d

    def test_produces_canonical_probability_maps_with_lines_on_the_palm(
        self, model: PalmLineReaderV0, detector: HandLandmarkDetector, example_palm: RGBImage
    ) -> None:
        det = detector.detect(example_palm)[0]
        rect = rectify(example_palm, det)
        probs = model.predict(example_palm, det, rect)

        assert probs.shape == (len(LINE_CLASSES), CANONICAL_SIZE, CANONICAL_SIZE)
        assert probs.dtype == np.float32
        assert probs.min() >= 0.0 and probs.max() <= 1.0
        # Each major line should be confidently present somewhere on this clear palm.
        assert (probs.reshape(3, -1).max(axis=1) > 0.5).all()
        # ...and lines are thin: only a small fraction of the canvas is "line".
        assert (probs > 0.5).mean() < 0.05

    def test_mirrored_photo_gives_mirror_consistent_lines(
        self, model: PalmLineReaderV0, detector: HandLandmarkDetector, example_palm: RGBImage
    ) -> None:
        # Canonical frame is chirality-normalised, so a mirrored photo should yield
        # nearly the same canonical line maps.
        flipped = np.ascontiguousarray(example_palm[:, ::-1])
        d = detector.detect(example_palm)[0]
        e = detector.detect(flipped)[0]
        a = model.predict(example_palm, d, rectify(example_palm, d))
        b = model.predict(flipped, e, rectify(flipped, e))
        union = int(((a > 0.5) | (b > 0.5)).sum())
        overlap = int(((a > 0.5) & (b > 0.5)).sum()) / max(1, union)
        assert overlap > 0.3
