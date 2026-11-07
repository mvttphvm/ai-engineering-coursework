"""Resolve MCP server — built with the official `mcp` Python package
(FastMCP, stdio transport).

Tools:
  - search_kb(query, top_k): hybrid search over the knowledge base.
  - get_ticket_draft(title, body): classify + retrieve + draft a support
    reply. Read-only by design — drafting never files or modifies a ticket;
    acting stays behind the agent's human approval gate (app/agent).

Run:   python -m mcp_server.server
Point any MCP client (Claude Desktop, an IDE, the agent layer) at that
command. The server loads the sample KB (or RESOLVE_KB_DIR) with the fake
embedder by default so it works offline with zero setup; set
RESOLVE_EMBEDDER=st to use the real sentence-transformers model.
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from app.agent.agent import SupportAgent
from app.config import Settings
from app.ingestion.pipeline import ingest_directory
from app.retrieval.embeddings import FakeEmbedder, get_embedder
from app.retrieval.search import HybridSearcher
from app.retrieval.store import InMemoryStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_searcher() -> HybridSearcher:
    settings = Settings.from_env()
    store = InMemoryStore()
    embedder = (get_embedder(settings)
                if os.environ.get("RESOLVE_EMBEDDER") == "st"
                else FakeEmbedder())
    kb_dir = os.environ.get("RESOLVE_KB_DIR", str(PROJECT_ROOT / "data" / "sample_kb"))
    ingest_directory(kb_dir, store, embedder,
                     settings.chunk_size, settings.chunk_overlap)
    return HybridSearcher(store=store, embedder=embedder)


_settings = Settings.from_env()
_searcher = build_searcher()
_agent = SupportAgent(searcher=_searcher, settings=_settings)

mcp = FastMCP("resolve-kb")


@mcp.tool()
def search_kb(query: str, top_k: int = 5) -> list[dict]:
    """Search the Resolve support knowledge base (hybrid vector + keyword).

    Returns ranked chunks with their source article names — use the source
    names as citations."""
    results = _searcher.search(query, top_k=top_k)
    return [
        {
            "source": r.chunk.source,
            "title": r.chunk.title,
            "chunk_id": r.chunk.chunk_id,
            "text": r.chunk.text,
            "score": round(r.score, 6),
        }
        for r in results
    ]


@mcp.tool()
def get_ticket_draft(title: str, body: str = "") -> dict:
    """Classify a support ticket and draft a reply from the knowledge base.

    Read-only: returns the category, priority, draft text, and sources.
    Nothing is filed or sent — a human approves before any action."""
    result = _agent.process_ticket(title=title, body=body, approve=False)
    return {
        "category": result.category,
        "priority": result.priority,
        "draft": result.draft,
        "sources": result.sources,
        "status": result.status,
        "steps": result.steps,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
