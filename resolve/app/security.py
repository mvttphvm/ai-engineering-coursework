"""API-key auth: a single shared key in the X-API-Key header.

Deliberately simple (this is a portfolio v1, not a bank) — but real: when
RESOLVE_API_KEY is set, every non-health endpoint requires it. When it is
unset, auth is disabled for local development and a warning is logged.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import Settings
from app.logging_config import get_logger

log = get_logger(__name__)


def make_api_key_dependency(settings: Settings):
    if not settings.api_key:
        log.warning(
            "RESOLVE_API_KEY is not set — API auth is DISABLED (dev mode)."
        )

    def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
        if not settings.api_key:
            return  # dev mode
        if x_api_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid X-API-Key header.",
            )

    return require_api_key
