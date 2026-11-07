"""Layer 4: classification, drafting, and the human approval gate."""
from app.agent.agent import SupportAgent
from app.agent.classify import classify_ticket
from app.agent.github_client import GitHubIssuesClient


def test_classification_categories():
    assert classify_ticket("I forgot my password and I'm locked out")[0] == "account_access"
    assert classify_ticket("I was charged twice on my invoice")[0] == "billing"
    assert classify_ticket("Please refund my annual plan")[0] == "refund"
    assert classify_ticket("Where is my package? Tracking hasn't moved")[0] == "shipping"
    assert classify_ticket("My API key returns 401 errors")[0] == "api_technical"
    assert classify_ticket("How do I delete my account?")[0] == "account_deletion"


def test_classification_priority():
    _, priority = classify_ticket("URGENT: I was charged twice and it looks like fraud")
    assert priority == "high"
    _, priority = classify_ticket("Question about your pricing plans")
    assert priority in {"low", "medium"}


def test_agent_without_approval_takes_no_action(searcher, settings):
    github = GitHubIssuesClient(dry_run=True)
    agent = SupportAgent(searcher=searcher, settings=settings, github=github)
    result = agent.process_ticket(
        title="Can't sign in, forgot my password",
        body="The reset email never arrives.",
        approve=False,
    )
    assert result.status == "awaiting_approval"
    assert result.action is None
    # The gate: nothing was even recorded as an action.
    assert github.recorded_actions == []
    assert result.category == "account_access"
    assert result.draft
    assert "password-reset.md" in result.sources
    assert any("approval gate" in s for s in result.steps)


def test_agent_with_approval_acts_in_dry_run(searcher, settings):
    github = GitHubIssuesClient(token="", repo="", dry_run=True)
    agent = SupportAgent(searcher=searcher, settings=settings, github=github)
    result = agent.process_ticket(
        title="Refund request for my monthly plan",
        body="I bought it 3 days ago and want a refund.",
        approve=True,
    )
    assert result.status == "acted"
    assert result.action is not None
    assert result.action["dry_run"] is True  # recorded, NOT sent to GitHub
    assert len(github.recorded_actions) == 1
    assert github.recorded_actions[0]["type"] == "create_issue"


def test_github_client_stays_dry_run_without_token():
    client = GitHubIssuesClient(token="", repo="", dry_run=False)
    assert client.dry_run is True  # no token+repo -> cannot go live


def test_agent_via_api_requires_no_approval_default(client):
    resp = client.post("/agent/tickets", json={
        "title": "I need to reset my password",
        "body": "Forgot it completely.",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "awaiting_approval"
    assert body["category"] == "account_access"
