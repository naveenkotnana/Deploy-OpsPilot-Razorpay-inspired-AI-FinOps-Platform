# -*- coding: utf-8 -*-
"""Razorpay-inspired Fintech Visual Design System for OpsPilot Dashboard."""

RAZORPAY_THEME_CSS = """
<style>
/* Import modern typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Root reset and workspace styling */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #F7F9FC !important;
    color: #0F172A;
}

/* Streamlit main block container */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1440px !important;
}

/* ------------------------------------------------------------- SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #0B1F3A !important;
    border-right: 1px solid #162E50 !important;
}

[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}

[data-testid="stSidebar"] hr {
    border-color: #1E3A5F !important;
    margin: 0.8rem 0 !important;
}

/* Sidebar branding header */
.sidebar-brand-box {
    padding: 0.5rem 0.2rem 1.2rem 0.2rem;
    border-bottom: 1px solid #1E3A5F;
    margin-bottom: 1rem;
}
.sidebar-brand-title {
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF !important;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sidebar-brand-badge {
    font-size: 0.65rem;
    font-weight: 700;
    background: #2F5BFF;
    color: #FFFFFF !important;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
}
.sidebar-brand-sub {
    font-size: 0.75rem;
    color: #94A3B8 !important;
    margin-top: 2px;
}

/* Sidebar section header */
.sidebar-section-header {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B !important;
    margin: 1.2rem 0 0.4rem 0.4rem;
}

/* Sidebar Radio Buttons styling to look like razorpay nav items */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 2px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 0.45rem 0.75rem !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease-in-out !important;
    cursor: pointer !important;
    margin-bottom: 2px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: rgba(255, 255, 255, 0.06) !important;
    color: #FFFFFF !important;
}

/* Active navigation item */
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
[data-testid="stSidebar"] [data-testid="stRadio"] div[aria-checked="true"] {
    background-color: #2F5BFF !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Sidebar user card */
.sidebar-user-card {
    background-color: #122846;
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 0.75rem;
    margin-top: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.sidebar-user-name {
    font-size: 0.82rem;
    font-weight: 600;
    color: #FFFFFF !important;
}
.sidebar-user-role {
    font-size: 0.7rem;
    color: #38BDF8 !important;
    font-weight: 600;
    background: rgba(56, 189, 248, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
}

/* -------------------------------------------------------- TOP HEADER BAR */
.top-header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #E6EAF0;
}
.top-header-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.02em;
    margin: 0;
}
.top-header-subtitle {
    font-size: 0.85rem;
    color: #64748B;
    margin-top: 2px;
}
.top-header-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.8rem;
    color: #64748B;
}
.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background-color: #ECFDF5;
    border: 1px solid #A7F3D0;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #065F46;
}
.live-dot {
    width: 6px;
    height: 6px;
    background-color: #10B981;
    border-radius: 50%;
}

/* ---------------------------------------------------- DATE FILTER ROW */
.filter-bar {
    background-color: #FFFFFF;
    border: 1px solid #E6EAF0;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.75rem;
}

/* ----------------------------------------------------------- KPI CARDS */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
@media (max-width: 1024px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
    .kpi-row { grid-template-columns: 1fr; }
}

.kpi-card {
    background-color: #FFFFFF;
    border: 1px solid #E6EAF0;
    border-top: 3px solid #2F5BFF !important;
    border-radius: 12px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    position: relative;
    min-width: 0;
    overflow: hidden;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
    border-color: #CBD5E1;
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.35rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-value {
    font-size: 1.52rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.2;
    letter-spacing: -0.025em;
    font-family: 'Inter', sans-serif;
    white-space: nowrap !important;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-subtext {
    font-size: 0.74rem;
    color: #64748B;
    margin-top: 0.35rem;
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.trend-up {
    color: #16A34A;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
}
.trend-down {
    color: #DC2626;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
}
.trend-neutral {
    color: #64748B;
    font-weight: 600;
    white-space: nowrap;
}

/* ---------------------------------------------------- FINTECH PANELS */
.fintech-panel {
    background-color: #FFFFFF;
    border: 1px solid #E6EAF0;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.fintech-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #F1F5F9;
}
.fintech-panel-title {
    font-size: 1rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0;
}
.fintech-panel-sub {
    font-size: 0.8rem;
    color: #64748B;
}

/* ------------------------------------------- HORIZONTAL INSIGHT BAR */
.insight-bar-container {
    background-color: #FFFFFF;
    border: 1px solid #E6EAF0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
}
.insight-bar-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
}
.insight-bar-track {
    height: 12px;
    border-radius: 6px;
    display: flex;
    overflow: hidden;
    background-color: #E2E8F0;
    margin-bottom: 0.75rem;
}
.insight-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 1.25rem;
    font-size: 0.8rem;
}
.insight-legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #334155;
}
.insight-legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 2px;
}

/* ----------------------------------------------------------- BADGES */
.fintech-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.badge-critical { background-color: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }
.badge-high     { background-color: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
.badge-medium   { background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
.badge-low      { background-color: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }
.badge-pass     { background-color: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
.badge-fail     { background-color: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }

/* ----------------------------------------------------------- BUTTONS */
.stButton > button, 
button[kind="secondary"],
[data-testid="baseButton-secondary"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.15s ease-in-out !important;
}

.stButton > button:hover, 
button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover {
    background-color: #F8FAFC !important;
    border-color: #2F5BFF !important;
    color: #2F5BFF !important;
}

.stButton > button p,
button[kind="secondary"] p,
[data-testid="baseButton-secondary"] p {
    color: #0F172A !important;
    font-weight: 600 !important;
}

.stButton > button:hover p,
button[kind="secondary"]:hover p,
[data-testid="baseButton-secondary"]:hover p {
    color: #2F5BFF !important;
}

button[kind="primary"],
.stButton > button[kind="primary"],
[data-testid="baseButton-primary"] {
    background-color: #2F5BFF !important;
    color: #FFFFFF !important;
    border: 1px solid #2F5BFF !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(47, 91, 255, 0.3) !important;
}

button[kind="primary"] p,
.stButton > button[kind="primary"] p,
[data-testid="baseButton-primary"] p {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover,
[data-testid="baseButton-primary"]:hover {
    background-color: #1E47E6 !important;
    border-color: #1E47E6 !important;
    color: #FFFFFF !important;
}

/* Streamlit dataframes and tables */
[data-testid="stDataFrame"] {
    border: 1px solid #E6EAF0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* Code and monospaced text */
code, pre, .font-mono {
    font-family: 'JetBrains Mono', monospace !important;
}

/* ------------------------------------------- FORM & INPUT COMPONENT STYLING */
/* Strict light theme for ALL inputs - NO BLACK BOXES */
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="input"] input,
.stTextInput > div > div > input,
.stTextInput input,
input {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    font-family: 'Inter', sans-serif !important;
}

div[data-baseweb="input"] input:focus,
.stTextInput input:focus {
    border-color: #2F5BFF !important;
    box-shadow: 0 0 0 2px rgba(47, 91, 255, 0.2) !important;
}

/* Password reveal icon */
div[data-baseweb="input"] button,
div[data-baseweb="input"] svg {
    color: #64748B !important;
    fill: #64748B !important;
}

/* Form labels - clear visible dark slate */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
label[data-testid="stWidgetLabel"],
.stTextInput label,
.stSelectbox label {
    color: #1E293B !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.01em !important;
}

/* Form Submit Button - Sleek dark pill button matching modern reference */
.stFormSubmitButton > button {
    background-color: #111827 !important;
    color: #FFFFFF !important;
    border: 1px solid #111827 !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 12px rgba(17, 24, 39, 0.2) !important;
    transition: all 0.15s ease-in-out !important;
}
.stFormSubmitButton > button:hover {
    background-color: #1F2937 !important;
    border-color: #1F2937 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(17, 24, 39, 0.25) !important;
}
.stFormSubmitButton > button p {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}

/* Reference-inspired Glassmorphism Login Card Styles */
.login-glass-card {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.95);
    border-radius: 28px;
    padding: 2.25rem 2.25rem 1.75rem 2.25rem;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08), 0 2px 8px rgba(0, 0, 0, 0.02);
    text-align: center;
    margin: 1rem auto;
    max-width: 480px;
}
.login-brand-topbar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 800;
    font-size: 1.15rem;
    color: #0F172A;
    margin-bottom: 1.25rem;
    justify-content: flex-start;
}
.login-avatar-pill {
    width: 48px;
    height: 48px;
    margin: 0 auto 1rem auto;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}
.login-title-text {
    font-size: 1.55rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.025em;
    margin: 0 0 0.35rem 0;
}
.login-sub-text {
    font-size: 0.82rem;
    color: #64748B;
    line-height: 1.45;
    margin: 0 0 1.25rem 0;
}
.login-admin-banner {
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

/* Tabs styling - clear active tab, blue underline, no red */
button[data-baseweb="tab"] {
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    background: transparent !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
}
button[data-baseweb="tab"]:hover {
    color: #0F172A !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #2F5BFF !important;
    font-weight: 700 !important;
}
div[data-baseweb="tab-highlight"],
[data-testid="stTabs"] div[role="tablist"] div[style*="background-color"] {
    background-color: #2F5BFF !important;
}
[data-testid="stTabs"] div[role="tablist"] {
    border-bottom: 1px solid #E2E8F0 !important;
}

/* Selectbox dropdowns - clean white background */
div[data-baseweb="select"],
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #CBD5E1 !important;
    border-radius: 6px !important;
}
div[data-baseweb="select"] span {
    color: #0F172A !important;
    font-weight: 500 !important;
}

/* Expander - clean white surface */
.streamlit-expanderHeader {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
}
.streamlit-expanderContent {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
}
</style>
"""
