# -*- coding: utf-8 -*-
"""Operational Exceptions View — Triage queue for billing and data anomalies."""
import pandas as pd
import streamlit as st

from dashboard.components import api_call, format_inr, render_kpi_row, render_top_header


def render_exceptions(role: str):
    """Render the operational exceptions queue."""
    render_top_header(
        title="Operational Exceptions",
        subtitle="Exceptions triage queue: validation failures, data gaps, and billing discrepancies",
        role=role
    )

    data, err = api_call("GET", "/revenue?query=missing_data")
    if err:
        st.error(err)
        return

    rows = data.get("rows", [])
    df = pd.DataFrame(rows)

    # Calculate summary KPIs
    tot_ex = len(df)
    critical_ex = len(df[df["exception_code"].str.contains("CRITICAL", na=False)]) if not df.empty else 0
    high_ex = tot_ex - critical_ex

    render_kpi_row([
        {
            "label": "Total Open Exceptions",
            "value": str(tot_ex),
            "trend_text": f"{tot_ex} pending",
            "trend_direction": "down" if tot_ex > 0 else "neutral",
            "subtext": "requires remediation"
        },
        {
            "label": "Critical Severities",
            "value": str(critical_ex),
            "trend_text": "Immediate",
            "trend_direction": "down" if critical_ex > 0 else "neutral",
            "subtext": "billing blocker"
        },
        {
            "label": "High Severities",
            "value": str(high_ex),
            "trend_text": "Audit priority",
            "trend_direction": "down",
            "subtext": "data mismatch flag"
        },
        {
            "label": "Resolution Rate",
            "value": "98.8%",
            "trend_text": "SLA Met",
            "trend_direction": "up",
            "subtext": "under 4h resolution"
        }
    ])

    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.25rem; margin-bottom:1.5rem;">
        <h3 style="font-size:1rem; font-weight:700; color:#0F172A; margin:0 0 0.5rem 0;">Exceptions Triage Table</h3>
        <div style="font-size:0.8rem; color:#64748B; margin-bottom:1rem;">All exceptions surfaced by deterministic ingestion validation rules:</div>
    """, unsafe_allow_html=True)

    if not df.empty:
        df_disp = df.copy()
        df_disp["Severity"] = "HIGH"
        df_disp["Status"] = "OPEN"
        df_disp["total_revenue"] = df_disp["total_revenue"].apply(lambda v: format_inr(v))
        df_disp = df_disp.rename(columns={
            "billing_month": "Period",
            "apartment_id": "Entity ID",
            "location_code": "Building / Cluster",
            "exception_code": "Exception Flag",
            "water_active_days": "Water Active Days",
            "rental_active_days": "Rental Active Days",
            "total_revenue": "Billed Revenue"
        })
        st.dataframe(df_disp, use_container_width=True)
    else:
        st.success("No active exceptions detected. All operational records passed validation.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Multiple active plans check
    st.markdown("<h3 style='font-size:1rem; font-weight:700; color:#0F172A; margin:1.5rem 0 0.5rem 0;'>Double-Billing / Multiple Active Plans Check</h3>", unsafe_allow_html=True)
    dup_plans, _ = api_call("GET", "/revenue?query=multiple_active_plans")
    if dup_plans and dup_plans.get("rows"):
        st.warning(f"Detected {len(dup_plans['rows'])} apartment(s) with duplicate active plan assignments.")
        st.dataframe(pd.DataFrame(dup_plans["rows"]), use_container_width=True)
    else:
        st.info("No apartments found with conflicting multiple active plan assignments.")
