"""Read-only connectors for external systems.

Each connector exposes the same shape: a ``fetch()`` method returning a list of
normalized dicts. In demo mode, the engines bypass connectors and use mock data.
The connector code below is production-real; it's just gated by credentials.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .config import SETTINGS

log = logging.getLogger(__name__)


class GoogleCalendarConnector:
    """Pulls events from the primary calendar for the past N days."""

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self, days: int = 14):
        self.days = days

    def available(self) -> bool:
        return bool(
            SETTINGS.google_client_id
            and SETTINGS.google_client_secret
            and SETTINGS.google_refresh_token
        )

    def fetch(self) -> list[dict[str, Any]]:
        if not self.available():
            return []
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials(
                token=None,
                refresh_token=SETTINGS.google_refresh_token,
                client_id=SETTINGS.google_client_id,
                client_secret=SETTINGS.google_client_secret,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=self.SCOPES,
            )
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)

            time_min = (datetime.now(timezone.utc) - timedelta(days=self.days)).isoformat()
            events = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=250,
                )
                .execute()
                .get("items", [])
            )

            normalized = []
            for ev in events:
                start = ev.get("start", {}).get("dateTime")
                end = ev.get("end", {}).get("dateTime")
                if not start or not end:
                    continue
                normalized.append(
                    {
                        "title": ev.get("summary", "(no title)"),
                        "start": start,
                        "end": end,
                        "attendees": [
                            a.get("email", "") for a in ev.get("attendees", [])
                        ],
                        "description": ev.get("description", ""),
                    }
                )
            return normalized
        except Exception as exc:
            log.warning("GoogleCalendarConnector.fetch failed: %s", exc)
            return []


class GitHubConnector:
    """Pulls recent PRs across the configured org."""

    def __init__(self, days: int = 14):
        self.days = days

    def available(self) -> bool:
        return SETTINGS.has_github

    def fetch(self) -> list[dict[str, Any]]:
        if not self.available():
            return []
        try:
            from github import Github

            gh = Github(SETTINGS.github_token, per_page=100)
            org = gh.get_organization(SETTINGS.github_org)
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.days)

            prs = []
            for repo in list(org.get_repos())[:25]:
                for pr in repo.get_pulls(state="all", sort="updated", direction="desc"):
                    if pr.updated_at < cutoff.replace(tzinfo=None):
                        break
                    prs.append(
                        {
                            "repo": repo.name,
                            "number": pr.number,
                            "title": pr.title,
                            "author": pr.user.login if pr.user else "",
                            "created_at": pr.created_at.isoformat(),
                            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                            "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                            "state": pr.state,
                            "draft": pr.draft,
                            "url": pr.html_url,
                            "review_count": pr.get_reviews().totalCount,
                        }
                    )
            return prs
        except Exception as exc:
            log.warning("GitHubConnector.fetch failed: %s", exc)
            return []


class JiraConnector:
    """Pulls recently updated issues."""

    def __init__(self, days: int = 30):
        self.days = days

    def available(self) -> bool:
        return bool(SETTINGS.jira_base_url and SETTINGS.jira_email and SETTINGS.jira_api_token)

    def fetch(self) -> list[dict[str, Any]]:
        if not self.available():
            return []
        try:
            jql = f"updated >= -{self.days}d ORDER BY updated DESC"
            r = requests.get(
                f"{SETTINGS.jira_base_url}/rest/api/3/search",
                params={"jql": jql, "maxResults": 100},
                auth=(SETTINGS.jira_email, SETTINGS.jira_api_token),
                timeout=15,
            )
            r.raise_for_status()
            issues = r.json().get("issues", [])
            return [
                {
                    "key": it["key"],
                    "summary": it["fields"].get("summary", ""),
                    "status": it["fields"].get("status", {}).get("name", ""),
                    "assignee": (it["fields"].get("assignee") or {}).get("displayName", ""),
                    "created": it["fields"].get("created", ""),
                    "updated": it["fields"].get("updated", ""),
                }
                for it in issues
            ]
        except Exception as exc:
            log.warning("JiraConnector.fetch failed: %s", exc)
            return []
