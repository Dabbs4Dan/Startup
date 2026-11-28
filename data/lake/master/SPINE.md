# The spine: how every research table connects

Built by `tools/spine.py` on 2026-11-28 08:59 UTC. Re-run after any table is rebuilt. Read this before adding a table.

**Master version: `m20261128-0345b9a1`** (built 2026-11-28 06:16 UTC; `data/lake/master/VERSION.json`). Every result names the version it read.

**One set of keys:** market → event → time slot (`snapshot_et`) → line (`strike`). Days join to inputs by `asof_date`.

**Layers:** L0 inputs → L1 master → L2 slices (4 outcome boxes) → L3 our ratios + scan → L4 market-maker copy → takeaways (`research/takeaways/master.csv`).

**Two engines (every test says which one it is):**
- **E1 settle engine:** hold to the end. Did the line settle Yes or No vs the price paid.
- **E2 intraday engine:** trade the price path between time slots and exit before the end.

## Tables

| Table | Layer | Engine | One row is | Rows | Events | From | To | Duplicate keys | Built by | File |
|---|---|---|---|---|---|---|---|---|---|---|
| **inputs_daily** | L0 inputs | both | date | 2890 |  | 2019-01-01 | 2026-11-29 | 0 | `tools/backtest_master.py` | `data/lake/master/inputs_daily.csv` |
| **aaa_daily** | L0 inputs | both | date x fuel | 1558 |  | 2022-11-28 | 2026-11-27 | 0 | `tools/backtest_master.py` | `data/lake/master/aaa_daily.csv` |
| **backtest_master** | L1 master | both | event x snapshot x snapshot_et | 12790 | 581 | 2023-09-18 | 2026-11-27 | 0 | `tools/backtest_master.py` | `data/lake/master/backtest_master.csv.gz` |
| **ladder_snapshots** | L1 master | E2 (and shape layer) | event x snapshot x snapshot_et x floor_strike | 146477 | 581 |  |  | 0 | `tools/backtest_master.py` | `data/lake/master/ladder_snapshots.csv.gz` |
| **slices** | L2 slices + L3 ratios | E1 | event x snapshot x snapshot_et x line_rank | 23631 | 542 | 2023-09-25 | 2026-11-27 | 0 | `tools/slice_scan.py` | `data/lake/master/slices.csv.gz` |
| **favorite_ledger** | L2 roll-up | E1 | market x favorite x price_band | 84 |  |  |  | 0 | `tools/slice_scan.py` | `research/engine_room/favorite_ledger.csv` |
| **favorite_ledger_by_time_and_line** | L2 roll-up | E1 | market x favorite x cut x value | 137 |  |  |  | 0 | `tools/slice_scan.py` | `research/engine_room/favorite_ledger_by_time_and_line.csv` |
| **market_scorecard** | L2 roll-up | E1 | market | 6 |  |  |  | 0 | `tools/market_scorecard.py` | `research/engine_room/market_scorecard.csv` |
| **bet_grid** | L3 scan | E1 | market x side x price_cut x slot x line | 10748 |  |  |  | 0 | `tools/bet_grid.py` | `research/engine_room/bet_grid.csv` |
| **swing_cohort** | L2 for E2 (first piece of paths) | E2 | event x floor_strike x snapshot_et | 2237 | 374 |  |  | 0 | `tools/swing_cohort.py` | `research/engine_room/swing_cohort.csv` |
| **slice_scan** | L3 scan | E1 | market x fav_side x bet x slice | 1318 |  |  |  | 0 | `tools/slice_scan.py` | `research/engine_room/slice_scan.csv` |
| **mm_model_scorecard** | L4 market-maker copy | both | fuel x slice | 6 |  |  |  | 0 | `tools/mm_model.py` | `research/engine_room/mm_model_scorecard.csv` |
| **mm_anchor_scorecard** | L4 market-maker copy | both | fuel x slice | 6 |  |  |  | 0 | `tools/mm_anchor.py` | `research/engine_room/mm_anchor_scorecard.csv` |
| **l3_truckstop_scorecard** | live test | E1 | see file | 4 |  |  |  |  | `tools/truckstop_test.py` | `research/engine_room/l3_truckstop_scorecard.csv` |

## Planned (not built)

- **paths** (L2 for E2): one row is event x strike x (time slot in -> time slot out). buy at one slot's ask, sell at a later slot's bid: the intraday engine's raw table. Not built yet (Dan: after the tracking datasets are nailed).

## Join checks (do the tables really connect?)

