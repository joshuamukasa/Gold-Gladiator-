import datetime
from typing import Optional

import streamlit as st
import MetaTrader5 as mt5


# ----------------------------------------------------
# PAGE & SESSION SETUP
# ----------------------------------------------------

st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# Initialise session state keys
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "risk_perc" not in st.session_state:
    st.session_state.risk_perc = 1.0
if "exec_mode" not in st.session_state:
    st.session_state.exec_mode = "Paper / Monitor Only"
if "mt5_connected" not in st.session_state:
    st.session_state.mt5_connected = False
if "mt5_info" not in st.session_state:
    st.session_state.mt5_info = None
if "mt5_login" not in st.session_state:
    st.session_state.mt5_login = ""
if "mt5_password" not in st.session_state:
    st.session_state.mt5_password = ""
if "mt5_server" not in st.session_state:
    st.session_state.mt5_server = ""


# ----------------------------------------------------
# MT5 CONNECTOR
# ----------------------------------------------------

def connect_mt5(login: str, password: str, server: str):
    """
    Simple MT5 connection helper.
    Returns (ok: bool, info_or_error: dict | str)
    """
    try:
        # Ensure previous session is closed
        mt5.shutdown()

        if not mt5.initialize():
            return False, f"initialize() failed: {mt5.last_error()}"

        # login must be int
        try:
            login_int = int(login)
        except ValueError:
            mt5.shutdown()
            return False, "Login must be a number (account ID)."

        authorized = mt5.login(login_int, password=password, server=server)
        if not authorized:
            err = mt5.last_error()
            mt5.shutdown()
            return False, f"login failed: {err}"

        acc = mt5.account_info()
        if acc is None:
            err = mt5.last_error()
            mt5.shutdown()
            return False, f"account_info() failed: {err}"

        info = {
            "login": acc.login,
            "name": acc.name,
            "server": acc.server,
            "balance": acc.balance,
            "equity": acc.equity,
        }

        # you can keep MT5 open if you want; here we close after test
        mt5.shutdown()
        return True, info

    except Exception as e:
        mt5.shutdown()
        return False, str(e)


# ----------------------------------------------------
# UI SECTIONS
# ----------------------------------------------------

def login_screen():
    st.title("GOLD GLADIATOR – Owner Login")
    st.write(
        "This login only protects the console on **this laptop**. "
        "No data is being sent anywhere yet."
    )

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if username.strip() and password:
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
        else:
            st.error("Please enter **both** username and password.")


def mt5_connection_panel():
    st.subheader("MT5 Connection")

    st.caption(
        "Enter the **exact** MT5 login, password and server name from your MT5 terminal."
    )

    login = st.text_input(
        "MT5 Login (account number)",
        value=st.session_state.mt5_login,
        key="mt5_login_input",
    )
    password = st.text_input(
        "MT5 Password",
        type="password",
        value=st.session_state.mt5_password,
        key="mt5_password_input",
    )
    server = st.text_input(
        "MT5 Server (exact name, e.g. 'XMGlobal-MT5 6')",
        value=st.session_state.mt5_server,
        key="mt5_server_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connect / Test MT5"):
            if not login.strip() or not password or not server.strip():
                st.error("Fill **all** MT5 fields before connecting.")
            else:
                # save to session
                st.session_state.mt5_login = login.strip()
                st.session_state.mt5_password = password
                st.session_state.mt5_server = server.strip()

                ok, info = connect_mt5(
                    st.session_state.mt5_login,
                    st.session_state.mt5_password,
                    st.session_state.mt5_server,
                )

                if ok:
                    st.session_state.mt5_connected = True
                    st.session_state.mt5_info = info
                    st.success(
                        f"✅ Connected to MT5 account **{info['login']}** on **{info['server']}**"
                    )
                else:
                    st.session_state.mt5_connected = False
                    st.session_state.mt5_info = None
                    st.error(f"❌ MT5 connection failed: {info}")

    with col2:
        if st.button("Clear MT5 Details"):
            st.session_state.mt5_login = ""
            st.session_state.mt5_password = ""
            st.session_state.mt5_server = ""
            st.session_state.mt5_connected = False
            st.session_state.mt5_info = None
            st.info("Cleared saved MT5 details.")

    if st.session_state.mt5_connected and st.session_state.mt5_info:
        info = st.session_state.mt5_info
        st.success(
            f"Currently marked as **CONNECTED** to {info['server']} – "
            f"Login: {info['login']}, Balance: {info['balance']}, Equity: {info['equity']}"
        )
    else:
        st.info("Not connected to MT5 yet. Use the form above to test connection.")


def owner_console():
    st.title("Gold Gladiator – Owner Console")
    st.caption(f"Logged in as **{st.session_state.username}**")

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.mt5_connected = False
        st.session_state.mt5_info = None
        st.experimental_set_query_params()  # soft reset of URL state
        st.stop()

    st.divider()

    # === Risk Settings ===
    st.subheader("Risk Settings")
    st.session_state.risk_perc = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        value=float(st.session_state.risk_perc),
        step=0.25,
        help="This is the percentage of account equity the AI will risk per trade once live execution is enabled.",
    )

    st.write(f"**Current risk per trade:** {st.session_state.risk_perc:.2f}%")

    # === Execution Mode ===
    st.subheader("Execution Mode")

    exec_mode = st.selectbox(
        "Mode",
        [
            "Paper / Monitor Only",
            "Mirror (confirm trades manually in MT5 first)",
            "Full Auto (AI sends orders to MT5)",
        ],
        index=["Paper / Monitor Only", "Mirror (confirm trades manually in MT5 first)",
               "Full Auto (AI sends orders to MT5)"].index(st.session_state.exec_mode)
        if st.session_state.exec_mode in [
            "Paper / Monitor Only",
            "Mirror (confirm trades manually in MT5 first)",
            "Full Auto (AI sends orders to MT5)",
        ]
        else 0,
    )

    st.session_state.exec_mode = exec_mode

    if exec_mode == "Paper / Monitor Only":
        st.info("The AI will **only scan and display** trades. No orders will be sent.")
    elif exec_mode == "Mirror (confirm trades manually in MT5 first)":
        st.warning(
            "The AI will propose trades. You will **manually confirm/execute** them in MT5."
        )
    else:
        st.error(
            "Full Auto is a future step. For safety, live order sending is **not enabled** yet."
        )

    st.divider()

    # === Session Overview (placeholder until engine is wired) ===
    st.subheader("Session Overview (placeholder until engine is wired)")

    cols = st.columns(4)
    with cols[0]:
        st.metric("Account Balance", "—")
    with cols[1]:
        st.metric("Net P/L (Session)", "—")
    with cols[2]:
        st.metric("Win Rate", "—")
    with cols[3]:
        st.metric("Risk / Trade", f"{st.session_state.risk_perc:.2f}%")

    st.caption(
        "These values will be filled once the strategy engine is fully wired to MT5 history and live trades."
    )

    st.divider()

    # === MT5 Connection Panel ===
    mt5_connection_panel()

    st.divider()

    st.caption(
        "Next step: wire your **StrategyEngine** so this console pulls real stats and signals from MT5."
    )


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

def main():
    if not st.session_state.logged_in:
        login_screen()
    else:
        owner_console()


if __name__ == "__main__":
    main()
