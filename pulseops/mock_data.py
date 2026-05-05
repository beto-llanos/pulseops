"""Realistic synthetic data for the demo. Numbers are tuned so the Top 5 Money
Drains feel plausible for a 60-person Series B startup.

Determinism: a fixed seed plus a stable "today" anchor make the dashboard look
the same every time the demo is loaded.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

SEED = 42
COMPANY_SIZE = 60
COMPANY_NAME = "Northwind Robotics"
TODAY = datetime(2026, 5, 5, 9, 0, 0)


def _rng() -> random.Random:
    return random.Random(SEED)


@dataclass
class Person:
    name: str
    role: str
    email: str


PEOPLE: list[Person] = [
    Person("Ana Reyes", "engineering_manager", "ana.reyes@northwind.example"),
    Person("Diego Park", "senior_engineer", "diego.park@northwind.example"),
    Person("Mira Okafor", "senior_engineer", "mira.okafor@northwind.example"),
    Person("Tom Chen", "engineer", "tom.chen@northwind.example"),
    Person("Priya Shah", "engineer", "priya.shah@northwind.example"),
    Person("Lukas Berg", "engineer", "lukas.berg@northwind.example"),
    Person("Sara Liang", "junior_engineer", "sara.liang@northwind.example"),
    Person("Marcus Hall", "staff_engineer", "marcus.hall@northwind.example"),
    Person("Jin Watanabe", "designer", "jin.watanabe@northwind.example"),
    Person("Elena Rossi", "product_manager", "elena.rossi@northwind.example"),
    Person("Sam Patel", "senior_product_manager", "sam.patel@northwind.example"),
    Person("Noor Hassan", "data_scientist", "noor.hassan@northwind.example"),
    Person("Carla Mendes", "director", "carla.mendes@northwind.example"),
    Person("Owen Schultz", "vp", "owen.schultz@northwind.example"),
    Person("Riley Tran", "support", "riley.tran@northwind.example"),
    Person("Ben Kowalski", "operations", "ben.kowalski@northwind.example"),
]


# ----------------------------- Meetings -----------------------------

MEETING_TEMPLATES = [
    ("Weekly all-hands", 60, 28, "recurring"),
    ("Engineering standup", 30, 9, "recurring"),
    ("Product sync", 60, 7, "recurring"),
    ("Roadmap review", 90, 11, "recurring"),
    ("Design critique", 45, 6, "recurring"),
    ("1:1 Ana / Diego", 30, 2, "one_off"),
    ("1:1 Ana / Mira", 30, 2, "one_off"),
    ("Q3 planning offsite prep", 120, 14, "one_off"),
    ("Customer escalation: Acme", 60, 8, "one_off"),
    ("Vendor demo: Datadog", 45, 5, "one_off"),
    ("Hiring loop debrief", 60, 6, "one_off"),
    ("Architecture review", 90, 10, "recurring"),
    ("Marketing campaign sync", 45, 5, "recurring"),
    ("Friday wins", 30, 16, "recurring"),
]


def generate_meetings() -> list[dict[str, Any]]:
    rng = _rng()
    meetings: list[dict[str, Any]] = []
    for day_offset in range(0, 14):
        day = TODAY - timedelta(days=day_offset)
        if day.weekday() >= 5:
            continue
        rng.shuffle(MEETING_TEMPLATES)
        n_today = rng.randint(4, 8)
        for i in range(n_today):
            tpl = MEETING_TEMPLATES[i % len(MEETING_TEMPLATES)]
            title, duration, n_attendees, kind = tpl
            attendees = rng.sample(PEOPLE, min(n_attendees, len(PEOPLE)))
            start_hour = rng.choice([9, 10, 11, 13, 14, 15, 16])
            start = day.replace(hour=start_hour, minute=rng.choice([0, 15, 30]))
            has_action_items = rng.random() > 0.45  # 55% of meetings produce nothing tracked
            meetings.append(
                {
                    "id": f"m{day_offset:02d}{i:02d}",
                    "title": title,
                    "start": start.isoformat(),
                    "duration_minutes": duration,
                    "attendees": [
                        {"name": p.name, "role": p.role, "email": p.email}
                        for p in attendees
                    ],
                    "kind": kind,
                    "has_action_items": has_action_items,
                    "has_decisions_recorded": has_action_items and rng.random() > 0.3,
                }
            )
    return meetings


# ----------------------------- Pull requests -----------------------------

PR_TITLES = [
    "Add retry logic to payment webhook",
    "Refactor billing service for multi-currency",
    "Fix race condition in order fulfillment queue",
    "Migrate user auth to OAuth2 PKCE flow",
    "Drop legacy v1 inventory API",
    "Bump pandas to 2.2",
    "Add idempotency keys to checkout endpoint",
    "Cache product catalog in Redis",
    "Switch logging to structured JSON",
    "Reduce cold-start latency in fulfillment lambda",
    "Backfill missing customer_segment on orders table",
    "Add feature flag for new pricing engine",
    "Rate-limit forgot-password endpoint",
    "Trace context propagation across services",
    "Replace cron with EventBridge scheduler",
]


def generate_prs() -> list[dict[str, Any]]:
    rng = _rng()
    engineers = [p for p in PEOPLE if "engineer" in p.role]
    prs: list[dict[str, Any]] = []
    for i, title in enumerate(PR_TITLES):
        author = rng.choice(engineers)
        opened = TODAY - timedelta(days=rng.randint(1, 18), hours=rng.randint(0, 23))
        first_review_hours = rng.choice([2, 4, 8, 18, 36, 60, 96, 120])
        merged = rng.random() > 0.3
        merged_at = opened + timedelta(hours=first_review_hours + rng.randint(2, 24)) if merged else None
        wait_hours = first_review_hours
        prs.append(
            {
                "number": 1840 + i,
                "title": title,
                "author": author.name,
                "author_role": author.role,
                "opened_at": opened.isoformat(),
                "merged_at": merged_at.isoformat() if merged_at else None,
                "first_review_hours": first_review_hours,
                "wait_hours": wait_hours,
                "is_blocked": (not merged) and first_review_hours > 48,
                "url": f"https://github.com/northwind/monolith/pull/{1840 + i}",
            }
        )
    return prs


# ----------------------------- SaaS billing -----------------------------

SAAS_TOOLS = [
    # (name, monthly_per_seat, total_seats, active_seats_pct, category)
    ("Figma", 15, 24, 0.42, "Design"),
    ("Sketch", 9, 18, 0.11, "Design"),
    ("Notion", 10, 60, 0.81, "Docs"),
    ("Confluence", 6, 60, 0.27, "Docs"),
    ("Datadog", 31, 22, 0.95, "Observability"),
    ("New Relic", 28, 14, 0.21, "Observability"),
    ("Linear", 8, 38, 0.92, "Project tracking"),
    ("Jira", 7, 60, 0.45, "Project tracking"),
    ("Loom", 12, 30, 0.36, "Comms"),
    ("Zoom", 18, 60, 0.83, "Comms"),
    ("Slack", 12, 65, 0.95, "Comms"),
    ("Mixpanel", 25, 12, 0.58, "Analytics"),
    ("Amplitude", 30, 8, 0.12, "Analytics"),
    ("Pendo", 20, 6, 0.16, "Analytics"),
    ("PagerDuty", 21, 14, 0.78, "Ops"),
    ("Intercom", 39, 10, 0.62, "Support"),
]


def generate_saas() -> list[dict[str, Any]]:
    out = []
    for name, per_seat, total, active_pct, category in SAAS_TOOLS:
        active = int(total * active_pct)
        unused = total - active
        monthly_waste = unused * per_seat
        out.append(
            {
                "tool": name,
                "category": category,
                "monthly_cost_per_seat": per_seat,
                "total_seats": total,
                "active_seats": active,
                "unused_seats": unused,
                "monthly_waste": monthly_waste,
                "annual_waste": monthly_waste * 12,
                "active_pct": active_pct,
            }
        )
    return out


# ----------------------------- Tickets / Repetition -----------------------------

REPETITIVE_WORKFLOWS = [
    {
        "title": "Manual export of weekly support metrics from Intercom into Google Sheets",
        "occurrences_per_month": 4,
        "minutes_per_run": 65,
        "owner_role": "support",
    },
    {
        "title": "Copy-paste closed-won deals from HubSpot into onboarding tracker",
        "occurrences_per_month": 18,
        "minutes_per_run": 12,
        "owner_role": "operations",
    },
    {
        "title": "Generate monthly invoice from Stripe + reconcile with Xero",
        "occurrences_per_month": 1,
        "minutes_per_run": 240,
        "owner_role": "operations",
    },
    {
        "title": "Manually backfill product_segment column after each launch",
        "occurrences_per_month": 6,
        "minutes_per_run": 35,
        "owner_role": "data_scientist",
    },
    {
        "title": "Forward GitHub deploy notifications to #releases Slack manually",
        "occurrences_per_month": 22,
        "minutes_per_run": 4,
        "owner_role": "engineer",
    },
    {
        "title": "Run weekly NPS survey, paste responses into the QBR deck",
        "occurrences_per_month": 4,
        "minutes_per_run": 90,
        "owner_role": "product_manager",
    },
    {
        "title": "Review Datadog cost report, screenshot to leadership",
        "occurrences_per_month": 2,
        "minutes_per_run": 25,
        "owner_role": "engineering_manager",
    },
]


def generate_repetitive_workflows() -> list[dict[str, Any]]:
    return list(REPETITIVE_WORKFLOWS)
