"""Caching (M5): /search response cache, X-Cache headers, provider
namespacing of the answer cache, and the CACHE_ENABLED=off bypass.

The /search cache proof is the X-Cache header the endpoint sets: MISS on
the first request, HIT on an identical repeat — plus identical bodies,
so a hit is both signalled and semantically the stored response.
"""
import time

import pytest

from app.cache import AnswerCache, ResponseCache
from app.config import Settings
from app.main import create_app


# ---------------------------------------------------------------------------
# ResponseCache unit behavior
# ---------------------------------------------------------------------------

def test_response_cache_hit_and_miss():
    cache = ResponseCache(ttl_seconds=60, max_entries=4)
    assert cache.get("k1") is None
    cache.put("k1", {"results": [1, 2]})
    assert cache.get("k1") == {"results": [1, 2]}
    stats = cache.stats()
    assert stats["hits"] == 1 and stats["misses"] == 1


def test_response_cache_ttl_expiry():
    cache = ResponseCache(ttl_seconds=0, max_entries=4)
    cache.put("k1", {"results": []})
    time.sleep(0.01)
    assert cache.get("k1") is None


def test_response_cache_max_entries_eviction():
    cache = ResponseCache(ttl_seconds=60, max_entries=2)
    cache.put("a", {"v": 1})
    cache.put("b", {"v": 2})
    cache.put("c", {"v": 3})  # at capacity -> oldest entry (a) evicted
    assert cache.get("a") is None
    assert cache.get("b") == {"v": 2}
    assert cache.get("c") == {"v": 3}
    assert cache.stats()["entries"] == 2


def test_response_cache_clear():
    cache = ResponseCache(ttl_seconds=60, max_entries=4)
    cache.put("a", {"v": 1})
    cache.clear()
    assert cache.get("a") is None
    assert cache.stats()["entries"] == 0


# ---------------------------------------------------------------------------
# AnswerCache provider namespacing
# ---------------------------------------------------------------------------

def test_answer_cache_is_namespaced_by_provider():
    cache = AnswerCache()
    cache.put("how do I reset my password?", 5, {"answer": "gemini"},
              namespace="gemini")
    # Same question, same top_k, different provider -> different entry.
    assert cache.get("how do I reset my password?", 5,
                     namespace="groq") is None
    assert cache.get("how do I reset my password?", 5,
                     namespace="gemini") == {"answer": "gemini"}
    # The unnamed namespace is its own namespace too.
    assert cache.get("how do I reset my password?", 5) is None


# ---------------------------------------------------------------------------
# /search endpoint caching
# ---------------------------------------------------------------------------

def test_search_second_identical_request_is_a_cache_hit(client):
    first = client.get("/search", params={"q": "refund policy window"})
    assert first.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    second = client.get("/search", params={"q": "refund policy window"})
    assert second.status_code == 200
    assert second.headers.get("X-Cache") == "HIT"
    assert second.json() == first.json()
    health = client.get("/health").json()
    assert health["search_cache"]["hits"] >= 1


def test_search_different_query_is_not_served_from_cache(client):
    assert client.get(
        "/search", params={"q": "refund policy window"}
    ).headers.get("X-Cache") == "MISS"
    other = client.get("/search", params={"q": "delete my account"})
    assert other.headers.get("X-Cache") == "MISS"
    # A different top_k is a different cache entry as well.
    other_k = client.get(
        "/search", params={"q": "refund policy window", "top_k": 3}
    )
    assert other_k.headers.get("X-Cache") == "MISS"


def test_search_cache_cleared_on_ingest(client):
    client.get("/search", params={"q": "refund policy window"})
    resp = client.post("/ingest", json={
        "documents": [{"source": "new.md", "text": "Brand new policy text."}],
    })
    assert resp.status_code == 200
    again = client.get("/search", params={"q": "refund policy window"})
    assert again.headers.get("X-Cache") == "MISS"


def test_ask_second_identical_request_is_a_cache_hit(client):
    payload = {"question": "how do I reset my password"}
    first = client.post("/ask", json=payload)
    assert first.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    second = client.post("/ask", json=payload)
    assert second.status_code == 200
    assert second.headers.get("X-Cache") == "HIT"
    assert second.json() == first.json()


# ---------------------------------------------------------------------------
# CACHE_ENABLED=false bypasses everything
# ---------------------------------------------------------------------------

@pytest.fixture()
def uncached_client(store, embedder):
    from fastapi.testclient import TestClient

    disabled = Settings(
        llm_provider="fake",
        llm_fallbacks="",
        api_key="",
        rate_limit_per_min=10000,
        cache_enabled=False,
    )
    app = create_app(settings=disabled, store=store, embedder=embedder)
    with TestClient(app) as test_client:
        yield test_client


def test_disabled_cache_never_hits(uncached_client):
    for _ in range(2):
        resp = uncached_client.get(
            "/search", params={"q": "refund policy window"})
        assert resp.status_code == 200
        assert resp.headers.get("X-Cache") is None
    payload = {"question": "how do I reset my password"}
    for _ in range(2):
        resp = uncached_client.post("/ask", json=payload)
        assert resp.status_code == 200
        assert resp.headers.get("X-Cache") is None
    health = uncached_client.get("/health").json()
    assert health["cache"] == {"entries": 0, "disabled": True}
    assert health["search_cache"] == {"entries": 0, "disabled": True}
