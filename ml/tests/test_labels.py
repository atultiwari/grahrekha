import cv2
import numpy as np

from grahrekha_ml.labels import (
    FATE,
    HEAD,
    HEART,
    IGNORE,
    LIFE,
    assign_branch_classes,
    build_label_map,
    split_branches,
)

SIZE = 1024


def _mask(lines: list[list[tuple[int, int]]], width: int = 9) -> np.ndarray:
    m = np.zeros((SIZE, SIZE), np.uint8)
    for pts in lines:
        cv2.polylines(m, [np.array(pts, np.int32)], False, 255, width)
    return m > 0


def _probs(partial: dict[int, list[tuple[int, int]]]) -> np.ndarray:
    """v0-style probabilities (heart, head, life) covering only PART of each line."""
    p = np.zeros((3, SIZE, SIZE), np.float32)
    for channel, pts in partial.items():
        cv2.polylines(p[channel], [np.array(pts, np.int32)], False, 0.9, 11)
    return p


def test_branches_split_at_junctions() -> None:
    cross = _mask([[(200, 500), (800, 500)], [(500, 200), (500, 800)]])
    branches = split_branches(cross)
    assert len(branches) == 4  # a plus sign has four arms


def test_a_partially_detected_line_is_labelled_along_its_whole_length() -> None:
    life = [(380, 450), (420, 650), (470, 850)]
    mask = _mask([life])
    probs = _probs({2: [(380, 450), (400, 550)]})  # v0 saw only the top of the life line
    branches = split_branches(mask)
    classes = assign_branch_classes(branches, probs)
    labels = build_label_map(mask, branches, classes)
    assert (labels[mask] == LIFE).mean() > 0.95  # including the part v0 missed


def test_vertical_central_line_without_model_support_becomes_fate() -> None:
    mask = _mask([[(520, 850), (510, 650), (500, 440)]])
    labels = build_label_map(
        mask, split_branches(mask), assign_branch_classes(split_branches(mask), _probs({}))
    )
    assert (labels[mask] == FATE).mean() > 0.95


def test_unexplained_lines_are_ignored_not_background() -> None:
    mask = _mask([[(650, 700), (760, 760)]])  # short diagonal crease on the outer palm
    branches = split_branches(mask)
    labels = build_label_map(mask, branches, assign_branch_classes(branches, _probs({})))
    assert (labels[mask] == IGNORE).all()
    assert (labels[~mask] == 0).all()


def test_distinct_lines_keep_distinct_classes() -> None:
    heart = [(780, 470), (600, 440), (420, 430)]
    head = [(380, 520), (560, 560), (720, 620)]
    mask = _mask([heart, head])
    probs = _probs({0: heart[:2], 1: head[:2]})
    branches = split_branches(mask)
    labels = build_label_map(mask, branches, assign_branch_classes(branches, probs))
    assert labels[440, 600] == HEART
    assert labels[560, 560] == HEAD
