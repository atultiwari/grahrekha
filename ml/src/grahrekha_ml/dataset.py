"""Per-line segmentation dataset (canonical palm frame) with alignment-safe augmentation."""

import csv
from pathlib import Path

import cv2
import numpy as np
import torch
from numpy.typing import NDArray
from PIL import Image
from torch.utils.data import Dataset

IGNORE_INDEX = 255
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def augment(
    image: NDArray[np.uint8], label: NDArray[np.uint8], rng: np.random.Generator
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """Geometry (shared by image and label) + photometric changes (image only).

    No horizontal flip: the canonical frame is a fixed left-palm layout, so a flip would
    swap anatomy (thumb side). Geometry is kept small because rectification already
    normalises pose; it only covers residual landmark error.
    """
    h, w = label.shape
    angle = rng.uniform(-10, 10)
    scale = rng.uniform(0.9, 1.1)
    rotation: NDArray[np.float64] = np.asarray(
        cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale), dtype=np.float64
    )
    shift = np.zeros((2, 3))
    shift[:, 2] = rng.uniform(-0.04, 0.04, 2) * np.array([w, h], dtype=np.float64)
    matrix = rotation + shift
    warped: NDArray[np.uint8] = np.asarray(
        cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0)),
        dtype=np.uint8,
    )
    warped_label: NDArray[np.uint8] = np.asarray(
        cv2.warpAffine(label, matrix, (w, h), flags=cv2.INTER_NEAREST, borderValue=0),
        dtype=np.uint8,
    )

    # float64 throughout (NumPy promoted to it anyway when mixing with rng values).
    out: NDArray[np.float64] = warped.astype(np.float64)
    out = out * rng.uniform(0.7, 1.3) + rng.uniform(-25, 25)  # contrast, brightness
    gray = out.mean(axis=2, keepdims=True)
    out = gray + (out - gray) * rng.uniform(0.6, 1.4)  # saturation
    out = out * rng.uniform(0.9, 1.1, 3)  # white balance
    if rng.random() < 0.3:
        out = np.asarray(cv2.GaussianBlur(out, (0, 0), rng.uniform(0.5, 1.5)), dtype=np.float64)
    if rng.random() < 0.3:
        out = out + rng.normal(0, rng.uniform(2, 8), out.shape)
    return np.clip(out, 0, 255).astype(np.uint8), warped_label


class LinesDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, root: Path, train: bool, seed: int = 0) -> None:
        with (root / "index.tsv").open(newline="") as f:
            self.rows = list(csv.DictReader(f, delimiter="\t"))
        self.root = root
        self.train = train
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.rows[index]
        image = np.asarray(Image.open(self.root / row["image"]).convert("RGB"))
        label = np.asarray(Image.open(self.root / row["label"]))
        if self.train:
            image, label = augment(image, label, self.rng)
        x = (image.astype(np.float32) / 255.0 - MEAN) / STD
        return torch.from_numpy(x.transpose(2, 0, 1).copy()), torch.from_numpy(
            label.astype(np.int64)
        )


def sample_weights(dataset: LinesDataset, fate_boost: float = 3.0) -> list[float]:
    """Per-image sampling weights: palms with a fate line are drawn `fate_boost`x as often.

    The fate line appears in only ~22% of training palms; without this the model can
    learn to never predict it (the first v1 run had fate Dice 0 for 6 epochs).
    """
    return [fate_boost if int(row.get("fate") or 0) > 0 else 1.0 for row in dataset.rows]
