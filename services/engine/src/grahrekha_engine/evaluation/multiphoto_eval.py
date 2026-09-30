"""Does combining 3 photos make features reproducible? (Phase 2, D-015)

Usage (from services/engine):
  uv run python -m grahrekha_engine.evaluation.multiphoto_eval ../../data [--segmenter v1]

For each retest person and hand (D3; people never used elsewhere) there are 3 rear-camera
and 3 front-camera photos. Compared, feature by feature:
  single:     rear photo i vs front photo i          (one photo each, different camera)
  aggregated: median/majority of 3 rear vs of 3 front (independent photo sets)
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from grahrekha_engine.contracts.palm import PalmFeaturesV1
from grahrekha_engine.evaluation.retest_eval import CATEGORICAL, zone_coverage
from grahrekha_engine.palm.aggregate import aggregate_features
from grahrekha_engine.palm.pipeline import PalmAnalyzer

MODELS = Path(__file__).resolve().parents[3] / "models/weights"
D3 = "raw/D3-axondata-palm-recognition/contactless-palmprint-sample"


def agreement(pairs: list[tuple[PalmFeaturesV1, PalmFeaturesV1]]) -> dict[str, float]:
    return {
        name: float(np.mean([get(a) == get(b) for a, b in pairs]))
        for name, get in CATEGORICAL.items()
    }


def report(
    single: dict[str, float], combined: dict[str, float], coverage: tuple[float, float], n: int
) -> str:
    lines = [
        "# Multi-photo consistency (cross-camera)",
        "",
        f"Hands compared: {n}",
        "",
        "| Feature | 1 photo vs 1 photo | 3 photos vs 3 photos |",
        "|---|---|---|",
    ]
    lines += [f"| {k} | {single[k]:.2f} | {combined[k]:.2f} |" for k in single]
    lines += [
        "",
        f"**Mean agreement:** 1 photo {np.mean(list(single.values())):.2f} → "
        f"3 photos {np.mean(list(combined.values())):.2f} (target >= 0.85)",
        f"Zone coverage (certain endpoints): 1 photo {coverage[0]:.2f}, 3 photos {coverage[1]:.2f}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:  # pragma: no cover - needs datasets and models
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--segmenter", choices=["v0", "v1", "v2"], default="v0")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    with (args.data / "splits/retest_v1.tsv").open(newline="") as f:
        users = sorted({row["group"].split("/")[0] for row in csv.DictReader(f, delimiter="\t")})
    analyzer = PalmAnalyzer(MODELS, args.segmenter)
    photos: dict[tuple[str, str, str], list[PalmFeaturesV1]] = defaultdict(list)
    try:
        for user in users:
            for folder in sorted((args.data / D3 / user).iterdir()):
                hand = "left" if folder.name.startswith("left") else "right"
                camera = "rear" if "back_cam" in folder.name else "front"
                for image in sorted(folder.glob("*.jpg")):
                    result = analyzer.analyze(image.read_bytes(), hand)  # type: ignore[arg-type]
                    if result.features is not None:
                        photos[(user, hand, camera)].append(result.features)
    finally:
        analyzer.close()
    single_pairs, combined_pairs, singles, combined = [], [], [], []
    for user, hand in sorted({(u, h) for u, h, _ in photos}):
        rear, front = photos.get((user, hand, "rear"), []), photos.get((user, hand, "front"), [])
        if len(rear) < 2 or len(front) < 2:
            continue
        single_pairs += list(zip(rear, front, strict=False))
        a, b = aggregate_features(rear), aggregate_features(front)
        combined_pairs.append((a, b))
        singles += rear + front
        combined += [a, b]
    text = report(
        agreement(single_pairs),
        agreement(combined_pairs),
        (zone_coverage({"s": singles}), zone_coverage({"c": combined})),
        len(combined_pairs),
    )
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":  # pragma: no cover
    main()
