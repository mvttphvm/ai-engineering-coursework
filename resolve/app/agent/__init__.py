"""Layer 4 — support-ops agent: classify, retrieve, draft, (approved) act."""
from app.agent.agent import AgentResult, SupportAgent
from app.agent.classify import classify_ticket
from app.agent.github_client import GitHubIssuesClient

__all__ = ["AgentResult", "SupportAgent", "classify_ticket", "GitHubIssuesClient"]
