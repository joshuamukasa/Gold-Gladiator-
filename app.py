# ======================================================
# GOLD GLADIATOR – STREAMLIT DASHBOARD (WITH CSV FIX)
# ======================================================

import streamlit as st
import pandas as pd
from datetime import datetime

from engine import scan_setups, trades_to_df

# ------------------------------------------------------
# PAGE CONFIG & BASIC STYLE
# ------------------------------------------------------

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
        max-width: 1200px;
    }
    .gg-title {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }
    .gg-sub {
        font-size: 13px;
        opacity: 0.7;
        margin-bottom: 0.9rem;
    }
    .gg-card {
        padding: 0.9rem 1.1rem;
        border-radius: 0.9rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(0,0,0,0.4));
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 0 18px rgba(0,0,0,0.4);
    }
    .gg-label {
        font-size: 11px;
        text-transform: uppercase;
        opacity: 0.65;
        letter-spacing: 0.09em;
        margin-bottom: 0.1rem;
    }
    .gg-value {
        font-size: 20px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------
# SIDEBAR – CONTROL PANEL
# ------------------------------------------------------

with st.sidebar:
    st.markdown("### Control Panel")

    risk_pct = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        value=1.0,
        step=0.25,
    )

    st.markdown("---")
    uploaded = st.file_uploader(
        "Upload M5 CSV from MT5",
        type=["csv"],
        help="Export from MT5: Time, Open, High, Low, Close, Volume/Tick Volume.",
    )

    st.markdown("---")
    st.caption("Gold Gladiator • Prototype dashboard • Engine wired to CSV backtest for now.")

# ------------------------------------------------------
# HEADER
# ------------------------------------------------------

st.markdown('<div class="gg-title">GOLD GLADIATOR</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="gg-sub">Intraday performance console for your private execution engine.</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ------------------------------------------------------
# SAFE CSV LOADER (FIXES UTF ERRORS FROM MT5)
# ------------------------------------------------------

def load_mt5_csv(file) -> pd.DataFrame:
    """
    Try multiple encodings so MT5 exports don't crash the app.
    """
    last_err = None
    for enc in ["utf-16", "utf-8", "cp1252"]:
        try:
            file.seek(0)  # reset pointer each attempt
            df = pd.read_csv(file, encoding=enc)
            return df
        except Exception as e:
            last_err = e
            continue
    raise last_err if last_err is not None else ValueError("Could not decode CSV file.")


def normalize_ohlcv(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Tries to standardize to columns: time index + open, high, low, close, volume.
    """
    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # find time column
    time_col = None
    for c in ["time", "date", "datetime"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        raise ValueError(f"Could not find time column. Columns: {list(df.columns)}")

    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values(time_col).set_index(time_col)

    def pick(*names):
        for n in names:
            if n in df.columns:
                return n
        return None

    o_col = pick("open", "o")
    h_col = pick("high", "h")
    l_col = pick("low", "l")
    c_col = pick("close", "c")
    v_col = pick("tick_volume", "tickvolume", "volume", "vol")

    missing = [name for name, col in
               [("open", o_col), ("high", h_col), ("low", l_col), ("close", c_col), ("volume", v_col)]
               if col is None]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}. Columns: {list(df.columns)}")

    out = pd.DataFrame(
        {
            "open": df[o_col].astype(float),
            "high": df[h_col].astype(float),
            "low": df[l_col].astype(float),
            "close": df[c_col].astype(float),
            "volume": df[v_col].astype(float),
        },
        index=df.index,
    )
    return out

# ------------------------------------------------------
# KPI DEFAULTS
# ------------------------------------------------------

account_balance_display = "--"   # future: from MT5
net_pl_display = "--"
winrate_display = "--"
risk_display = f"{risk_pct:.2f}%"

stats = {
    "setups_found": 0,
    "completed_trades": 0,
    "wins": 0,
    "losses": 0,
    "winrate_pct": 0.0,
}
trades_df = pd.DataFrame()

# ------------------------------------------------------
# IF CSV UPLOADED → LOAD, NORMALIZE, RUN ENGINE
# ------------------------------------------------------

if uploaded is not None:
    try:
        raw = load_mt5_csv(uploaded)
        df_ohlc = normalize_ohlcv(raw)

        trades, stats = scan_setups(df_ohlc, risk_pct=risk_pct)
        trades_df = trades_to_df(trades)

        if stats["completed_trades"] > 0:
            winrate_display = f"{stats['winrate_pct']:.1f}%"
        else:
            winrate_display = "--"

        # simple net R estimate: wins 4R, losses -1R (since TP=4R, SL=1R in engine)
        net_R = stats["wins"] * 4.0 - stats["losses"] * 1.0
        net_pl_display = f"{net_R:.1f}R"

        st.success("✅ CSV loaded and engine run successfully.")

    except Exception as e:
        st.error("❌ Problem reading or processing the CSV.")
        st.code(str(e))

# ------------------------------------------------------
# KPI ROW
# ------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Account Balance</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{account_balance_display}</div>', unsafe_allow_html=True)
    st.caption("Will display live MT5 equity later.")
    st.markdown('</div>', unsafe_allow_html=True)

with k2:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Net P/L (Session)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{net_pl_display}</div>', unsafe_allow_html=True)
    st.caption("Prototype: estimated total R from this dataset.")
    st.markdown('</div>', unsafe_allow_html=True)

with k3:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Win Rate</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{winrate_display}</div>', unsafe_allow_html=True)
    st.caption("From completed trades in uploaded data.")
    st.markdown('</div>', unsafe_allow_html=True)

with k4:
    st.markdown('<div class="gg-card">', unsafe_allow_html=True)
    st.markdown('<div class="gg-label">Risk / Trade</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gg-value">{risk_display}</div>', unsafe_allow_html=True)
    st.caption("User-defined; engine uses % to size risk.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ------------------------------------------------------
# LOWER PANELS: LIVE SETUPS & PERFORMANCE SNAPSHOT
# ------------------------------------------------------

left, right = st.columns([2, 1])

with left:
    st.markdown("### 📡 Live Setup Feed")
    if uploaded is None:
        st.info("Upload an M5 CSV on the left to see detected setups.")
    else:
        if trades_df.empty:
            st.warning("No valid setups found with current rules on this dataset.")
        else:
            st.dataframe(
                trades_df[
                    ["Direction", "Entry", "SL", "TP", "Session", "Tag", "Status"]
                ],
                use_container_width=True,
            )

with right:
    st.markdown("### 📊 Performance Snapshot")
    if uploaded is None:
        st.write("Waiting for data…")
    else:
        st.write(
            {
                "Setups found": stats["setups_found"],
                "Completed trades": stats["completed_trades"],
                "Wins": stats["wins"],
                "Losses": stats["losses"],
                "Winrate (%)": round(stats["winrate_pct"], 1),
            }
        )
    st.markdown("---")
    st.caption("Later this will show live session stats + real money P/L once MT5 is connected.")
