# Kalshi Twins — Trading Research Brain

> Read this file first, every session. It tells you what the project is, where everything lives,
> what we've learned, and exactly where we left off. Branch: `kalshi-twins` of `Dabbs4Dan/Startup`
> (separate from `main`, which is Dan's startup-mentor project — never touch `main` from here).

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
| This brain | `CLAUDE.md` | Log at the bottom, newest first. |
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
| `truckstops.yml` | Love's + TA posted prices, hourly | `data/live/truckstops/` | relay each shift |
| `backfill.yml` | diesel daily pull: Kalshi, trades, candles, panel, testing, Engine Room | **`data/kalshi_twins.db`** (only writer), `data/exports/` | relay if no success in 20h |
| `gas_backfill.yml` | same for gas (side test) | **`data/gas/`** (only writer) | relay if no success in 20h |
| `warehouse.yml` | EIA + Yahoo + Internet Archive AAA national → catalog + feed health | `data/lake/`, `data/warehouse_catalog.*`, `data/feed_health.csv` | relay if no success in 20h |
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

**N → F → Z framework (2026-11-24):** N = price of our side at bet (10 AM), F = 1 if it wins, Z = win rate. Profit iff Z > avg(N+fee).
AAA engine fit (67 days, R² 0.65): ΔAAA ≈ 6.06¢ − 6.72¢×Delivery($) + 1.83¢×HO bet-day move($). Market already prices this by 10 AM.
Losses come from the intraday info gap (market forecast moves 0.73¢ on losing days vs 0.31¢ on wins), not explained by futures → look at station-level prices. See `research/2026-11-24_N-F-Z-framework.md`.

**Reconstructed formulas (2026-11-24, see `research/2026-11-24_formula-reconstruction.md`):**
- N (crowd at 10 AM): mu_N ≈ AAA_today + 0.89×yesterday's change (R² 0.69), σ ≈ 0.35¢, + bias/spread/fee layer. Kalshi publishes no pricing model (order book + private market makers).
- F (truth): AAA_tomorrow ≈ AAA_today + 0.73×yesterday's change (R² 0.66) + fundamentals + unmeasured station-price moves. Crowd at close ≈ 0.77× (miss 0.11¢).
- Morning crowd over-extrapolates momentum (0.89 vs 0.73) = first candidate edge.
- ⚠️ Update 2026-11-25: momentum-only fails after big wholesale moves (Nov 25: said 5.7804). Base F formula = fundamentals version: AAA_today − 6.72%×(Delivery − $0.90) + 1.83¢/$ HO today − 1.30¢/$ HO prior 5d → 5.7626 vs crowd 5.7625.

**Risk formula (2026-11-25, `tools/risk_calc.py`):** c = price + fee. P&L = (B/n)·[(n−L)(1−c)/c − L]. Max losses L* = n(1−c). Win rate needed = c. Wins per loss = c/(1−c). Chance negative = P(Binomial(n,1−q) > L*).

**Official diesel rulebook (verified 2026-11-25):** KXDIESELD series `contract_terms_url` = ECONSTAT.pdf (same generic econ-stat terms). Source Agency = AAA (Trading Economics backup). First release counts, later revisions ignored. Market rule: "If the Diesel Price on <date> is above $K → Yes", strike_type greater, settlement timer 30 min, closes early "if the economic data is released". Fee type quadratic, multiplier 1. ⚠️ Prohibition: people with material non-public info on the Underlying (or employed by the Source Agency) may not trade → check any paid OPIS data for MNPI risk before using it.

**Formula registry + master-panel column plan:** `research/2026-11-25_formulas-and-panel-columns.md` (18 formulas, ~50 columns with ease/parent/source).

**Free AAA history hack:** Kalshi's settled KXDIESELD markets carry `expiration_value` = the exact AAA number (verified 5.7982 = AAA site).

---

## 6. Open questions / next steps

| # | Item | Status |
|---|---|---|
| 1 | Confirm backfill ran on GitHub; check row counts | ✅ 2026-11-24 |
| 2 | Lag study: how many days for a ULSD move to reach AAA? Up vs. down speed (rockets & feathers)? | ⬜ |
| 3 | Find the exact time AAA posts each day | ◐ flip tracker live since 11/25 (`aaa_flips`) — read after ~1 week |
| 4 | Turn the forecast into odds per strike; compare with Kalshi prices (backtest on history) | ⬜ |
| 5 | Gas twin | ✅ side test/analog (own DB + workbook) |
| 6 | Real-time ULSD/HO source | ◐ TradingView ~10-min delayed, live since 11/25; EIA daily settles/spot for history |
| 8 | Minute-level candles | ✅ top-3 lines daily (`kalshi_trades.py`) + all strikes every 5 min live |
| 9 | Edge test: does our engine's morning forecast beat the market's morning ladder? | ⬜ |
| 10 | Master research panel | ◐ `panel_daily` (10 AM + close); warehouse views for any snapshot time |
| 7 | Longer AAA history | ◐ Internet Archive national (since 2019) + states running; EIA weekly 1994+ ✅ |

---

## 7. Log → `research/LOG.md`

The full dated log (newest first) lives in **`research/LOG.md`**. Add new entries **there**, at the top, not here.
Keep this file short: it is what every new session reads first.

## 8. Related places

- Google Drive "Kalshi Twins – Trading Brain" (Dan's personal Google account) — human-level tracking, earlier pairs-trading research (SPY vs US Large Cap perps).
- Mac folder `~/Documents/kalshi-twins` — earlier Claude Code home base (Kalshi demo API key lives there, never commit keys).
- Kalshi demo: https://demo.kalshi.co (API: external-api.demo.kalshi.co).
