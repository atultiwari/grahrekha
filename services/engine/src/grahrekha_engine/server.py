"""ASGI entry point: `uv run uvicorn grahrekha_engine.server:app`."""

from grahrekha_engine.main import create_app

app = create_app()
