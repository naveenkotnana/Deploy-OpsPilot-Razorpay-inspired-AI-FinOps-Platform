# -*- coding: utf-8 -*-
"""Intelligence Analytics View — Full SQL analytics query explorer."""
import pandas as pd
import streamlit as st

from dashboard.components import api_call, format_inr, render_top_header


def render_analytics(role: str):
    """Render the SQL analytics workbench for operations and revenue analysts."""
    render_top_header(
        title="Operations Analytics Workbench",
        subtitle="11 pre-compiled canonical SQL analytical models with bounded row limits and guardrails",
        role=role
    )

    qs_data, err = api_call("GET", "/analytics/queries")
    if err:
        st.error(err)
        return

    queries_list = qs_data.get("queries", []) if qs_data else []

    col_sel, col_btn = st.columns([4, 1])
    with col_sel:
        selected_q = st.selectbox("Analytical Model Query", queries_list, index=0)
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run_clicked = st.button("Run Model", type="primary", use_container_width=True)

    data, err = api_call("GET", f"/revenue?query={selected_q}")
    if err:
        st.error(err)
        return

    rows = data.get("rows", [])
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin:0.75rem 0; font-size:0.8rem; color:#64748B;">
        <span>Query: <strong class="font-mono" style="color:#0F172A;">{selected_q}</strong></span>
        <span>Rows returned: <strong>{len(rows)}</strong> | Execution latency: <strong>{data.get('latency_ms', 1)}ms</strong></span>
    </div>
    """, unsafe_allow_html=True)

    if rows:
        df = pd.DataFrame(rows)
        # Format currency columns
        df_disp = df.copy()
        for c in df_disp.columns:
            if "revenue" in c or "avg" in c or "prev" in c or "delta" in c:
                df_disp[c] = df_disp[c].apply(lambda v: format_inr(v) if pd.notna(v) else "—")
        st.dataframe(df_disp, use_container_width=True)
    else:
        st.info("Query executed successfully. 0 records returned.")
