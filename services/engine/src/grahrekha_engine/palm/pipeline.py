"""End-to-end palm analysis: bytes -> gate -> canonical frame -> lines -> features."""

import hashlib
import threading
from pathlib import Path

import numpy as np

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
from grahrekha_engine.palm.image_io import decode_image
from grahrekha_engine.palm.landmarks import HandLandmarkDetector
from grahrekha_engine.palm.rectify import RectifiedPalm, rectify
from grahrekha_engine.palm.segment import v0
from grahrekha_engine.palm.segment.classical import detect_fate_line
from grahrekha_engine.palm.segment.postprocess import LineTrace, trace_line
from grahrekha_engine.palm.types import Handedness

HAND_MODEL = Path("M1-mediapipe/hand_landmarker.task")
LINE_MODEL = Path("M2-palm-line-reader/student_fp16.onnx")
PIPELINE_IDS = {
    "engine": __version__,
    "gate": "g1",
    "rectify": "affine-t1",
    "segmenter": v0.MODEL_ID,
    "fate": "classical-f1",
}


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

    def __init__(self, models_dir: Path) -> None:
        for relative in (HAND_MODEL, LINE_MODEL):
            if not (models_dir / relative).exists():
                raise FileNotFoundError(models_dir / relative)
        self._detector = HandLandmarkDetector(models_dir / HAND_MODEL)
        self._segmenter = v0.PalmLineReaderV0(models_dir / LINE_MODEL)
        self._lock = threading.Lock()

    def analyze(self, data: bytes, declared_hand: Handedness | None) -> PalmAnalysisV1:
        image = decode_image(data)  # raises InvalidImageError with a user-safe message
        with self._lock:
            gate = evaluate_gate(image, self._detector.detect(image), declared_hand=declared_hand)
            if not gate.passed or gate.detection is None:
                return PalmAnalysisV1(gate=_gate_report(gate))
            detection = gate.detection
            rect = rectify(image, detection)
            probs = self._segmenter.predict(image, detection, rect)

        traces: dict[LineName, LineTrace] = {}
        for index, name in enumerate(v0.LINE_CLASSES):
            trace = trace_line(probs[index])
            if trace is not None:
                traces[name] = trace  # type: ignore[index]
        fate = detect_fate_line(rect.image)
        if fate is not None:
            traces["fate"] = fate

        lines = {
            name: line_features(name, traces.get(name), "classical" if name == "fate" else "model")
            for name in ("heart", "head", "life", "fate")
        }
        features = PalmFeaturesV1(
            hand=declared_hand or detection.handedness,
            mirrored=rect.mirrored,
            hand_geometry=hand_geometry(detection.landmarks),
            lines=lines,
            head_life_joined=head_life_joined(traces.get("head"), traces.get("life")),
            pipeline=PIPELINE_IDS,
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
