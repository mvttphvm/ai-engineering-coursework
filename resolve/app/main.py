"""Resolve — AI Support Operations Platform (FastAPI app).

Layers:
  1. Knowledge core  — POST /ingest, GET /search   (ingestion + retrieval)
  2. RAG assistant   — POST /ask                   (citation-first answers)
  3. Eval harness    — the evals/ package          (python -m evals.run)
  4. Support agent   — POST /agent/tickets         (classify/retrieve/draft,
                                                    human approval gate)

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app import rag
from app.agent.agent import SupportAgent
from app.cache import AnswerCache, ResponseCache
from app.config import Settings
from app.tracing import trace_span
from app.ingestion.pipeline import ingest_directory, ingest_texts
from app.logging_config import get_logger, setup_logging
from app.providers.base import ProviderError
from app.ratelimit import RateLimitMiddleware
from app.retrieval.embeddings import FakeEmbedder, get_embedder
from app.retrieval.search import HybridSearcher
from app.retrieval.store import InMemoryStore, PostgresStore
from app.security import make_api_key_dependency

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    directory: str | None = Field(
        default=None, description="Server-side directory of .md/.txt/.html files"
    )
    documents: list[dict] | None = Field(
        default=None, description="Inline docs: [{source, title?, text}]"
    )


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class TicketRequest(BaseModel):
    title: str
    body: str = ""
    approve: bool = Field(
        default=False,
        description="Human approval: the agent only 'acts' when true.",
    )


# ---------------------------------------------------------------------------
# App construction (dependencies are injectable for tests)
# ---------------------------------------------------------------------------

def create_app(settings: Settings | None = None,
               store=None, embedder=None) -> FastAPI:
    setup_logging()
    settings = settings or Settings.from_env()

    if store is None:
        if os.environ.get("RESOLVE_STORE", "").lower() == "memory":
            store = InMemoryStore()
        else:
            try:
                store = PostgresStore(settings.database_url)
                store.init_schema()
            except Exception as exc:  # no DB reachable (local dev/tests)
                log.warning(
                    "Postgres unavailable (%s); falling back to in-memory "
                    "store. Set RESOLVE_STORE=memory to silence this.", exc,
                )
                store = InMemoryStore()
    if embedder is None:
        embedder = (FakeEmbedder() if os.environ.get("RESOLVE_EMBEDDER") == "fake"
                    else get_embedder(settings))

    searcher = HybridSearcher(
        store=store,
        embedder=embedder,
        rerank_enabled=settings.rerank_enabled,
        rerank_model=settings.rerank_model,
    )
    agent = SupportAgent(searcher=searcher, settings=settings)
    require_key = make_api_key_dependency(settings)
    answer_cache = AnswerCache(
        ttl_seconds=settings.cache_ttl_seconds,
        max_entries=settings.cache_max_entries,
        semantic_threshold=settings.semantic_cache_threshold,
    ) if settings.cache_enabled else None
    search_cache = ResponseCache(
        ttl_seconds=settings.cache_ttl_seconds,
        max_entries=settings.cache_max_entries,
    ) if settings.cache_enabled else None

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        log.info("Resolve starting (provider=%s, chunks=%d)",
                 settings.llm_provider, store.count())
        yield

    app = FastAPI(title="Resolve — AI Support Operations Platform",
                  version="1.0.0", lifespan=lifespan)
    app.add_middleware(RateLimitMiddleware,
                       limit_per_min=settings.rate_limit_per_min)
    app.state.settings = settings
    app.state.store = store
    app.state.searcher = searcher
    app.state.agent = agent
    app.state.answer_cache = answer_cache
    app.state.search_cache = search_cache

    # ------------------------------------------------------------------
    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "chunks": store.count(),
            "provider": settings.llm_provider,
            "auth_enabled": bool(settings.api_key),
            "cache": (answer_cache.stats() if answer_cache is not None
                      else {"entries": 0, "disabled": True}),
            "search_cache": (search_cache.stats()
                             if search_cache is not None
                             else {"entries": 0, "disabled": True}),
        }

    # ------------------------------------------------------------------
    @app.post("/ingest", dependencies=[Depends(require_key)])
    def ingest(payload: IngestRequest) -> dict:
        if payload.directory:
            try:
                result = ingest_directory(
                    payload.directory, store, embedder,
                    settings.chunk_size, settings.chunk_overlap,
                )
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        elif payload.documents:
            result = ingest_texts(
                payload.documents, store, embedder,
                settings.chunk_size, settings.chunk_overlap,
            )
        else:
            raise HTTPException(
                status_code=422,
                detail="Provide either 'directory' or 'documents'.",
            )
        log.info("ingested: %s (total chunks now %d)", result, store.count())
        if answer_cache is not None:
            answer_cache.clear()  # cached answers must not outlive the corpus
        if search_cache is not None:
            search_cache.clear()  # same for cached search results
        return {**result, "total_chunks": store.count()}

    # ------------------------------------------------------------------
    @app.get("/search", dependencies=[Depends(require_key)])
    def search(q: str = Query(..., min_length=1),
               top_k: int = Query(5, ge=1, le=25),
               response: Response = None) -> dict:
        # Cache key = the request's meaningful inputs: normalized query,
        # top_k, and whether reranking is on (it changes the ranking).
        cache_key = None
        if search_cache is not None:
            cache_key = (
                f"search|rerank={int(settings.rerank_enabled)}|"
                f"top_k={top_k}|{' '.join(q.lower().split())}"
            )
            cached = search_cache.get(cache_key)
            if cached is not None:
                if response is not None:
                    response.headers["X-Cache"] = "HIT"
                return cached
        results = searcher.search(q, top_k=top_k)
        result = {
            "query": q,
            "results": [
                {
                    "chunk_id": r.chunk.chunk_id,
                    "source": r.chunk.source,
                    "title": r.chunk.title,
                    "text": r.chunk.text,
                    "score": round(r.score, 6),
                    "cosine": round(r.cosine, 4),
                    "vector_rank": r.vector_rank,
                    "keyword_rank": r.keyword_rank,
                }
                for r in results
            ],
        }
        if search_cache is not None:
            search_cache.put(cache_key, result)
            if response is not None:
                response.headers["X-Cache"] = "MISS"
        return result

    # ------------------------------------------------------------------
    @app.post("/ask", dependencies=[Depends(require_key)])
    def ask_endpoint(payload: AskRequest,
                     http_response: Response = None) -> dict:
        if answer_cache is not None:
            cached = answer_cache.get(
                payload.question, payload.top_k, embedder=embedder,
                namespace=settings.llm_provider,
            )
            if cached is not None:
                if http_response is not None:
                    http_response.headers["X-Cache"] = "HIT"
                return cached
        with trace_span(settings, "ask",
                        {"question": payload.question}) as span:
            try:
                response = rag.ask(payload.question, searcher, settings,
                                   top_k=payload.top_k)
            except ProviderError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            result = {
                "question": response.question,
                "answer": response.answer,
                "refused": response.refused,
                "provider": response.provider,
                "citations": [
                    {"source": c.source, "chunk_id": c.chunk_id,
                     "snippet": c.snippet}
                    for c in response.citations
                ],
            }
            if span is not None:
                span.end(output={"refused": response.refused,
                                 "provider": response.provider})
        if answer_cache is not None:
            answer_cache.put(
                payload.question, payload.top_k, result,
                embedder=embedder, namespace=settings.llm_provider,
            )
            if http_response is not None:
                http_response.headers["X-Cache"] = "MISS"
        return result

    # ------------------------------------------------------------------
    @app.post("/agent/tickets", dependencies=[Depends(require_key)])
    def process_ticket(payload: TicketRequest) -> dict:
        """Run the support-ops agent on one ticket. Without approve=true
        the agent classifies, retrieves, and drafts — but takes NO action."""
        result = agent.process_ticket(
            title=payload.title, body=payload.body, approve=payload.approve,
        )
        return {
            "ticket": {"title": payload.title, "body": payload.body},
            "category": result.category,
            "priority": result.priority,
            "draft": result.draft,
            "sources": result.sources,
            "status": result.status,
            "action": result.action,
            "steps": result.steps,
        }

    return app


app = create_app()
