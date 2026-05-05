"""PulseOps - Home page.

Top 5 Money Drains This Week, headline KPIs, and shortcuts to each engine.
"""
from __future__ import annotations

import streamlit as st

from pulseops import engines, telegram
from pulseops.config import SETTINGS
from pulseops.mock_data import COMPANY_NAME, COMPANY_SIZE

st.set_page_config(
    page_title="PulseOps",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=300)
def load_state():
    return engines.run_all()


def money(x: float) -> str:
    return f"${x:,.0f}"


def confidence_badge(conf: str) -> str:
    color = {"high": "#22c55e", "medium": "#f59e0b", "low": "#94a3b8"}[conf]
    return f"<span style='background:{color}; color:#0b0f17; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:600;'>{conf.upper()}</span>"


def engine_pill(engine: str) -> str:
    label = {
        "meeting": "Meetings",
        "dev_flow": "Dev Flow",
        "saas": "SaaS",
        "repetition": "Repetition",
    }[engine]
    return f"<span style='background:#1f2937; color:#9ca3af; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>{label}</span>"


# ---------------- Header ----------------

state = load_state()
findings = state["findings"]
totals = state["totals"]

st.markdown(
    """
    <div style='display:flex; align-items:baseline; gap:16px;'>
        <h1 style='margin:0;'>PulseOps</h1>
        <span style='color:#9ca3af;'>Real-time operational intelligence</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Connected workspace: **{COMPANY_NAME}**  |  "
    f"{COMPANY_SIZE} employees  |  "
    f"Mode: **{'DEMO (synthetic data)' if SETTINGS.is_demo else 'LIVE'}**  |  "
    f"Claude: {'connected' if SETTINGS.has_claude else 'fallback heuristics'}"
)

st.divider()

# ---------------- Headline KPIs ----------------

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Annual recoverable spend",
    money(totals["annual_recoverable"]),
    help="Sum of all detected inefficiencies, projected to a full year.",
)
c2.metric(
    "This week's drain",
    money(sum(f["weekly_cost_usd"] for f in findings)),
    help="Estimated cost of inefficiencies in the last 7 days.",
)
c3.metric("Active findings", str(len(findings)))
high_conf = sum(1 for f in findings if f["confidence"] == "high")
c4.metric("High-confidence", str(high_conf))

st.divider()

# ---------------- Top 5 Money Drains ----------------

st.subheader("Top 5 Money Drains This Week")
st.caption("Ranked by annualized recoverable spend.")

top = findings[:5]
for i, f in enumerate(top, 1):
    with st.container(border=True):
        cols = st.columns([0.05, 0.55, 0.20, 0.20])
        cols[0].markdown(f"### {i}")
        cols[1].markdown(
            f"**{f['title']}**  {engine_pill(f['engine'])}  {confidence_badge(f['confidence'])}<br/>"
            f"<span style='color:#9ca3af;'>{f['description']}</span>",
            unsafe_allow_html=True,
        )
        cols[2].metric("Annual cost", money(f["annual_cost_usd"]))
        cols[3].markdown(f"**Suggested fix**<br/><span style='color:#9ca3af;'>{f['suggested_fix']}</span>", unsafe_allow_html=True)

st.divider()

# ---------------- Engine summary ----------------

st.subheader("By engine")

summary_cols = st.columns(4)
engine_names = [
    ("meeting", "Meeting Cost Radar", "Calendar"),
    ("dev_flow", "Dev Flow Analyzer", "GitHub + Jira"),
    ("saas", "SaaS Utilization Audit", "Billing data"),
    ("repetition", "Repetition Detector", "Tickets + Claude"),
]
for col, (key, label, source) in zip(summary_cols, engine_names):
    engine_findings = [f for f in findings if f["engine"] == key]
    annual = sum(f["annual_cost_usd"] for f in engine_findings)
    with col:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.caption(source)
            st.metric("Annual", money(annual))
            st.caption(f"{len(engine_findings)} findings")

st.divider()

# ---------------- Weekly digest ----------------

st.subheader("Weekly digest")

dc1, dc2 = st.columns([0.6, 0.4])
with dc1:
    st.caption("Preview of the Telegram digest sent every Monday at 9am.")
    st.code(telegram.format_digest(findings), language="markdown")
with dc2:
    st.markdown("**Send a test digest**")
    if SETTINGS.has_telegram:
        if st.button("Send to Telegram now", type="primary"):
            ok = telegram.send_digest(telegram.format_digest(findings))
            st.success("Sent.") if ok else st.error("Failed. Check logs.")
    else:
        st.info("Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to enable live sending.")
        st.button("Send to Telegram now", disabled=True)

st.divider()

st.caption(
    "PulseOps - built for the Internal Tools Hackathon. "
    "Source: github.com/beto-llanos/pulseops"
)
