#!/usr/bin/env python3
"""Pull history into data/kalshi_twins.db, then export CSVs. Stdlib only, no API keys.

1. Kalshi: every KXDIESELD market (settled + open) -> kalshi_markets,
   and each settled day's expiration_value -> diesel_daily.aaa_diesel (= AAA number).
2. Yahoo futures: Brent (BZ=F), NY Harbor ULSD (HO=F). FRED (often blocks cloud runners) as backup + EIA weekly diesel (GASDESW).
3. Kalshi candlesticks: hour-by-hour bid/ask/volume for every market -> kalshi_candles.
4. Export every table/view to data/exports/*.csv (GitHub renders these as tables).

Never overwrites a filled value (fills NULLs only). Safe to re-run.
Usage:  python3 tools/backfill.py            (all steps)
        python3 tools/backfill.py --export   (CSV export only)
"""
import csv, datetime, json, pathlib, re, sqlite3, sys, time, urllib.request, io

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kalshi_twins.db"
EXPORTS = ROOT / "data" / "exports"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ["KXDIESELD"]          # add more diesel/gas series here later (e.g. weekly)
FRED = {"brent_usd_bbl": "DCOILBRENTEU", "ulsd_nyh_usd_gal": "DDFUELNYH", "eia_weekly_diesel": "GASDESW"}
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
MONTHS = {m: i for i, m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"], 1)}


def get(url, tries=4):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kalshi-twins-research)"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode()
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"retry {i+1} {url[:60]}: {e}")
            time.sleep(10 * (i + 1))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def event_date(event_ticker):
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})$", event_ticker or "")
    if not m:
        return None
    return f"20{m.group(1)}-{MONTHS[m.group(2)]:02d}-{int(m.group(3)):02d}"


