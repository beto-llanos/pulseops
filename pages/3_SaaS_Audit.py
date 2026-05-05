"""SaaS Utilization Audit - unused seats, redundant tools, recoverable spend."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from pulseops import engines

st.set_page_config(page_title="SaaS Utilization Audit", page_icon="💳", layout="wide")


@st.cache_data(ttl=300)
def load_state():
    return engines.run_all()


def money(x: float) -> str:
    return f"${x:,.0f}"


state = load_state()
saas = state["saas"]

st.title("SaaS Utilization Audit")
st.caption("Cross-reference billing data against actual login activity.")

df = pd.DataFrame(saas)

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tools tracked", str(len(df)))
c2.metric("Total monthly spend", money(df["total_seats"].mul(df["monthly_cost_per_seat"]).sum()))
c3.metric("Monthly waste", money(df["monthly_waste"].sum()))
c4.metric("Annual recoverable", money(df["annual_waste"].sum()))

st.divider()

# Utilization chart
df_chart = df.sort_values("active_pct")
fig = px.bar(
    df_chart,
    x="active_pct",
    y="tool",
    orientation="h",
    title="Utilization rate by tool (active seats / total seats)",
    color="active_pct",
    color_continuous_scale=[(0, "#ef4444"), (0.5, "#f59e0b"), (1, "#22c55e")],
    range_color=(0, 1),
    labels={"active_pct": "Utilization", "tool": "Tool"},
)
fig.update_layout(
    plot_bgcolor="#0b0f17",
    paper_bgcolor="#0b0f17",
    font_color="#e5e7eb",
    height=500,
    coloraxis_showscale=False,
)
fig.update_xaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Per-tool table
st.subheader("Per-tool breakdown")
view = df.copy()
view["monthly_cost"] = view["total_seats"] * view["monthly_cost_per_seat"]
view["active_pct"] = (view["active_pct"] * 100).round(0).astype(int).astype(str) + "%"
view["monthly_waste"] = view["monthly_waste"].apply(money)
view["annual_waste"] = view["annual_waste"].apply(money)
view["monthly_cost"] = view["monthly_cost"].apply(money)
view = view[
    [
        "tool",
        "category",
        "total_seats",
        "active_seats",
        "unused_seats",
        "active_pct",
        "monthly_cost",
        "monthly_waste",
        "annual_waste",
    ]
].rename(
    columns={
        "tool": "Tool",
        "category": "Category",
        "total_seats": "Total seats",
        "active_seats": "Active",
        "unused_seats": "Unused",
        "active_pct": "Utilization",
        "monthly_cost": "Monthly cost",
        "monthly_waste": "Monthly waste",
        "annual_waste": "Annual waste",
    }
)
st.dataframe(view, use_container_width=True, hide_index=True)

st.divider()

# Findings
st.subheader("PulseOps findings")
saas_findings = [f for f in state["findings"] if f["engine"] == "saas"]
for f in saas_findings:
    with st.container(border=True):
        cols = st.columns([0.7, 0.15, 0.15])
        cols[0].markdown(f"**{f['title']}**\n\n{f['description']}\n\n_Fix:_ {f['suggested_fix']}")
        cols[1].metric("Annual", money(f["annual_cost_usd"]))
        cols[2].metric("Confidence", f["confidence"].upper())
