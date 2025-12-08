import streamlit as st
import datetime as dt
from datetime import timedelta
import numpy as np

# Only used later when we wire MT5 back in
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# --------------------------------------------------
# SESSION INITIALISATION
# --------------------------------------------------
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "plan" not in st.session_state:
        st.session_state.plan = "Free (Backtest / Demo only)"

init_session()

# --------------------------------------------------
# SIMPLE LOCAL LOGIN LOGIC
# --------------------------------------------------
VALID_USERS = {
    # change these if you like – they are ONLY checked locally
    "admin": "gladiator123",
    "josh": "oneSetup4Life",
}

def login_screen():
    st.title("GOLD GLADIATOR – Login")

    st.write(
        "This is a **local login** for your private AI trading console.\n"
        "Credentials are checked only on this machine and are *not* sent anywhere."
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Logged in successfully. Loading dashboard…")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")

    st.info(
        "For now you can use, for example:\n"
        "- **Username:** `josh`\n"
        "- **Password:** `oneSetup4Life`"
    )

def logout_button():
    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_rerun()

# --------------------------------------------------
# VERY SIMPLE PLACEHOLDER TRADING LOGIC
# (we will replace this with your Setup 1 & 2 rules)
# --------------------------------------------------
def dummy_direction():
    # Always NO-TRADE for now – just to prove wiring
    return "NO-TRADE", "Strategy core not wired yet (placeholder)."

# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------
def main_dashboard():
    st.title("GOLD GLADIATOR")

    st.caption(
        f"Private intraday AI execution console – logged in as "
        f"**{st.session_state.username}**"
    )

    # ---------- SIDEBAR: SUBSCRIPTION ----------
    st.sidebar.subheader("Account")

    logout_button()

    plan = st.sidebar.selectbox(
        "Subscription plan",
        [
            "Free (Backtest / Demo only)",
            "Pro (Live signals, manual execution)",
            "Live (Auto-execution with MT5)",
        ],
        index=["Free (Backtest / Demo only)",
               "Pro (Live signals, manual execution)",
               "Live (Auto-execution with MT5)"].index(st.session_state.plan),
    )
    st.session_state.plan = plan

    if plan.startswith("Free"):
        st.sidebar.info(
            "You are on the **Free** plan.\n\n"
            "- No live auto-trading\n"
            "- You can still run scans and get directions\n"
            "- Great for demo / forward testing"
        )
    elif plan.startswith("Pro"):
        st.sidebar.success(
            "You are on **Pro** (concept).\n\n"
            "In the real system this would unlock:\n"
            "- Live signals during London & New York sessions\n"
            "- Manual click-to-execute suggestions"
        )
    else:
        st.sidebar.warning(
            "You selected **Live (Auto-execution)**.\n\n"
            "To actually auto-trade we would still need:\n"
            "- Secure API key / license check\n"
            "- MT5 terminal authorised & linked\n"
            "- Broker / prop firm risk agreement."
        )

    st.sidebar.markdown("---")

    # ---------- SIDEBAR: RISK & SYMBOL ----------
    risk_pct = st.sidebar.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        value=1.0,
        step=0.25,
    )

    symbol = st.sidebar.selectbox(
        "Symbol",
        options=["XAUUSD", "EURUSD"],
        index=0,
    )

    tf_label = st.sidebar.radio(
        "Trading timeframe",
        options=["M5", "M15"],
        index=1,
    )

    st.sidebar.caption(
        "Real execution will only be allowed inside your London & "
        "New York windows once the full strategy core is wired."
    )

    # ---------- TOP SUMMARY ----------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("ACCOUNT BALANCE", "—")
    with col2:
        st.metric("NET P/L (SESSION)", "—")
    with col3:
        st.metric("WIN RATE", "—")
    with col4:
        st.metric("RISK PER TRADE", f"{risk_pct:.2f}%")

    st.markdown("### Equity / Performance")
    equity_placeholder = st.empty()
    equity_placeholder.line_chart([0])  # placeholder flat line

    st.markdown("---")

    # ---------- SCAN BUTTON ----------
    st.markdown("### Intraday scan")

    st.write(
        "This is the **shell** of your AI. Right now it only proves the flow:\n"
        "1. You log in\n"
        "2. You select a subscription plan\n"
        "3. You choose symbol / timeframe & risk\n"
        "4. You click **Scan today for setups** and see a decision\n\n"
        "Next step is to wire your full Setup 1 & 2 logic into this scan."
    )

    scan_button = st.button("🔍 Scan today for setups")

    result_box = st.empty()

    if scan_button:
        direction, explanation = dummy_direction()

        if direction == "NO-TRADE":
            result_box.warning(f"NO-TRADE: {explanation}")
        elif direction == "BUY":
            result_box.success(f"✅ BUY {symbol} ({tf_label}). Reason: {explanation}")
        elif direction == "SELL":
            result_box.success(f"✅ SELL {symbol} ({tf_label}). Reason: {explanation}")

    # ---------- FOOTER ----------
    st.markdown("---")
    st.caption(
        "Login and subscription system are **local only** right now. "
        "No credentials or trading data are sent outside this machine."
    )

# --------------------------------------------------
# ROUTER: SHOW LOGIN OR DASHBOARD
# --------------------------------------------------
if not st.session_state.logged_in:
    login_screen()
else:
    main_dashboard()
