"""Layer 1b — retrieval: embeddings, storage, hybrid search."""
from app.retrieval.embeddings import (
    Embedder,
    FakeEmbedder,
    SentenceTransformerEmbedder,
    get_embedder,
)
from app.retrieval.search import HybridSearcher, SearchResult
from app.retrieval.store import ChunkRecord, ChunkStore, InMemoryStore

__all__ = [
    "Embedder",
    "FakeEmbedder",
    "SentenceTransformerEmbedder",
    "get_embedder",
    "HybridSearcher",
    "SearchResult",
    "ChunkRecord",
    "ChunkStore",
    "InMemoryStore",
]
