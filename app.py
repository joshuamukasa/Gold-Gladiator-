import streamlit as st
import MetaTrader5 as mt5

# ----------------------------------------------------
# PAGE SETUP
# ----------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# ----------------------------------------------------
# SESSION STATE
# ----------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "mt5_connected" not in st.session_state:
    st.session_state.mt5_connected = False
if "mt5_account" not in st.session_state:
    st.session_state.mt5_account = None
if "mt5_server" not in st.session_state:
    st.session_state.mt5_server = None


# ----------------------------------------------------
# LOGIN SCREEN (LOCAL ONLY)
# ----------------------------------------------------
def login_screen():
    st.title("GOLD GLADIATOR – Owner Login")

    st.write(
        "This login just protects the console **on this laptop**. "
        "No data is being sent anywhere yet."
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if username.strip() != "" and password.strip() != "":
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
            st.success("Logged in. Loading dashboard…")
            st.experimental_rerun()
        else:
            st.error("Please enter a username and password.")

    st.info(
        "For now, you can log in with **any** username/password "
        "(e.g. `josh` / `1234`).\n"
        "Later we can hard-code or externalize real owner creds."
    )


def logout_button():
    if st.sidebar.button("Log out"):
        # also disconnect MT5 when logging out
        if st.session_state.mt5_connected:
            mt5.shutdown()
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.mt5_connected = False
        st.session_state.mt5_account = None
        st.session_state.mt5_server = None
        st.experimental_rerun()


# ----------------------------------------------------
# MT5 CONNECTION PANEL
# ----------------------------------------------------
def mt5_connection_panel():
    st.sidebar.subheader("MT5 Connection")

    if st.session_state.mt5_connected:
        st.sidebar.success(
            f"Connected: {st.session_state.mt5_account} @ "
            f"{st.session_state.mt5_server}"
        )

        if st.sidebar.button("Disconnect MT5"):
            mt5.shutdown()
            st.session_state.mt5_connected = False
            st.session_state.mt5_account = None
            st.session_state.mt5_server = None
            st.sidebar.info("Disconnected from MT5.")
    else:
        st.sidebar.warning("Not connected to MT5")

        with st.sidebar.form("mt5_login_form"):
            account = st.text_input("Account number")
            password = st.text_input("Account password", type="password")
            server = st.text_input("Server name (as shown in MT5)")
            submitted = st.form_submit_button("Connect to MT5")

        if submitted:
            # Basic sanity-check
            if account.strip() == "" or password.strip() == "" or server.strip() == "":
                st.sidebar.error("Fill in account, password and server.")
            else:
                try:
                    acc_number = int(account.strip())
                except ValueError:
                    st.sidebar.error("Account number must be digits only.")
                    return

                # Try to initialize MT5
                ok = mt5.initialize(
                    login=acc_number,
                    password=password.strip(),
                    server=server.strip(),
                )

                if not ok:
                    st.sidebar.error(f"MT5 init failed: {mt5.last_error()}")
                else:
                    st.session_state.mt5_connected = True
                    st.session_state.mt5_account = acc_number
                    st.session_state.mt5_server = server.strip()
                    st.sidebar.success("MT5 connected successfully!")


# ----------------------------------------------------
# STRATEGY PLACEHOLDER
# ----------------------------------------------------
def scan_for_setups(symbol: str, timeframe: str):
    """
    TEMPORARY STRATEGY SHELL.

    Right now it ALWAYS returns NO-TRADE so we don't fire
    random orders. Once your Setup 1 / Setup 2 engine is
    locked in, we will replace this to call the real logic.
    """
    direction = "NO-TRADE"
    explanation = (
        "Engine shell online. Setup 1 / Setup 2 logic not wired "
        "into this app yet, so I am deliberately not trading."
    )
    return direction, explanation


# ----------------------------------------------------
# MAIN DASHBOARD
# ----------------------------------------------------
def main_dashboard():
    st.title("GOLD GLADIATOR – AI Execution Console")

    st.caption(
        f"Owner: **{st.session_state.username}**  |  "
        "Mode: local dev – MT5 connection is per login"
    )

    # ---- Sidebar controls ----
    logout_button()
    mt5_connection_panel()

    symbol = st.sidebar.selectbox("Symbol", ["XAUUSD", "EURUSD"], index=0)
    timeframe = st.sidebar.radio("Timeframe", ["M5", "M15"], index=1)
    risk_pct = st.sidebar.slider(
        "Risk per trade (%)", min_value=0.25, max_value=10.0, value=1.0, step=0.25
    )

    st.sidebar.caption(
        "Execution will respect your London / New York windows "
        "once the full strategy logic is integrated."
    )

    # ---- Top metrics row (visual only for now) ----
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("ACCOUNT BALANCE", "—")
    with c2:
        st.metric("NET P/L (SESSION)", "—")
    with c3:
        st.metric("WIN RATE", "—")
    with c4:
        st.metric("RISK PER TRADE", f"{risk_pct:.2f}%")

    st.markdown("### Equity / Performance")
    st.line_chart([0, 0, 0])  # flat placeholder line

    st.markdown("---")
    st.markdown("### Intraday scan")

    if not st.session_state.mt5_connected:
        st.warning("Connect to your MT5 account in the sidebar first.")
    else:
        st.info(
            "When you click **Scan today for setups**, the AI engine will "
            "look for your Setup 1 / Setup 2 structures. "
            "For now it only returns NO-TRADE until the core is integrated."
        )

        if st.button("🔍 Scan today for setups"):
            direction, explanation = scan_for_setups(symbol, timeframe)

            if direction == "NO-TRADE":
                st.warning(f"NO-TRADE: {explanation}")
            elif direction == "BUY":
                st.success(f"✅ BUY {symbol} ({timeframe}) – {explanation}")
            elif direction == "SELL":
                st.success(f"✅ SELL {symbol} ({timeframe}) – {explanation}")

            st.caption(
                "Next step: wire your full strategy into this scan and then "
                "map its signals to MT5 orders."
            )


# ----------------------------------------------------
# ROUTER
# ----------------------------------------------------
if not st.session_state.logged_in:
    login_screen()
else:
    main_dashboard()
