"""Architecture & how it works - included so judges who skim Devpost see the system at a glance."""
from __future__ import annotations

import streamlit as st

from pulseops.config import SETTINGS

st.set_page_config(page_title="Architecture", page_icon="🏗️", layout="wide")

st.title("How PulseOps works")
st.caption("Architecture, integrations, and the path from hackathon prototype to production.")

st.markdown(
    """
## Pipeline

```
        ┌─────────────────────────────────────────┐
        │   Connectors (read-only OAuth)          │
        │   Google Calendar | GitHub | Jira | ... │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │   4 Detection Engines (independent)     │
        │   Meeting | DevFlow | SaaS | Repetition │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │   Intelligence Layer                    │
        │   Claude API (tiered, budget-capped)    │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │   Findings DB (SQLite / Postgres)       │
        └─────────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Streamlit dashboard     Telegram digest
```

## Why this design wins

**Modular by construction.** Each detection engine is an independent function with the same output shape. Adding Slack, GitLab, AWS billing, or Notion is one connector + one engine — no rewiring.

**LLM as analytical layer, not chat.** Claude scores repetition candidates and explains anomalies in natural language. There is no chat surface — the user reads ranked findings, not a conversation.

**Money is the universal sort key.** Every finding includes an annual dollar cost. Engineering, finance, and leadership all read the same dashboard.

**Demo-mode by default.** The app boots with realistic synthetic data so judges (or any prospect) can experience the product in 5 seconds without OAuth flows.

## Connectors

| Source         | Mode                | Status     |
| -------------- | ------------------- | ---------- |
| Google Calendar | OAuth refresh token | Implemented in `pulseops.connectors.GoogleCalendarConnector` |
| GitHub         | Personal access token | Implemented in `pulseops.connectors.GitHubConnector` |
| Jira Cloud     | Email + API token   | Implemented in `pulseops.connectors.JiraConnector` |
| Slack          | Bot token           | Roadmap |
| AWS Billing    | Cost Explorer API   | Roadmap |
| Stripe         | Restricted key      | Roadmap |

## Cost model

All dollar figures use a configurable salary band table (`pulseops/salary_bands.py`) with public-market defaults (Levels.fyi, BLS) and a 1.3x burden multiplier (industry standard for benefits + taxes + overhead). Companies override the bands at deployment time with their own data.

## LLM budget

The Claude integration enforces a daily token budget (default 50k). When exceeded or the API key is absent, the system falls back to keyword heuristics so the dashboard never breaks on LLM failures.
"""
)

st.divider()

st.markdown("### Current configuration")
st.json(
    {
        "mode": SETTINGS.mode,
        "claude_connected": SETTINGS.has_claude,
        "github_connected": SETTINGS.has_github,
        "telegram_connected": SETTINGS.has_telegram,
        "currency": SETTINGS.currency,
    }
)
