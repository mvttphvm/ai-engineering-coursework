"""Hybrid search: vector similarity + BM25 keyword matching, fused with
Reciprocal Rank Fusion (RRF), with optional cross-encoder reranking.

Why hybrid: vector search catches paraphrases ("sign-in issues" -> password
article), keyword search catches exact terms users actually type ("429",
"rsv_live_", invoice numbers). RRF merges the two ranked lists without
needing to normalize their very different score scales.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.retrieval.embeddings import Embedder, tokenize
from app.retrieval.store import ChunkRecord, ChunkStore

RRF_K = 60  # standard RRF constant


@dataclass
class SearchResult:
    chunk: ChunkRecord
    score: float                      # fused (RRF) score, or rerank score
    vector_rank: int | None = None
    keyword_rank: int | None = None
    cosine: float = 0.0               # raw vector similarity of this chunk

    @property
    def source(self) -> str:
        return self.chunk.source


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class BM25:
    """Small, correct BM25 over a fixed corpus of chunk texts."""

    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(d) for d in documents]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avg_len = (sum(self.doc_len) / len(self.doc_len)) if documents else 0.0
        self._idf: dict[str, float] = {}
        n = len(documents)
        df: dict[str, int] = {}
        for tokens in self.doc_tokens:
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        for token, freq in df.items():
            self._idf[token] = math.log(1 + (n - freq + 0.5) / (freq + 0.5))

    def scores(self, query: str) -> list[float]:
        query_tokens = tokenize(query)
        out: list[float] = []
        for tokens, length in zip(self.doc_tokens, self.doc_len):
            if not tokens:
                out.append(0.0)
                continue
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            score = 0.0
            for qt in query_tokens:
                if qt not in tf:
                    continue
                freq = tf[qt]
                denom = freq + self.k1 * (1 - self.b + self.b * length / max(self.avg_len, 1e-9))
                score += self._idf.get(qt, 0.0) * (freq * (self.k1 + 1)) / denom
            out.append(score)
        return out


@dataclass
class HybridSearcher:
    store: ChunkStore
    embedder: Embedder
    rerank_enabled: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    _reranker: object = field(default=None, repr=False)

    def _load_reranker(self):
        if self._reranker is None:
            from app.retrieval.rerank import CrossEncoderReranker

            self._reranker = CrossEncoderReranker(self.rerank_model)
        return self._reranker

    def search(self, query: str, top_k: int = 5,
               candidate_pool: int = 20) -> list[SearchResult]:
        chunks = self.store.all_chunks()
        if not chunks:
            return []

        # --- vector leg ---
        query_vec = self.embedder.embed([query])[0]
        cosines = [_cosine(query_vec, c.embedding) for c in chunks]
        vector_order = sorted(range(len(chunks)), key=lambda i: -cosines[i])

        # --- keyword leg (BM25) ---
        bm25 = BM25([c.text for c in chunks])
        kw_scores = bm25.scores(query)
        keyword_order = sorted(range(len(chunks)), key=lambda i: -kw_scores[i])

        vector_rank = {idx: r + 1 for r, idx in enumerate(vector_order)}
        keyword_rank = {idx: r + 1 for r, idx in enumerate(keyword_order)}

        # --- RRF fusion (chunks with a 0 score on a leg still get its rank;
        # ranks beyond the pool contribute nothing) ---
        fused: dict[int, float] = {}
        for idx in range(len(chunks)):
            score = 0.0
            if cosines[idx] > 0:
                score += 1.0 / (RRF_K + vector_rank[idx])
            if kw_scores[idx] > 0:
                score += 1.0 / (RRF_K + keyword_rank[idx])
            if score > 0:
                fused[idx] = score

        # Fused score first; exact RRF ties break toward the chunk with the
        # stronger raw vector similarity (the more topical match).
        ranked = sorted(fused.items(), key=lambda kv: (-kv[1], -cosines[kv[0]]))
        results = [
            SearchResult(
                chunk=chunks[idx],
                score=score,
                vector_rank=vector_rank[idx] if cosines[idx] > 0 else None,
                keyword_rank=keyword_rank[idx] if kw_scores[idx] > 0 else None,
                cosine=cosines[idx],
            )
            for idx, score in ranked[:candidate_pool]
        ]

        # --- optional cross-encoder rerank over the fused candidates ---
        if self.rerank_enabled and results:
            reranker = self._load_reranker()
            new_scores = reranker.score(query, [r.chunk.text for r in results])
            for result, s in zip(results, new_scores):
                result.score = float(s)
            results.sort(key=lambda r: -r.score)

        return results[:top_k]
