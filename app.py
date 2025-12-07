import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================
# GOLD GLADIATOR – CLIENT DASHBOARD (UI)
# =========================================

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# ---------- BASIC STYLING (premium dark look) ----------
st.markdown(
    """
    <style>
        .main {
            background: radial-gradient(circle at top left, #151821, #05060a);
            color: #f5f5f7;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* hide default footer & menu */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* metric cards */
        .gg-card {
            background: linear-gradient(145deg, #141824, #0a0b11);
            border-radius: 14px;
            padding: 14px 18px;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.02),
                        0 18px 35px rgba(0,0,0,0.65);
        }
        .gg-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #9da3b4;
        }
        .gg-value {
            font-size: 1.4rem;
            font-weight: 600;
            color: #f5f5f7;
        }
        .gg-sub {
            font-size: 0.7rem;
            color: #7d8292;
        }

        /* section titles */
        .gg-section-title {
            font-size: 1.0rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #e5e7f0;
        }
        .gg-section-sub {
            font-size: 0.78rem;
            color: #8b90a1;
        }

        .gg-pill-green {
            display:inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            background: rgba(46, 204, 113, 0.12);
            color: #2ecc71;
            font-size: 0.7rem;
        }
        .gg-pill-red {
            display:inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            background: rgba(231, 76, 60, 0.12);
            color: #e74c3c;
            font-size: 0.7rem;
        }

        /* tables */
        .dataframe tbody tr:hover {
            background-color: rgba(255,255,255,0.03);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================= SIDEBAR CONTROLS =================
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")

    symbol = st.selectbox("Symbol", ["XAUUSD"], index=0)
    timeframe = st.selectbox("Execution timeframe", ["M5"], index=0)

    risk_pct = st.slider("Configured risk per trade (%)",
                         min_value=0.25, max_value=5.0, step=0.25, value=1.0)

    engine_state = st.toggle("Gold Gladiator engine", value=True)

    st.markdown("---")
    st.caption(
        "Prototype dashboard UI. Live execution + MT5 link will be wired into the "
        "engine later – this screen is focused on **monitoring performance**."
    )

# ================= HEADER =================
st.markdown("## 🦾 GOLD GLADIATOR")

st.markdown(
    """
    <span style="font-size:0.9rem;color:#a1a6b8;">
    Live intraday performance monitor for your private day-trading engine.
    </span>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# ================= TOP STATS STRIP =================
col_a, col_b, col_c, col_d = st.columns(4)

# NOTE: these are placeholders until we plug in real trade history.
# To avoid fake numbers, keep them neutral.
with col_a:
    st.markdown(
        """
        <div class="gg-card">
            <div class="gg-label">Account Balance</div>
            <div class="gg-value">--</div>
            <div class="gg-sub">Waiting for MT5 connection</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_b:
    st.markdown(
        """
        <div class="gg-card">
            <div class="gg-label">Net P/L (This Week)</div>
            <div class="gg-value">--</div>
            <div class="gg-sub">Closed trades only</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_c:
    # we can show live winrate from backend later; for now neutral
    st.markdown(
        """
        <div class="gg-card">
            <div class="gg-label">Win Rate</div>
            <div class="gg-value">--</div>
            <div class="gg-sub">Based on last 20 completed trades</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_d:
    st.markdown(
        f"""
        <div class="gg-card">
            <div class="gg-label">Configured Risk / Trade</div>
            <div class="gg-value">{risk_pct:.2f}%</div>
            <div class="gg-sub">Visual setting – execution engine decides sizing</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# ================= MAIN BODY =================
left, right = st.columns([1.4, 1.0])

# ------- LEFT: LIVE SETUP FEED -------
with left:
    st.markdown(
        '<div class="gg-section-title">Live Setup Feed</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gg-section-sub">Stream of current intraday opportunities detected by the engine.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Placeholder row – later this will be real-time from backend / MT5 logs
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    setups_df = pd.DataFrame(
        [
            {
                "Time (UTC)": now_str,
                "Direction": "BUY",
                "Tag": "Core Setup v1",
                "Status": "Waiting for confirmation",
                "Est. Target (R)": "4R+",
            }
        ]
    )

    st.dataframe(
        setups_df,
        use_container_width=True,
        hide_index=True,
    )

# ------- RIGHT: ENGINE STATUS + SNAPSHOT -------
with right:
    st.markdown(
        '<div class="gg-section-title">Engine Overview</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gg-section-sub">High-level status of the Gold Gladiator engine.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    status_label = "Online" if engine_state else "Paused"

    st.markdown(
        f"""
        <div class="gg-card">
            <div class="gg-label">Connection</div>
            <div class="gg-value" style="margin-bottom:4px;">{status_label}</div>
            <div class="gg-sub">
                Symbol: {symbol} · Execution TF: {timeframe}
            </div>
            <div style="margin-top:10px;">
                <span class="gg-pill-green">Backend wiring: pending</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.markdown(
        '<div class="gg-section-title">Session Snapshot</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gg-section-sub">Quick view of today\'s trade log once the engine starts saving data.</div>',
        unsafe_allow_html=True,
    )

    # Empty performance placeholder – will be replaced with real charts
    perf_df = pd.DataFrame(
        {
            "Metric": ["Trades Today", "Wins", "Losses", "Max Drawdown (R)", "Best Trade (R)"],
            "Value": ["--", "--", "--", "--", "--"],
        }
    )
    st.table(perf_df)

# Footer hint (small)
st.markdown("")
st.caption(
    "Next step: hook this UI to your real AI engine / MT5 trade log so balance, P/L, win rate "
    "and setup feed are driven by live data instead of placeholders."
)
