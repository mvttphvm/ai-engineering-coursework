"""Provider selection, configuration checks, and fallback behavior."""
import pytest

from app.config import Settings
from app.providers.base import ProviderNotConfigured
from app.providers.factory import generate_with_fallback, get_provider
from app.providers.fake import FakeProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.ollama import OllamaProvider


def test_get_provider_by_name():
    settings = Settings(gemini_api_key="k", groq_api_key="k")
    assert isinstance(get_provider("gemini", settings), GeminiProvider)
    assert isinstance(get_provider("groq", settings), GroqProvider)
    assert isinstance(get_provider("ollama", settings), OllamaProvider)
    assert isinstance(get_provider("fake", settings), FakeProvider)


def test_unknown_provider_rejected():
    with pytest.raises(ValueError):
        get_provider("chatgpt-plus-max", Settings())


def test_unconfigured_gemini_raises_clear_error():
    provider = GeminiProvider(api_key="")
    assert not provider.is_configured()
    with pytest.raises(ProviderNotConfigured) as excinfo:
        provider.generate("hello")
    assert "gemini" in str(excinfo.value).lower()


def test_fallback_skips_unconfigured_primary():
    # gemini selected but no key -> must fall back to fake, not crash.
    settings = Settings(llm_provider="gemini", llm_fallbacks="fake",
                        gemini_api_key="", groq_api_key="")
    text, used = generate_with_fallback(settings, "Say something [1] x\nhello world.")
    assert used == "fake"
    assert text


def test_all_providers_missing_gives_actionable_error():
    settings = Settings(llm_provider="gemini", llm_fallbacks="groq",
                        gemini_api_key="", groq_api_key="")
    with pytest.raises(ProviderNotConfigured) as excinfo:
        generate_with_fallback(settings, "hello")
    message = str(excinfo.value)
    assert "GEMINI_API_KEY" in message and "GROQ_API_KEY" in message


def test_fake_provider_answers_from_first_source():
    provider = FakeProvider()
    prompt = ("Sources:\n[1] Source: a.md — Title\n"
              "The reset link expires after 60 minutes. More text here.\n\n"
              "Question: when does it expire?\n")
    answer = provider.generate(prompt)
    assert "60 minutes" in answer
    assert "[1]" in answer
