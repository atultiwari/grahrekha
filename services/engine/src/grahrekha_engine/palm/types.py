"""Core palm data types. Landmarks follow MediaPipe's 21-point hand topology."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

Handedness = Literal["left", "right"]
Points = NDArray[np.float64]  # shape (21, 2), image pixel coordinates (x right, y down)

WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_TIP = 5, 8
MIDDLE_MCP, MIDDLE_TIP = 9, 12
RING_MCP, RING_TIP = 13, 16
PINKY_MCP, PINKY_TIP = 17, 20
PALM_POLYGON = (WRIST, THUMB_CMC, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)


@dataclass(frozen=True)
class HandDetection:
    landmarks: Points
    handedness: Handedness  # MediaPipe's label; unreliable on some phone photos
    handedness_score: float
