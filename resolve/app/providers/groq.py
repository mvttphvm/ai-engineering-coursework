"""Groq via its OpenAI-compatible REST API (free tier, no credit card).

Get a free key at https://console.groq.com/keys — no billing required.
Docs: https://console.groq.com/docs/api-reference
"""
from __future__ import annotations

import httpx

from app.providers.base import LLMProvider, ProviderError

_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile",
                 timeout: float = 60.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system: str | None = None) -> str:
        self.require_configured()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = httpx.post(
                _API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages,
                      "temperature": 0.2},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except (httpx.HTTPError, httpx.InvalidURL, ValueError) as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected Groq response shape: {data!r}") from exc
