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
    if (ROOT / "data" / "live" / "aaa_flips.csv").exists():
        con.execute(f"CREATE VIEW live.aaa_flips AS SELECT * FROM {_csv('data/live/aaa_flips.csv')}")
    if _files("research/engine_room/wayback_states/*.csv"):
        con.execute(f"CREATE VIEW er.wayback_states AS SELECT * FROM {_csv('research/engine_room/wayback_states/*.csv')}")
    if _files("research/engine_room/aaa_states_gas/*.csv"):
        con.execute(f"CREATE VIEW er.aaa_states_gas AS SELECT * FROM {_csv('research/engine_room/aaa_states_gas/*.csv')}")
    _unified(con, products)
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
    if _has(con, "live", "kalshi_markets"):
        parts.append("""SELECT ts_utc::TIMESTAMP AS ts_utc, CASE WHEN series='KXAAAGASD' THEN 'gas' ELSE 'diesel' END AS product,
                        strptime(regexp_extract(event, '-(\\d{2}[A-Z]{3}\\d{2})$', 1), '%y%b%d')::DATE AS event_date,
                        strike::DOUBLE AS strike, yes_bid::DOUBLE AS yes_bid, yes_ask::DOUBLE AS yes_ask,
                        (yes_bid::DOUBLE + yes_ask::DOUBLE)/2 AS mid, TRY_CAST(volume AS DOUBLE) AS volume,
                        TRY_CAST(open_interest AS DOUBLE) AS open_interest, 'live_5m' AS source FROM live.kalshi_markets""")
    _union(con, "ladder_all", parts, [("ts_utc", "TIMESTAMP"), ("product", "VARCHAR"), ("strike", "DOUBLE"), ("source", "VARCHAR")])
    con.execute(f"CREATE VIEW ladder AS SELECT *, {ERA} AS era FROM ladder_all")
    # ---- Kalshi trades ---------------------------------------------------------------------------------
    parts = [f"""SELECT created_time::TIMESTAMP AS ts_utc, '{p}' AS product, ticker, event_date::DATE AS event_date, strike::DOUBLE AS strike,
                 yes_price::DOUBLE AS yes_price, "count"::DOUBLE AS contracts, taker_side FROM {p}.kalshi_trades"""
             for p in products if _has(con, p, "kalshi_trades")]
    _union(con, "trades_all", parts, [("ts_utc", "TIMESTAMP"), ("product", "VARCHAR"), ("ticker", "VARCHAR")])
    con.execute(f"CREATE VIEW trades AS SELECT *, {ERA} AS era FROM trades_all")
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
    con.execute("CREATE VIEW eia_weekly AS SELECT * FROM eia_all WHERE series LIKE 'retail_%' OR series LIKE '%stocks%'")
    # ---- pass-through live feeds with era ---------------------------------------------------------------
    for v, src in (("orderbook", "kalshi_orderbook"), ("truckstops", "truckstops")):
        if _has(con, "live", src):
            con.execute(f"CREATE VIEW {v} AS SELECT * EXCLUDE (filename), ts_utc::TIMESTAMP AS ts, {ERA.replace('ts_utc', 'ts_utc::TIMESTAMP')} AS era FROM live.{src}")
        else:
            con.execute(f"CREATE VIEW {v} AS SELECT NULL::TIMESTAMP AS ts, NULL AS era WHERE false")


CATALOG = [  # view, time column, group-by for one line per source, what it is (plain words)
    ("aaa_daily", "date", "product", "AAA national price per day (Kalshi settlements, live recorder, Internet Archive)"),
    ("state_prices", "date", "product", "AAA price per state per day (daily recorder + Internet Archive state pages)"),
    ("ladder", "ts_utc", "product, source", "Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live)"),
    ("trades", "ts_utc", "product", "Every Kalshi trade"),
    ("futures_bars", "ts_utc", "symbol, bar", "Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live)"),
    ("spot_daily", "date", "series", "EIA daily spot prices + NYMEX front-month settlements"),
    ("eia_weekly", "date", "series", "EIA weekly retail diesel/gas by region + diesel inventories"),
    ("orderbook", "ts", None, "Kalshi order book depth (live only, no history exists)"),
    ("truckstops", "ts", None, "Love's truckstop posted diesel prices (live only)"),
]


def catalog(con):
    rows = []
    for view, tcol, grp, what in CATALOG:
        g = f"{grp}," if grp else ""
        era = ", sum(CASE WHEN era='since_live' THEN 1 ELSE 0 END)" if "era" in [c[0] for c in con.execute(f"DESCRIBE {view}").fetchall()] else ", NULL"
        q = f"SELECT {g} count(*), min({tcol})::VARCHAR, max({tcol})::VARCHAR {era} FROM {view} {'GROUP BY ' + grp if grp else ''} ORDER BY 1"
        try:
            for r in con.execute(q).fetchall():
                r = list(r)
                key = " · ".join(str(x) for x in r[:len(grp.split(','))]) if grp else ""
                n, first, last, live = r[-4:]
                if n:
                    rows.append([view, key, what, n, (first or "")[:16], (last or "")[:16], live if live is not None else ""])
        except Exception as e:  # noqa
            rows.append([view, "", what, 0, "", "", f"error: {str(e)[:80]}"])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = ["dataset", "slice", "what it is", "rows", "first", "last", "rows since go-live"]
    with (ROOT / "data" / "warehouse_catalog.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    md = [f"# Warehouse catalog ({stamp})", "", f"Go-live (start of 'since inception'): {GO_LIVE} UTC", "",
          "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
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
