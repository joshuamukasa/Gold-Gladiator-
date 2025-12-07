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

# ---------- GLOBAL STYLES ----------

st.markdown(
    """
    <style>
    body {
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .gg-title {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }
    .gg-subtitle {
        font-size: 13px;
        opacity: 0.7;
        margin-bottom: 1.1rem;
    }
    .gg-row {
        margin-bottom: 0.8rem;
    }
    .gg-card {
        padding: 0.9rem 1.1rem;
        border-radius: 0.9rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(0,0,0,0.35));
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 0 18px rgba(0,0,0,0.35);
    }
    .gg-label {
        font-size: 11px;
        text-transform: uppercase;
        opacity: 0.66;
        margin-bottom: 0.05rem;
        letter-spacing: 0.09em;
    }
    .gg-value {
        font-size: 20px;
        font-weight: 600;
    }
    .gg-chip-on {
        padding: 0.12rem 0.6rem;
        border-radius: 999px;
        font-size: 10px;
        text-transform: uppercase;
        background: rgba(46, 204, 113, 0.18);
        color: rgb(46, 204, 113);
        border: 1px solid rgba(46, 204, 113, 0.55);
        margin-left: 0.45rem;
    }
    .gg-chip-off {
        padding: 0.12rem 0.6rem;
        border-radius: 999px;
        font-size: 10px;
        text-transform: uppercase;
        background: rgba(231, 76, 60, 0.18);
        color: rgb(231, 76, 60);
        border: 1px solid rgba(231, 76, 60, 0.55);
        margin-left: 0.45rem;
    }
    .gg-section-title {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- SIDEBAR (minimal, no symbol / TF) ----------

with st.sidebar:
    st.markdown("### Control Panel")

    risk_pct = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        value=1.0,
        step=0.25,
    )

    engine_on = st.toggle("Gold Gladiator engine", value=True)

    st.session_state["risk_pct"] = risk_pct
    st.session_state["engine_on"] = engine_on

# ---------- HELPERS FOR BACKEND DATA ----------

def get_stats():
    s = st.session_state.get("gg_stats", {})
    def g(k, d="--"):
        return s.get(k, d)
    return {
        "balance": g("balance"),
        "weekly_pl": g("weekly_pl"),
        "winrate": g("winrate"),
        "closed_trades": g("closed_trades"),
        "open_trades": g("open_trades"),
    }

def get_live_setups():
    df = st.session_state.get("gg_live_setups_df", None)
    if df is None:
        return pd.DataFrame(
            columns=["Time (UTC)", "Direction", "Tag", "Status", "Est. R multiple"]
        )
    return df

def get_equity_curve():
    curve = st.session_state.get("gg_equity_curve", None)
    if curve is None:
        # flat placeholder so chart space is visible
        idx = pd.date_range(end=datetime.utcnow(), periods=25, freq="T")
        return pd.DataFrame({"time": idx, "equity": [0]*len(idx)})
    return curve

def get_recent_trades():
    df = st.session_state.get("gg_recent_trades_df", None)
    if df is None:
        return pd.DataFrame(
            columns=["Time (UTC)", "Direction", "Result (R)", "Cum. R"]
        )
    return df

# ---------- HEADER ----------

st.markdown(
    """
    <div class="gg-title">GOLD GLADIATOR</div>
    <div class="gg-subtitle">
        Intraday performance console for your private execution engine.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- TOP METRICS ROW ----------

stats = get_stats()

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown('<div class="gg-card gg-row">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Account balance</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{stats["balance"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with m2:
    st.markdown('<div class="gg-card gg-row">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Net P/L (this week)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{stats["weekly_pl"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="gg-card gg-row">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Win rate</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{stats["winrate"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with m4:
    st.markdown('<div class="gg-card gg-row">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Risk / trade</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{risk_pct:.2f}%</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- MID ROW: LIVE FEED + ENGINE STATUS ----------

c1, c2 = st.columns([2.3, 1.2])

with c1:
    st.markdown('<div class="gg-section-title">Live setups</div>', unsafe_allow_html=True)
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    live_df = get_live_setups()
    if live_df.empty:
        st.write("No active setups yet.")
    else:
        st.dataframe(live_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="gg-section-title">Engine status</div>', unsafe_allow_html=True)
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)

    chip_cls = "gg-chip-on" if engine_on else "gg-chip-off"
    chip_txt = "ONLINE" if engine_on else "OFFLINE"

    st.markdown(
        f"""
        <div class="gg-label">Connection</div>
        <div class="gg-value">
            Execution node
            <span class="{chip_cls}">{chip_txt}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="gg-label">Today</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{stats["closed_trades"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Closed trades")

    st.markdown('<div class="gg-label">Open</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gg-value">{stats["open_trades"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Open positions")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------- BOTTOM ROW: EQUITY + RECENT TRADES ----------

b1, b2 = st.columns([1.6, 1.4])

with b1:
    st.markdown('<div class="gg-section-title">Equity curve</div>', unsafe_allow_html=True)
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    eq = get_equity_curve()
    if not eq.empty:
        eq = eq.set_index("time")
        st.line_chart(eq)
    else:
        st.write("Waiting for trade history.")
    st.markdown('</div>', unsafe_allow_html=True)

with b2:
    st.markdown('<div class="gg-section-title">Recent trades</div>', unsafe_allow_html=True)
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    rt = get_recent_trades()
    if rt.empty:
        st.write("No trades logged yet.")
    else:
        st.dataframe(rt, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
