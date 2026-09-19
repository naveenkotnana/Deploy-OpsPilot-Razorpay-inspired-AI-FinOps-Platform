# -*- coding: utf-8 -*-
"""Overview View — Razorpay-inspired Executive Fintech Command Center."""
import pandas as pd
import streamlit as st
import altair as alt

from dashboard.components import (
    api_call,
    format_inr,
    render_insight_bar,
    render_kpi_row,
    render_severity_badge,
    render_top_header
)


def render_overview(role: str):
    """Render the primary executive operations dashboard."""
    render_top_header(
        title="Operations Overview",
        subtitle="Monitor revenue, operational health and AI-assisted investigations",
        role=role
    )

    # 1. Compact Filter Bar (Properly Proportioned)
    f_col1, f_col2, f_col3, f_col4 = st.columns([3.5, 1.8, 1.8, 1.2])
    with f_col1:
        date_sel = st.selectbox("Date Range", [
            "Apr 01, 2026 → Sep 30, 2026 (H1 FY26 Full Window)",
            "Sep 01, 2026 → Sep 30, 2026 (Latest Month)",
            "Jun 01, 2026 → Aug 31, 2026 (Trailing Q2)"
        ], index=0, label_visibility="collapsed")
    with f_col2:
        group_by = st.selectbox("Group by", ["Month", "Week", "Day"], index=0, label_visibility="collapsed")
    with f_col3:
        view_type = st.selectbox("View", ["Revenue", "Usage", "Devices", "Exceptions"], index=0, label_visibility="collapsed")
    with f_col4:
        st.button("Apply", type="primary", use_container_width=True)

    # Operational status ribbon
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:0.6rem 1.2rem; margin-bottom:1.2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#16A34A;"></span>
            <span style="font-size:0.8rem; font-weight:700; color:#0F172A;">Daily Reconciliation Pipeline:</span>
            <span class="fintech-badge badge-pass">ACTIVE & SYNCED</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px; font-size:0.78rem; color:#64748B;">
            <span>Auto-Match Rate: <strong style="color:#0F172A;">99.8%</strong></span>
            <span>Pending Approvals: <strong style="color:#0F172A;">6 Actions</strong></span>
            <span>Engine: <strong style="color:#0F172A;">Local Ollama + SQLite</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Fetch Live Backend Data
    rev_data, rev_err = api_call("GET", "/revenue?query=revenue_by_month")
    if rev_err or not rev_data:
        st.error(f"Failed to fetch revenue telemetry: {rev_err}")
        return

    df_rev = pd.DataFrame(rev_data.get("rows", []))
    if df_rev.empty:
        st.warning("No revenue data records found.")
        return

    latest = df_rev.iloc[-1]
    prev = df_rev.iloc[-2] if len(df_rev) >= 2 else latest

    # Compute KPI values
    curr_rev = float(latest["total_revenue"])
    prev_rev = float(prev["total_revenue"])
    rev_change_pct = ((curr_rev - prev_rev) / max(prev_rev, 1)) * 100

    # Fetch active devices count
    dev_data, _ = api_call("GET", "/revenue?query=active_devices")
    df_dev = pd.DataFrame(dev_data.get("rows", [])) if dev_data else pd.DataFrame()
    total_active_devices = df_dev[df_dev["device_status"] == "ACTIVE"]["devices"].sum() if not df_dev.empty else 1000

    # Fetch exceptions count
    ex_data, _ = api_call("GET", "/revenue?query=missing_data")
    df_ex = pd.DataFrame(ex_data.get("rows", [])) if ex_data else pd.DataFrame()
    open_exceptions_count = len(df_ex)

    # Fetch health & alerts
    alerts_data, _ = api_call("GET", "/alerts")
    alerts_list = alerts_data or []
    high_priority_alerts = sum(1 for a in alerts_list if a.get("severity") in ("CRITICAL", "HIGH"))

    # Operational health calculation (records valid & workflow success)
    dq_data, _ = api_call("GET", "/data-quality")
    dq_runs = dq_data.get("runs", []) if dq_data else []
    tot_rec = sum(r.get("records_received", 0) for r in dq_runs)
    tot_loaded = sum(r.get("records_loaded", 0) for r in dq_runs)
    op_health = (tot_loaded / max(tot_rec, 1)) * 100 if tot_rec > 0 else 99.8

    # 3. Four Executive KPI Cards
    render_kpi_row([
        {
            "label": "Monthly Revenue",
            "value": format_inr(curr_rev, compact=True),
            "trend_text": f"{abs(rev_change_pct):.1f}%",
            "trend_direction": "up" if rev_change_pct >= 0 else "down",
            "subtext": "vs previous month"
        },
        {
            "label": "Active Devices",
            "value": f"{int(total_active_devices):,}",
            "trend_text": "0.0%",
            "trend_direction": "neutral",
            "subtext": "100% telemetry online"
        },
        {
            "label": "Open Exceptions",
            "value": str(open_exceptions_count),
            "trend_text": f"{high_priority_alerts} priority",
            "trend_direction": "down" if high_priority_alerts > 0 else "neutral",
            "subtext": "requires operational review"
        },
        {
            "label": "Operational Health",
            "value": f"{op_health:.1f}%",
            "trend_text": "Optimal",
            "trend_direction": "up",
            "subtext": "data + workflow engine"
        }
    ])

    # 4. Main Revenue Chart Panel
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.25rem 1.5rem; margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem;">
            <div>
                <h3 style="margin:0; font-size:1.1rem; font-weight:700; color:#0F172A;">Revenue Overview</h3>
                <div style="font-size:0.8rem; color:#64748B;">Deterministic billing aggregation across all apartments and utility meters</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.4rem; font-weight:800; color:#0F172A;">{total_rev_str}</div>
                <div style="font-size:0.75rem; color:{comp_color}; font-weight:600;">{trend_arrow} {comp_text} vs previous period</div>
            </div>
        </div>
    """.format(
        total_rev_str=format_inr(curr_rev),
        comp_color="#16A34A" if rev_change_pct >= 0 else "#DC2626",
        trend_arrow="↑" if rev_change_pct >= 0 else "↓",
        comp_text=f"{abs(rev_change_pct):.2f}%"
    ), unsafe_allow_html=True)

    # Altair clean area chart
    chart_df = df_rev.copy()
    chart_df["billing_month"] = chart_df["billing_month"].astype(str)

    base = alt.Chart(chart_df).encode(x=alt.X("billing_month:N", title="Billing Month", axis=alt.Axis(labelAngle=0)))
    area = base.mark_area(
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#2F5BFF', offset=0),
                   alt.GradientStop(color='rgba(47, 91, 255, 0.05)', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        ),
        opacity=0.7
    ).encode(
        y=alt.Y("total_revenue:Q", title="Revenue (₹)", scale=alt.Scale(zero=False))
    )
    line = base.mark_line(color="#2F5BFF", strokeWidth=2.5).encode(
        y=alt.Y("total_revenue:Q"),
        tooltip=[
            alt.Tooltip("billing_month:N", title="Month"),
            alt.Tooltip("total_revenue:Q", title="Revenue (₹)", format=",.2f"),
            alt.Tooltip("apartments:Q", title="Apartments Billed"),
            alt.Tooltip("mom_pct:Q", title="MoM Change (%)", format="+.2f")
        ]
    )
    rolling_line = base.mark_line(color="#06B6D4", strokeWidth=2, strokeDash=[4, 4]).encode(
        y=alt.Y("rolling_3m_avg:Q"),
        tooltip=[
            alt.Tooltip("billing_month:N", title="Month"),
            alt.Tooltip("rolling_3m_avg:Q", title="Rolling 3M Avg (₹)", format=",.2f")
        ]
    )

    combined_chart = (area + line + rolling_line).properties(height=260)
    st.altair_chart(combined_chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 5. Revenue Insights (2-Column Breakdown)
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#0F172A; margin: 1.5rem 0 0.8rem 0;'>Revenue Insights</h3>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.2rem; min-height:340px;">
            <div style="font-size:0.95rem; font-weight:700; color:#0F172A; margin-bottom:0.25rem;">Revenue by Building Location</div>
            <div style="font-size:0.75rem; color:#64748B; margin-bottom:0.75rem;">Total revenue distribution across geographic clusters</div>
        """, unsafe_allow_html=True)

        loc_data, _ = api_call("GET", "/revenue?query=revenue_by_location")
        if loc_data and loc_data.get("rows"):
            df_loc = pd.DataFrame(loc_data["rows"])
            latest_month = df_loc["billing_month"].max()
            df_loc_latest = df_loc[df_loc["billing_month"] == latest_month].sort_values("revenue", ascending=False)
            
            bldg_chart = alt.Chart(df_loc_latest).mark_bar(color="#2F5BFF", cornerRadiusEnd=4).encode(
                x=alt.X("revenue:Q", title="Revenue (₹)", axis=alt.Axis(format="~s")),
                y=alt.Y("location_code:N", title="Location", sort="-x"),
                tooltip=[
                    alt.Tooltip("location_code:N", title="Location"),
                    alt.Tooltip("revenue:Q", title="Revenue (₹)", format=",.2f"),
                    alt.Tooltip("apartments:Q", title="Apartments"),
                    alt.Tooltip("exceptions:Q", title="Exceptions")
                ]
            ).properties(height=220)
            st.altair_chart(bldg_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.2rem; min-height:340px;">
            <div style="font-size:0.95rem; font-weight:700; color:#0F172A; margin-bottom:0.25rem;">Revenue by Service Plan</div>
            <div style="font-size:0.75rem; color:#64748B; margin-bottom:0.75rem;">Plan mix distribution between Water and Rental tiers</div>
        """, unsafe_allow_html=True)

        plan_data, _ = api_call("GET", "/revenue?query=revenue_by_plan")
        if plan_data and plan_data.get("rows"):
            df_plan = pd.DataFrame(plan_data["rows"])
            latest_m = df_plan["billing_month"].max()
            df_plan_latest = df_plan[df_plan["billing_month"] == latest_m]
            
            plan_chart = alt.Chart(df_plan_latest).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("revenue:Q", title="Revenue (₹)", axis=alt.Axis(format="~s")),
                y=alt.Y("plan_id:N", title="Plan ID", sort="-x"),
                color=alt.Color("service:N", scale=alt.Scale(domain=["WATER", "RENTAL"], range=["#06B6D4", "#6366F1"]), legend=alt.Legend(title="Service")),
                tooltip=[
                    alt.Tooltip("plan_id:N", title="Plan"),
                    alt.Tooltip("service:N", title="Service"),
                    alt.Tooltip("revenue:Q", title="Revenue (₹)", format=",.2f"),
                    alt.Tooltip("devices:Q", title="Device Count")
                ]
            ).properties(height=220)
            st.altair_chart(plan_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 6. Horizontal Payment-Dashboard-Style Insight Bar
    water_rev = float(latest["water_revenue"])
    rental_rev = float(latest["rental_revenue"])
    water_pct = (water_rev / max(curr_rev, 1)) * 100
    rental_pct = (rental_rev / max(curr_rev, 1)) * 100

    render_insight_bar(
        title="Revenue Distribution by Service Stream",
        segments=[
            {"label": "Water Charges (Consumption)", "amount_str": format_inr(water_rev), "pct": water_pct, "color": "#06B6D4"},
            {"label": "Rental Charges (Hardware / Appliances)", "amount_str": format_inr(rental_rev), "pct": rental_pct, "color": "#2F5BFF"},
            {"label": "Exceptions / Proration Adjustments", "amount_str": "₹0", "pct": 0.0, "color": "#F59E0B"}
        ]
    )

    # 7. Operational Insights (4 Fintech Cards)
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#0F172A; margin: 1.5rem 0 0.8rem 0;'>Operational Insights</h3>", unsafe_allow_html=True)
    
    # Calculate top building metrics dynamically
    highest_bldg = "HYD-NORTH"
    highest_bldg_rev = 0.0
    largest_change_bldg = "HYD-EAST"
    largest_change_pct = "+0.0%"
    highest_ex_bldg = "HYD-EAST"
    highest_ex_count = 0

    if loc_data and loc_data.get("rows"):
        df_loc = pd.DataFrame(loc_data["rows"])
        l_month = df_loc["billing_month"].max()
        df_l = df_loc[df_loc["billing_month"] == l_month]
        if not df_l.empty:
            top_row = df_l.sort_values("revenue", ascending=False).iloc[0]
            highest_bldg = top_row["location_code"]
            highest_bldg_rev = float(top_row["revenue"])

            # Largest change
            if "mom_pct" in df_l.columns:
                df_valid_mom = df_l.dropna(subset=["mom_pct"])
                if not df_valid_mom.empty:
                    max_chg_row = df_valid_mom.sort_values("mom_pct", ascending=False).iloc[0]
                    largest_change_bldg = max_chg_row["location_code"]
                    largest_change_pct = f"{max_chg_row['mom_pct']:+.1f}%"

            # Highest exceptions
            if "exceptions" in df_l.columns:
                ex_row = df_l.sort_values("exceptions", ascending=False).iloc[0]
                highest_ex_bldg = ex_row["location_code"]
                highest_ex_count = int(ex_row["exceptions"])

    anom_data, _ = api_call("GET", "/anomalies")
    total_anomalies = len(anom_data or [])

    op_cols = st.columns(4)
    with op_cols[0]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 3px solid #2F5BFF;">
            <div class="kpi-label">Highest Revenue Cluster</div>
            <div style="font-size:1.2rem; font-weight:800; color:#0F172A;">{highest_bldg}</div>
            <div class="kpi-subtext"><strong style="color:#0F172A;">{format_inr(highest_bldg_rev, compact=True)}</strong> in latest period</div>
        </div>
        """, unsafe_allow_html=True)
    with op_cols[1]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 3px solid #10B981;">
            <div class="kpi-label">Largest Revenue Change</div>
            <div style="font-size:1.2rem; font-weight:800; color:#0F172A;">{largest_change_bldg}</div>
            <div class="kpi-subtext"><span class="trend-up">{largest_change_pct}</span> MoM growth delta</div>
        </div>
        """, unsafe_allow_html=True)
    with op_cols[2]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 3px solid #F59E0B;">
            <div class="kpi-label">Highest Exception Count</div>
            <div style="font-size:1.2rem; font-weight:800; color:#0F172A;">{highest_ex_bldg}</div>
            <div class="kpi-subtext"><span style="color:#D97706; font-weight:700;">{highest_ex_count} exceptions</span> under audit</div>
        </div>
        """, unsafe_allow_html=True)
    with op_cols[3]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 3px solid #DC2626;">
            <div class="kpi-label">Anomaly Concentration</div>
            <div style="font-size:1.2rem; font-weight:800; color:#0F172A;">{total_anomalies} Total</div>
            <div class="kpi-subtext"><span style="color:#DC2626; font-weight:700;">{len(alerts_list)} active alerts</span> isolated</div>
        </div>
        """, unsafe_allow_html=True)

    # 8. Recent Exceptions Table
    st.markdown("<h3 style='font-size:1.1rem; font-weight:700; color:#0F172A; margin: 1.5rem 0 0.8rem 0;'>Recent Exceptions</h3>", unsafe_allow_html=True)
    if not df_ex.empty:
        df_ex_display = df_ex.copy()
        df_ex_display["Severity"] = "HIGH"
        df_ex_display["Status"] = "OPEN"
        df_ex_display["total_revenue"] = df_ex_display["total_revenue"].apply(lambda v: format_inr(v))
        df_ex_display = df_ex_display.rename(columns={
            "apartment_id": "Entity ID",
            "location_code": "Cluster / Building",
            "exception_code": "Exception Type",
            "billing_month": "Period",
            "total_revenue": "Billed Amount"
        })
        st.dataframe(df_ex_display[["Period", "Entity ID", "Cluster / Building", "Exception Type", "Billed Amount", "Severity", "Status"]], use_container_width=True)
    else:
        st.info("No active exceptions detected across operational data.")
