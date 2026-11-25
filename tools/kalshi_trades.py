#!/usr/bin/env python3
"""Kalshi trade tape + 1-minute candles for KXDIESELD (Custom Build CB6 + CB7). Runs on GitHub (sandbox can't reach Kalshi).

1. kalshi_trades: every trade (time, price, size, taker side) for every traded line of the last N events.
2. kalshi_candles (period_min=1): 1-minute candles for the 3 most-traded lines of each event (last 16 h before close).
Fills new data only; safe to re-run daily. Usage: python3 tools/kalshi_trades.py [n_events=60]
"""
import sys, json, time, sqlite3, pathlib, datetime, urllib.request, urllib.error, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.elections.kalshi.com/trade-api/v2"
ET = datetime.timezone(datetime.timedelta(hours=-5))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
sys.path.insert(0, str(ROOT / "tools"))
import product  # noqa: E402
SER_IN = ",".join("'%s'" % s for s in product.SERIES)
con = sqlite3.connect(product.DB)
con.execute("""CREATE TABLE IF NOT EXISTS kalshi_trades (
    trade_id TEXT PRIMARY KEY, ticker TEXT, event_date TEXT, strike REAL, created_time TEXT, created_et TEXT,
    yes_price REAL, no_price REAL, count REAL, taker_side TEXT)""")
con.execute("CREATE INDEX IF NOT EXISTS ix_trades_ticker ON kalshi_trades(ticker)")


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kalshi-twins-research/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            time.sleep(5 * (i + 1) if e.code == 429 else 2)
        except Exception:
            time.sleep(3 * (i + 1))
    return {}


def price(t, k):
    v = t.get(f"{k}_dollars", t.get(k))
    if v in (None, ""):
        return None
    v = float(v)
    return v / 100 if v > 1.0001 else v


def to_ts(s):
    return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


events = [r[0] for r in con.execute(f"SELECT DISTINCT event_date FROM kalshi_markets WHERE series_ticker IN ({SER_IN}) ORDER BY 1")][-N:]
done = {r[0] for r in con.execute("SELECT DISTINCT ticker FROM kalshi_trades")}
nt = nc = 0
for E in events:
    mk = con.execute("""SELECT ticker, strike, volume, open_time, close_time, status FROM kalshi_markets
                        WHERE event_date=? AND series_ticker IN ({SER_IN})""".format(SER_IN=SER_IN), (E,)).fetchall()
    settled = all((s or "") in ("settled", "finalized", "determined") for *_, s in mk)
    # ---- trades ----
    for t, k, vol, ot, ct, st in mk:
        if not vol or (t in done and settled):
            continue
        cursor = ""
        while True:
            q = urllib.parse.urlencode({"ticker": t, "limit": 1000, **({"cursor": cursor} if cursor else {})})
            d = get(f"{API}/markets/trades?{q}")
            if not d.get("trades"):
                d = get(f"{API}/historical/trades?{q}")
            for tr in d.get("trades") or []:
                ts = tr.get("created_time")
                con.execute("INSERT OR IGNORE INTO kalshi_trades VALUES (?,?,?,?,?,?,?,?,?,?)", (
                    tr.get("trade_id"), t, E, k, ts,
                    datetime.datetime.fromtimestamp(to_ts(ts), ET).strftime("%Y-%m-%d %H:%M:%S") if ts else None,
                    price(tr, "yes_price"), price(tr, "no_price"), float(tr.get("count_fp", tr.get("count")) or 0), tr.get("taker_side")))
                nt += 1
            cursor = d.get("cursor") or ""
            time.sleep(0.15)
            if not cursor:
                break
    # ---- 1-minute candles for the 3 most-traded lines ----
    top = sorted([m for m in mk if m[2]], key=lambda m: -m[2])[:3]
    for t, k, vol, ot, ct, st in top:
        if not ct or con.execute("SELECT 1 FROM kalshi_candles WHERE ticker=? AND period_min=1 LIMIT 1", (t,)).fetchone():
            continue
        en = to_ts(ct); sa = max(to_ts(ot) if ot else en - 16 * 3600, en - 16 * 3600)
        qs = f"start_ts={sa}&end_ts={en}&period_interval=1"
        cs = get(f"{API}/series/{t.split('-')[0]}/markets/{t}/candlesticks?{qs}").get("candlesticks") or \
             get(f"{API}/historical/markets/{t}/candlesticks?{qs}").get("candlesticks") or []
        for c in cs:
            ts = c["end_period_ts"]
            b, a = price(c.get("yes_bid") or {}, "close"), price(c.get("yes_ask") or {}, "close")
            pr = c.get("price") or {}
            con.execute("INSERT OR REPLACE INTO kalshi_candles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                t, E, k, 1, ts, datetime.datetime.fromtimestamp(ts, ET).strftime("%Y-%m-%d %H:%M"), round((en - ts) / 3600, 3),
                b, a, round((b + a) / 2, 4) if b is not None and a is not None else None,
                round(a - b, 4) if b is not None and a is not None else None, price(pr, "close"),
                float(c.get("volume_fp", c.get("volume")) or 0), float(c.get("open_interest_fp", c.get("open_interest")) or 0), None))
            nc += 1
        time.sleep(0.15)
    con.commit()
print(f"kalshi_trades: +{nt} trades | 1-min candles: +{nc} rows | events {events[0]} -> {events[-1]}")
print("totals:", con.execute("SELECT COUNT(*), COUNT(DISTINCT ticker) FROM kalshi_trades").fetchone(),
      con.execute("SELECT COUNT(*) FROM kalshi_candles WHERE period_min=1").fetchone())
