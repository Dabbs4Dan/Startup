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
- **Quick questions are light (Dan, 2026-11-28).** A plain question about data we already hold ("what % of favorites over 75c win?") is answered with `tools/ask.py`, logged in `research/QUESTION_LOG.md` and mirrored to the Google Sheet "Kalshi – Question Log" (Sheet only: Dan, 2026-11-28). No LOG plan needed. It is a look-back, not a strategy test; the trial count and the vault live at the top of that file.
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
| **Question log** ⭐ | `research/QUESTION_LOG.md` (reading copy: Google Sheet "Kalshi – Question Log", id `1gEA0uReDapkYyfzYarXi94Pc4pswj73gE34-WYssDc8`, tab Questions, newest row on top) | The `test` command. Dated quick questions + answers, the trial count, the baselines, the vault date. Answer tool: `tools/ask.py`. |
| **Market scorecard** ⭐ | `tools/market_scorecard.py` → `research/engine_room/market_scorecard.csv` | The six markets on one ruler: events, favorite edge vs its noise, cost, crowd miss, taker vs maker, depth. Ranks which markets can be tested now. |
| **Bet grid** ⭐ | `tools/bet_grid.py` → `research/engine_room/bet_grid.csv` (`lab.bet_grid`), `bet_grid_summary.json`, `bet_grid_highlights.csv` | Every simple bet: market × YES/NO × price cut × time slot × busy line, with noise per cell and a luck check (1,000 replays). Superset of the favorite ledgers. Sheet tab "Big grid" in the Question Log holds the highlights. |
| **Method review** | `research/2026-11-27_method-review.md` | Outside guidance (Kalshi papers, Becker's repo, backtest-overfitting) + the build ladder + the three tracks (A structure, B information, C path). |
| **Truckstop test (L3)** ⭐ | `tools/truckstop_test.py` → `research/engine_room/l3_truckstop_scorecard.csv` | One row per day: truckstop move vs what the crowd missed. Refreshed hourly by `truckstops.yml`. Verdict at 10 scored days; PASS needs 20+. |
| **Spine** ⭐⭐⭐ | `tools/spine.py` → `data/lake/master/SPINE.md` | **Read before touching any table.** How every research table connects (keys: market → event → time slot → line), layers L0–L4, the two engines (E1 settle, E2 intraday), join checks, known issues. Re-run after any rebuild. All of it is queryable in the database: `tools/warehouse.py`, schema `lab`. |
| **Backtest master** ⭐⭐ | `tools/backtest_master.py` → `data/lake/master/` (`backtest_master.csv.gz`, `ladder_snapshots.csv.gz`, `inputs_daily.csv`, `aaa_daily.csv`, `COVERAGE.md`) | **The one table every backtest reads.** Versioned: `VERSION.json` (quote the version in every result; `m20261128-…` = first version, 3 builder bugs fixed). Both fuels × daily / weekly / monthly × 7 time slots, 3 busiest lines, crowd center, ~75 as-of-safe inputs, regime + holiday labels. `COVERAGE.md` = how far back, what was vetted, and the contract cards for the 6 markets. RULEBOOK = the tool's docstring. |
| **Kalshi full history** | `tools/pull_kalshi_history.py` → `data/lake/kalshi/<SERIES>/` | Every settled market + hourly candles from Kalshi's live AND historical tiers. `_series_discovered.csv` lists all 289 fuel-like series; related ones are pulled raw and join the master only after vetting. |
| **Deep scan** ⭐ | `tools/deep_scan.py` → `research/backtests/deep_scan/`, write-up `research/2026-11-26_deep-scan.md` | Every stored parameter × price band × side × hour, diesel + gas, with false-discovery filter + holdout + cross-product check. Re-run when a new parameter is added to `panel_daily`. |
| **Market-maker equation** | `tools/mm_model.py` → `research/engine_room/mm_model_scorecard.csv`, `mm_model_coefficients.csv` | The equation we solve backwards, 6 markets, 4 layers (center, width, shape, cost). v1: center 66–76% (gas monthly 19–28%); width only gas weekly. **`tools/mm_anchor.py`** (`mm_anchor_scorecard.csv`): engine fit on outside data, Kalshi sets 2 dials; lines still 6–16 pts off vs 2–4 spread; crowd beats our engine at the open (missing input). Extends L0.1. |
| **Slices + ratios** ⭐ | `tools/slice_scan.py` → `data/lake/master/slices.csv.gz`, `research/engine_room/slice_scan.csv` | Layer 2 (favorite outcomes per market × event × time × busy line) + layer 3 (11 own ratios) + scan with holdout and false-winner filter. Also writes `favorite_ledger.csv` (sheet tab **Favorite Ledger**): plain count of favorite won/lost by side and price band. |
| **Engine Room** | `tools/engine_room.py` → tables `algo_registry` / `inputs_asof` / `algo_predictions` / `algo_scorecard` (both DBs) | Proves each pricing algo layer (L0 market maker → L1 AAA → L2 OPIS state roll-up → L3 inputs) before patterns. Sheet tab **Engine Room** (diesel + gas). Only ✅ PASS algos (20+ points) may feed slices/bricks. |
| **Strategy engine** | `nautilus/` (read `nautilus/README.md`) | NautilusTrader **2.0.0rc9, locked**. Same strategy code → backtest → Kalshi demo → live. Strategy IDs = sheet tab **Strategies** (S00 = replay check, no orders). |
| DIY scheduler | `.github/workflows/live_recorder.yml` (relay step) | ⚠️ GitHub ignores `schedule:` off `main`. Each recorder shift starts the next, then runs `nautilus.yml` + daily backfill if none in 20h. Pause: commit `data/live/STOP`. |
| **Live recorder** | `tools/live_recorder.py` → `data/live/<feed>/YYYY-MM-DD.csv` | Free GitHub shifts, every 5 min: Kalshi diesel+gas strikes, order book (15 min), AAA national + flip log (15 min), HO/Brent/WTI/RBOB/natgas (TradingView, ~10 min delayed). Map to Inputs Map rows: `research/2026-11-25_live-recorders.md` + sheet column N. |
| **Warehouse** ⭐ | `tools/warehouse.py` (DuckDB) + `data/lake/history/` (`tools/history_pull.py`, `warehouse.yml`) | ONE query layer over every source (diesel + gas SQLite, live CSVs, history CSVs, Engine Room files). Unified views: `aaa_daily`, `state_prices`, `ladder`, `trades`, `futures_bars`, `spot_daily`, `eia_weekly`, `orderbook`, `truckstops`, each with `era` (history / since_live). Catalog → `data/warehouse_catalog.csv` → sheet tab **Warehouse**. Notes: `research/2026-11-25_warehouse.md`. |

### Older database views (`data/schema.sql`; new work reads the master)

`v_diesel_breakdown` (per day: AAA split into crude / refining / taxes / delivery) · `diesel_daily` · `kalshi_markets` · `kalshi_candles` (`v_event_hourly`) · `daily_story` (`tools/story.py`).

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
| `probe.yml`, `connectivity.yml` | one-off source probes (11/27: `tools/probe_archive.py` = what the Internet Archive holds for live pump-price pages → `research/engine_room/archive_probe*.csv`) | `research/` | push |

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

**Edge thesis:** AAA retail is a slow, smoothed number; wholesale + crude move first. Retail "catches up" over days
(EIA notes the refining and delivery slices swing because of this lag). So tomorrow's AAA is partly visible today.
A swollen delivery slice (Nov 24: $1.50 vs ~$0.84 in Jan 2026) = pump prices still have room to fall.

**Settlement facts:** KXDIESELD "Diesel prices tomorrow" resolves on AAA's national average diesel (AAA data is from OPIS, updated daily).
Strikes are $0.005 apart. Market opens 8:00 AM ET the day before (API open_time; the app's "10:00 PM" label is NOT the open). Close: 11:59 PM ET (Nov) / ~1:59 AM ET (Aug–Sep archive).

**How Kalshi prices the ladder (verified 2026-11-24):**
- Each strike's % = the crowd's probability that AAA > strike. Whole ladder = one probability curve.
- Chance of landing in a half-cent bin = P(>low) − P(>high). "Forecast" shown in app = where ladder crosses 50%.
- Payout per $1 = 1 ÷ (ask price + taker fee). Taker fee = 0.07 × P × (1−P) per contract (rounded up per order). Maker fee 0.0175× on some series. Matched app payouts to the penny.
- Price tick 1¢. ~16-hour market. AAA daily move: median 1.43¢, max 3.9¢ (Sep–Nov 2026) → only ~3–6 strikes are ever "live".

**Earlier formula work** (N → F → Z): `research/2026-11-24_N-F-Z-framework.md`, `research/2026-11-24_formula-reconstruction.md`. Not a tradable edge by itself (M12, M15, M35).

**Risk formula (2026-11-25, `tools/risk_calc.py`):** c = price + fee. P&L = (B/n)·[(n−L)(1−c)/c − L]. Max losses L* = n(1−c). Win rate needed = c. Wins per loss = c/(1−c). Chance negative = P(Binomial(n,1−q) > L*).

**Official diesel rulebook (verified 2026-11-25):** KXDIESELD series `contract_terms_url` = ECONSTAT.pdf (same generic econ-stat terms). Source Agency = AAA (Trading Economics backup). First release counts, later revisions ignored. Market rule: "If the Diesel Price on <date> is above $K → Yes", strike_type greater, settlement timer 30 min, closes early "if the economic data is released". Fee type quadratic, multiplier 1. ⚠️ Prohibition: people with material non-public info on the Underlying (or employed by the Source Agency) may not trade → check any paid OPIS data for MNPI risk before using it.

**Free AAA history hack:** Kalshi's settled KXDIESELD markets carry `expiration_value` = the exact AAA number (verified 5.7982 = AAA site).

---

## 6. Now: the direction (updated 2026-11-28, Chat 7)

**Stage: still raw data + simple questions first (Dan, 2026-11-28).** We are still finding which of the 6 markets has
the most edge. Simple counts on raw Kalshi data come before deep plays. Build ladder (method review, approved rungs 1-3):

| Rung | Step | Status |
|---|---|---|
| 1 | **Lock the canvas:** 3 builder bugs fixed, master versioned, spine checks run after every rebuild | ✅ 11/28 |
| 2 | **Market scorecard:** six markets on one ruler (`market_scorecard.csv`) | ✅ v1 11/28. Depth and trade tape only cover the two daily markets |
| 3 | **Guard rails:** trial count, baselines, vault (events settling after 2026-11-27), question log + `test` command | ✅ 11/28 |
| 4 | **Track A (structure = the crowd's habits):** favorites, long shots, Yes vs No, taker vs maker | ◐ Q001–Q004. Bet grid: losers beyond luck (YES overpriced in gas, long shots); winners not. One candidate: gas daily NO-favorite at 10 PM–close |
| 5 | **Track B (information = know AAA sooner):** truckstop scorecard (first read ~Dec 6), free data fill (state AAA history, more posted-price chains, older trade tape) | ◐ running |
| 6 | **Track C (path = intraday price route, engine E2):** `paths` table, market-maker copy graded here | ⬜ after 30+ days of recorded order book |

**Where it stands (scorecard, master m20261128):** favorites beat their price only in diesel daily (+2.9 points, noise 2.1, 110 events, one falling stretch). Gas is priced about fair; gas Yes-favorites lose. Takers beat makers in both daily markets on our short tape. No edge is proven: all look-back on days already scanned.

**Becker's public data set:** what it holds and how we could use it → method review + `master.csv` M74.

**Still true:** deep scan found no stored parameter that predicts the 10 AM miss; the market-maker copy is 6–16 points
off per line. **Parked:** limit-order favorites (M28) · evening overshoot in a rising trend (M36).

**Waiting on Dan (11/28):** (1) record all six but test on gas daily, gas weekly, diesel daily, vs "all six equally" · (2) Becker's gas trades by GitHub job, or extend our own trade pull · (3) "clean it" = hide 6 replaced sheet tabs · (4) Crowd-habit leans (Q001–Q005, e.g. gas NO-favorite at 10 PM) are **not the strategy** (Dan, 11/28, 2:52 AM): we bet on our own AAA forecast (fundamentals) and size up when the price gap is big. The leans stay as clues to a missing input and as a baseline our forecast must beat.

**Older open items:** rockets & feathers (G9) · exact AAA post time (G2) · 10 AM futures history (W1) · engine gaps in `nautilus/README.md`. Legacy scripts named in SPINE history: new work reads the master.

---

## 7. Log → `research/LOG.md`

The full dated log (newest first) lives in **`research/LOG.md`**. Add new entries **there**, at the top, not here.
Keep this file short: it is what every new session reads first.

## 8. Related places

- Google Drive "Kalshi Twins – Trading Brain" (Dan's personal Google account) — human-level tracking, earlier pairs-trading research (SPY vs US Large Cap perps).
- Mac folder `~/Documents/kalshi-twins` — earlier Claude Code home base (Kalshi demo API key lives there, never commit keys).
- Kalshi demo: https://demo.kalshi.co (API: external-api.demo.kalshi.co).
