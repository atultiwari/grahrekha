"""Measured palm features in the canonical frame (docs/ARCHITECTURE.md §4.5).

Deliberately limited to what the v0 pipeline measures reliably. Forks, islands, chains
and the single transverse crease are NOT reported yet rather than guessed.
"""

from typing import Literal

import numpy as np

from grahrekha_engine.contracts.palm import (
    HandGeometryV1,
    LineFeaturesV1,
    LineName,
    Zone,
)
from grahrekha_engine.palm.geometry import finger_to_palm_ratio, palm_length, palm_width
from grahrekha_engine.palm.rectify import PALM_UNIT_PX, template_points
from grahrekha_engine.palm.segment.postprocess import LineTrace
from grahrekha_engine.palm.types import (
    INDEX_MCP,
    INDEX_TIP,
    RING_MCP,
    RING_TIP,
    THUMB_CMC,
    THUMB_TIP,
    Points,
)

# Zone boundaries (canonical px), anchored to template knuckles:
# index MCP x=374, middle 500, ring 610, pinky 714; wrist y=880; thumb CMC (309, 761).
# The gap between index and middle fingers is its own zone (Cheiro's heart line
# "rising from between the first and second fingers"), defined anatomically as the gap
# centre (437) +/- a quarter of the knuckle spacing (126 / 4). Human-drawn heart lines
# end there in 61% of palms (PLSU; docs/eval/lines-v1.md).
_INDEX_MIDDLE_GAP = (405.5, 468.5)
_FINGER_BANDS = (
    (_INDEX_MIDDLE_GAP[0], "under_index"),
    (_INDEX_MIDDLE_GAP[1], "between_index_middle"),
    (555, "under_middle"),
    (662, "under_ring"),
    (740, "under_pinky"),
)
_PERCUSSION_X = 740
_UPPER_BAND_Y = 560
_WRIST_Y = 800
_THUMB_EDGE_X, _THUMB_EDGE_Y = 385, (380, 620)
_LOWER_Y = 620
_THENAR_X, _HYPOTHENAR_X = 430, 600
_THUMB_CMC_X = float(template_points()[1, 0])

# Population-relative splits at the medians of 139 real palms (positives_v1); these are
# NOT Benham's or Cheiro's physical definitions. Each has a middle band of +/- the 75th
# percentile of within-hand measurement noise (retest_v1), so noise cannot flip a hand
# between the outer classes.
PALM_RATIO_MEDIAN, PALM_RATIO_NOISE = 1.571, 0.068  # palm length / knuckle width
FINGER_RATIO_MEDIAN, FINGER_RATIO_NOISE = 0.843, 0.054  # finger length / palm length
DIGIT_RATIO_NOISE = 0.043  # 2D:4D within-hand SD (p75)
ZONE_NOISE_PALM = 0.05  # endpoint jitter (palm lengths) used to judge zone certainty


def zone_of(point: np.ndarray) -> Zone:
    x, y = float(point[0]), float(point[1])
    if y > _WRIST_Y:
        return "wrist"
    if x > _PERCUSSION_X:
        return "percussion"
    if x < _THUMB_EDGE_X and _THUMB_EDGE_Y[0] <= y < _THUMB_EDGE_Y[1]:
        return "thumb_index_edge"
    if y < _UPPER_BAND_Y:
        for bound, name in _FINGER_BANDS:
            if x < bound:
                return name  # type: ignore[return-value]
        return "under_pinky"
    if y >= _LOWER_Y and x < _THENAR_X:
        return "thenar"
    if y >= _LOWER_Y and x > _HYPOTHENAR_X:
        return "hypothenar"
    return "palm_centre"


def _oriented(name: LineName, points: np.ndarray) -> np.ndarray:
    """Order points by palmistry convention for each line."""
    first, last = points[0], points[-1]
    reverse = {
        "heart": first[0] < last[0],  # starts at the percussion (larger x)
        "head": first[0] > last[0],  # starts at the thumb side (smaller x)
        "life": first[1] > last[1],  # starts at the top, runs down to the wrist
        "fate": first[1] < last[1],  # starts at the wrist, runs up
    }[name]
    return points[::-1] if reverse else points


