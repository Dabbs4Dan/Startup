#!/usr/bin/env python3
"""Daily recorders for inputs that have NO free history (history starts the day we start saving).
Runs on GitHub (the runner can reach AAA + Yahoo; Claude's sandbox can't).

1. AAA state diesel averages (51) -> table aaa_state_daily (date, state, current, yesterday, week, month, year ago).
   Feeds the mini-AAA / national roll-up weights (Inputs Map #48, #51, #52; formula #16).
2. HO futures price at 10:00 AM ET from Yahoo 5-minute bars (last ~60 days in one request)
   -> research/connectivity/ho_10am.json  (Inputs Map #35; removes the look-ahead in model F).
Each part fails soft: an error is printed and the rest still runs.
Usage: python3 tools/daily_recorders.py
"""
import json, sqlite3, pathlib, datetime, time, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from connectivity_pull import get, aaa_states  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ET = datetime.timezone(datetime.timedelta(hours=-5))


def to_num(x):
    try:
        return float(str(x).replace("$", "").strip())
    except ValueError:
        return None


def record_states():
    con = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
    con.execute("""CREATE TABLE IF NOT EXISTS aaa_state_daily (
        pulled_date TEXT, as_of TEXT, state TEXT, diesel_current REAL, diesel_yesterday REAL,
        diesel_week_ago REAL, diesel_month_ago REAL, diesel_year_ago REAL, PRIMARY KEY (as_of, state))""")
    res, n = aaa_states(), 0
    today = datetime.datetime.now(ET).date().isoformat()
    for s, v in res.items():
        tabs = v.get("tables") or []
        if not tabs:
            continue
        t = tabs[0]
        col = lambda label: to_num(t.get(label, [None] * 4)[3]) if len(t.get(label, [])) > 3 else None
        con.execute("INSERT OR REPLACE INTO aaa_state_daily VALUES (?,?,?,?,?,?,?,?)",
                    (today, v.get("as_of"), s, col("Current Avg."), col("Yesterday Avg."), col("Week Ago Avg."),
                     col("Month Ago Avg."), col("Year Ago Avg.")))
        n += 1
    con.commit()
    print(f"aaa_state_daily: {n} states recorded")


def record_ho_10am():
    p1 = int((datetime.datetime.now(ET) - datetime.timedelta(days=59)).timestamp())
    p2 = int(datetime.datetime.now(ET).timestamp())
    body = None
    for host in ("query1", "query2"):
        time.sleep(10)
        st, body = get(f"https://{host}.finance.yahoo.com/v8/finance/chart/HO=F?interval=5m&period1={p1}&period2={p2}")
        if st == 200:
            break
    else:
        print("ho_10am: Yahoo refused:", str(body)[:200])
        record_ho_stooq()
        return
    r = json.loads(body)["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    out = {}
    for ts, c in zip(r.get("timestamp", []), q["close"]):
        t = datetime.datetime.fromtimestamp(ts, ET)
        if c is not None and t.strftime("%H:%M") <= "10:00":          # last 5-min close at or before 10:00 AM ET
            out[t.date().isoformat()] = round(c, 4)
    path = ROOT / "research" / "connectivity" / "ho_10am.json"
    old = json.loads(path.read_text()).get("ho_10am", {}) if path.exists() else {}
    old.update(out)
    path.write_text(json.dumps({"note": "HO=F last 5-min close at or before 10:00 AM ET (Yahoo)", "ho_10am": dict(sorted(old.items()))}, indent=1))
    print(f"ho_10am: {len(out)} days ({min(out) if out else '-'} -> {max(out) if out else '-'})")


def record_ho_stooq():
    """Fallback: Stooq 5-min bars for HO futures (ho.f). Saves the raw file for inspection + any 10 AM values."""
    st, body = get("https://stooq.com/q/d/l/?s=ho.f&i=5")
    raw = ROOT / "research" / "connectivity" / "ho_stooq_5m.csv"
    if st != 200 or not body or "Date" not in body[:50]:
        print("ho_10am (stooq): no data:", str(body)[:120])
        return
    raw.write_text(body)
    out = {}
    for line in body.splitlines()[1:]:
        f = line.split(",")
        if len(f) >= 6 and f[1][:5] <= "10:00":   # Stooq times are exchange/local; checked by Claude before use
            out[f[0]] = float(f[5])
    print(f"ho_10am (stooq): {len(body.splitlines())-1} bars saved to {raw.name}; {len(out)} days with a bar <= 10:00 (timezone unverified)")


if __name__ == "__main__":
    for fn in (record_states, record_ho_10am):
        try:
            fn()
        except Exception as e:  # noqa
            print(f"{fn.__name__} failed: {e}")
