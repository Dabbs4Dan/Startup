# Kalshi Twins — Trading Research Brain

> Read this file first, every session. It tells you what the project is, where everything lives,
> what we've learned, and exactly where we left off. Branch: `kalshi-twins` of `Dabbs4Dan/Startup`
> (separate from `main`, which is Dan's startup-mentor project — never touch `main` from here).

---

## 0. Start here: how every session works (added 2026-11-26, Chat 6)

**Starting a session (2 minutes):**
1. `git pull` the `kalshi-twins` branch. Read this file. Then read **§6 (Now)**: it holds the one live direction.
2. Read `research/takeaways/master.csv` (what is true now) and the top 3 entries of `research/LOG.md` (what just happened).
3. Check feeds: bottom of `data/warehouse_catalog.md` (OK / STALE).
4. Tell Dan which chat number you are and what you will do. Don't re-open settled questions (§3b, master.csv).

**Ending a session (always, without being asked):**
1. Add a `research/LOG.md` entry at the top. Title starts with the chat number: `### 2026-11-26 (2:10 AM) · Chat 6 · title`.
2. Update takeaways: edit the lists in `research/takeaways/build_takeaways.py`, run it, mirror both tabs to the Build Board sheet.
3. If the direction, a job, or a file location changed: update §4 or §6 here. Keep this file under ~20 KB.
4. Push. Confirm the push landed (`git ls-remote origin refs/heads/kalshi-twins`).

**Working rules (so chats don't collide or fool themselves):**
- **Several chats push to this branch.** Always `git pull --rebase` right before pushing. Never force-push. Never move or rename a file a workflow uses without updating the Jobs table and every workflow that names it.
- **One home per fact.** Findings → `master.csv`. History of what was done → `LOG.md`. Where things are → §4. What's next → §6. Gaps → `research/2026-11-26_gaps-and-direction.md`. Don't start a new tracking file or sheet tab for something that already has a home.
- **Write the test before running it.** One LOG line first: the question, the one number that decides it, the days held out. Then run. We have ~115 days and have tested dozens of cuts; a lucky "winner" is expected (the favorites edge went +8% → +3.3% not proven this way).
- **A result counts only with** day-clustered ranges, costs included, and a check on days the rule never saw. Otherwise label it "hint".
- **Check the thing before building on it (added 2026-11-27).** For any market or data source, first read its own rule text and write its fact card (`data/lake/master/COVERAGE.md` → Contract cards). In every plan, split what you rely on into **verified** (say how) and **assumed**. Tell Dan the assumed ones up front; chase any oddity the same day (Chat 6 built the master before checking that weekly and monthly settle like daily; they do, but that was luck).
- **Data flow is one-way:** recorders/pulls → raw files + DBs → warehouse views → Engine Room scorecards → takeaways → Sheets. Sheets and CSV exports are read-only copies; never treat them as a source.

```
Kalshi / AAA / futures / truckstops / EIA
        │  (GitHub jobs, started by the relay)
        ▼
data/live/*.csv   data/kalshi_twins.db   data/gas/   data/lake/history/     ← RAW (append-only, one writer each)
        ▼
tools/warehouse.py  (DuckDB views: one place to query everything)           ← QUERY LAYER
        ▼
Engine Room + scorecards (research/engine_room/, algo_scorecard)            ← PROOF (20+ days to PASS)
        ▼
research/takeaways/master.csv  →  Google Sheets (Build Board)               ← WHAT DAN READS
```

---

## 1. Mission (one paragraph)

Build an AI-assisted algorithmic trading system for **Kalshi** event contracts, starting with **U.S. retail diesel**.
Dan is the visionary/curator (ideas, intuition, spotting holes). Claude does the heavy lifting: data, code, research, testing.
Goal: a research table that mimics the real diesel pricing engine *independently of Kalshi*, so we can forecast tomorrow's
AAA diesel number and find gaps vs. Kalshi's odds. Demo money only until a strategy is proven on history.

## 2. Rules for the market we trade (Dan's criteria, 2026-11-24)

- Must be **consistent and repeatable** → daily or weekly trades a bot can optimize.
- **Off limits:** temperature/weather, securities (crypto, stocks, companies), irregular events (sports, concerts, culture).
- Current focus: **diesel** (KXDIESELD daily). Sister market: **gas** (KXAAAGASD daily / KXAAAGASM weekly). Later: 30-yr mortgage weekly.

## 3. How Claude should talk to Dan

- Plain language, ~4th-grade level, emojis as anchors, no walls of text.
- Medium length. Organize around **decisions and next steps**. End with one clear next step.
- Dan does as little hands-on work as possible (no Finder/Terminal). Claude builds, runs, commits, and pushes.
- **Mobile-first (Dan, 2026-11-25):** Dan works from his phone. Never ask him to open a computer, click banners, or run anything. Sheets: no `IMPORTDATA` (needs an "Allow access" click). Instead, after any data run, run `python3 tools/sheet_payload.py` and write each block with the Google Sheets connector (`update_values`).

## 3b. North star (Dan, 2026-11-25) — do not re-argue this

- We compete on the **same vantage point as the market maker**. Never frame their model as "private, so we play a different game."
- Market makers price the diesel ladder from inputs that are mostly knowable: AAA, OPIS-style sub-components (truckstop / rack prices), HO futures, timing. **Our job is to rebuild their model**: ladder at every minute = f(inputs known at that minute) + spread/inventory layer.
- Any ladder move our inputs don't explain = a **missing input** the market maker sees and we don't. That gap list is the shopping list for data.
- Edge = knowing **why** tomorrow's AAA moves with more certainty than AAA's own history tells (e.g. day X−1 truckstop prices → day X AAA), and earlier/better than the market maker's model.

---

## 4. Where everything lives (the map)

| What | Path | Notes |
|---|---|---|
| **Main database** | `data/kalshi_twins.db` | SQLite. The one place for data. |
| Schema (all tables + views) | `data/schema.sql` | Read this to know every column. |
| **Easy-view tables** | `data/exports/*.csv` | Auto-exported copies. GitHub shows them as tables. |
| Build/refresh DB | `tools/build_db.py` | Creates tables, seeds hand-verified rows. Safe to re-run. |
| Pull history | `tools/backfill.py` | Kalshi + Yahoo futures (+FRED backup). Fills blanks only, never overwrites. |
| Daily pull | `.github/workflows/backfill.yml` | Started by the relay (see Jobs table). `schedule:` never fires off `main`. |
| Deep research notes | `research/` | One dated file per topic. |
| **Takeaways** ⭐ | `research/takeaways/` (`master.csv` = what is true now, `by_chat.csv` = each chat's closing table) | Same as Build Board sheet tabs "Takeaways – master / by chat". Update both at the end of a chat. |
| This brain | `CLAUDE.md` | §0 = how to work, §6 = what's next. The dated log is `research/LOG.md`. |
| **Gaps + direction** ⭐ | `research/2026-11-26_gaps-and-direction.md` | 13 ranked gaps in our understanding and the one direction. Update statuses in place. |
| **Truckstop test (L3)** ⭐ | `tools/truckstop_test.py` → `research/engine_room/l3_truckstop_scorecard.csv` | One row per day: truckstop move vs what the crowd missed. Refreshed hourly by `truckstops.yml`. Verdict at 10 scored days; PASS needs 20+. |
| **Backtest master** ⭐⭐ | `tools/backtest_master.py` → `data/lake/master/` (`backtest_master.csv.gz`, `ladder_snapshots.csv.gz`, `inputs_daily.csv`, `aaa_daily.csv`, `COVERAGE.md`) | **The one table every backtest reads.** Both fuels × daily / weekly / monthly × 7 snapshots (open, 10 AM, noon, 3 PM, 6 PM, 10 PM, close; the five clock marks repeat on every open day), with the 3 most liquid lines, favorite line, crowd center, ~75 as-of-safe inputs, regime + holiday labels, per-market facts (fee type, strike step, days open). `COVERAGE.md` also holds the **contract cards** (how each of the 6 markets is built and settles) and the crowd's behavior by days to settlement. Inputs Map sheet column O says which of the 83 inputs are in it. The RULEBOOK is the docstring of the tool. Read `COVERAGE.md` first: it shows how far back everything goes and what was vetted. |
| **Kalshi full history** | `tools/pull_kalshi_history.py` → `data/lake/kalshi/<SERIES>/` | Every settled market + hourly candles for 7 series from Kalshi's live AND historical tiers (older markets only exist on `/historical/*`). Resumable. `_series_discovered.csv` lists all 289 fuel-like series Kalshi has (100 state-level daily gas markets, older tickers, heating oil, jet); the related ones are pulled raw and join the master only after vetting. |
| **Deep scan** ⭐ | `tools/deep_scan.py` → `research/backtests/deep_scan/`, write-up `research/2026-11-26_deep-scan.md` | Every stored parameter × price band × side × hour, diesel + gas, with false-discovery filter + holdout + cross-product check. Re-run when a new parameter is added to `panel_daily`. |
| **Market-maker equation** | `tools/mm_model.py` → `research/engine_room/mm_model_scorecard.csv`, `mm_model_coefficients.csv` | The equation we are solving backwards, all 6 markets, 4 layers: center, width, shape, cost. v1 (11/27): center explained 66–76% except gas monthly (19–28%, era drift); width cracked only for gas weekly (0.55); crowd's range too wide in all 6. **`tools/mm_anchor.py`** (`mm_anchor_scorecard.csv`): engine fit on outside data, Kalshi sets 2 dials; lines still 6–16 pts off vs 2–4 spread; crowd beats our engine at the open (missing input). Extends L0.1. |
| **Engine Room** | `tools/engine_room.py` → tables `algo_registry` / `inputs_asof` / `algo_predictions` / `algo_scorecard` (both DBs) | Proves each pricing algo layer (L0 market maker → L1 AAA → L2 OPIS state roll-up → L3 inputs) before patterns. Sheet tab **Engine Room** (diesel + gas). Only ✅ PASS algos (20+ points) may feed slices/bricks. |
| **Strategy engine** | `nautilus/` (read `nautilus/README.md`) | NautilusTrader **2.0.0rc9, locked**. Same strategy code → backtest → Kalshi demo → live. Strategy IDs = sheet tab **Strategies** (S00 = replay check, no orders). |
| DIY scheduler | `.github/workflows/live_recorder.yml` (relay step) | ⚠️ GitHub ignores `schedule:` off `main`. Each recorder shift starts the next, then runs `nautilus.yml` + daily backfill if none in 20h. Pause: commit `data/live/STOP`. |
| **Live recorder** | `tools/live_recorder.py` → `data/live/<feed>/YYYY-MM-DD.csv` | Free GitHub shifts, every 5 min: Kalshi diesel+gas strikes, order book (15 min), AAA national + flip log (15 min), HO/Brent/WTI/RBOB/natgas (TradingView, ~10 min delayed). Map to Inputs Map rows: `research/2026-11-25_live-recorders.md` + sheet column N. |
| **Warehouse** ⭐ | `tools/warehouse.py` (DuckDB) + `data/lake/history/` (`tools/history_pull.py`, `warehouse.yml`) | ONE query layer over every source (diesel + gas SQLite, live CSVs, history CSVs, Engine Room files). Unified views: `aaa_daily`, `state_prices`, `ladder`, `trades`, `futures_bars`, `spot_daily`, `eia_weekly`, `orderbook`, `truckstops`, each with `era` (history / since_live). Catalog → `data/warehouse_catalog.csv` → sheet tab **Warehouse**. Notes: `research/2026-11-25_warehouse.md`. |

### Tables & views (what to query)

- `v_diesel_breakdown` ⭐ — **start here.** Per day: AAA price, crude / refining / taxes / delivery in $ and %, 1-day change.
- `diesel_daily` — raw inputs per day (AAA, Brent, ULSD, EIA weekly, taxes) + the source of each value.
- `kalshi_markets` — every KXDIESELD strike: strike, result, settle value, last price, bid/ask, volume, OI, full raw JSON.
- `kalshi_candles` — hour-by-hour yes bid/ask/mid/spread/volume for every market (18K rows). `v_event_hourly` = same joined with the final AAA answer.
- `daily_story` ⭐ — one row per day: AAA before/after, market forecast at 10 AM (mu_N) and close (mu_C), the 75¢ bet (N_price, F_payout), HO moves, delivery slice. Built by `tools/story.py`.
- `v_win_loss` — `daily_story` split into WIN / LOSS rows (export `win_loss.csv`) for trend extraction.
- `sources` — where each number comes from.
- `research_log` — queryable copy of findings (mirror of the log below).

Quick query example: `sqlite3 data/kalshi_twins.db "SELECT * FROM v_diesel_breakdown ORDER BY date DESC LIMIT 10;"`

### Jobs (all started by the relay or by a push to their own files; none use `schedule:`)

| Workflow | What it does | Writes (commits) | Started by |
|---|---|---|---|
| `live_recorder.yml` | 5-min Kalshi + futures, 15-min order book + AAA; **relay**: starts next shift + nautilus + truckstops + daily jobs | `data/live/` | itself (relay), push to its files |
| `truckstops.yml` | Love's + TA posted prices, hourly, **saved after every snapshot**; then refreshes the L3 scorecard | `data/live/truckstops/`, `research/engine_room/l3_truckstop_scorecard.csv` | relay each shift |
| `backfill.yml` | diesel daily pull: Kalshi, trades, candles, panel, testing, Engine Room | **`data/kalshi_twins.db`** (only writer), `data/exports/` | relay if no success in 20h |
| `gas_backfill.yml` | same for gas (side test) | **`data/gas/`** (only writer) | relay if no success in 20h |
| `warehouse.yml` | daily futures (full history) + ~70 EIA series (regional pump prices, stocks, refining, demand) + Yahoo intraday + Internet Archive AAA national → catalog + feed health | `data/lake/`, `data/warehouse_catalog.*`, `data/feed_health.csv` | relay if no success in 20h |
| `kalshi_history.yml` | full Kalshi history, 7 fuel series, both tiers | `data/lake/kalshi/` | by hand / push |
| `history.yml` | Internet Archive AAA **state** pages → Engine Room re-score | `research/engine_room/` (never the DB) | by hand / push |
| `nautilus.yml` | engine replay + fee check | `nautilus/reports/` | relay |
| `probe.yml`, `connectivity.yml` | one-off source probes | `research/` | push |

**Rules every session must keep:**
1. **One writer per database.** Only `backfill.yml` commits the diesel DB; only `gas_backfill.yml` commits the gas DB. Anything else that touches a DB must `git checkout --` it before committing.
2. **Never `cancel-in-progress: true` on a data job.** A push must not kill a running pull.
3. **Push triggers list only the job's own scripts** (never `tools/**`).
4. **Is it working?** Read `data/warehouse_catalog.md` (bottom: Feed health, OK/STALE). Sheet tab **Warehouse** shows the same.
5. **Sheets:** no IMPORTDATA. After a data run: `python3 tools/sheet_payload.py`, then write each block with the Sheets connector.

---

## 5. Core knowledge (the diesel engine)

**Formula (EIA "Today in Energy" method):**
```
AAA diesel = Crude + Refining + Taxes + Delivery
Crude      = Brent $/bbl ÷ 42
Refining   = NY Harbor ULSD wholesale − Crude
Taxes      = 24.4¢ federal + 35.86¢ avg state (EIA, Jan 2026)
Delivery   = AAA − ULSD − Taxes   (trucks, station costs + profit; the "leftover")
```

**Nov 24, 2026 snapshot:** crude $2.1610 (37.3%) · refining $1.5344 (26.5%) · delivery $1.5002 (25.9%) · taxes $0.6026 (10.4%) = **$5.7982**.

**Edge thesis:** AAA retail is a slow, smoothed number; wholesale + crude move first. Retail "catches up" over days
(EIA notes the refining and delivery slices swing because of this lag). So tomorrow's AAA is partly visible today.
A swollen delivery slice (Nov 24: $1.50 vs ~$0.84 in Jan 2026) = pump prices still have room to fall.

**Settlement facts:** KXDIESELD "Diesel prices tomorrow" resolves on AAA's national average diesel (AAA data is from OPIS, updated daily).
Strikes are $0.005 apart. Market opens 8:00 AM ET the day before (API open_time; the app's "10:00 PM" label is NOT the open). Close: 11:59 PM ET (Nov) / ~1:59 AM ET (Aug–Sep archive).

**How Kalshi prices the ladder (verified 2026-11-24):**
- Each strike's % = the crowd's probability that AAA > strike. Whole ladder = one probability curve.
- Chance of landing in a half-cent bin = P(>low) − P(>high). "Forecast" shown in app = where ladder crosses 50%.
- Payout per $1 = 1 ÷ (ask price + taker fee). Taker fee = 0.07 × P × (1−P) per contract (rounded up per order). Maker fee 0.0175× on some series. Matched app payouts to the penny.
- Daily market opens 8:00 AM ET the day before, closes 11:59 PM ET, settles on the next day's AAA number. ~16-hour market, not 24h.
- Price tick 1¢. Strikes $0.005 apart. AAA daily move: median 1.43¢, max 3.9¢ (Sep–Nov 2026) → only ~3–6 strikes are ever "live".

**Earlier formula work** (N → F → Z framework, reconstructed crowd and truth formulas, momentum 0.89× vs 0.73×): `research/2026-11-24_N-F-Z-framework.md`, `research/2026-11-24_formula-reconstruction.md`. Tested since: not a tradable edge by itself (`master.csv` M12, M15, M35).

**Risk formula (2026-11-25, `tools/risk_calc.py`):** c = price + fee. P&L = (B/n)·[(n−L)(1−c)/c − L]. Max losses L* = n(1−c). Win rate needed = c. Wins per loss = c/(1−c). Chance negative = P(Binomial(n,1−q) > L*).

**Official diesel rulebook (verified 2026-11-25):** KXDIESELD series `contract_terms_url` = ECONSTAT.pdf (same generic econ-stat terms). Source Agency = AAA (Trading Economics backup). First release counts, later revisions ignored. Market rule: "If the Diesel Price on <date> is above $K → Yes", strike_type greater, settlement timer 30 min, closes early "if the economic data is released". Fee type quadratic, multiplier 1. ⚠️ Prohibition: people with material non-public info on the Underlying (or employed by the Source Agency) may not trade → check any paid OPIS data for MNPI risk before using it.

**Formula registry + master-panel column plan:** `research/2026-11-25_formulas-and-panel-columns.md` (18 formulas, ~50 columns with ease/parent/source).

**Free AAA history hack:** Kalshi's settled KXDIESELD markets carry `expiration_value` = the exact AAA number (verified 5.7982 = AAA site).

---

## 6. Now: the direction (updated 2026-11-26 evening, Chat 6)

**Stage: raw data collection (Dan, 2026-11-26).** Build the biggest clean canvas first, test later.
Scope: **gas and diesel × daily, weekly, monthly**, every input we can break the Kalshi / AAA / OPIS-style pricing
down into. This reopens gas and the weekly/monthly ladders (paused the night before) for data collection.

| Order | Step | Status |
|---|---|---|
| 1 | **Backtest master**: one table for both fuels and all three time slices (`data/lake/master/`) | ✅ v1 built 11/26; see `COVERAGE.md` |
| 2 | **Fill what is still missing**: state-level AAA history (Internet Archive), older trade tape (`/historical/trades`), AAA national before mid-2023/2024, rack prices (no free source), **live station-price average history** (top suspect for what the daily crowd sees, M56–M57; no free history). Futures curve: pulling since 11/27 | ⬜ |
| 3 | **Custom arrays on top of the master** (Dan's next stage): regime tables, Sharpe-style scoring, correlations | ⬜ not started; wait for Dan |
| 4 | Live side keeps running by itself: truckstop scorecard (first read ~Dec 6), order-book depth (G1) | ◐ |

**Still true:** no edge is proven. Deep scan (11/26): no stored parameter predicts the direction of the 10 AM miss
(0 of 38); the all-parameter model makes forecasts worse. Gaps list: `research/2026-11-26_gaps-and-direction.md`.

**Parked findings (not being worked):** limit-order favorites, +6.2% per $ in diesel (`master.csv` M28) · evening
crowd overshoots a rising trend, gas +28% per $ on 63 days (M36; needs a forward test in the next rising stretch).

**Rules for the next tests:** read the master, follow its RULEBOOK, write the test in the LOG first, cluster weekly
and monthly results by event, and keep the false-discovery filter + holdout from `tools/deep_scan.py`.

**Older open items:** rockets & feathers lag study (G9) · exact AAA post time (G2, flip log recording) · 10 AM
futures history (Wishlist W1). Older backtest scripts (`backtest_horizons*.py`, `edge_check.py`, `favorite_test.py`,
`sim_favorites.py`, `signal_scan.py`) are legacy: new work reads the master instead.

---

## 7. Log → `research/LOG.md`

The full dated log (newest first) lives in **`research/LOG.md`**. Add new entries **there**, at the top, not here.
Keep this file short: it is what every new session reads first.

## 8. Related places

- Google Drive "Kalshi Twins – Trading Brain" (Dan's personal Google account) — human-level tracking, earlier pairs-trading research (SPY vs US Large Cap perps).
- Mac folder `~/Documents/kalshi-twins` — earlier Claude Code home base (Kalshi demo API key lives there, never commit keys).
- Kalshi demo: https://demo.kalshi.co (API: external-api.demo.kalshi.co).
