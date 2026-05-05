"""Telegram digest sender. Splits messages above the 4096 char limit."""
from __future__ import annotations

import logging
from typing import Iterable

import requests

from .config import SETTINGS

log = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4000


def send_digest(text: str) -> bool:
    if not SETTINGS.has_telegram:
        log.info("Telegram not configured; would have sent %d chars", len(text))
        return False
    url = API.format(token=SETTINGS.telegram_bot_token)
    for chunk in _chunks(text):
        r = requests.post(
            url,
            json={
                "chat_id": SETTINGS.telegram_chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if r.status_code != 200:
            log.warning("Telegram send failed: %s %s", r.status_code, r.text)
            return False
    return True


def _chunks(text: str) -> Iterable[str]:
    while text:
        if len(text) <= MAX_LEN:
            yield text
            return
        cut = text.rfind("\n", 0, MAX_LEN)
        if cut == -1:
            cut = MAX_LEN
        yield text[:cut]
        text = text[cut:].lstrip()


def format_digest(findings: list[dict]) -> str:
    if not findings:
        return "*PulseOps weekly digest*\n\nNo material inefficiencies detected this week. Good week."
    lines = ["*PulseOps weekly digest*", ""]
    total_annual = sum(f.get("annual_cost_usd", 0) for f in findings)
    lines.append(f"Total recoverable annual spend detected: *${total_annual:,.0f}*")
    lines.append("")
    lines.append("*Top findings:*")
    for i, f in enumerate(findings[:10], 1):
        lines.append(
            f"{i}. *{f['title']}* — ${f['annual_cost_usd']:,.0f}/yr\n"
            f"   _{f.get('description', '')}_\n"
            f"   Fix: {f.get('suggested_fix', '')}"
        )
    return "\n".join(lines)
