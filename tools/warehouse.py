#!/usr/bin/env python3
"""The Warehouse: ONE place to query every dataset (history + live) for diesel and gas, using DuckDB.

Nothing is copied or migrated. The warehouse reads every source where it already lives:
  - SQLite DBs: data/kalshi_twins.db (diesel), data/gas/kalshi_gas.db (gas)       -> schemas  diesel.*, gas.*
  - History zone: data/lake/history/*.csv (EIA, Yahoo intraday, Wayback AAA)    -> schema   hist.*
  - Live zone: data/live/<feed>/*.csv (5-min recorder, truckstops)              -> schema   live.*
  - Engine Room files (Wayback AAA state pages, gas state files)                -> schema   er.*
On top sit the UNIFIED views every algo/backtest should read (one shape, both products, both eras):
  aaa_daily · state_prices · ladder · trades · futures_bars · spot_daily · eia_weekly · orderbook · truckstops
Each row has `era` = 'history' (before the live recorder started) or 'since_live' -> "backtest since inception"
is the same query with WHERE era = 'since_live'.

Usage:
  python3 tools/warehouse.py catalog             -> data/warehouse_catalog.csv + .md (what we have, rows, dates)
  python3 tools/warehouse.py sql "SELECT ..."    -> prints the result
  python3 tools/warehouse.py export VIEW FILE    -> writes a view to CSV/Parquet
In Python:  from warehouse import connect; con = connect(); con.sql("select * from aaa_daily").df()
"""
import csv, datetime, glob, pathlib, sqlite3, sys

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
GO_LIVE = "2026-11-25 19:21:00"           # first live-recorder snapshot (UTC) = start of "since inception"
DBS = {"diesel": ROOT / "data" / "kalshi_twins.db", "gas": ROOT / "data" / "gas" / "kalshi_gas.db"}
SKIP_TABLES = {"sqlite_sequence"}
ERA = f"CASE WHEN ts_utc >= TIMESTAMP '{GO_LIVE}' THEN 'since_live' ELSE 'history' END"


def _files(pattern):
    return sorted(glob.glob(str(ROOT / pattern)))


def _csv(pattern):
    opts = ("union_by_name=true, filename=true, all_varchar=true, header=true, delim=',', "
            "quote='\"', escape='\"', null_padding=true, strict_mode=false")
    return f"read_csv('{ROOT / pattern}', {opts})"


def _attach_sqlite(con, name, path):
    """Attach a SQLite DB as a schema. Uses DuckDB's sqlite extension if it can load; otherwise copies tables in."""
    try:
        con.execute("LOAD sqlite")
    except Exception:  # noqa
        try:
            con.execute("INSTALL sqlite; LOAD sqlite")
        except Exception:  # noqa
            pass
    try:
        con.execute(f"ATTACH '{path}' AS {name} (TYPE sqlite, READ_ONLY)")
        return
    except Exception:  # noqa
        pass
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {name}")
    src = sqlite3.connect(path)
    import pandas as pd
    for (t,) in src.execute("select name from sqlite_master where type in ('table','view')"):
        if t in SKIP_TABLES:
            continue
        try:
            df = pd.read_sql_query(f'select * from "{t}"', src)
            df = df.drop(columns=[c for c in ("raw_json",) if c in df.columns])
            con.register(f"_tmp_{name}_{t}", df)
            con.execute(f'CREATE TABLE {name}."{t}" AS SELECT * FROM _tmp_{name}_{t}')
            con.unregister(f"_tmp_{name}_{t}")
        except Exception as e:  # noqa
            print(f"warehouse: skip {name}.{t}: {e}", file=sys.stderr)


def _has(con, schema, table):
    return con.execute("select count(*) from information_schema.tables where table_schema=? and table_name=?",
                       [schema, table]).fetchone()[0] > 0


def _cols(con, schema, table):
    return {r[0] for r in con.execute("select column_name from information_schema.columns where table_schema=? and table_name=?",
                                      [schema, table]).fetchall()}


