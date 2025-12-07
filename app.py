import streamlit as st
import pandas as pd

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator • Execution Console",
    page_icon="🥇",
    layout="wide",
)

# -------------------------------------------------
# PREMIUM-STYLE CSS
# -------------------------------------------------
st.markdown(
    """
    <style>
        .main {
            background: radial-gradient(circle at top left, #1b2030, #05060a 55%);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07090f, #131728);
            border-right: 1px solid rgba(255,255,255,0.04);
        }
        .metric-card {
            padding: 1.0rem 1.2rem;
            border-radius: 0.9rem;
            background: radial-gradient(circle at top left, #262b3f, #101322);
            border: 1px solid rgba(255,255,255,0.04);
            box-shadow: 0 10px 25px rgba(0,0,0,0.55);
        }
        .metric-label {
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.65);
        }
        .metric-value {
            font-size: 1.4rem;
            font-weight: 600;
            margin-top: 0.25rem;
        }
        .metric-sub {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.55);
            margin-top: 0.15rem;
        }
        .section-title {
            font-size: 0.9rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.55);
            margin-bottom: 0.4rem;
        }
        .block-card {
            padding: 1.0rem 1.2rem;
            border-radius: 0.9rem;
            background: rgba(8,9,16,0.92);
            border: 1px solid rgba(255,255,255,0.04);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def load_mt5_csv(file):
    """
    Read raw MT5 M5 CSV:
    time, open, high, low, close, tick_volume, ...
    No headers in MT5 export, so we force them.
    """
    try:
        df = pd.read_csv(file, header=None)
        if df.shape[1] < 5:
            return None, "CSV looks wrong: expected at least 5 columns (time, open, high, low, close)."

        # Keep only first 6 columns: time + OHLC + tick_volume
        df = df.iloc[:, :6]
        df.columns = ["time", "open", "high", "low", "close", "tick_volume"]

        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["time"])
        df = df.set_index("time").sort_index()

        return df, None
    except Exception as e:
        return None, f"Error while reading CSV: {e}"


def simple_backtest(df, risk_pct: float = 1.0, rr_multiple: float = 4.0):
    """
    VERY SIMPLE placeholder engine so the dashboard has numbers.
    This is NOT your final ICT window / 15M+5M logic.
    We will replace this later with your proper NY-window engine.
    """
    o = df["open"].values
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values

    results_R = []

    # basic engulfing-style placeholder
    for i in range(1, len(df) - 50):
        # bullish engulfing
        if c[i] > o[i] and c[i - 1] < o[i - 1] and c[i] > h[i - 1] and l[i] < l[i - 1]:
            entry = c[i]
            sl = l[i]
            risk = entry - sl
            tp = entry + rr_multiple * risk

            win = False
            for j in range(i + 1, i + 51):
                if l[j] <= sl:
                    break
                if h[j] >= tp:
                    win = True
                    break
            results_R.append(rr_multiple if win else -1.0)

        # bearish engulfing
        elif c[i] < o[i] and c[i - 1] > o[i - 1] and c[i] < l[i - 1] and h[i] > h[i - 1]:
            entry = c[i]
            sl = h[i]
            risk = sl - entry
            tp = entry - rr_multiple * risk

            win = False
            for j in range(i + 1, i + 51):
                if h[j] >= sl:
                    break
                if l[j] <= tp:
                    win = True
                    break
            results_R.append(rr_multiple if win else -1.0)

    total = len(results_R)
    wins = sum(1 for r in results_R if r > 0)
    losses = total - wins
    winrate = (wins / total * 100.0) if total > 0 else 0.0
    total_R = sum(results_R)

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "winrate": winrate,
        "total_R": total_R,
    }


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")

    # ONLY risk slider (0.25 → 10%)
    risk_pct = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        step=0.25,
        value=1.0,
    )

    st.markdown("---")
    st.markdown("##### Backtest data (optional)")
    uploaded_file = st.file_uploader(
        "Upload M5 CSV exported from MT5",
        type=["csv"],
        help="Raw time, open, high, low, close, tick_volume from MT5. Used for prototype stats only.",
    )

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.markdown("## 🥇 GOLD GLADIATOR")
st.markdown(
    "<span style='color:rgba(255,255,255,0.75);font-size:0.9rem;'>"
    "Intraday performance console for your private execution engine."
    "</span>",
    unsafe_allow_html=True,
)
st.markdown("")

stats = None
df_prices = None

# -------------------------------------------------
# LOAD DATA + RUN PLACEHOLDER ENGINE
# -------------------------------------------------
if uploaded_file is not None:
    df_prices, error_msg = load_mt5_csv(uploaded_file)

    if error_msg:
        st.error(error_msg)
    else:
        stats = simple_backtest(df_prices, risk_pct=risk_pct, rr_multiple=4.0)

# -------------------------------------------------
# TOP METRIC STRIP (4 CARDS)
# -------------------------------------------------
m1, m2, m3, m4 = st.columns(4)


def metric_card(col, label: str, value: str, sub: str = ""):
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


bal_val = "--"
pl_val = "--"
wr_val = "--"

if stats:
    wr_val = f"{stats['winrate']:.1f}%"
    pl_val = f"{stats['total_R']:.1f} R"

metric_card(
    m1,
    "ACCOUNT BALANCE",
    bal_val,
    "Live equity will show once MT5 is connected.",
)

metric_card(
    m2,
    "NET P/L (SESSION)",
    pl_val,
    "Prototype: total R from uploaded dataset.",
)

metric_card(
    m3,
    "WIN RATE",
    wr_val,
    "Based on completed trades found in dataset.",
)

metric_card(
    m4,
    "RISK / TRADE",
    f"{risk_pct:.2f}%",
    "Configured in the control panel.",
)

st.markdown("")

# -------------------------------------------------
# MIDDLE ROW: EQUITY / PERFORMANCE + SESSION SUMMARY
# -------------------------------------------------
left, right = st.columns([2.2, 1.3])

with left:
    st.markdown(
        '<div class="section-title">EQUITY / PERFORMANCE</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    if stats and stats["total_trades"] > 0:
        # Dummy cumulative R curve so it looks like a real equity chart
        results = [1 if i < stats["wins"] else -1 for i in range(stats["total_trades"])]
        cum = pd.Series(results).cumsum()
        cum.index.name = "Trade #"
        st.line_chart(cum)
        st.caption("Prototype cumulative R curve (engine logic will be replaced by your NY-window model).")
    else:
        st.caption(
            "Upload a CSV in the sidebar to generate a prototype equity curve. "
            "Live MT5-driven equity will sit here once the execution engine is wired in."
        )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        '<div class="section-title">SESSION SUMMARY</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    if stats:
        st.write(
            {
                "Trades": stats["total_trades"],
                "Wins": stats["wins"],
                "Losses": stats["losses"],
            }
        )
    else:
        st.write(
            "No session data yet. Once the live execution engine is connected to MT5, "
            "this block will show realtime session stats."
        )

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# BOTTOM: RAW SNAPSHOT (DEBUG STYLE)
# -------------------------------------------------
st.markdown(
    '<div class="section-title">RAW ENGINE SNAPSHOT</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="block-card">', unsafe_allow_html=True)

if stats:
    st.json(
        {
            "total_trades": stats["total_trades"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "winrate_pct": round(stats["winrate"], 2),
            "total_R": round(stats["total_R"], 2),
        }
    )
else:
    st.caption(
        "Waiting for data. Upload historical M5 data or (later) plug in the live MT5 backend."
    )

st.markdown("</div>", unsafe_allow_html=True)
