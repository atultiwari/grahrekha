"""Build the per-line training set in the canonical palm frame (Phase 2).

Usage (from ml/):  uv run python -m grahrekha_ml.build_lines_dataset ../data

For every PLSU image in lines_train_v1 / lines_eval_v1 that passes the quality gate:
canonical 512px RGB image + label PNG (0 bg, 1 heart, 2 head, 3 life, 4 fate,
255 ignore). Output: data/processed/lines_v1/{train,eval}/ and an index.tsv.
Research-only data: PLSU has no stated licence (D-006, D-014).
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from grahrekha_engine.palm.gate import evaluate_gate
from grahrekha_engine.palm.image_io import decode_image
from grahrekha_engine.palm.landmarks import HandLandmarkDetector
from grahrekha_engine.palm.rectify import CANONICAL_SIZE, rectify
from grahrekha_engine.palm.segment.v0 import PalmLineReaderV0
from PIL import Image

from grahrekha_ml.labels import (
    CLASS_NAMES,
    IGNORE,
    assign_branch_classes,
    build_label_map,
    split_branches,
)

OUT_SIZE = 512
WEIGHTS = Path(__file__).resolve().parents[3] / "services/engine/models/weights"


def build(data: Path) -> dict[str, dict[str, int]]:
    out_root = data / "processed/lines_v1"
    model = PalmLineReaderV0(WEIGHTS / "M2-palm-line-reader/student_fp16.onnx")
    summary: dict[str, dict[str, int]] = {}
    with HandLandmarkDetector(WEIGHTS / "M1-mediapipe/hand_landmarker.task") as detector:
        for split, tsv in (("train", "lines_train_v1.tsv"), ("eval", "lines_eval_v1.tsv")):
            out = out_root / split
            out.mkdir(parents=True, exist_ok=True)
            counts: Counter[str] = Counter()
            rows = list(csv.DictReader((data / "splits" / tsv).open(newline=""), delimiter="\t"))
            with (out / "index.tsv").open("w", newline="") as index:
                writer = csv.writer(index, delimiter="\t", lineterminator="\n")
                writer.writerow(["image", "label", "source", *CLASS_NAMES.values(), "ignore"])
                for row in rows:
                    image = decode_image((data / row["path"]).read_bytes())
                    h, w = image.shape[:2]
                    gate = evaluate_gate(image, detector.detect(image))
                    if not gate.passed or gate.detection is None:
                        counts["gate_rejected"] += 1
                        continue
                    mask_path = data / json.loads(row["extra"])["mask"]
                    mask = (
                        np.asarray(
                            Image.open(mask_path)
                            .convert("L")
                            .resize((w, h), Image.Resampling.NEAREST)
                        )
                        > 127
                    )
                    rect = rectify(image, gate.detection)
                    probs = model.predict(image, gate.detection, rect)
                    size = (CANONICAL_SIZE, CANONICAL_SIZE)
                    canon_mask = (
                        cv2.warpAffine(
                            mask.astype(np.uint8), rect.forward, size, flags=cv2.INTER_NEAREST
                        )
                        > 0
                    )
                    branches = split_branches(canon_mask)
                    labels = build_label_map(
                        canon_mask, branches, assign_branch_classes(branches, probs)
                    )

                    stem = Path(row["path"]).stem
                    small_image = cv2.resize(
                        rect.image, (OUT_SIZE, OUT_SIZE), interpolation=cv2.INTER_AREA
                    )
                    small_labels = cv2.resize(
                        labels, (OUT_SIZE, OUT_SIZE), interpolation=cv2.INTER_NEAREST
                    )
                    Image.fromarray(small_image).save(out / f"{stem}.png")
                    Image.fromarray(small_labels).save(out / f"{stem}_label.png")
                    pixels = [int((small_labels == c).sum()) for c in CLASS_NAMES]
                    writer.writerow(
                        [
                            f"{stem}.png",
                            f"{stem}_label.png",
                            "D2-plsu",
                            *pixels,
                            int((small_labels == IGNORE).sum()),
                        ]
                    )
                    counts["written"] += 1
                    for cls, name in CLASS_NAMES.items():
                        counts[f"has_{name}"] += int((small_labels == cls).any())
            summary[split] = dict(counts)
    return summary


if __name__ == "__main__":  # pragma: no cover
    for split, counts in build(Path(sys.argv[1]).resolve()).items():
        print(split, counts)
