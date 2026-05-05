"""Thin Claude API wrapper with daily token budget enforcement and graceful fallback."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from .config import SETTINGS

log = logging.getLogger(__name__)

DAILY_TOKEN_BUDGET = 50_000
MODEL = "claude-sonnet-4-6"


@dataclass
class Budget:
    day: date
    tokens_used: int = 0

    def reset_if_new_day(self) -> None:
        today = date.today()
        if today != self.day:
            self.day = today
            self.tokens_used = 0

    def can_afford(self, estimate: int) -> bool:
        self.reset_if_new_day()
        return self.tokens_used + estimate <= DAILY_TOKEN_BUDGET

    def charge(self, used: int) -> None:
        self.tokens_used += used


_budget = Budget(day=date.today())


def _client():
    if not SETTINGS.has_claude:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=SETTINGS.anthropic_api_key)
    except Exception as exc:
        log.warning("anthropic SDK init failed: %s", exc)
        return None


def score_repetition(workflow_descriptions: list[str]) -> list[dict[str, Any]]:
    """Score a batch of workflow descriptions for automation potential.

    Returns one dict per input: {automation_score: 0-100, reason: str, suggested_fix: str}.
    Falls back to a heuristic if Claude is unavailable or budget is exhausted.
    """
    if not workflow_descriptions:
        return []

    client = _client()
    estimate = 200 * len(workflow_descriptions)
    if client is None or not _budget.can_afford(estimate):
        return [_heuristic_score(d) for d in workflow_descriptions]

    prompt = _build_prompt(workflow_descriptions)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        _budget.charge(msg.usage.input_tokens + msg.usage.output_tokens)
        text = msg.content[0].text if msg.content else "[]"
        # Be tolerant of code fences or extra prose
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        return json.loads(text)
    except Exception as exc:
        log.warning("Claude scoring failed, falling back: %s", exc)
        return [_heuristic_score(d) for d in workflow_descriptions]


def _build_prompt(workflows: list[str]) -> str:
    items = "\n".join(f"{i + 1}. {w}" for i, w in enumerate(workflows))
    return (
        "You are an operations efficiency analyst. For each workflow below, "
        "score its automation potential 0-100 (higher = better candidate to automate). "
        "Reply with ONLY a JSON array of objects with keys "
        "automation_score, reason, suggested_fix. No prose outside the JSON.\n\n"
        f"Workflows:\n{items}"
    )


def _heuristic_score(description: str) -> dict[str, Any]:
    text = description.lower()
    score = 40
    repetition_hints = ["every", "weekly", "daily", "manual", "copy", "paste", "again"]
    score += 10 * sum(1 for h in repetition_hints if h in text)
    score = min(score, 95)
    return {
        "automation_score": score,
        "reason": "Heuristic: contains repetition signals" if score > 50 else "Heuristic: weak signal",
        "suggested_fix": "Wrap as a scheduled script or webhook-triggered automation.",
    }
