"""Adapter for the v0 line segmenter: samuelwbarber/palm-line-reader `student_fp16.onnx`.

PROTOTYPE ONLY (docs/DECISIONS.md D-006): the weights were trained on scraped photos,
so they are used for R&D and never shipped. The adapter reproduces the model's
training-time crop exactly (see its pipeline/hand_preprocess.py and model_meta.json):
  1. rotate so the wrist -> middle-MCP axis points up;
  2. crop the bounding box of all 21 landmarks plus a margin;
  3. mirror unless MediaPipe labels the hand "Left" (a consistency convention);
  4. plain (non-letterboxed) resize to 512x512; ImageNet normalisation.
Outputs are softmax probabilities warped into the canonical palm frame, so everything
downstream is independent of this model's peculiar crop.
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from numpy.typing import NDArray

from grahrekha_engine.palm.geometry import palm_length
from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.rectify import CANONICAL_SIZE, RectifiedPalm
from grahrekha_engine.palm.types import MIDDLE_MCP, WRIST, HandDetection

MODEL_ID = "plr-v0-fp16"
INPUT_SIZE = 512
LINE_CLASSES = ("heart", "head", "life")  # model output channels 1..3 (0 = background)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

Affine = NDArray[np.float64]  # 2x3


def _to3(a: Affine) -> NDArray[np.float64]:
    return np.vstack([a, [0.0, 0.0, 1.0]])


def compose(outer: Affine, inner: Affine) -> Affine:
    """outer ∘ inner as a 2x3 affine."""
    result: Affine = (_to3(outer) @ _to3(inner))[:2]
    return result


def model_crop_transform(detection: HandDetection, margin_ratio: float = 0.25) -> Affine:
    """2x3 affine mapping original pixels into the model's 512x512 input."""
    pts = detection.landmarks
    v = pts[MIDDLE_MCP] - pts[WRIST]
    z = complex(v[0], v[1])
    rot = -1j / (z / abs(z))  # unit complex rotating v onto "up" (0, -1) in image coords
    rotation = np.array([[rot.real, -rot.imag, 0.0], [rot.imag, rot.real, 0.0]])

    rotated = pts @ rotation[:, :2].T
    margin = margin_ratio * palm_length(pts)
    x0, y0 = rotated.min(axis=0) - margin
    x1, y1 = rotated.max(axis=0) + margin
    sx, sy = INPUT_SIZE / (x1 - x0), INPUT_SIZE / (y1 - y0)
    to_input = np.array([[sx, 0.0, -x0 * sx], [0.0, sy, -y0 * sy]])
    crop = compose(to_input, rotation)
    if detection.handedness != "left":
        flip = np.array([[-1.0, 0.0, float(INPUT_SIZE)], [0.0, 1.0, 0.0]])
        crop = compose(flip, crop)
    return crop


class PalmLineReaderV0:
    def __init__(self, weights: Path, margin_ratio: float = 0.25) -> None:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        self._session = ort.InferenceSession(
            str(weights), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self.margin_ratio = margin_ratio

    def _logits(self, crop: RGBImage) -> NDArray[np.float32]:
        x = (crop.astype(np.float32) / 255.0 - _MEAN) / _STD
        x = np.ascontiguousarray(x.transpose(2, 0, 1)[None])
        (logits,) = self._session.run(["logits"], {"input": x})
        result: NDArray[np.float32] = np.asarray(logits[0], dtype=np.float32)
        return result

    def predict(
        self, image: RGBImage, detection: HandDetection, rect: RectifiedPalm
    ) -> NDArray[np.float32]:
        """Per-class line probabilities (heart, head, life) in the canonical frame."""
        to_crop = model_crop_transform(detection, self.margin_ratio)
        size_in = (INPUT_SIZE, INPUT_SIZE)
        crop: RGBImage = cv2.warpAffine(image, to_crop, size_in, flags=cv2.INTER_LINEAR).astype(
            np.uint8
        )
        logits = self._logits(crop)
        exp = np.exp(logits - logits.max(axis=0, keepdims=True))
        probs = exp / exp.sum(axis=0, keepdims=True)

        from_crop: Affine = cv2.invertAffineTransform(to_crop).astype(np.float64)
        crop_to_canonical = compose(rect.forward, from_crop)
        size = (CANONICAL_SIZE, CANONICAL_SIZE)
        maps = [
            cv2.warpAffine(probs[i], crop_to_canonical, size, flags=cv2.INTER_LINEAR)
            for i in range(1, 1 + len(LINE_CLASSES))
        ]
        return np.clip(np.stack(maps), 0.0, 1.0).astype(np.float32)
