"""Per-line training labels from class-agnostic human masks (Phase 2, docs/eval/lines-v0.md).

PLSU masks trace palm lines completely but do not say which line is which. v0 predicts
line identity but truncates lines. Combining them:
  1. skeletonise the human mask and split it into branches at junctions;
  2. give each branch the line class v0 supports along it (even partial support labels
     the WHOLE branch, which fixes v0's truncation);
  3. an unsupported, near-vertical branch in the centre of the palm is the fate line;
  4. anything else is IGNORE (not background), so the model is never taught to
     suppress a real crease it cannot name.
All coordinates are in the canonical palm frame (1024 px, 560 px per palm length).
"""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy import ndimage
from skimage.morphology import skeletonize

BACKGROUND, HEART, HEAD, LIFE, FATE = 0, 1, 2, 3, 4
IGNORE = 255
CLASS_NAMES = {HEART: "heart", HEAD: "head", LIFE: "life", FATE: "fate"}

Branch = NDArray[np.intp]  # (N, 2) pixel coordinates as (y, x)


@dataclass(frozen=True)
class LabelConfig:
    palm_px: float = 560.0  # canonical pixels per palm length
    min_branch_px: int = 8
    probe_radius_px: int = 6  # v0 lines may sit a few px off the hand-drawn line
    min_support: float = 0.15  # share of a branch that v0 must mark as a line class
    fate_max_tilt_deg: float = 30.0
    fate_min_length: float = 0.2  # palm lengths
    fate_x_range: tuple[float, float] = (400.0, 640.0)
    fate_min_centroid_y: float = 450.0
    max_label_distance_px: float = 12.0


def split_branches(mask: NDArray[np.bool_], cfg: LabelConfig | None = None) -> list[Branch]:
    """Skeleton branches of a line mask, cut at junctions where lines meet or cross."""
    config = cfg or LabelConfig()
    skeleton = skeletonize(mask)
    neighbours = cv2.filter2D(skeleton.astype(np.uint8), -1, np.ones((3, 3), np.float32)) - skeleton
    junctions = skeleton & (neighbours >= 3)
    cut = skeleton & ~cv2.dilate(junctions.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    count, labels = cv2.connectedComponents(cut.astype(np.uint8), connectivity=8)
    branches = [np.argwhere(labels == i) for i in range(1, count)]
    return [b for b in branches if len(b) >= config.min_branch_px]


def _is_fate_like(branch: Branch, cfg: LabelConfig) -> bool:
    ys, xs = branch[:, 0].astype(float), branch[:, 1].astype(float)
    centred = np.stack([xs - xs.mean(), ys - ys.mean()])
    _, vectors = np.linalg.eigh(centred @ centred.T)
    direction = vectors[:, -1]  # principal axis (x, y)
    tilt = float(np.degrees(np.arccos(min(1.0, abs(float(direction[1]))))))
    extent = float(np.ptp(centred.T @ direction))
    return bool(
        tilt <= cfg.fate_max_tilt_deg
        and extent >= cfg.fate_min_length * cfg.palm_px
        and cfg.fate_x_range[0] <= xs.mean() <= cfg.fate_x_range[1]
        and ys.mean() >= cfg.fate_min_centroid_y
    )


def assign_branch_classes(
    branches: list[Branch], probs: NDArray[np.float32], cfg: LabelConfig | None = None
) -> list[int]:
    """Line class per branch from v0 probabilities (heart, head, life) plus anatomy."""
    config = cfg or LabelConfig()
    kernel = np.ones((2 * config.probe_radius_px + 1,) * 2, np.uint8)
    near = np.stack([cv2.dilate(p, kernel) >= 0.5 for p in probs])  # (3, H, W)
    classes = []
    for branch in branches:
        support = near[:, branch[:, 0], branch[:, 1]].mean(axis=1)
        best = int(np.argmax(support))
        if support[best] >= config.min_support:
            classes.append((HEART, HEAD, LIFE)[best])
        elif _is_fate_like(branch, config):
            classes.append(FATE)
        else:
            classes.append(IGNORE)
    return classes


def build_label_map(
    mask: NDArray[np.bool_],
    branches: list[Branch],
    classes: list[int],
    cfg: LabelConfig | None = None,
) -> NDArray[np.uint8]:
    """Label every mask pixel with the class of its nearest skeleton branch."""
    config = cfg or LabelConfig()
    branch_ids = np.zeros(mask.shape, np.int32)
    for index, branch in enumerate(branches, start=1):
        branch_ids[branch[:, 0], branch[:, 1]] = index
    labels = np.zeros(mask.shape, np.uint8)
    if not branches:
        labels[mask] = IGNORE
        return labels
    distance, (iy, ix) = ndimage.distance_transform_edt(branch_ids == 0, return_indices=True)
    lookup = np.array([IGNORE, *classes], np.uint8)
    nearest = lookup[branch_ids[iy, ix]]
    labels[mask] = np.where(distance[mask] <= config.max_label_distance_px, nearest[mask], IGNORE)
    return labels
