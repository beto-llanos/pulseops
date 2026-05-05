"""The four detection engines.

Each engine returns a list of ``Finding`` dicts with a uniform shape:
    {
        "engine": "meeting" | "dev_flow" | "saas" | "repetition",
        "title": str,
        "description": str,
        "annual_cost_usd": float,
        "weekly_cost_usd": float,
        "confidence": "high" | "medium" | "low",
        "suggested_fix": str,
        "metadata": dict (engine-specific),
    }
"""
from __future__ import annotations

from typing import Any

from . import claude, mock_data, salary_bands

WEEKS_PER_YEAR = 50  # account for holidays


# --------------------------- Meeting Cost Radar ---------------------------

def run_meeting_radar(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find the most expensive meetings, especially those with no recorded outcome."""
    scored = []
    for m in meetings:
        cost = sum(
            salary_bands.cost_for(a["role"], m["duration_minutes"])
            for a in m["attendees"]
        )
        zero_output = not m["has_action_items"] and not m["has_decisions_recorded"]
        scored.append({**m, "cost": cost, "zero_output": zero_output})

    # Aggregate by title for recurring meetings
    by_title: dict[str, dict[str, Any]] = {}
    for m in scored:
        agg = by_title.setdefault(
            m["title"],
            {
                "title": m["title"],
                "kind": m["kind"],
                "cost_total": 0.0,
                "zero_output_cost": 0.0,
                "occurrences": 0,
                "zero_output_count": 0,
            },
        )
        agg["cost_total"] += m["cost"]
        agg["occurrences"] += 1
        if m["zero_output"]:
            agg["zero_output_cost"] += m["cost"]
            agg["zero_output_count"] += 1

    findings = []
    for agg in by_title.values():
        if agg["zero_output_cost"] < 200:  # skip noise
            continue
        weekly = agg["zero_output_cost"] / 2  # mock_data covers ~2 weeks
        annual = weekly * WEEKS_PER_YEAR
        confidence = "high" if agg["zero_output_count"] >= 3 else "medium"
        suggested = (
            "Mark as async-by-default; require an agenda + action-item template "
            "before next occurrence."
            if agg["kind"] == "recurring"
            else "Convert to an async update or shorten to 15 min with explicit decision-owner."
        )
        findings.append(
            {
                "engine": "meeting",
                "title": f"'{agg['title']}' produces no tracked outcome {agg['zero_output_count']}/{agg['occurrences']} times",
                "description": (
                    f"This {agg['kind']} meeting has cost ${agg['cost_total']:,.0f} "
                    f"in the last 14 days, of which ${agg['zero_output_cost']:,.0f} "
                    f"came from sessions with no action items or decisions recorded."
                ),
                "annual_cost_usd": annual,
                "weekly_cost_usd": weekly,
                "confidence": confidence,
                "suggested_fix": suggested,
                "metadata": agg,
            }
        )
    findings.sort(key=lambda f: f["annual_cost_usd"], reverse=True)
    return findings


def total_meeting_spend(meetings: list[dict[str, Any]]) -> dict[str, float]:
    weekly = 0.0
    for m in meetings:
        weekly += sum(
            salary_bands.cost_for(a["role"], m["duration_minutes"])
            for a in m["attendees"]
        )
    weekly = weekly / 2
    return {"weekly": weekly, "annual": weekly * WEEKS_PER_YEAR}


# --------------------------- Dev Flow Analyzer ---------------------------

def run_dev_flow(prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cost of waiting on PR reviews and abandoned tickets."""
    findings = []
    blocked = [pr for pr in prs if pr["is_blocked"]]
    if blocked:
        # Productivity loss while waiting on review (industry estimates ~15-25%)
        PRODUCTIVITY_LOSS = 0.2
        total_wait_hours = sum(pr["wait_hours"] for pr in blocked)
        cost = sum(
            salary_bands.hourly_cost(pr["author_role"]) * pr["wait_hours"] * PRODUCTIVITY_LOSS
            for pr in blocked
        )
        annual = cost * (WEEKS_PER_YEAR / 2)  # data is 2 weeks
        findings.append(
            {
                "engine": "dev_flow",
                "title": f"{len(blocked)} pull requests blocked over 48h",
                "description": (
                    f"Across {len(blocked)} PRs, engineers waited a combined "
                    f"{total_wait_hours} hours for review. Authors typically context-switch "
                    f"to other work while waiting, recovering only ~50% productivity."
                ),
                "annual_cost_usd": annual,
                "weekly_cost_usd": cost / 2,
                "confidence": "high",
                "suggested_fix": "Set a 24h SLA on first review; auto-page a backup reviewer if breached.",
                "metadata": {"blocked_prs": blocked},
            }
        )

    # Slow-review pattern: anyone with median wait > 36h and >= 2 PRs
    by_author: dict[str, list[float]] = {}
    for pr in prs:
        by_author.setdefault(pr["author"], []).append(pr["first_review_hours"])
    slow = []
    for author, hours in by_author.items():
        if len(hours) >= 2 and sorted(hours)[len(hours) // 2] > 36:
            slow.append((author, sorted(hours)[len(hours) // 2], len(hours)))
    if slow:
        slow.sort(key=lambda t: -t[1])
        top = slow[0]
        # rough cost: median wait hours * pr count * senior eng rate * 20% productivity loss
        est = top[1] * top[2] * salary_bands.hourly_cost("senior_engineer") * 0.2
        annual = est * (WEEKS_PER_YEAR / 2)
        findings.append(
            {
                "engine": "dev_flow",
                "title": f"{top[0]}'s PRs wait {int(top[1])}h on average for first review",
                "description": (
                    f"{top[0]} opened {top[2]} PRs in the last 14 days, with a median "
                    f"of {int(top[1])}h until first review."
                ),
                "annual_cost_usd": annual,
                "weekly_cost_usd": est / 2,
                "confidence": "medium",
                "suggested_fix": "Rebalance reviewer load; consider a dedicated reviewer rotation.",
                "metadata": {"author": top[0], "median_hours": top[1], "pr_count": top[2]},
            }
        )

    findings.sort(key=lambda f: f["annual_cost_usd"], reverse=True)
    return findings


# --------------------------- SaaS Utilization Audit ---------------------------

def run_saas_audit(saas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Surface tools with low utilization and obvious overlaps."""
    findings = []

    # Per-tool unused seats
    for tool in saas:
        if tool["unused_seats"] >= 3 and tool["annual_waste"] >= 500:
            confidence = "high" if tool["active_pct"] < 0.3 else "medium"
            findings.append(
                {
                    "engine": "saas",
                    "title": f"{tool['unused_seats']} unused seats on {tool['tool']}",
                    "description": (
                        f"{tool['tool']} ({tool['category']}) has {tool['total_seats']} seats "
                        f"provisioned, but only {tool['active_seats']} have logged in this month. "
                        f"That's ${tool['monthly_waste']:,.0f}/mo of unused capacity."
                    ),
                    "annual_cost_usd": tool["annual_waste"],
                    "weekly_cost_usd": tool["annual_waste"] / WEEKS_PER_YEAR,
                    "confidence": confidence,
                    "suggested_fix": f"Reclaim {tool['unused_seats']} seats at next renewal; switch dormant users to viewer-only.",
                    "metadata": tool,
                }
            )

    # Detect overlapping categories where the smaller tool is underused
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for tool in saas:
        by_cat.setdefault(tool["category"], []).append(tool)
    for category, tools in by_cat.items():
        if len(tools) < 2:
            continue
        tools_sorted = sorted(tools, key=lambda t: -t["active_seats"])
        primary, *others = tools_sorted
        for other in others:
            if other["active_pct"] < 0.25:
                annual = other["annual_waste"] + (other["active_seats"] * other["monthly_cost_per_seat"] * 12) * 0.6
                findings.append(
                    {
                        "engine": "saas",
                        "title": f"{other['tool']} duplicates {primary['tool']} in {category}",
                        "description": (
                            f"{other['tool']} has {other['active_seats']} active users "
                            f"({int(other['active_pct'] * 100)}% utilization) while "
                            f"{primary['tool']} covers the same category at "
                            f"{int(primary['active_pct'] * 100)}% utilization."
                        ),
                        "annual_cost_usd": annual,
                        "weekly_cost_usd": annual / WEEKS_PER_YEAR,
                        "confidence": "medium",
                        "suggested_fix": f"Sunset {other['tool']}; migrate the {other['active_seats']} active users to {primary['tool']}.",
                        "metadata": {"primary": primary, "redundant": other},
                    }
                )
    findings.sort(key=lambda f: f["annual_cost_usd"], reverse=True)
    return findings


# --------------------------- Repetition Detector ---------------------------

def run_repetition(workflows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score manual workflows for automation potential and translate to dollar cost."""
    if not workflows:
        return []
    descriptions = [w["title"] for w in workflows]
    scores = claude.score_repetition(descriptions)

    findings = []
    for w, s in zip(workflows, scores):
        annual_minutes = w["occurrences_per_month"] * w["minutes_per_run"] * 12
        annual_cost = salary_bands.cost_for(w["owner_role"], annual_minutes)
        if s["automation_score"] < 50:
            continue
        confidence = "high" if s["automation_score"] >= 75 else "medium"
        findings.append(
            {
                "engine": "repetition",
                "title": w["title"],
                "description": (
                    f"Performed {w['occurrences_per_month']}x/month, {w['minutes_per_run']} min/run, "
                    f"by {w['owner_role'].replace('_', ' ')}. "
                    f"Claude automation score: {s['automation_score']}/100. {s.get('reason', '')}"
                ),
                "annual_cost_usd": annual_cost,
                "weekly_cost_usd": annual_cost / WEEKS_PER_YEAR,
                "confidence": confidence,
                "suggested_fix": s.get("suggested_fix", "Automate via scheduled script."),
                "metadata": {"automation_score": s["automation_score"], **w},
            }
        )
    findings.sort(key=lambda f: f["annual_cost_usd"], reverse=True)
    return findings


# --------------------------- Aggregate ---------------------------

def run_all() -> dict[str, Any]:
    meetings = mock_data.generate_meetings()
    prs = mock_data.generate_prs()
    saas = mock_data.generate_saas()
    workflows = mock_data.generate_repetitive_workflows()

    findings = (
        run_meeting_radar(meetings)
        + run_dev_flow(prs)
        + run_saas_audit(saas)
        + run_repetition(workflows)
    )
    findings.sort(key=lambda f: f["annual_cost_usd"], reverse=True)
    return {
        "findings": findings,
        "meetings": meetings,
        "prs": prs,
        "saas": saas,
        "workflows": workflows,
        "totals": {
            "annual_recoverable": sum(f["annual_cost_usd"] for f in findings),
            "meeting_total_annual": total_meeting_spend(meetings)["annual"],
        },
    }
