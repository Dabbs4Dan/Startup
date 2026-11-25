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

## Live feeds from both chats: where each fits (audit 2026-11-25, 4:20 PM ET)

| Feed | Built by | Layer it feeds | Warehouse view | Verdict |
|---|---|---|---|---|
| Kalshi strikes every 5 min (diesel + gas, all 21 lines, top-of-book size) | live recorder | L0 market maker | `ladder` (source `live_5m`) | Keep. Overlaps the daily 1-min candles, but those cover only the 3 busiest lines and arrive a day late |
| Kalshi order book every 15 min | live recorder | L0 (spread/inventory, slippage) | `orderbook` | Keep. No history exists anywhere else |
| AAA national every 15 min + flip log | live recorder | L1 + timing | `aaa_daily`, `aaa_flips` | Keep. Settlement gives the number; only this gives the minute it changes |
| Futures every 5 min (TradingView, ~10 min delay) | live recorder | L3 wholesale + L0 move explainer | `futures_bars` (`live_5m`), `ho_at_10am` | Keep. **Replaces** the daily HO-at-10-AM recorder in `daily_recorders.py`, which never produced data (Yahoo 429, Stooq timeout) |
| Love's + TA truckstop prices, hourly | Chat 4 | L3 station prices → L2 states | `truckstop_diesel`, `truckstop_state`, `l3_state_compare` | Keep. The key L3 input. TA posts only "Auto Diesel"; Love's posts truck-lane "Diesel" + "Auto Diesel" (grades kept separate) |
| AAA 51 states daily | Chat 1/4 (`daily_recorders.py` diesel; `engine_room.py` gas) | L2 | `state_prices` | ⚠️ The same 51 pages are scraped twice (once per grade). Harmless, merge later |
| Internet Archive: AAA state pages / national page | Chat 4 / this chat | L2 / L1 history | `state_prices` / `aaa_daily` | Complementary. Both hit the Internet Archive and share its rate limit |
| Daily backfill: settlements, hourly + 1-min candles, trades | daily jobs | L0/L1 history | `ladder`, `trades`, `aaa_daily` | Keep (backfillable source of truth) |

**Fixes made in this audit:** the truckstop loop only restarts at each recorder shift change, so a ~5 h gap was coming → started it by hand now (the relay restarts it each shift after this). `feed_health` view + sheet block flag any feed that goes quiet (STALE = more than 2× its expected gap).
**First L3 read (1 pull, Nov 25):** Love's truck-lane diesel sits a median **−7¢** under AAA state averages (10–90% range −31 to +20¢), and TA "Auto Diesel" **+3¢**. As expected, levels don't match, so L3 tests must use day-to-day CHANGES.
