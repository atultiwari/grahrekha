"""End-to-end palm analysis: bytes -> gate -> canonical frame -> lines -> features."""

import hashlib
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from grahrekha_engine import __version__
from grahrekha_engine.contracts.palm import (
    GateIssueV1,
    GateReportV1,
    LineName,
    OverlayV1,
    PalmAnalysisV1,
    PalmFeaturesV1,
)
from grahrekha_engine.palm.features import hand_geometry, head_life_joined, line_features
from grahrekha_engine.palm.gate import GateResult, evaluate_gate
from grahrekha_engine.palm.image_io import RGBImage, decode_image
from grahrekha_engine.palm.landmarks import HandLandmarkDetector
from grahrekha_engine.palm.rectify import RectifiedPalm, rectify
from grahrekha_engine.palm.segment import v0, v1
from grahrekha_engine.palm.segment.classical import detect_fate_line
from grahrekha_engine.palm.segment.postprocess import LineTrace, trace_line
from grahrekha_engine.palm.types import HandDetection, Handedness

HAND_MODEL = Path("M1-mediapipe/hand_landmarker.task")
LINE_MODELS = {
    "v0": Path("M2-palm-line-reader/student_fp16.onnx"),
    "v1": Path("M9-grahrekha-lines-v1/model.onnx"),
}
Segmenter = Literal["v0", "v1"]


def pipeline_ids(segmenter: Segmenter) -> dict[str, str]:
    """Versions of every stage, stamped on each feature set (no silent changes)."""
    return {
        "engine": __version__,
        "gate": "g1",
        "rectify": "affine-t1",
        "segmenter": v0.MODEL_ID if segmenter == "v0" else v1.MODEL_ID,
        # v0 has no fate class, so it relies on the classical detector.
        "fate": "classical-f1" if segmenter == "v0" else v1.MODEL_ID,
    }


@dataclass(frozen=True)
class Inspection:
    """Intermediate results, for evaluation scripts and debugging."""

    image: RGBImage
    gate: GateResult
    rect: RectifiedPalm | None = None
    probs: NDArray[np.float32] | None = None  # (4, H, W): heart, head, life, fate (fate may be 0)
    traces: dict[LineName, LineTrace] = field(default_factory=dict)


def _gate_report(result: GateResult) -> GateReportV1:
    return GateReportV1(
        passed=result.passed,
        reasons=[GateIssueV1(code=r.code, message=r.message) for r in result.reasons],
        warnings=[GateIssueV1(code=w.code, message=w.message) for w in result.warnings],
        metrics={k: round(v, 4) for k, v in result.metrics.items()},
    )


def _overlay(
    image_shape: tuple[int, ...],
    landmarks: np.ndarray,
    rect: RectifiedPalm,
    traces: dict[LineName, LineTrace],
) -> OverlayV1:
    def pts(a: np.ndarray) -> list[list[float]]:
        return [[round(float(x), 1), round(float(y), 1)] for x, y in a]

    return OverlayV1(
        width=int(image_shape[1]),
        height=int(image_shape[0]),
        landmarks=pts(landmarks),
        lines={name: [pts(rect.to_original(s)) for s in t.segments] for name, t in traces.items()},
    )


class PalmAnalyzer:
    """Holds loaded models. MediaPipe is not thread-safe, so analysis is serialised."""

    def __init__(self, models_dir: Path, segmenter: Segmenter = "v0") -> None:
        for relative in (HAND_MODEL, LINE_MODELS[segmenter]):
            if not (models_dir / relative).exists():
                raise FileNotFoundError(models_dir / relative)
        self.segmenter: Segmenter = segmenter
        self._detector = HandLandmarkDetector(models_dir / HAND_MODEL)
        self._v0 = (
            v0.PalmLineReaderV0(models_dir / LINE_MODELS["v0"]) if segmenter == "v0" else None
        )
        self._v1 = (
            v1.CanonicalLineSegmenter(models_dir / LINE_MODELS["v1"]) if segmenter == "v1" else None
        )
        self._lock = threading.Lock()

    def _line_probs(
        self, image: RGBImage, detection: HandDetection, rect: RectifiedPalm
    ) -> NDArray[np.float32]:
        if self._v1 is not None:
            return self._v1.predict(rect.image)
        assert self._v0 is not None
        three = self._v0.predict(image, detection, rect)
        return np.concatenate([three, np.zeros_like(three[:1])])  # no fate channel

    def inspect(self, image: RGBImage, declared_hand: Handedness | None = None) -> Inspection:
        with self._lock:
            gate = evaluate_gate(image, self._detector.detect(image), declared_hand=declared_hand)
            if not gate.passed or gate.detection is None:
                return Inspection(image=image, gate=gate)
            rect = rectify(image, gate.detection)
            probs = self._line_probs(image, gate.detection, rect)
        traces: dict[LineName, LineTrace] = {}
        for index, name in enumerate(("heart", "head", "life", "fate")):
            trace = trace_line(probs[index])
            if trace is not None:
                traces[name] = trace  # type: ignore[index]
        if self.segmenter == "v0":
            fate = detect_fate_line(rect.image)
            if fate is not None:
                traces["fate"] = fate
        return Inspection(image=image, gate=gate, rect=rect, probs=probs, traces=traces)

    def analyze(self, data: bytes, declared_hand: Handedness | None) -> PalmAnalysisV1:
        image = decode_image(data)  # raises InvalidImageError with a user-safe message
        result = self.inspect(image, declared_hand)
        gate, rect, traces = result.gate, result.rect, result.traces
        if rect is None or gate.detection is None:
            return PalmAnalysisV1(gate=_gate_report(gate))
        detection = gate.detection
        fate_source: Literal["model", "classical"] = (
            "classical" if self.segmenter == "v0" else "model"
        )
        lines = {
            name: line_features(name, traces.get(name), fate_source if name == "fate" else "model")
            for name in ("heart", "head", "life", "fate")
        }
        features = PalmFeaturesV1(
            hand=declared_hand or detection.handedness,
            mirrored=rect.mirrored,
            hand_geometry=hand_geometry(detection.landmarks),
            lines=lines,
            head_life_joined=head_life_joined(traces.get("head"), traces.get("life")),
            pipeline=pipeline_ids(self.segmenter),
        )
        digest = hashlib.sha256(features.model_dump_json().encode()).hexdigest()
        return PalmAnalysisV1(
            gate=_gate_report(gate),
            features=features,
            overlay=_overlay(image.shape, detection.landmarks, rect, traces),
            feature_hash=digest,
        )

    def close(self) -> None:
        self._detector.close()
