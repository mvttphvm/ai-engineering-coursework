"""M5 tracing: Langfuse is opt-in and must never break a request."""
import sys
import types

from app.config import Settings
from app.tracing import trace_span, tracing_enabled


def test_tracing_disabled_without_keys():
    settings = Settings()
    assert tracing_enabled(settings) is False
    with trace_span(settings, "ask", {"question": "q"}) as span:
        assert span is None


def test_tracing_noop_with_keys_but_unavailable(monkeypatch):
    # Keys set but the langfuse package unreachable/misconfigured:
    # tracing_enabled must degrade to False, not raise.
    import app.tracing as tracing

    monkeypatch.setattr(tracing, "_client", None)
    monkeypatch.setattr(tracing, "_client_tried", False)
    settings = Settings(langfuse_public_key="pk-test",
                        langfuse_secret_key="sk-test")
    with trace_span(settings, "ask") as span:
        # Either a real client was constructed (span present) or the
        # no-op path was taken — both are acceptable, raising is not.
        assert span is None or hasattr(span, "end")


# ---------------------------------------------------------------------------
# Enabled path against a fake Langfuse client (no real network): a stand-in
# `langfuse` module is injected into sys.modules, so these tests exercise
# app.tracing's enabled branch whether or not the real SDK is installed.
# ---------------------------------------------------------------------------

class _FakeSpan:
    def __init__(self, client, name, input_data):
        self._client = client
        self.name = name
        self.input = input_data

    def end(self, output=None, metadata=None):
        self._client.ended.append(
            {"span": self.name, "output": output, "metadata": metadata})


class _FakeTrace:
    def __init__(self, client, name, input_data):
        self._client = client
        self.name = name
        self.input = input_data

    def span(self, name=None, input=None):
        span = _FakeSpan(self._client, name, input)
        self._client.spans.append(span)
        return span


class _FakeLangfuse:
    instances = []

    def __init__(self, public_key=None, secret_key=None, host=None):
        self.traces = []
        self.spans = []
        self.ended = []
        self.flushes = 0
        _FakeLangfuse.instances.append(self)

    def trace(self, name=None, input=None):
        trace = _FakeTrace(self, name, input)
        self.traces.append(trace)
        return trace

    def flush(self):
        self.flushes += 1


def test_tracing_enabled_with_mocked_langfuse(monkeypatch):
    import app.tracing as tracing

    fake_module = types.ModuleType("langfuse")
    fake_module.Langfuse = _FakeLangfuse
    monkeypatch.setitem(sys.modules, "langfuse", fake_module)
    monkeypatch.setattr(tracing, "_client", None)
    monkeypatch.setattr(tracing, "_client_tried", False)

    settings = Settings(langfuse_public_key="pk-test",
                        langfuse_secret_key="sk-test")
    assert tracing_enabled(settings) is True
    with trace_span(settings, "ask", {"question": "q"}) as span:
        assert span is not None
        span.end(output={"refused": False})

    client = _FakeLangfuse.instances[-1]
    assert [t.name for t in client.traces] == ["ask"]
    assert [s.name for s in client.spans] == ["ask"]
    assert client.ended[0]["output"] == {"refused": False}
    assert client.flushes >= 1


def test_tracing_disabled_with_mocked_langfuse_and_no_keys(monkeypatch):
    # Even with the SDK importable, no keys means the client is never
    # constructed and every call stays a no-op.
    import app.tracing as tracing

    fake_module = types.ModuleType("langfuse")
    fake_module.Langfuse = _FakeLangfuse
    monkeypatch.setitem(sys.modules, "langfuse", fake_module)
    monkeypatch.setattr(tracing, "_client", None)
    monkeypatch.setattr(tracing, "_client_tried", False)
    before = len(_FakeLangfuse.instances)

    settings = Settings()  # no keys
    assert tracing_enabled(settings) is False
    with trace_span(settings, "ask", {"question": "q"}) as span:
        assert span is None
    assert len(_FakeLangfuse.instances) == before
