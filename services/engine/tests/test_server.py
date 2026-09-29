import importlib

import pytest


def test_asgi_entrypoint_builds_the_app_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENGINE_SHARED_SECRET", "entrypoint")
    import grahrekha_engine.server as server

    reloaded = importlib.reload(server)
    assert reloaded.app.title == "GrahRekha Engine"
