# -*- coding: utf-8 -*-
"""Operational Records View — Fintech payment-transaction style operational ledger."""
import pandas as pd
import streamlit as st

from dashboard.components import api_call, format_inr, render_top_header


def render_transactions(role: str):
    """Render the high-density operational records table (inspired by fintech payment ledgers)."""
    render_top_header(
        title="Operational Records",
        subtitle="Granular operational billing ledger with search, multi-dimensional filters, and status auditing",
        role=role
    )

    # Fetch operational revenue rows from backend
    data, err = api_call("GET", "/revenue?query=device_revenue")
    if err or not data:
        st.error(f"Failed to load records: {err}")
        return

    df = pd.DataFrame(data.get("rows", []))
    if df.empty:
        st.info("No operational records available.")
        return

    # Add derived columns to match fintech transaction ledger
    df["record_id"] = [f"TXN-OPS-{20260400 + i}" for i in range(len(df))]
    df["status"] = "SETTLED"
    # Mark records with exceptions or oddities
    df.loc[df["total_revenue"] < 1000, "status"] = "FLAGGED"

    # Filter row
    f1, f2, f3, f4, f5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
    with f1:
        search_query = st.text_input("Search Apartment / Device", placeholder="e.g. APT-001 or WTR...", label_visibility="collapsed")
    with f2:
        bldg_options = ["All Buildings"] + sorted(df["location_code"].dropna().unique().tolist())
        sel_bldg = st.selectbox("Building", bldg_options, label_visibility="collapsed")
    with f3:
        month_options = ["All Months"] + sorted(df["billing_month"].dropna().unique().tolist(), reverse=True)
        sel_month = st.selectbox("Month", month_options, label_visibility="collapsed")
    with f4:
        status_options = ["All Statuses", "SETTLED", "FLAGGED"]
        sel_status = st.selectbox("Status", status_options, label_visibility="collapsed")
    with f5:
        page_size = st.selectbox("Page Size", [25, 50, 100, 200], index=0, label_visibility="collapsed")

    # Apply filters
    filtered_df = df.copy()
    if search_query:
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["apartment_id"].str.lower().str.contains(q) |
            filtered_df["water_device_id"].fillna("").str.lower().str.contains(q) |
            filtered_df["rental_device_id"].fillna("").str.lower().str.contains(q) |
            filtered_df["record_id"].str.lower().str.contains(q)
        ]
    if sel_bldg != "All Buildings":
        filtered_df = filtered_df[filtered_df["location_code"] == sel_bldg]
    if sel_month != "All Months":
        filtered_df = filtered_df[filtered_df["billing_month"] == sel_month]
    if sel_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["status"] == sel_status]

    # Metrics summary header
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin:0.75rem 0; font-size:0.85rem; color:#64748B;">
        <div>Showing <strong>{min(len(filtered_df), page_size)}</strong> of <strong>{len(filtered_df):,}</strong> records</div>
        <div>Total Value: <strong>{format_inr(filtered_df['total_revenue'].sum(), compact=True)}</strong></div>
    </div>
    """, unsafe_allow_html=True)

    # Format dataframe for presentation
    display_df = filtered_df.head(page_size).copy()
    display_df["Water Revenue"] = display_df["water_revenue"].apply(lambda v: format_inr(v))
    display_df["Rental Revenue"] = display_df["rental_revenue"].apply(lambda v: format_inr(v))
    display_df["Total Revenue"] = display_df["total_revenue"].apply(lambda v: format_inr(v))

    display_df = display_df.rename(columns={
        "record_id": "Record ID",
        "apartment_id": "Apartment",
        "location_code": "Building / Cluster",
        "water_device_id": "Water Meter",
        "rental_device_id": "Rental Controller",
        "billing_month": "Period",
        "status": "Status"
    })

    cols_to_show = ["Record ID", "Apartment", "Building / Cluster", "Period", "Water Meter", "Water Revenue", "Rental Controller", "Rental Revenue", "Total Revenue", "Status"]
    st.dataframe(display_df[cols_to_show], use_container_width=True)
