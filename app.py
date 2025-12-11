import datetime as dt
from typing import Optional, List

import streamlit as st
import pandas as pd

try:
    import MetaTrader5 as mt5  # type: ignore
except Exception:
    mt5 = None  # type: ignore

from engine import StrategyEngine, TradeSignal  # type: ignore


# --------------------------------------------------------------------
# BASIC PAGE SETUP
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

# --------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""

if "mt5_connected" not in st.session_state:
    st.session_state["mt5_connected"] = False

if "mt5_login" not in st.session_state:
    st.session_state["mt5_login"] = None

if "mt5_server" not in st.session_state:
    st.session_state["mt5_server"] = None

if "risk_perc" not in st.session_state:
    st.session_state["risk_perc"] = 1.0

if "engine" not in st.session_state:
    st.session_state["engine"] = StrategyEngine(
        risk_per_trade_pct=st.session_state["risk_perc"]
    )

if "last_scan_signals" not in st.session_state:
    st.session_state["last_scan_signals"] = []

if "last_scan_time" not in st.session_state:
    st.session_state["last_scan_time"] = None


# --------------------------------------------------------------------
# LOGIN SCREEN
# --------------------------------------------------------------------
def show_login_screen() -> None:
    st.title("GOLD GLADIATOR – Owner Login")
    st.write(
        "This login just protects this console on this laptop. "
        "No data is being sent anywhere yet."
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username.strip() == "" or password.strip() == "":
                st.error("Enter any username and password to continue.")
            else:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username.strip()
                st.success(f"Logged in as {username.strip()}")
                st.rerun()


# --------------------------------------------------------------------
# MT5 CONNECTION BLOCK
# --------------------------------------------------------------------
def connect_mt5_block() -> None:
    st.header("MT5 Connection")

    if mt5 is None:
        st.error(
            "MetaTrader5 Python package is not available. "
            "Make sure it is installed in this Python environment."
        )
        return

    st.write("Enter the exact MT5 login, password and server name from your MT5 terminal.")

    login = st.text_input(
        "MT5 Login (account number)",
        value=str(st.session_state.get("mt5_login") or ""),
        key="mt5_login_input",
    )
    password = st.text_input("MT5 Password", type="password", key="mt5_password_input")
    server = st.text_input(
        "MT5 Server (exact name, e.g. 'XMGlobal-MT5 5')",
        value=str(st.session_state.get("mt5_server") or ""),
        key="mt5_server_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connect / Test MT5"):
            if not login or not password or not server:
                st.error("Fill ALL MT5 fields before connecting.")
            else:
                # Clean any previous connection
                mt5.shutdown()
                ok = mt5.initialize()
                if not ok:
                    st.error(f"MT5 initialize() failed: {mt5.last_error()}")
                else:
                    authorized = mt5.login(int(login), password=password, server=server)
                    if not authorized:
                        st.error(f"MT5 login failed: {mt5.last_error()}")
                    else:
                        info = mt5.account_info()
                        if info is None:
                            st.error("Connected, but could not fetch account_info().")
                        else:
                            st.session_state["mt5_connected"] = True
                            st.session_state["mt5_login"] = int(login)
                            st.session_state["mt5_server"] = server
                            st.success(
                                f"Connected to MT5 account {info.login} on {server} – "
                                f"Balance: {info.balance}, Equity: {info.equity}"
                            )

    with col2:
        if st.button("Clear MT5 Details"):
            st.session_state["mt5_connected"] = False
            st.session_state["mt5_login"] = None
            st.session_state["mt5_server"] = None
            mt5.shutdown()
            st.info("Cleared MT5 connection details.")

    if st.session_state["mt5_connected"]:
        st.success(
            f"Currently marked as CONNECTED to {st.session_state['mt5_server']} – "
            f"Login: {st.session_state['mt5_login']}"
        )
    else:
        st.info("Not connected to MT5 yet.")


# --------------------------------------------------------------------
# RISK + MODE
# --------------------------------------------------------------------
def risk_and_mode_block() -> str:
    st.subheader("Risk Settings")

    risk = st.slider(
        "Risk per trade (%)",
        min_value=0.25,
        max_value=10.0,
        value=float(st.session_state["risk_perc"]),
        step=0.25,
    )
    st.session_state["risk_perc"] = float(risk)
    st.session_state["engine"].risk_per_trade_pct = float(risk)

    st.write(f"Current risk per trade: **{risk:.2f}%**")

    st.subheader("Execution Mode")
    mode = st.selectbox(
        "Mode",
        ["Paper / Monitor Only", "Live (send orders later)"],
        index=0,
        help="For now, only 'Paper / Monitor Only' is supported. No orders are sent.",
    )
    st.info(
        "In this first version the AI will only scan and display trades. "
        "It will NOT send any orders, regardless of mode."
    )

    return mode


# --------------------------------------------------------------------
# SESSION OVERVIEW
# --------------------------------------------------------------------
def session_overview_block(engine: StrategyEngine) -> None:
    st.subheader("Session Overview (live once engine is fully wired)")

    if not st.session_state["mt5_connected"]:
        st.info("Connect to MT5 above to see live account stats.")
        return

    try:
        snap = engine.get_account_snapshot()
    except Exception as e:
        st.error(f"Error reading account info from MT5: {e}")
        return

    if snap is None:
        st.warning("Could not fetch account info from MT5.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Account Balance", f"{snap['balance']:.2f}")
    c2.metric("Equity", f"{snap['equity']:.2f}")
    c3.metric("Free Margin", f"{snap['margin_free']:.2f}")
    c4.metric("Risk / Trade", f"{st.session_state['risk_perc']:.2f}%")

    st.caption("P/L and Win-rate stats will come once live strategy results are recorded.")


# --------------------------------------------------------------------
# SCANNER BLOCK
# --------------------------------------------------------------------
def scanner_block(engine: StrategyEngine) -> None:
    st.subheader("Gold Scanner – LIVE Market Check")

    if not st.session_state["mt5_connected"]:
        st.info("Connect to MT5 above, then use this scanner.")
        return

    st.write(
        """When you press **Scan GOLD now**, the engine will:

- Find your GOLD symbol on this MT5 server (XAUUSD / GOLD / etc)
- Pull recent M15 candles
- Detect a simple impulse move and, if found, propose **one** momentum trade.

This is only the *first wiring* so you can see it working.
Later we can replace this with your full London / NY Setup-1 & Setup-2 logic."""
    )

    if st.button("Scan GOLD now"):
        try:
            signals = engine.scan_gold_momentum()
            st.session_state["last_scan_signals"] = signals
            st.session_state["last_scan_time"] = dt.datetime.now()
        except Exception as e:
            st.error(f"Error while scanning market: {e}")
            return

    last_time: Optional[dt.datetime] = st.session_state["last_scan_time"]
    signals: List[TradeSignal] = st.session_state["last_scan_signals"]

    if last_time is None:
        st.info("No scan has been run yet. Press the button above.")
        return

    st.write(f"Last scan time: **{last_time.strftime('%Y-%m-%d %H:%M:%S')}**")

    if not signals:
        st.warning("Scan completed. No valid GOLD setups detected at this moment.")
        return

    # Build a small table of suggested trades
    rows = []
    for sig in signals:
        rows.append(
            {
                "Time": sig.time.strftime("%Y-%m-%d %H:%M"),
                "Symbol": sig.symbol,
                "TF": sig.timeframe,
                "Direction": sig.direction.upper(),
                "Setup": sig.setup,
                "Entry": round(sig.entry, 2),
                "SL": round(sig.stop_loss, 2),
                "TP": round(sig.take_profit, 2),
                "R-multiple": sig.risk_r,
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    st.caption(
        "These are **paper** trade suggestions only. "
        "No orders are being sent to MT5 yet."
    )


# --------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------
def main() -> None:
    if not st.session_state["logged_in"]:
        show_login_screen()
        return

    st.title("Gold Gladiator – Owner Console")
    st.write(f"Logged in as **{st.session_state['username']}**")

    engine: StrategyEngine = st.session_state["engine"]

    _mode = risk_and_mode_block()

    st.markdown("---")

    connect_mt5_block()

    st.markdown("---")

    session_overview_block(engine)

    st.markdown("---")

    scanner_block(engine)


if __name__ == "__main__":
    main()
