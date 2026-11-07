# Resolve — AI Support Operations Platform

A support knowledge system that can **search itself, answer from itself,
grade itself, and act on tickets through itself** — built as one connected
system for **$0**: every model, database, and service it uses is a free
tier or runs locally. No credit card is required for any of it.

It is a portfolio project with a rule: no code here is decoration. Every
layer runs, is tested offline, and can be explained end to end.

## The four layers

```
                 ┌────────────────────────────────────────────┐
   tickets ───►  │ 4. SUPPORT-OPS AGENT (app/agent/)          │
                 │    classify → retrieve → draft →           │
                 │    HUMAN APPROVAL GATE → GitHub Issues     │
                 └──────────────▲─────────────────────────────┘
                                │ uses
   question ──►  ┌──────────────┴─────────────────────────────┐
                 │ 2. RAG ASSISTANT (app/rag.py)              │
                 │    citation-first answers, refusal when    │
                 │    evidence is weak                        │
                 └──────────────▲─────────────────────────────┘
                                │ uses
                 ┌──────────────┴─────────────────────────────┐
                 │ 1. KNOWLEDGE CORE (app/ingestion/,         │
                 │    app/retrieval/)                         │
                 │    load → clean → chunk → embed →          │
                 │    hybrid search (vector + BM25, RRF)      │
                 │    → optional cross-encoder rerank         │
                 └────────────────────────────────────────────┘
   3. EVAL HARNESS (evals/) grades layers 1–2 continuously:
      golden dataset → recall@k, MRR, faithfulness → CI regression gate
```

### Layer 1 — Knowledge core
- Loaders for `.md` / `.txt` / `.html` with a cleaning pass and
  content-hash de-duplication (`app/ingestion/loaders.py`).
- Chunking on paragraph/sentence boundaries with configurable size and
  overlap (`app/ingestion/chunking.py`).
- Embeddings via sentence-transformers, **lazy-loaded** (importing the
  app never downloads a model). Storage behind one interface:
  Postgres + **pgvector** in production (`app/db.py`, `db/init.sql`),
  in-memory for tests and offline evals.
- **Hybrid search**: vector cosine + BM25 keyword scores fused with
  Reciprocal Rank Fusion; fused ties break toward the stronger vector
  match. Optional cross-encoder reranking behind `RERANK_ENABLED`.

### Layer 2 — RAG assistant
- Answers are generated **only** from retrieved chunks, cite their
  sources with `[n]` markers, and — the important part — **refuse** when
  the best chunk's similarity is below the evidence threshold
  (`ASK_MIN_COSINE`). A support bot that says "I don't know" beats one
  that hallucinates a refund policy.

### Layer 3 — Eval harness (the headline)
- A hand-built golden dataset (`evals/golden.jsonl`, 16 Q&A items with
  source labels and expected answer facts).
- `python -m evals.run` reports per-item and average **recall@5, MRR,
  and answer faithfulness**, and exits non-zero if the averages fall
  below the regression thresholds — wired to be a CI gate.
- Faithfulness has two paths: a deterministic keyword proxy (offline)
  and an **LLM-as-judge** hook (`--judge`) that uses whichever provider
  is configured.
- Current results on the sample KB (offline harness, fake embedder +
  extractive fake provider): **recall@5 = 1.000, MRR = 1.000**,
  keyword faithfulness ≈ 0.47 (a real LLM synthesizes multi-fact
  answers and scores higher; the number is reported, not massaged).

### Layer 4 — Support-ops agent
- Loop: **classify → retrieve → draft → human approval gate → act**.
- Classification is a deterministic rules baseline (explainable,
  testable, and the baseline an LLM classifier would be graded against).
- The approval gate is the design's center: without `approve=true` the
  agent is read-only — it drafts but cannot touch the ticket system.
  Every step is recorded in a run trace.
- Its "hands" are the GitHub Issues API, **dry-run by default**: actions
  are recorded, not sent. Going live requires `GITHUB_TOKEN` +
  `GITHUB_REPO` + `AGENT_DRY_RUN=false`.
- The same capabilities are exposed to any MCP client by the **MCP
  server** (`mcp_server/`, official `mcp` Python package, stdio):
  `search_kb` and `get_ticket_draft` tools.

### Production layer (M5)
- **Caching** (`app/cache.py`): two in-memory TTL caches (dependency-
  free, `CACHE_TTL_SECONDS` / `CACHE_MAX_ENTRIES`, both off entirely
  with `CACHE_ENABLED=false`). `/search` responses are cached by
  normalized query + top_k + rerank setting. `/ask` answers are keyed
  by **provider** + question and cached two ways — exact match on the
  normalized question, and a **semantic cache** that reuses an answer
  when a reworded repeat question's embedding clears the similarity
  threshold (`SEMANTIC_CACHE_THRESHOLD`, default 0.95). Both caches
  are **cleared on every ingest**, so a cached response never outlives
  the corpus behind it, and `/search` + `/ask` responses carry an
  `X-Cache: HIT`/`MISS` header so hits are visible to clients. Live
  stats for both caches ride along on `/health`.
