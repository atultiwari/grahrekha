"""Rotation- and scale-invariant hand geometry used by the quality gate and features."""

from itertools import pairwise

import numpy as np

from grahrekha_engine.palm.types import (
    INDEX_MCP,
    INDEX_TIP,
    MIDDLE_MCP,
    PINKY_MCP,
    PINKY_TIP,
    WRIST,
    HandDetection,
    Points,
)


def chirality(points: Points) -> float:
    """Signed area of the cross product (wrist→index MCP) x (wrist→pinky MCP), image coords.

    Negative for a right palm (or a left hand's back) facing the camera; the sign is
    invariant to rotation and scale and flips under mirroring.
    """
    a = points[INDEX_MCP] - points[WRIST]
    b = points[PINKY_MCP] - points[WRIST]
    return float(a[0] * b[1] - a[1] * b[0])


def is_palm_facing(detection: HandDetection) -> bool:
    """Palm (not back of hand) faces the camera.

    Calibrated on 11K Hands (palmar/dorsal ground truth) and smartphone photos: the
    combination (MediaPipe handedness == right) == (chirality < 0) separated palm from
    back on every detected image, even when MediaPipe's left/right label itself was
    wrong (see docs/eval). Neither signal alone is sufficient.
    """
    return (detection.handedness == "right") == (chirality(detection.landmarks) < 0)


def palm_length(points: Points) -> float:
    """Wrist to middle-finger MCP: the scale unit for all palm measurements."""
    return float(np.linalg.norm(points[MIDDLE_MCP] - points[WRIST]))


def palm_width(points: Points) -> float:
    return float(np.linalg.norm(points[INDEX_MCP] - points[PINKY_MCP]))


def finger_spread(points: Points) -> float:
    """Distance between index and pinky tips relative to knuckle width (~1 when closed)."""
    width = palm_width(points)
    if width == 0:
        return 0.0
    return float(np.linalg.norm(points[INDEX_TIP] - points[PINKY_TIP]) / width)


FINGER_CHAINS = ((5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16))  # index, middle, ring


def finger_to_palm_ratio(points: Points) -> float:
    """Mean index/middle/ring finger length (along joints) relative to palm length.

    Real palms: min 0.63, median 0.85 (positives_v1). Low values mean the "fingers" are
    implausibly short, e.g. MediaPipe fitting a hand skeleton onto a foot sole.
    """
    length = palm_length(points)
    if length == 0:
        return 0.0
    fingers = [
        sum(float(np.linalg.norm(points[b] - points[a])) for a, b in pairwise(chain))
        for chain in FINGER_CHAINS
    ]
    return float(np.mean(fingers)) / length
