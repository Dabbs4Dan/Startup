#!/usr/bin/env python3
"""Pull FULL Kalshi history (live + archived) for AAA-settled series into kalshi_markets + kalshi_candles.
Series: diesel daily (since 2026-08-03), gas daily + weekly (since fall 2023, incl. old AAAGAS* tickers).
Event list -> markets per event (live endpoint, else /historical) -> hourly candles (live, else /historical).
Idempotent: skips markets that already have candles. Stdlib only.
Usage: python3 tools/backfill_history.py [SERIES ...]
"""
import json, re, sys, time, datetime, sqlite3, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kalshi_twins.db"
API = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = sys.argv[1:] or ["KXDIESELD", "KXAAAGASD", "KXAAAGASW"]
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
ET = datetime.timezone(datetime.timedelta(hours=-5))


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


num = lambda x: float(x) if x not in (None, "") else None


def dollars(x):
    if isinstance(x, dict):
        x = x.get("close_dollars", x.get("close"))
    v = num(x) if not isinstance(x, dict) else None
    return None if v is None else (v / 100 if v > 1.0001 else v)


def edate(ticker):
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})", ticker or "")
    return f"20{m.group(1)}-{MON[m.group(2)]:02d}-{int(m.group(3)):02d}" if m else None


def strike_of(m):
    for k in ("floor_strike", "cap_strike"):
        if m.get(k) is not None:
            return num(m[k])
    s = re.search(r"-T?([\d.]+)$", m["ticker"])
    return float(s.group(1)) if s else None


def events(series):
    out, cur = [], ""
    while True:
        d = get(f"{API}/events?series_ticker={series}&status=settled&limit=200" + (f"&cursor={cur}" if cur else ""))
        out += [e["event_ticker"] for e in d.get("events", [])]
        cur = d.get("cursor") or ""
        if not cur or not d.get("events"):
            return out


def main():
    con = sqlite3.connect(DB)
    con.executescript((ROOT / "data" / "schema.sql").read_text())
    have_candles = {r[0] for r in con.execute("SELECT DISTINCT ticker FROM kalshi_candles WHERE period_min=60")}
    to_ts = lambda s: int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())
    for series in SERIES:
        evs = events(series)
        print(f"{series}: {len(evs)} settled events")
        nm = nc = 0
        for ev in evs:
            ms = get(f"{API}/markets?event_ticker={ev}&limit=200").get("markets") or \
                 get(f"{API}/historical/markets?event_ticker={ev}&limit=200").get("markets") or []
            for m in ms:
                t = m["ticker"]
                con.execute("INSERT OR REPLACE INTO kalshi_markets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                    t, series, ev, edate(ev), strike_of(m), m.get("status"), m.get("result"), num(m.get("expiration_value")),
                    num(m.get("last_price_dollars")), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars")),
                    num(m.get("volume_fp")), num(m.get("open_interest_fp")), m.get("open_time"), m.get("close_time"),
                    None, NOW))
                nm += 1
                if t in have_candles or not m.get("open_time") or not m.get("close_time"):
                    continue
                if (num(m.get("volume_fp")) or 0) == 0:          # never traded -> no useful candles
                    continue
                st, en = to_ts(m["open_time"]), to_ts(m["close_time"])
                if en - st > 2 * 86400:                           # keep DB small: last 48h before close is enough
                    st = en - 2 * 86400
                ser = m.get("series_ticker") or t.split("-")[0]
                q = f"start_ts={st}&end_ts={en}&period_interval=60"
                cs = get(f"{API}/series/{ser}/markets/{t}/candlesticks?{q}").get("candlesticks") or \
                     get(f"{API}/historical/markets/{t}/candlesticks?{q}").get("candlesticks") or []
                for c in cs:
                    ts = c["end_period_ts"]; bid = dollars(c.get("yes_bid")); ask = dollars(c.get("yes_ask"))
                    pr = c.get("price") or {}
                    con.execute("INSERT OR REPLACE INTO kalshi_candles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                        t, edate(ev), strike_of(m), 60, ts, datetime.datetime.fromtimestamp(ts, ET).strftime("%Y-%m-%d %H:%M"),
                        round((en - ts) / 3600, 2), bid, ask,
                        round((bid + ask) / 2, 4) if bid is not None and ask is not None else None,
                        round(ask - bid, 4) if bid is not None and ask is not None else None,
                        dollars(pr.get("close_dollars", pr.get("close"))),
                        num(c.get("volume_fp", c.get("volume"))), num(c.get("open_interest_fp", c.get("open_interest"))),
                        None))                                     # raw_json skipped for history (size)
                    nc += 1
                time.sleep(0.15)
            con.commit()
        print(f"{series}: {nm} markets stored, {nc} new hourly candles")
        if series == "KXDIESELD":   # copy settled AAA values into diesel_daily (fills blanks only)
            for d, v in con.execute("""SELECT event_date, MAX(expiration_value) FROM kalshi_markets
                                      WHERE series_ticker='KXDIESELD' AND expiration_value IS NOT NULL GROUP BY event_date""").fetchall():
                con.execute("INSERT OR IGNORE INTO diesel_daily (date, updated_at) VALUES (?, ?)", (d, NOW))
                con.execute("UPDATE diesel_daily SET aaa_diesel=COALESCE(aaa_diesel, ?), aaa_source=COALESCE(aaa_source,'kalshi_settlement'), updated_at=? WHERE date=?", (v, NOW, d))
            con.commit()
    con.close()


if __name__ == "__main__":
    main()
