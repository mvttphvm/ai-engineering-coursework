"""Retrieval + answer metrics for the eval harness."""
from __future__ import annotations


def recall_at_k(retrieved_sources: list[str], expected: list[str], k: int) -> float:
    """Fraction of expected sources present in the top-k retrieved sources."""
    if not expected:
        return 1.0
    top = set(retrieved_sources[:k])
    hits = sum(1 for source in expected if source in top)
    return hits / len(expected)


def reciprocal_rank(retrieved_sources: list[str], expected: list[str]) -> float:
    """1/rank of the first expected source (0 if none was retrieved)."""
    expected_set = set(expected)
    for i, source in enumerate(retrieved_sources, start=1):
        if source in expected_set:
            return 1.0 / i
    return 0.0


def keyword_faithfulness(answer: str, expected_keywords: list[str]) -> float:
    """Cheap faithfulness proxy: fraction of expected answer keywords that
    actually appear in the generated answer. Offline and deterministic —
    the LLM-as-judge path (evals/run.py --judge) complements it when a
    provider key is available."""
    if not expected_keywords:
        return 1.0
    lowered = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in lowered)
    return hits / len(expected_keywords)