def line_features(
    name: LineName, trace: LineTrace | None, source: Literal["model", "classical"] = "model"
) -> LineFeaturesV1:
    if trace is None or not trace.segments:
        return LineFeaturesV1(name=name, present=False)
    points = _oriented(name, np.concatenate(trace.segments))
    start, end = points[0], points[-1]
    chord = end - start
    chord_len = float(np.linalg.norm(chord))
    if chord_len > 0:
        normal = np.array([-chord[1], chord[0]]) / chord_len
        curvature = float(np.abs((points - start) @ normal).max() / chord_len)
    else:
        curvature = 0.0
    sweep = float((points[:, 0].max() - _THUMB_CMC_X) / PALM_UNIT_PX) if name == "life" else None
    return LineFeaturesV1(
        name=name,
        present=True,
        source=source,
        confidence=round(trace.confidence, 3),
        length=round(trace.length_px / PALM_UNIT_PX, 3),
        start_zone=zone_of(start),
        end_zone=zone_of(end),
        start_zone_certain=zone_is_certain(start),
        end_zone_certain=zone_is_certain(end),
        curvature=round(curvature, 3),
        slope_deg=round(float(np.degrees(np.arctan2(-chord[1], chord[0]))), 1),
        breaks=len(trace.gaps_px),
        gaps=[round(g / PALM_UNIT_PX, 3) for g in trace.gaps_px],
        sweep=None if sweep is None else round(sweep, 3),
    )


PalmShape = Literal["square", "medium", "long"]
FingerLength = Literal["short", "medium", "long"]
Element = Literal["earth", "air", "fire", "water", "mixed"]
IndexRing = Literal["index_longer", "ring_longer", "equal"]


def classify_palm_shape(ratio: float) -> PalmShape:
    if ratio <= PALM_RATIO_MEDIAN - PALM_RATIO_NOISE:
        return "square"
    if ratio >= PALM_RATIO_MEDIAN + PALM_RATIO_NOISE:
        return "long"
    return "medium"


def classify_finger_length(ratio: float) -> FingerLength:
    if ratio <= FINGER_RATIO_MEDIAN - FINGER_RATIO_NOISE:
        return "short"
    if ratio >= FINGER_RATIO_MEDIAN + FINGER_RATIO_NOISE:
        return "long"
    return "medium"


def compare_index_ring(ratio: float) -> IndexRing:
    if ratio >= 1 + DIGIT_RATIO_NOISE:
        return "index_longer"
    if ratio <= 1 - DIGIT_RATIO_NOISE:
        return "ring_longer"
    return "equal"


def element_of(palm_shape: PalmShape, finger_length: FingerLength) -> Element:
    """Four-element hand types (Cheiro and later Western palmists); "mixed" otherwise."""
    if palm_shape == "medium" or finger_length == "medium":
        return "mixed"
    if palm_shape == "square":
        return "earth" if finger_length == "short" else "air"
    return "fire" if finger_length == "short" else "water"


def zone_is_certain(point: np.ndarray, noise_palm: float = ZONE_NOISE_PALM) -> bool:
    """True when nudging the point by measurement noise cannot change its zone."""
    zone = zone_of(point)
    radius = noise_palm * PALM_UNIT_PX
    for angle in np.linspace(0, 2 * np.pi, 16, endpoint=False):
        probe = point + radius * np.array([np.cos(angle), np.sin(angle)])
        if zone_of(probe) != zone:
            return False
    return True


def _chain_length(points: Points, first: int, last: int) -> float:
    return float(sum(np.linalg.norm(points[i + 1] - points[i]) for i in range(first, last)))


def _angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    cos = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def hand_geometry(landmarks: Points) -> HandGeometryV1:
    """Measured on ORIGINAL landmarks: the canonical warp normalises shape by design."""
    lw = palm_length(landmarks) / palm_width(landmarks)
    fp = finger_to_palm_ratio(landmarks)
    palm_shape = classify_palm_shape(lw)
    finger_length = classify_finger_length(fp)
    d2d4 = _chain_length(landmarks, INDEX_MCP, INDEX_TIP) / _chain_length(
        landmarks, RING_MCP, RING_TIP
    )
    thumb = landmarks[THUMB_TIP] - landmarks[THUMB_CMC]
    index = landmarks[INDEX_TIP] - landmarks[INDEX_MCP]
    return HandGeometryV1(
        palm_length_width_ratio=round(lw, 3),
        finger_to_palm_ratio=round(fp, 3),
        palm_shape=palm_shape,
        finger_length=finger_length,
        element=element_of(palm_shape, finger_length),
        digit_ratio_2d4d=round(d2d4, 3),
        index_vs_ring=compare_index_ring(d2d4),
        thumb_opening_deg=round(_angle_deg(thumb, index), 1),
    )


# Head and life lines "joined at the start" (a classic palmistry distinction): their
# starting points lie within this distance (palm lengths).
HEAD_LIFE_JOIN_MAX = 0.08


def head_life_joined(head: LineTrace | None, life: LineTrace | None) -> bool | None:
    """None when either line is absent (unknown, not False)."""
    if head is None or life is None or not head.segments or not life.segments:
        return None
    head_start = _oriented("head", np.concatenate(head.segments))[0]
    life_start = _oriented("life", np.concatenate(life.segments))[0]
    return bool(np.linalg.norm(head_start - life_start) / PALM_UNIT_PX < HEAD_LIFE_JOIN_MAX)
