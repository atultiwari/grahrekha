"""Tolerance-based precision/recall for thin line structures.

Both prediction and ground truth are reduced to 1-px skeletons; a skeleton pixel counts
as matched if the other set has a pixel within `tolerance_px`. This is the standard way
to score thin curvilinear structures, where pixel-IoU punishes 1-2px offsets that are
irrelevant to reading the line.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.morphology import skeletonize


@dataclass(frozen=True)
class LineScores:
    precision: float
    recall: float

    @property
    def f1(self) -> float:
        total = self.precision + self.recall
        return 0.0 if total == 0 else 2 * self.precision * self.recall / total


def _near(mask: NDArray[np.bool_], tolerance_px: float) -> NDArray[np.bool_]:
    """Pixels within tolerance of any True pixel in mask."""
    if not mask.any():
        return np.zeros_like(mask)
    distance = cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 5)
    result: NDArray[np.bool_] = distance <= tolerance_px
    return result


def tolerant_scores(
    predicted: NDArray[np.bool_], truth: NDArray[np.bool_], tolerance_px: float
) -> LineScores:
    pred_skel = skeletonize(predicted)
    truth_skel = skeletonize(truth)
    if not pred_skel.any() and not truth_skel.any():
        return LineScores(1.0, 1.0)
    precision = float((pred_skel & _near(truth_skel, tolerance_px)).sum() / max(1, pred_skel.sum()))
    recall = float((truth_skel & _near(pred_skel, tolerance_px)).sum() / max(1, truth_skel.sum()))
    if not pred_skel.any():
        precision = 0.0
    return LineScores(precision, recall)
