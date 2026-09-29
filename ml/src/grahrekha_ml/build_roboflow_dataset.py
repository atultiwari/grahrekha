"""Build canonical-frame per-line training data from Roboflow sets (D24) for v2.

Usage (from ml/):  uv run python -m grahrekha_ml.build_roboflow_dataset ../data

Writes data/processed/lines_v2/{train,eval_phone}/ in the lines_v1 format. eval_phone is a
~20% hold-out of the phone-photo set (24rd021) with human line identities: an unbiased
check that PLSU (scanner-like photos, v0-derived identities) cannot give.

Leakage guard: images whose canonical crop is a near-duplicate (dHash) of any PLSU eval
image are dropped, as are near-duplicates within a set (Roboflow augmentation copies).
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from grahrekha_engine.palm.gate import evaluate_gate
from grahrekha_engine.palm.landmarks import HandLandmarkDetector
from grahrekha_engine.palm.rectify import CANONICAL_SIZE, rectify
from PIL import Image

from grahrekha_ml.labels import CLASS_NAMES, IGNORE
from grahrekha_ml.roboflow_labels import (
    class_for,
    dhash,
    hamming,
    is_holdout,
    normalise_width,
    rasterize,
)

OUT_SIZE = 512
LINE_WIDTH_CANONICAL = 13  # PLSU strokes average 6.4 px at 512 (docs/eval/lines-v1.md)
EVAL_DUPLICATE_BITS = 8  # max dHash distance treated as the same photo as a PLSU eval image
SET_DUPLICATE_BITS = 4
WEIGHTS = Path(__file__).resolve().parents[3] / "services/engine/models/weights"
SETS = {
    "24rd021__palm-reading-itwlw__v13": "phone",  # real phone photos: source of eval_phone
    "cv2project-uu3kn__palmistry-zbcbn__v2": "train",
    "palm-reading-test__palm-line-segmentation__v1": "train",
}


def _annotations(coco: dict) -> dict[int, list[tuple[int, list[list[float]]]]]:  # type: ignore[type-arg]
    names = {c["id"]: c["name"] for c in coco["categories"]}
    by_image: dict[int, list[tuple[int, list[list[float]]]]] = {}
    for ann in coco["annotations"]:
        cls = class_for(names.get(ann["category_id"], ""))
        if cls is not None and isinstance(ann.get("segmentation"), list):
            by_image.setdefault(ann["image_id"], []).append((cls, ann["segmentation"]))
    return by_image


def _canonical_sample(
    image: np.ndarray, anns: list[tuple[int, list[list[float]]]], detector: HandLandmarkDetector
) -> tuple[np.ndarray, np.ndarray] | None:
    gate = evaluate_gate(image, detector.detect(image))
    if not gate.passed or gate.detection is None:
        return None
    rect = rectify(image, gate.detection)
    label = rasterize(anns, image.shape[:2])
    size = (CANONICAL_SIZE, CANONICAL_SIZE)
    warped = cv2.warpAffine(label, rect.forward, size, flags=cv2.INTER_NEAREST, borderValue=0)
    canon = normalise_width(np.asarray(warped, dtype=np.uint8), LINE_WIDTH_CANONICAL)
    small_image = cv2.resize(rect.image, (OUT_SIZE, OUT_SIZE), interpolation=cv2.INTER_AREA)
    small_label = cv2.resize(canon, (OUT_SIZE, OUT_SIZE), interpolation=cv2.INTER_NEAREST)
    return small_image, small_label


class _Writer:
    def __init__(self, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        self.out = out
        self.file = (out / "index.tsv").open("w", newline="")
        self.rows = csv.writer(self.file, delimiter="\t", lineterminator="\n")
        self.rows.writerow(["image", "label", "source", *CLASS_NAMES.values(), "ignore"])

    def write(self, stem: str, image: np.ndarray, label: np.ndarray, source: str) -> None:
        Image.fromarray(image).save(self.out / f"{stem}.png")
        Image.fromarray(label).save(self.out / f"{stem}_label.png")
        pixels = [int((label == c).sum()) for c in CLASS_NAMES]
        self.rows.writerow(
            [f"{stem}.png", f"{stem}_label.png", source, *pixels, int((label == IGNORE).sum())]
        )


def build(data: Path) -> dict[str, int]:  # pragma: no cover - needs downloaded data
    eval_hashes = [
        dhash(np.asarray(Image.open(p).convert("RGB")))
        for p in (data / "processed/lines_v1/eval").glob("*.png")
        if not p.name.endswith("_label.png")
    ]
    out_root = data / "processed/lines_v2"
    writers = {"train": _Writer(out_root / "train"), "eval_phone": _Writer(out_root / "eval_phone")}
    counts: Counter[str] = Counter()
    with HandLandmarkDetector(WEIGHTS / "M1-mediapipe/hand_landmarker.task") as detector:
        for folder, role in SETS.items():
            kept_hashes: list[int] = []
            for coco_path in sorted(
                (data / "raw/D24-roboflow" / folder).glob("*/_annotations.coco.json")
            ):
                coco = json.loads(coco_path.read_text())
                anns_by_image = _annotations(coco)
                for info in coco["images"]:
                    anns = anns_by_image.get(info["id"], [])
                    if not any(cls != IGNORE for cls, _ in anns):
                        counts["no_line_labels"] += 1
                        continue
                    # Raw pixels, NOT EXIF-rotated: Roboflow's polygons are in the raw
                    # frame (48/120 phone photos carry an EXIF rotation). MediaPipe and
                    # rectify cope with any hand orientation.
                    with Image.open(coco_path.parent / info["file_name"]) as raw:
                        image = np.asarray(raw.convert("RGB"))
                    sample = _canonical_sample(image, anns, detector)
                    if sample is None:
                        counts["gate_rejected"] += 1
                        continue
                    digest = dhash(sample[0])
                    if any(hamming(digest, h) <= EVAL_DUPLICATE_BITS for h in eval_hashes):
                        counts["duplicate_of_plsu_eval"] += 1
                        continue
                    if any(hamming(digest, h) <= SET_DUPLICATE_BITS for h in kept_hashes):
                        counts["duplicate_within_set"] += 1
                        continue
                    kept_hashes.append(digest)
                    base = info["file_name"].split(".rf.")[0]  # augmented copies share it
                    split = "eval_phone" if role == "phone" and is_holdout(base) else "train"
                    stem = f"{folder.split('__')[0]}_{len(kept_hashes):05d}"
                    writers[split].write(stem, *sample, source=f"D24-{folder}")
                    counts[f"written_{split}"] += 1
    for writer in writers.values():
        writer.file.close()
    return dict(counts)


if __name__ == "__main__":  # pragma: no cover
    print(build(Path(sys.argv[1]).resolve()))
