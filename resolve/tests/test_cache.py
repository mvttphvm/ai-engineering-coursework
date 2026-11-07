"""M5 caching: exact hits, semantic hits, TTL expiry, ingest invalidation."""
import time

from app.cache import AnswerCache
from app.retrieval.embeddings import FakeEmbedder


def _cache(**kw):
    return AnswerCache(ttl_seconds=kw.get("ttl", 300),
                       semantic_threshold=kw.get("threshold", 0.95))


def test_exact_hit_and_miss():
    cache = _cache()
    assert cache.get("how do I reset my password?", 5) is None
    cache.put("How do I reset my password?", 5, {"answer": "A"})
    # normalization: case/whitespace differences still hit exactly
    assert cache.get("how  do i reset my password?", 5) == {"answer": "A"}
    # different top_k is a different entry
    assert cache.get("how do I reset my password?", 3) is None
    stats = cache.stats()
    assert stats["hits"] == 1 and stats["misses"] == 2


def test_semantic_hit_for_reworded_question():
    cache = _cache()
    embedder = FakeEmbedder()
    cache.put("how do I reset my password", 5, {"answer": "A"},
              embedder=embedder)
    # identical meaning words, different surface form
    hit = cache.get("how do I reset my password?", 5, embedder=embedder)
    assert hit == {"answer": "A"}
    assert cache.stats()["semantic_hits"] >= 1


def test_semantic_miss_for_unrelated_question():
    cache = _cache()
    embedder = FakeEmbedder()
    cache.put("how do I reset my password", 5, {"answer": "A"},
              embedder=embedder)
    assert cache.get("what is the refund window for annual plans", 5,
                     embedder=embedder) is None


def test_ttl_expiry():
    cache = _cache(ttl=0)
    cache.put("q", 5, {"answer": "A"})
    time.sleep(0.01)
    assert cache.get("q", 5) is None


def test_clear():
    cache = _cache()
    cache.put("q", 5, {"answer": "A"})
    cache.clear()
    assert cache.get("q", 5) is None
    assert cache.stats()["entries"] == 0


def test_ask_endpoint_serves_second_call_from_cache(client):
    payload = {"question": "how do I reset my password"}
    first = client.post("/ask", json=payload)
    assert first.status_code == 200
    second = client.post("/ask", json=payload)
    assert second.status_code == 200
    assert second.json() == first.json()
    health = client.get("/health").json()
    assert health["cache"]["hits"] >= 1


def test_ingest_invalidates_cache(client):
    payload = {"question": "how do I reset my password"}
    assert client.post("/ask", json=payload).status_code == 200
    resp = client.post("/ingest", json={
        "documents": [{"source": "new.md", "text": "Brand new policy text."}],
    })
    assert resp.status_code == 200
    health = client.get("/health").json()
    assert health["cache"]["entries"] == 0
