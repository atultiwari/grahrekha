"""Freeze evaluation splits from the R&D datasets in data/raw (see docs/IMPLEMENTATION-PLAN.md 1A).

Usage (from ml/):  uv run python -m grahrekha_ml.splits ../data

Writes git-ignored TSVs to data/splits/ (paths relative to data/):
  positives_v1.tsv      palm-side photos the gate should ACCEPT
  negatives_v1.tsv      images the gate should REJECT (with the expected reason)
  lines_eval_v1.tsv     PLSU image/mask pairs held out for line-detection evaluation
  lines_train_v1.tsv    the remaining PLSU pairs (never evaluated on)
  retest_v1.tsv         groups of photos of the same hand (test-retest agreement)
Materialises non-file negatives (pets parquet, QuickDraw strokes) into data/processed/.
Deterministic: same data + same SEED -> identical files.
"""

import csv
import io
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

from grahrekha_ml.render import render_quickdraw
from grahrekha_ml.sampling import stratified_sample

SEED = 20260929
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class Row:
    path: str
    source: str
    expect: str  # "palm" or a rejection reason code
    hand: str = ""
    skin: str = ""
    device: str = ""
    group: str = ""
    extra: dict[str, str] = field(default_factory=dict)


def _rel(data: Path, p: Path) -> str:
    return p.relative_to(data).as_posix()


def _images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)


# ---------------------------------------------------------------- positives
def eleven_k(data: Path, aspect_prefix: str) -> list[Row]:
    info = data / "raw/D1-11k-hands/HandInfo.csv"
    rows = []
    with info.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["aspectOfHand"].startswith(aspect_prefix) and r["accessories"] == "0":
                hand = r["aspectOfHand"].split()[-1]
                expect = "palm" if aspect_prefix == "palmar" else "BACK_OF_HAND"
                rows.append(
                    Row(
                        _rel(data, data / "raw/D1-11k-hands/Hands" / r["imageName"]),
                        "D1-11k",
                        expect,
                        hand=hand,
                        skin=r["skinColor"],
                        device="scanner-like",
                        group=r["id"],
                    )
                )
    return rows


