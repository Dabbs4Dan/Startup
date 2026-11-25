#!/usr/bin/env python3
"""Live recorder (free, GitHub-only). Saves data that has NO history anywhere: if we don't record it today, it's gone.

One "shift" = a loop that takes a snapshot every few minutes for up to ~5.5 hours, then stops.
Four shifts a day cover 24 hours (see .github/workflows/live_recorder.yml). No paid server needed.

Feeds (each fails soft; one broken feed never stops the others):
  1. kalshi_markets   every 5 min   every open KXDIESELD strike: yes bid/ask, last, volume, open interest
                                     (Inputs Map: Yes %, No %, spread, strike ladder, volume)          [Custom Build CB5-lite]
  2. kalshi_orderbook every 15 min  full order book (every price level + contracts waiting) for the
                                     most-traded live strikes -> slippage + "big order" signals         [CB5]
  3. aaa_national     every 15 min  AAA national diesel (current + yesterday + "price as of" date);
                                     aaa_flips.csv logs the first snapshot where the number changed    [CB4 flip time]
  4. futures          every 5 min   delayed HO (diesel futures) + Brent + WTI quotes from Stooq          [CB3]

Output: data/live/<feed>/YYYY-MM-DD.csv (one file per ET day, append-only, raw). Pushed to GitHub about every hour.
Usage:  python3 tools/live_recorder.py [--minutes 330] [--every 5] [--once]
"""
import argparse, csv, datetime, json, pathlib, re, subprocess, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT / "data" / "live"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ["KXDIESELD"]                 # add "KXAAAGASD" here to record the gas twin too
BOOK_TOP_N = 6                         # order books for this many live strikes per snapshot
STOOQ = {"HO": "ho.f", "BRENT": "cb.f", "WTI": "cl.f"}
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}


def et_now():
    """US Eastern time with daylight saving (EDT 2nd Sun Mar -> 1st Sun Nov)."""
    utc = datetime.datetime.now(datetime.timezone.utc)
    y = utc.year
    mar = datetime.datetime(y, 3, 8, 7, tzinfo=datetime.timezone.utc)
    nov = datetime.datetime(y, 11, 1, 6, tzinfo=datetime.timezone.utc)
    start = mar + datetime.timedelta(days=(6 - mar.weekday()) % 7)
    end = nov + datetime.timedelta(days=(6 - nov.weekday()) % 7)
    off = -4 if start <= utc < end else -5
    return utc, utc.astimezone(datetime.timezone(datetime.timedelta(hours=off)))


def fetch(url, tries=3, as_json=False):
    err = ""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                body = r.read().decode("utf-8", "replace")
                return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code == 404:
                break
            time.sleep(5 * (i + 1) if e.code == 429 else 2)
        except Exception as e:  # noqa
            err = str(e)
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{err} :: {url[:90]}")


def append(feed, header, rows, day):
    if not rows:
        return
    path = LIVE / feed / f"{day}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerows(rows)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------- feeds ----------

def kalshi_markets(ts_utc, ts_et, day, state):
    rows, live = [], []
    for series in SERIES:
        data = fetch(f"{KALSHI}/markets?series_ticker={series}&status=open&limit=200", as_json=True)
        for m in data.get("markets", []):
            yb, ya = num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars"))
            vol = num(m.get("volume_fp")) or num(m.get("volume"))
            rows.append([ts_utc, ts_et, series, m.get("event_ticker"), m.get("ticker"), num(m.get("floor_strike")),
                         yb, ya, num(m.get("no_bid_dollars")), num(m.get("no_ask_dollars")),
                         num(m.get("last_price_dollars")), vol, num(m.get("volume_24h_fp")) or num(m.get("volume_24h")),
                         num(m.get("open_interest_fp")) or num(m.get("open_interest")), m.get("close_time")])
            mid = (yb + ya) / 2 if yb is not None and ya is not None else None
            if mid is not None and 0.03 <= mid <= 0.97:
                live.append((vol or 0, m.get("ticker"), m.get("event_ticker")))
    append("kalshi_markets", ["ts_utc", "ts_et", "series", "event", "ticker", "strike", "yes_bid", "yes_ask",
                              "no_bid", "no_ask", "last", "volume", "volume_24h", "open_interest", "close_time"], rows, day)
    state["live"] = sorted(live, reverse=True)[:BOOK_TOP_N]
    return f"{len(rows)} strikes, {len(state['live'])} live"


def kalshi_orderbook(ts_utc, ts_et, day, state):
    rows = []
    for _, ticker, event in state.get("live", []):
        ob = fetch(f"{KALSHI}/markets/{ticker}/orderbook", as_json=True).get("orderbook") or {}
        for key, levels in ob.items():          # yes / no (cents) or yes_dollars / no_dollars, whichever the API sends
            if not isinstance(levels, list):
                continue
            side = "yes" if key.startswith("yes") else "no" if key.startswith("no") else key
            for lvl in levels:
                if isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
                    rows.append([ts_utc, ts_et, event, ticker, key, side, lvl[0], lvl[1]])
        time.sleep(0.3)
    append("kalshi_orderbook", ["ts_utc", "ts_et", "event", "ticker", "field", "side", "price", "contracts"], rows, day)
    return f"{len(rows)} levels over {len(state.get('live', []))} strikes"


