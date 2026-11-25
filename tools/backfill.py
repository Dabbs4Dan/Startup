#!/usr/bin/env python3
"""Pull history into data/kalshi_twins.db, then export CSVs. Stdlib only, no API keys.

1. Kalshi: every KXDIESELD market (settled + open) -> kalshi_markets,
   and each settled day's expiration_value -> diesel_daily.aaa_diesel (= AAA number).
2. FRED: Brent (DCOILBRENTEU), NY Harbor ULSD (DDFUELNYH), EIA weekly diesel (GASDESW).
3. Export every table/view to data/exports/*.csv (GitHub renders these as tables).

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


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kalshi-twins-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


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
        text = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}")
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
        for step in (pull_kalshi, pull_fred):
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
