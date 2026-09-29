"""FastAPI application factory."""

import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile, status

from grahrekha_engine import __version__
from grahrekha_engine.auth import require_shared_secret
from grahrekha_engine.config import Settings
from grahrekha_engine.contracts import HealthResponse
from grahrekha_engine.contracts.palm import PalmAnalysisV1
from grahrekha_engine.contracts.rules import RulesRequestV1, RulesResponseV1
from grahrekha_engine.palm.image_io import MAX_UPLOAD_BYTES, InvalidImageError
from grahrekha_engine.rules.engine import evaluate_rules
from grahrekha_engine.rules.model import load_rules, rulebase_version


class Analyzer(Protocol):
    def analyze(
        self, data: bytes, declared_hand: Literal["left", "right"] | None
    ) -> PalmAnalysisV1: ...


class _LazyAnalyzer:
    """Loads models on first use (keeps /healthz fast and lets tests run without models)."""

    def __init__(self, factory: Callable[[], Analyzer]) -> None:
        self._factory = factory
        self._instance: Analyzer | None = None
        self._lock = threading.Lock()

    def get(self) -> Analyzer:
        with self._lock:
            if self._instance is None:
                try:
                    self._instance = self._factory()
                except FileNotFoundError as error:
                    raise HTTPException(
                        status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="palm models are not installed (scripts/fetch-data.sh --only M1,M2)",
                    ) from error
            return self._instance

    def close(self) -> None:
        close = getattr(self._instance, "close", None)
        if callable(close):
            close()


def create_app(
    settings: Settings | None = None, analyzer_factory: Callable[[], Analyzer] | None = None
) -> FastAPI:
    resolved = settings or Settings()  # values come from ENGINE_* env vars

    def default_factory() -> Analyzer:
        from grahrekha_engine.palm.pipeline import PalmAnalyzer  # heavy imports, lazily

        return PalmAnalyzer(resolved.models_dir, resolved.segmenter)

    analyzer = _LazyAnalyzer(analyzer_factory or default_factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        analyzer.close()  # an unclosed MediaPipe landmarker hangs interpreter shutdown

    app = FastAPI(title="GrahRekha Engine", version=__version__, lifespan=lifespan)

    @app.get("/healthz")
    def healthz() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    service_auth = Depends(require_shared_secret(resolved.shared_secret))
    v1 = APIRouter(prefix="/v1", dependencies=[service_auth])

    @v1.get("/ping")
    def ping() -> dict[str, bool]:
        return {"pong": True}

    @v1.post("/palm/analyze")
    def analyze_palm(
        file: Annotated[UploadFile, File()],
        declared_hand: Annotated[Literal["left", "right"] | None, Form()] = None,
    ) -> PalmAnalysisV1:
        # Sync route: FastAPI runs it in a worker thread, keeping CPU work off the loop.
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "image is too large (max 20 MB)"
            )
        try:
            return analyzer.get().analyze(data, declared_hand)
        except InvalidImageError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error

    rules = load_rules(resolved.rules_dir / "palm")
    version = rulebase_version(resolved.rules_dir)

    @v1.post("/rules/evaluate")
    def evaluate(request: RulesRequestV1) -> RulesResponseV1:
        statuses = (
            {"extracted", "reviewed", "approved"} if request.include_unreviewed else {"approved"}
        )
        fired = evaluate_rules(request.features, rules, statuses=statuses)  # type: ignore[arg-type]
        return RulesResponseV1(rulebase_version=version, fired=fired)

    app.include_router(v1)
    return app
