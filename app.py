import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator • Execution Console",
    page_icon="🥇",
    layout="wide",
)

# -------------------------------------------------
# PREMIUM DARK UI (StakingAI-style)
# -------------------------------------------------
st.markdown(
    """
    <style>
        /* Global background */
        .main {
            background: radial-gradient(circle at top left, #1b1f2b, #050509 60%);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #050509, #111320);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        /* Remove default top padding */
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
        }

        /* Sidebar title */
        .gg-sidebar-title {
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #f4f4f6;
        }
        .gg-sidebar-sub {
            font-size: 0.72rem;
            color: rgba(255,255,255,0.55);
        }

        /* Metric cards */
        .metric-card {
            padding: 0.9rem 1.1rem;
            border-radius: 0.9rem;
            background: radial-gradient(circle at top left, #232634, #0c0f18);
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 14px 30px rgba(0,0,0,0.7);
        }
        .metric-label {
            font-size: 0.75rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.65);
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 0.15rem;
            color: #fdfdfd;
        }
        .metric-sub {
            font-size: 0.7rem;
            margin-top: 0.1rem;
            color: rgba(255,255,255,0.5);
        }

        /* Section titles */
        .section-title {
            font-size: 0.8rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.6);
            margin: 0.4rem 0 0.3rem 0;
        }

        /* Generic block card */
        .block-card {
            padding: 1rem 1.1rem;
            border-radius: 0.9rem;
            background: rgba(8,9,15,0.96);
            border: 1px solid rgba(255,255,255,0.06);
        }

        /* Accent chip */
        .accent-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: linear-gradient(90deg, #ff8c32, #ffb347);
            color: #050509;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        /* Positions table wrapper look */
        .positions-wrapper {
            border-radius: 0.6rem;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
            background: rgba(5,6,12,0.9);
        }

        /* Tiny footer text */
        .gg-footer {
            font-size: 0.65rem;
            color: rgba(255,255,255,0.4);
            margin-top: 0.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# SIDEBAR – ONLY RISK + TOGGLE
# -------------------------------------------------
with st.sidebar:
    st.markdown('<div class="gg-sidebar-title">GOLD GLADIATOR</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="gg-sidebar-sub">Private intraday execution console. '
        'Live MT5 wiring will feed this panel later.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    engine_on = st.toggle("Execution engine active", value=False)

    risk_pct = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        step=0.25,
        value=1.0,
        help="Sizing parameter the engine will use once it is connected to MT5.",
    )

    st.markdown("---")
    st.markdown(
        '<span class="gg-sidebar-sub">'
        'Sidebar will later hold broker, account, and symbol selectors. '
        'For now this is a visual shell only.'
        "</span>",
        unsafe_allow_html=True,
    )

# -------------------------------------------------
# HEADER
# -------------------------------------------------
col_title, col_chip = st.columns([3, 1])

with col_title:
    st.markdown(
        "### 🥇 Gold Gladiator",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<span style='color:rgba(255,255,255,0.72);font-size:0.9rem;'>"
        "Intraday AI execution surface for your New York / London day-trading system."
        "</span>",
        unsafe_allow_html=True,
    )

with col_chip:
    chip_text = "ENGINE • STANDBY"
    if engine_on:
        chip_text = "ENGINE • ARMED"
    st.markdown(
        f"<div style='text-align:right; margin-top:0.35rem;'><span class='accent-chip'>{chip_text}</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# -------------------------------------------------
# TOP METRIC STRIP (4 CARDS, STATIC FOR NOW)
# -------------------------------------------------
m1, m2, m3, m4 = st.columns(4)


def metric_card(col, label, value, sub):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value">{value}</div>
              <div class="metric-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


metric_card(
    m1,
    "ACCOUNT BALANCE",
    "—",
    "Will display live MT5 equity once linked.",
)
metric_card(
    m2,
    "NET P/L (SESSION)",
    "—",
    "Realized P/L from today’s executions.",
)
metric_card(
    m3,
    "WIN RATE",
    "—",
    "Rolling win-rate over last 20–50 trades.",
)
metric_card(
    m4,
    "RISK / TRADE",
    f"{risk_pct:.2f}%",
    "User-defined risk parameter.",
)

st.markdown("")

# -------------------------------------------------
# MIDDLE: EQUITY / PERFORMANCE + ENGINE STATUS
# -------------------------------------------------
left, right = st.columns([2.2, 1.0])

with left:
    st.markdown(
        '<div class="section-title">EQUITY / PERFORMANCE</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    # Placeholder equity curve so page is not empty
    # (Replace with real live / historical equity once MT5 is wired)
    horizon = 60  # last 60 bars / trades
    idx = [datetime.now() - timedelta(minutes=5 * i) for i in range(horizon)][::-1]
    equity = pd.DataFrame(
        {
            "Equity": [100_000 + i * 50 for i in range(horizon)]
        },
        index=idx,
    )
    st.line_chart(equity)

    st.markdown(
        "<div class='gg-footer'>"
        "Chart currently displays a static mock equity line. "
        "When the execution engine is connected, this will track real account equity or R-multiple curve."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        '<div class="section-title">ENGINE OVERVIEW</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    status = "ONLINE • ARMED" if engine_on else "OFFLINE • STANDBY"
    color = "#37ff8b" if engine_on else "#ffb347"

    st.markdown(
        f"""
        <div style="font-size:0.85rem; color:rgba(255,255,255,0.72);">
          <span style="font-size:0.8rem; letter-spacing:0.16em; text-transform:uppercase; color:rgba(255,255,255,0.6);">
            EXECUTION STATUS
          </span><br/>
          <span style="font-size:1.0rem; font-weight:600; color:{color};">{status}</span>
          <br/><br/>
          <span style="font-size:0.8rem; color:rgba(255,255,255,0.6);">
            • Reads higher-timeframe structure outside session.<br/>
            • Hunts manipulation into liquidity during your NY / London windows.<br/>
            • Executes using your configured risk % and internal R-targets.<br/>
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# BOTTOM: POSITIONS / RECENT ORDERS GRID (STATIC MOCK)
# -------------------------------------------------
st.markdown(
    '<div class="section-title">OPEN / RECENT POSITIONS</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="block-card positions-wrapper">', unsafe_allow_html=True)

# Static sample table – replace later with live positions from MT5
positions_df = pd.DataFrame(
    [
        ["XAUUSD", "BUY", "NY", "Core Setup v1", "—", "—", "Awaiting engine"],
        ["XAUUSD", "SELL", "LONDON", "Core Setup v1", "—", "—", "Awaiting engine"],
    ],
    columns=["Symbol", "Direction", "Session", "Tag", "Entry", "P/L", "Status"],
)

st.dataframe(
    positions_df,
    hide_index=True,
    use_container_width=True,
)

st.markdown("</div>", unsafe_allow_html=True)
