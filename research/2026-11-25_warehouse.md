# Warehouse (DuckDB) — 2026-11-25

**What:** one place to query every dataset, both products (diesel + gas), history + live. `tools/warehouse.py`.
Nothing gets copied or migrated. DuckDB reads each source where it lives: SQLite DBs (`diesel.*`, `gas.*`),
`data/lake/history/*.csv` (`hist.*`), `data/live/<feed>/*.csv` (`live.*`), and Engine Room files (`er.*`).

**Unified views (read these, not raw tables):** `aaa_daily` · `state_prices` · `ladder` · `trades` · `futures_bars` ·
`spot_daily` · `eia_weekly` · `orderbook` · `truckstops`. Each time-stamped view has `era` = `history` / `since_live`
(go-live = first live snapshot, 2026-11-25 19:21 UTC). "Backtest since inception" = the same query `WHERE era='since_live'`.

**Use:** `python3 tools/warehouse.py catalog` (writes `data/warehouse_catalog.csv/.md`, which the sheet's Warehouse tab imports) ·
`python3 tools/warehouse.py sql "select ..."` · in Python `from warehouse import connect`.
If DuckDB's sqlite extension can't download (e.g. in Claude's sandbox), the SQLite tables are copied into memory instead (same result).

**History zone (`tools/history_pull.py`, workflow `warehouse.yml`, started daily by the relay):**
- EIA works from GitHub: 17 series. Daily spot NYH/Gulf/LA-CARB ULSD (2006+/1996+), NYH/Gulf gasoline, Brent/WTI spot (1986+), NYMEX HO/RBOB front-month settles (1980–2024-04, EIA stopped publishing them), weekly retail diesel US + 5 PADDs (1994+), regular gas (1990+), distillate stocks (1982+).
- Yahoo intraday (60m/5m/1m) is **blocked from GitHub** (all requests fail). The script keeps trying daily, and files are monthly so they can't outgrow GitHub's limits. Going-forward intraday futures come from the live recorder (TradingView, ~10 min delay).
- Internet Archive: daily snapshots of AAA's **national** page since 2019 → `aaa_national_wayback.csv` (today / yesterday / week / month / year ago for regular, mid, premium, diesel). Resumable, newest first. State pages are done by Chat 4's `wayback_states.py`.

**First findings:**
- AAA Monday diesel vs EIA weekly US diesel: within 0–4¢ through Oct, then +4.5¢ (11/09), +6.2¢ (11/16), **+12.3¢ (11/23)** → the two surveys diverge as prices fall (AAA slower to drop?). Candidate L1/L3 input.
- Gas: 269 AAA days since 2023-09 already in the warehouse via the gas DB.

**Wishlist** (things to add later, simple list) lives in the sheet tab **Wishlist**.
