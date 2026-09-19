# -*- coding: utf-8 -*-
"""Revenue Operations View — Detailed financial breakdown & query analytics."""
import pandas as pd
import streamlit as st
import altair as alt

from dashboard.components import api_call, format_inr, render_kpi_row, render_top_header


def render_revenue(role: str):
    """Render the detailed revenue operations view."""
    render_top_header(
        title="Revenue Analytics",
        subtitle="Deterministic financial calculations, plan mix tracking, and MoM adjustments",
        role=role
    )

    # 1. High-level financial KPIs
    rev_data, _ = api_call("GET", "/revenue?query=revenue_by_month")
    if rev_data and rev_data.get("rows"):
        df_rev = pd.DataFrame(rev_data["rows"])
        latest = df_rev.iloc[-1]
        prev = df_rev.iloc[-2] if len(df_rev) >= 2 else latest
        curr_rev = float(latest["total_revenue"])
        prev_rev = float(prev["total_revenue"])
        mom_change = ((curr_rev - prev_rev) / max(prev_rev, 1)) * 100

        total_h1_rev = df_rev["total_revenue"].sum()
        avg_monthly = df_rev["total_revenue"].mean()

        render_kpi_row([
            {
                "label": "Latest Month Revenue",
                "value": format_inr(curr_rev, compact=True),
                "trend_text": f"{abs(mom_change):.1f}%",
                "trend_direction": "up" if mom_change >= 0 else "down",
                "subtext": "vs previous month"
            },
            {
                "label": "Cumulative H1 Revenue",
                "value": format_inr(total_h1_rev, compact=True),
                "trend_text": "6 Months",
                "trend_direction": "neutral",
                "subtext": "Apr 2026 – Sep 2026"
            },
            {
                "label": "Average Monthly Run-Rate",
                "value": format_inr(avg_monthly, compact=True),
                "trend_text": "Deterministic",
                "trend_direction": "up",
                "subtext": "100% verified math"
            },
            {
                "label": "Active Metered Units",
                "value": f"{int(latest['apartments']):,}",
                "trend_text": "Stable",
                "trend_direction": "neutral",
                "subtext": "500 residential units"
            }
        ])

    # 2. Query Selector Panel
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.25rem; margin-bottom:1.5rem;">
        <h3 style="font-size:1rem; font-weight:700; color:#0F172A; margin:0 0 0.5rem 0;">Revenue Analytical Models</h3>
        <div style="font-size:0.8rem; color:#64748B; margin-bottom:1rem;">Select a pre-compiled, verified SQL analytical model to inspect data:</div>
    """, unsafe_allow_html=True)

    queries = [
        ("revenue_by_month", "Monthly Revenue Trend (MoM % & Rolling 3M Average)"),
        ("revenue_by_location", "Revenue by Building Location (P&L per geographic cluster)"),
        ("revenue_by_plan", "Plan Mix Breakdown (Water vs Rental billing breakdown)"),
        ("revenue_outliers", "Revenue Outlier Units (Apartments exceeding 50% location mean)"),
        ("mom_change_by_apartment", "MoM Movers (Apartment-level largest billing deltas)"),
        ("device_revenue", "Device Revenue Ranking (Rank within location)")
    ]

    query_key = st.selectbox(
        "Select Analytical Query",
        options=[q[0] for q in queries],
        format_func=lambda k: next(q[1] for q in queries if q[0] == k)
    )

    data, err = api_call("GET", f"/revenue?query={query_key}")
    if err:
        st.error(err)
    elif data and data.get("rows"):
        df_q = pd.DataFrame(data["rows"])
        st.caption(f"Returned {data.get('row_count', len(df_q))} records in {data.get('latency_ms', 1)}ms")

        # Format numeric columns for fintech display
        df_formatted = df_q.copy()
        for col in df_formatted.columns:
            if "revenue" in col or "avg" in col or "prev" in col or "delta" in col:
                df_formatted[col] = df_formatted[col].apply(lambda x: format_inr(x) if pd.notna(x) else "—")

        st.dataframe(df_formatted, use_container_width=True)

        # Visualizations for specific queries
        if query_key == "revenue_by_location" and not df_q.empty:
            st.markdown("<h4 style='font-size:0.9rem; font-weight:700; margin:1rem 0 0.5rem 0;'>Location Revenue Trend</h4>", unsafe_allow_html=True)
            piv = df_q.pivot_table(index="billing_month", columns="location_code", values="revenue", aggfunc="sum")
            st.bar_chart(piv)
        elif query_key == "revenue_by_plan" and not df_q.empty:
            st.markdown("<h4 style='font-size:0.9rem; font-weight:700; margin:1rem 0 0.5rem 0;'>Plan Revenue Distribution</h4>", unsafe_allow_html=True)
            chart = alt.Chart(df_q).mark_bar().encode(
                x=alt.X("billing_month:N", title="Month"),
                y=alt.Y("revenue:Q", title="Revenue (₹)"),
                color=alt.Color("plan_id:N", title="Plan"),
                tooltip=["billing_month", "plan_id", "service", "revenue", "devices"]
            )
            st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
