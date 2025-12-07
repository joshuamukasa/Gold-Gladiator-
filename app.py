import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
#  GOLD GLADIATOR – DASHBOARD
# ============================

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
    page_icon="🛡️"
)

# ---- Custom CSS for a more "QuantFlow" / hedge-fund look ----
st.markdown(
    """
    <style>
        /* Dark background */
        .stApp {
            background: #050910;
            color: #e5e7eb;
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #070d16;
            border-right: 1px solid #1f2933;
        }

        /* Titles */
        h1, h2, h3 {
            color: #f9fafb;
        }

        /* Metric cards */
        div[data-testid="metric-container"] {
            background-color: #0b1220;
            border-radius: 14px;
            padding: 16px 20px;
            border: 1px solid #1f2937;
            box-shadow: 0 8px 20px rgba(0,0,0,0.45);
        }

        /* Tables */
        table {
            border-radius: 10px;
            overflow: hidden;
        }
        thead tr {
            background-color: #0b1220 !important;
        }
        tbody tr:nth-child(even) {
            background-color: #050910 !important;
        }

        /* Section cards */
        .section-card {
            background-color: #050b13;
            border-radius: 16px;
            padding: 18px 22px;
            border: 1px solid #1f2937;
            box-shadow: 0 8px 22px rgba(0,0,0,0.55);
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .subtext {
            font-size: 0.8rem;
            color: #9ca3af;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================
#  HELPER: LOAD TRADES
# ============================

@st.cache_data
def load_trades() -> pd.DataFrame:
    """
    Load trades_log.csv if present.
    If missing, create a small demo set so the UI doesn't break.
    Expected columns (you can change later):
      time, symbol, timeframe, direction, setup, status, r_multiple, result
    """
    try:
        df = pd.read_csv("trades_log.csv")
    except Exception:
        # Demo data so the dashboard always shows something
        demo = [
            {
                "time": "2025-12-05 10:15",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "direction": "BUY",
                "setup": "M15 Sweep + M5 Engulf",
                "status": "Completed",
                "r_multiple": 4.0,
                "result": "win",
            },
            {
                "time": "2025-12-05 12:30",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "direction": "SELL",
                "setup": "M15 Sweep + M5 Engulf",
                "status": "Completed",
                "r_multiple": -1.0,
                "result": "loss",
            },
            {
                "time": "2025-12-05 15:05",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "direction": "BUY",
                "setup": "M15 Sweep + M5 Engulf",
                "status": "Completed",
                "r_multiple": 3.0,
                "result": "win",
            },
        ]
        df = pd.DataFrame(demo)

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])

    return df


def compute_stats(df: pd.DataFrame, starting_balance: float = 25000.0):
    total = len(df)
    wins = (df.get("result", "") == "win").sum()
    losses = (df.get("result", "") == "loss").sum()
    winrate = (wins / total * 100) if total > 0 else 0.0

    # If you don't have r_multiple yet, treat missing as 0
    r_mult = df.get("r_multiple", pd.Series([0] * total))
    total_R = r_mult.sum()

    # For now we pretend each 1R = 1% of balance
    net_profit = starting_balance * (total_R / 100.0)
    equity = starting_balance + net_profit

    return {
        "total_trades": total,
        "wins": int(wins),
        "losses": int(losses),
        "winrate": winrate,
        "total_R": float(total_R),
        "starting_balance": starting_balance,
        "net_profit": net_profit,
        "equity": equity,
    }


def build_equity_curve(df: pd.DataFrame, base_balance: float = 25000.0):
    """Very simple equity curve based on cumulative R."""
    if "r_multiple" not in df.columns:
        return pd.DataFrame()

    df_sorted = df.sort_values("time").copy()
    df_sorted["cum_R"] = df_sorted["r_multiple"].cumsum()
    df_sorted["equity"] = base_balance * (1 + df_sorted["cum_R"] / 100.0)
    curve = df_sorted[["time", "equity"]].set_index("time")
    return curve


# ============================
#  SIDEBAR – CONTROLS
# ============================

with st.sidebar:
    st.markdown("### Controls")

    symbol = st.selectbox("Symbol", ["XAUUSD", "EURUSD", "GBPUSD"])
    timeframe = st.selectbox("Timeframe", ["M5", "M15", "M30", "H1"])

    user_risk = st.slider("User risk % (visual only)", 0.5, 20.0, 2.0, step=0.5)

    st.markdown("---")
    st.markdown("⚠️ **This is NOT an EA/Bot**")
    st.caption("Signals are observational only. Execution stays 100% manual.")

# ============================
#  MAIN LAYOUT
# ============================

st.title("🛡️ Gold Gladiator")
st.subheader("Live Day-Trading Performance Dashboard")

st.markdown(
    """
This dashboard lets you:

- Monitor your strategy’s live setups  
- Track wins, losses and overall performance  
- View intraday behaviour across different sessions  

**Note:** Signals are for observation and research only.  
Execution always stays 100% manual.
"""
)

# ---- Load data + stats ----
trades_df = load_trades()
stats = compute_stats(trades_df)

# ============================
#  TOP METRIC CARDS
# ============================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Balance",
        value=f"${stats['equity']:,.2f}",
        delta=f"${stats['net_profit']:,.2f}",
    )

with col2:
    st.metric(
        label="Net Profit",
        value=f"${stats['net_profit']:,.2f}",
        delta=f"{stats['total_R']:.1f} R total",
    )

with col3:
    st.metric(
        label="Win Rate",
        value=f"{stats['winrate']:.0f}%",
        delta=f"Last {stats['total_trades']} trades",
    )

st.markdown("")

# ============================
#  MIDDLE: CHART + ACCOUNT BOX
# ============================

left, right = st.columns([3, 2])

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Performance Visualization</div>', unsafe_allow_html=True)

    equity_curve = build_equity_curve(trades_df, stats["starting_balance"])
    if not equity_curve.empty:
        st.line_chart(equity_curve)
    else:
        st.caption("Equity curve will appear here once `r_multiple` data is available.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Account Snapshot</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
**Symbol:** `{symbol}`  
**Timeframe:** `{timeframe}`  
**Risk per trade (visual):** `{user_risk:.1f}%`  

**Total trades:** {stats['total_trades']}  
- Wins: {stats['wins']}  
- Losses: {stats['losses']}  
- Total R: {stats['total_R']:.1f} R  
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ============================
#  LIVE SETUP SCANNER
# ============================

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📡 Live Setup Scanner</div>', unsafe_allow_html=True)

# Filter latest setups for selected symbol/timeframe
scanner_df = trades_df.copy()
if "symbol" in scanner_df.columns:
    scanner_df = scanner_df[scanner_df["symbol"] == symbol]
if "timeframe" in scanner_df.columns:
    scanner_df = scanner_df[scanner_df["timeframe"] == timeframe]

# Basic column rename for cleaner display
display_cols = []
for c in ["time", "symbol", "timeframe", "direction", "setup", "status", "r_multiple"]:
    if c in scanner_df.columns:
        display_cols.append(c)

if display_cols:
    tmp = scanner_df.sort_values("time", ascending=False)[display_cols].head(20)
    tmp = tmp.rename(
        columns={
            "time": "Time",
            "symbol": "Pair",
            "timeframe": "TF",
            "direction": "Direction",
            "setup": "Setup",
            "status": "Status",
            "r_multiple": "Est. TP (R mult)",
        }
    )
    st.dataframe(tmp, use_container_width=True)
else:
    st.caption("No setup data available yet. Once trades are logged, they will appear here.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ============================
#  PERFORMANCE TRACKING (RAW)
# ============================

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📊 Performance Tracking (raw data)</div>', unsafe_allow_html=True)

st.json(
    {
        "Total Trades": stats["total_trades"],
        "Wins": stats["wins"],
        "Losses": stats["losses"],
        "Winrate %": round(stats["winrate"], 1),
        "Total R": round(stats["total_R"], 2),
        "Net Profit (approx)": round(stats["net_profit"], 2),
    }
)

st.markdown("</div>", unsafe_allow_html=True)
