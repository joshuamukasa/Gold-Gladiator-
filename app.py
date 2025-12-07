import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
#  GOLD GLADIATOR — PROFESSIONAL EXECUTION DASHBOARD (UI ONLY)
# ============================================================

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide"
)

# -------------------- GLOBAL STYLES --------------------

st.markdown("""
<style>

/* Page background */
body {
    background: radial-gradient(circle at top left, #15161b 0%, #06070c 60%, #000000 100%);
}

/* Remove weird Streamlit top padding */
.block-container {
    padding-top: 0.6rem !important;
}

/* MAIN TITLE */
.gg-title {
    font-size: 1.9rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.1rem;
}

/* SUBTITLE */
.gg-subtitle {
    font-size: 0.9rem;
    color: #a3a7c6;
    margin-bottom: 1rem;
}

/* CARD STYLE */
.gg-card {
    background: linear-gradient(135deg, #171821 0%, #101118 55%, #0b0c11 100%);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 18px 45px rgba(0,0,0,0.6);
}

/* Metric titles */
.gg-label {
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #8f93b2;
    margin-bottom: 0.3rem;
}

/* Metric values */
.gg-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #ffffff;
}

/* Help text */
.gg-sub {
    font-size: 0.78rem;
    color: #8c90a8;
}

/* Section titles */
.gg-section-title {
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #9ca1be;
}

/* Divider */
.gg-divider {
    margin: 0.4rem 0 0.8rem 0;
    height:1px;
    background: rgba(255,255,255,0.06);
}

/* Sidebar look */
[data-testid="stSidebar"] {
    background: radial-gradient(circle at top left, #181924 0%, #05060b 60%, #000000 100%);
    border-right: 1px solid rgba(255,255,255,0.04);
}

</style>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR CONTROLS --------------------

st.sidebar.markdown("### GOLD GLADIATOR")

st.sidebar.markdown("""
<span style="font-size:0.78rem; color:#9da0bb;">
Private intraday AI execution console.<br>
Live MT5 integration will feed performance metrics here.
</span>
""", unsafe_allow_html=True)

# ONLY slider — NO execution toggle
risk_pct = st.sidebar.slider(
    "Risk per trade (%)",
    min_value=0.25,
    max_value=10.0,
    value=1.0,
    step=0.25
)

st.sidebar.markdown("""
<span style="font-size:0.75rem; color:#8689a3;">
This slider controls the system’s trade exposure sizing once MT5 execution is active.
</span>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------

st.markdown("""
<div class="gg-title">GOLD GLADIATOR</div>
<div class="gg-subtitle">
Intraday AI execution surface for your New York & London trading framework.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -------------------- TOP METRICS --------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
<div class="gg-card">
    <div class="gg-label">Account Balance</div>
    <div class="gg-value">—</div>
    <div class="gg-sub">Live MT5 equity once linked</div>
</div>
""", unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="gg-card">
    <div class="gg-label">Net P/L (Session)</div>
    <div class="gg-value">—</div>
    <div class="gg-sub">Today's realized execution only</div>
</div>
""", unsafe_allow_html=True)

with col3:
    st.markdown("""
<div class="gg-card">
    <div class="gg-label">Win Rate</div>
    <div class="gg-value">—</div>
    <div class="gg-sub">Rolling sample results</div>
</div>
""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
<div class="gg-card">
    <div class="gg-label">Risk Per Trade</div>
    <div class="gg-value">{risk_pct:.2f}%</div>
    <div class="gg-sub">System exposure parameter</div>
</div>
""", unsafe_allow_html=True)

# -------------------- PERFORMANCE CHART --------------------

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="gg-card">
  <div class="gg-section-title">Equity / Performance</div>
  <div class="gg-divider"></div>
""", unsafe_allow_html=True)

# Placeholder equity curve until MT5 is connected
def demo_equity_curve(points=80):
    base = 100000
    times = [datetime.utcnow() - timedelta(minutes=5*(points-p)) for p in range(points)]
    curve = []

    equity = base
    for i in range(points):
        equity += (1 if i % 3 else -1) * 120
        curve.append(equity)

    return pd.DataFrame({"Time": times, "Equity": curve})

eq_df = demo_equity_curve()
eq_df = eq_df.set_index("Time")

st.line_chart(eq_df["Equity"])

st.markdown("</div>", unsafe_allow_html=True)

# -------------------- FOOTER --------------------

st.markdown("""
<div style="font-size:0.7rem; color:#6f7390; margin-top:0.6rem;">
Prototype interface only. Live execution feed activates after MT5 integration.
</div>
""", unsafe_allow_html=True)
