# ======================================================
# GOLD GLADIATOR – STREAMLIT DASHBOARD (FINAL FIXED)
# ======================================================

import streamlit as st
import pandas as pd

# ------------------------------------------------------
# PAGE SETUP
# ------------------------------------------------------

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

st.title("⚔️ GOLD GLADIATOR")
st.subheader("Private Intraday Trading Engine Dashboard")


# ------------------------------------------------------
# SAFE CSV READER – FIXES UTF-8 + MT5 ISSUES
# ------------------------------------------------------

def load_mt5_csv(uploaded_file):

    encodings = ["utf-16", "utf-8", "cp1252"]

    last_error = None

    for enc in encodings:
        try:
            df = pd.read_csv(uploaded_file, encoding=enc)
            return df
        except Exception as e:
            last_error = e

    # If all fail:
    st.error("❌ CSV file could not be decoded. Export directly from MT5 with default settings.")
    raise last_error


# ------------------------------------------------------
# ENGINE PLACEHOLDER
# ------------------------------------------------------

def run_engine(df):
    """
    Placeholder for your real engine:

    Strategy flow:
    - Look left for structure bias
    - Wait for manipulation sweep
    - Confirm break of swing
    - Identify valid FVG
    - Confirm engulfing candle within London/NY session
    """

    # TEMP: no trades generated until engine logic is wired
    return {
        "total_setups": 0,
        "wins": 0,
        "losses": 0,
        "winrate": 0.0
    }


# ------------------------------------------------------
# LEFT CONTROL PANEL
# ------------------------------------------------------

st.sidebar.header("CONTROL PANEL")

risk_percent = st.sidebar.slider(
    "Configured Risk per Trade (%)",
    min_value=0.25,
    max_value=10.00,
    step=0.25,
    value=1.00
)

st.sidebar.markdown(f"### Current Risk Setting: **{risk_percent}%**")

uploaded_file = st.sidebar.file_uploader(
    "Upload MT5 CSV File",
    type=["csv"]
)


# ------------------------------------------------------
# MAIN DASHBOARD
# ------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Configured Risk / Trade", f"{risk_percent}%")

with col2:
    st.metric("Detected Setups", "0")

with col3:
    st.metric("Winrate", "--%")


st.divider()


# ------------------------------------------------------
# DATA IMPORT + ENGINE
# ------------------------------------------------------

if uploaded_file is not None:

    try:
        # ---- CSV LOAD (FIXED)
        df = load_mt5_csv(uploaded_file)

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        st.success("✅ MT5 data loaded successfully")

        # ---- RUN STRATEGY ENGINE
        stats = run_engine(df)

        st.subheader("Live Setup Feed")
        st.info("No valid setups found yet in this dataset with current rules")

        # ---- PERFORMANCE SNAPSHOT
        st.subheader("Performance Snapshot")
        st.json({
            "Setups Found": stats["total_setups"],
            "Wins": stats["wins"],
            "Losses": stats["losses"],
            "Winrate (%)": stats["winrate"]
        })

    except Exception as e:
        st.error("CSV load failed")
        st.code(str(e))


else:
    st.info("Upload an MT5 CSV file to start processing")
