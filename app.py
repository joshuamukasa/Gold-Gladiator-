# app.py – Gold Gladiator console with login + MT5 hook points
# Replace your entire app.py with this file.

import datetime as dt

import streamlit as st

# Try to import MetaTrader5, but don't crash the UI if it's missing
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except Exception:
    mt5 = None
    MT5_AVAILABLE = False


# ---------------------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# ---------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "mt5_connected" not in st.session_state:
    st.session_state.mt5_connected = False

if "mt5_login_data" not in st.session_state:
    st.session_state.mt5_login_data = {}


# ---------------------------------------------------------------------
# SIMPLE AUTH (LOCAL ONLY FOR NOW)
# ---------------------------------------------------------------------
def show_login_page():
    st.title("GOLD GLADIATOR – Owner Login")
    st.write(
        "This login just protects the console on **this laptop**. "
        "No data is being sent anywhere yet."
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        # For now: accept ANY username/password.
        # Later we can lock this down (env vars / database / etc.)
        if username.strip() == "" or password.strip() == "":
            st.error("Please enter both username and password.")
        else:
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
            st.success("Logged in. Loading dashboard...")
            # IMPORTANT: use st.rerun(), not experimental_rerun
            st.rerun()


# ---------------------------------------------------------------------
# MT5 CONNECTION HELPERS
# ---------------------------------------------------------------------
def connect_mt5(login: int, password: str, server: str) -> bool:
    """
    Try to initialize and login to MT5.
    Returns True on success, False on failure.
    """
    if not MT5_AVAILABLE:
        st.error("MetaTrader5 Python package is not installed.")
        return False

    # shutdown any previous session
    mt5.shutdown()

    if not mt5.initialize():
        st.error(f"MT5 initialize() failed, error code: {mt5.last_error()}")
        return False

    authorized = mt5.login(login=login, password=password, server=server)
    if not authorized:
        st.error(f"MT5 login failed, error code: {mt5.last_error()}")
        mt5.shutdown()
        return False

    return True


def show_mt5_connection_panel():
    st.subheader("MT5 Connection")

    if not MT5_AVAILABLE:
        st.warning(
            "MetaTrader5 package not found. "
            "Install it in your environment with: `pip install MetaTrader5`."
        )
        return

    with st.form("mt5_connect_form"):
        server = st.text_input("Broker server name (e.g. FBS-Real, Exness-MT5Trial)")
        login_str = st.text_input("MT5 Login (account number)")
        password = st.text_input("MT5 Password", type="password")
        connect_clicked = st.form_submit_button("Connect to MT5")

    if connect_clicked:
        if not server.strip() or not login_str.strip() or not password.strip():
            st.error("Please fill in server, login and password.")
            return

        try:
            login = int(login_str)
        except ValueError:
            st.error("Login must be a number (your MT5 account ID).")
            return

        with st.spinner("Connecting to MT5…"):
            ok = connect_mt5(login, password, server)

        if ok:
            st.session_state.mt5_connected = True
            st.session_state.mt5_login_data = {
                "login": login,
                "server": server,
                "time": dt.datetime.now().isoformat(timespec="seconds"),
            }
            st.success("✅ MT5 connection successful. Ready for AI execution.")
        else:
            st.session_state.mt5_connected = False

    if st.session_state.mt5_connected:
        data = st.session_state.mt5_login_data
        st.info(
            f"Connected MT5 account: **{data.get('login')}** on **{data.get('server')}** "
            f"(since {data.get('time')})."
        )
        if st.button("Disconnect MT5"):
            if MT5_AVAILABLE:
                mt5.shutdown()
            st.session_state.mt5_connected = False
            st.session_state.mt5_login_data = {}
            st.success("Disconnected from MT5.")


# ---------------------------------------------------------------------
# DASHBOARD LAYOUT (PLACEHOLDER FOR YOUR STRATEGY ENGINE)
# ---------------------------------------------------------------------
def show_owner_dashboard():
    st.title("Gold Gladiator – Owner Console")

    # Top bar – logout
    cols_top = st.columns([3, 1])
    with cols_top[0]:
        st.write(f"Logged in as **{st.session_state.username}**")
    with cols_top[1]:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.mt5_connected = False
            if MT5_AVAILABLE:
                mt5.shutdown()
            st.rerun()

    st.markdown("---")

    # Main layout: left controls, right metrics
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Risk Settings")
        risk = st.slider(
            "Risk per trade (%)",
            min_value=0.25,
            max_value=10.0,
            value=1.0,
            step=0.25,
            help="This is the percentage of account equity the AI will risk per trade.",
        )
        st.caption(
            "Later, this value will be passed into the strategy engine for position sizing."
        )

        st.subheader("Execution Mode")
        st.radio(
            "Mode (future):",
            ["Paper / Demo only", "Live (when enabled)"],
            index=0,
            help="For now this is just visual. Execution logic will hook into this later.",
        )

    with col_right:
        st.subheader("Session Overview (mock until MT5 is linked)")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Account Balance", "—")
        with m2:
            st.metric("Net P/L (session)", "—")
        with m3:
            st.metric("Win Rate", "—")
        with m4:
            st.metric("Risk / Trade", f"{risk:.2f}%")

        st.write("")
        st.write("Equity / Performance (placeholder)")
        st.line_chart(
            {
                "Equity": [100_000, 100_250, 100_100, 100_600, 100_450],
                "Benchmark": [100_000, 100_050, 100_020, 100_040, 100_030],
            }
        )

    st.markdown("---")

    # Tabs for MT5 + future subscriber view
    tabs = st.tabs(["MT5 Connection", "Subscribers (future)"])

    with tabs[0]:
        show_mt5_connection_panel()

    with tabs[1]:
        st.subheader("Subscription Engine (future)")
        st.write(
            "Here we will later manage user subscriptions, seats, and which MT5 "
            "accounts are allowed to receive live AI signals."
        )


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------
if not st.session_state.logged_in:
    show_login_page()
else:
    show_owner_dashboard()
