"""Ticket classification: deterministic keyword rules.

A rules baseline first, on purpose: it is explainable, testable, costs
$0, and becomes the baseline the eval harness can grade an LLM classifier
against (the spec's stretch goal). Categories mirror the sample KB.
"""
from __future__ import annotations

_RULES: list[tuple[str, list[str]]] = [
    ("account_access", ["password", "sign in", "sign-in", "login", "log in",
                        "locked out", "forgot", "reset password", "2fa",
                        "two-factor", "authentication"]),
    ("billing", ["invoice", "charged", "charge", "payment", "card declined",
                 "billing", "receipt", "tax", "vat", "double charged"]),
    ("refund", ["refund", "money back", "chargeback", "dispute the charge"]),
    ("shipping", ["shipping", "delivery", "tracking", "package", "order",
                  "shipped", "damaged", "carrier"]),
    ("api_technical", ["api", "api key", "401", "429", "error code", "sdk",
                       "integration", "rate limit"]),
    ("outage", ["down", "outage", "not working", "broken", "error 500",
                "unavailable", "status page"]),
    ("account_deletion", ["delete my account", "delete account", "close my account",
                          "remove my data", "gdpr", "export my data"]),
    ("plan_change", ["upgrade", "downgrade", "change plan", "cancel subscription",
                     "cancel my plan", "seats", "pricing"]),
]

_HIGH_PRIORITY = ["charged twice", "double charged", "fraud", "hacked",
                  "compromised", "leaked", "security", "locked out",
                  "major outage", "completely down", "legal"]
_MEDIUM_PRIORITY = ["refund", "damaged", "missing", "declined", "failed",
                    "error", "broken"]


def classify_ticket(title: str, body: str = "") -> tuple[str, str]:
    """Return (category, priority). First matching category rule wins;
    ties are broken by rule order, which encodes support-team priority."""
    text = f"{title}\n{body}".lower()
    category = "general"
    for name, keywords in _RULES:
        if any(k in text for k in keywords):
            category = name
            break
    if any(k in text for k in _HIGH_PRIORITY):
        priority = "high"
    elif category != "general" or any(k in text for k in _MEDIUM_PRIORITY):
        priority = "medium"
    else:
        priority = "low"
    return category, priority
