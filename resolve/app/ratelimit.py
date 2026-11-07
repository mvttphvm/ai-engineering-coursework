"""Simple in-memory fixed-window rate limiting (per client IP).

Good enough for a single-instance deployment and for demonstrating the
pattern; a multi-instance production deployment would move the counters
to Redis. /health is exempt so uptime checks never get throttled.
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_min: int = 120) -> None:
        super().__init__(app)
        self.limit = max(1, limit_per_min)
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        now = time.time()
        window = [t for t in self._hits[client] if now - t < 60.0]
        if len(window) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
                headers={"Retry-After": "60"},
            )
        window.append(now)
        self._hits[client] = window
        return await call_next(request)