def connect():
    con = duckdb.connect()
    con.execute("SET TimeZone='UTC'")
    products = []
    for name, path in DBS.items():
        if path.exists():
            _attach_sqlite(con, name, path)
            products.append(name)
    for s in ("hist", "live", "er"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")
    # history zone: one view per file
    for f in _files("data/lake/history/*.csv"):
        con.execute(f"CREATE VIEW hist.\"{pathlib.Path(f).stem}\" AS SELECT * FROM {_csv(pathlib.Path(f).relative_to(ROOT))}")
    # live zone: one view per feed folder (all days, all column versions)
    for d in sorted(p for p in (ROOT / "data" / "live").glob("*") if p.is_dir() and not p.name.startswith("_")):
        if list(d.glob("*.csv")):
            con.execute(f"CREATE VIEW live.\"{d.name}\" AS SELECT * FROM {_csv(f'data/live/{d.name}/*.csv')}")
    for prod in ("diesel", "gas"):
        base = "data/archive" if prod == "diesel" else f"data/{prod}/archive"
        for kind in ("trades", "candles_1min"):
            if _files(f"{base}/{kind}/*.csv.gz"):
                con.execute(f"CREATE VIEW live.\"archive_{prod}_{kind}\" AS SELECT * FROM {_csv(f'{base}/{kind}/*.csv.gz')}")
    if (ROOT / "data" / "live" / "aaa_flips.csv").exists():
        con.execute(f"CREATE VIEW live.aaa_flips AS SELECT * FROM {_csv('data/live/aaa_flips.csv')}")
    if _files("research/engine_room/wayback_states/*.csv"):
        con.execute(f"CREATE VIEW er.wayback_states AS SELECT * FROM {_csv('research/engine_room/wayback_states/*.csv')}")
    if _files("research/engine_room/aaa_states_gas/*.csv"):
        con.execute(f"CREATE VIEW er.aaa_states_gas AS SELECT * FROM {_csv('research/engine_room/aaa_states_gas/*.csv')}")
    _unified(con, products)
    _live_extras(con)
    return con


def _union(con, name, parts, empty_cols):
    parts = [p for p in parts if p]
    if not parts:
        con.execute(f"CREATE VIEW {name} AS SELECT " + ", ".join(f"NULL::{t} AS {c}" for c, t in empty_cols) + " WHERE false")
    else:
        con.execute(f"CREATE VIEW {name} AS " + "\nUNION ALL BY NAME\n".join(f"SELECT * FROM ({p})" for p in parts))


def _unified(con, products):
    mmddyy = "strptime({c}, '%m/%d/%y')::DATE"
    # ---- AAA national, one row per date x product x source --------------------------------------------
    parts = []
    for p in products:
        if _has(con, p, "diesel_daily"):
            parts.append(f"""SELECT date::DATE AS date, '{p}' AS product, aaa_diesel::DOUBLE AS value, aaa_source AS source,
                             (date::DATE + INTERVAL 7 HOUR)::TIMESTAMP AS ts_utc FROM {p}.diesel_daily WHERE aaa_diesel IS NOT NULL""")
    if _has(con, "live", "aaa_national"):
        for p, col in (("diesel", "diesel_current"), ("gas", "regular_gas_current")):
            parts.append(f"""SELECT {mmddyy.format(c='price_as_of')} AS date, '{p}' AS product, max(TRY_CAST({col} AS DOUBLE)) AS value,
                             'live_recorder' AS source, min(ts_utc::TIMESTAMP) AS ts_utc FROM live.aaa_national
                             WHERE price_as_of IS NOT NULL AND TRY_CAST({col} AS DOUBLE) IS NOT NULL GROUP BY 1""")
    if _has(con, "hist", "aaa_national_wayback"):
        for p, col in (("diesel", "diesel"), ("gas", "regular")):
            parts.append(f"""SELECT TRY_CAST({mmddyy.format(c='price_as_of')} AS DATE) AS date, '{p}' AS product,
                             max(TRY_CAST({col} AS DOUBLE)) AS value, 'wayback_national' AS source,
                             min(strptime(snapshot_ts, '%Y%m%d%H%M%S')) AS ts_utc
                             FROM hist.aaa_national_wayback WHERE "row" = 'Current' AND price_as_of IS NOT NULL GROUP BY 1""")
    _union(con, "aaa_daily_all", parts, [("date", "DATE"), ("product", "VARCHAR"), ("value", "DOUBLE"), ("source", "VARCHAR"), ("ts_utc", "TIMESTAMP")])
    con.execute(f"""CREATE VIEW aaa_daily AS
        SELECT date, product, arg_min(value, CASE WHEN source LIKE 'kalshi%' THEN 0 WHEN source='live_recorder' THEN 1 ELSE 2 END) AS value,
               string_agg(DISTINCT source, '+') AS sources, count(DISTINCT round(value, 4)) AS n_distinct_values,
               min(ts_utc) AS ts_utc, {ERA.replace('ts_utc', 'min(ts_utc)')} AS era
        FROM aaa_daily_all WHERE date IS NOT NULL AND value IS NOT NULL GROUP BY date, product""")
    # ---- AAA state prices (daily recorder + Wayback state pages + gas state files) ------------------------
    parts = []
    if _has(con, "diesel", "aaa_state_daily"):
        parts.append(f"""SELECT {mmddyy.format(c='as_of')} AS date, state, 'diesel' AS product, diesel_current::DOUBLE AS value,
                         'daily_recorder' AS source FROM diesel.aaa_state_daily""")
    if _has(con, "er", "wayback_states"):
        parts.append(f"""SELECT TRY_CAST({mmddyy.format(c='as_of')} AS DATE) AS date, state,
                         CASE WHEN grade='diesel' THEN 'diesel' ELSE 'gas' END AS product, TRY_CAST(current AS DOUBLE) AS value,
                         'wayback_state' AS source FROM er.wayback_states""")
    if _has(con, "er", "aaa_states_gas"):
        c = _cols(con, "er", "aaa_states_gas")
        if {"as_of", "state"} <= c:
            vcol = next((x for x in ("regular_current", "current", "regular") if x in c), None)
            if vcol:
                parts.append(f"""SELECT TRY_CAST({mmddyy.format(c='as_of')} AS DATE) AS date, state, 'gas' AS product,
                                 TRY_CAST({vcol} AS DOUBLE) AS value, 'daily_recorder' AS source FROM er.aaa_states_gas""")
    _union(con, "state_prices_all", parts, [("date", "DATE"), ("state", "VARCHAR"), ("product", "VARCHAR"), ("value", "DOUBLE"), ("source", "VARCHAR")])
    con.execute("""CREATE VIEW state_prices AS SELECT date, state, product, max(value) AS value, string_agg(DISTINCT source, '+') AS sources
                   FROM state_prices_all WHERE date IS NOT NULL AND value IS NOT NULL GROUP BY ALL""")
    # ---- Kalshi ladder: hourly + 1-min candles (history) and 5-min live snapshots --------------------------
    parts = []
    for p in products:
        if _has(con, p, "kalshi_candles"):
            parts.append(f"""SELECT to_timestamp(end_ts::BIGINT)::TIMESTAMP AS ts_utc, '{p}' AS product, event_date::DATE AS event_date,
                             strike::DOUBLE AS strike, yes_bid::DOUBLE AS yes_bid, yes_ask::DOUBLE AS yes_ask, mid::DOUBLE AS mid,
                             volume::DOUBLE AS volume, open_interest::DOUBLE AS open_interest,
                             'candle_' || period_min || 'm' AS source FROM {p}.kalshi_candles""")
    for p in products:
        if _has(con, "live", f"archive_{p}_candles_1min"):
            parts.append(f"""SELECT to_timestamp(end_ts::BIGINT)::TIMESTAMP AS ts_utc, '{p}' AS product, event_date::DATE AS event_date,
                             strike::DOUBLE AS strike, yes_bid::DOUBLE AS yes_bid, yes_ask::DOUBLE AS yes_ask, mid::DOUBLE AS mid,
                             TRY_CAST(volume AS DOUBLE) AS volume, TRY_CAST(open_interest AS DOUBLE) AS open_interest,
                             'candle_1m' AS source FROM live.archive_{p}_candles_1min""")
    if _has(con, "live", "kalshi_markets"):
        parts.append("""SELECT ts_utc::TIMESTAMP AS ts_utc, CASE WHEN series='KXAAAGASD' THEN 'gas' ELSE 'diesel' END AS product,
                        strptime(regexp_extract(event, '-(\\d{2}[A-Z]{3}\\d{2})$', 1), '%y%b%d')::DATE AS event_date,
                        strike::DOUBLE AS strike, yes_bid::DOUBLE AS yes_bid, yes_ask::DOUBLE AS yes_ask,
                        (yes_bid::DOUBLE + yes_ask::DOUBLE)/2 AS mid, TRY_CAST(volume AS DOUBLE) AS volume,
                        TRY_CAST(open_interest AS DOUBLE) AS open_interest, 'live_5m' AS source FROM live.kalshi_markets""")
    _union(con, "ladder_all", parts, [("ts_utc", "TIMESTAMP"), ("product", "VARCHAR"), ("strike", "DOUBLE"), ("source", "VARCHAR")])
    con.execute(f"CREATE VIEW ladder AS SELECT *, {ERA} AS era FROM ladder_all")
    # ---- Kalshi trades ---------------------------------------------------------------------------------
    parts = [f"""SELECT trade_id, created_time::TIMESTAMP AS ts_utc, '{p}' AS product, ticker, event_date::DATE AS event_date, strike::DOUBLE AS strike,
                 yes_price::DOUBLE AS yes_price, "count"::DOUBLE AS contracts, taker_side FROM {p}.kalshi_trades"""
             for p in products if _has(con, p, "kalshi_trades")]
    parts += [f"""SELECT trade_id, created_time::TIMESTAMP AS ts_utc, '{p}' AS product, ticker, event_date::DATE AS event_date,
                  strike::DOUBLE AS strike, yes_price::DOUBLE AS yes_price, "count"::DOUBLE AS contracts, taker_side
                  FROM live.archive_{p}_trades""" for p in products if _has(con, "live", f"archive_{p}_trades")]
    _union(con, "trades_all", parts, [("ts_utc", "TIMESTAMP"), ("product", "VARCHAR"), ("ticker", "VARCHAR")])
    con.execute(f"CREATE VIEW trades AS SELECT * EXCLUDE (trade_id), {ERA} AS era FROM trades_all QUALIFY row_number() OVER (PARTITION BY trade_id) = 1")
    # ---- Futures: daily closes, EIA settlements, Yahoo intraday, live TradingView ------------------------
    parts = []
    if _has(con, "diesel", "diesel_daily"):
        parts.append("""SELECT (date::DATE + INTERVAL 19 HOUR)::TIMESTAMP AS ts_utc, 'HO' AS symbol, ulsd_nyh_usd_gal::DOUBLE AS price,
                        '1d' AS bar, ulsd_source AS source FROM diesel.diesel_daily WHERE ulsd_nyh_usd_gal IS NOT NULL""")
        parts.append("""SELECT (date::DATE + INTERVAL 19 HOUR)::TIMESTAMP AS ts_utc, 'BRENT' AS symbol, brent_usd_bbl::DOUBLE AS price,
                        '1d' AS bar, brent_source AS source FROM diesel.diesel_daily WHERE brent_usd_bbl IS NOT NULL""")
    for name, sym in (("eia_ho_futures_m1", "HO"), ("eia_rbob_futures_m1", "RBOB")):
        if _has(con, "hist", name):
            parts.append(f"""SELECT (date::DATE + INTERVAL 19 HOUR)::TIMESTAMP AS ts_utc, '{sym}' AS symbol, value::DOUBLE AS price,
                             '1d' AS bar, 'eia_settle' AS source FROM hist.{name}""")
    ymap = {"HO": "HO", "BZ": "BRENT", "RB": "RBOB", "CL": "WTI", "NG": "NATGAS"}
    for f in _files("data/lake/history/yahoo_*.csv"):
        stem = pathlib.Path(f).stem                     # yahoo_HO_60m_2026-11
        _, s, bar = stem.split("_")[:3]
        parts.append(f"""SELECT ts_utc::TIMESTAMP AS ts_utc, '{ymap.get(s, s)}' AS symbol, close::DOUBLE AS price, '{bar}' AS bar,
                         'yahoo' AS source FROM hist."{stem}" WHERE close IS NOT NULL AND close <> ''""")
    for f in _files("data/lake/history/fut_*_1d.csv"):        # Yahoo daily, full history (history_pull.py daily)
        stem = pathlib.Path(f).stem                             # fut_rbob_1d
        sym = {"ho": "HO", "rbob": "RBOB", "brent": "BRENT", "wti": "WTI", "natgas": "NATGAS"}.get(stem.split("_")[1], stem)
        parts.append(f"""SELECT (date::DATE + INTERVAL 19 HOUR)::TIMESTAMP AS ts_utc, '{sym}' AS symbol, close::DOUBLE AS price,
                         '1d' AS bar, 'yahoo_daily' AS source FROM hist."{stem}" WHERE close IS NOT NULL""")
    if _has(con, "live", "futures"):
        parts.append("""SELECT ts_utc::TIMESTAMP AS ts_utc, name AS symbol, TRY_CAST("last" AS DOUBLE) AS price, 'live_5m' AS bar,
                        coalesce(source, 'stooq') AS source FROM live.futures""")
    _union(con, "futures_all", parts, [("ts_utc", "TIMESTAMP"), ("symbol", "VARCHAR"), ("price", "DOUBLE"), ("bar", "VARCHAR"), ("source", "VARCHAR")])
    con.execute(f"CREATE VIEW futures_bars AS SELECT *, {ERA} AS era FROM futures_all WHERE price IS NOT NULL")
    # ---- EIA spot (daily) + weekly retail / inventories ----------------------------------------------------
    sp = [f"SELECT date::DATE AS date, '{pathlib.Path(f).stem[4:]}' AS series, value::DOUBLE AS value FROM hist.\"{pathlib.Path(f).stem}\""
          for f in _files("data/lake/history/eia_*.csv")]
    _union(con, "eia_all", sp, [("date", "DATE"), ("series", "VARCHAR"), ("value", "DOUBLE")])
    con.execute("CREATE VIEW spot_daily AS SELECT * FROM eia_all WHERE series LIKE '%spot%' OR series LIKE '%futures%'")
    con.execute("CREATE VIEW eia_weekly AS SELECT * FROM eia_all WHERE series LIKE 'retail_%' OR series LIKE '%stocks%' OR series LIKE 'weekly_%' OR series LIKE 'monthly_%'")
    # ---- pass-through live feeds with era ---------------------------------------------------------------
    for v, src in (("orderbook", "kalshi_orderbook"), ("truckstops", "truckstops")):
        if _has(con, "live", src):
            con.execute(f"CREATE VIEW {v} AS SELECT * EXCLUDE (filename), ts_utc::TIMESTAMP AS ts, {ERA.replace('ts_utc', 'ts_utc::TIMESTAMP')} AS era FROM live.{src}")
        else:
            con.execute(f"CREATE VIEW {v} AS SELECT NULL::TIMESTAMP AS ts, NULL AS era WHERE false")


def _live_extras(con):
    """Live feeds from both chats, shaped for algos: truckstop diesel (L3), AAA flips, HO at bet time, feed health."""
    if _has(con, "live", "truckstops"):
        con.execute(f"""CREATE VIEW truckstop_diesel AS
            SELECT ts_utc::TIMESTAMP AS ts_utc, (ts_utc::TIMESTAMP AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')::DATE AS date_et,
                   chain, store, state, city, TRY_CAST(price AS DOUBLE) AS price,
                   CASE WHEN lower(product) LIKE '%bio%' OR lower(product) LIKE '%b20%' THEN 'biodiesel'
                        WHEN lower(product) LIKE '%auto diesel%' THEN 'auto_diesel' ELSE 'diesel' END AS grade,
                   product, {ERA.replace('ts_utc', 'ts_utc::TIMESTAMP')} AS era
            FROM live.truckstops
            WHERE lower(product) LIKE '%diesel%' AND TRY_CAST(price AS DOUBLE) BETWEEN 2 AND 12""")
        # one number per state per pull (median of truck-lane diesel), the L3 input that lines up with AAA states
        con.execute("""CREATE VIEW truckstop_state AS
            SELECT ts_utc, date_et, state, chain, grade, median(price) AS diesel_median, count(*) AS stores, era
            FROM truckstop_diesel WHERE grade <> 'biodiesel' GROUP BY ALL""")
        con.execute("""CREATE VIEW l3_state_compare AS
            WITH last_pull AS (SELECT date_et, state, chain, grade, arg_max(diesel_median, ts_utc) AS truckstop_diesel,
                                      arg_max(stores, ts_utc) AS stores FROM truckstop_state GROUP BY ALL)
            SELECT l.date_et AS date, l.state, l.chain, l.grade, l.truckstop_diesel, l.stores, s.value AS aaa_state_diesel,
                   round((l.truckstop_diesel - s.value) * 100, 2) AS gap_cents
            FROM last_pull l LEFT JOIN state_prices s ON s.date = l.date_et AND s.state = l.state AND s.product = 'diesel'""")
    if _has(con, "live", "aaa_flips"):
        con.execute("""CREATE VIEW aaa_flips AS SELECT first_seen_utc::TIMESTAMP AS ts_utc, first_seen_et, price_as_of,
                       TRY_CAST(diesel_new AS DOUBLE) AS diesel_new, TRY_CAST(diesel_before AS DOUBLE) AS diesel_before
                       FROM live.aaa_flips""")
    # HO at the 10 AM bet time, no peeking: last live quote stamped at/before 10:10 ET (quotes run ~10 min late)
    con.execute("""CREATE VIEW ho_at_10am AS
        SELECT (ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')::DATE AS date_et,
               arg_max(price, ts_utc) AS ho_price, max(ts_utc) AS quote_ts_utc
        FROM futures_bars WHERE symbol = 'HO' AND bar = 'live_5m'
          AND strftime(ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York', '%H:%M') <= '10:10'
        GROUP BY 1""")
    # feed health: is every recorder still on point?
    checks = [
        ("Kalshi strikes, 5-min (live recorder)", "SELECT max(ts_utc) FROM ladder WHERE source='live_5m'", 15),
        ("Kalshi order book, 15-min (live recorder)", "SELECT max(ts) FROM orderbook", 30),
        ("AAA national, 15-min (live recorder)", "SELECT max(ts_utc::TIMESTAMP) FROM live.aaa_national" if _has(con, "live", "aaa_national") else None, 30),
        ("Futures quotes, 5-min (live recorder)", "SELECT max(ts_utc) FROM futures_bars WHERE bar='live_5m'", 15),
        ("Love's truckstops, hourly (Chat 4)", "SELECT max(ts_utc) FROM truckstop_diesel WHERE chain='loves'" if _has(con, "live", "truckstops") else None, 90),
        ("TA truckstops, hourly (Chat 4)", "SELECT max(ts_utc) FROM truckstop_diesel WHERE chain='ta'" if _has(con, "live", "truckstops") else None, 90),
        ("Kalshi trades + 1-min candles (daily job)", "SELECT max(ts_utc) FROM trades", 36 * 60),
        ("Kalshi hourly candles + settlements (daily job)", "SELECT max(ts_utc) FROM ladder WHERE source='candle_60m'", 36 * 60),
        ("AAA state prices (daily job)", "SELECT max(date)::TIMESTAMP + INTERVAL 12 HOUR FROM state_prices WHERE sources LIKE '%daily_recorder%'", 36 * 60),
        ("EIA spot prices (warehouse job)", "SELECT max(date)::TIMESTAMP + INTERVAL 20 HOUR FROM spot_daily", 4 * 24 * 60),
    ]
    parts = []
    for name, q, limit in checks:
        if q:
            parts.append(f"SELECT '{name.replace(chr(39), chr(39) * 2)}' AS feed, ({q}) AS last_row_utc, {limit} AS expect_every_min")
    con.execute("CREATE VIEW feed_health AS SELECT feed, last_row_utc, expect_every_min, "
                "round(date_diff('second', last_row_utc, now()::TIMESTAMP) / 60.0) AS minutes_since, "
                "CASE WHEN last_row_utc IS NULL THEN 'NO DATA' "
                "WHEN date_diff('second', last_row_utc, now()::TIMESTAMP) / 60.0 <= expect_every_min * 2 + 75 THEN 'OK' ELSE 'STALE' END AS status "
                "FROM (" + " UNION ALL ".join(parts) + ")")


CATALOG = [  # view, time column, group-by for one line per source, what it is (plain words)
    ("aaa_daily", "date", "product", "AAA national price per day (Kalshi settlements, live recorder, Internet Archive)"),
    ("state_prices", "date", "product", "AAA price per state per day (daily recorder + Internet Archive state pages)"),
    ("ladder", "ts_utc", "product, source", "Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live)"),
    ("trades", "ts_utc", "product", "Every Kalshi trade"),
    ("futures_bars", "ts_utc", "symbol, bar", "Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live)"),
    ("spot_daily", "date", "series", "EIA daily spot prices + NYMEX front-month settlements"),
    ("eia_weekly", "date", "series", "EIA weekly retail diesel/gas by region + diesel inventories"),
    ("orderbook", "ts", None, "Kalshi order book depth (live only, no history exists)"),
    ("truckstop_diesel", "ts_utc", "chain", "Truckstop posted diesel prices, Love's + TA (live only, Chat 4)"),
    ("aaa_flips", "ts_utc", None, "Moments AAA's national number changed (live recorder)"),
    ("ho_at_10am", "date_et", None, "Diesel futures price at the 10 AM bet time, no peeking (live recorder)"),
]


GAS_WORDS = ("gas", "gasoline", "rbob", "regular")
SHARED_WORDS = ("brent", "wti", "natgas")


def _role(view, key):
    """Diesel = the main system. Gas = side test / analog (same AAA engine, used to check ideas and inputs).
    Oil + nat gas feed both."""
    k = key.lower()
    if any(w in k for w in SHARED_WORDS):
        return "🔗 Shared input"
    if any(w in k for w in GAS_WORDS) and "diesel" not in k:
        return "⛽ Side test (gas analog)"
    return "🎯 Main (diesel)"


def catalog(con):
    rows = []
    for view, tcol, grp, what in CATALOG:
        if not con.execute("select count(*) from information_schema.tables where table_name=?", [view]).fetchone()[0]:
            continue                                   # feed not recorded yet (e.g. no AAA flip seen so far)
        g = f"{grp}," if grp else ""
        era = ", sum(CASE WHEN era='since_live' THEN 1 ELSE 0 END)" if "era" in [c[0] for c in con.execute(f"DESCRIBE {view}").fetchall()] else ", NULL"
        q = f"SELECT {g} count(*), min({tcol})::VARCHAR, max({tcol})::VARCHAR {era} FROM {view} {'GROUP BY ' + grp if grp else ''} ORDER BY 1"
        try:
            for r in con.execute(q).fetchall():
                r = list(r)
                key = " · ".join(str(x) for x in r[:len(grp.split(','))]) if grp else ""
                n, first, last, live = r[-4:]
                if n:
                    rows.append([_role(view, key), view, key, what, n, (first or "")[:16], (last or "")[:16],
                                 live if live is not None else ""])
        except Exception as e:  # noqa
            rows.append([_role(view, ""), view, "", what, 0, "", "", f"error: {str(e)[:80]}"])
    order = {"🎯 Main (diesel)": 0, "🔗 Shared input": 1, "⛽ Side test (gas analog)": 2}
    rows.sort(key=lambda r: order.get(r[0], 9))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = ["role", "dataset", "slice", "what it is", "rows", "first", "last", "rows since go-live"]
    with (ROOT / "data" / "warehouse_catalog.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    md = [f"# Warehouse catalog ({stamp})", "", f"Go-live (start of 'since inception'): {GO_LIVE} UTC", "",
          "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    fh = con.execute("SELECT feed, strftime(last_row_utc, '%Y-%m-%d %H:%M') AS last_row_utc, expect_every_min, minutes_since, status FROM feed_health").fetchall()
    with (ROOT / "data" / "feed_health.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["feed", "last row (UTC)", "expected every (min)", "minutes since", "status"])
        w.writerows(fh)
    md += ["", f"## Feed health ({stamp})", "", "| feed | last row (UTC) | expected every (min) | minutes since | status |", "|---|---|---|---|---|"]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in fh]
    (ROOT / "data" / "warehouse_catalog.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return rows


if __name__ == "__main__":
    a = sys.argv[1:] or ["catalog"]
    con = connect()
    if a[0] == "catalog":
        catalog(con)
    elif a[0] == "sql":
        print(con.sql(a[1]))
    elif a[0] == "export":
        view, out = a[1], a[2]
        fmt = "PARQUET" if out.endswith(".parquet") else "CSV, HEADER"
        con.execute(f"COPY (SELECT * FROM {view}) TO '{out}' (FORMAT {fmt})")
        print(f"wrote {out}")
