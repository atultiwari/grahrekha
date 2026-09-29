from pathlib import Path

import numpy as np
from PIL import Image

from grahrekha_ml.dataset import LinesDataset, augment

RNG = np.random.default_rng(0)


def test_augmentation_keeps_image_and_label_aligned() -> None:
    image = np.full((128, 128, 3), 40, np.uint8)
    label = np.zeros((128, 128), np.uint8)
    image[60:68, 20:108] = 250  # a bright "line"
    label[60:68, 20:108] = 3
    for seed in range(10):
        aug_image, aug_label = augment(image, label, np.random.default_rng(seed))
        line = aug_label == 3
        assert line.any()
        # Label pixels land on the bright image pixels (within the colour jitter range).
        assert aug_image[line].mean() > aug_image[aug_label == 0].mean() + 80


def test_augmentation_never_invents_classes_or_smears_labels() -> None:
    label = np.zeros((64, 64), np.uint8)
    label[30:34, 10:54] = 2
    label[0:4, 0:4] = 255
    _, aug_label = augment(np.zeros((64, 64, 3), np.uint8), label, RNG)
    assert set(np.unique(aug_label)) <= {0, 2, 255}


def test_dataset_reads_index_and_returns_tensors(tmp_path: Path) -> None:
    Image.fromarray(np.zeros((32, 32, 3), np.uint8)).save(tmp_path / "a.png")
    Image.fromarray(np.full((32, 32), 3, np.uint8)).save(tmp_path / "a_label.png")
    (tmp_path / "index.tsv").write_text(
        "image\tlabel\tsource\nA\tB\tC\n".replace("A", "a.png").replace("B", "a_label.png")
    )
    item = LinesDataset(tmp_path, train=False)[0]
    assert item[0].shape == (3, 32, 32) and item[1].shape == (32, 32)
    assert int(item[1].max()) == 3
