"""Cross-encoder reranking (optional, behind RERANK_ENABLED).

Lazy-loads a sentence-transformers CrossEncoder on first use so importing
the app never downloads a model. Reranking is the classic
precision-booster: the hybrid legs retrieve broadly, the cross-encoder
reads (query, chunk) pairs jointly and reorders the top candidates.
"""
from __future__ import annotations


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    def score(self, query: str, texts: list[str]) -> list[float]:
        model = self._load()
        pairs = [(query, t) for t in texts]
        scores = model.predict(pairs)
        return [float(s) for s in scores]
