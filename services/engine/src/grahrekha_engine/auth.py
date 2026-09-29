"""Service-to-service authentication: only the web API layer may call /v1 routes."""

import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import Header, HTTPException, status

SECRET_HEADER = "X-Engine-Secret"  # noqa: S105 - header name, not a secret value


def require_shared_secret(expected: str) -> Callable[[str | None], None]:
    expected_bytes = expected.encode("utf-8")

    def dependency(
        x_engine_secret: Annotated[str | None, Header(alias=SECRET_HEADER)] = None,
    ) -> None:
        # Compare bytes, not str: hmac.compare_digest raises TypeError on non-ASCII str,
        # which would turn a bad header into a 500. Constant-time either way.
        provided = (x_engine_secret or "").encode("utf-8", errors="replace")
        if not x_engine_secret or not hmac.compare_digest(provided, expected_bytes):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid engine secret")

    return dependency
