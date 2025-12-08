import pandas as pd
from engine import find_trades

# -------------------------------------------------
# 1. LOAD YOUR M15 + M5 DATA
# -------------------------------------------------
# For now we assume you have two CSV files in the project:
#   - XAUUSDM15.csv  (15-minute candles)
#   - XAUUSDM5.csv   (5-minute candles)
#
# Each must have at least:
#   time_ny, open, high, low, close
#
# If your column names are slightly different, we can adjust later.

m15_path = "XAUUSDM15.csv"
m5_path  = "XAUUSDM5.csv"

print("Loading data...")
m15 = pd.read_csv(m15_path)
m5  = pd.read_csv(m5_path)

# Make sure time_ny is a proper datetime column
m15["time_ny"] = pd.to_datetime(m15["time_ny"])
m5["time_ny"]  = pd.to_datetime(m5["time_ny"])

# -------------------------------------------------
# 2. RUN THE ENGINE
# -------------------------------------------------
print("Running Josh Gold Engine...")
trades = find_trades(m15, m5, rr_target=3.0)

print(f"\n✅ Engine finished. Total trades found: {len(trades)}\n")

# -------------------------------------------------
# 3. SHOW FIRST FEW TRADES
# -------------------------------------------------
if trades:
    rows = []
    for t in trades[:20]:  # first 20 trades
        rows.append({
            "time_ny":   t.time_ny,
            "session":   t.session,
            "setup":     t.setup_type,
            "direction": t.direction,
            "tf":        t.timeframe,
            "entry":     t.entry_price,
            "stop":      t.stop_price,
            "RR_target": t.rr_target,
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
else:
    print("No trades detected. We may need to adjust data or rules.")
