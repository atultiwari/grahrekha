"""Test-retest consistency: the same hand photographed several times (1D.4, 1G).

Usage (from services/engine):
  uv run python -m grahrekha_engine.evaluation.retest_eval ../../data [--out FILE.md]

retest_v1 groups hold 3 photos of the same hand (same person, hand and camera; different
backgrounds). A feature is consistent in a group when every photo gives the same value.
"""

import argparse
import csv
import time
from collections import defaultdict
from collections.abc import Callable
from itertools import combinations
from pathlib import Path

import numpy as np

from grahrekha_engine.contracts.palm import PalmFeaturesV1
from grahrekha_engine.palm.pipeline import PalmAnalyzer

MODELS = Path(__file__).resolve().parents[3] / "models/weights"
LINES = ("heart", "head", "life", "fate")


def _effective(f: PalmFeaturesV1, name: str, end: str) -> object:
    line = f.lines[name]  # type: ignore[index]
    zone, certain = getattr(line, f"{end}_zone"), getattr(line, f"{end}_zone_certain")
    return zone if certain else "uncertain"


def zone_coverage(groups: dict[str, list[PalmFeaturesV1]]) -> float:
    """Share of present-line endpoints whose zone is certain."""
    flags = [
        getattr(f.lines[n], f"{end}_zone_certain")  # type: ignore[index]
        for fs in groups.values()
        for f in fs
        for n in LINES
        for end in ("start", "end")
        if f.lines[n].present  # type: ignore[index]
    ]
    return sum(flags) / len(flags) if flags else 0.0


CATEGORICAL: dict[str, Callable[[PalmFeaturesV1], object]] = {
    **{f"{n}.present": (lambda f, n=n: f.lines[n].present) for n in LINES},  # type: ignore[misc]
    # Zones as the rules consume them: the zone when certain, otherwise "uncertain".
    **{f"{n}.start_zone": (lambda f, n=n: _effective(f, n, "start")) for n in LINES},  # type: ignore[misc]
    **{f"{n}.end_zone": (lambda f, n=n: _effective(f, n, "end")) for n in LINES},  # type: ignore[misc]
    "head_life_joined": lambda f: f.head_life_joined,
    "palm_shape": lambda f: f.hand_geometry.palm_shape,
    "finger_length": lambda f: f.hand_geometry.finger_length,
    "element": lambda f: f.hand_geometry.element,
    "index_vs_ring": lambda f: f.hand_geometry.index_vs_ring,
}


def _measure(line: str, attr: str) -> Callable[[PalmFeaturesV1], float | None]:
    def get(f: PalmFeaturesV1) -> float | None:
        feature = f.lines[line]  # type: ignore[index]
        value = getattr(feature, attr)
        return float(value) if feature.present and value is not None else None

    return get


CONTINUOUS: dict[str, Callable[[PalmFeaturesV1], float | None]] = {
    f"{line}.{attr}": _measure(line, attr)
    for line in ("heart", "head", "life")
    for attr in ("length", "curvature", "slope_deg")
} | {"life.sweep": _measure("life", "sweep")}


def pair_agreement(values: list[object]) -> float:
    """Share of photo pairs in a group that agree on a value."""
    pairs = list(combinations(values, 2))
    return sum(a == b for a, b in pairs) / len(pairs) if pairs else 1.0


def report(groups: dict[str, list[PalmFeaturesV1]], latencies: list[float], rejected: int) -> str:
    usable = {g: fs for g, fs in groups.items() if len(fs) >= 2}
    lines = [
        "# Test-retest consistency",
        "",
        f"Groups with >= 2 accepted photos: {len(usable)}; photos rejected by the gate: {rejected}",
        "",
        "| Feature | Pairwise agreement |",
        "|---|---|",
    ]
    overall = []
    for name, get in CATEGORICAL.items():
        score = float(np.mean([pair_agreement([get(f) for f in fs]) for fs in usable.values()]))
        overall.append(score)
        lines.append(f"| {name} | {score:.2f} |")
    lines += [
        "",
        f"**Mean categorical agreement: {np.mean(overall):.2f}** (target >= 0.85)",
        f"Zone coverage (endpoints with a certain zone): {zone_coverage(usable):.2f}",
        "",
    ]
    lines += [
        "| Measure | Within-hand SD | Between-hand SD | Reliability (1 - within/between) |",
        "|---|---|---|---|",
    ]
    for name, get in CONTINUOUS.items():
        within, means = [], []
        for fs in usable.values():
            vals = [v for f in fs if (v := get(f)) is not None]
            if len(vals) >= 2:
                within.append(float(np.std(vals, ddof=1)))
                means.append(float(np.mean(vals)))
        if len(means) >= 3:
            w, b = float(np.mean(within)), float(np.std(means, ddof=1))
            rel = 1 - w / b if b > 0 else float("nan")
            lines.append(f"| {name} | {w:.3f} | {b:.3f} | {rel:.2f} |")
        else:
            lines.append(f"| {name} | n/a | n/a | n/a |")
    if latencies:
        lines += [
            "",
            f"Analysis latency (per photo, this machine): p50 {np.percentile(latencies, 50):.2f}s, "
            f"p95 {np.percentile(latencies, 95):.2f}s",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:  # pragma: no cover - needs datasets and models
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--segmenter", choices=["v0", "v1", "v2"], default="v0")
    args = parser.parse_args()
    analyzer = PalmAnalyzer(MODELS, args.segmenter)
    groups: dict[str, list[PalmFeaturesV1]] = defaultdict(list)
    latencies, rejected = [], 0
    try:
        with (args.data / "splits/retest_v1.tsv").open(newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                data = (args.data / row["path"]).read_bytes()
                start = time.perf_counter()
                result = analyzer.analyze(data, row["hand"] or None)  # type: ignore[arg-type]
                latencies.append(time.perf_counter() - start)
                if result.features is None:
                    rejected += 1
                else:
                    groups[row["group"]].append(result.features)
    finally:
        analyzer.close()
    text = report(groups, latencies, rejected)
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":  # pragma: no cover
    main()
