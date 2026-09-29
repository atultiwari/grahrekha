"""Palm photo quality gate (docs/ARCHITECTURE.md §4.2).

Authoritative server-side check run before anything else. It returns every failing
reason with a specific code and user-facing advice. Thresholds are defaults to be
calibrated on the frozen evaluation splits (data/splits, docs/eval).
"""

from dataclasses import dataclass, field

import cv2
import numpy as np

from grahrekha_engine.palm.geometry import (
    finger_spread,
    finger_to_palm_ratio,
    is_palm_facing,
    palm_length,
)
from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.types import PALM_POLYGON, WRIST, HandDetection, Handedness

# Landmarks that must be inside the frame. Fingertips may be cropped; the palm may not.
REQUIRED_LANDMARKS = PALM_POLYGON
QUALITY_CROP_PALM_PX = 256  # palm length after normalising, so sharpness is scale-free
# MediaPipe's wrist point sits below the heel of the palm; it may fall just outside
# the frame while the whole palm is still visible (common framing, e.g. 11K Hands).
WRIST_TOLERANCE = 0.15  # fraction of palm length

ADVICE = {
    "NO_HAND": "We couldn't find a hand. Photograph one open palm, filling most of the frame.",
    "MULTIPLE_HANDS": "We found more than one hand. Photograph one palm at a time.",
    "BACK_OF_HAND": "This looks like the back of the hand. Turn your palm towards the camera.",
    "NOT_A_PALM": "This doesn't look like a hand. Photograph an open palm with fingers visible.",
    "HAND_TOO_SMALL": "The hand is too far away. Move closer so the palm fills the frame.",
    "CROPPED": "Part of the palm is outside the photo. Include the whole palm and wrist.",
    "FINGERS_CLOSED": "Spread your fingers slightly so the lines at their base are visible.",
    "BLURRY": "The photo is blurry. Hold still, tap to focus on the palm, and retake.",
    "TOO_DARK": "The photo is too dark. Use even light, such as near a window.",
    "OVEREXPOSED": "The photo is too bright. Avoid direct flash or harsh light on the palm.",
    "HANDEDNESS_UNCERTAIN": "Please confirm which hand this is.",
}


@dataclass(frozen=True)
class GateConfig:
    # Palm length / shorter image side. Real palms: p5 = 0.34. Below 0.25 the creases are
    # too small to read, and incidental hands in unrelated photos are excluded.
    min_palm_length_ratio: float = 0.25
    # Conservative: real palms min 0.63; catches the clearest foot soles without
    # rejecting palms. A learned hand/foot classifier is future work (docs/eval).
    min_finger_to_palm_ratio: float = 0.60
    # Index-pinky tip distance / knuckle width. Real palms: p5 = 0.96, min = 0.85;
    # fingers merely touching still leave the palm readable, so reject only below 0.75.
    min_finger_spread: float = 0.75
    # Laplacian variance inside the 256px-normalised palm crop. Calibrated on
    # positives_v1: real palms p2 = 7.49; the same palms blurred by 1.5% of palm length
    # (creases erased) p98 = 2.14. 4.0 sits in the gap (docs/eval/gate-calibration.md).
    min_sharpness: float = 4.0
    min_brightness: float = 40.0
    max_brightness: float = 235.0


@dataclass(frozen=True)
class GateIssue:
    code: str
    message: str


def _issue(code: str) -> GateIssue:
    return GateIssue(code, ADVICE[code])


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: list[GateIssue]
    warnings: list[GateIssue] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    detection: HandDetection | None = None


def _palm_crop(image: RGBImage, det: HandDetection) -> tuple[np.ndarray, np.ndarray]:
    """Grayscale palm crop scaled so palm length is QUALITY_CROP_PALM_PX, plus its mask."""
    polygon = det.landmarks[list(PALM_POLYGON)]
    scale = QUALITY_CROP_PALM_PX / max(palm_length(det.landmarks), 1.0)
    h, w = image.shape[:2]
    x0, y0 = np.floor(polygon.min(axis=0)).clip(0, [w - 1, h - 1]).astype(int)
    x1, y1 = np.ceil(polygon.max(axis=0)).clip(1, [w, h]).astype(int)
    crop = cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY)
    size = (max(1, round((x1 - x0) * scale)), max(1, round((y1 - y0) * scale)))
    crop = cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
    mask = np.zeros(crop.shape, np.uint8)
    local = ((polygon - [x0, y0]) * scale).round().astype(np.int32)
    cv2.fillPoly(mask, [local], 255)
    return crop, mask > 0


def _image_quality(image: RGBImage, det: HandDetection) -> dict[str, float]:
    crop, mask = _palm_crop(image, det)
    if mask.sum() < 16:
        return {"sharpness": 0.0, "brightness": 0.0}
    laplacian = cv2.Laplacian(crop, cv2.CV_64F)
    return {
        "sharpness": float(laplacian[mask].var()),
        "brightness": float(crop[mask].mean()),
    }


def evaluate_gate(
    image: RGBImage,
    detections: list[HandDetection],
    declared_hand: Handedness | None = None,
    config: GateConfig | None = None,
) -> GateResult:
    cfg = config or GateConfig()
    if not detections:
        return GateResult(False, [_issue("NO_HAND")])

    det = max(detections, key=lambda d: d.handedness_score)
    h, w = image.shape[:2]
    pts = det.landmarks
    margin = np.zeros(len(REQUIRED_LANDMARKS))
    margin[REQUIRED_LANDMARKS.index(WRIST)] = WRIST_TOLERANCE * palm_length(pts)
    required = pts[list(REQUIRED_LANDMARKS)]
    inside = (
        (required[:, 0] >= -margin)
        & (required[:, 0] <= w + margin)
        & (required[:, 1] >= -margin)
        & (required[:, 1] <= h + margin)
    )

    metrics = {
        "palm_length_ratio": palm_length(pts) / min(h, w),
        "finger_spread": finger_spread(pts),
        "finger_to_palm_ratio": finger_to_palm_ratio(pts),
        "handedness_score": det.handedness_score,
    }
    reasons: list[GateIssue] = []
    if len(detections) > 1:
        reasons.append(_issue("MULTIPLE_HANDS"))
    if metrics["finger_to_palm_ratio"] < cfg.min_finger_to_palm_ratio:
        reasons.append(_issue("NOT_A_PALM"))
    if not is_palm_facing(det):
        reasons.append(_issue("BACK_OF_HAND"))
    if not inside.all():
        reasons.append(_issue("CROPPED"))
    if metrics["palm_length_ratio"] < cfg.min_palm_length_ratio:
        reasons.append(_issue("HAND_TOO_SMALL"))
    if metrics["finger_spread"] < cfg.min_finger_spread:
        reasons.append(_issue("FINGERS_CLOSED"))

    if inside.all():
        metrics |= _image_quality(image, det)
        if metrics["sharpness"] < cfg.min_sharpness:
            reasons.append(_issue("BLURRY"))
        if metrics["brightness"] < cfg.min_brightness:
            reasons.append(_issue("TOO_DARK"))
        elif metrics["brightness"] > cfg.max_brightness:
            reasons.append(_issue("OVEREXPOSED"))

    warnings = []
    if declared_hand is not None and declared_hand != det.handedness:
        # MediaPipe's left/right label is wrong on ~20% of phone photos (calibration),
        # so a disagreement is surfaced for confirmation rather than rejected.
        warnings.append(_issue("HANDEDNESS_UNCERTAIN"))

    return GateResult(not reasons, reasons, warnings, metrics, det)