- **Tracing** (`app/tracing.py`): optional **Langfuse** traces for
  `/ask` and the agent. Tracing is **off by default** — sign up for
  the free tier at https://cloud.langfuse.com (**no credit card**)
  and set `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` (and
  optionally `LANGFUSE_HOST`) to turn it on. The SDK is imported
  lazily behind a guard, so without keys every call is a no-op with
  the same interface — tests and offline evals send nothing anywhere,
  and a tracing failure can never break a request.
- **CI** (`.github/workflows/ci.yml`): GitHub Actions runs the full
  pytest suite **and** the eval regression gate (`python -m evals.run`
  fails the build below recall@5 0.90 / MRR 0.70) on every push and PR —
  both gates fully offline, no keys or model downloads.
- Already in place from earlier layers: API-key auth, per-IP rate
  limiting, structured JSON logging, Docker + docker-compose.

## The $0 LLM stack — three free providers, one interface

All LLM access goes through a provider abstraction
(`app/providers/`): one `generate()` interface, plain httpx REST calls,
no vendor SDKs. `LLM_PROVIDER` picks the primary; `LLM_FALLBACKS` lists
what to try next. A missing key never crashes anything — the provider is
skipped with a clear message, and if none are available the error tells
you exactly what to set.

| Provider | Cost | Get it | Strength |
|---|---|---|---|
| **Gemini** (AI Studio) | Free tier, **no card** | https://aistudio.google.com/apikey | Smartest free answers, 1M context |
| **Groq** | Free tier, **no card** | https://console.groq.com/keys | Extremely fast; agent loops |
| **Ollama** | Free, local, **no key** | https://ollama.com | Private, offline, no quotas |

(Plus a deterministic fake provider used by tests and the offline eval
harness — an extractive-QA baseline that answers from the sources with
citations.)

## Quickstart

### On a Mac (one command)

```bash
bash scripts/setup_mac.sh   # checks Python/Docker, builds .venv, installs
                            # deps, starts the DB, runs the tests, and
                            # prints where to paste your free keys
```

### Docker (everything)

```bash
cp .env.example .env        # paste free GEMINI_API_KEY / GROQ_API_KEY
docker compose up --build   # API on :8000, Postgres+pgvector on :5432
```

### Local Python

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then load the sample knowledge base and ask it something:

```bash
curl -X POST localhost:8000/ingest -H 'Content-Type: application/json' \
     -d '{"directory": "data/sample_kb"}'
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
     -d '{"question": "How long do refunds take to appear on my statement?"}'
```

Interactive API docs: http://localhost:8000/docs

No database handy? Set `RESOLVE_STORE=memory` and the app runs on the
in-memory store. No keys handy? Set `LLM_PROVIDER=fake` for the offline
extractive answerer.

## API summary

| Endpoint | Auth | What it does |
|---|---|---|
| `GET /health` | open | Status, chunk count, active provider |
| `POST /ingest` | key* | Ingest a server directory or inline documents |
| `GET /search?q=&top_k=` | key* | Hybrid search over the knowledge base |
| `POST /ask` | key* | Citation-first RAG answer (or a refusal) |
| `POST /agent/tickets` | key* | Classify + retrieve + draft a ticket reply; acts only with `"approve": true` |

\* Auth = `X-API-Key` header, enforced when `RESOLVE_API_KEY` is set
(unset = dev mode). A simple in-memory rate limiter
(`RATE_LIMIT_PER_MIN`) protects everything except `/health`.

## MCP server

```bash
python -m mcp_server.server   # stdio; point any MCP client at this
```

Tools: `search_kb(query, top_k)` and `get_ticket_draft(title, body)`
(read-only — drafting never files anything; acting stays behind the
agent's approval gate).

## Evals

```bash
python -m evals.run           # offline: retrieval metrics + keyword faithfulness
python -m evals.run --judge   # + LLM-as-judge faithfulness (needs a key/Ollama)
```

## Tests

```bash
pytest tests/ -q   # 53 tests, fully offline: no keys, no downloads, no DB
```

Covered: chunking (sizes, overlap, hard splits), hybrid ranking on the
real sample KB, /ask citations + refusal + provider-missing error,
provider selection/fallback, the agent approval gate (no approval → zero
recorded actions), GitHub dry-run stickiness, API auth, ingest/search,
and the M5 layer: answer/response caching (exact + semantic hits, TTL
expiry, ingest invalidation, provider namespacing, `X-Cache` headers,
`CACHE_ENABLED=false` bypass) and Langfuse tracing (no-op without keys,
enabled path against a mocked Langfuse client — no real network).

## Configuration

Everything is environment variables — see `.env.example` for the full
list with comments (database URL, provider keys/models, chunking,
reranking, evidence threshold, API key, rate limit, GitHub agent
settings).

## Honest limitations of this v1

- Retrieval ranking runs in Python over the store's chunks. That's the
  right call at KB scale; the pgvector schema (with an HNSW index note in
  `db/init.sql`) is where the vector leg moves when the corpus grows.
- The rate limiter and API-key auth are single-instance grade; a real
  multi-instance deployment would move both to shared infrastructure.
- The classifier is rules-based by design — it's the graded baseline,
  not the final word (the spec's stretch goal is a small fine-tune
  compared against it in the harness).
