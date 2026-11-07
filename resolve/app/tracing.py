"""Optional Langfuse tracing (M5 polish) — free tier, fully opt-in.

Tracing is active only when BOTH Langfuse keys are present in the
environment (LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY). Without keys —
every test run, every offline eval, any deployment that doesn't want
it — every call here is a silent no-op, and the `langfuse` package
itself is imported lazily so it is never required to run Resolve.

When active, each /ask and /agent/tickets call becomes one Langfuse
trace with a span per stage, carrying the same step data the JSON
response already exposes. A tracing failure never breaks a request:
all Langfuse calls are wrapped and logged, never raised.
"""
from __future__ import annotations

import time
from contextlib import contextmanager

from app.logging_config import get_logger

log = get_logger(__name__)

_client = None
_client_tried = False


def _get_client(settings):
    """Return the Langfuse client, or None when tracing is off/unavailable."""
    global _client, _client_tried
    if _client is not None:
        return _client
    if _client_tried:
        return None
    _client_tried = True
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        log.info("Langfuse tracing enabled (host=%s)", settings.langfuse_host)
    except Exception as exc:  # package missing or bad config — stay silent
        log.warning("Langfuse tracing unavailable (%s); continuing without it.",
                    exc)
        _client = None
    return _client


def tracing_enabled(settings) -> bool:
    return _get_client(settings) is not None


@contextmanager
def trace_span(settings, name: str, input_data: dict | None = None):
    """Context manager yielding a span-like object with .end(output=...).

    No-op (yields None) when tracing is disabled. Usage:

        with trace_span(settings, "ask", {"question": q}) as span:
            ...
            if span is not None:
                span.end(output={"refused": False})
    """
    client = _get_client(settings)
    if client is None:
        yield None
        return
    started = time.monotonic()
    span = None
    try:
        trace = client.trace(name=name, input=input_data)
        span = trace.span(name=name, input=input_data)
    except Exception as exc:
        log.warning("Langfuse trace start failed: %s", exc)
        yield None
        return

    class _Span:
        def end(self, output=None):
            try:
                span.end(output=output,
                         metadata={"duration_ms": round(
                             (time.monotonic() - started) * 1000)})
                client.flush()
            except Exception as exc:
                log.warning("Langfuse trace end failed: %s", exc)

    yield _Span()
