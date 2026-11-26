#!/usr/bin/env python3
"""One-off pull: weekly + monthly Kalshi diesel/gas ladders for the multi-horizon backtest.

Writes CSVs only (never a database, rule 1):
  research/backtests/horizon_ladders/series.csv           which series exist + their settings
  research/backtests/horizon_ladders/markets_<S>.csv      every settled market (strike, result, settle value, times)
  research/backtests/horizon_ladders/candles_<S>.csv      daily candles (yes bid/ask/close, volume) per market
Runs on GitHub (the Kalshi API is not reachable from the chat workspace). Usage: python3 tools/pull_horizon_ladders.py
"""
import csv, json, os, time, urllib.request, urllib.error, datetime

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
OUT = os.path.join(os.path.dirname(__file__), "..", "research", "backtests", "horizon_ladders")
CANDIDATES = ["KXDIESELW", "KXDIESELMON", "KXDIESELM", "KXAAAGASW", "KXAAAGASM", "KXGASW", "KXGASM"]
os.makedirs(OUT, exist_ok=True)


def get(url, tries=4):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kalshi-twins-research)"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == tries - 1:
                raise
        except Exception:
            if i == tries - 1:
                raise
        time.sleep(5 * (i + 1))


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


def main():
    found = []
    for s in CANDIDATES:
        info = get(f"{KALSHI}/series/{s}")
        if not info or not info.get("series"):
            print(f"{s}: not found")
            continue
        se = info["series"]
        found.append({"series": s, "title": se.get("title"), "frequency": se.get("frequency"),
                      "fee_type": se.get("fee_type"), "fee_multiplier": se.get("fee_multiplier")})
        markets, cursor = [], ""
        while True:
            page = get(f"{KALSHI}/markets?series_ticker={s}&status=settled&limit=1000" + (f"&cursor={cursor}" if cursor else ""))
            markets += page.get("markets", [])
            cursor = page.get("cursor")
            if not cursor:
                break
        print(f"{s}: {len(markets)} settled markets")
        mcols = ["ticker", "event_ticker", "strike_type", "floor_strike", "cap_strike", "result", "expiration_value",
                 "open_time", "close_time", "expiration_time", "volume", "yes_sub_title"]
        with open(os.path.join(OUT, f"markets_{s}.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(mcols)
            for m in markets:
                w.writerow([m.get(c, m.get(c + "_fp")) for c in mcols])
        with open(os.path.join(OUT, f"candles_{s}.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ticker", "end_ts", "end_utc", "yes_bid", "yes_ask", "close", "volume", "open_interest"])
            for i, m in enumerate(markets):
                if not m.get("open_time") or not m.get("close_time"):
                    continue
                url = (f"{KALSHI}/series/{s}/markets/{m['ticker']}/candlesticks?start_ts={ts(m['open_time'])}"
                       f"&end_ts={ts(m['close_time'])}&period_interval=1440")
                try:
                    data = get(url, tries=2) or {}
                except Exception as e:
                    print(f"  skip {m['ticker']}: {e}")
                    continue
                for c in data.get("candlesticks", []):
                    price = c.get("price") or {}
                    w.writerow([m["ticker"], c["end_period_ts"],
                                datetime.datetime.fromtimestamp(c["end_period_ts"], datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),
                                dollars(c.get("yes_bid")), dollars(c.get("yes_ask")),
                                dollars(price.get("close_dollars", price.get("close"))),
                                c.get("volume_fp", c.get("volume")), c.get("open_interest_fp", c.get("open_interest"))])
                if i % 100 == 0:
                    print(f"  candles {i}/{len(markets)}")
                time.sleep(0.12)
    with open(os.path.join(OUT, "series.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["series", "title", "frequency", "fee_type", "fee_multiplier"])
        w.writeheader()
        w.writerows(found)
    print("done:", [f["series"] for f in found])


if __name__ == "__main__":
    main()
