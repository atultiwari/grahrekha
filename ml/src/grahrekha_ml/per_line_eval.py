"""Per-line evaluation against derived per-line labels (Phase 2).

Usage (from ml/):  uv run python -m grahrekha_ml.per_line_eval ../data --segmenter v1

Ground truth: data/processed/lines_v1/eval (PLSU held-out masks with line identity from
labels.py). Caveat: identity comes partly from v0, so it favours v0 slightly; the masks
themselves are human-drawn and complete. Tolerance: 2.5% of palm length (14 canonical px).
"""

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from grahrekha_engine.evaluation.line_metrics import tolerant_scores
from grahrekha_engine.palm.features import zone_of
from grahrekha_engine.palm.image_io import decode_image
from grahrekha_engine.palm.pipeline import PalmAnalyzer
from grahrekha_engine.palm.rectify import CANONICAL_SIZE
from PIL import Image

from grahrekha_ml.labels import CLASS_NAMES

WEIGHTS = Path(__file__).resolve().parents[3] / "services/engine/models/weights"
TOLERANCE_PX = 0.025 * 560


@dataclass(frozen=True)
class LineTally:
    truth_present: bool
    predicted: bool
    recall: float
    precision: float


@dataclass(frozen=True)
class LineSummary:
    line: str
    truth_present: int
    missed: int
    false_alarms: int
    recall: float | None
    precision: float | None


def summarise(tallies: dict[str, list[LineTally]]) -> list[LineSummary]:
    out = []
    for line, items in tallies.items():
        with_truth = [t for t in items if t.truth_present]
        both = [t for t in with_truth if t.predicted]
        out.append(
            LineSummary(
                line=line,
                truth_present=len(with_truth),
                missed=sum(not t.predicted for t in with_truth),
                false_alarms=sum(t.predicted and not t.truth_present for t in items),
                recall=round(float(np.mean([t.recall for t in with_truth])), 3)
                if with_truth
                else None,
                precision=round(float(np.mean([t.precision for t in both])), 3) if both else None,
            )
        )
    return out


def heart_end_zone(points: np.ndarray) -> str | None:
    """Zone of the heart line's index-side end (smallest canonical x; left-palm layout)."""
    if len(points) == 0:
        return None
    return str(zone_of(points[int(np.argmin(points[:, 0]))]))


def zone_agreement(
    pairs: list[tuple[str, str]],
) -> tuple[float | None, dict[tuple[str, str], int]]:
    """Share of (human, predicted) zone pairs that agree, plus counts of each disagreement."""
    if not pairs:
        return None, {}
    agree = sum(human == predicted for human, predicted in pairs)
    confusions = Counter(pair for pair in pairs if pair[0] != pair[1])
    return agree / len(pairs), dict(confusions)


@dataclass(frozen=True)
class Evaluation:
    lines: list[LineSummary]
    heart_zone_pairs: list[tuple[str, str]]


def evaluate(data: Path, segmenter: str) -> Evaluation:  # pragma: no cover - data
    root = data / "processed/lines_v1/eval"
    tallies: dict[str, list[LineTally]] = {name: [] for name in CLASS_NAMES.values()}
    heart_pairs: list[tuple[str, str]] = []
    analyzer = PalmAnalyzer(WEIGHTS, segmenter)  # type: ignore[arg-type]
    try:
        for row in csv.DictReader(
            (data / "splits/lines_eval_v1.tsv").open(newline=""), delimiter="\t"
        ):
            label_path = root / f"{Path(row['path']).stem}_label.png"
            if not label_path.exists():
                continue  # rejected by the gate when the dataset was built
            label = np.asarray(Image.open(label_path))
            label = cv2.resize(
                label, (CANONICAL_SIZE, CANONICAL_SIZE), interpolation=cv2.INTER_NEAREST
            )
            found = analyzer.inspect(decode_image((data / row["path"]).read_bytes()))
            for cls, name in CLASS_NAMES.items():
                truth = label == cls
                canvas = np.zeros((CANONICAL_SIZE, CANONICAL_SIZE), np.uint8)
                trace = found.traces.get(name)  # type: ignore[call-overload]
                if trace is not None:
                    for segment in trace.segments:
                        cv2.polylines(canvas, [segment.round().astype(np.int32)], False, 255, 1)
                predicted = canvas > 0
                if name == "heart" and trace is not None and truth.any():
                    ys, xs = np.nonzero(truth)
                    human = heart_end_zone(np.column_stack([xs, ys]).astype(float))
                    ours = heart_end_zone(np.concatenate(trace.segments))
                    if human and ours:
                        heart_pairs.append((human, ours))
                scores = tolerant_scores(predicted, truth, TOLERANCE_PX)
                tallies[name].append(
                    LineTally(
                        bool(truth.any()), bool(predicted.any()), scores.recall, scores.precision
                    )
                )
    finally:
        analyzer.close()
    return Evaluation(summarise(tallies), heart_pairs)


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--segmenter", choices=["v0", "v1"], default="v1")
    args = parser.parse_args()
    header = ["Line", "Palms with line", "Missed", "False alarms", "Recall", "Precision"]
    print(f"Segmenter: {args.segmenter}")
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    result = evaluate(args.data, args.segmenter)
    for r in result.lines:
        cells = [r.line, r.truth_present, r.missed, r.false_alarms, r.recall, r.precision]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    agreement, confusions = zone_agreement(result.heart_zone_pairs)
    agreed = len(result.heart_zone_pairs) - sum(confusions.values())
    print(f"\nHeart end-zone agreement: {agreement:.2f} ({agreed}/{len(result.heart_zone_pairs)})")
    for (human, predicted), count in sorted(confusions.items(), key=lambda kv: -kv[1]):
        print(f"- human {human} vs predicted {predicted}: {count}")


if __name__ == "__main__":  # pragma: no cover
    main()
