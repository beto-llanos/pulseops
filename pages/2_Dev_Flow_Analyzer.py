"""Dev Flow Analyzer - PR cycle time, blocked work, reviewer load."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from pulseops import engines, salary_bands

st.set_page_config(page_title="Dev Flow Analyzer", page_icon="🚧", layout="wide")


@st.cache_data(ttl=300)
def load_state():
    return engines.run_all()


def money(x: float) -> str:
    return f"${x:,.0f}"


state = load_state()
prs = state["prs"]

st.title("Dev Flow Analyzer")
st.caption("Translate PR cycle time and blocked work directly into engineering cost.")

df = pd.DataFrame(prs)
df["opened_at"] = pd.to_datetime(df["opened_at"])

# Compute cost
df["wait_cost"] = df.apply(
    lambda r: salary_bands.hourly_cost(r["author_role"]) * r["wait_hours"] * 0.2,
    axis=1,
)

# KPIs
blocked = df[df["is_blocked"]]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Open PRs", str(len(df[df["merged_at"].isna()])))
c2.metric("Blocked over 48h", str(len(blocked)))
c3.metric("Median first-review", f"{df['first_review_hours'].median():.0f}h")
c4.metric("Wait cost (14d)", money(df["wait_cost"].sum()))

st.divider()

# Wait-time distribution
fig = px.histogram(
    df,
    x="first_review_hours",
    nbins=10,
    title="First-review wait time distribution",
    labels={"first_review_hours": "Hours until first review"},
)
fig.update_traces(marker_color="#22c55e")
fig.update_layout(plot_bgcolor="#0b0f17", paper_bgcolor="#0b0f17", font_color="#e5e7eb")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Per-author breakdown
st.subheader("Reviewer load by author")
by_author = df.groupby("author").agg(
    pr_count=("number", "count"),
    median_wait=("first_review_hours", "median"),
    total_wait_cost=("wait_cost", "sum"),
).reset_index().sort_values("total_wait_cost", ascending=False)
by_author["total_wait_cost"] = by_author["total_wait_cost"].apply(money)
by_author = by_author.rename(
    columns={
        "author": "Author",
        "pr_count": "PRs",
        "median_wait": "Median wait (h)",
        "total_wait_cost": "Wait cost",
    }
)
st.dataframe(by_author, use_container_width=True, hide_index=True)

st.divider()

# Blocked PRs detail
st.subheader("Currently blocked")
if not blocked.empty:
    view = blocked[["number", "title", "author", "first_review_hours", "wait_cost", "url"]].copy()
    view["wait_cost"] = view["wait_cost"].apply(money)
    view = view.rename(
        columns={
            "number": "#",
            "title": "Title",
            "author": "Author",
            "first_review_hours": "Hours waiting",
            "wait_cost": "Cost so far",
            "url": "Link",
        }
    )
    st.dataframe(view, use_container_width=True, hide_index=True)
else:
    st.success("No PRs currently blocked over 48h. Nice.")

st.divider()

# Findings from this engine
st.subheader("PulseOps findings")
flow_findings = [f for f in state["findings"] if f["engine"] == "dev_flow"]
for f in flow_findings:
    with st.container(border=True):
        cols = st.columns([0.7, 0.15, 0.15])
        cols[0].markdown(f"**{f['title']}**\n\n{f['description']}\n\n_Fix:_ {f['suggested_fix']}")
        cols[1].metric("Annual", money(f["annual_cost_usd"]))
        cols[2].metric("Confidence", f["confidence"].upper())
