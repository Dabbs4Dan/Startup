# Kalshi Twins — full research log (newest first)

Moved out of CLAUDE.md on 2026-11-25 so new sessions load fast. **Add new entries at the top of this file.**

Template:
```
### YYYY-MM-DD (time) · short title
- **Did:** …
- **Learned:** …
- **Decided:** …
- **Next:** …
```

### 2026-11-26 (12:45 AM) · Backtest across horizons: the market beats our simple models everywhere
- **Did:** `tools/backtest_horizons.py` (daily ladders + 1/7/30-day history + EIA weekly 1994+) and `tools/backtest_horizon_ladders.py` (weekly/monthly ladders pulled by new one-off `horizon_ladders.yml`). Walk-forward models, bets at ask + fee, clustered CIs. Notes: `research/2026-11-26_backtest-horizons.md`.
- **Learned:** Daily: market median miss 0.55¢ (diesel) vs best model 0.70¢; all model bets lose. History: gap + momentum beats "no change" by ~24% at 7 days, ~0–9% at 30 days. Weekly ladders (10 events each): market misses 2.5¢ (diesel) / 1.8¢ (gas) 5–7 days out vs our 7.8¢ / 5.6¢. Monthly: only 2 events each.
- **Decided:** simple price-history features are already priced at every horizon. Edge must come from new inputs (truckstops, rack, timing).
- **Next:** try Kalshi's historical endpoint for older weekly/monthly markets; re-run after 2–3 weeks of truckstop + rack data.

