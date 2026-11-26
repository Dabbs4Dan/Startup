#!/usr/bin/env python3
"""Kalshi FULL history for one series: every settled market + hourly candles, from BOTH data tiers.

Kalshi keeps recent data on the live API and moves older settled markets to /historical/* (see
https://docs.kalshi.com/getting_started/historical_data). Earlier pulls only read the live tier.
Replaces tools/pull_horizon_ladders.py (weekly/monthly, live tier, daily candles only).

Writes (CSV only, never a database):
  data/lake/kalshi/<SERIES>/markets.csv          one row per market (strike, result, settle value, times, tier)
  data/lake/kalshi/<SERIES>/candles_60m.csv.gz   hourly yes bid/ask/last/volume/open interest per market
  data/lake/kalshi/<SERIES>/_meta.json           counts, date range, cutoff, raw samples (for vetting)
Resumable: markets already in the candle file are skipped. Runs on GitHub (the API is not reachable from chat).
Usage: python3 tools/pull_kalshi_history.py KXDIESELW
"""
import csv, datetime, gzip, io, json, os, sys, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lake", "kalshi")
MCOLS = ["ticker", "event_ticker", "strike_type", "floor_strike", "cap_strike", "result", "expiration_value",
         "open_time", "close_time", "expiration_time", "settlement_ts", "volume", "open_interest", "yes_sub_title"]
CCOLS = ["ticker", "end_ts", "yes_bid", "yes_ask", "last", "volume", "open_interest"]
_lock, _last = threading.Lock(), [0.0]


def get(url, tries=5):
    for i in range(tries):
        with _lock:                                   # global pacing: ~12 requests / second
            wait = _last[0] + 0.085 - time.time()
            if wait > 0:
                time.sleep(wait)
            _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kalshi-twins-research)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return {"_http": e.code, "_body": e.read().decode()[:300]}
            time.sleep(2 * (i + 1) if e.code != 429 else 6 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return {"_http": "failed"}


def dollars(x):
    if isinstance(x, dict):
        x = x.get("close_dollars", x.get("close"))
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v / 100 if v > 1.0001 else v


def ts(s):
    return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def page_all(base):
    out, cursor, first = [], "", None
    while True:
        page = get(base + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
        if first is None:
            first = {k: (v if not isinstance(v, list) else f"list[{len(v)}]") for k, v in page.items()}
        out += page.get("markets", []) or []
        cursor = page.get("cursor")
        if not cursor or not page.get("markets"):
            return out, first


def candles(series, m):
    """Hourly candles for one market; tries the tier it came from first, then the other."""
    if not m.get("open_time") or not m.get("close_time"):
        return []
    a, b = ts(m["open_time"]), ts(m["close_time"]) + 3600
    urls = [f"{KALSHI}/series/{series}/markets/{m['ticker']}/candlesticks", f"{KALSHI}/historical/markets/{m['ticker']}/candlesticks"]
    if m["_tier"] == "historical":
        urls.reverse()
    rows = []
    for u in urls:
        s = a
        while s < b:                                  # 4,000 hourly candles per call
            e = min(b, s + 4000 * 3600)
            data = get(f"{u}?start_ts={s}&end_ts={e}&period_interval=60", tries=3)
            for c in data.get("candlesticks", []) or []:
                price = c.get("price") or {}
                yb, ya = dollars(c.get("yes_bid")), dollars(c.get("yes_ask"))
                if yb is None and ya is None:
                    continue
                rows.append([m["ticker"], c.get("end_period_ts"), yb, ya,
                             dollars(price.get("close_dollars", price.get("close"))),
                             c.get("volume_fp", c.get("volume")), c.get("open_interest_fp", c.get("open_interest"))])
            s = e
        if rows:
            break
    return rows


def main(series):
    out = os.path.join(ROOT, series)
    os.makedirs(out, exist_ok=True)
    meta = {"series": series, "pulled_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")}
    info = get(f"{KALSHI}/series/{series}")
    if not info.get("series"):
        print(f"{series}: series not found ({info.get('_http')})")
        meta["found"] = False
        json.dump(meta, open(os.path.join(out, "_meta.json"), "w"), indent=1)
        return
    se = info["series"]
    meta.update({"found": True, "title": se.get("title"), "frequency": se.get("frequency"), "fee_type": se.get("fee_type"),
                 "fee_multiplier": se.get("fee_multiplier"), "cutoff": get(f"{KALSHI}/historical/cutoff")})
    live, f1 = page_all(f"{KALSHI}/markets?series_ticker={series}&status=settled&limit=1000")
    hist, f2 = page_all(f"{KALSHI}/historical/markets?series_ticker={series}&limit=1000")
    meta["first_page_live"], meta["first_page_historical"] = f1, f2
    markets = {}
    for tier, lst in (("historical", hist), ("live", live)):
        for m in lst:
            m["_tier"] = tier
            markets[m["ticker"]] = m
    ms = sorted(markets.values(), key=lambda m: (m.get("close_time") or "", m["ticker"]))
    print(f"{series}: live {len(live)} + historical {len(hist)} = {len(ms)} unique settled markets")
    if hist:
        meta["sample_historical_market"] = {k: v for k, v in hist[0].items() if k != "rules_secondary"}
    with open(os.path.join(out, "markets.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(MCOLS + ["tier"])
        for m in ms:
            w.writerow([m.get(c, m.get(c + "_fp", m.get(c + "_dollars"))) for c in MCOLS] + [m["_tier"]])
    # candles (resumable)
    cpath, done = os.path.join(out, "candles_60m.csv.gz"), set()
    if os.path.exists(cpath):
        with gzip.open(cpath, "rt") as fh:
            done = {r[0] for r in csv.reader(fh)} - {"ticker"}
    todo = [m for m in ms if m["ticker"] not in done]
    print(f"  candles: {len(done)} markets already saved, {len(todo)} to pull")
    n_rows, empty, t0 = 0, 0, time.time()
    with gzip.open(cpath, "at", newline="") as fh:
        w = csv.writer(fh)
        if not done:
            w.writerow(CCOLS)
        with ThreadPoolExecutor(max_workers=8) as ex:
            for i, rows in enumerate(ex.map(lambda m: candles(series, m), todo)):
                w.writerows(rows)
                n_rows += len(rows)
                empty += not rows
                if i % 500 == 0:
                    print(f"  {i}/{len(todo)} markets, {n_rows} candle rows, {empty} empty, {int(time.time()-t0)}s", flush=True)
                if time.time() - t0 > 100 * 60:        # leave time to commit; next run resumes
                    print("  time budget reached; stopping early (resumable)")
                    break
    closes = [m.get("close_time") for m in ms if m.get("close_time")]
    meta.update({"markets_live": len(live), "markets_historical": len(hist), "markets_total": len(ms),
                 "events": len({m.get("event_ticker") for m in ms}), "first_close": min(closes) if closes else None,
                 "last_close": max(closes) if closes else None, "candle_rows_added": n_rows, "markets_no_candles": empty})
    json.dump(meta, open(os.path.join(out, "_meta.json"), "w"), indent=1, default=str)
    print(json.dumps({k: meta[k] for k in ("markets_live", "markets_historical", "events", "first_close", "last_close", "candle_rows_added", "markets_no_candles")}))


if __name__ == "__main__":
    main(sys.argv[1])
