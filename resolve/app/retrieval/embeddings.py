"""Embedders.

`SentenceTransformerEmbedder` is the real one — it imports
sentence-transformers LAZILY on first use, so importing the app (and running
the test suite) never downloads a model.

`FakeEmbedder` is deterministic and offline: a hashed bag-of-words vector.
Cosine similarity on it behaves like soft keyword overlap, which is exactly
what the tests and the offline eval harness need.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


# Function words carry no topic signal; real embedding models learn to
# down-weight them, so the fake embedder drops them explicitly. Without
# this, "what is the..." would cosine-match every chunk in the KB.
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "how", "do", "does",
    "i", "you", "my", "your", "it", "to", "of", "in", "on", "for", "and",
    "or", "if", "can", "me", "we", "be", "am", "at", "by", "with", "from",
}


def _normalize(token: str) -> str:
    """Crude stemming so 'refunds'/'refund', 'expires'/'expire', and
    'tracking'/'track' share a bucket (real embedding models learn this;
    the fake has to fake it)."""
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    return token


class FakeEmbedder:
    """Hashing embedder: each token adds +1 to a bucket chosen by its hash."""

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for token in tokenize(text):
                if token in _STOPWORDS:
                    continue
                token = _normalize(token)
                digest = hashlib.md5(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "little") % self.dim
                vec[bucket] += 1.0
            out.append(_l2_normalize(vec))
        return out


class SentenceTransformerEmbedder:
    """Real embedder backed by sentence-transformers (lazy model load)."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 dim: int = 384) -> None:
        self.model_name = model_name
        self.dim = dim
        self._model = None  # loaded on first embed() call

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in v] for v in vectors]


def get_embedder(settings, fake: bool = False) -> Embedder:
    if fake:
        return FakeEmbedder()
    return SentenceTransformerEmbedder(settings.embedding_model, settings.embedding_dim)
