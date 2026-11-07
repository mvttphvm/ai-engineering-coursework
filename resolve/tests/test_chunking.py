"""Chunking behavior: sizes, overlap, boundaries, metadata."""
from app.ingestion.chunking import chunk_text


def test_chunks_respect_size_limit():
    text = "\n\n".join(f"Paragraph {i}. " + "word " * 60 for i in range(10))
    chunks = chunk_text(text, source="doc.md", chunk_size=400, chunk_overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        # overlap tail is prepended, so allow chunk_size + overlap
        assert len(chunk.text) <= 400 + 50


def test_chunk_ids_and_sources():
    chunks = chunk_text("Hello world. This is one small doc.",
                        source="a.md", title="A")
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "a.md#0"
    assert chunks[0].source == "a.md"
    assert chunks[0].title == "A"


def test_overlap_carries_previous_tail():
    para = "alpha " * 100  # ~600 chars
    text = f"{para}\n\n{para}\n\n{para}"
    chunks = chunk_text(text, source="x.md", chunk_size=700, chunk_overlap=40)
    assert len(chunks) >= 2
    # the second chunk begins with carried-over overlap text from block 1
    # (the tail is cut at a character boundary, so it may start mid-word)
    assert "alpha" in chunks[1].text[:45]
    assert len(chunks[1].text) > 600  # overlap tail + its own block


def test_long_sentence_is_hard_split():
    text = "x" * 5000
    chunks = chunk_text(text, source="big.md", chunk_size=1000, chunk_overlap=0)
    assert len(chunks) == 5
    assert all(len(c.text) <= 1000 for c in chunks)


def test_invalid_overlap_rejected():
    import pytest

    with pytest.raises(ValueError):
        chunk_text("hello", source="s.md", chunk_size=100, chunk_overlap=100)
