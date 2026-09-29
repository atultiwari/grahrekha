"""FastAPI application factory."""

from fastapi import APIRouter, Depends, FastAPI

from grahrekha_engine import __version__
from grahrekha_engine.auth import require_shared_secret
from grahrekha_engine.config import Settings
from grahrekha_engine.contracts import HealthResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()  # values come from ENGINE_* env vars
    app = FastAPI(title="GrahRekha Engine", version=__version__)

    @app.get("/healthz")
    def healthz() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    service_auth = Depends(require_shared_secret(resolved.shared_secret))
    v1 = APIRouter(prefix="/v1", dependencies=[service_auth])

    @v1.get("/ping")
    def ping() -> dict[str, bool]:
        return {"pong": True}

    app.include_router(v1)
    return app
