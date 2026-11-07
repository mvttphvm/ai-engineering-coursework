"""Provider selection by name + ordered fallback generation."""
from __future__ import annotations

from app.config import Settings
from app.logging_config import get_logger
from app.providers.base import LLMProvider, ProviderError, ProviderNotConfigured
from app.providers.fake import FakeProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.ollama import OllamaProvider

log = get_logger(__name__)


def get_provider(name: str, settings: Settings) -> LLMProvider:
    """Build the provider adapter for `name`. Unknown names raise ValueError."""
    key = name.strip().lower()
    if key == "gemini":
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    if key == "groq":
        return GroqProvider(settings.groq_api_key, settings.groq_model)
    if key == "ollama":
        return OllamaProvider(settings.ollama_host, settings.ollama_model)
    if key == "fake":
        return FakeProvider()
    raise ValueError(
        f"Unknown LLM provider '{name}'. Valid: gemini, groq, ollama, fake."
    )


def provider_chain(settings: Settings) -> list[LLMProvider]:
    """Primary provider followed by the configured fallbacks, de-duplicated."""
    names = [settings.llm_provider]
    names += [n for n in settings.llm_fallbacks.split(",") if n.strip()]
    chain: list[LLMProvider] = []
    seen: set[str] = set()
    for name in names:
        provider = get_provider(name, settings)
        if provider.name not in seen:
            seen.add(provider.name)
            chain.append(provider)
    return chain


def generate_with_fallback(settings: Settings, prompt: str,
                           system: str | None = None) -> tuple[str, str]:
    """Try each provider in the chain; return (text, provider_name).

    Unconfigured providers are skipped with a clear log line. If every
    provider fails, raise ProviderNotConfigured/ProviderError explaining
    exactly what to set — never an unhandled crash.
    """
    errors: list[str] = []
    for provider in provider_chain(settings):
        if not provider.is_configured():
            msg = f"{provider.name}: not configured (missing key/config)"
            log.warning("provider skipped: %s", msg)
            errors.append(msg)
            continue
        try:
            return provider.generate(prompt, system=system), provider.name
        except ProviderError as exc:
            log.warning("provider %s failed: %s", provider.name, exc)
            errors.append(f"{provider.name}: {exc}")
        except Exception as exc:  # a provider bug must degrade, never crash
            log.warning("provider %s raised unexpectedly: %r", provider.name, exc)
            errors.append(f"{provider.name}: unexpected error: {exc}")
    raise ProviderNotConfigured(
        "No LLM provider is available. Tried: " + "; ".join(errors) +
        ". Set GEMINI_API_KEY or GROQ_API_KEY (both free, no credit card) "
        "or run Ollama locally — see .env.example."
    )
