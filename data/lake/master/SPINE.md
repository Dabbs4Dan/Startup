# The spine: how every research table connects

Built by `tools/spine.py` on 2026-11-27 23:12 UTC. Re-run after any table is rebuilt. Read this before adding a table.

**One set of keys:** market → event → time slot (`snapshot_et`) → line (`strike`). Days join to inputs by `asof_date`.

**Layers:** L0 inputs → L1 master → L2 slices (4 outcome boxes) → L3 our ratios + scan → L4 market-maker copy → takeaways (`research/takeaways/master.csv`).

**Two engines (every test says which one it is):**
- **E1 settle engine:** hold to the end. Did the line settle Yes or No vs the price paid.
- **E2 intraday engine:** trade the price path between time slots and exit before the end.

## Tables

| Table | Layer | Engine | One row is | Rows | Events | From | To | Duplicate keys | Built by | File |
|---|---|---|---|---|---|---|---|---|---|---|
| **inputs_daily** | L0 inputs | both | date | 2889 |  | 2019-01-01 | 2026-11-28 | 0 | `tools/backtest_master.py` | `data/lake/master/inputs_daily.csv` |
| **aaa_daily** | L0 inputs | both | date x fuel | 1558 |  | 2022-11-28 | 2026-11-27 | 0 | `tools/backtest_master.py` | `data/lake/master/aaa_daily.csv` |
| **backtest_master** | L1 master | both | event x snapshot x snapshot_et | 12896 | 581 | 2023-09-18 | 2026-11-27 | 0 | `tools/backtest_master.py` | `data/lake/master/backtest_master.csv.gz` |
| **ladder_snapshots** | L1 master | E2 (and shape layer) | event x snapshot x snapshot_et x floor_strike | 147830 | 581 |  |  | 0 | `tools/backtest_master.py` | `data/lake/master/ladder_snapshots.csv.gz` |
| **slices** | L2 slices + L3 ratios | E1 | event x snapshot x snapshot_et x line_rank | 23757 | 542 | 2023-09-25 | 2026-11-27 | 0 | `tools/slice_scan.py` | `data/lake/master/slices.csv.gz` |
| **favorite_ledger** | L2 roll-up | E1 | market x favorite x price_band | 84 |  |  |  | 0 | `tools/slice_scan.py` | `research/engine_room/favorite_ledger.csv` |
| **favorite_ledger_by_time_and_line** | L2 roll-up | E1 | market x favorite x cut x value | 137 |  |  |  | 0 | `tools/slice_scan.py` | `research/engine_room/favorite_ledger_by_time_and_line.csv` |
| **slice_scan** | L3 scan | E1 | market x fav_side x bet x slice | 1328 |  |  |  | 0 | `tools/slice_scan.py` | `research/engine_room/slice_scan.csv` |
| **mm_model_scorecard** | L4 market-maker copy | both | fuel x slice | 6 |  |  |  | 0 | `tools/mm_model.py` | `research/engine_room/mm_model_scorecard.csv` |
| **mm_anchor_scorecard** | L4 market-maker copy | both | fuel x slice | 6 |  |  |  | 0 | `tools/mm_anchor.py` | `research/engine_room/mm_anchor_scorecard.csv` |
| **l3_truckstop_scorecard** | live test | E1 | see file | 3 |  |  |  |  | `tools/truckstop_test.py` | `research/engine_room/l3_truckstop_scorecard.csv` |

## Planned (not built)

- **paths** (L2 for E2): one row is event x strike x (time slot in -> time slot out). buy at one slot's ask, sell at a later slot's bid: the intraday engine's raw table. Not built yet (Dan: after the tracking datasets are nailed).

## Join checks (do the tables really connect?)

| Check | Pass | Of | % |
|---|---|---|---|
| ladder rows hang off a master row (event + time slot) | 12788 | 12788 | 100.0 |
| slice rows hang off a master row (event + time slot) | 9870 | 9870 | 100.0 |
| slice lines exist in the full ladder (event + time slot + strike) | 23624 | 23624 | 100.0 |
| master rows whose as-of day exists in the inputs table | 12896 | 12896 | 100.0 |
| events whose settle day has an AAA number in aaa_daily | 581 | 581 | 100.0 |
| of those, settle value equals the AAA number (to 0.1 cent) | 580 | 581 | 99.8 |
| clock-mark rows whose label matches the real hour (misses = the 2 days a year clocks change; known builder bug) | 11687 | 11747 | 99.5 |
| master rows that are a distinct moment (misses = the open landing on a clock mark, counted twice downstream) | 12788 | 12896 | 99.2 |
| ledger instance count equals slice rows | 23757 | 23757 | 100.0 |

## Rules

- A new table must name its layer, its engine, and its key columns from the set above, and be added to `T` in `tools/spine.py`.
- A new test writes its plan in `research/LOG.md` first, names the table and engine it reads, and lands its verdict in `research/takeaways/master.csv`.
- Roll-ups (ledger, scan) are rebuilt from `slices`; never edited by hand.
- **Database vs sheet:** these files are the database (query them through `tools/warehouse.py`, schema `lab`). Google Sheets tabs are read-only copies for Dan's phone; nothing is ever built or tested in a sheet.

## Known issues (fix in the builder, then re-run everything downstream)

- `snapshot_et` is written in two text styles; compare it as a time, not as text.
- On the two days a year clocks change, the five clock marks sit one hour early (60 of 11,747 rows).
- When a market opens exactly on a clock mark, that moment appears twice (open + the mark): 108 master rows, 133 slice rows (0.6%).
