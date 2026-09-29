"""Losses for thin, connected structures (palm lines).

- Cross-entropy with ignore_index: pixels we could not name are neither line nor
  background (see labels.py).
- Soft Dice per line class: counters the extreme background/line imbalance.
- Soft clDice (Shit et al., CVPR 2021, "clDice - a Novel Topology-Preserving Loss
  Function for Tubular Structure Segmentation"): compares soft skeletons, so a gap in a
  predicted line costs much more than a slightly thinner line. Targets v0's truncation.
"""

import torch
import torch.nn.functional as F
from torch import Tensor, nn

IGNORE_INDEX = 255
LINE_CLASSES = (1, 2, 3, 4)  # heart, head, life, fate


def _erode(x: Tensor) -> Tensor:
    return -F.max_pool2d(-x, kernel_size=3, stride=1, padding=1)


def _dilate(x: Tensor) -> Tensor:
    return F.max_pool2d(x, kernel_size=3, stride=1, padding=1)


def soft_skeleton(x: Tensor, iterations: int = 10) -> Tensor:
    """Differentiable morphological skeleton of a soft mask (N, C, H, W) in [0, 1]."""
    opened = _dilate(_erode(x))
    skeleton = F.relu(x - opened)
    for _ in range(iterations):
        x = _erode(x)
        opened = _dilate(_erode(x))
        delta = F.relu(x - opened)
        skeleton = skeleton + F.relu(delta - skeleton * delta)
    return skeleton


def soft_dice(pred: Tensor, target: Tensor, eps: float = 1.0) -> Tensor:
    intersection = (pred * target).sum()
    return (2 * intersection + eps) / (pred.sum() + target.sum() + eps)


def soft_cldice(pred: Tensor, target: Tensor, iterations: int = 10, eps: float = 1.0) -> Tensor:
    pred_skel = soft_skeleton(pred, iterations)
    target_skel = soft_skeleton(target, iterations)
    topology_precision = ((pred_skel * target).sum() + eps) / (pred_skel.sum() + eps)
    topology_sensitivity = ((target_skel * pred).sum() + eps) / (target_skel.sum() + eps)
    return (
        2 * topology_precision * topology_sensitivity / (topology_precision + topology_sensitivity)
    )


class LineLoss(nn.Module):
    def __init__(
        self,
        dice_weight: float = 1.0,
        cldice_weight: float = 0.5,
        class_weights: tuple[float, ...] = (0.2, 1.0, 1.0, 1.0, 1.5),
    ) -> None:
        super().__init__()
        self.dice_weight = dice_weight
        self.cldice_weight = cldice_weight
        self.register_buffer("class_weights", torch.tensor(class_weights))

    def forward(self, logits: Tensor, target: Tensor) -> Tensor:
        ce = F.cross_entropy(
            logits, target, weight=self.get_buffer("class_weights"), ignore_index=IGNORE_INDEX
        )
        probs = logits.softmax(dim=1)
        valid = (target != IGNORE_INDEX).unsqueeze(1).float()
        dice_terms, cldice_terms = [], []
        for cls in LINE_CLASSES:
            pred = probs[:, cls : cls + 1] * valid
            truth = (target == cls).unsqueeze(1).float()
            if truth.sum() == 0 and pred.sum() < 1:
                continue  # class absent in this batch and correctly not predicted
            dice_terms.append(1 - soft_dice(pred, truth))
            cldice_terms.append(1 - soft_cldice(pred, truth))
        if not dice_terms:
            return ce
        dice = torch.stack(dice_terms).mean()
        cldice = torch.stack(cldice_terms).mean()
        return ce + self.dice_weight * dice + self.cldice_weight * cldice
