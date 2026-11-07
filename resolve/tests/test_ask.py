"""Layer 2: citation-first answers and evidence-based refusal."""
from app import rag
from app.config import Settings


def test_ask_answers_with_citations(searcher, settings):
    response = rag.ask("How do I reset my password?", searcher, settings)
    assert not response.refused
    assert response.answer
    assert response.citations, "every non-refused answer must cite sources"
    assert response.citations[0].source == "password-reset.md"
    assert "[1]" in response.answer


def test_ask_refuses_without_evidence(searcher, settings):
    response = rag.ask("What is the airspeed velocity of an unladen swallow?",
                       searcher, settings)
    assert response.refused
    assert response.citations == []
    assert "don't have enough information" in response.answer


def test_ask_via_api(client):
    resp = client.post("/ask", json={"question": "How do refunds work?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["refused"] is False
    assert body["provider"] == "fake"
    assert body["citations"][0]["source"] == "refunds.md"


def test_ask_refusal_via_api(client):
    resp = client.post("/ask", json={"question": "zanzibar quantum banana"})
    assert resp.status_code == 200
    assert resp.json()["refused"] is True


def test_ask_without_provider_gives_clear_error(searcher):
    import pytest

    from app.providers.base import ProviderNotConfigured

    settings = Settings(llm_provider="gemini", llm_fallbacks="",
                        gemini_api_key="", groq_api_key="")
    # Retrieval succeeds, but no LLM is configured: a clear, actionable
    # ProviderNotConfigured must surface — not a crash.
    with pytest.raises(ProviderNotConfigured) as excinfo:
        rag.ask("How do I reset my password?", searcher, settings)
    assert "GEMINI_API_KEY" in str(excinfo.value)
