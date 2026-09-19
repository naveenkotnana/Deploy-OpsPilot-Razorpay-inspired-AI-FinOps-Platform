# -*- coding: utf-8 -*-
"""Audit Trail View — Immutable Enterprise Traceability Ledger."""
import pandas as pd
import streamlit as st

from dashboard.components import api_call, render_top_header


def render_audit(role: str):
    """Render the cryptographic-style audit ledger."""
    render_top_header(
        title="Audit & Traceability Ledger",
        subtitle="Immutable logging of all AI agent tool calls, latencies, input hashes, and human authorizations",
        role=role
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        wid_filter = st.text_input("Filter by Workflow ID", placeholder="e.g. WF-...")
    with c2:
        limit = st.selectbox("Record Limit", [50, 100, 200, 500], index=1)

    query_str = f"?limit={limit}"
    if wid_filter:
        query_str += f"&workflow_id={wid_filter.strip()}"

    rows, err = api_call("GET", f"/audit{query_str}")
    if err:
        st.error(err)
        return

    if rows:
        df = pd.DataFrame(rows)
        df_disp = df.rename(columns={
            "audit_id": "Audit ID",
            "workflow_id": "Workflow",
            "user_id": "User",
            "agent_node": "Agent Node",
            "tool_name": "Tool Invocation",
            "input_hash": "Input Hash",
            "latency_ms": "Latency (ms)",
            "result_status": "Status",
            "timestamp": "Timestamp"
        })
        st.dataframe(df_disp, use_container_width=True)
    else:
        st.info("No audit logs matching query.")
