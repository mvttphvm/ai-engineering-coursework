"""Google Gemini via the AI Studio REST API (free tier, no credit card).

Get a free key at https://aistudio.google.com/apikey — no billing required.
Docs: https://ai.google.dev/api/generate-content
"""
from __future__ import annotations

import httpx

from app.providers.base import LLMProvider, ProviderError

_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 timeout: float = 60.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system: str | None = None) -> str:
        self.require_configured()
        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        url = f"{_API_ROOT}/{self.model}:generateContent"
        try:
            resp = httpx.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except (httpx.HTTPError, httpx.InvalidURL, ValueError) as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc
        data = resp.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected Gemini response shape: {data!r}") from exc
