"""Deterministic fake provider for tests and offline demos.

It never calls the network. Given a RAG-style prompt (numbered sources +
"Question:" line) it behaves like an extractive-QA baseline: it scores
every source sentence by token overlap with the question and answers with
the best one or two sentences, each followed by its [n] citation marker.
That exercises the full citation pipeline end to end — and produces
genuinely faithful answers — with zero keys and zero downloads.
"""
from __future__ import annotations

import re

from app.providers.base import LLMProvider
from app.retrieval.embeddings import _STOPWORDS, _normalize, tokenize

# Source blocks are anchored to the exact format both prompt builders emit
# ("[n] Source: <file> — <title>" at line start) so bracketed numbers in
# instruction text (e.g. "cite as [1], [2]") are never mistaken for sources.
_SOURCE_RE = re.compile(
    r"(?m)^\[(\d+)\] Source:[^\n]*\n(.*?)(?=^\[\d+\] Source:|\n\nQuestion:|\Z)",
    re.DOTALL)
_QUESTION_RE = re.compile(r"Question:\s*(.+)", re.DOTALL)


def _content_tokens(text: str) -> set[str]:
    return {_normalize(t) for t in tokenize(text) if t not in _STOPWORDS}


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, canned: str | None = None) -> None:
        self.canned = canned

    def is_configured(self) -> bool:
        return True

    def generate(self, prompt: str, system: str | None = None) -> str:
        if self.canned is not None:
            return self.canned
        sources = _SOURCE_RE.findall(prompt)
        question_match = _QUESTION_RE.search(prompt)
        if not sources or not question_match:
            return "I don't have information about that in the knowledge base."
        question_tokens = _content_tokens(question_match.group(1))

        candidates: list[tuple[int, str, set[str]]] = []
        for number, block in sources:
            for sentence in re.split(r"(?<=[.!?])\s+", " ".join(block.split())):
                sentence = sentence.strip()
                if len(sentence) < 15:
                    continue
                tokens = question_tokens & _content_tokens(sentence)
                if tokens:
                    candidates.append((int(number), sentence, tokens))
        if not candidates:
            return "I don't have information about that in the knowledge base."

        # Greedy coverage (an MMR-style extractive baseline): keep adding
        # the sentence that covers the most still-uncovered question
        # tokens, up to 3 sentences.
        picked: list[tuple[int, str]] = []
        covered: set[str] = set()
        remaining = list(candidates)
        while remaining and len(picked) < 3:
            remaining.sort(key=lambda c: -len(c[2] - covered))
            number, sentence, tokens = remaining.pop(0)
            if not (tokens - covered) and picked:
                break
            picked.append((number, sentence))
            covered |= tokens
        return " ".join(f"{sentence} [{number}]" for number, sentence in picked)
