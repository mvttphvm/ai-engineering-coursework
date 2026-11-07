"""Layer 2 — citation-first RAG assistant.

Contract:
- Answers are generated ONLY from retrieved chunks, and every answer
  carries citations ([n] markers mapped to chunk sources).
- If the best retrieved chunk's vector similarity is below the evidence
  threshold, the assistant REFUSES instead of improvising. A support bot
  that says "I don't know" beats one that hallucinates a refund policy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.config import Settings
from app.providers.factory import generate_with_fallback
from app.retrieval.search import HybridSearcher, SearchResult

REFUSAL_MESSAGE = (
    "I don't have enough information in the knowledge base to answer that "
    "confidently. Please rephrase, or contact support for help with this one."
)

_SYSTEM = (
    "You are Resolve, a support assistant. Answer ONLY from the numbered "
    "sources provided. Cite every factual claim with its source number in "
    "square brackets, e.g. [1]. If the sources do not contain the answer, "
    "say you don't know. Never invent policies, prices, or timeframes."
)


@dataclass
class Citation:
    source: str
    chunk_id: str
    snippet: str


@dataclass
class AskResponse:
    question: str
    answer: str
    refused: bool
    citations: list[Citation] = field(default_factory=list)
    provider: str | None = None


def build_prompt(question: str, results: list[SearchResult]) -> str:
    blocks = []
    for i, result in enumerate(results, start=1):
        blocks.append(
            f"[{i}] Source: {result.chunk.source} — {result.chunk.title}\n"
            f"{result.chunk.text}"
        )
    joined = "\n\n".join(blocks)
    return f"Sources:\n{joined}\n\nQuestion: {question}\n\nAnswer with citations:"


def extract_citations(answer: str, results: list[SearchResult]) -> list[Citation]:
    """Map [n] markers in the answer back to retrieved chunks."""
    cited_numbers = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    citations: list[Citation] = []
    for number in sorted(cited_numbers):
        if 1 <= number <= len(results):
            chunk = results[number - 1].chunk
            citations.append(Citation(
                source=chunk.source,
                chunk_id=chunk.chunk_id,
                snippet=chunk.text[:240],
            ))
    if not citations and results:
        # The model answered without markers: still attribute the evidence
        # it was given rather than returning an uncited answer.
        for result in results:
            citations.append(Citation(
                source=result.chunk.source,
                chunk_id=result.chunk.chunk_id,
                snippet=result.chunk.text[:240],
            ))
    return citations


def ask(question: str, searcher: HybridSearcher, settings: Settings,
        top_k: int = 5) -> AskResponse:
    results = searcher.search(question, top_k=top_k)
    best_cosine = max((r.cosine for r in results), default=0.0)
    if not results or best_cosine < settings.ask_min_cosine:
        return AskResponse(
            question=question,
            answer=REFUSAL_MESSAGE,
            refused=True,
            citations=[],
            provider=None,
        )
    prompt = build_prompt(question, results)
    answer_text, provider_name = generate_with_fallback(
        settings, prompt, system=_SYSTEM
    )
    return AskResponse(
        question=question,
        answer=answer_text,
        refused=False,
        citations=extract_citations(answer_text, results),
        provider=provider_name,
    )
