"""Evaluate line detection on PLSU held-out masks (docs/IMPLEMENTATION-PLAN.md 1C, 1G).

Usage (from services/engine):
  uv run python -m grahrekha_engine.evaluation.lines_eval ../../data [--out FILE.md]

PLSU masks mark palm lines without saying which line is which, so this is a
class-agnostic score of "did we find the lines". Per-line accuracy needs line-labelled
ground truth (Roboflow sets or our own annotation, Phase 2).
"""

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image

from grahrekha_engine.evaluation.line_metrics import LineScores, tolerant_scores
from grahrekha_engine.palm.gate import evaluate_gate
from grahrekha_engine.palm.geometry import palm_length
from grahrekha_engine.palm.image_io import decode_image
from grahrekha_engine.palm.landmarks import HandLandmarkDetector
from grahrekha_engine.palm.rectify import RectifiedPalm, rectify
from grahrekha_engine.palm.segment.classical import detect_fate_line
from grahrekha_engine.palm.segment.postprocess import LineTrace, trace_line
from grahrekha_engine.palm.segment.v0 import LINE_CLASSES, PalmLineReaderV0

WEIGHTS = Path(__file__).resolve().parents[3] / "models/weights"
TOLERANCES = (0.015, 0.025)  # fraction of palm length


@dataclass(frozen=True)
class ImageResult:
    path: str
    gate_passed: bool
    raw: dict[float, LineScores]
    traced: dict[float, LineScores]
    with_fate: dict[float, LineScores]
    lines_found: int
    fate_found: bool


def _raster_traces(
    traces: list[LineTrace], rect: RectifiedPalm, shape: tuple[int, int]
) -> NDArray[np.bool_]:
    canvas = np.zeros(shape, np.uint8)
    for trace in traces:
        for segment in trace.segments:
            pts = rect.to_original(segment).round().astype(np.int32)
            cv2.polylines(canvas, [pts], False, 255, 1)
    result: NDArray[np.bool_] = canvas > 0
    return result


def _raw_mask(
    probs: NDArray[np.float32], rect: RectifiedPalm, shape: tuple[int, int]
) -> NDArray[np.bool_]:
    union = probs.max(axis=0)
    back = cv2.warpAffine(union, rect.inverse, (shape[1], shape[0]), flags=cv2.INTER_LINEAR)
    result: NDArray[np.bool_] = back > 0.5
    return result


def evaluate(data: Path, split: str = "lines_eval_v1.tsv") -> list[ImageResult]:
    model = PalmLineReaderV0(WEIGHTS / "M2-palm-line-reader/student_fp16.onnx")
    results = []
    with (
        HandLandmarkDetector(WEIGHTS / "M1-mediapipe/hand_landmarker.task") as detector,
        (data / "splits" / split).open(newline="") as f,
    ):
        for row in csv.DictReader(f, delimiter="\t"):
            image = decode_image((data / row["path"]).read_bytes())
            h, w = image.shape[:2]
            mask_path = data / row["extra"].split('"mask": "')[1].split('"')[0]
            truth = (
                np.asarray(
                    Image.open(mask_path).convert("L").resize((w, h), Image.Resampling.NEAREST)
                )
                > 127
            )
            gate = evaluate_gate(image, detector.detect(image))
            if gate.detection is None or not gate.passed:
                results.append(ImageResult(row["path"], False, {}, {}, {}, 0, False))
                continue
            rect = rectify(image, gate.detection)
            probs = model.predict(image, gate.detection, rect)
            traces = [
                t for i in range(len(LINE_CLASSES)) if (t := trace_line(probs[i])) is not None
            ]
            fate = detect_fate_line(rect.image)
            raw = _raw_mask(probs, rect, (h, w))
            traced = _raster_traces(traces, rect, (h, w))
            with_fate = _raster_traces([*traces, fate] if fate else traces, rect, (h, w))
            length = palm_length(gate.detection.landmarks)
            results.append(
                ImageResult(
                    row["path"],
                    True,
                    {t: tolerant_scores(raw, truth, t * length) for t in TOLERANCES},
                    {t: tolerant_scores(traced, truth, t * length) for t in TOLERANCES},
                    {t: tolerant_scores(with_fate, truth, t * length) for t in TOLERANCES},
                    len(traces),
                    fate is not None,
                )
            )
    return results


def report(results: list[ImageResult]) -> str:
    scored = [r for r in results if r.gate_passed]
    lines = [
        "# Line detection evaluation (PLSU, class-agnostic)",
        "",
        f"Images: {len(results)}; passed the quality gate: {len(scored)}",
        "",
        "| Output | Tolerance | Precision | Recall | F1 |",
        "|---|---|---|---|---|",
    ]
    outputs = (
        ("raw model (p>0.5)", "raw"),
        ("traced lines", "traced"),
        ("traced + classical fate line", "with_fate"),
    )
    for label, attr in outputs:
        for t in TOLERANCES:
            s = [getattr(r, attr)[t] for r in scored]
            p = np.mean([x.precision for x in s])
            rc = np.mean([x.recall for x in s])
            f1 = np.mean([x.f1 for x in s])
            lines.append(f"| {label} | {t:.1%} of palm length | {p:.3f} | {rc:.3f} | {f1:.3f} |")
    found = np.bincount([r.lines_found for r in scored], minlength=4)
    fates = sum(r.fate_found for r in scored)
    lines += [
        "",
        "Lines traced per palm: " + ", ".join(f"{i}: {n}" for i, n in enumerate(found)),
        f"Fate line reported (classical): {fates}/{len(scored)}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:  # pragma: no cover - needs datasets and models
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = report(evaluate(args.data))
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)


if __name__ == "__main__":  # pragma: no cover
    main()