def pull_kalshi(con):
    total = 0
    for series in SERIES:
        for status in ("settled", "open", "closed"):
            cursor = ""
            while True:
                url = f"{KALSHI}/markets?series_ticker={series}&status={status}&limit=1000" + (f"&cursor={cursor}" if cursor else "")
                data = json.loads(get(url))
                for m in data.get("markets", []):
                    t = m["ticker"]
                    strike = num(m.get("floor_strike"))
                    if strike is None:
                        s = re.search(r"-T([\d.]+)$", t)
                        strike = float(s.group(1)) if s else None
                    con.execute("""INSERT OR REPLACE INTO kalshi_markets VALUES
                        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                        t, series, m.get("event_ticker"), event_date(m.get("event_ticker")), strike,
                        m.get("status"), m.get("result"), num(m.get("expiration_value")),
                        num(m.get("last_price_dollars")), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars")),
                        num(m.get("volume_fp")), num(m.get("open_interest_fp")),
                        m.get("open_time"), m.get("close_time"), json.dumps(m), NOW))
                    total += 1
                cursor = data.get("cursor") or ""
                if not cursor or not data.get("markets"):
                    break
                time.sleep(0.3)
    # One AAA value per settled day.
    rows = con.execute("""SELECT event_date, MAX(expiration_value) FROM kalshi_markets
                          WHERE series_ticker='KXDIESELD' AND expiration_value IS NOT NULL
                          GROUP BY event_date""").fetchall()
    for d, v in rows:
        upsert(con, d, {"aaa_diesel": v, "aaa_source": "kalshi_settlement"})
    print(f"kalshi: {total} markets, {len(rows)} settled days")


def pull_fred(con):
    start = "2022-01-01"
    for col, sid in FRED.items():
        text = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}", tries=1)
        n = 0
        for row in csv.DictReader(io.StringIO(text)):
            d = row.get("observation_date") or row.get("DATE")
            v = num(row.get(sid))
            if d and v is not None:
                fields = {col: v}
                if col == "brent_usd_bbl":
                    fields["brent_source"] = f"fred:{sid}"
                elif col == "ulsd_nyh_usd_gal":
                    fields["ulsd_source"] = f"fred:{sid}"
                upsert(con, d, fields)
                n += 1
        print(f"fred {sid}: {n} rows")


YAHOO = {"brent_usd_bbl": ("BZ=F", "brent_source"), "ulsd_nyh_usd_gal": ("HO=F", "ulsd_source")}


def pull_yahoo(con):
    """Daily closes of front-month futures: Brent (BZ=F, $/bbl) and NY Harbor ULSD (HO=F, $/gal)."""
    for col, (sym, src_col) in YAHOO.items():
        data = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5y&interval=1d"))
        res = data["chart"]["result"][0]
        off = res["meta"].get("gmtoffset", -18000)
        closes = res["indicators"]["quote"][0]["close"]
        n = 0
        for ts, v in zip(res["timestamp"], closes):
            if v is None:
                continue
            d = datetime.datetime.fromtimestamp(ts + off, datetime.timezone.utc).strftime("%Y-%m-%d")
            upsert(con, d, {col: round(v, 4), src_col: f"yahoo:{sym}"})
            n += 1
        print(f"yahoo {sym}: {n} rows")


def dollars(x):
    """Candle fields come as dollar strings (*_dollars) or cents ints; return $ float."""
    if isinstance(x, dict):
        x = x.get("close_dollars", x.get("close"))
    v = num(x)
    if v is None:
        return None
    return v / 100 if v > 1.0001 else v


def pull_candles(con, period=60, only_missing=True):
    """Hour-by-hour bid/ask/price/volume for every diesel market we know about."""
    rows = con.execute("""SELECT ticker, series_ticker, event_date, strike, open_time, close_time
                          FROM kalshi_markets WHERE open_time IS NOT NULL""").fetchall()
    done = {r[0] for r in con.execute("SELECT DISTINCT ticker FROM kalshi_candles WHERE period_min=?", (period,))}
    n_mk = n_c = 0
    for ticker, series, edate, strike, ot, ct in rows:
        if only_missing and ticker in done:
            continue
        to_ts = lambda s: int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())
        start, end = to_ts(ot), to_ts(ct)
        try:
            data = json.loads(get(f"{KALSHI}/series/{series}/markets/{ticker}/candlesticks?start_ts={start}&end_ts={end}&period_interval={period}", tries=2))
        except Exception as e:
            print(f"candles skip {ticker}: {e}")
            continue
        for c in data.get("candlesticks", []):
            ts = c["end_period_ts"]
            bid = dollars(c.get("yes_bid"))
            ask = dollars(c.get("yes_ask"))
            price = c.get("price") or {}
            last = dollars(price.get("close_dollars", price.get("close")))
            mid = round((bid + ask) / 2, 4) if bid is not None and ask is not None else None
            et = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M")
            con.execute("INSERT OR REPLACE INTO kalshi_candles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                ticker, edate, strike, period, ts, et, round((end - ts) / 3600, 2), bid, ask, mid,
                round(ask - bid, 4) if bid is not None and ask is not None else None, last,
                num(c.get("volume_fp", c.get("volume"))), num(c.get("open_interest_fp", c.get("open_interest"))),
                json.dumps(c)))
            n_c += 1
        n_mk += 1
        if n_mk % 100 == 0:
            con.commit()
            print(f"candles: {n_mk} markets...")
        time.sleep(0.12)
    print(f"candles: {n_mk} markets, {n_c} hourly rows")


def upsert(con, date, fields):
    con.execute("INSERT OR IGNORE INTO diesel_daily (date, updated_at) VALUES (?, ?)", (date, NOW))
    sets = ", ".join(f"{k} = COALESCE({k}, ?)" for k in fields)
    con.execute(f"UPDATE diesel_daily SET {sets}, updated_at = ? WHERE date = ?", (*fields.values(), NOW, date))


def export(con):
    EXPORTS.mkdir(parents=True, exist_ok=True)
    targets = {
        "diesel_breakdown.csv": "SELECT * FROM v_diesel_breakdown",
        "diesel_daily.csv": "SELECT * FROM diesel_daily ORDER BY date",
        "kalshi_markets.csv": "SELECT ticker, event_date, strike, status, result, expiration_value, last_price, yes_bid, yes_ask, volume, open_interest, close_time FROM kalshi_markets ORDER BY event_date, strike",
        "event_hourly.csv": "SELECT * FROM v_event_hourly",
        "sources.csv": "SELECT * FROM sources",
        "research_log.csv": "SELECT * FROM research_log ORDER BY date, id",
    }
    for name, sql in targets.items():
        cur = con.execute(sql)
        with open(EXPORTS / name, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([c[0] for c in cur.description])
            w.writerows(cur.fetchall())
    print(f"exported {len(targets)} CSVs -> {EXPORTS}")


def main():
    con = sqlite3.connect(DB)
    if "--export" not in sys.argv:
        for step in (pull_kalshi, pull_candles, pull_yahoo, pull_fred):
            try:
                step(con)
                con.commit()
            except Exception as e:          # one source failing must not block the others
                print(f"WARN {step.__name__}: {e}")
    export(con)
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
