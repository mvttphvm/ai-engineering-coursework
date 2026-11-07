"""Provider interface and error types."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderError(RuntimeError):
    """A provider call failed (network, quota, bad response...)."""


class ProviderNotConfigured(ProviderError):
    """The provider was selected but its credentials/config are missing.

    Raised instead of crashing so callers can surface a clear, actionable
    message (e.g. "set GEMINI_API_KEY") or fall back to another provider.
    """


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """True when this provider can actually be called right now."""

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Return the model's text response. Raises ProviderError on failure."""

    def require_configured(self) -> None:
        if not self.is_configured():
            raise ProviderNotConfigured(
                f"Provider '{self.name}' is not configured. "
                f"See .env.example for the free key / setup for it."
            )