| Check | Pass | Of | % |
|---|---|---|---|
| ladder rows hang off a master row (event + time slot) | 12790 | 12790 | 100.0 |
| slice rows hang off a master row (event + time slot) | 9874 | 9874 | 100.0 |
| slice lines exist in the full ladder (event + time slot + strike) | 23631 | 23631 | 100.0 |
| master rows whose as-of day exists in the inputs table | 12790 | 12790 | 100.0 |
| events whose settle day has an AAA number in aaa_daily | 581 | 581 | 100.0 |
| of those, settle value equals the AAA number (to 0.1 cent) | 580 | 581 | 99.8 |
| clock-mark rows whose label matches the real hour (fixed in the builder 2026-11-28; must be 100%) | 11641 | 11641 | 100.0 |
| master rows that are a distinct moment (fixed in the builder 2026-11-28; must be 100%) | 12790 | 12790 | 100.0 |
| ledger instance count equals slice rows | 23631 | 23631 | 100.0 |
| time columns are written in one text style | 1 | 1 | 100.0 |

## Sheet tabs (read-only windows; audit 2026-11-27)

| Workbook | Tab | Role | Fed from | Verdict |
|---|---|---|---|---|
| Build Board | Takeaways – master | what is true now | `research/takeaways/master.csv` | LIVE |
| Build Board | Takeaways – by chat | each chat's closing table | `research/takeaways/by_chat.csv` | LIVE |
| Build Board | Favorite Ledger | the 4 outcome boxes by price band | `research/engine_room/favorite_ledger.csv` | LIVE |
| Build Board | Backtest Master | how far back each market and input goes | `data/lake/master/COVERAGE.md` | LIVE, refresh after each master rebuild (last 11/26) |
| Build Board | Board | Dan's kanban of 21 build cards | `none (hand-kept)` | OVERLAPS CLAUDE.md section 6 and the Cards tab; not updated since the direction changed on 11/26 |
| Build Board | Cards | same 21 cards as a list | `none (hand-kept)` | DUPLICATE of Board |
| Build Board | Backtest – horizons | old daily / weekly / monthly miss table | `legacy scripts (backtest_horizons*.py)` | SUPERSEDED by the master + mm_model scorecards |
| Build Board | Example – weather bot | outside example | `none` | NOT CONNECTED (off-limits market) |
| Build Board | Example – MLB bot | outside example | `none` | NOT CONNECTED (off-limits market) |
| Inputs Map | Inputs Map | the 83 inputs and whether we hold each (column O) | `data/lake/master/inputs_daily.csv + COVERAGE.md` | LIVE |
| Inputs Map | Engine Room | pricing layers L0-L3 scorecard | `tools/engine_room.py via tools/sheet_payload.py` | LIVE but missing L4 (market-maker copy: mm_model / mm_anchor scorecards) |
| Inputs Map | Warehouse | every dataset + feed health | `data/warehouse_catalog.csv via tools/sheet_payload.py` | STALE since 11/25 (catalog not rebuilt; open oddity) |
| Inputs Map | Strategies | strategy gates tied to nautilus code | `nautilus/` | LIVE, waits on proven bricks |
| Inputs Map | Bricks | idea hopper from the first 60-day work | `none (hand-kept)` | OVERLAPS slice_scan survivors + favorite ledger leads; should be fed from them |
| Inputs Map | Testing | old test tree (T1.1 ...) | `DB table from Chat 2-3` | SUPERSEDED by LOG plans + takeaways |
| Inputs Map | 60 Day | the first 60-day panel | `panel_daily in data/kalshi_twins.db` | SUPERSEDED by the master (kept as history) |
| Inputs Map | Connectivity | one-day pipe test (Nov 23) | `none` | FROZEN history |
| Inputs Map | Formulas | the 18 formulas in plain words | `research/2026-11-25_formulas-and-panel-columns.md` | REFERENCE |
| Inputs Map | Custom Build | data that needs more than a daily job | `none (hand-kept)` | OVERLAPS Wishlist + CLAUDE.md section 6 step 2 + the gaps doc |
| Inputs Map | Wishlist | data or systems to add later | `none (hand-kept)` | OVERLAPS Custom Build + section 6 step 2 + the gaps doc |

## Rules

- A new table must name its layer, its engine, and its key columns from the set above, and be added to `T` in `tools/spine.py`.
- A new test writes its plan in `research/LOG.md` first, names the table and engine it reads, and lands its verdict in `research/takeaways/master.csv`.
- Roll-ups (ledger, scan) are rebuilt from `slices`; never edited by hand.
- **Database vs sheet:** these files are the database (query them through `tools/warehouse.py`, schema `lab`). Google Sheets tabs are read-only copies for Dan's phone; nothing is ever built or tested in a sheet.
- **Rebuild order:** `backtest_master.py` -> `slice_scan.py` -> `market_scorecard.py` -> `spine.py`. The spine exits with an error if a join check is under 100% (the one known AAA mismatch aside).
- **Quick questions** (the `test` command) are answered with `tools/ask.py` and logged in `research/QUESTION_LOG.md`.

## Known issues

- Fixed 2026-11-28 (master m20261128): two text styles for time columns; clock marks one hour early on clock-change days; an open on a clock mark counted twice.
- 1 of 581 events settles 0.1c or more away from the AAA print for that day (unchanged).
- Trade tape is short (diesel from 2026-09-27, gas from 2026-10-27) and order-book depth exists for diesel daily only: the scorecard's taker / maker and depth cells are blank elsewhere.
