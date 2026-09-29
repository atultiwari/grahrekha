# GrahRekha engine, CPU only. Build context: repository root (see docker-compose.yml).

# --- Stage 1: download pinned runtime models, verified against data/checksums.sha256.
# The engine has no internet at runtime (D-016), so everything it needs is baked in here.
# Python base: fetch-data.sh extracts zip archives with python3.
FROM python:3.12-slim AS models
RUN apt-get update \
 && apt-get install -y --no-install-recommends bash curl ca-certificates file \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY scripts/fetch-data.sh scripts/fetch-data.sh
COPY data/checksums.sha256 data/checksums.sha256
RUN bash scripts/fetch-data.sh --only M1,M2,A1,A2

# --- Stage 2: runtime.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app
# MediaPipe's Linux wheel loads OpenGL ES / EGL even when running on CPU.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgles2 libegl1 \
 && rm -rf /var/lib/apt/lists/*

# Dependencies first for layer caching.
COPY services/engine/pyproject.toml services/engine/uv.lock services/engine/.python-version ./
RUN uv sync --locked --no-dev --no-install-project
COPY services/engine/src ./src
RUN uv sync --locked --no-dev

COPY --from=models /build/services/engine/models/weights ./models/weights
COPY rules ./rules
ENV ENGINE_MODELS_DIR=/app/models/weights ENGINE_RULES_DIR=/app/rules

RUN useradd --create-home --uid 10001 engine
USER engine
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["/app/.venv/bin/uvicorn", "grahrekha_engine.server:app", "--host", "0.0.0.0", "--port", "8000"]
