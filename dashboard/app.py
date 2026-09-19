# -*- coding: utf-8 -*-
"""OpsPilot Streamlit Dashboard — Razorpay-inspired Fintech Analytics Command Center.

Synthetic portfolio project. Local Ollama LLM. Zero paid external APIs.
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path when running from dashboard directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# Auto-initialize database schema and demo users for standalone Streamlit Cloud deployments
try:
    from app.db.base import init_db, SessionLocal
    from app.core.security import seed_demo_users
    from app.models import User
    init_db()
    with SessionLocal() as _bootstrap_db:
        if _bootstrap_db.query(User).count() == 0:
            seed_demo_users(_bootstrap_db)
except Exception:
    pass

from dashboard.components import api_call, get_image_base64
from dashboard.styles import RAZORPAY_THEME_CSS
from dashboard.views.analytics import render_analytics
from dashboard.views.anomalies import render_anomalies
from dashboard.views.approvals import render_approvals
from dashboard.views.audit import render_audit
from dashboard.views.data_quality import render_data_quality
from dashboard.views.exceptions import render_exceptions
from dashboard.views.investigation import render_investigation
from dashboard.views.overview import render_overview
from dashboard.views.revenue import render_revenue
from dashboard.views.settings import render_settings
from dashboard.views.transactions import render_transactions

st.set_page_config(
    page_title="OpsPilot — Operations Command Center",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Razorpay-inspired visual styling
st.markdown(RAZORPAY_THEME_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------- Authentication
def login_view():
    """Fintech-styled authentication gateway matching modern SaaS reference design with cloud backdrop."""
    bg_uri = get_image_base64(PROJECT_ROOT / "dashboard" / "login_bg.jpg")
    admin_banner_uri = get_image_base64(PROJECT_ROOT / "dashboard" / "admin_banner.jpg")

    if bg_uri:
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url('{bg_uri}') !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        [data-testid="stSidebar"] {{
            display: none !important;
        }}
        /* Centered floating glassmorphism card */
        div[data-testid="column"]:nth-child(2) > div {{
            background: rgba(255, 255, 255, 0.90) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid rgba(255, 255, 255, 0.95) !important;
            border-radius: 28px !important;
            padding: 2.25rem 2.25rem 1.75rem 2.25rem !important;
            box-shadow: 0 20px 60px rgba(15, 23, 42, 0.09), 0 2px 8px rgba(0, 0, 0, 0.02) !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    # Top-left brand mark
    st.markdown("""
    <div class="login-brand-topbar">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2F5BFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
            <polyline points="2 17 12 22 22 17"></polyline>
            <polyline points="2 12 12 17 22 12"></polyline>
        </svg>
        <span style="font-weight:800; font-size:1.2rem; color:#0F172A; letter-spacing:-0.02em;">OpsPilot</span>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1.1, 1.8, 1.1])
    with col_c:
        st.markdown("""
        <div style="text-align:center;">
            <div class="login-avatar-pill">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0F172A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                    <polyline points="10 17 15 12 10 7"></polyline>
                    <line x1="15" y1="12" x2="3" y2="12"></line>
                </svg>
            </div>
            <div class="login-title-text">Sign in to OpsPilot</div>
            <div class="login-sub-text">Unified AI operations, telemetry monitoring, and financial automation.</div>
        </div>
        """, unsafe_allow_html=True)

        tab_m, tab_a, tab_ad = st.tabs(["Manager Portal", "User / Analyst", "Admin Portal"])

        # 1. MANAGER PORTAL
        with tab_m:
            st.markdown("""
            <div style="padding:0.4rem 0 0.8rem 0; text-align:left;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <strong style="color:#0F172A; font-size:0.92rem;">Operations Manager</strong>
                    <span class="fintech-badge badge-high">LEVEL 2 CLEARANCE</span>
                </div>
                <div style="font-size:0.78rem; color:#64748B; line-height:1.4;">
                    Operational dashboard, exception triage, and action approval authority.
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.form("form_manager"):
                u_m = st.text_input("Username", value="manager", key="u_m")
                p_m = st.text_input("Password", value="manager123", type="password", key="p_m")
                sub_m = st.form_submit_button("Sign In to Manager Portal", use_container_width=True)
                if sub_m:
                    res, err = api_call("POST", "/auth/login", json={"username": u_m, "password": p_m})
                    if err:
                        st.error(err)
                    elif res:
                        st.session_state.update(token=res["access_token"], role=res["role"], user_id=res["user_id"], username=u_m)
                        st.rerun()

        # 2. ANALYST PORTAL
        with tab_a:
            st.markdown("""
            <div style="padding:0.4rem 0 0.8rem 0; text-align:left;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <strong style="color:#0F172A; font-size:0.92rem;">Revenue Operations Analyst</strong>
                    <span class="fintech-badge badge-low">LEVEL 1 CLEARANCE</span>
                </div>
                <div style="font-size:0.78rem; color:#64748B; line-height:1.4;">
                    Telemetry monitoring, SQL model execution, and AI root-cause investigation.
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.form("form_analyst"):
                u_a = st.text_input("Username", value="analyst", key="u_a")
                p_a = st.text_input("Password", value="analyst123", type="password", key="p_a")
                sub_a = st.form_submit_button("Sign In to Analyst Portal", use_container_width=True)
                if sub_a:
                    res, err = api_call("POST", "/auth/login", json={"username": u_a, "password": p_a})
                    if err:
                        st.error(err)
                    elif res:
                        st.session_state.update(token=res["access_token"], role=res["role"], user_id=res["user_id"], username=u_a)
                        st.rerun()

        # 3. ADMINISTRATOR PORTAL WITH GOVERNANCE ILLUSTRATION
        with tab_ad:
            if admin_banner_uri:
                st.markdown(f"""
                <div class="login-admin-banner">
                    <img src="{admin_banner_uri}" style="width:100%; max-height:140px; object-fit:cover; display:block;" />
                </div>
                """, unsafe_allow_html=True)
            st.markdown("""
            <div style="padding:0.2rem 0 0.8rem 0; text-align:left;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <strong style="color:#0F172A; font-size:0.92rem;">Platform Administrator</strong>
                    <span class="fintech-badge badge-critical">LEVEL 3 CLEARANCE</span>
                </div>
                <div style="font-size:0.78rem; color:#64748B; line-height:1.4;">
                    Full platform governance, data pipeline control, and system security.
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.form("form_admin"):
                u_ad = st.text_input("Username", value="admin", key="u_ad")
                p_ad = st.text_input("Password", value="admin123", type="password", key="p_ad")
                sub_ad = st.form_submit_button("Sign In to Admin Portal", use_container_width=True)
                if sub_ad:
                    res, err = api_call("POST", "/auth/login", json={"username": u_ad, "password": p_ad})
                    if err:
                        st.error(err)
                    elif res:
                        st.session_state.update(token=res["access_token"], role=res["role"], user_id=res["user_id"], username=u_ad)
                        st.rerun()

        st.markdown("""
        <div style="margin-top:1.5rem; padding-top:1rem; border-top:1px solid #F1F5F9; font-size:0.75rem; color:#64748B; display:flex; justify-content:center; align-items:center; gap:8px;">
            <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#16A34A;"></span>
            <span>Local Enterprise Engine • Zero External APIs</span>
        </div>
        """, unsafe_allow_html=True)


if "token" not in st.session_state:
    login_view()
    st.stop()

# Current user role and display name
role = st.session_state.get("role", "MANAGER")
username = st.session_state.get("username", "manager")

USER_PROFILES = {
    "manager": {"name": "Senior Operations Manager", "title": "Operations Manager", "clearance": "Level 2 (Approve & Execute)"},
    "analyst": {"name": "Revenue Operations Analyst", "title": "Operations Analyst", "clearance": "Level 1 (View & Investigate)"},
    "admin": {"name": "Lead Platform Administrator", "title": "Platform Admin", "clearance": "Level 3 (Full Governance)"}
}
user_profile = USER_PROFILES.get(username.lower(), {"name": f"User {username}", "title": role, "clearance": role})

# ------------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-box">
        <div class="sidebar-brand-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2F5BFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            OPSPILOT
            <span class="sidebar-brand-badge">PROD</span>
        </div>
        <div class="sidebar-brand-sub">Operations Command Center</div>
    </div>
    """, unsafe_allow_html=True)

    # Clean navigation options
    NAV_PAGES = [
        "Overview",
        "Revenue",
        "Transactions",
        "Exceptions",
        "Anomalies",
        "Analytics",
        "AI Investigation",
        "Approvals",
        "Audit Trail",
        "Data Quality",
        "Settings"
    ]

    target_nav = st.session_state.get("nav_page", "Overview")
    matching_idx = 0
    if target_nav in NAV_PAGES:
        matching_idx = NAV_PAGES.index(target_nav)

    current_page = st.radio(
        "Navigation",
        options=NAV_PAGES,
        index=matching_idx,
        label_visibility="collapsed"
    )

    # User profile and sign-out card with clean name
    st.markdown(f"""
    <div class="sidebar-user-card">
        <div>
            <div class="sidebar-user-name">{user_profile['name']}</div>
            <div class="sidebar-user-role">@{username} · {role}</div>
            <div style="font-size:0.68rem; color:#94A3B8; margin-top:2px;">{user_profile['clearance']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.markdown("""
    <div style="font-size:0.7rem; color:#64748B; margin-top:1.25rem; text-align:center;">
        Synthetic Data • Local Ollama<br>Zero Paid APIs
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------- Page Router
if current_page == "Overview":
    render_overview(role)
elif current_page == "Revenue":
    render_revenue(role)
elif current_page == "Transactions":
    render_transactions(role)
elif current_page == "Exceptions":
    render_exceptions(role)
elif current_page == "Anomalies":
    render_anomalies(role)
elif current_page == "Analytics":
    render_analytics(role)
elif current_page == "AI Investigation":
    render_investigation(role)
elif current_page == "Approvals":
    render_approvals(role)
elif current_page == "Audit Trail":
    render_audit(role)
elif current_page == "Data Quality":
    render_data_quality(role)
elif current_page == "Settings":
    render_settings(role)
