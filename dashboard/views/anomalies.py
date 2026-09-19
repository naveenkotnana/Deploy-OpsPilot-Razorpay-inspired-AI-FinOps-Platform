# -*- coding: utf-8 -*-
"""Anomaly Detection View — Statistical outliers and Isolation Forest alerts."""
import pandas as pd
import streamlit as st

from dashboard.components import api_call, format_inr, render_kpi_row, render_top_header


def render_anomalies(role: str):
    """Render the anomaly detection and analysis dashboard."""
    render_top_header(
        title="Anomaly Detection",
        subtitle="Isolation Forest statistical deviations, z-score outliers, and automated operational alerts",
        role=role
    )

    anom_data, err = api_call("GET", "/anomalies")
    if err:
        st.error(err)
        return

    df_anom = pd.DataFrame(anom_data or [])
    alerts_data, _ = api_call("GET", "/alerts")
    alerts_list = alerts_data or []

    # KPI counts by severity
    tot = len(df_anom)
    crit = len(df_anom[df_anom["severity"] == "CRITICAL"]) if not df_anom.empty else 0
    high = len(df_anom[df_anom["severity"] == "HIGH"]) if not df_anom.empty else 0
    med = len(df_anom[df_anom["severity"] == "MEDIUM"]) if not df_anom.empty else 0
    low = len(df_anom[df_anom["severity"] == "LOW"]) if not df_anom.empty else 0

    render_kpi_row([
        {
            "label": "Total Anomalies",
            "value": str(tot),
            "trend_text": f"{len(alerts_list)} alerts",
            "trend_direction": "down" if len(alerts_list) > 0 else "neutral",
            "subtext": "statistically scored"
        },
        {
            "label": "Medium Severity",
            "value": str(med),
            "trend_text": "Escalated",
            "trend_direction": "down",
            "subtext": "requires ops review"
        },
        {
            "label": "Low Severity",
            "value": str(low),
            "trend_text": "Monitored",
            "trend_direction": "neutral",
            "subtext": "within threshold band"
        },
        {
            "label": "Model Algorithm",
            "value": "iForest + Rule",
            "trend_text": "Zero-Cost",
            "trend_direction": "up",
            "subtext": "local scikit-learn"
        }
    ])

    # Active operational alerts
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.25rem; margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
            <div>
                <h3 style="font-size:1rem; font-weight:700; color:#0F172A; margin:0;">Active Operational Alerts</h3>
                <div style="font-size:0.8rem; color:#64748B;">Elevated anomalies that met severity thresholds and generated tickets:</div>
            </div>
            <span style="font-size:0.75rem; background:#FEF3C7; color:#B45309; padding:4px 8px; border-radius:4px; font-weight:700;">
                {alert_count} TICKETS ACTIVE
            </span>
        </div>
    """.format(alert_count=len(alerts_list)), unsafe_allow_html=True)

    if alerts_list:
        df_al = pd.DataFrame(alerts_list)
        df_al_disp = df_al[["alert_id", "entity", "metric", "billing_month", "observed_value", "anomaly_score", "severity", "status"]].copy()
        df_al_disp["observed_value"] = df_al_disp["observed_value"].apply(lambda v: format_inr(v))
        df_al_disp["anomaly_score"] = df_al_disp["anomaly_score"].apply(lambda s: f"{float(s):.3f}")
        df_al_disp = df_al_disp.rename(columns={
            "alert_id": "Alert ID",
            "entity": "Entity / Cluster",
            "metric": "Telemetry Metric",
            "billing_month": "Month",
            "observed_value": "Observed",
            "anomaly_score": "Score",
            "severity": "Severity",
            "status": "Ticket Status"
        })
        st.dataframe(df_al_disp, use_container_width=True)
    else:
        st.info("No active operational alerts.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Full anomalies breakdown
    st.markdown("<h3 style='font-size:1rem; font-weight:700; color:#0F172A; margin:1.5rem 0 0.5rem 0;'>Comprehensive Scored Anomalies (All Tiers)</h3>", unsafe_allow_html=True)
    if not df_anom.empty:
        df_anom_disp = df_anom.rename(columns={
            "anomaly_id": "Anomaly ID",
            "billing_month": "Month",
            "entity_id": "Entity / Cluster",
            "method": "Detector Method",
            "severity": "Severity",
            "anomaly_score": "Score",
            "reason": "Detection Rationale"
        })
        st.dataframe(df_anom_disp, use_container_width=True)
    else:
        st.info("No anomaly records detected.")
