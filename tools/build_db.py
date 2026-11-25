#!/usr/bin/env python3
"""Create / refresh data/kalshi_twins.db from schema.sql + hand-verified seed rows.

Safe to re-run any time: tables use CREATE IF NOT EXISTS and seeds use upserts
that never overwrite a value already filled by a better source.
Usage:  python3 tools/build_db.py
"""
import sqlite3, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kalshi_twins.db"
SCHEMA = ROOT / "data" / "schema.sql"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

SOURCES = [
    ("kalshi_settlement", "Kalshi KXDIESELD settled markets: expiration_value = AAA national diesel avg for that date (verified 2026-11-24: 5.7982 = AAA site 5.7982)",
     "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXDIESELD&status=settled", "daily", "Free, no key. Backfill history from here."),
    ("aaa_site", "AAA national average (updated daily by OPIS); shows current/yesterday/week/month/year ago only",
     "https://gasprices.aaa.com/", "daily", "No history download."),
    ("fred:DCOILBRENTEU", "Brent crude spot $/bbl (EIA via FRED)", "https://fred.stlouisfed.org/series/DCOILBRENTEU", "daily", "Lags ~1 week."),
    ("fred:DDFUELNYH", "NY Harbor ULSD No.2 diesel spot $/gal (EIA via FRED)", "https://fred.stlouisfed.org/series/DDFUELNYH", "daily", "Lags ~1 week."),
    ("fred:GASDESW", "EIA weekly U.S. on-highway diesel retail $/gal", "https://fred.stlouisfed.org/series/GASDESW", "weekly (Mon)", "Different survey than AAA; long history to 1994."),
    ("yahoo:BZ=F", "Brent front-month futures daily close $/bbl (Yahoo Finance)", "https://finance.yahoo.com/quote/BZ=F", "daily", "Futures, not spot; close proxy for Brent spot."),
    ("yahoo:HO=F", "NY Harbor ULSD front-month futures daily close $/gal (Yahoo Finance)", "https://finance.yahoo.com/quote/HO=F", "daily", "Futures proxy for NY Harbor ULSD wholesale."),
    ("manual:tradingeconomics", "Brent and heating-oil quotes read by hand from tradingeconomics.com", "https://tradingeconomics.com/commodity/heating-oil", "ad hoc", "CFD/OTC-based, not official benchmark; may differ by a cent or two."),
    ("eia:taxes", "Federal 24.4c + avg state 35.86c/gal (EIA, as of Jan 2026)", "https://www.eia.gov/energyexplained/index.php?page=diesel_prices", "rarely changes", ""),
]

# Hand-verified rows from the 2026-11-24 research session.
SEED_DAILY = [
    # date, aaa, aaa_src, brent, brent_src, ulsd, ulsd_src, notes
    ("2026-11-24", 5.7982, "kalshi_settlement+aaa_site", 90.76, "manual:tradingeconomics", 3.6954, "manual:tradingeconomics",
     "Session 1 teardown row. Delivery slice $1.50 vs ~$0.84 in Jan-2026 = retail lagging the wholesale drop."),
    ("2026-11-23", 5.8182, "aaa_site", None, None, None, None, "AAA 'yesterday' value read 2026-11-24"),
    ("2026-11-17", 5.9848, "aaa_site", None, None, None, None, "AAA 'week ago' value read 2026-11-24"),
    ("2026-10-24", 6.3374, "aaa_site", None, None, None, None, "AAA 'month ago' value read 2026-11-24"),
    ("2025-11-24", 3.7849, "aaa_site", None, None, None, None, "AAA 'year ago' value read 2026-11-24"),
]

SEED_LOG = [
    ("2026-11-24", "market-selection", "Liquidity scan of 12 candidate Kalshi markets. Under Dan's rules (no temperature, securities, or irregular events; daily/weekly cadence) gas + diesel rank first.", "Kalshi public API + category pages"),
    ("2026-11-24", "market-selection", "Diesel tomorrow ~$52K vol, diesel this week ~$85K, 30-yr mortgage weekly ~$84K, nat gas daily ~$29K, WTI daily ~$27K, gold daily ~$24K. Jobless claims ~5K contracts (thin).", "kalshi.com/category/economics, /commodities"),
    ("2026-11-24", "edge-thesis", "Edge = AAA retail diesel lags wholesale (NY Harbor ULSD) and crude. Forecast tomorrow's AAA from upstream prices; trade gaps vs Kalshi odds.", "EIA pump-component methodology"),
    ("2026-11-24", "data", "Kalshi settled KXDIESELD markets carry expiration_value = exact AAA diesel number -> free AAA history archive.", "Kalshi API, verified vs gasprices.aaa.com"),
    ("2026-11-24", "breakdown", "Nov 24: crude $2.1610 (37.3%), refining $1.5344 (26.5%), delivery+station $1.5002 (25.9%), taxes $0.6026 (10.4%) = $5.7982.", "Computed; see v_diesel_breakdown"),
]


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text())
    con.executemany("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?)", SOURCES)
    for d, aaa, aaas, b, bs, u, us, notes in SEED_DAILY:
        con.execute("""
            INSERT INTO diesel_daily (date, aaa_diesel, aaa_source, brent_usd_bbl, brent_source,
                                      ulsd_nyh_usd_gal, ulsd_source, notes, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(date) DO UPDATE SET
              aaa_diesel       = COALESCE(diesel_daily.aaa_diesel, excluded.aaa_diesel),
              aaa_source       = COALESCE(diesel_daily.aaa_source, excluded.aaa_source),
              brent_usd_bbl    = COALESCE(diesel_daily.brent_usd_bbl, excluded.brent_usd_bbl),
              brent_source     = COALESCE(diesel_daily.brent_source, excluded.brent_source),
              ulsd_nyh_usd_gal = COALESCE(diesel_daily.ulsd_nyh_usd_gal, excluded.ulsd_nyh_usd_gal),
              ulsd_source      = COALESCE(diesel_daily.ulsd_source, excluded.ulsd_source),
              notes            = COALESCE(diesel_daily.notes, excluded.notes)
        """, (d, aaa, aaas, b, bs, u, us, notes, NOW))
    if con.execute("SELECT COUNT(*) FROM research_log").fetchone()[0] == 0:
        con.executemany("INSERT INTO research_log (date, topic, finding, source) VALUES (?,?,?,?)", SEED_LOG)
    con.commit()
    con.close()
    print(f"OK -> {DB}")


if __name__ == "__main__":
    main()
