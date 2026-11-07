"""API surface: health, ingest, search, auth."""
from app.config import Settings
from app.main import create_app
from app.retrieval.embeddings import FakeEmbedder
from app.retrieval.store import InMemoryStore


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["chunks"] > 0


def test_search_endpoint(client):
    resp = client.get("/search", params={"q": "how do I change my plan and upgrade"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    assert results[0]["source"] == "plans-and-plan-changes.md"


def test_ingest_inline_documents(client):
    resp = client.post("/ingest", json={"documents": [{
        "source": "vpn-setup.md",
        "title": "VPN setup",
        "text": "To connect to the company VPN, open the VPN client and sign "
                "in with your work account, then approve the push notification.",
    }]})
    assert resp.status_code == 200
    assert resp.json()["documents"] == 1
    found = client.get("/search", params={"q": "company VPN client sign in"})
    assert found.json()["results"][0]["source"] == "vpn-setup.md"


def test_ingest_requires_payload(client):
    resp = client.post("/ingest", json={})
    assert resp.status_code == 422


def test_auth_enforced_when_key_set(settings):
    from fastapi.testclient import TestClient

    settings.api_key = "test-secret"
    app = create_app(settings=settings, store=InMemoryStore(),
                     embedder=FakeEmbedder())
    with TestClient(app) as c:
        assert c.get("/search", params={"q": "x"}).status_code == 401
        ok = c.get("/search", params={"q": "x"},
                   headers={"X-API-Key": "test-secret"})
        assert ok.status_code == 200
        # health stays open for uptime checks
        assert c.get("/health").status_code == 200
