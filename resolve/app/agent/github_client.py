"""GitHub Issues client — the agent's hands.

Safety defaults, on purpose:
- **Dry-run by default**: actions are recorded and returned, never sent.
- Even with dry-run off, a real call requires GITHUB_TOKEN and a
  GITHUB_REPO ("owner/repo"); without them it stays in dry-run.
"""
from __future__ import annotations

import httpx

from app.logging_config import get_logger

log = get_logger(__name__)

_API = "https://api.github.com"


class GitHubIssuesClient:
    def __init__(self, token: str = "", repo: str = "",
                 dry_run: bool = True, timeout: float = 30.0) -> None:
        self.token = token
        self.repo = repo
        # Dry-run is sticky: it can only be off when a token AND repo exist.
        self.dry_run = dry_run or not (token and repo)
        self.timeout = timeout
        self.recorded_actions: list[dict] = []  # everything it *would* do

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_issue(self, title: str, body: str,
                     labels: list[str] | None = None) -> dict:
        action = {"type": "create_issue", "repo": self.repo,
                  "title": title, "body": body, "labels": labels or []}
        self.recorded_actions.append(action)
        if self.dry_run:
            log.info("DRY-RUN would create GitHub issue: %s", title)
            return {"dry_run": True, "action": action}
        resp = httpx.post(f"{_API}/repos/{self.repo}/issues",
                          headers=self._headers(),
                          json={"title": title, "body": body,
                                "labels": labels or []},
                          timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return {"dry_run": False, "number": data["number"], "url": data["html_url"]}

    def post_comment(self, issue_number: int, body: str) -> dict:
        action = {"type": "post_comment", "repo": self.repo,
                  "issue_number": issue_number, "body": body}
        self.recorded_actions.append(action)
        if self.dry_run:
            log.info("DRY-RUN would comment on issue #%s", issue_number)
            return {"dry_run": True, "action": action}
        resp = httpx.post(
            f"{_API}/repos/{self.repo}/issues/{issue_number}/comments",
            headers=self._headers(), json={"body": body},
            timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return {"dry_run": False, "id": data["id"], "url": data["html_url"]}
