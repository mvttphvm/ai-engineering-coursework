"""Chunking: split documents into overlapping, retrievable pieces.

Strategy (defensible defaults): split on paragraph boundaries first, pack
paragraphs up to `chunk_size` characters, hard-split anything still too
long on sentence boundaries, and carry `chunk_overlap` characters of the
previous chunk into the next so facts that straddle a boundary survive.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str        # "<source>#<index>"
    source: str          # document/source id (citation target)
    title: str
    text: str
    index: int
    metadata: dict = field(default_factory=dict)


def _split_long_block(block: str, chunk_size: int) -> list[str]:
    """Split an oversized block on sentence boundaries, then hard-cut."""
    sentences = re.split(r"(?<=[.!?])\s+", block)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                pieces.append(current)
                current = ""
            for i in range(0, len(sentence), chunk_size):
                pieces.append(sentence[i:i + chunk_size])
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            pieces.append(current)
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, source: str, title: str = "",
               chunk_size: int = 800, chunk_overlap: int = 120) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    blocks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if current:
                blocks.append(current)
                current = ""
            blocks.extend(_split_long_block(para, chunk_size))
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            blocks.append(current)
            current = para
    if current:
        blocks.append(current)

    chunks: list[Chunk] = []
    for i, block in enumerate(blocks):
        body = block
        if i > 0 and chunk_overlap:
            tail = blocks[i - 1][-chunk_overlap:]
            body = f"{tail} {body}" if tail else body
        chunks.append(Chunk(
            chunk_id=f"{source}#{i}",
            source=source,
            title=title,
            text=body.strip(),
            index=i,
        ))
    return chunks
