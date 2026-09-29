"""Per-line labels from Roboflow Universe COCO exports (manifest D24).

Unlike PLSU (labels.py), line identity here is human-annotated, so these labels do not
inherit v0's mistakes. Annotators draw lines as polygons of varying width; labels are
redrawn at a standard width so they match PLSU strokes.
"""

import hashlib
import re

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.morphology import skeletonize

from grahrekha_ml.labels import FATE, HEAD, HEART, IGNORE, LIFE

_OURS = {"heart": HEART, "head": HEAD, "life": LIFE, "fate": FATE}
# Real palm creases outside our four classes: ignored in the loss, not background.
_MINOR = {"marriage", "solar", "sun", "mercury", "mars", "health", "girdle", "family", "property"}
# Paint order: later classes win where polygons overlap.
_PRIORITY = (IGNORE, FATE, LIFE, HEAD, HEART)
HOLDOUT_SHARE = 0.2


def class_for(name: str) -> int | None:
    """Our class id for a Roboflow category name, IGNORE for minor lines, None for junk."""
    words = re.split(r"[^a-z]+", name.lower())
    for word in words:
        if word in _OURS:
            return _OURS[word]
    return IGNORE if any(word in _MINOR for word in words) else None


def rasterize(
    annotations: list[tuple[int, list[list[float]]]], shape: tuple[int, int]
) -> NDArray[np.uint8]:
    """Fill COCO polygons ([x0, y0, x1, y1, ...]) into a label map with class priority."""
    label = np.zeros(shape, np.uint8)
    for cls in _PRIORITY:
        for ann_cls, polygons in annotations:
            if ann_cls != cls:
                continue
            for flat in polygons:
                if len(flat) >= 6:
                    points = np.asarray(flat, np.float64).reshape(-1, 2).round().astype(np.int32)
                    cv2.fillPoly(label, [points], int(cls))
    return label


_NEIGHBOURS = np.ones((3, 3), np.float32)


def _endpoints(skeleton: NDArray[np.bool_]) -> NDArray[np.bool_]:
    count = cv2.filter2D(skeleton.astype(np.uint8), -1, _NEIGHBOURS, borderType=cv2.BORDER_CONSTANT)
    result: NDArray[np.bool_] = skeleton & (count == 2)  # itself + exactly one neighbour
    return result


def prune_spurs(skeleton: NDArray[np.bool_], length: int) -> NDArray[np.bool_]:
    """Remove side branches shorter than `length` px, then regrow the main line's tips.

    Classic pruning: strip endpoints `length` times (spurs vanish, lines shorten), then
    grow back along the original skeleton from the surviving endpoints only, so spurs
    attached mid-line are not restored.
    """
    pruned = skeleton.copy()
    for _ in range(length):
        pruned = pruned & ~_endpoints(pruned)
    grow = _endpoints(pruned)
    kernel = np.ones((3, 3), np.uint8)
    for _ in range(length):
        grow = (cv2.dilate(grow.astype(np.uint8), kernel) > 0) & skeleton & ~pruned
        pruned = pruned | grow
    return pruned


def normalise_width(label: NDArray[np.uint8], width: int) -> NDArray[np.uint8]:
    """Redraw each line class as its pruned skeleton dilated to `width` px.

    Annotators draw lines as polygons with jagged outlines; their raw skeletons grow short
    spurs. IGNORE regions are kept as they are.
    """
    out = np.where(label == IGNORE, IGNORE, 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (width, width))
    for cls in _PRIORITY[1:]:
        mask = label == cls
        if mask.any():
            skeleton = prune_spurs(skeletonize(mask), length=2 * width)
            thin = cv2.dilate(skeleton.astype(np.uint8), kernel) > 0
            out[thin] = cls
    return out


def dhash(image: NDArray[np.uint8], size: int = 8) -> int:
    """Difference hash: robust to brightness changes, sensitive to content."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    small = cv2.resize(gray, (size + 1, size), interpolation=cv2.INTER_AREA).astype(np.int16)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def is_holdout(name: str) -> bool:
    """Deterministic ~20% hold-out by file name (independent of processing order)."""
    digest = hashlib.sha256(name.encode()).digest()
    return digest[0] < 256 * HOLDOUT_SHARE
