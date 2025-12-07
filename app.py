import streamlit as st
import pandas as pd
from datetime import datetime

# ===============================
#  GOLD GLADIATOR – CONTROL CENTRE
# ===============================

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CUSTOM CSS (premium look) ----------
st.markdown("""
<style>
/* Global */
body {
    background-color: #05070D;
}
section.main > div {
    padding-top: 0rem;
}

/* Main background + cards */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}
.gold-card {
    background: linear-gradient(135deg, #0B1020 0%, #090C16 60%, #111827 100%);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    border: 1px solid rgba(255, 215, 0, 0.16);
    box-shadow: 0 20px 40px rgba(0,0,0,0.45);
}
.metric-card {
    background: radial-gradient(circle at top left, #1F2933 0%, #05070D 60%);
    border-radius: 16px;
    padding: 1.0rem 1.0rem;
    border: 1px solid rgba(148, 163, 184, 0.35);
}

/* Titles */
h1, h2, h3, h4 {
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: 0.02em;
}

h1 {
    font-weight: 800;
    font-size: 2.4rem;
}

h2 {
    font-weight: 700;
    font-size: 1.4rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: radial-gradient(circle at top left, #020617 0%, #020617 35%, #020617 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.25);
}
.sidebar-title {
    font-size: 1.0rem;
    font-weight: 700;
    color: #E5E7EB;
    margin-bottom: 0.25rem;
}

/* Badges & labels */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid rgba(148, 163, 184, 0.55);
    color: #E5E7EB;
    background: radial-gradient(circle at top left, #00472D 0%, #020617 65%);
}
.badge-pill span.dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #22C55E;
}

/* Tables */
.dataframe tbody tr:hover {
    background-color: rgba(15, 23, 42, 0.8) !important;
}

/* Small text */
.muted {
    color: #9CA3AF;
    font-size: 0.78rem;
}
.muted-strong {
    color: #E5E7EB;
    font-weight: 500;
    font-size: 0.8rem;
}

/* Divider label */
.section-label {
    color: #9CA3AF;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
}

/* Green button look for Streamlit primary */
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #22C55E, #16A34A);
    border-radius: 999px;
    color: #020617;
    font-weight: 700;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ==========================
#  SIDEBAR – CONTROLS
# ==========================
with st.sidebar:
    st.markdown("### ⚙️ Controls")

    st.markdown('<div class="sidebar-title">Symbol</div>', unsafe_allow_html=True)
    symbol = st.selectbox("", ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "US30"], index=0)

    st.markdown('<div class="sidebar-title">Primary timeframe</div>', unsafe_allow_html=True)
    tf = st.selectbox("", ["M5", "M15", "M30", "H1"], index=0)

    st.markdown('<div class="sidebar-title">Session focus</div>', unsafe_allow_html=True)
    session = st.radio(
        "",
        ["London", "New York", "Asia", "All sessions"],
        index=1
    )

    st.markdown("---")
    st.markdown('<span class="section-label">Risk visuals</span>', unsafe_allow_html=True)
    user_risk = st.slider("User risk % (visual only)", 0.25, 20.0, 2.0, 0.25)

    st.markdown("---")
    st.markdown('<span class="section-label">Account view</span>', unsafe_allow_html=True)
    account_mode = st.radio(
        "",
        ["My capital", "Subscriber pool"],
        index=0
    )

    st.markdown("---")
    st.caption("Gold Gladiator Control Centre • Prototype UI\nBackend execution engine to be wired later to MT5 bridge.")

# ==========================
#  HEADER – HERO SECTION
# ==========================
col_logo, col_title, col_badge = st.columns([0.9, 4.2, 2.3])

with col_logo:
    st.markdown("### 🟡")

with col_title:
    st.markdown("#### GOLD GLADIATOR")
    st.markdown(
        "<span class='muted-strong'>Live Day-Trading Performance Dashboard</span>",
        unsafe_allow_html=True
    )

with col_badge:
    st.markdown(
        "<div style='text-align:right; margin-top:0.4rem;'>"
        "<span class='badge-pill'><span class='dot'></span>Engine Monitor Online</span>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("")

# ==========================
#  KPI STRIP – TOP ROW
# ==========================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# --- Dummy values for now (you will later plug in real stats from the AI engine)
current_equity = 25000.00
this_week_pnl = 450.00
winrate_20 = 72.0
open_risk = user_risk  # just to show something tied to the slider

with kpi1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("**Balance**")
    st.markdown(f"<span class='muted-strong'>${current_equity:,.2f}</span>", unsafe_allow_html=True)
    st.markdown("<span class='muted'>Linked MT5 account (read-only in this prototype)</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kpi2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("**Net P/L (This Week)**")
    pnl_color = "#22C55E" if this_week_pnl >= 0 else "#EF4444"
    sign = "+" if this_week_pnl >= 0 else "-"
    st.markdown(
        f"<span class='muted-strong' style='color:{pnl_color};'>{sign}${abs(this_week_pnl):,.2f}</span>",
        unsafe_allow_html=True
    )
    st.markdown("<span class='muted'>Closed trades only</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kpi3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("**Win Rate**")
    st.markdown(
        f"<span class='muted-strong' style='color:#A855F7;'>{winrate_20:.0f}%</span>",
        unsafe_allow_html=True
    )
    st.markdown("<span class='muted'>Last 20 completed trades</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kpi4:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("**Configured Risk / Trade**")
    st.markdown(
        f"<span class='muted-strong' style='color:#FBBF24;'>{open_risk:.2f}%</span>",
        unsafe_allow_html=True
    )
    st.markdown("<span class='muted'>Visual risk control – user adjustable</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ==========================
#  MAIN BODY – TWO COLUMNS
# ==========================
left, right = st.columns([2.1, 1.4])

# ---------- LEFT: LIVE SETUP FEED ----------
with left:
    st.markdown("#### 📡 Live Setup Feed")
    st.markdown(
        "<span class='muted'>Stream of detected intraday opportunities based on your private rule-set.</span>",
        unsafe_allow_html=True
    )

    # Example single row – later this will be filled from your pattern engine output
    now = datetime.utcnow().replace(microsecond=0)
    demo_row = {
        "Time (UTC)": [now],
        "Symbol": [symbol],
        "Primary TF": [tf],
        "Direction": ["BUY"],
        "Engine Tag": ["Prime Setup v1"],
        "State": ["Awaiting execution"],
        "Est. Target (R multiple)": ["4R+"],
    }
    live_df = pd.DataFrame(demo_row)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.dataframe(
        live_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### 📈 Intraday Session View (placeholder)")
    st.markdown(
        "<span class='muted'>Here we’ll later plug in charts / heatmaps showing how your engine behaves across different sessions and time windows.</span>",
        unsafe_allow_html=True
    )

# ---------- RIGHT: PERFORMANCE / ACCOUNT PANEL ----------
with right:
    st.markdown("#### 🧠 Engine Diagnostics")
    st.markdown("<div class='gold-card'>", unsafe_allow_html=True)

    st.markdown("**Strategy Profile**")
    st.markdown(
        "<span class='muted'>Time-window intraday system built around liquidity grabs, structural breaks and confirmation price action.</span>",
        unsafe_allow_html=True
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**Engine Status**")
    st.markdown(
        """
        • Signal quality filter: **STRICT**  
        • Execution mode: **Manual / research** in this prototype  
        • Cloud location: Shared Streamlit workspace  
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**Next upgrades (roadmap)**")
    st.markdown(
        """
        • 🔌 Secure MT5 bridge for live execution  
        • 👥 Multi-user accounts & subscription tiers  
        • 📊 Deeper analytics: equity curves, max drawdown, risk-of-ruin  
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### 📊 Performance Snapshot (mock data)")
    stats = {
        "Total Trades": [0],
        "Wins": [0],
        "Losses": [0],
        "Win Rate %": [0],
        "Best R Multiple": [0],
        "Worst R Multiple": [0],
    }
    stats_df = pd.DataFrame(stats)
    st.dataframe(stats_df, hide_index=True, use_container_width=True)