def aaa_national(ts_utc, ts_et, day, state):
    html = fetch("https://gasprices.aaa.com/")
    asof = re.search(r"Price as of\s*([0-9/]+)", html)
    asof = asof.group(1) if asof else None
    cur = yest = None
    for tb in re.findall(r"<table[^>]*>(.*?)</table>", html, re.S | re.I):
        if "Current Avg" not in tb:
            continue
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S | re.I):
            cells = [re.sub(r"<[^>]+>|\s+", " ", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
            if len(cells) >= 5 and cells[0].startswith("Current"):
                cur = num(cells[4].replace("$", ""))
            if len(cells) >= 5 and cells[0].startswith("Yesterday"):
                yest = num(cells[4].replace("$", ""))
        break                                    # first table = national
    append("aaa_national", ["ts_utc", "ts_et", "price_as_of", "diesel_current", "diesel_yesterday"],
           [[ts_utc, ts_et, asof, cur, yest]], day)
    last = state.get("aaa_last")
    if cur is not None and last is not None and (cur, asof) != last:
        flips = LIVE / "aaa_flips.csv"
        new = not flips.exists()
        with flips.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["first_seen_utc", "first_seen_et", "price_as_of", "diesel_new", "diesel_before", "as_of_before"])
            w.writerow([ts_utc, ts_et, asof, cur, last[0], last[1]])
    if cur is not None:
        state["aaa_last"] = (cur, asof)
    return f"diesel {cur} as of {asof}"


def futures(ts_utc, ts_et, day, state):
    rows = []
    for name, sym in STOOQ.items():
        body = fetch(f"https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv")
        lines = [l for l in body.strip().splitlines() if l]
        if len(lines) >= 2:
            f = lines[1].split(",")
            if len(f) >= 7 and f[6] not in ("N/D", ""):
                rows.append([ts_utc, ts_et, name, sym, f[1], f[2], num(f[3]), num(f[4]), num(f[5]), num(f[6])])
    append("futures", ["ts_utc", "ts_et", "name", "symbol", "quote_date", "quote_time", "open", "high", "low", "last"], rows, day)
    return f"{len(rows)}/{len(STOOQ)} quotes"


FEEDS = [  # (feed, run every Nth snapshot)  — with --every 5: 1 = 5 min, 3 = 15 min
    (kalshi_markets, 1),
    (kalshi_orderbook, 3),
    (aaa_national, 3),
    (futures, 1),
]


def push(msg):
    cmds = [["git", "add", "data/live"], ["git", "commit", "-q", "-m", msg]]
    for c in cmds:
        if subprocess.run(c, cwd=ROOT).returncode != 0 and c[1] == "commit":
            return                               # nothing new
    for _ in range(4):
        subprocess.run(["git", "pull", "-q", "--rebase", "-X", "theirs", "origin", "kalshi-twins"], cwd=ROOT)
        if subprocess.run(["git", "push", "-q", "origin", "HEAD:kalshi-twins"], cwd=ROOT).returncode == 0:
            return
        time.sleep(15)


def seed_aaa(state):
    """Start flip detection from the last value on disk, so a new shift doesn't miss a flip at the seam."""
    files = sorted((LIVE / "aaa_national").glob("*.csv"))
    if files:
        rows = list(csv.reader(files[-1].open()))
        for r in reversed(rows[1:]):
            if len(r) >= 4 and r[3]:
                state["aaa_last"] = (float(r[3]), r[2] or None)
                return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=330)
    ap.add_argument("--every", type=int, default=5)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--push-every", type=int, default=60, help="minutes between git pushes (0 = never)")
    a = ap.parse_args()
    state, n = {}, 0
    seed_aaa(state)
    t_end = time.time() + a.minutes * 60
    last_push = time.time()
    while True:
        t0 = time.time()
        u, e = et_now()
        ts_utc, ts_et, day = u.strftime("%Y-%m-%dT%H:%M:%SZ"), e.strftime("%Y-%m-%d %H:%M"), e.date().isoformat()
        parts = []
        for fn, k in FEEDS:
            if n % k:
                continue
            try:
                parts.append(f"{fn.__name__}: {fn(ts_utc, ts_et, day, state)}")
            except Exception as ex:  # noqa
                parts.append(f"{fn.__name__}: FAILED {ex}")
        print(f"[{ts_et} ET] " + " | ".join(parts), flush=True)
        n += 1
        if a.once or time.time() + a.every * 60 > t_end:
            break
        if a.push_every and time.time() - last_push > a.push_every * 60:
            push(f"live: snapshots to {ts_et} ET")
            last_push = time.time()
        time.sleep(max(5, a.every * 60 - (time.time() - t0)))


if __name__ == "__main__":
    sys.exit(main())
