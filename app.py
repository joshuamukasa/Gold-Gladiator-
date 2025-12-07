import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --------------------------------------------------
# GOLD GLADIATOR – EXECUTION DASHBOARD (UI SHELL)
# --------------------------------------------------

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# ---------- GLOBAL CSS (INCLUDING TITLE FIX) ----------
st.markdown(
    """
<style>
/* Remove excess top padding so title is not halfway down */
.block-container {
    padding-top: 0.6rem !important;
}

/* Tighten header margins so hero title sits near the top */
h1, h2, h3 {
    margin-top: 0rem !important;
    padding-top: 0rem !important;
}

/* Base page background */
body {
    background: radial-gradient(circle at top left, #15161b 0, #050608 55%, #000000 100%) !important;
}

/* Card look for top metrics & panels */
.gg-card {
    background: linear-gradient(135deg, #171821 0%, #101118 55%, #0b0c11 100%);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    border: 1px solid rgba(255, 255, 255, 0.04);
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.65);
}

/* Metric title */
.gg-label {
    font-size: 0.70rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #8f93b2;
    margin-bottom: 0.3rem;
}

/* Metric main value */
.gg-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: #ffffff;
}

/* Secondary text */
.gg-sub {
    font-size: 0.78rem;
    color: #8c90a8;
}

/* Hero row */
.gg-hero {
    margin-top: -0.3rem !important;  /* pulls everything a bit higher */
    margin-bottom: 0.7rem;
}

/* Section headings */
.gg-section-title {
    font-size: 0.78rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #9ea3c7;
    margin-bottom: 0.35rem;
}

/* Thin divider line */
.gg-divider {
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    margin: 0.35rem 0 0.75rem 0;
}

/* Equity chart container */
.gg-chart-box {
    height: 260px;
}

/* Engine overview bullet list */
.gg-bullets ul {
    padding-left: 1.1rem;
    margin-bottom: 0.3rem;
}
.gg-bullets li {
    font-size: 0.80rem;
    color: #c4c7dd;
    margin-bottom: 0.3rem;
}

/* Sidebar tweaks */
[data-testid="stSidebar"] {
    background: radial-gradient(circle at top left, #181924 0, #05060b 60%, #000000 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.04);
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- SIDEBAR (CONTROL PANEL) ----------

st.sidebar.markdown("### GOLD GLADIATOR")
st.sidebar.markdown(
    "<span style='font-size:0.8rem; color:#9da0bb;'>"
    "Private intraday execution console. Live MT5 wiring will feed this panel later."
    "</span>",
    unsafe_allow_html=True,
)

engine_active = st.sidebar.toggle("Execution engine active", value=False)

risk_pct = st.sidebar.slider(
    "Risk per trade (%)",
    min_value=0.25,
    max_value=10.0,
    value=1.0,
    step=0.25,
)

st.sidebar.markdown(
    "<span style='font-size:0.78rem; color:#8689a3;'>"
    "This slider controls your risk parameter that the execution engine will use."
    "</span>",
    unsafe_allow_html=True,
)

# ---------- MAIN LAYOUT ----------

# Fake placeholders for now – to be wired to MT5 later
account_balance = None   # when live: float or Decimal
session_pl = None        # realized P/L for current session
win_rate = None          # last N trades

# Hero section
with st.container():
    st.markdown(
        """
<div class="gg-hero">
  <h1 style="font-size:1.4rem; font-weight:700; color:#ffffff; margin-bottom:0.15rem;">
    🥇 GOLD GLADIATOR
  </h1>
  <p style="font-size:0.85rem; color:#a5a8c4; margin-bottom:0.2rem;">
    Intraday AI execution surface for your New York / London day-trading system.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

# ----- Top metric cards -----
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
<div class="gg-card">
  <div class="gg-label">ACCOUNT BALANCE</div>
  <div class="gg-value">{'--' if account_balance is None else f"${account_balance:,.2f}"}</div>
  <div class="gg-sub">Will display live MT5 equity once linked.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
<div class="gg-card">
  <div class="gg-label">NET P/L (SESSION)</div>
  <div class="gg-value">{'--' if session_pl is None else f"${session_pl:,.2f}"}</div>
  <div class="gg-sub">Realized P/L from today's execution only.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with col3:
    win_text = "--" if win_rate is None else f"{win_rate:.1f}%"
    st.markdown(
        f"""
<div class="gg-card">
  <div class="gg-label">WIN RATE</div>
  <div class="gg-value">{win_text}</div>
  <div class="gg-sub">Rolling win-rate over last 20–50 trades.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
<div class="gg-card">
  <div class="gg-label">RISK / TRADE</div>
  <div class="gg-value">{risk_pct:.2f}%</div>
  <div class="gg-sub">User-defined risk parameter used by execution engine.</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("")  # small vertical space

# ----- Middle row: Equity curve + Engine overview -----
left, right = st.columns([2.2, 1.3])

# Simple placeholder equity curve using a dummy series
def demo_equity_curve(n_points: int = 60):
    base = 100_000
    times = [datetime.utcnow() - timedelta(minutes=5 * (n_points - i)) for i in range(n_points)]
    # small synthetic fluctuations
    pnl = pd.Series([0])
    for i in range(1, n_points):
        pnl.loc[i] = pnl.loc[i - 1] + 100 * ((-1) ** i) * 0.3
    equity = base + pnl
    df = pd.DataFrame({"time": times, "equity": equity.values})
    return df

with left:
    st.markdown(
        """
<div class="gg-card gg-chart-box">
  <div class="gg-section-title">EQUITY / PERFORMANCE</div>
  <div class="gg-divider"></div>
""",
        unsafe_allow_html=True,
    )

    eq_df = demo_equity_curve()
    eq_df = eq_df.set_index("time")
    st.line_chart(eq_df["equity"])
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    status_text = "ONLINE" if engine_active else "OFFLINE – STANDBY"
    status_color = "#11c76f" if engine_active else "#ffb347"

    st.markdown(
        f"""
<div class="gg-card">
  <div class="gg-section-title">ENGINE OVERVIEW</div>
  <div class="gg-divider"></div>

  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
    <div>
      <div style="font-size:0.78rem; color:#8f93b5; text-transform:uppercase; letter-spacing:0.13em;">EXECUTION STATUS</div>
      <div style="font-size:0.95rem; font-weight:700; color:{status_color}; margin-top:0.08rem;">
        {status_text}
      </div>
    </div>
    <div style="font-size:0.78rem; color:#9a9ec0; text-align:right;">
      Risk/trade: <span style="font-weight:600; color:#ffffff;">{risk_pct:.2f}%</span>
    </div>
  </div>

  <div class="gg-bullets">
    <ul>
      <li>Reads overall structure and key liquidity levels before your time windows.</li>
      <li>Tracks manipulation into liquidity during NY / London intraday periods.</li>
      <li>Uses confirmations on your execution timeframe for entries & exits.</li>
      <li>Position sizing driven entirely by your configured risk percentage.</li>
    </ul>
  </div>

  <div style="font-size:0.72rem; color:#777b97; margin-top:0.35rem;">
    Backend trade-logging + MT5 link will write live stats into this panel in the next phase.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# ----- Bottom spacer / future sections -----
st.markdown("")
st.markdown(
    "<div style='font-size:0.72rem; color:#656981; margin-top:0.3rem;'>"
    "Prototype UI only. Next step: wire MT5 data + full execution engine using your time-window strategy."
    "</div>",
    unsafe_allow_html=True,
)
