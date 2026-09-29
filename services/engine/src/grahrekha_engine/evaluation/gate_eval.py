"""Evaluate the quality gate on the frozen splits (docs/IMPLEMENTATION-PLAN.md 1B, 1G).

Usage (from services/engine):
  uv run python -m grahrekha_engine.evaluation.gate_eval ../../data [--out ../../docs/eval/gate.md]

Targets: >=97% of negatives rejected; <=5% of positives falsely rejected.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from grahrekha_engine.palm.gate import GateConfig, evaluate_gate
from grahrekha_engine.palm.image_io import InvalidImageError, decode_image
from grahrekha_engine.palm.landmarks import HandLandmarkDetector

MODEL = Path(__file__).resolve().parents[3] / "models/weights/M1-mediapipe/hand_landmarker.task"


@dataclass(frozen=True)
class Outcome:
    path: str
    source: str
    expect: str
    slice: str
    passed: bool
    codes: tuple[str, ...]
    metrics: dict[str, float]


def run(
    data: Path, split: str, detector: HandLandmarkDetector, config: GateConfig
) -> list[Outcome]:
    outcomes = []
    with (data / "splits" / split).open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                image = decode_image((data / row["path"]).read_bytes())
            except InvalidImageError:
                outcomes.append(
                    Outcome(
                        row["path"], row["source"], row["expect"], "", False, ("INVALID_IMAGE",), {}
                    )
                )
                continue
            result = evaluate_gate(image, detector.detect(image), config=config)
            outcomes.append(
                Outcome(
                    row["path"],
                    row["source"],
                    row["expect"],
                    row["skin"] or row["device"] or "-",
                    result.passed,
                    tuple(r.code for r in result.reasons),
                    result.metrics,
                )
            )
    return outcomes


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}% ({n}/{d})" if d else "n/a"


def report(pos: list[Outcome], neg: list[Outcome], config: GateConfig) -> str:
    false_rejects = [o for o in pos if not o.passed]
    rejected = [o for o in neg if not o.passed]
    lines = [
        "# Quality gate evaluation",
        "",
        f"Config: `{json.dumps(config.__dict__)}`",
        "",
        "| Metric | Result | Target |",
        "|---|---|---|",
        f"| Negatives rejected | {pct(len(rejected), len(neg))} | >= 97% |",
        f"| Positives falsely rejected | {pct(len(false_rejects), len(pos))} | <= 5% |",
        "",
        "## False rejections of real palms, by reason",
        "",
    ]
    for code, n in Counter(c for o in false_rejects for c in o.codes).most_common():
        lines.append(f"- `{code}`: {n}")
    lines += ["", "## Positives by source (pass rate)", ""]
    by_source: dict[str, list[Outcome]] = defaultdict(list)
    for o in pos:
        by_source[o.source].append(o)
    for source, items in sorted(by_source.items()):
        lines.append(f"- {source}: {pct(sum(o.passed for o in items), len(items))}")
    lines += ["", "## Positives by skin tone / device slice (pass rate)", ""]
    by_slice: dict[str, list[Outcome]] = defaultdict(list)
    for o in pos:
        by_slice[o.slice].append(o)
    for name, items in sorted(by_slice.items()):
        lines.append(f"- {name}: {pct(sum(o.passed for o in items), len(items))}")
    lines += ["", "## Negatives that slipped through, by source", ""]
    by_neg: dict[str, list[Outcome]] = defaultdict(list)
    for o in neg:
        by_neg[o.source].append(o)
    for source, items in sorted(by_neg.items()):
        missed = [o for o in items if o.passed]
        lines.append(f"- {source}: rejected {pct(len(items) - len(missed), len(items))}")
    return "\n".join(lines) + "\n"


def main() -> None:  # pragma: no cover - needs datasets and models
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--dump", type=Path, help="write per-image outcomes as JSON lines")
    args = parser.parse_args()
    config = GateConfig()
    with HandLandmarkDetector(MODEL) as detector:
        pos = run(args.data, "positives_v1.tsv", detector, config)
        neg = run(args.data, "negatives_v1.tsv", detector, config)
    text = report(pos, neg, config)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    if args.dump:
        with args.dump.open("w") as f:
            for o in pos + neg:
                f.write(json.dumps(o.__dict__) + "\n")


if __name__ == "__main__":  # pragma: no cover
    main()
