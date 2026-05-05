"""Centralized configuration loader."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    mode: str
    currency: str
    anthropic_api_key: str
    github_token: str
    github_org: str
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    telegram_bot_token: str
    telegram_chat_id: str

    @property
    def is_demo(self) -> bool:
        return self.mode.lower() == "demo"

    @property
    def has_claude(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_github(self) -> bool:
        return bool(self.github_token and self.github_org)

    @property
    def has_telegram(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def _env(key: str, default: str = "") -> str:
    value = os.getenv(key, default)
    return value.strip() if value else default


def load_settings() -> Settings:
    return Settings(
        mode=_env("PULSEOPS_MODE", "demo"),
        currency=_env("PULSEOPS_CURRENCY", "USD"),
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        github_token=_env("GITHUB_TOKEN"),
        github_org=_env("GITHUB_ORG"),
        google_client_id=_env("GOOGLE_CLIENT_ID"),
        google_client_secret=_env("GOOGLE_CLIENT_SECRET"),
        google_refresh_token=_env("GOOGLE_REFRESH_TOKEN"),
        jira_base_url=_env("JIRA_BASE_URL"),
        jira_email=_env("JIRA_EMAIL"),
        jira_api_token=_env("JIRA_API_TOKEN"),
        telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
    )


SETTINGS = load_settings()
