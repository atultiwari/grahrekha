"""MediaPipe Hand Landmarker wrapper (CPU, IMAGE mode)."""

from pathlib import Path
from typing import cast

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.types import HandDetection, Handedness


class HandLandmarkDetector:
    """Detects up to two hands so the gate can reject multi-hand photos.

    Note: mediapipe is pinned to 0.10.x; 1.0.1's macOS build aborts on a Metal
    service check even with the CPU delegate.
    """

    def __init__(self, model_path: Path, min_detection_confidence: float = 0.3) -> None:
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=str(model_path), delegate=BaseOptions.Delegate.CPU
            ),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=min_detection_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def detect(self, image: RGBImage) -> list[HandDetection]:
        h, w = image.shape[:2]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image))
        result = self._landmarker.detect(mp_image)
        detections = []
        for landmarks, handedness in zip(result.hand_landmarks, result.handedness, strict=True):
            points = np.array([[p.x * w, p.y * h] for p in landmarks], dtype=np.float64)
            top = handedness[0]
            detections.append(
                HandDetection(
                    landmarks=points,
                    handedness=cast(Handedness, top.category_name.lower()),
                    handedness_score=float(top.score),
                )
            )
        return detections

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> "HandLandmarkDetector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
