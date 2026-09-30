"""Per-line evaluation on canonical-frame samples with human line identities.

Usage (from ml/):
  uv run python -m grahrekha_ml.eval_canonical ../data --model <model.onnx> \
      [--dataset lines_v2 --split eval_phone | --dataset lines_v1 --split eval]

Scores the raw model output (probability > 0.5 per line) against labels built by
build_roboflow_dataset.py. Predictions on IGNORE pixels (minor creases) are not counted.
Tolerance: 2.5% of palm length (7 px at 512).
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
from grahrekha_engine.evaluation.line_metrics import tolerant_scores
from grahrekha_engine.palm.segment.v1 import CanonicalLineSegmenter
from numpy.typing import NDArray
from PIL import Image

from grahrekha_ml.labels import CLASS_NAMES, IGNORE
from grahrekha_ml.per_line_eval import LineTally, summarise

TOLERANCE_PX = 0.025 * 560 / 2  # canonical palm unit is 560 px at 1024; labels are 512


def score_sample(
    probs: NDArray[np.float32], label: NDArray[np.uint8], tolerance_px: float
) -> dict[str, LineTally]:
    """probs: (4, H, W) line probabilities at the label's resolution."""
    counted = label != IGNORE
    tallies = {}
    for index, (cls, name) in enumerate(CLASS_NAMES.items()):
        predicted = (probs[index] > 0.5) & counted
        truth = label == cls
        scores = tolerant_scores(predicted, truth, tolerance_px)
        tallies[name] = LineTally(
            bool(truth.any()), bool(predicted.any()), scores.recall, scores.precision
        )
    return tallies


def evaluate(root: Path, model: Path) -> dict[str, list[LineTally]]:  # pragma: no cover
    segmenter = CanonicalLineSegmenter(model)
    tallies: dict[str, list[LineTally]] = {name: [] for name in CLASS_NAMES.values()}
    with (root / "index.tsv").open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            image = np.asarray(Image.open(root / row["image"]).convert("RGB"))
            label = np.asarray(Image.open(root / row["label"]))
            size = (label.shape[1], label.shape[0])
            probs = np.stack(
                [
                    cv2.resize(p, size, interpolation=cv2.INTER_LINEAR)
                    for p in segmenter.predict(image)
                ]
            )
            for name, tally in score_sample(probs, label, TOLERANCE_PX).items():
                tallies[name].append(tally)
    return tallies


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--dataset", default="lines_v2", help="folder under data/processed")
    parser.add_argument("--split", default="eval_phone")
    args = parser.parse_args()
    root = args.data / "processed" / args.dataset / args.split
    header = ["Line", "Palms with line", "Missed", "False alarms", "Recall", "Precision"]
    print(f"Model: {args.model}\nSplit: {root}")
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for r in summarise(evaluate(root, args.model)):
        cells = [r.line, r.truth_present, r.missed, r.false_alarms, r.recall, r.precision]
        print("| " + " | ".join(str(c) for c in cells) + " |")


if __name__ == "__main__":  # pragma: no cover
    main()
