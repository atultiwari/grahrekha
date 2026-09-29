"""Warp a palm into the canonical palm frame (docs/ARCHITECTURE.md §4.3).

Every measurement is made in this frame so features are comparable across photos,
phones and distances. The frame uses the LEFT-palm layout (palm facing the viewer,
thumb on the left); right palms are mirrored into it.

Transform: least-squares affine fit of six palm landmarks to a template. Affine rather
than a full homography: the palm is not planar and landmark noise makes 8-DOF fits
unstable, while an affine (which can include the mirror) captures rotation, scale,
shear and translation robustly.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.types import (
    INDEX_MCP,
    MIDDLE_MCP,
    PINKY_MCP,
    RING_MCP,
    THUMB_CMC,
    WRIST,
    HandDetection,
    Points,
)

CANONICAL_SIZE = 1024
TEMPLATE_INDICES = (WRIST, THUMB_CMC, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)

# Mean shape of 139 real palms that passed the gate (positives_v1), mirrored to the
# left-palm layout and normalised so wrist -> middle-MCP = (0, -1). Per-landmark SD
# was 0.02-0.03 palm lengths, so this is a tight, data-derived template.
_TEMPLATE_UNIT = np.array(
    [
        (0.000, 0.000),  # wrist
        (-0.341, -0.213),  # thumb CMC
        (-0.225, -0.990),  # index MCP
        (0.000, -1.000),  # middle MCP
        (0.197, -0.924),  # ring MCP
        (0.383, -0.784),  # pinky MCP
    ]
)
# Placement in the canvas: 560 px per palm length leaves room for the finger bases
# above (mounts, heart line) and the wrist creases below.
PALM_UNIT_PX = 560.0  # canonical pixels per palm length (the unit for all features)
_PALM_PX = PALM_UNIT_PX
_WRIST_AT = np.array([500.0, 880.0])


def template_points() -> NDArray[np.float64]:
    """Canonical-frame pixel positions of TEMPLATE_INDICES."""
    result: NDArray[np.float64] = _TEMPLATE_UNIT * _PALM_PX + _WRIST_AT
    return result


def _fit_affine(src: Points, dst: Points) -> NDArray[np.float64]:
    """Least-squares 2x3 affine mapping src -> dst (deterministic, no RANSAC)."""
    design = np.hstack([src, np.ones((len(src), 1))])
    solution, *_ = np.linalg.lstsq(design, dst, rcond=None)
    affine: NDArray[np.float64] = solution.T
    return affine


def _apply(affine: NDArray[np.float64], points: Points) -> Points:
    result: Points = points @ affine[:, :2].T + affine[:, 2]
    return result


@dataclass(frozen=True)
class RectifiedPalm:
    image: RGBImage  # CANONICAL_SIZE x CANONICAL_SIZE
    forward: NDArray[np.float64]  # 2x3: original pixels -> canonical pixels
    inverse: NDArray[np.float64]  # 2x3: canonical pixels -> original pixels
    mirrored: bool  # True when a right palm was mirrored into the left-palm frame
    fit_rms_px: float  # template fit residual (canonical px); large = unusual pose

    def to_canonical(self, points: Points) -> Points:
        return _apply(self.forward, np.asarray(points, dtype=np.float64))

    def to_original(self, points: Points) -> Points:
        return _apply(self.inverse, np.asarray(points, dtype=np.float64))


def rectify(image: RGBImage, detection: HandDetection) -> RectifiedPalm:
    src = detection.landmarks[list(TEMPLATE_INDICES)]
    dst = template_points()
    forward = _fit_affine(src, dst)
    inverse = cv2.invertAffineTransform(forward).astype(np.float64)
    residual = _apply(forward, src) - dst
    warped: RGBImage = cv2.warpAffine(
        image,
        forward,
        (CANONICAL_SIZE, CANONICAL_SIZE),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    ).astype(np.uint8)
    return RectifiedPalm(
        image=warped,
        forward=forward,
        inverse=inverse,
        mirrored=bool(np.linalg.det(forward[:, :2]) < 0),
        fit_rms_px=float(np.sqrt((residual**2).sum(axis=1).mean())),
    )
