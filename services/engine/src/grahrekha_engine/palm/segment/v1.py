"""Adapter for GrahRekha's own line segmenter (Phase 2), trained in the canonical frame.

Unlike v0 there is no model-specific crop: the input is the rectified palm itself, so
predictions are already in the frame all features are measured in. Adds a fate class.
RESEARCH ONLY until trained on licence-cleared data (model card, D-006).
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from numpy.typing import NDArray

from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.rectify import CANONICAL_SIZE

MODEL_ID = "grahrekha-lines-v1"
MODEL_INPUT = 512
LINE_CLASSES = ("heart", "head", "life", "fate")  # output channels 1..4 (0 = background)
_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
_STD = np.array([0.229, 0.224, 0.225], np.float32)


def preprocess(canonical_image: RGBImage) -> NDArray[np.float32]:
    small = cv2.resize(canonical_image, (MODEL_INPUT, MODEL_INPUT), interpolation=cv2.INTER_AREA)
    x = (small.astype(np.float32) / 255.0 - _MEAN) / _STD
    result: NDArray[np.float32] = np.ascontiguousarray(x.transpose(2, 0, 1)[None])
    return result


def logits_to_canonical_probs(logits: NDArray[np.float32]) -> NDArray[np.float32]:
    """(1, 5, 512, 512) logits -> (4, 1024, 1024) line probabilities."""
    z = logits[0] - logits[0].max(axis=0, keepdims=True)
    exp = np.exp(z)
    probs = exp / exp.sum(axis=0, keepdims=True)
    size = (CANONICAL_SIZE, CANONICAL_SIZE)
    maps = [cv2.resize(probs[c], size, interpolation=cv2.INTER_LINEAR) for c in range(1, 5)]
    result: NDArray[np.float32] = np.clip(np.stack(maps), 0.0, 1.0).astype(np.float32)
    return result


class CanonicalLineSegmenter:
    def __init__(self, weights: Path) -> None:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        self._session = ort.InferenceSession(
            str(weights), sess_options=options, providers=["CPUExecutionProvider"]
        )

    def predict(self, canonical_image: RGBImage) -> NDArray[np.float32]:
        (logits,) = self._session.run(["logits"], {"input": preprocess(canonical_image)})
        return logits_to_canonical_probs(np.asarray(logits, dtype=np.float32))
