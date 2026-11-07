"""Ollama — runs models locally on your machine. Fully free, no key, offline.

Install from https://ollama.com, then `ollama pull llama3.1:8b`.
Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
"""
from __future__ import annotations

import httpx

from app.providers.base import LLMProvider, ProviderError


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, host: str = "http://localhost:11434",
                 model: str = "llama3.1:8b", timeout: float = 120.0) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_configured(self) -> bool:
        # Configured = host set; reachability is verified per call so a
        # stopped Ollama raises a clear ProviderError, not a crash at import.
        return bool(self.host)

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = httpx.post(
                f"{self.host}/api/chat",
                json={"model": self.model, "messages": messages,
                      "stream": False, "options": {"temperature": 0.2}},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except (httpx.HTTPError, httpx.InvalidURL, ValueError) as exc:
            raise ProviderError(
                f"Ollama request failed ({exc}). Is Ollama running at "
                f"{self.host} with model '{self.model}' pulled?"
            ) from exc
        data = resp.json()
        try:
            return data["message"]["content"].strip()
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"Unexpected Ollama response shape: {data!r}") from exc