### 2026-11-26 (12:20 AM) · Imported an outside Kalshi bot that already models AAA diesel
- **Did:** Copied MIT-licensed `ryanfrigo/kalshi-ai-trading-bot` (commit 5d7b70a) into `research/sample_models/` with an analysis file. Two unlicensed bots (weather, MLB) are link-only in `research/sample_models/README.md` (copies in Dan's Drive "Sample Kalshi Models").
- **Learned:** It has its own KXDIESELD/KXAAAGASD model. Retail lags wholesale futures ~4–7 days (lag-7 R² ≈ 0.42); an "excess gap" (retail − wholesale vs trailing baseline) closes at ~2¢/day. Its streak-only model showed a fake 40-pt edge on 2026-09-26; the ladder was efficient once wholesale was included. It expects any real edge in the convergence rate and in weekly/monthly ladders. Its own live account shows NO measured edge (n=55, −1.9 pts).
- **Next:** merge its `data/aaa/aaa_daily.csv` (Jan 2025→) into the warehouse; build an `excess_gap` column and test it against our F formula; reuse its forward-only Brier scoring in edge test #9.

### 2026-11-25 (11:50 PM) · L2 on 11 exact days: EIA weights 0.41¢, fitted regional weights 0.14–0.37¢ (not yet 0.10¢)
- **Did:** Fast all-states archive pass finished (1h): only **9 archived days** exist since Aug for that page (Aug 3, Aug 19, Oct 15–31) + 2 live days = 11 exact days. Re-scored; tested 5 regional (PADD) weights fit on half the days, tested on the other half (non-negative, sum to 1).
- **Learned:** L2.1 (EIA 2024 weights, 0 fitted): median miss **0.41¢**, 2/11 within 0.10¢. Misses drift with time (Aug −0.7 to −1.1¢, Oct +0.2 to +1.0¢, Nov ~0) → fixed weights can't nail it. Fitted regional weights out-of-sample: **0.37¢ / 0.14¢** (two splits) vs EIA 0.66¢ / 0.41¢. Weights stable across splits: East ~0.29, Midwest ~0.29, Gulf ~0.26 (≫ EIA share), Rockies ~0.02, West ~0.15.
- **Next:** add L2.2 (fitted regional weights, walk-forward) to engine_room.py; 1 new exact day/day from the recorder; consider state-level station-count weights.

### 2026-11-25 (9:10 PM) · L2 history: per-state archive throttled → one-page fast path; first August test misses
- **Did:** First `history.yml` run (5h) recovered only ~80 per-state pages for 17 states (Internet Archive throttling). Added `wayback_states.py --all-states`: archived `gasprices.aaa.com/state-gas-price-averages/` = all 51 states per fetch → `research/engine_room/wayback_states/_all_states.csv`. `history.yml` now runs the fast pass by default (slow per-state pass opt-in: input `slow=yes`).
- **Learned:** First archived full day (Aug 3, 2026): L2.1 volume-weighted blend **misses −1.14¢** (plain mean −2.74¢), vs 0.06–0.09¢ on Nov 24–25. Fixed EIA-2024 weights are not the whole story → weights likely vary (season / station mix) or need fitting.
- **Next:** collect ≥15 exact days → fit state weights on half, test on the other half (no peeking); compare fitted vs EIA weights.

### 2026-11-25 (6:20 PM) · Quant-standard edge check: the favorite edge is NOT proven
- **Did:** `tools/edge_check.py`: every 10 AM ET line/side priced 60–97¢ (spread ≤10¢), bought at ask + fee, settled on AAA; returns **clustered by day** + bootstrap CI + monthly split.
- **Learned:** 362 bets / 72 days, 87% win at avg cost 85.7¢. Return per $ **+3.3%, t = 1.41, 95% CI [−1.6%, +7.7%] → includes zero.** By month: Aug +6.6% (7d), Sep −1.0%, Oct −5.3%, Nov +13.1% → it's a November (falling-price) effect, not a structural edge. Matches gas (no edge). Earlier "+6–8%" figures counted lines as independent and mixed in-sample tuning.
- **Re-check (same session):** backfill success 21:30 ✅; recorder shift + relay running ✅. Risk: `truckstops.yml` and the warehouse Internet Archive step only commit at the END of 4–5 h runs (a crash loses the run) → truckstops.py should push hourly like live_recorder.
- **Decided (proposed):** stop treating favorite bias as an edge. The only edge worth testing = information timing: a nowcast of tomorrow's AAA from today's state / truckstop data that beats the crowd's 10 AM miss (~0.3¢) on unseen days.

### 2026-11-25 (6:05 PM) · Cross-chat audit: 3 silent breaks fixed, CLAUDE.md slimmed
- **Fixed:** (1) `backfill.yml` was cancelled 5× in a row (`cancel-in-progress: true` + trigger on any `tools/**` change from any chat); last success 12:52 PM ET. Now it queues instead, and it only triggers on its own scripts. (2) `history.yml` committed `data/kalshi_twins.db` too. With `pull --rebase -X theirs`, the last pusher's copy wins, so a long Internet Archive run could silently roll the DB back. Single-writer rule now (only backfill.yml commits the diesel DB). The run already in progress still uses the old file, and its rollback self-heals on the next daily pull. (3) `warehouse.yml` restarted its 4-h pull on every `warehouse.py` edit → trigger narrowed.
- **CLAUDE.md:** 51 KB → 14 KB. Log moved here (`research/LOG.md`). Added a Jobs table (who writes what, who starts it) + 5 rules. Fixed stale lines ("static, uncomment schedule") and the open-questions statuses.
- **Realness check:** real = data foundation (verified rows, live recorders, truckstops, EIA decades), crowd-sharpness measurements, L2 state blend (2 exact points). Not yet moving the needle: no strategy has passed a holdout; model F (0.59¢) is worse than the 10 AM crowd (~0.3¢); Nautilus runs only a replay; sheet tabs overlap (Custom Build ↔ Wishlist; Connectivity was a one-off). The open needle question = #9: can any bet-time signal beat the 10 AM crowd after fees?

### 2026-11-25 (5:35 PM) · Warehouse roles: diesel main, gas = side test/analog
- **Did:** Catalog + sheet Warehouse tab now has a **role** column: 🎯 Main (diesel) · 🔗 Shared input (Brent, WTI, nat gas) · ⛽ Side test (gas analog: same AAA engine, used to check ideas/inputs, not the main system). Warehouse now also reads the gas archive (`data/gas/archive/{trades,candles_1min}/*.csv.gz`, created by the DB size guard), so gas trades stay complete (221K) after old rows move out of the DB; trades de-duplicated by trade_id. Feed health allows +75 min because live feeds push to GitHub hourly.
- **Decided (Dan):** gas twin = side test / analog that informs which diesel inputs to track; diesel stays the main system.

### 2026-11-25 (5:25 PM) · Warehouse wired to all live feeds + feed health + audit
- **Did:** New warehouse views `truckstop_diesel`, `truckstop_state`, `l3_state_compare` (truckstop vs AAA state), `aaa_flips`, `ho_at_10am` (last live HO ≤10:10 ET, no peeking), `feed_health` (OK/STALE per recorder). Catalog writes `data/feed_health.csv`. `sheet_payload.py` now also emits the **Warehouse** tab blocks (catalog A4:G53, feed health A56:E70). IMPORTDATA removed per mobile-first rule. Started the truckstop loop by hand (it only restarts at shift change). Audit table in `research/2026-11-25_warehouse.md`.
- **Learned:** No duplicate feeds that matter. Dead: HO-at-10-AM step in `daily_recorders.py` (never got data) → use `ho_at_10am`. Minor duplicates: AAA state pages scraped twice (diesel + gas jobs). Love's truck diesel ≈ −7¢ vs AAA state, TA auto diesel ≈ +3¢ → use changes, not levels. Gas DB already holds 221K trades + 2023+ hourly ladder.
- **Next:** after a few days of truckstops: L3.1 = does a state's truckstop change on day X−1 predict its AAA state change on day X.

### 2026-11-25 (5:10 PM) · Warehouse layer + free long history (EIA) + Wishlist tab
- **Did:** `tools/warehouse.py`: DuckDB views over all sources, both products, with `era` = history / since_live (go-live 19:21 UTC). `tools/history_pull.py` + `warehouse.yml` (relay runs it daily): EIA 17 series, Yahoo intraday (monthly files, merge-forward), Internet Archive AAA **national** snapshots since 2019 (resumable). Sheet: **Warehouse** tab (IMPORTDATA of the catalog) and **Wishlist** tab (W1–W17).
- **Learned:** EIA reachable from GitHub (FRED isn't). Spot ULSD 2006+, Brent/WTI 1986+, HO settles 1980–Apr 2024, weekly retail diesel by PADD 1994+. Yahoo intraday blocked from GitHub (all fail). AAA Monday vs EIA weekly diesel gap: ~0–4¢ in Oct → +12.3¢ on 11/23.
- **Next:** read the Internet Archive national run → years of L1 history (diesel before Aug 2026); point Engine Room + Nautilus loaders at warehouse views; HO intraday history = Wishlist W1 (Databento credits) unless a free source opens.

### 2026-11-25 (4:50 PM) · Gas twin filled + DB size guard
- **Did:** First gas pull finished (after fixing `cancel-in-progress` killing it). Gas workbook filled: 60 Day (Sep 27 – Nov 25), Testing (37 tests), Bricks (B1–B12 re-tested + gas-only B13/B14), Connectivity raw values (control day Nov 23 / KXAAAGASD-26NOV24), Strategies column L. `kalshi_trades.py` size guard: when a DB passes 70 MB, trades + 1-min candles older than `trades_keep_days` (gas 30) move to `data/<product>/archive/{trades,candles_1min}/YYYY-MM-DD.csv.gz`, then VACUUM (gas 92 MB → ~38 MB in a dry run). Gas workflow now pulls trade tape for 30 events.
- **Learned:** Gas history = 270 events (11 days Sep–Oct 2023, 1 in 2024, then daily from Mar 26 2026). Gas is ~13× busier than diesel (221K trades / 60 days). **Diesel favorite edge does NOT exist in gas:** baseline −2.5 (60d) / −6.4 (unseen Aug 4–Sep 26) / −2.4 (Apr–Sep). Holds in gas: avoid cheap YES favorites ≤83.5¢ (−30 / −24 / −18, B14); YES always worse than NO. Mixed: weekend (−4.6 / +4.3 / +5.7), big favorites after a down day (+5.9 / +9.3 / +0.1, B13). Reading: the diesel edge is probably a thin-market edge → watch it shrink as diesel volume grows.
- **Next:** fit gas model F; re-cut B3 at gas-sized volumes; check B14 rule on diesel.

### 2026-11-25 (4:45 PM) · L3 truckstops live (Love's) + Wayback L2 history + sheet auto-feed
- **Did:** `tools/probe_sources.py` (+`probe.yml`) found Love's feeds: `GET /api/fetch_stores` (734 stores, no prices) and `POST /api/search_stores` body `{"lat","lng","radius":300}` → stores WITH `fuelPrices` (cashPrice, fuelType, productName). `tools/truckstops.py` searches a ~150-mile grid of store points (151 cells) → `data/live/truckstops/YYYY-MM-DD.csv`; `truckstops.yml` runs hourly for ~5.5h, started by the relay each shift. TA/Petro added: `GET /api/locations/coordinates/?lat=&lon=` returns an HTML panel of sites within 100 mi with fuel prices (first pull 120 sites, 110 diesel). Pilot (SvelteKit + Contentstack): no open price feed found (`/api/*` and `__data.json` return the page shell). `tools/wayback_states.py` (+`history.yml`, resumable) recovers archived `gasprices.aaa.com/?state=XX` pages since Aug 2026 → `research/engine_room/wayback_states/<ST>.csv` (diesel + regular in one pass); Engine Room L2 now reads them (exact = current/yesterday columns; needs all 51 states for an exact point, 48–50 scored separately with re-scaled weights). Exports `engine_room_l2_points.csv`; sheet Engine Room tab scorecard + points are written by Claude via `tools/sheet_payload.py` + Sheets connector (IMPORTDATA dropped: needs a desktop "Allow access" click).
- **Learned:** First Love's pull: 624 stores with prices, 1,112 diesel rows (types: "Auto Diesel", "Diesel", "Bio-Diesel B20"), 42 states. Love's posted diesel runs ~9–11¢ under AAA state averages (cash posted vs AAA mix) → test CHANGES not levels. Wayback CDX: ~100–200 archived days per state in 2026 (some states returned 0 = CDX throttling, retry).
- **Next:** read wayback job → L2.1 on ~100 days; after ~10 days of Love's: does Love's day X−1 move predict AAA day X state move (L3.1)?

### 2026-11-25 (4:20 PM) · Engine Room v0 — L2 state blend nearly exact, L0 bell curve not enough
- **Did:** `tools/engine_room.py` (product-aware, runs in both daily workflows). L2.1 = national AAA as states weighted by EIA 2024 transportation fuel use (diesel: distillate, gas: motor gasoline; weights in `research/engine_room/`), zero fitted numbers. L2.0 plain mean baseline. L0.1 = normal-curve ladder fit per hourly snapshot; L0.2 = log of every ≥0.3¢ hourly move in crowd centre (marked UNEXPLAINED until intraday inputs exist). Gas state regular prices now saved daily to `research/engine_room/aaa_states_gas/*.csv` (CSV, not the gas DB, so two workflows never fight over one binary). Sheet tab **Engine Room** in both workbooks.
- **Learned:** L2.1 misses **0.09¢ (Nov 24) and 0.06¢ (Nov 25)** vs plain mean 3.7¢ → national ≈ fuel-volume-weighted states. Only 2 exact points → "promising", pass needs 20. Week/month/year-ago points miss 0.2–1.0¢ (fuzzy dates, 2024 weights). L0.1 median line miss 2.09¢ (48% ≤2¢) → ladder has fatter tails/lean than a bell curve. L0.2: 184 moves; peaks noon–1 PM and 6 PM ET.
- **Decided (Dan):** prove the algo stack before patterns. Order: L2 → L1 → L3 truckstops → L0 explained.
- **Next:** L2 exact points accrue daily (pass ≈ mid-Dec); L0.1 v2 fat-tailed curve + spread layer; L0.2 match moves to live HO futures; L3 truckstop recorder (Love's/Pilot terms check, CB10).

### 2026-11-25 (3:55 PM) · Live recorder verified (4 feeds) + relay fix
- **Did:** `tools/live_recorder.py` + `live_recorder.yml`. Snapshot loop per shift: Kalshi strikes, diesel + gas (5 min, incl. top-of-book sizes); order book for the 6 most-traded live diesel lines (15 min); AAA national diesel + regular gas (15 min), with `data/live/aaa_flips.csv` on change; futures quotes (5 min). If columns change, the recorder starts a new `_v2` file. Fixed the relay: dispatch by **numeric workflow ID**, because `gh workflow run <file>` looks the file up on `main` and 404s. Notes in `research/2026-11-25_live-recorders.md`. Sheet: Inputs Map **column N** maps each row to its file/column; Custom Build CB3/CB4/CB5 set to ✅.
- **Learned:** Works from GitHub: Kalshi public API, AAA homepage (5.7645 as of 11/25), **TradingView scanner** (`delayed_streaming_600` = ~10 min delay). Blocked from GitHub: Yahoo (429), Stooq (timeout). Order book fields are `yes_dollars`/`no_dollars` with fractional contract counts. Kalshi sends `volume_fp`=0.00 on quiet lines (treat 0 as real, not missing).
- **Next:** After ~1 week, read `aaa_flips.csv` (earliest knowable time) and use 5-min crowd μ/σ vs futures to explain the noon move; take forward `ho_10am` from live futures (last row ≤ 10:10 ET).

### 2026-11-25 (3:40 PM) · NautilusTrader in the system + Strategies tab + DIY relay
- **Did:** `nautilus/` skeleton on NautilusTrader **2.0.0rc9** (only line with the official Kalshi adapter; stable 1.231 has none). Bridge: KXDIESELD strikes → `BinaryOption` `<ticker>.KALSHI`; `kalshi_trades` → TradeTick; 1-min candles → QuoteTick; live recorder CSVs → QuoteTick with real top-of-book sizes. Kalshi quadratic fee model plugged into the sim venue. Strategy registry (S00 replay check only — Dan: no strategy wiring yet). Locked Kalshi DEMO node (`live_demo_node.py`, 3 locks, refuses GitHub). `nautilus.yml` (replay + fee check + demo config check → `nautilus/reports/`). Relay step in `live_recorder.yml`. Sheet: new **Strategies** tab (S00–S12 + rejected X1–X2, gate dropdown) + Custom Build **CB20** (Nautilus) / **CB21** (relay).
- **Learned:** All 115 events replay 1:1 (29,159 trades + 54,253 quotes). Fee meter = Kalshi to the cent (10 @ 90¢ → $0.07). Kalshi now trades **fractional contracts** (0.01; 12.6K of 29.5K trades) → size precision 2. Adapter: limit orders only, risk engine must be bypassed, no auto-reconnect, no historical books/quotes, backtest can't open net-short NO. **Daily backfill `schedule:` never fired** (non-default branch) — relay now covers it.
- **Decided (Dan):** engine locked at 2.0 rc; stay public for now (private later; relay minutes are free only while public); GitHub only until the server (CB1).
- **Next:** first real strategy = S01 baseline in Nautilus, after adding (1) $1/$0 settlement at AAA, (2) NO-side mirror instrument. Then demo keys → GitHub Secrets and paper trade on CB1.

### 2026-11-25 (3:45 PM) · Gas twin cloned (own DB + workbook)
- **Did:** `tools/product.py` = product switch (env `KT_PRODUCT=gas`; default diesel). build_db / backfill / backfill_history / panel / testing / kalshi_trades all read DB path, exports folder, series, wholesale symbol, tax, delivery "normal", model coefficients from it. Gas = `data/gas/kalshi_gas.db` + `data/gas/exports/` (never mixes with diesel; same table names — in gas DB `aaa_diesel` = AAA regular gas, `ulsd_nyh_usd_gal` = RBOB RB=F; view `gas_daily` has readable names). Series KXAAAGASD + old AAAGASD. Tax 51.67¢ (EIA Jan 2026: 18.40 fed + 33.27 state). Delivery normal = trailing 90-day median (point-in-time). Model F blank until re-fit. Candles: last 20 h before close. New workflow `.github/workflows/gas_backfill.yml` (daily 11:47 UTC, saves progress mid-run). Diesel workflow now installs scikit-learn (computer slices were silently failing there). New workbook **"Kalshi Gas – Inputs Map"** (copy of diesel, text swapped to gas, gas-only inputs added #84–86, data tabs cleared pending first pull).
- **Risk noted:** federal gas-tax holiday proposed in 2026 but not enacted (CRS, Oct 2026); some states (IN, GA) suspended their own — breaks the fixed tax slice on those days.
- **Next:** first gas pull → fill gas 60 Day / Testing / Bricks; pick gas unseen window; fit gas model F.

### 2026-11-25 (3:00 PM) · Bricks hopper + unseen-days check
- **Did:** Sheet tab **Bricks** (Stage dropdown: 🤖 AI screened → ⭐ Selected → ✅ Vetted, + ❌ Rejected). 12 candidates B1–B12, all "AI screened", each with 60-day result, unseen-days result, holds-up verdict, mechanism, risks, next check, mind-map link. `testing.py` now takes a date window (`testing.py 0 START END` → `testing_results_unseen`); unseen window Aug 3 – Sep 25 (54 days, mostly rising) added to workflow.
- **Learned:** Holds on unseen days: favorite bias (B1 +7.8 / +8.1), 70–90¢ sweet spot (+10.4 / +16.1), liquid lines ≥500 contracts (+9.2 / +12.3), fat delivery slice (+10.4 / +16.1, small n). Mostly holds: weekend, tight spread. Fails: No-beats-Yes (flips), model-agrees (not on unseen). Can't test: falling regime (no falling days in Aug–Sep).
- **Decided:** More diesel days don't exist before Aug 3. Next sample boost = gas daily twin (same AAA source, history from 2023) for structural bricks + extra intraday snapshots.

### 2026-11-25 (2:45 PM) · 60-day audit: two data fixes, story check
- **Fixed:** (1) Daylight saving: stored `end_et` is fixed UTC−5, so Sep–Oct "10 AM" snapshots were really 11 AM EDT. panel.py + testing.py now cut snapshots with real America/New_York time (end_ts). (2) Stale books: lines with no two-sided quote (spread > 10¢) showed a fake 50% mid and broke the crowd forecast/σ fit (19 mornings had σ stuck at 1.8¢). Forecast + σ now use only lines with spread ≤ 10¢; mornings with none stay blank (8 of 60). Sheet tabs 60 Day + Testing refreshed. ⚠️ story.py / signal_scan.py still use end_et strings (legacy, not in sheet).
- **Checks passed:** AAA continuity day to day, AAA change math, every pair/Goldilocks WIN-LOSS label vs settled AAA, delivery slice math.
- **Learned (60 days):** baseline edge now +6.6% (90.8% win, 142 line bets); Oct −2.3% vs Nov +12.0%; NO side +12.7% vs YES +1.0%; model agrees +10.3% vs disagrees −0.2%. Crowd 10 AM median miss 0.28¢ (Nov 0.16¢), close 0.17¢; model F 0.59¢. All 3 Goldilocks losses in mid/late Oct (choppy, delivery slice below $0.90).
- **Next:** Bricks tab; re-check candidates on unseen Aug 3 – Sep 25.

### 2026-11-25 (1:10 PM) · Daily schedule ON + Custom Build tab + trade tape
- **Did:** Turned on the daily GitHub schedule (6:17 AM ET, Dan's request). Added Stooq fallback for HO 5-min (`daily_recorders.py`). New `tools/kalshi_trades.py` (CB6 + CB7): every trade per traded line → `kalshi_trades`; 1-min candles for top-3 lines per event → `kalshi_candles` period_min=1 (panel/testing/story all filter period_min=60). New sheet tab **Custom Build**: 19 items (CB1–CB19) needing more than a daily GitHub job, each with time horizon, where it runs, build scope, cost, blocker.
- **Decided:** GitHub = all once-a-day + backfillable jobs. Always-on server (CB1, ~$5–6/mo) = home for every ⚡ realtime item; pending Dan's OK. Databento ($125 free credits) = proposed one-time HO 10 AM backfill (CB2), pending Dan's signup.
- **Next:** read first trade-tape run; EIA API key (CB13); Dan decisions on CB1 / CB2 / CB10.

### 2026-11-25 (12:40 PM) · Testing framework v0 (sheet tab "Testing")
- **Did:** `tools/testing.py` → `testing_results` + `data/exports/testing_results.csv` (37 tests on the 60-day window). Two units: DAY (one Goldilocks 75–85¢ favorite/day, 26 bets) and LINE (every line/side 60–97¢ at 10 AM passing the liquidity filter, 162 bets). Layer 1 = standard checks (favorite win/lose, baseline, calibration, monthly stability, costs/streaks, holdout rule); Layer 2 = one condition; Layer 3 = two. Origin column: Core (obvious) vs Computer (depth-2 decision tree, min 15 per leaf). "What sticks out" = top-3 standardized win-vs-loss gaps inside the slice (needs ≥3 losses). Recorder result: AAA 51 states saved ✅; Yahoo 5-min HO still 429 ❌.
- **Learned (60 days, hints only):** baseline edge +4.3% (89.5% win at 84.3¢). Oct negative (−4.8%), Nov +10.4%. NO side +7.8% vs YES ≈ 0. Losses sit closer to the crowd forecast (0.58σ vs 1.15σ) and are cheaper (75¢ vs 85¢). Tree: lines ≤82.5¢ with refining slice >$2.04 → 60% win, −19% per $100.
- **Next:** Bricks tab linked to Test IDs; widen to 114 days + close snapshot; apply holdout.

### 2026-11-25 (11:30 AM) · 60-day panel + daily recorders + top-3 liquidity rule
- **Did:** `tools/panel.py` → table `panel_daily` + `data/exports/panel_daily.csv` (one row per event day, 91 point-in-time columns: calendar, AAA trend/regime, HO/Brent last-known closes, price slices, model F no-peek, Kalshi 10 AM + close: crowd forecast, σ, Goldilocks bet, top-3 liquid Yes/No pairs, misses). Sheet tab "60 Day" mirrors the last 60 rows. `tools/daily_recorders.py` (AAA 51-state snapshot → `aaa_state_daily`; HO 10 AM from Yahoo 5-min → `research/connectivity/ho_10am.json`), both fail-soft, added to backfill workflow (still static: runs on push / by hand; daily schedule NOT turned on — Dan's call).
- **Decided:** Formula #19 "Top-3 liquid pairs": line tradeable if traded since open, spread ≤10¢, 3–97%; rank by volume since open; keep 3. Inputs needing a live realtime system marked ⚡ in the sheet; forward-only daily recorders marked 📼.
- **Learned:** Last 60 days: crowd 10 AM median miss 0.34¢, close 0.13¢, model F (no peek) 0.59¢. 10 AM has no tradeable line on 10/60 days; at close usually only 1 line is between 3–97%.
- **Next:** Bricks tab (hypothesis cards) on top of panel_daily.

### 2026-11-25 (3:50 AM) · Connectivity tier 2 + back-solved state weights
- **Did:** `tools/connectivity_pull.py` + `.github/workflows/connectivity.yml` (one-shot; excluded from backfill trigger). Raw output: `research/connectivity/tier2_pull*.json`. Filled tier-2 rows in the sheet's Connectivity tab.
- **Learned:**
  - AAA state pages (`gasprices.aaa.com/?state=XX`) work from GitHub: table 0 = state (current / yesterday / week / month / year ago); ~27 metro tables follow. Nov 24 plain state mean $5.8372 vs national $5.7982.
  - Back-solve: 5 regions (PADD) × 5 AAA snapshots → weights East 24.8% / Midwest 48.2% / Gulf 7.9% / Rockies 6.2% / West 12.9%. Leave-one-out miss 0.2¢ on recent days (vs 3.9¢ plain mean), 2.9¢ year-ago. Fragile (5 pts / 5 unknowns) → mini-AAA v0.
  - Yahoo 5-min bars return 429 from GitHub runners → HO live (#35) not connected.
  - Truckstops: no free history. Love's prices load from apiservices.loves.com; Pilot via Contentstack; TA none seen. ToS check pending.
  - Control day regime: 27 straight AAA down days; 10-day −24.6¢.
- **Next:** daily AAA state snapshot on schedule (builds history for weights); HO intraday fallback source; Love's API mapping + ToS.

### 2026-11-25 (3:30 AM) · Inputs Map priorities + Connectivity tab (Google Sheet)
- **Did:** Google Sheet "Kalshi Diesel – Inputs Map" (Dan's Drive): 83 inputs in 10 sections, each scored Priority 1–4 (13 essential / 12 test-first / 32 later / 26 parked); Formulas tab (18). New **Connectivity** tab: tier-1 inputs with the raw value for control day Mon 2026-11-23 (event KXDIESELD-26NOV24, 10 AM ET snapshot) + exact source + pipe.
- **Learned:** 10 of 13 tier-1 inputs already flow through GitHub; 3 are Claude one-time (fee rule, σ fit, model F). Control day: AAA $5.8182 → $5.7982; crowd 10 AM $5.7996 (σ 0.37¢); model F $5.7897 (miss 0.85¢). ⚠️ F uses HO full-day close = look-ahead at 10 AM.
- **Next:** wire σ + model F into story.py; store can_close_early; then tier 2 on the same control day.

### 2026-11-25 (3:00 AM) · Archive pull (Aug 3 – Sep 17) breaks the 75–85¢ rule
- **Did:** Workflow ran `backfill_history.py KXDIESELD`: 114 settled days (2026-08-03 → 11-24), 2,548 markets, 29K hourly candles. Fixed: numpy install in workflow; archived AAA values now copied into `diesel_daily`.
- **Learned:**
  - On never-seen days (Aug 3 – Sep 17): 75–85¢ favorites 80.8% win, ROI +0.9% (26 bets); one-per-day 7/11 wins, ROI −21%; 85–97¢ ROI −7.6%. Weekend 75–85¢ still 5/5.
  - All 114 days: 75–85¢ 87.2% win, ROI +8.1%; one-per-day +2.0%; weekend 22/22 (+23%, 13 days).
  - Regime: Aug 3 – Sep 17 AAA rose 5.36 → 6.50 (32 up / 13 down days, "rockets"); Sep 18+ fell (17 up / 51 down, "feathers"). Favorites worked in the slow fall, not the fast rise.
  - Yesterday's AAA direction alone does NOT separate (75–85¢: fell +8.1% vs rose +8.3%) → regime is multi-week, not 1-day.
  - Correction to handoff brief: market opens 8 AM ET day before (not 10 PM).
- **Decided:** 75–85¢ rule = regime-dependent, not standalone. Need a regime detector (multi-day trend / wholesale direction) + weekend effect check.
- **Next:** Regime test (5–10 day AAA trend, HO trend) + weekend mechanism; AAA flip-time tracker.

### 2026-11-25 (2:30 AM) · Signal scan: when do favorites win ~90%?
- **Did:** `tools/signal_scan.py` — every line/side priced 60–97¢ at 10 AM (258 bets, 55 days), bucketed by bet-time features; walk-forward model agreement (fit only on earlier days).
- **Learned:**
  - Price buckets: 60–75¢ win 73% (ROI +5%) · **75–85¢ win 90% (ROI +11.8%)** · 85–97¢ win 97% (ROI +3.8%). Sweet spot = 75–85¢: ~90% wins while paying ~80¢.
  - 75–85¢ filters: weekend bet day 17/17 wins (+22%, small n); line ≥1σ from crowd 93% (+14%); model agrees 91% (+13%); one bet/day 36 bets → 32 wins, +9%.
  - Our AAA model barely separates winners (agree 90.8% vs disagree 86.7%) → not a strong signal yet.
  - "Wins 90%+" alone ≠ profit: 85–97¢ wins 97% but ROI only +3.8%. What matters = win rate minus price.
  - Line timing: all 21 strikes open together at 8 AM ET the day before and never change; odds move continuously until 11:59 PM close; no midday freeze. AAA itself posts once per morning. Market can close early if AAA data releases.
- **Decided:** Candidate rule to test on more days: favorites priced 75–85¢ at 10 AM, one per day; extra filters (weekend, ≥1σ, model agrees) = hints only.
- **Next:** Validate 75–85¢ rule on archived diesel days (Aug 3 – Sep 17) not yet in the DB.

### 2026-11-25 (2:15 AM) · Diesel rulebook = ECONSTAT; research framework
- **Learned:** KXDIESELD official terms ARE ECONSTAT.pdf (series contract_terms_url). AAA = Source Agency, Trading Economics backup, first release only, early close if data released, 30-min settlement timer. MNPI prohibition applies — paid OPIS feeds that are AAA's own inputs need a compliance check.
- **Decided (framework):** Replace "dozens of side-by-side Excels" with one master panel (event × snapshot time, point-in-time inputs) → deltas open→close → attribution → hypothesis → walk-forward backtest → demo.
- **Next:** Build the master panel (#10) once Dan confirms snapshot times.

### 2026-11-25 (2:00 AM) · Paused favorite topic; read ECONSTAT terms
- **Did:** Cancelled full-history backfill run (Dan's request). Removed `backfill_history.py` + `favorite_test.py` from the workflow (scripts kept in `tools/` for later). Read Kalshi ECONSTAT contract terms.
- **Learned:** Kalshi diesel daily archive goes back to 2026-08-03 (114 events); AAA gas daily/weekly back to Sep/Oct 2023 (old tickers AAAGASD/AAAGASW). Archived markets live at `/historical/markets`. Kalshi-wide study (Bürgi/Deng/Whelan, 300K contracts): favorite-longshot bias is market-wide, shrinking, makers out-earn takers.
  - ECONSTAT terms (generic economic stats, not AAA): first non-preliminary release counts; later revisions ignored; expiration 10:00 AM ET; last trade 1 min before scheduled release; Trading Economics is backup source; Kalshi can set payouts if value can't be determined.
- **Decided:** Favorite edge = not a focus. Back to formulas.
- **Next:** Find the AAA-specific diesel contract terms (likely a separate PDF on assets.kalshi.com/contract_terms/).

### 2026-11-25 (1:00 AM) · Risk threshold formula + driver-chain approach
- **Did:** Built `tools/risk_calc.py` + interactive calculator; notes `research/2026-11-25_risk-threshold.md`.
- **Learned:** $400 over 30 real favorite bets (avg cost 75.8¢): +$128 with 0 losses, +$75 with 3, break-even ≈7 losses, −$48 with 10. Each loss needs ~3–4 wins to erase. At 79% win rate: ~28–30% chance of finishing negative; Monte Carlo median +$21.
- **Decided (approach):** Build a driver chain, each link with a measured pass-through rate: news/sources → wholesale & rack → truckstop prices → AAA → Kalshi crowd. Prove each rate across all diesel days; keep only drivers that hold up.
- **Next:** Link test #1: wholesale (HO) move → next-day AAA move (lags 0–5 days, up vs down) → crowd reaction speed.

### 2026-11-25 (12:50 AM) · Clarified: AAA does not move intraday
- **Learned:** AAA posts once per day (morning), so between a 10 AM bet and close the AAA number is constant; only the crowd's guess of TOMORROW's AAA moves. Example event 2026-11-24 (bet day 11/23): AAA known 5.8182 all day; crowd forecast 10 AM 5.7996 → close 5.7977; actual 5.7982 (−2.00¢). Line "above 5.800": 47% (10 AM) → 28% (noon) → 32.5% (4 PM) → 7.5% (11 PM) → settled NO. Wholesale HO fell 22.4¢ that day.
- **Shared by N and F:** AAA today (anchor), squeeze/delivery slice, oil (HO, Brent), taxes, station/rack prices (unseen). N-only: crowd wiggle, bias, spread, fee, market makers. F-only: payout rule, OPIS method.

### 2026-11-25 (12:40 AM) · AAA formula teardown + backtest
- **Did:** Researched AAA/OPIS method; pulled 51 state diesel averages; backtested F formula in/out of sample (`tools/aaa_backtest.py`). Notes: `research/2026-11-25_aaa-formula.md`.
- **Learned:**
  - AAA = OPIS, fleet-card swipes (WEX) + direct feeds, up to ~120–130K stations, previous day's transactions.
  - National ≠ simple mean of states: mean $5.8350 vs national $5.7982 (−3.7¢) → hidden state weights.
  - F formula: median miss 0.56¢ in-sample, 0.64¢ out-of-sample; right half-cent bin ~25%. Beats "no change" (1.46¢) but loses to crowd at 10 AM (0.34¢) and close (0.11¢). Coefficients unstable.
- **Decided:** Fundamentals formula = trend anchor only. Precision must come from sub-formulas: state weights, timing window, margin dynamics, regional basis.
- **Next:** Start collecting AAA state averages daily (add to backfill) to solve national weights; then truckstop chain prices.

### 2026-11-25 (12:20 AM) · Component map: known vs unknown, N vs F
- **Did:** Laid both formulas out as one line each (green = clear source, amber = measured but cause unclear, red = unknown). Built the 24-row item table → `research/2026-11-25_component-map.md`.
- **Learned:** F is fully external (Kalshi reads AAA/OPIS). N = crowd belief (external data) + Kalshi's published fee/order-book mechanics. Unknowns cluster in OPIS methodology, intraday rack/station prices, private market-maker models.
- **Next:** Solve red rows in order: #15 truckstop prices → #14 rack proxy → #21 daily rulebook → #18–20 OPIS method.

### 2026-11-25 (12:10 AM) · Formulas plugged in live (Nov 25 market) — fundamentals beat momentum
- **Did:** Pulled hourly candles for KXDIESELD-26NOV25 lines 5.760 / 5.765 / 5.770; fit crowd center μ and wiggle σ (normal curve) at 10 AM, noon, 11 PM; plugged today's inputs into both formulas.
- **Learned:**
  - **F (agreed draft):** AAA_tmrw = AAA_today − 6.72%×(Delivery − $0.90) + 1.83¢/$ HO bet-day move − 1.30¢/$ HO prior-5d move + station surprise(?). Nov 25: 5.7982 −4.02¢ +0.46¢ −0.00¢ = **5.7626**.
  - **N:** chance(AAA > K) with center μ = F, σ 0.24¢ (10 AM) → 0.18¢ (noon) → 0.14¢ (11 PM), + bias + spread + fee.
  - Crowd center: 10 AM 5.7636 → noon 5.7619 → 11 PM 5.7625 ≈ model 5.7626. Momentum-only model said 5.7804 (wrong) → momentum fails after big wholesale drops; fundamentals version is the base formula.
  - Model vs crowd at 10 AM: >5.760 86% vs 93.5%; >5.765 16% vs 28%; >5.770 0.1% vs 2.5%. At 11 PM nearly identical (96.8/4.3/0 vs 96.5/3.5/1).
  - Mystery: at noon the 5.765 line fell 28% → 4.5% with no futures move (HO −0.2¢). Timing matches OPIS 11 AM rack snapshot (hypothesis).
- **Open ?s:** (1) what caused the noon move; (2) why σ shrinks 8–11 PM; (3) OPIS window/weighting; (4) HO futures ≠ rack prices; (5) market-maker models private; (6) only 67 days of fit.
- **Next:** Add model_F / model_N columns to `daily_story` on Dan's OK; test noon-move ↔ rack/station prices.

### 2026-11-24 (11:55 PM) · Formula reconstruction: N vs F + shared components
- **Did:** Searched for published models (Kalshi, CFTC filings, OPIS methodology, academic pass-through). Reconstructed N and F from data. Added `v_win_loss` view + `win_loss.csv`. Wrote `research/2026-11-24_formula-reconstruction.md` (component map + flags).
- **Learned:**
  - Kalshi publishes no pricing model; prices = order book (makers × takers) incl. designated market makers. Settlement rule = "Diesel Price on <date> above $K" (AAA). Old weekly diesel contract used EIA as Source Agency.
  - OPIS diesel = 9,000+ truckstops via fuel cards (Comdata, TCH) + chain feeds; files at 7:30 AM. Collection window, weighting, national roll-up NOT published.
  - Crowd 10 AM forecast ≈ AAA + 0.89×yesterday's move (R² 0.69); truth ≈ 0.73× (R² 0.66); crowd at close ≈ 0.77×. Morning crowd over-extrapolates momentum.
  - Median miss: "same as yesterday" 0.63¢ · crowd 10 AM 0.35¢ · crowd close 0.11¢.
- **Decided:** Proposed formulas pending Dan's sign-off before adding model columns to `daily_story`.
- **Next:** (a) Dan approves formulas → add model_N / model_F columns per day. (b) Research free truckstop chain prices (Pilot/Love's/TA) as the missing intraday input. (c) Find daily KXDIESELD CFTC filing.

### 2026-11-24 (11:40 PM) · N → F → Z framework + why AAA moves
- **Did:** Built `tools/story.py` → `daily_story` table (one row per day). Fit AAA daily change on fundamentals; compared winning vs losing favorite bets. Added story.py to the GitHub workflow.
- **Learned:**
  - AAA engine: ΔAAA ≈ 6.06¢ − 6.72¢×Delivery slice + 1.83¢×HO bet-day move (R² 0.65). Delivery $1.50 → ~−4¢/day; falling stops near ~$0.90 slice.
  - Market's 10 AM forecast already includes these fundamentals (miss vs fundamentals R² 0.05).
  - Losing days = bigger morning miss (0.80¢ vs 0.29¢) and bigger intraday forecast move (0.73¢ vs 0.31¢). Futures explain ~2% of the intraday move.
  - AAA's data = OPIS station prices (~5M prices/day, up to 150K stations); OPIS rack snapshots at 11 AM / 2 PM.
  - Strike distance from forecast did not separate wins from losses (median 0.33¢ vs 0.32¢).
- **Decided:** Fundamentals = table stakes, not the edge. Edge hunt = find a bet-time signal that predicts the intraday info gap (station-level retail prices first).
- **Next:** Test GasBuddy/crowd diesel prices and AAA state averages as leading indicators of F.

### 2026-11-24 (11:15 PM) · Bankroll sims: $500, $100 favorite bet per day
- **Did:** `tools/sim_favorites.py` → results in `research/sims/2026-11-24_favorites_sim.json`. Buy at hourly ask +1¢ slippage + taker fee (rounded up per order). Favorites = lines priced 60–85¢.
- **Learned:**
  - Sim A fixed rule (~75¢ favorite at 10 AM): 65 days, 51 wins / 14 losses, $500 → $615. Fees $107. Dipped to $56 on Nov 2 before recovering.
  - Sim A random picks ×1,000: median $799, 10th pct $0 (bust), 90th pct $1,254; lost money in 34% of runs.
  - Sim B (30 wins, 0 losses, $100/bet @ ~76¢): +$857 (~$28.55/win).
  - Win/loss math per $100: @65¢ +$50/−$100 (need 66.6%), @75¢ +$31/−$99 (76.3%), @85¢ +$16/−$99 (85.9%), @95¢ +$5/−$98 (95.3%).
  - No minimum bankroll: fees are a % (~1.5–1.8% of stake). Size only adds slippage.
- **Decided:** Win RATE vs break-even is what matters, not bankroll size. Strategy = bet fewer days (skip risky ones) to lift win rate above break-even.
- **Next:** Edge test (#9): which features (oil move, delivery slice, time of day) predict losing days?

### 2026-11-24 (11 PM) · Stress test: "always bet the favorite"
- **Did:** Split favorite backtest into Sep–Oct vs Nov, added +1¢ worse fills, computed break-even win rates.
- **Learned:**
  - Favorite 60–85¢: Sep–Oct 75% win, ROI +1.5% · Nov 87% win, ROI +18.5%. Heavy fav 85–97¢: Sep–Oct 94%, +3.3% · Nov 98%, +7.1%.
  - With 1¢ worse fills: 60–85¢ → +4.3%, 85–97¢ → +3.4%. Worst single days ≈ −1.6 to −1.8 units.
  - Break-even: at 90¢ need 90.6% wins (1 loss ≈ 10 wins); at 95¢ need 95.3% (1 loss ≈ 20 wins).
  - Most of the profit came from November's steady price slide; in Sep–Oct favorites barely beat break-even.
- **Decided:** "Always favorite" = baseline strategy to beat, not the strategy. Engine's job: skip favorites on risky days (e.g. wholesale jump / trend turn).
- **Next:** Edge test (#9) with the favorite baseline as the benchmark.

### 2026-11-24 (late night) · Liquidity filter, underdog test, $100 vs $1,000
- **Did:** Backtested every price level on all 68 settled days (hourly candles, books with spread ≤10¢, one bet per line/side/day, buying at ask + taker fee). Read tonight's live order book (KXDIESELD-26NOV25-T5.765).
- **Learned:**
  - Prices = other traders' orders (peer-to-peer order book). Kalshi does not set the odds.
  - Liquidity: 21 strikes/day; 431 of 1,448 settled markets (30%) never traded; top 3 strikes = 63% of a day's volume.
  - Calibration (favorite-longshot bias): lines priced 10–20% won 4%; 20–30% won 9%; 30–40% won 27%; 60–70% won 78%; 70–80% won 84%. Cheap side is overpriced, favorites underpriced.
  - Blind strategies: underdog ≥4x (2–25¢): 1,143 bets, 19 wins (2%), ROI −75%, up on 4/67 days. Middle 25–50¢: ROI −26%. Favorite 60–85¢: 78% win, ROI +6%, up 43/65 days. Heavy favorite 85–97¢: 95% win, ROI +4%, up 50/64 days.
  - Last hour before close, ≥4x underdogs hit 2 of 480 chances (2 days).
  - Order book depth (10:47 PM): YES at 4¢ ≈ 1,000 contracts, at 5¢ ≈ 3,000; NO at 97¢ ≈ 3,000 contracts. $100 fills at one price; $1,000 can walk 1–2 cents on the cheap side (slippage).
- **Decided:** Liquidity filter for the bot = drop strikes with zero volume, spread >10¢, or priced <3% / >97%. Underdog-only strategy rejected unless our model finds specific mispriced days. Sample is small (68 days, falling-price regime) — treat ROI numbers as hints, not proof.
- **Next:** Edge test (#9) — model probability vs market per bin; check if favorites' +4–6% survives costs and a longer history. Minute candles (#8) for 30-min-before-close questions.

### 2026-11-24 (night) · How Kalshi prices the diesel ladder + intraday history
- **Did:** Decoded payouts from Dan's screenshots. Added `kalshi_candles` (hourly bid/ask/volume for all 1,469 markets, 18,094 rows) + `v_event_hourly`. Measured how fast the market finds the answer.
- **Learned:**
  - Payout = $1 ÷ (price + fee), fee = 0.07·P·(1−P). Checks: 5.760 YES @97¢ → 1.03x; NO @4¢ → 23.43x; 5.765 NO @90¢ → 1.10x. All match app.
  - Nov 25 ladder at 10 PM: P(>5.760)=96–97%, P(>5.765)=8–9% → ~87% on the 5.760–5.765 bin (forecast ≈ 5.76, i.e. −3.5¢ vs today).
  - Market sharpens through the day: favorite half-cent bin right 26/68 days at ~12h before close vs 42/68 at ~1h. Median forecast miss 0.34¢ (12–15h out) → 0.15¢ (last 3h).
  - Volume timing: 29% traded 12–15h before close (morning after open), 22% in last 3h.
  - Near-money spreads: ~20¢ in first hours, ~4¢ midday, ~11¢ last hours.
  - Example 2026-11-24 event, strike 5.795 (settled YES at 5.7982): 92% at 9 AM → 84–86% 11 AM–noon → 96% 1 PM → 98% by 4 PM.
  - AAA site still showed 11/24 at ~10:15 PM ET → next AAA number is NOT posted before close; late confidence comes from other info (station-level prices / drift).
- **Decided:** The edge window is the morning (wide spreads, market only ~38% right on the bin). Our engine must output a probability per half-cent bin; bot only trades strikes priced 10–90%, where (our prob − ask − fee) is biggest.
- **Next:** #9 edge test on history; #8 minute candles; find AAA posting time (#3).

### 2026-11-24 (late) · DB filled by GitHub backfill
- **Did:** GitHub Action ran `tools/backfill.py`. Pulled 1,469 Kalshi diesel markets (69 days, ~4.93M contracts volume) and 5 years of Yahoo futures (BZ=F Brent, HO=F NY Harbor ULSD).
- **Learned:**
  - AAA diesel history from Kalshi settlements: 2026-09-18 → 2026-11-24 (64 settled days + 5 hand-seeded AAA points).
  - 48 days have the full 4-part breakdown. Weekends have AAA but no futures close → breakdown blank (use Friday's futures if needed).
  - **Delivery slice keeps widening as wholesale falls:** ~$1.01 (Sep 20) → $1.20 (Nov 13) → $1.38 (Nov 18) → $1.50 (Nov 24). Year ago: $0.78. Retail is lagging the wholesale drop (feathers on the way down).
  - AAA has been falling 1.4–3.4¢ every day in mid/late Nov.
  - FRED blocks/times out from GitHub runners → switched oil prices to Yahoo futures; FRED kept as backup only.
- **Decided:** Yahoo front-month futures are the history source for Brent + ULSD (proxy for spot). Hand-verified Nov 24 row keeps its manual values (fills-blanks-only rule).
- **Next:** Lag study (#2): regress daily AAA change on past N days of HO=F changes; test up vs. down speed.

### 2026-11-24 · Session 1: market scan → diesel teardown → research DB
- **Did:** Scanned liquidity on 12 Kalshi markets via the public API. Re-filtered with Dan's rules. Broke down how diesel is priced. Built this repo branch, SQLite DB, backfill script, and auto-runner (static).
- **Learned:**
  - Liquidity (Nov 24): Fed Dec meeting ~24M contracts (but ~6-week cadence); CPI Nov ~840K; AAA gas weekly ~160K/24h; NYC temp ~130K/day (excluded by rules); payrolls, U3, jobless claims, core CPI thin.
  - Rule-fitting daily/weekly markets: gas (best liquidity), diesel daily ~$52K + weekly ~$85K, 30-yr mortgage weekly ~$84K, nat gas daily ~$29K, WTI daily ~$27K, gold daily ~$24K (borderline: commodity traded like an asset).
  - Edge ranking: diesel (less crowded) ≈ gas > mortgage > WTI / nat gas / gold (these settle on pro-traded futures, weak edge).
  - Kalshi leaderboard is opt-in; individual bets aren't public. Better path: backtest our own model, not copy traders.
  - Kalshi settlement value = AAA number → free history.
- **Decided:** Focus diesel first. Static table for ideation; live schedule is one uncomment away. SQLite as main store. Repo lives on `kalshi-twins` branch of Startup (same pattern as the prayer app's `daily-bread` branch). ⚠️ Startup repo is **public**.
- **Next:** Verify backfill output → run lag study (#2).

See `research/2026-11-24_diesel-teardown.md` for full detail and sources.

---

