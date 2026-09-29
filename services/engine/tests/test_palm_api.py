from typing import Literal

import pytest
from fastapi.testclient import TestClient

from grahrekha_engine.config import Settings
from grahrekha_engine.contracts.palm import GateReportV1, PalmAnalysisV1
from grahrekha_engine.main import Analyzer, create_app
from grahrekha_engine.palm.image_io import InvalidImageError

SECRET = "api-test-secret"
HEADERS = {"X-Engine-Secret": SECRET}
REJECTED = PalmAnalysisV1(gate=GateReportV1(passed=False, reasons=[], warnings=[], metrics={}))


class FakeAnalyzer:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[bytes, Literal["left", "right"] | None]] = []

    def analyze(
        self, data: bytes, declared_hand: Literal["left", "right"] | None
    ) -> PalmAnalysisV1:
        self.calls.append((data, declared_hand))
        if self.error:
            raise self.error
        return REJECTED


def _client(analyzer: Analyzer) -> TestClient:
    return TestClient(create_app(Settings(shared_secret=SECRET), analyzer_factory=lambda: analyzer))


def test_requires_the_engine_secret() -> None:
    response = _client(FakeAnalyzer()).post("/v1/palm/analyze", files={"file": ("p.jpg", b"x")})
    assert response.status_code == 401


def test_passes_upload_and_declared_hand_to_the_analyzer() -> None:
    analyzer = FakeAnalyzer()
    response = _client(analyzer).post(
        "/v1/palm/analyze",
        headers=HEADERS,
        files={"file": ("p.jpg", b"img")},
        data={"declared_hand": "left"},
    )
    assert response.status_code == 200
    assert response.json()["schema_version"] == "palm_analysis.v1"
    assert analyzer.calls == [(b"img", "left")]


def test_rejects_an_unknown_declared_hand() -> None:
    response = _client(FakeAnalyzer()).post(
        "/v1/palm/analyze",
        headers=HEADERS,
        files={"file": ("p.jpg", b"x")},
        data={"declared_hand": "middle"},
    )
    assert response.status_code == 422


def test_invalid_image_is_a_400_with_a_safe_message() -> None:
    analyzer = FakeAnalyzer(InvalidImageError("file is not a readable image"))
    response = _client(analyzer).post(
        "/v1/palm/analyze", headers=HEADERS, files={"file": ("p.jpg", b"x")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "file is not a readable image"}


def test_oversized_upload_is_refused_before_analysis() -> None:
    analyzer = FakeAnalyzer()
    big = b"\0" * (20 * 1024 * 1024 + 1)
    response = _client(analyzer).post(
        "/v1/palm/analyze", headers=HEADERS, files={"file": ("p.jpg", big)}
    )
    assert response.status_code == 413
    assert analyzer.calls == []


def test_missing_models_is_a_503_not_a_crash() -> None:
    def broken_factory() -> Analyzer:
        raise FileNotFoundError("hand_landmarker.task")

    client = TestClient(create_app(Settings(shared_secret=SECRET), analyzer_factory=broken_factory))
    response = client.post("/v1/palm/analyze", headers=HEADERS, files={"file": ("p.jpg", b"x")})
    assert response.status_code == 503
    assert "models" in response.json()["detail"]


@pytest.mark.models
def test_real_pipeline_end_to_end(example_palm_bytes: bytes) -> None:
    client = TestClient(create_app(Settings(shared_secret=SECRET)))
    first = client.post(
        "/v1/palm/analyze", headers=HEADERS, files={"file": ("palm.png", example_palm_bytes)}
    )
    assert first.status_code == 200, first.text
    body = PalmAnalysisV1.model_validate(first.json())
    assert body.gate.passed
    assert body.features is not None and body.overlay is not None
    assert all(body.features.lines[name].present for name in ("heart", "head", "life"))
    assert all(
        0 <= x <= body.overlay.width and 0 <= y <= body.overlay.height
        for x, y in body.overlay.landmarks
    )

    again = client.post(
        "/v1/palm/analyze", headers=HEADERS, files={"file": ("palm.png", example_palm_bytes)}
    )
    assert again.json()["feature_hash"] == body.feature_hash  # deterministic
