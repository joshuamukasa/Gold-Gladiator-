import streamlit as st
import pandas as pd
from datetime import datetime

from engine import scan_setups, trades_to_df

# ----------------------------------------------------
# GOLD GLADIATOR – LIVE DASHBOARD (PROTOTYPE)
# ----------------------------------------------------

st.set_page_config(page_title="Gold Gladiator", layout="wide")

# ============= SIDEBAR / CONTROL PANEL =============
with st.sidebar:
    st.markdown("### Control Panel")

    # Only risk control (no symbol / timeframe)
    risk_pct = st.slider(
        "Configured risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        value=1.0,
        step=0.25,
    )

    st.markdown("---")
    st.markdown("**Data input**")
    uploaded = st.file_uploader(
        "Upload M5 CSV (time, open, high, low, close, volume/tick_volume)",
        type=["csv"],
    )

    st.markdown("---")
    st.caption("Gold Gladiator – prototype dashboard UI.")

# ============= MAIN LAYOUT =============
st.markdown("## 🥇 GOLD GLADIATOR")
st.markdown("##### Live intraday performance monitor for your private day-trading engine.")
st.markdown("---")

# Top KPI row
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

# Defaults (before we have data)
account_balance_display = "--"
net_pl_display = "--"
winrate_display = "--"
risk_display = f"{risk_pct:.2f}%"

# Containers for later
trades_df = pd.DataFrame()
stats = {
    "setups_found": 0,
    "completed_trades": 0,
    "wins": 0,
    "losses": 0,
    "winrate_pct": 0.0,
}

# ============= DATA + ENGINE CALL =============
if uploaded is not None:
    try:
        # Read CSV
        df = pd.read_csv(uploaded)

        # Try to locate the time column
        time_col_candidates = ["time", "Time", "datetime", "DateTime"]
        time_col = None
        for c in time_col_candidates:
            if c in df.columns:
                time_col = c
                break
        if time_col is None:
            st.error("Could not find a time column in your CSV.")
        else:
            df[time_col] = pd.to_datetime(df[time_col])
            df.set_index(time_col, inplace=True)

            # Normalize volume column name
            if "volume" not in df.columns:
                for c in ["Volume", "tick_volume", "tickvol", "TickVolume"]:
                    if c in df.columns:
                        df.rename(columns={c: "volume"}, inplace=True)
                        break

            # Keep only OHLCV we need
            needed = ["open", "high", "low", "close", "volume"]
            missing = [c for c in needed if c not in df.columns]
            if missing:
                st.error(f"Missing columns in CSV: {missing}")
            else:
                df = df[needed]

                # Run the core engine
                trades, stats = scan_setups(df, risk_pct=risk_pct)
                trades_df = trades_to_df(trades)

                # Update winrate display
                if stats["completed_trades"] > 0:
                    winrate_display = f"{stats['winrate_pct']:.1f}%"
                else:
                    winrate_display = "--"

                # Net P/L placeholder (for when we later attach real P/L)
                # For now we simply count wins-losses in R terms
                net_R = stats["wins"] * 4.0 - stats["losses"] * 1.0
                net_pl_display = f"{net_R:.1f}R"

    except Exception as e:
        st.error(f"Error reading or processing CSV: {e}")

# ============= KPI DISPLAY =============
with kpi_col1:
    st.markdown("###### Account Balance")
    st.markdown(f"### {account_balance_display}")
    st.caption("Will show live MT5 balance later.")

with kpi_col2:
    st.markdown("###### Net P/L (Session)")
    st.markdown(f"### {net_pl_display}")
    st.caption("Based on closed trades only (prototype).")

with kpi_col3:
    st.markdown("###### Win Rate")
    st.markdown(f"### {winrate_display}")
    st.caption("Calculated from last completed trades in dataset.")

with kpi_col4:
    st.markdown("###### Configured Risk / Trade")
    st.markdown(f"### {risk_display}")
    st.caption("Visual setting – execution engine will use this.")

st.markdown("---")

# ============= LOWER PANELS =============

left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("### 📡 Live Setup Feed")

    if uploaded is None:
        st.info("Upload an M5 CSV on the left to see detected setups.")
    else:
        if trades_df.empty:
            st.warning("No valid setups found in this dataset with current rules.")
        else:
            st.dataframe(
                trades_df[
                    ["Direction", "Entry", "SL", "TP", "Session", "Tag", "Status"]
                ],
                use_container_width=True,
            )

with right_col:
    st.markdown("### 📊 Performance Snapshot")

    if uploaded is None:
        st.write("Waiting for data...")
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
    st.caption(
        "Once the execution AI + MT5 bridge are wired, this panel will show live "
        "session stats and real P/L in money."
    )
