"""Repetition Detector - manual workflows scored for automation by Claude."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from pulseops import engines, salary_bands
from pulseops.config import SETTINGS

st.set_page_config(page_title="Repetition Detector", page_icon="🔁", layout="wide")


@st.cache_data(ttl=300)
def load_state():
    return engines.run_all()


def money(x: float) -> str:
    return f"${x:,.0f}"


state = load_state()
repetition_findings = [f for f in state["findings"] if f["engine"] == "repetition"]
workflows = state["workflows"]

st.title("Repetition Detector")
st.caption(
    "Manual workflows scored by Claude for automation potential. "
    f"{'Live Claude integration active.' if SETTINGS.has_claude else 'Running in heuristic fallback mode (no ANTHROPIC_API_KEY set).'}"
)

# Build full table even for sub-50 scores
all_rows = []
for w in workflows:
    annual_minutes = w["occurrences_per_month"] * w["minutes_per_run"] * 12
    annual_cost = salary_bands.cost_for(w["owner_role"], annual_minutes)
    score = next(
        (f["metadata"]["automation_score"] for f in repetition_findings if f["title"] == w["title"]),
        None,
    )
    all_rows.append(
        {
            "Workflow": w["title"],
            "Per month": w["occurrences_per_month"],
            "Min/run": w["minutes_per_run"],
            "Owner role": w["owner_role"].replace("_", " "),
            "Annual cost": annual_cost,
            "Automation score": score if score is not None else "below threshold",
        }
    )
df = pd.DataFrame(all_rows)

c1, c2, c3 = st.columns(3)
c1.metric("Workflows analyzed", str(len(df)))
c2.metric("Automation candidates", str(len(repetition_findings)))
c3.metric("Recoverable annually", money(sum(f["annual_cost_usd"] for f in repetition_findings)))

st.divider()

# Cost vs score scatter
chart_df = df[df["Automation score"] != "below threshold"].copy()
if not chart_df.empty:
    chart_df["Automation score"] = chart_df["Automation score"].astype(int)
    fig = px.scatter(
        chart_df,
        x="Automation score",
        y="Annual cost",
        size="Per month",
        text="Workflow",
        title="Annual cost vs automation potential",
    )
    fig.update_traces(textposition="top center", marker_color="#22c55e")
    fig.update_layout(plot_bgcolor="#0b0f17", paper_bgcolor="#0b0f17", font_color="#e5e7eb")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Full table
st.subheader("All detected repetitive workflows")
df_view = df.copy()
df_view["Annual cost"] = df_view["Annual cost"].apply(money)
st.dataframe(df_view, use_container_width=True, hide_index=True)

st.divider()

# Findings
st.subheader("PulseOps findings")
for f in repetition_findings:
    with st.container(border=True):
        cols = st.columns([0.7, 0.15, 0.15])
        cols[0].markdown(f"**{f['title']}**\n\n{f['description']}\n\n_Fix:_ {f['suggested_fix']}")
        cols[1].metric("Annual", money(f["annual_cost_usd"]))
        cols[2].metric("Confidence", f["confidence"].upper())
