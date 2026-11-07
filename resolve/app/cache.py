"""Caching for /search and /ask — in-memory, dependency-free (M5 polish).

Two caches, both thread-safe TTL caches with max-entries eviction,
both configured by the same CACHE_* settings and both cleared whenever
new knowledge is ingested (a cached response must never outlive the
corpus behind it):

  1. ResponseCache — generic key -> response-dict cache, used by
     /search. The key is built from the request's meaningful inputs
     (normalized query, top_k, rerank on/off).
  2. AnswerCache — /ask answers, keyed by provider namespace + top_k +
     normalized question, with two lookup layers:
       a. Exact match on the normalized question text.
       b. Semantic match — the question's embedding is compared
          (cosine) against previously cached questions; at or above
          the similarity threshold the stored answer is reused, so a
          reworded repeat of a question ("how do I reset my password"
          vs "password reset steps") costs no retrieval and no LLM
          call.
     Refusals are cached too: they are cheap to serve and equally
     invalidated by an ingest.

Responses served from either cache carry an `X-Cache: HIT` header
(`MISS` otherwise) when CACHE_ENABLED is on; with it off, no caching
happens at all.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field

from app.logging_config import get_logger

log = get_logger(__name__)


def _normalize(question: str) -> str:
    return " ".join(question.lower().split())


@dataclass
class ResponseCache:
    """Generic TTL response cache (used by /search).

    Eviction: expired entries are pruned on every access; when the
    cache is still at capacity, the entry closest to expiry (the
    oldest write) is evicted first.
    """

    ttl_seconds: int = 300
    max_entries: int = 256

    _entries: dict[str, tuple[dict, float]] = field(
        default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _hits: int = 0
    _misses: int = 0

    def _expire(self, now: float) -> None:
        expired = [k for k, (_, exp) in self._entries.items() if exp <= now]
        for k in expired:
            del self._entries[k]

    def _make_room(self) -> None:
        # Eviction happens on write only — a read must never drop a
        # live entry just because the cache happens to be full.
        while len(self._entries) >= self.max_entries and self._entries:
            oldest = min(self._entries, key=lambda k: self._entries[k][1])
            del self._entries[oldest]

    def get(self, key: str) -> dict | None:
        now = time.monotonic()
        with self._lock:
            self._expire(now)
            item = self._entries.get(key)
            if item is None:
                self._misses += 1
                return None
            self._hits += 1
            return item[0]

    def put(self, key: str, value: dict) -> None:
        now = time.monotonic()
        with self._lock:
            self._expire(now)
            if key not in self._entries:
                self._make_room()
            self._entries[key] = (value, now + self.ttl_seconds)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict:
        with self._lock:
            return {
                "entries": len(self._entries),
                "hits": self._hits,
                "misses": self._misses,
                "ttl_seconds": self.ttl_seconds,
                "max_entries": self.max_entries,
            }


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


@dataclass
class _Entry:
    key: str
    value: dict
    embedding: list[float] | None
    expires_at: float


@dataclass
class AnswerCache:
    ttl_seconds: int = 300
    max_entries: int = 256
    semantic_threshold: float = 0.95

    _entries: dict[str, _Entry] = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _hits: int = 0
    _semantic_hits: int = 0
    _misses: int = 0

    def _prune(self, now: float) -> None:
        expired = [k for k, e in self._entries.items() if e.expires_at <= now]
        for k in expired:
            del self._entries[k]
        while len(self._entries) >= self.max_entries and self._entries:
            oldest = min(self._entries.values(), key=lambda e: e.expires_at)
            del self._entries[oldest.key]

    @staticmethod
    def _prefix(top_k: int, namespace: str) -> str:
        # The namespace (the configured LLM provider in main.py) keeps
        # answers from different providers from colliding: the same
        # question answered by Gemini is a different cache entry than
        # the same question answered by Groq.
        return f"{namespace}|{top_k}:" if namespace else f"{top_k}:"

    def get(self, question: str, top_k: int, embedder=None,
            namespace: str = "") -> dict | None:
        """Return a cached /ask response dict, or None on a miss.

        Exact match first; then, when an embedder is supplied, a
        semantic match against cached questions with the same top_k
        and namespace.
        """
        prefix = self._prefix(top_k, namespace)
        key = prefix + _normalize(question)
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            entry = self._entries.get(key)
            if entry is not None:
                self._hits += 1
                return entry.value
            if embedder is not None:
                try:
                    vec = embedder.embed([question])[0]
                except Exception as exc:  # embedding must never break /ask
                    log.warning("semantic cache lookup skipped: %s", exc)
                    vec = None
                if vec is not None:
                    best: _Entry | None = None
                    best_sim = 0.0
                    for e in self._entries.values():
                        if e.embedding is None or not e.key.startswith(prefix):
                            continue
                        sim = _cosine(vec, e.embedding)
                        if sim > best_sim:
                            best, best_sim = e, sim
                    if best is not None and best_sim >= self.semantic_threshold:
                        self._semantic_hits += 1
                        log.info("semantic cache hit (cosine=%.3f) for %r",
                                 best_sim, question)
                        return best.value
            self._misses += 1
            return None

    def put(self, question: str, top_k: int, value: dict,
            embedder=None, namespace: str = "") -> None:
        key = self._prefix(top_k, namespace) + _normalize(question)
        vec = None
        if embedder is not None:
            try:
                vec = embedder.embed([question])[0]
            except Exception as exc:
                log.warning("semantic cache store skipped: %s", exc)
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            self._entries[key] = _Entry(
                key=key, value=value, embedding=vec,
                expires_at=now + self.ttl_seconds,
            )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict:
        with self._lock:
            return {
                "entries": len(self._entries),
                "hits": self._hits,
                "semantic_hits": self._semantic_hits,
                "misses": self._misses,
                "ttl_seconds": self.ttl_seconds,
                "semantic_threshold": self.semantic_threshold,
            }
