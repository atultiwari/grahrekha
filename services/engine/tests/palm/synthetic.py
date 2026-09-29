"""Synthetic hand landmarks for tests (MediaPipe 21-point topology, pixel coords).

RIGHT_PALM is an idealised right hand, palm facing the camera, fingers up and spread,
in a 1000x1000 image. Mirroring x gives a left palm (or a right hand's back).
"""

import numpy as np

from grahrekha_engine.palm.types import HandDetection, Handedness

_WRIST = (500, 900)
_THUMB = [(600, 830), (680, 750), (740, 680), (790, 620)]
# (MCP, PIP, DIP, TIP) for index, middle, ring, pinky; thumb on the image right.
_FINGERS = [
    [(620, 550), (650, 420), (675, 310), (700, 200)],
    [(520, 520), (525, 380), (528, 260), (530, 150)],
    [(430, 540), (415, 410), (405, 290), (400, 180)],
    [(350, 580), (320, 480), (300, 390), (280, 300)],
]


def right_palm_points(scale: float = 1.0, offset: tuple[float, float] = (0, 0)) -> np.ndarray:
    pts = [_WRIST, *_THUMB, *[p for finger in _FINGERS for p in finger]]
    arr = np.array(pts, dtype=float)
    centre = np.array([500.0, 500.0])
    result: np.ndarray = (arr - centre) * scale + centre + np.array(offset)
    return result


def mirror_x(points: np.ndarray, width: float = 1000) -> np.ndarray:
    out = points.copy()
    out[:, 0] = width - out[:, 0]
    return out


def rotate(
    points: np.ndarray, degrees: float, centre: tuple[float, float] = (500, 500)
) -> np.ndarray:
    t = np.radians(degrees)
    r = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    c = np.array(centre)
    result: np.ndarray = (points - c) @ r.T + c
    return result


def detection(points: np.ndarray, hand: Handedness = "right", score: float = 0.95) -> HandDetection:
    return HandDetection(landmarks=points, handedness=hand, handedness_score=score)
