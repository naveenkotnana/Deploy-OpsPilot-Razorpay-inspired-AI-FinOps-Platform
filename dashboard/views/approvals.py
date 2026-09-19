# -*- coding: utf-8 -*-
"""Approval Center View — Human-in-the-loop Governance and RBAC Authorization."""
import pandas as pd
import streamlit as st

from dashboard.components import api_call, render_top_header


def render_approvals(role: str):
    """Render the approval center for operational decisions."""
    render_top_header(
        title="Approval Center",
        subtitle="Human-in-the-loop governance: Strict RBAC verification before sensitive remediation actions",
        role=role
    )

    is_authorized = role.upper() in ("MANAGER", "ADMIN")

    if not is_authorized:
        st.markdown("""
        <div style="background:#FEF2F2; border:1px solid #FCA5A5; border-radius:8px; padding:1rem 1.25rem; margin-bottom:1.5rem;">
            <strong style="color:#B91C1C;">🔒 Clearance Notice:</strong>
            <span style="color:#991B1B; font-size:0.85rem; margin-left:6px;">
                Your current persona (<strong>ANALYST</strong>) has permission to investigate, but lacks authorization to approve. Approval actions will be rejected by the backend. Switch to <strong>MANAGER</strong> or <strong>ADMIN</strong> in Settings to test approval workflows.
            </span>
        </div>
        """, unsafe_allow_html=True)

    wid_default = st.session_state.get("last_workflow", "")
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E6EAF0; border-radius:10px; padding:1.25rem; margin-bottom:1.5rem;">
        <h3 style="font-size:1rem; font-weight:700; color:#0F172A; margin:0 0 0.5rem 0;">Authorize or Reject Workflow Action</h3>
        <div style="font-size:0.8rem; color:#64748B; margin-bottom:1rem;">Inspect pending workflow state and record a binding human authorization decision:</div>
    """, unsafe_allow_html=True)

    wid = st.text_input("Workflow ID", value=wid_default, placeholder="WF-...")
    if wid:
        wf, err = api_call("GET", f"/workflows/{wid}")
        if err:
            st.error(f"Workflow lookup failed: {err}")
        elif wf:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Workflow Status", wf.get("status", "UNKNOWN"))
            with c2:
                st.metric("Approval Status", wf.get("approval_status", "UNKNOWN"))
            with c3:
                st.metric("Proposed Action", wf.get("final_action") or "create_incident")

            st.markdown("<h4 style='font-size:0.9rem; font-weight:700; margin:1rem 0 0.5rem 0;'>Recommended Action Payload:</h4>", unsafe_allow_html=True)
            st.json(wf.get("recommendation", {}))

            with st.expander("▶ Inspect Full Evidence Bundle (Grounding Check)"):
                st.json(wf.get("evidence", {}))

            reason = st.text_input("Decision Justification Note", value="Approved for operational execution")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Approve & Execute Action", type="primary", use_container_width=True):
                    res, err = api_call("POST", f"/workflows/{wid}/approve", json={"reason": reason})
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Action APPROVED! {res.get('action_result', '')}")
                        st.rerun()

            with btn_col2:
                if st.button("Reject Action", use_container_width=True):
                    res, err = api_call("POST", f"/workflows/{wid}/reject", json={"reason": reason})
                    if err:
                        st.error(err)
                    else:
                        st.warning("Action REJECTED. No remediation executed.")
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Executed Incidents / Remediation Ledger
    st.markdown("<h3 style='font-size:1rem; font-weight:700; color:#0F172A; margin:1.5rem 0 0.5rem 0;'>Executed Operational Actions</h3>", unsafe_allow_html=True)
    inc_data, _ = api_call("GET", "/incidents")
    if inc_data:
        df_inc = pd.DataFrame(inc_data)
        st.dataframe(df_inc, use_container_width=True)
    else:
        st.info("No approved remediation actions executed yet.")
