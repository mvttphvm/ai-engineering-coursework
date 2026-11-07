"""Ingestion pipeline: documents -> chunks -> embedded store records."""
from __future__ import annotations

from app.ingestion.chunking import chunk_text
from app.ingestion.loaders import LoadedDocument, load_directory
from app.retrieval.embeddings import Embedder
from app.retrieval.store import ChunkRecord, ChunkStore


def _ingest_documents(docs: list[LoadedDocument], store: ChunkStore,
                      embedder: Embedder, chunk_size: int,
                      chunk_overlap: int) -> dict:
    total_chunks = 0
    for doc in docs:
        # Re-ingesting a source replaces its old chunks (idempotent ingest).
        store.clear_source(doc.source)
        chunks = chunk_text(doc.text, source=doc.source, title=doc.title,
                            chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            continue
        vectors = embedder.embed([c.text for c in chunks])
        records = [
            ChunkRecord(
                chunk_id=c.chunk_id,
                source=c.source,
                title=c.title,
                text=c.text,
                embedding=v,
                metadata=dict(c.metadata),
            )
            for c, v in zip(chunks, vectors)
        ]
        total_chunks += store.add(records)
    return {"documents": len(docs), "chunks": total_chunks}


def ingest_directory(directory: str, store: ChunkStore, embedder: Embedder,
                     chunk_size: int = 800, chunk_overlap: int = 120) -> dict:
    docs = load_directory(directory)
    return _ingest_documents(docs, store, embedder, chunk_size, chunk_overlap)


def ingest_texts(items: list[dict], store: ChunkStore, embedder: Embedder,
                 chunk_size: int = 800, chunk_overlap: int = 120) -> dict:
    """Ingest raw documents passed over the API: {source, title?, text}."""
    docs = [
        LoadedDocument(
            source=item["source"],
            title=item.get("title") or item["source"],
            text=item["text"],
        )
        for item in items
    ]
    return _ingest_documents(docs, store, embedder, chunk_size, chunk_overlap)
