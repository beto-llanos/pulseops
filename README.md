# PulseOps

> Real-time operational intelligence that finds where your company is bleeding money — before month-end.

PulseOps connects (read-only) to the tools your company already uses (Google Calendar, GitHub, Jira, SaaS billing) and continuously calculates the dollar cost of detected inefficiencies. The output is a live dashboard ranking your **Top 5 Money Drains This Week** with a specific fix for each.

## Live demo

- **Dashboard:** _add your Streamlit Cloud URL after deploy_
- **Video walkthrough (3 min):** _add your YouTube link_

## How it works

PulseOps runs four detection engines in parallel:

| Engine | What it detects | How it monetizes |
|---|---|---|
| Meeting Cost Radar | Low-output meetings | attendees x salary x duration |
| Dev Flow Analyzer | Blocked PRs, abandoned tickets, context switching | engineer salary x wait time |
| SaaS Utilization Audit | Unused licenses, redundant tools | seat cost x days inactive |
| Repetition Detector | Manual workflows that repeat | Claude scores automation candidates |

Each engine writes to a unified `findings` table with a dollar estimate, a recommended fix, and a confidence score. The dashboard ranks by recoverable spend.

## Architecture

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

## Quick start (local)

```bash
git clone https://github.com/beto-llanos/pulseops.git
cd pulseops
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app boots in **demo mode** with realistic synthetic data. No API keys required to see it run.

To enable live integrations, copy `.env.example` to `.env` and fill in the keys you have. Each integration is opt-in.

## Deploy

### Streamlit Community Cloud (recommended, free)

1. Push this repo to GitHub
2. Go to https://share.streamlit.io
3. Click "New app", select this repo, branch `main`, file `streamlit_app.py`
4. Add secrets in the Streamlit Cloud UI (same keys as `.env.example`)
5. Done

### Docker

```bash
docker compose up
```

## Tech stack

Python 3.11, Streamlit, Plotly, Anthropic Claude API, SQLite, Google Calendar API, GitHub REST API, Jira Cloud API, Telegram Bot API, Docker.

## License

MIT
