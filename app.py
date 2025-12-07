import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
#  GOLD GLADIATOR – DASHBOARD
# ============================

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# --------- SIDEBAR / CONTROL PANEL ---------

with st.sidebar:
    st.markdown("### Control Panel")

    # Only risk slider – user sets, engine uses it later
    risk_pct = st.slider(
        "Configured risk per trade (%)",
        min_value=0.25,
        max_value=5.0,
        value=1.0,
        step=0.25,
    )

    engine_on = st.toggle("Gold Gladiator engine", value=True)

    # Store in session so backend can read later
    st.session_state["risk_pct"] = risk_pct
    st.session_state["engine_on"] = engine_on

    st.markdown("---")
    st.caption("Prototype UI. Execution / MT5 wiring comes next phase.")

# --------- SMALL HELPERS ---------

def get_stats():
    """
    Safely read stats from session_state.
    When backend is not wired, we show placeholders instead of crashing.
    """
    stats = st.session_state.get("gg_stats", {})  # gg_stats is a placeholder key

    def g(key, default="--"):
        return stats.get(key, default)

    return {
        "balance": g("balance"),
        "weekly_pl": g("weekly_pl"),
        "winrate": g("winrate"),
        "trades": g("trades"),
    }


def get_live_setups_df():
    """
    Read live setups DataFrame from session_state.
    Expecting something like columns: time, direction, tag, status, est_R
    """
    df = st.session_state.get("gg_live_setups_df", None)
    if df is None:
        return pd.DataFrame(
            columns=["Time (UTC)", "Direction", "Tag", "Status", "Est. R multiple"]
        )
    return df


def get_equity_curve():
    """
    Equity / PnL curve placeholder.
    Backend can later overwrite st.session_state['gg_equity_curve'] with real data.
    """
    curve = st.session_state.get("gg_equity_curve", None)
    if curve is None:
        # Dummy flat line so chart area doesn’t look empty
        dates = pd.date_range(end=datetime.utcnow(), periods=20, freq="T")
        return pd.DataFrame({"time": dates, "equity": [0] * len(dates)})
    return curve


# --------- HEADER ---------

st.markdown(
    """
    <style>
    .gg-title {
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .gg-subtitle {
        font-size: 14px;
        opacity: 0.75;
        margin-bottom: 1.5rem;
    }
    .gg-card {
        padding: 0.9rem 1.2rem;
        border-radius: 0.9rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.06);
    }
    .gg-label {
        font-size: 11px;
        text-transform: uppercase;
        opacity: 0.7;
        margin-bottom: 0.2rem;
    }
    .gg-value {
        font-size: 20px;
        font-weight: 600;
    }
    .gg-chip-on {
        padding: 0.1rem 0.55rem;
        border-radius: 999px;
        font-size: 10px;
        text-transform: uppercase;
        background: rgba(46, 204, 113, 0.14);
        color: rgb(46, 204, 113);
        border: 1px solid rgba(46, 204, 113, 0.4);
        margin-left: 0.5rem;
    }
    .gg-chip-off {
        padding: 0.1rem 0.55rem;
        border-radius: 999px;
        font-size: 10px;
        text-transform: uppercase;
        background: rgba(231, 76, 60, 0.16);
        color: rgb(231, 76, 60);
        border: 1px solid rgba(231, 76, 60, 0.5);
        margin-left: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="gg-title">GOLD GLADIATOR</div>
    <div class="gg-subtitle">
        Live intraday performance monitor for your private day-trading engine.
    </div>
    """,
    unsafe_allow_html=True,
)

# --------- TOP METRIC ROW ---------

stats = get_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Account balance</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{stats["balance"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Live MT5 equity (once connected).")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Net P/L (this week)</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{stats["weekly_pl"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Closed trades only.")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Win rate</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{stats["winrate"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Based on last 20 completed trades.")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Configured risk / trade</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{risk_pct:.2f}%</div>',
        unsafe_allow_html=True,
    )
    st.caption("UI setting – execution engine will size positions.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# --------- SECOND ROW: LIVE FEED + ENGINE STATUS ---------

col_left, col_right = st.columns([2.2, 1.1])

with col_left:
    st.markdown("#### Live Setup Feed")

    live_df = get_live_setups_df()
    if live_df.empty:
        st.info("Waiting for the first intraday setup from the engine…")
    else:
        st.dataframe(
            live_df,
            use_container_width=True,
            hide_index=True,
        )

with col_right:
    st.markdown("#### Engine Overview")

    conn_label = "ONLINE" if engine_on else "OFFLINE"
    conn_class = "gg-chip-on" if engine_on else "gg-chip-off"

    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="gg-label">Connection</div>
        <div class="gg-value">
            {conn_label}
            <span class="{conn_class}">Status</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Backend wiring to MT5 & execution engine is the next build stage.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Session snapshot</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{stats["trades"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Trades logged today.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# --------- BOTTOM ROW: EQUITY / PERFORMANCE PANEL ---------

st.markdown("#### Equity Curve (prototype view)")

equity_df = get_equity_curve()
if not equity_df.empty:
    equity_df = equity_df.set_index("time")
    st.line_chart(equity_df)
else:
    st.info("Equity curve will appear here once trade history is recorded.")
