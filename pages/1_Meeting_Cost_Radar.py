"""Meeting Cost Radar - per-meeting dollar cost, attendees, output tracking."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from pulseops import engines, salary_bands

st.set_page_config(page_title="Meeting Cost Radar", page_icon="📅", layout="wide")


@st.cache_data(ttl=300)
def load_state():
    return engines.run_all()


def money(x: float) -> str:
    return f"${x:,.0f}"


state = load_state()
meetings = state["meetings"]

st.title("Meeting Cost Radar")
st.caption("Real-time dollar cost of every meeting, based on attendees, role, and duration.")

# Compute per-meeting cost
rows = []
for m in meetings:
    cost = sum(
        salary_bands.cost_for(a["role"], m["duration_minutes"])
        for a in m["attendees"]
    )
    rows.append(
        {
            "title": m["title"],
            "start": datetime.fromisoformat(m["start"]),
            "duration_min": m["duration_minutes"],
            "attendees": len(m["attendees"]),
            "cost": cost,
            "kind": m["kind"],
            "tracked_outcome": m["has_action_items"] and m["has_decisions_recorded"],
        }
    )
df = pd.DataFrame(rows)
df["day"] = df["start"].dt.date

# KPIs
total = df["cost"].sum()
zero = df[~df["tracked_outcome"]]["cost"].sum()
avg = df["cost"].mean() if not df.empty else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric("14-day meeting spend", money(total))
c2.metric("No tracked outcome", money(zero), delta=f"{zero / total * 100:.0f}% of total" if total else "")
c3.metric("Average meeting cost", money(avg))
c4.metric("Total meetings", str(len(df)))

st.divider()

# Daily cost chart
daily = df.groupby("day", as_index=False)["cost"].sum()
fig = px.bar(
    daily,
    x="day",
    y="cost",
    title="Daily meeting spend (last 14 days)",
    labels={"cost": "Cost (USD)", "day": "Date"},
)
fig.update_traces(marker_color="#22c55e")
fig.update_layout(plot_bgcolor="#0b0f17", paper_bgcolor="#0b0f17", font_color="#e5e7eb")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Most expensive meetings
st.subheader("Most expensive meetings")
df_view = df.sort_values("cost", ascending=False).head(15).copy()
df_view["cost"] = df_view["cost"].apply(money)
df_view["start"] = df_view["start"].dt.strftime("%a %b %d, %H:%M")
df_view = df_view.rename(
    columns={
        "title": "Meeting",
        "start": "When",
        "duration_min": "Min",
        "attendees": "Attendees",
        "cost": "Cost",
        "kind": "Kind",
        "tracked_outcome": "Tracked outcome",
    }
)[["Meeting", "When", "Min", "Attendees", "Cost", "Kind", "Tracked outcome"]]
st.dataframe(df_view, use_container_width=True, hide_index=True)

st.divider()

# Findings from this engine
st.subheader("PulseOps findings")
meeting_findings = [f for f in state["findings"] if f["engine"] == "meeting"]
for f in meeting_findings:
    with st.container(border=True):
        cols = st.columns([0.7, 0.15, 0.15])
        cols[0].markdown(f"**{f['title']}**\n\n{f['description']}\n\n_Fix:_ {f['suggested_fix']}")
        cols[1].metric("Annual", money(f["annual_cost_usd"]))
        cols[2].metric("Confidence", f["confidence"].upper())
