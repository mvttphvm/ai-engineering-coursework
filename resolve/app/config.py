"""Environment-driven configuration. Everything Resolve needs is read from
environment variables (see .env.example). No paid services anywhere: the LLM
providers are free tiers, the database is Postgres, and all models run
locally.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


@dataclass
class Settings:
    # Data
    database_url: str = "postgresql+psycopg://resolve:resolve@localhost:5432/resolve"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Retrieval
    chunk_size: int = 800
    chunk_overlap: int = 120
    rerank_enabled: bool = False
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ask_min_cosine: float = 0.20  # evidence gate for /ask (below -> refusal)

    # LLM providers (all free tiers / local)
    llm_provider: str = "gemini"  # gemini | groq | ollama | fake
    llm_fallbacks: str = "groq,ollama"  # comma-separated, tried in order
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # App security / limits
    api_key: str = ""  # RESOLVE_API_KEY; empty = auth disabled (dev mode)
    rate_limit_per_min: int = 120

    # Caching (M5) — /ask answers, exact + semantic; cleared on ingest
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    cache_max_entries: int = 256
    semantic_cache_threshold: float = 0.95

    # Tracing (M5) — Langfuse free tier; off unless both keys are set
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Agent / GitHub
    github_token: str = ""
    github_repo: str = ""  # "owner/repo" the agent files tickets into
    agent_dry_run: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=_env(
                "DATABASE_URL",
                "postgresql+psycopg://resolve:resolve@localhost:5432/resolve",
            ),
            embedding_model=_env(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            embedding_dim=_env_int("EMBEDDING_DIM", 384),
            chunk_size=_env_int("CHUNK_SIZE", 800),
            chunk_overlap=_env_int("CHUNK_OVERLAP", 120),
            rerank_enabled=_env_bool("RERANK_ENABLED", False),
            rerank_model=_env(
                "RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
            ),
            ask_min_cosine=_env_float("ASK_MIN_COSINE", 0.20),
            llm_provider=_env("LLM_PROVIDER", "gemini").lower(),
            llm_fallbacks=_env("LLM_FALLBACKS", "groq,ollama"),
            gemini_api_key=_env("GEMINI_API_KEY"),
            gemini_model=_env("GEMINI_MODEL", "gemini-2.5-flash"),
            groq_api_key=_env("GROQ_API_KEY"),
            groq_model=_env("GROQ_MODEL", "llama-3.3-70b-versatile"),
            ollama_host=_env("OLLAMA_HOST", "http://localhost:11434"),
            ollama_model=_env("OLLAMA_MODEL", "llama3.1:8b"),
            api_key=_env("RESOLVE_API_KEY"),
            rate_limit_per_min=_env_int("RATE_LIMIT_PER_MIN", 120),
            cache_enabled=_env_bool("CACHE_ENABLED", True),
            cache_ttl_seconds=_env_int("CACHE_TTL_SECONDS", 300),
            cache_max_entries=_env_int("CACHE_MAX_ENTRIES", 256),
            semantic_cache_threshold=_env_float(
                "SEMANTIC_CACHE_THRESHOLD", 0.95
            ),
            langfuse_public_key=_env("LANGFUSE_PUBLIC_KEY"),
            langfuse_secret_key=_env("LANGFUSE_SECRET_KEY"),
            langfuse_host=_env("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            github_token=_env("GITHUB_TOKEN"),
            github_repo=_env("GITHUB_REPO"),
            agent_dry_run=_env_bool("AGENT_DRY_RUN", True),
        )
