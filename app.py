import streamlit as st
from engine import scan_market

# ---------------------------------
# APP PAGE SETTINGS
# ---------------------------------

st.set_page_config(page_title="Gold Gladiator", layout="wide")

# ---------------------------------
# HEADER
# ---------------------------------

st.title("GOLD GLADIATOR")
st.subheader("Intraday AI execution dashboard")

# ---------------------------------
# RISK CONTROL
# ---------------------------------

st.sidebar.header("RISK PARAMETERS")

risk_pct = st.sidebar.slider("Risk per trade (%)", 0.25, 10.0, 1.0)

# ---------------------------------
# SCANNER BUTTON
# ---------------------------------

st.header("AI MARKET SCANNER")

if st.button("Scan market now"):

    signal = scan_market("XAUUSD")

    if signal is None:
        st.warning("NO TRADE — No valid Setup 1 or 2 confirmed this session.")
    else:
        st.success(
            f"{signal['direction']} {signal['symbol']} "
            f"(Setup {signal['setup_type']}) — {signal['session']} Session"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Entry", signal["entry"])
        with col2:
            st.metric("Stop Loss", signal["sl"])
        with col3:
            st.metric("Take Profit", signal["tp"])

        st.markdown("**Reason:**")
        st.info(signal["reason"])


# ---------------------------------
# FAILSAFE
# ---------------------------------

st.caption("Trading AI is only active during the London & New York sessions. No forced trades. NO SIGNAL = NO TRADE.")
