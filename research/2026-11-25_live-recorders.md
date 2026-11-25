# Live recorders (free, GitHub-only) — 2026-11-25

**Why:** some inputs have no history anywhere. If we don't save them today, they're gone. This recorder saves them
without a paid server, using GitHub Actions "shifts".

## How it runs

- `tools/live_recorder.py` loops for one shift (~5h40m), taking a snapshot every 5 min, and pushes to GitHub about every hour.
- `.github/workflows/live_recorder.yml`: at the end of each shift, the **relay** step starts the next shift, then
  `nautilus.yml`, plus the daily backfill if none has succeeded in 20h.
  - GitHub ignores `schedule:` off the default branch (`main`), so the relay is our scheduler.
  - Dispatch uses the **numeric workflow ID**. `gh workflow run <file>` looks the file up on `main` and returns 404.
- **Pause:** commit an empty `data/live/STOP`. **Restart:** delete it, then dispatch `live_recorder.yml` once (by ID).
- A push that changes the recorder code runs a short 12-minute test shift. That shift then relays into full shifts.
- ⚠️ Minutes are free only while the repo is **public**. A private repo gets 2,000 min/month, and this uses ~41,000.
  Option when going private: keep the recorder plus public raw data in a separate public repo.
- ⚠️ There's a ~1–5 min gap between shifts (queue + setup). GitHub can also delay starts. Fine for research, not for trading → CB1 server later.

## Feeds → files → Inputs Map rows

| Feed | Every | File (one per ET day) | Columns | Inputs Map # | Custom Build |
|---|---|---|---|---|---|
| Kalshi strikes (diesel + gas) | 5 min | `data/live/kalshi_markets/` | strike, yes/no bid/ask, last, volume, volume_24h, open_interest, yes bid/ask sizes, close_time | 6, 7, 8, 10, 11, 12, 13, 16, 18, 19, 21, 22, 23, 24, 77, 79 | CB5-lite |
| Kalshi order book (6 most-traded live diesel lines, 3–97%) | 15 min | `data/live/kalshi_orderbook/` | price, contracts per level, side (`*_dollars` fields, fractional contracts) | 13, 14 | CB5 |
| AAA national | 15 min | `data/live/aaa_national/` | price_as_of, diesel_current, diesel_yesterday, regular_gas_current | 1, 80 | CB4 |
| AAA flips | on change | `data/live/aaa_flips.csv` | first_seen time, new value, old value | 4 (→ 5 indirectly) | CB4 |
| Futures quotes | 5 min | `data/live/futures/` | HO, BRENT, WTI, RBOB, NATGAS: open/high/low/last + source | 29 (HO − Brent/42), 33, 35, 36, 38, 39, 40, 41 | CB3 |

The same mapping is in the sheet: **Inputs Map → column N**.

**Source notes (verified on GitHub, Nov 25):**
- Kalshi public API works (no key needed).
- AAA homepage works (diesel 5.7645 as of 11/25/26).
- Futures: **TradingView scanner** works. Quotes are `delayed_streaming_600`, about **10 minutes behind**. Yahoo returns 429 and Stooq times out from GitHub, so they're kept only as fallbacks.
  Sanity check: HO 3.6562, Brent 90.58 (crude slice ≈ 2.157, matches panel).
- If the columns change, the recorder starts a new file (`DATE_v2.csv`), so headers never mix.

## Where to point it (algos & testing)

1. **AAA flip time (#4):** after a week of `aaa_flips.csv`, find the earliest time tomorrow's number is knowable. That's the input for the "can_close_early" / last-hour rules.
2. **Crowd forecast every 5 min (#6, #16, #77):** fit μ/σ from `kalshi_markets` per snapshot. That gives the big-jump flag and lines jumps up against `futures` and `aaa_flips` (the noon-move mystery).
3. **Slippage (#14):** walk `kalshi_orderbook` for $100 / $1,000 orders. That feeds the fill model in `nautilus/` (loaders already read live CSVs with top-of-book sizes).
4. **HO at 10 AM, no peeking (#35, CB2):** going forward, take the last `futures` HO row ≤ 10:10 ET (10-min delay) and put it in `panel_daily.ho_10am`.
5. **Crack spread live (#29, #38):** HO − Brent/42 per snapshot. That flags big refining moves during the bet window.
6. **Gas twin (#79, #80):** the same recorder already saves the KXAAAGASD ladder plus AAA regular gas.

## Not recorded (and why)

- Truckstop prices (#47–50): terms-of-use check pending (CB10).
- GasBuddy (#54): terms check (CB11).
- Rack prices (#42): paid OPIS + Kalshi insider-info rule (CB12).
- Weekly diesel market (#81): series ticker still to confirm.