def axondata(data: Path) -> dict[str, list[Row]]:
    """D3 phone photos grouped by user. 'back_cam' = phone rear camera (palm still faces it)."""
    root = data / "raw/D3-axondata-palm-recognition"
    meta = {}
    with (root / "metadata_comprehensive.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            meta[f"user_{r['user_id']}"] = r
    by_user: dict[str, list[Row]] = {}
    for user_dir in sorted((root / "contactless-palmprint-sample").iterdir()):
        if not user_dir.is_dir():
            continue
        m = meta.get(user_dir.name, {})
        for img in _images(user_dir):
            hand = "left" if img.parent.name.startswith("left") else "right"
            cam = "rear" if "back_cam" in img.parent.name else "front"
            by_user.setdefault(user_dir.name, []).append(
                Row(
                    _rel(data, img),
                    "D3-axondata",
                    "palm",
                    hand=hand,
                    skin=m.get("ethnicity", ""),
                    device=f"{m.get('device_model', '')} ({cam})",
                    group=f"{user_dir.name}/{img.parent.name}",
                )
            )
    return by_user


def dslr_palms(data: Path) -> list[Row]:
    root = data / "raw/D4-human-palm-images"
    return [
        Row(
            _rel(data, p), "D4-dslr", "palm", device="dslr", extra={"gender": p.parent.name.lower()}
        )
        for p in _images(root)
    ]


def yeonsumia_samples(data: Path) -> list[Row]:
    return [
        Row(_rel(data, p), "M3-samples", "palm", device="phone")
        for p in _images(data / "raw/M3-yeonsumia-samples")
    ]


# ---------------------------------------------------------------- negatives
def pets(data: Path, n: int) -> list[Row]:
    out = data / "processed/negatives/pets"
    out.mkdir(parents=True, exist_ok=True)
    table = pq.read_table(data / "raw/D8-oxford-pets-test/data/test-00000-of-00001.parquet")
    records = table.to_pylist()
    picked = stratified_sample(records, key=lambda r: r["label_cat_dog"], n=n, seed=SEED)
    rows = []
    for r in picked:
        target = out / f"{r['image_id']}.jpg"
        if not target.exists():
            Image.open(io.BytesIO(r["image"]["bytes"])).convert("RGB").save(target, quality=90)
        rows.append(Row(_rel(data, target), "D8-pets", "NO_HAND"))
    return rows


def quickdraw(data: Path, n: int) -> list[Row]:
    out = data / "processed/negatives/quickdraw"
    out.mkdir(parents=True, exist_ok=True)
    drawings = []
    with (data / "raw/D6-quickdraw-hand/hand.ndjson").open() as f:
        for i, line in enumerate(f):
            if i >= 5000:
                break
            d = json.loads(line)
            if d.get("recognized"):
                drawings.append(d)
    picked = stratified_sample(drawings, key=lambda d: d["countrycode"][:1], n=n, seed=SEED)
    rows = []
    for d in picked:
        target = out / f"{d['key_id']}.png"
        if not target.exists():
            render_quickdraw(d["drawing"], size=512, line_width=6).save(target)
        rows.append(Row(_rel(data, target), "D6-quickdraw", "NO_HAND"))
    return rows


def folder_negatives(data: Path, folder: str, source: str, n: int, expect: str) -> list[Row]:
    rows = [Row(_rel(data, p), source, expect) for p in _images(data / folder)]
    return stratified_sample(rows, key=lambda r: Path(r.path).parent.name, n=n, seed=SEED)


# ---------------------------------------------------------------- lines
def plsu_pairs(data: Path) -> list[Row]:
    root = data / "raw/D2-plsu/PLSU"
    rows = []
    for img in _images(root / "img"):
        mask = root / "Mask" / f"{img.stem}.png"
        if mask.exists():
            rows.append(Row(_rel(data, img), "D2-plsu", "palm", extra={"mask": _rel(data, mask)}))
    return rows


# ---------------------------------------------------------------- output
COLUMNS = ["path", "source", "expect", "hand", "skin", "device", "group", "extra"]


def write_tsv(path: Path, rows: Iterable[Row]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for r in rows:
            extra = json.dumps(r.extra, sort_keys=True) if r.extra else ""
            w.writerow([r.path, r.source, r.expect, r.hand, r.skin, r.device, r.group, extra])
            count += 1
    return count


def build(data: Path) -> dict[str, int]:
    splits = data / "splits"

    # D3 users are split: retest users never appear in positives (no leakage).
    d3 = axondata(data)
    users = sorted(d3)
    retest_users = set(stratified_sample(users, key=lambda u: "all", n=10, seed=SEED))
    d3_pos = [r for u in users if u not in retest_users for r in d3[u]]
    retest = [r for u in sorted(retest_users) for r in d3[u] if "rear" in r.device]

    positives = (
        stratified_sample(eleven_k(data, "palmar"), key=lambda r: (r.skin, r.hand), n=60, seed=SEED)
        + stratified_sample(d3_pos, key=lambda r: (r.skin, r.hand, r.device), n=60, seed=SEED)
        + stratified_sample(dslr_palms(data), key=lambda r: r.extra["gender"], n=30, seed=SEED)
        + yeonsumia_samples(data)
    )
    negatives = (
        stratified_sample(eleven_k(data, "dorsal"), key=lambda r: (r.skin, r.hand), n=80, seed=SEED)
        + folder_negatives(
            data, "raw/D7-imagenette2-320/imagenette2-320/val", "D7-imagenette", 60, "NO_HAND"
        )
        + pets(data, 40)
        + folder_negatives(data, "raw/D9-lfw-sample/data", "D9-lfw", 40, "NO_HAND")
        + folder_negatives(data, "raw/D10-dfu-feet/DFU/Original Images", "D10-feet", 40, "NO_HAND")
        + quickdraw(data, 40)
    )
    pairs = plsu_pairs(data)
    lines_eval = stratified_sample(pairs, key=lambda r: "all", n=100, seed=SEED)
    eval_paths = {r.path for r in lines_eval}
    lines_train = [r for r in pairs if r.path not in eval_paths]

    return {
        "positives_v1": write_tsv(splits / "positives_v1.tsv", positives),
        "negatives_v1": write_tsv(splits / "negatives_v1.tsv", negatives),
        "lines_eval_v1": write_tsv(splits / "lines_eval_v1.tsv", lines_eval),
        "lines_train_v1": write_tsv(splits / "lines_train_v1.tsv", lines_train),
        "retest_v1": write_tsv(splits / "retest_v1.tsv", retest),
    }


if __name__ == "__main__":  # pragma: no cover
    counts = build(Path(sys.argv[1]).resolve())
    for name, n in counts.items():
        print(f"{name}: {n}")
