"""Service-to-service authentication: only the web API layer may call /v1 routes."""

import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import Header, HTTPException, status

SECRET_HEADER = "X-Engine-Secret"  # noqa: S105 - header name, not a secret value


def require_shared_secret(expected: str) -> Callable[[str | None], None]:
    def dependency(
        x_engine_secret: Annotated[str | None, Header(alias=SECRET_HEADER)] = None,
    ) -> None:
        # Constant-time comparison avoids leaking the secret through timing.
        if x_engine_secret is None or not hmac.compare_digest(x_engine_secret, expected):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid engine secret")

    return dependency
