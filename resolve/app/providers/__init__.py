"""LLM provider abstraction.

One interface (:class:`LLMProvider`), three real adapters — Gemini (Google
AI Studio free tier), Groq (free tier), Ollama (local) — plus a deterministic
fake used by tests and offline demos. Selection is by environment variables
(LLM_PROVIDER, LLM_FALLBACKS). Providers talk to their APIs with plain httpx
REST calls; no vendor SDKs.
"""
from app.providers.base import LLMProvider, ProviderError, ProviderNotConfigured
from app.providers.factory import generate_with_fallback, get_provider

__all__ = [
    "LLMProvider",
    "ProviderError",
    "ProviderNotConfigured",
    "generate_with_fallback",
    "get_provider",
]
