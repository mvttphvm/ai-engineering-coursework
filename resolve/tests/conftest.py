"""Shared fixtures: a full Resolve app wired to fakes — no network, no API
keys, no model downloads, no Postgres."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Settings  # noqa: E402
from app.ingestion.pipeline import ingest_directory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.retrieval.embeddings import FakeEmbedder  # noqa: E402
from app.retrieval.search import HybridSearcher  # noqa: E402
from app.retrieval.store import InMemoryStore  # noqa: E402

KB_DIR = PROJECT_ROOT / "data" / "sample_kb"


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        llm_provider="fake",
        llm_fallbacks="",
        gemini_api_key="",
        groq_api_key="",
        api_key="",  # auth disabled unless a test overrides it
        rate_limit_per_min=10000,
        chunk_size=800,
        chunk_overlap=120,
        ask_min_cosine=0.20,
    )


@pytest.fixture()
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture()
def store(settings, embedder) -> InMemoryStore:
    store = InMemoryStore()
    ingest_directory(str(KB_DIR), store, embedder,
                     settings.chunk_size, settings.chunk_overlap)
    return store


@pytest.fixture()
def searcher(store, embedder) -> HybridSearcher:
    return HybridSearcher(store=store, embedder=embedder)


@pytest.fixture()
def client(settings, store, embedder):
    from fastapi.testclient import TestClient

    app = create_app(settings=settings, store=store, embedder=embedder)
    with TestClient(app) as test_client:
        yield test_client
