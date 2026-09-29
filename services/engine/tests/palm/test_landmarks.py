from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest

from grahrekha_engine.palm.gate import evaluate_gate
from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.landmarks import HandLandmarkDetector

pytestmark = pytest.mark.models


@pytest.fixture(scope="module")
def detector(hand_model_path: Path) -> Iterator[HandLandmarkDetector]:
    # Closing matters: an unclosed MediaPipe landmarker keeps worker threads alive and
    # hangs interpreter shutdown.
    instance = HandLandmarkDetector(hand_model_path)
    yield instance
    instance.close()


def test_detects_one_hand_with_21_pixel_landmarks(
    detector: HandLandmarkDetector, example_palm: RGBImage
) -> None:
    detections = detector.detect(example_palm)
    assert len(detections) == 1
    points = detections[0].landmarks
    w = example_palm.shape[1]
    assert points.shape == (21, 2)
    assert (points[:, 0] > 0).all() and (points[:, 0] < w).all()
    assert detections[0].handedness in ("left", "right")


def test_real_palm_passes_the_gate(detector: HandLandmarkDetector, example_palm: RGBImage) -> None:
    result = evaluate_gate(example_palm, detector.detect(example_palm))
    assert result.passed, [r.code for r in result.reasons]


def test_blank_image_has_no_hand(detector: HandLandmarkDetector) -> None:
    blank = np.full((512, 512, 3), 200, np.uint8)
    assert detector.detect(blank) == []


def test_mirrored_palm_is_rejected_as_back_of_hand_or_passes_as_other_hand(
    detector: HandLandmarkDetector, example_palm: RGBImage
) -> None:
    # A mirrored palm photo is still a palm (of the other hand); the gate must not
    # call it a back of hand. Guards the calibrated palm-facing rule end to end.
    mirrored = np.ascontiguousarray(example_palm[:, ::-1])
    result = evaluate_gate(mirrored, detector.detect(mirrored))
    assert "BACK_OF_HAND" not in {r.code for r in result.reasons}
