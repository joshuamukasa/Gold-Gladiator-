import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
#  GOLD GLADIATOR  –  DASHBOARD
# ============================

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- GLOBAL STYLE ----------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    /* main background */
    .stApp {
        background: radial-gradient(circle at top left, #111827 0, #020617 40%, #020617 100%);
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    /* generic card style */
    .gg-card {
        border-radius: 14px;
        padding: 1rem 1.25rem;
        background: linear-gradient(145deg, #020617, #020617);
        border: 1px solid rgba(148, 163, 184, 0.23);
        box-shadow: 0 18px 40px rgba(0,0,0,0.65);
    }
    .gg-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        background: linear-gradient(90deg, #22c55e33, #22c55e10);
        border: 1px solid #22c55e55;
        color: #bbf7d0;
    }
    .gg-metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #9ca3af;
        letter-spacing: 0.12em;
        margin-bottom: 0.25rem;
    }
    .gg-metric-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f9fafb;
    }
    .gg-metric-sub {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.15rem;
    }
    hr.gg-divider {
        border: none;
        border-top: 1px solid rgba(31, 41, 55, 1);
        margin: 1.25rem 0 1.2rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============= SIDEBAR =============
with st.sidebar:
    st.markdown("### Control Panel")

    # user-defined risk and reward – only visual for now
    risk_per_trade = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=5.0,
        value=2.0,
        step=0.25,
    )

    tp_multiple = st.slider(
        "Target multiple (R)",
        min_value=1.0,
        max_value=10.0,
        value=4.0,
        step=0.5,
    )

    st.markdown("---")

    st.markdown(
        """
        **Engine mode:**  
        Designed for *fully automated* execution from the cloud.  
        This dashboard prototype focuses on monitoring, not live trading yet.
        """
    )

# ============= HEADER =============
st.markdown(
    """
    <div class="gg-card" style="margin-bottom: 1.2rem;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1.2rem;">
        <div>
          <div class="gg-pill">
            <span>🛡️</span>
            <span>Gold Gladiator</span>
          </div>
          <h1 style="margin:0.55rem 0 0.15rem 0; font-size:1.8rem; font-weight:700; color:#f9fafb;">
            Live Strategy Engine Dashboard
          </h1>
          <p style="margin:0.25rem 0 0 0; font-size:0.9rem; color:#9ca3af; max-width:540px;">
            Intraday system built around liquidity grabs, structural breaks and price-action confirmation
            inside predefined time windows.
          </p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============= TOP METRICS =============
# NOTE: everything is neutral / zero until connected to real trade data.
stats = {
    "balance": None,
    "net_pl_week": None,
    "win_rate": None,
    "risk_per_trade": risk_per_trade,
}

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="gg-card">
          <div class="gg-metric-label">Balance</div>
          <div class="gg-metric-value">{'—' if stats['balance'] is None else f"${stats['balance']:,.2f}"}</div>
          <div class="gg-metric-sub">Will display from linked MT5 account</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="gg-card">
          <div class="gg-metric-label">Net P/L (This Week)</div>
          <div class="gg-metric-value">{'—' if stats['net_pl_week'] is None else f"${stats['net_pl_week']:,.2f}"}</div>
          <div class="gg-metric-sub">Closed trades only – coming from live engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    winrate_display = "—" if stats["win_rate"] is None else f"{stats['win_rate']:.1f}%"
    st.markdown(
        f"""
        <div class="gg-card">
          <div class="gg-metric-label">Win Rate</div>
          <div class="gg-metric-value">{winrate_display}</div>
          <div class="gg-metric-sub">Rolling sample of last N trades</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="gg-card">
          <div class="gg-metric-label">Configured Risk / Trade</div>
          <div class="gg-metric-value">{risk_per_trade:.2f}%</div>
          <div class="gg-metric-sub">User-defined – applied by execution engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="gg-divider">', unsafe_allow_html=True)

# ============= LIVE SETUP FEED + ENGINE PROFILE =============
left, right = st.columns([1.7, 1.3])

with left:
    st.markdown(
        """
        <div class="gg-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
            <div style="font-size:1.1rem; font-weight:600;">Live Setup Feed</div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    # placeholder – no fake rows, just empty table until engine pushes data
    columns = ["Time (UTC)", "Direction", "Setup Tag", "Status", "Planned TP (R)"]
    live_setups = pd.DataFrame(columns=columns)

    if live_setups.empty:
        st.info(
            "No live setups detected yet. "
            "When the Gold Gladiator engine is connected, new opportunities will stream here in real time."
        )
    else:
        st.dataframe(
            live_setups.style.hide(axis="index"),
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        """
        <div class="gg-card">
          <div style="font-size:1.05rem; font-weight:600; margin-bottom:0.5rem;">
            Engine Diagnostics
          </div>
          <div style="font-size:0.8rem; text-transform:uppercase; color:#9ca3af; letter-spacing:0.12em; margin-bottom:0.4rem;">
            Strategy Profile
          </div>
          <ul style="font-size:0.9rem; color:#d1d5db; padding-left:1.1rem; margin-top:0;">
            <li>Reads overall structure and key liquidity levels first (look left).</li>
            <li>Waits for manipulation leg into liquidity inside predefined time windows.</li>
            <li>Requires strong displacement away from that liquidity plus confirmation on the execution timeframe.</li>
            <li>Entry and management are based on user-defined risk % and target R-multiple.</li>
          </ul>
          <div style="margin-top:0.8rem; font-size:0.8rem; color:#9ca3af;">
            This dashboard is ready for a trade-logging backend.<br>
            Once your execution engine saves trades, win-rate and P/L stats will be shown automatically.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============= TRADE LOG PLACEHOLDER =============
st.markdown('<hr class="gg-divider">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="gg-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <div style="font-size:1.0rem; font-weight:600;">Recent Trades (log)</div>
        <div style="font-size:0.8rem; color:#9ca3af;">Backend not wired yet – waiting for execution data</div>
      </div>
    """,
    unsafe_allow_html=True,
)

trade_log = pd.DataFrame(
    columns=["Time (UTC)", "Direction", "Result (R)", "Comment"]
)

if trade_log.empty:
    st.caption("When the AI is executing and logging trades, they will appear here.")
else:
    st.dataframe(trade_log.style.hide(axis="index"), use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
