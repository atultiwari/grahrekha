from pathlib import Path

import numpy as np
import pytest

from grahrekha_engine.palm.rectify import CANONICAL_SIZE
from grahrekha_engine.palm.segment.v1 import (
    LINE_CLASSES,
    MODEL_INPUT,
    CanonicalLineSegmenter,
    logits_to_canonical_probs,
    preprocess,
)

WEIGHTS = Path(__file__).resolve().parents[2] / "models/weights/M9-grahrekha-lines-v1/model.onnx"


def test_line_classes_include_fate() -> None:
    assert LINE_CLASSES == ("heart", "head", "life", "fate")


def test_preprocess_resizes_and_normalises_to_nchw() -> None:
    image = np.full((CANONICAL_SIZE, CANONICAL_SIZE, 3), 128, np.uint8)
    x = preprocess(image)
    assert x.shape == (1, 3, MODEL_INPUT, MODEL_INPUT)
    assert x.dtype == np.float32
    assert abs(float(x[0, 0].mean()) - (128 / 255 - 0.485) / 0.229) < 1e-3


def test_logits_become_canonical_line_probabilities() -> None:
    logits = np.full((1, 5, MODEL_INPUT, MODEL_INPUT), -10.0, np.float32)
    logits[0, 0] = 10.0  # background everywhere...
    logits[0, 0, 100:110, :] = -10.0
    logits[0, 4, 100:110, :] = 10.0  # ...except a fate band
    probs = logits_to_canonical_probs(logits)
    assert probs.shape == (4, CANONICAL_SIZE, CANONICAL_SIZE)
    assert probs[3, 210, 500] > 0.99  # band at 100-110 (512px) -> ~200-220 (1024px)
    assert probs[3, 600, 500] < 0.01
    assert probs.max() <= 1.0 and probs.min() >= 0.0


@pytest.mark.models
def test_real_model_runs_on_a_canonical_image() -> None:
    if not WEIGHTS.exists():
        pytest.skip("train and export v1 first (ml/)")
    probs = CanonicalLineSegmenter(WEIGHTS).predict(
        np.zeros((CANONICAL_SIZE, CANONICAL_SIZE, 3), np.uint8)
    )
    assert probs.shape == (4, CANONICAL_SIZE, CANONICAL_SIZE)
