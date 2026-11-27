# Kalshi Twins — full research log (newest first)

Moved out of CLAUDE.md on 2026-11-25 so new sessions load fast. **Add new entries at the top of this file.**

Template:
```
### YYYY-MM-DD (time) · Chat N · short title
- **Did:** …
- **Learned:** …
- **Decided:** …
- **Next:** …
```

### 2026-11-27 (6:50 PM real clock) · Chat 6 · RESULTS: favorite ledger
- **Did:** `research/engine_room/favorite_ledger.csv` (84 rows: 6 markets + all-six × favorite side × price band) from `tools/slice_scan.py`; mirrored to new Build Board tab **Favorite Ledger**.
- **Learned (edge = win % − break-even %, per instance):** all six: Yes-favorites −3.8 pts (79.7% wins vs 83.5% needed), No-favorites +3.1 (86.7% vs 83.5%), No positive in every band early and late. Gas daily: Yes −4.6 / No +3.3. Gas weekly: Yes −6.3 / No +4.8 (No at 60–70¢ +12.8, at 70–80¢ +9.3). Gas monthly: Yes −4.4 / No +2.5 (too few events to flag). Diesel daily: Yes +3.2 / No +3.7 (No at 60–80¢ +10 to +12). Diesel weekly / monthly: too few events.
- **Regime check (gas, same day):** No-favorite edge +2.3 / +3.6 / +5.1 and Yes-favorite −2.0 / −2.9 / −8.1 in falling / flat / rising stretches; same signs in 2023, 2024, 2025, 2026. So it is not just one falling stretch. Gas weekly settles below the crowd's center 73% of the time.
- **Caveats:** instances repeat within an event (event counts shown beside); prices are hourly-candle asks; no forward test yet. Lead, not proof.
- **Decided (Dan):** slices should start as a plain count in 4 boxes (favorite Yes won / lost, favorite No won / lost) with a price range in each, then win % tied to price.
- **Next:** forward paper test of "gas No-favorites"; find why the gas crowd leans high (ties to the market-maker center layer).

### 2026-11-27 (6:35 PM real clock) · Chat 6 · PLAN: favorite ledger (Dan's cleaner slice design), written before building
- **Dan's ask:** start from a plain historical count. Four boxes: favorite Yes won / favorite Yes lost / favorite No won / favorite No lost. A price range inside each. Then the win % tied to the price paid.
- **Build (`tools/slice_scan.py` → `research/engine_room/favorite_ledger.csv`, Build Board tab "Favorite Ledger"):** per market × favorite side × price band (50–60, 60–70, 70–80, 80–90, 90+): instances, distinct events, wins, losses, win %, average price paid, break-even % (price + fee), **edge = win % − break-even %**, return per $, average bid-ask, and the same edge on the early 60% vs late 40% of events. Plus an "all six" roll-up.
- **Reading rule:** edge counts as a lead only with 20+ events in the band and the same sign early and late. Win % here is per instance; the event count sits beside it because one event repeats across time slots and lines.
- **Assumed (my reading of "% tied to the spread"):** the gap between how often the favorite wins and what its price says. Bid-ask width is shown too.

### 2026-11-27 (6:25 PM real clock) · Chat 6 · RESULTS: slice table + ratio layer + scan (`tools/slice_scan.py`)
- **Did:** built `data/lake/master/slices.csv.gz` (23,757 rows × 52, 542 events; layers 2 and 3) and `research/engine_room/slice_scan.csv` (1,328 cells) + `slice_scan_survivors.csv`.
- **Learned (base rates, per $ after costs, all rows):** favorite win rate 90 / 87 / 76 / 84 / 85 / 82% (diesel daily, diesel weekly, diesel monthly, gas daily, gas weekly, gas monthly); favorite return +4.4 / +3.8 / −6.4 / −0.7 / −0.1 / −1.3%; underdog return −58 / −56 / −34 / −33 / −37 / −37%.
- **Learned (scan):** 660 cells had 20+ fit events; 217 pass the 10% false-discovery filter, almost all of them "underdog loses". 18 survivors (positive in fit and holdout): gas daily No-favorite at night (+10.7% fit / +5.7% holdout, 91 holdout events, t 1.6; 80–90 band +9.6 / +7.9; 90+ band +3.5 / +3.2, t 2.0) · diesel daily Yes-favorite, morning, 90+ (37/37 and 28/28 wins, +3.2 / +5.1%; loss-free, so its t is inflated) · diesel daily No-favorite when crowd range ÷ jumpiness is low (+10.4 / +9.0, t 1.8) · diesel daily Yes-favorite when engine disagrees high (+12.4 / +7.1, t 1.5). Hint: gas weekly Yes-favorites −25% fit / −17% holdout (t −3.2).
- **Not testable:** diesel weekly, gas monthly, diesel monthly (0 cells with 20+ fit events).
- **Caveats:** asks from hourly candles assumed hittable for small size; fee rounding ignored; holdout t mostly under 2; with 660 tests about this many survivors can come from luck. Consistent with parked M28 (favorites) but not new proof.
- **Decided (Dan, 6 PM):** build everything; favorite = side above 50%; all six equally.
- **Next:** archive probe results (running); forward-test list from the 18 leads; more history for the long markets.

### 2026-11-27 (6:00 PM real clock) · Chat 6 · PLAN (written before running): slice table + ratio layer + scan, all six markets
- **Dan's direction (6 PM):** build everything: (2) slice table of favorite outcomes, (3) our own ratio layer, and keep the free-data hunt going. Favorite = the side priced above 50% on each of the 3 busiest lines. All six markets get equal depth.
- **Layer 2, `data/lake/master/slices.csv.gz`:** one row per market × event × snapshot × busy line (1–3). Favorite side, cost (ask + taker fee 0.07·p·(1−p)), outcome label (favorite won as Yes / won as No / lost as Yes / lost as No), return per $ for backing the favorite and for backing the underdog. Only lines with a bid-ask of 10 points or less, and only rows where the answer could not be public yet.
- **Layer 3, same file:** ratios per row: conviction (crowd's expected move ÷ its range) · trend score (5-day AAA move ÷ its usual 5-day size, Sharpe-style) · futures shock (5-day futures move ÷ its usual size) · futures-minus-pump divergence · pump-vs-wholesale gap · engine range ÷ crowd range · engine-vs-crowd disagreement in ranges (engine re-fit each quarter on earlier data only) · crowd range ÷ recent AAA jumpiness · line distance from center in ranges · spread · streak length · day of week · regime labels already in the master.
- **Scan, `research/engine_room/slice_scan.csv`:** (a) base cells: market × time of day (open / morning / afternoon / night) × days left × favorite side × price band (50–60 … 90+) × bet (favorite / underdog); (b) ratio cells: each ratio in thirds (cut points from the fit block) × market × favorite side × bet. **Deciding number:** return per $ after costs, averaged per event first (events are the sample, not rows). Fit block = first 60% of each market's events; false-discovery filter at 10% there; then the last 40% is looked at once. **Survivor** = passes the filter, 20+ events in each block, same sign and positive in the holdout. Also reported: Sharpe-style score per cell (mean ÷ spread of per-event returns × √events per year).
- **Expectation, stated up front:** ~1,300 cells and small samples (diesel daily 112 events, diesel weekly 15, diesel monthly 3) → a few lucky survivors are expected; survivors are leads for a forward test, not proof.
- **Verified:** the busy-line columns hold bid, ask, no-ask and the settled side. **Assumed:** hourly-candle asks could really be hit for small size; fee rounding ignored.

### 2026-11-27 (5:20 PM real clock) · Chat 6 · PROBE PLAN: what the Internet Archive holds for live pump-price sources
- **Dan's direction:** keep pushing every free angle; saved copies on the Internet Archive are fair to read for personal research (his call; noted that this is not legal advice and that our repo is public, so we store only the few numbers we need, not pages).
- **Probe (`tools/probe_archive.py`, reads web.archive.org only):** ~45 candidate pages (GasBuddy national / charts / fuel insights, AAA, Trading Economics, YCharts, truckstop and big-chain price pages, the Love's store feed we already record) → days saved per year since 2023, saves per day, hours of day seen, and a text sample near "average". Plus a list of saved URLs on 11 domains to find pages we did not think of.
- **Deciding number:** a source is worth pulling if it has 200+ distinct days in 2025–26 with a readable national (or many-station) price in the saved copy. Several saves per day = intraday history, the prize.

### 2026-11-27 (5:10 PM real clock) · Chat 6 · DECISION: free data only for now
- **Decided (Dan):** build the database with as much free data as possible; no buying for now. No quote requests sent.
- **Did:** CLAUDE.md §6 step 2 rewritten with the free-only order. Checked today's fix landed: `fut_*_1d.csv` now real daily bars (RBOB 6,550 rows) and 8 curve files (`curve_rb*/ho*_1d.csv`, Dec 2026 to Mar 2027 contracts). Live feeds fresh at 22:08 UTC.
- **Oddity (open):** `data/warehouse_catalog.md` header still says 2026-11-25 21:29 UTC although the warehouse job has finished since; a run is in progress now. Re-check when it ends.
- **Proposed order:** (a) state AAA history from Kalshi's own state markets (50 states, late Aug to Nov 10, numeric settle values already in `data/lake/kalshi/`) + Internet Archive; (b) widen our own live posted-price feed beyond Love's + TA, reading each chain's terms first; (c) curve into the master; (d) older trade tape.
- **Next:** (a), then (b).

### 2026-11-27 (5:25 PM real clock) · Chat 6 · Source check: history for a live station-price average (web search only)
- **Did:** searched for who holds daily / intraday station-average history. No data pulled, nothing scraped.
- **Learned:** GasBuddy publishes a **live** national average that moves during the day (its analyst posted a live diesel number at 3:25 PM ET on 2026-09-03 and a "full-day official" number the next day). That fits the crowd's intraday pattern (M57). GasBuddy history (2001 on) is sold, price not public; a third-party audit says automated use needs a license from PDI Technologies (not checked against the terms text: the terms page fetch needed an approval nobody answered). OPIS sells retail history from 2007 and has a 10-day trial for spot/rack; OPIS is AAA's source, so the MNPI rule in CLAUDE.md §5 applies before any use.
- **Free lead for a different gap:** GitHub `nathanqthai/gas_prices` holds daily AAA state-level prices from 2022-09-30 (fills "state-level AAA history" in §6 step 2). Needs vetting against our AAA national before joining the master.
- **Added 5:10 PM (terms now read, Dan approved the fetch):** GasBuddy Terms §15 bans bots / scraping / downloading price data (15.8) and building a database from its content (15.2); §11 and 15.14 ban commercial use; data may not be forwarded without written consent (15.3). So: no scraping, and do not use the GasBuddy part (2026-03-29 on) of the `nathanqthai/gas_prices` repo; its AAA part (2022-09-30 to 2026-03-27, state + county, gas only, no license stated) still needs vetting. Other sources: OPIS RetailSuite (paid, live + history, AAA's own source → MNPI check first). Internet Archive copies of GasBuddy's public page = gray area under 15.2, not used without Dan's call.
- **Decided (Dan):** go ahead on checking; wants more than a month of history. **Proposed:** ask PDI for a quote on daily national gas + diesel averages, 2023 on; do not scrape GasBuddy.
- **Next:** Dan's call on sending the quote request; vet the free AAA state file.

### 2026-11-27 (5:15 PM real clock) · Chat 6 · RESULTS: 8 AM input hunt (not found in history) + futures pull fix
- **Did:** tested S1–S3 on AAA history, scored on the open snapshot of the last 40% of daily events (40 diesel, 98 gas). Fixed `tools/history_pull.py pull_daily` (was writing monthly bars; now daily) and added the next 4 RBOB + heating-oil contract months (`data/lake/history/curve_*_1d.csv`, lands with the next `warehouse.yml` run).
- **Learned (typical miss to next AAA at the open, diesel / gas):** S0 yesterday only 0.81 / 0.62¢ · S1 + 7 moves 0.76 / 0.56 · S2 + day of week 0.62 / 0.40 · S3 + wholesale 0.44 / 0.46 · **crowd 0.25 / 0.25**. Explains the crowd's expected move: 0.63–0.81 (needed 0.85). **Verdict by the plan's rule: not found.**
- **Learned:** at the close the crowd explains 0.98 (diesel) / 0.99 (gas) of the next AAA move, miss 0.13 / 0.12¢, about 3 hours before AAA posts. All-days miss by snapshot (gas): 0.40 open, 0.36 noon, 0.27 3 PM, 0.21 6 PM, 0.19 close. Reads like a live station-price average that leads AAA.
- **Not run:** S4 (state AAA from Kalshi state markets): numeric state history starts late Aug 2026, inside the scored block, so no clean fit window.
- **Oddity chased:** `fut_*_1d.csv` had ~268 rows since 2000 = monthly bars. Master unaffected (it reads EIA + DB futures). State markets close 3:19 AM ET, matching the AAA post time in the flip log.
- **Decided:** nothing new from Dan. **Proposed:** the remaining suspect needs history we do not hold. GasBuddy sells daily history (2001 on); terms and cost need a check before any use. Free path = our own live recording (truckstops now; a live national average if terms allow), which is a forward test, not a backtest.
- **Next:** Dan's call on free-only vs buying history. Add day of week to the engine.

### 2026-11-27 (4:50 PM real clock) · Chat 6 · PLAN (written before running): hunt the input the daily crowd has at the 8 AM open, on history
- **Dan's ask:** find the missing input and prove it on a backtest before any live test.
- **Question:** which input, known by 8 AM, takes our next-day AAA miss from ~0.65¢ down to the crowd's 0.31¢ (diesel) / 0.40¢ (gas)?
- **Suspects that have history (tested in this order, each added on top of the last):** S1 longer AAA memory (the last 7 daily moves, not just yesterday's; AAA may be a rolling average) · S2 day of the week · S3 wholesale (futures moves 1 / 3 / 7 days, pump-vs-wholesale gap, split up / down) · S4 state-level AAA from Kalshi's own state markets (if their settle values line up with dates before the scored block).
- **Suspects with no history (cannot be backtested, live only):** same-morning station prices (truckstops, GasBuddy-type). If S1–S4 fail, this is what is left, and the truckstop scorecard is its test.
- **Method:** fit on AAA days before the scored block (last 40% of each daily market's events), score on the open snapshot of those events. **Deciding number:** typical miss to the next AAA number. "Found" = within 0.05¢ of the crowd's miss AND explains 85%+ of the crowd's expected move at the open. Costs do not apply (this is a copy test, not a trade).
- **Verified:** at the open the master's AAA is that morning's number (asof = snapshot date when the snapshot is after 6 AM). **Assumed:** the open snapshot (first hourly candle) is close enough to 8 AM.

### 2026-11-27 (5:20 PM) · Chat 6 · RESULTS: anchor engine on all six (`tools/mm_anchor.py`)
- **Did:** new tool `tools/mm_anchor.py` → `research/engine_room/mm_anchor_scorecard.csv`, `mm_anchor_engine.csv`. Engine fit on outside data only (long: ~1,050 EIA weeks since 2006; short: 380–630 AAA days), always on dates before the scored events. Kalshi sets 2 dials per layer.
- **Learned (center, last 40% / odd-even; v1 in brackets):** diesel daily 0.84 / 0.78 (0.76) · diesel weekly 0.76 / 0.68 (0.66) · gas weekly 0.68 / 0.73 (0.71) · gas daily 0.63 / 0.72 (0.70) · gas monthly 0.32 / 0.30 (0.28) · diesel monthly 0.08 with borrowed gas dials (3 events, not proven).
- **Learned (range):** gas weekly 0.59 / 0.62 (0.55) · gas monthly 0.40 / 0.70 (−0.04) · diesel weekly −0.07 / 0.52 · gas daily −0.88 / 0.08 · diesel daily −2.99 / 0.21. Third dial (time left to close) changed nothing (second look).
- **Learned (price terms, the real yardstick):** line built from inputs only vs real mid: 16.5 / 11.2 / 10.6 / 14.6 / 6.1 points off (gas daily, gas weekly, gas monthly, diesel daily, diesel weekly) vs no-model 23.5 / 18.5 / 13.5 / 25.9 / 8.0 and spreads of 2–4 points. Inside the real bid-ask: 4 / 6 / 5 / 8 / 18% of lines. **Not a usable baseline yet in any market.**
- **Learned (missing input):** at the 8 AM open the daily crowd's center is 0.31¢ (diesel) / 0.40¢ (gas) from the next AAA number; our engine 0.6–0.7¢; momentum alone 0.7¢. Monthly gas: engine 6.9¢ vs crowd 7.1¢ (a tie). Hint only, no costs.
- **Engine facts:** rockets-and-feathers engine explains 44% (gas) / 32% (diesel) of next week's pump move, falling to 20% / 17% at 6 weeks; AAA-daily engine ~59% at 1 day.
- **Caveats:** the price yardstick and the third dial were added after first scores. Spot (training) vs front futures (applied) assumed alike. Odd/even scores use an engine fit up to the start of the scored block.
- **Decided:** nothing new from Dan. **Proposed:** hunt the input the daily crowd has at the open (same-morning station-level prices are the first suspect); add the futures curve (next month vs front) for monthly.
- **Next:** see Proposed.

### 2026-11-27 (4:40 PM real clock; today's earlier stamps ran about an hour fast) · Chat 6 · PLAN (written before running): anchor engine, big real-world data first, Kalshi sets 2 dials
- **Dan's ask:** crack all six by using the big real-world gas and diesel wholesale + pump-price history to carry the small Kalshi samples.
- **Question:** if the pump-price engine (center and range of the next move) is fit on the big outside data only, can 2 dials per market per layer match the crowd on dates never seen?
- **Step 1 (no Kalshi data):** long engine = EIA weekly pump price vs NY Harbor wholesale spot, 2006 on (~1,060 weeks), direct fits at 1 to 6 weeks ahead on: last week's pump move, pump-minus-wholesale gap vs its 26-week norm (split up / down = rockets and feathers), wholesale move 1 week (split up / down) and 4 weeks. Short engine = AAA daily (700 to 850 days), 1 to 6 days ahead, same inputs at day scale. Range = size of the engine's own misses at each horizon, scaled by recent wholesale jumpiness (20-day average daily move). Engines fit only on dates before each market's scored events.
- **Step 2 (Kalshi, 2 dials each):** crowd expected move = k0 + k1 × engine move. log(crowd range) = c0 + c1 × log(engine range).
- **Deciding numbers:** share explained on the last 40% of events (and odd/even), vs v1: center 0.76 / 0.66 / 0.70 / 0.28 / 0.71, width −2.13 / −0.44 / −0.81 / −0.04 / +0.55 (diesel daily, diesel weekly, gas daily, gas monthly, gas weekly). "Cracked" = 0.5 or more on both scores. Diesel monthly (3 events): cannot be scored; it gets gas monthly's dials and is shown as borrowed, not proven.
- **Side number (hint only, no costs):** engine vs crowd, typical miss to the final AAA number on the scored events.
- **Added 5:00 PM after the first run (second look, say so in results):** range still fails in the two daily markets and diesel weekly. The engine only knows whole days, yet the ladder narrows hour by hour. Try one more range dial: log(time left to close). Report both the 2-dial and 3-dial scores.
- **Added 5:10 PM (third dial did not help):** final yardstick in price terms, since range is fuzzy to measure on half-cent ladders: build every line's price from inputs only (engine center + engine range + dials, bell curve) on the scored events and compare with the real mid price. Report typical gap in price points, share of lines inside the real bid-ask, and the same for a no-model copy (no move, average range). "Good enough to use as the baseline" = typical gap no bigger than the typical spread.
- **Verified:** inputs_daily futures are already lagged a day; AAA is keyed by its own date and joined on the master's asof_date. **Assumed:** wholesale spot (training) and front futures (applied) move alike; EIA weekly pump price behaves like AAA at week scale.

### 2026-11-27 (5:30 PM) · Chat 6 · RESULTS: Layer B (width) on all six + gas monthly center (mm_model v1)
- **Did:** Master +4 columns (`crowd_center_fit`, `crowd_sigma_fit_c`, `aaa_absmove_5d_c`, `aaa_absmove_20d_c`; 12,896 × 178). `tools/mm_model.py` v1: center forms A0 linear / A1 pass-through / A2 scale-free; width forms S1–S4; calibration; two scores per market (last 40% in time order, and odd/even events).
- **Learned (width, last-40% score / odd-even score):** gas weekly **+0.55** / 0.60 (error 43% vs 69% no model) = cracked. Gas daily −0.81 (S3; error 47% vs 83%) / 0.37 = half way. Diesel daily −2.13 / 0.52, diesel weekly −0.44 / 0.61, gas monthly −0.04 / 0.67 = fail in time order, fit with eras mixed. Diesel monthly: 3 events, no fit.
- **Learned (how they differ):** width 1 day out 1.01¢ / 2.44¢ / 0.83¢ / 1.65¢ / 0.95¢ (diesel daily, diesel weekly, gas daily, gas monthly, gas weekly); 7 days out 2.0 / 7.39 / 1.7 / 6.31 / 4.59¢; time power 0.35 / 0.57 / 0.37 / 0.69 / 0.81; in strike steps at 1 day 2.02 / 1.22 / 1.67 / 0.33 / 0.47. Settle inside ±1 width: 86 / 83 / 80 / 78 / 78% (diesel monthly 88% on 3 events) vs 68% for a well-sized bell → crowd's range is too wide everywhere (hint; no costs).
- **Learned (gas monthly center):** not solved. Last-40%: A0 0.28, A1 0.19 (picked by the inner split), A2 scale-free −0.09; odd/even 0.38. Cause: era drift (2026 ladders 16–44 lines vs 4–11; expected moves 2.5× larger), 29 events. Other centers unchanged: 0.76 diesel daily, 0.66 diesel weekly, 0.70 gas daily, 0.71 gas weekly (rows needing the new jumpiness column dropped a few events, hence 0.79 → 0.76).
- **Caveats:** the scale-free forms (A2, S4) were added after seeing first scores, so their last-40% numbers are a second look. Daily width is noisy to measure at 0.5¢ strikes (two width measures correlate only ~0.33). Width is measured from mid prices, not trades.
- **Decided:** nothing new from Dan. **Proposed:** treat weekly gas as the first market with a full baseline copy (center + width); re-fit moving numbers on a rolling window instead of one fixed fit.
- **Next:** rolling-window re-fit for width and gas monthly center (plan line first); same-day futures at midday snapshots (largest missing input).

### 2026-11-27 (4:30 PM) · Chat 6 · PLAN (written before running): Layer B (crowd's width) on all six markets
- **Asked (Dan):** crack Layer B on all 6 and show how they differ. Goal: a baseline "perfect copy" of the market maker to tweak later.
- **Step 1, measure width better:** v0 read width from two crossings (84% / 16%), which is coarse when strikes are far apart. Re-measure by fitting a bell curve to every tight line at each snapshot (`width_fit`), keep both.
- **Step 2, three candidate equations for log(width), chosen on the first 60% of events only (inner split), scored once on the last 40%:**
  S1 time only: log(days left). S2 = S1 + recent AAA jumpiness (5-day and 20-day average daily move). S3 = S2 + size of the move the crowd expects + size of yesterday's AAA move + size of the last ladder's closing miss + time-of-day marks.
- **Deciding numbers:** out-of-sample share explained (log scale) and typical % error, vs the baseline "always the usual width".
- **Step 3, how the six differ (description):** time exponent (0.5 = uncertainty grows like a random walk), width per day in ¢ and in strike steps, sensitivity to jumpiness, and calibration: share of settles inside ±1 width (a well-sized bell curve gives 68%).
- **Assumed:** a bell curve is a fair shape for measuring width (Layer C says it is ~3 points off per line).
- **Added 4:35 PM, before running (Dan: "if you can't solve monthly for diesel you gotta solve it for gas"):** Layer A for **gas monthly** scored 0.29 in v0. Candidate A1 = a pass-through form built for long horizons: yesterday's AAA move × how long momentum lasts (decay ρ), plus the retail-vs-wholesale gap and the 5-day and 20-day futures moves × how much of them reaches the pump by settlement (1 − e^(−days/τ)), plus a per-day drift. ρ ∈ {0.6, 0.8, 0.9} and τ ∈ {5, 10, 20, 40} are picked on an inner split of the first 60% of events; scored once on the last 40%. A1 is also run on the other five for comparison. Deciding number: out-of-sample share of the center explained vs v0's.
- **Second attempt, added 4:55 PM after seeing the first scores (so the last-40% score is no longer a clean first look; say so in results):** the first run showed the forms fit (gas monthly 0.60 in-sample, 0.62 on an odd/even event split) but do not carry from calm 2024–25 into jumpy 2026 (expected moves 2.5× larger). Fix to try: make both layers **scale-free**. A2 = center inputs and target divided by recent AAA jumpiness (20-day average daily move). S4 = log width on log(days left), log(recent jumpiness, 5d) and log(the crowd's own average closing miss over its last 5 ladders); 3 terms only. Report two scores for every market: last-40% (time order) and odd/even events (era-mixed).

### 2026-11-27 (4:20 PM) · Chat 6 · RESULTS: market-maker equation v0, all six markets (plan = the 4:00 PM entry below)
- **Did:** `tools/mm_model.py` → `research/engine_room/mm_model_scorecard.csv` + `mm_model_coefficients.csv`. Fit on the first 60% of events, scored on the last 40%.
- **Learned:**
  - **A. Center (where the crowd puts the answer):** out-of-sample explained 0.79 diesel daily (45 scored events), 0.71 gas daily (98), 0.68 diesel weekly (6), 0.72 gas weekly (18), 0.29 gas monthly (12); diesel monthly not fittable (3 events). Miss vs strike step: daily 0.56¢ / 0.50¢ (vs 0.5¢ step), weekly 1.95¢ / 1.37¢ (vs 2¢), gas monthly 4.1¢ (vs 5¢) → about one line everywhere.
  - Daily center ≈ **0.72× yesterday's AAA move (diesel), 0.64× (gas)**; futures and the retail gap add almost nothing. Weekly starts above 1× yesterday's move and adds futures as days-out grow.
  - **B. Width (how unsure the crowd is): not cracked.** √time + jumpiness explains gas weekly (0.58) and fails out of sample on the other five (negative). Width shifts over time for reasons we have not modeled.
  - **C. Shape:** a bell curve with the crowd's own center and width misses each line by 2.6–3.2 price points in all six. Low-chance lines are priced richer than the bell curve: +0.3–0.4 points daily, **+1.8 to +3.2 points weekly and monthly** (fat tails / long-shot premium; matches "cheap long shots lose" from the deep scan).
  - **D. Cost:** median spread 2–3¢ daily, 2–4¢ weekly, 3–5¢ monthly.
- **Limits:** one equation stands in for several market makers plus retail orders; weekly and monthly rows overlap inside an event; diesel weekly is 15 events, gas weekly ladders only exist in 2026.
- **Next (proposed):** width layer (try time-of-day, days-out and recent miss size); skew-aware shape; then compare this equation with a truth equation term by term (where the crowd's weights differ from what actually happens = candidate edge).

### 2026-11-27 (4:00 PM) · Chat 6 · PLAN (written before running): market-maker equation v0 on all six markets
- **Asked (Dan):** outline the market-making algorithm we are working backwards to solve, for all 6 markets, so each input can be isolated.
- **What this is:** a description of how the ladder is priced, not an edge test. Extends Engine Room L0.1 (diesel daily only) to all six.
- **Equation, four layers, fitted per fuel × time slice from `data/lake/master/`:**
  A. **Center** (crowd's expected move in ¢) = f(AAA 1-day and 5-day change, main future 1-day and 5-day change, retail-minus-wholesale gap vs its 60-day normal), with each term allowed to grow with days to settlement.
  B. **Width** (crowd range σ) = g(√days to settlement, recent AAA jumpiness).
  C. **Shape**: price of each line = bell curve with that center and width; score = median miss per line in price points.
  D. **Cost layer**: spread by price level.
- **Scoring:** fit on the first 60% of events, score on the last 40% (never used to fit). Deciding numbers: out-of-sample share of the center explained, center miss in ¢ vs the strike step, line miss in price points. Rows flagged `answer_may_be_public` excluded.
- **Assumed, not verified:** one equation per market is a fair summary of several market makers plus retail orders; hourly candle quotes are tradeable quotes.

### 2026-11-27 (3:45 PM) · Chat 6 · Are weekly and monthly different? Contract cards, Inputs Map reconciled, a miss owned
- **Asked (Dan):** is the master carrying every input from the first Excel (Inputs Map), across the time slots, 3 liquid lines and 6 markets? Have we tracked how the open (market making) and close (settlement) algos differ for weekly and monthly? Concern: Claude is not scouting these risks, so work can be fake.
- **Owned:** the master was built on the unverified assumption that all six markets settle like daily. The one 0.4¢ weekly mismatch was flagged on 11/26 and not chased. Checked today.
- **Learned (settlement = "close algo"):** rule text is the same shape on all six: AAA national on ONE date ("If the Diesel Price on <date> is above $K"; "average regular gas prices ... on <date> according to AAA"). Weekly = Monday, monthly = last day of month. Not an average. Against AAA prints from other sources: diesel 116/116 daily, 16/16 weekly, 3/3 monthly; gas 271/271 daily, 99/100 weekly (one 0.4¢ off, 2026-07-13), 25/25 monthly. 57 older gas weekly/monthly events have no outside print to check yet.
- **Learned (design differs):** days open 0.7 / 6.6 / ~31 · strike step diesel 0.5¢ / 2¢ / 10¢, gas 0.5¢ / 2¢ / 5–9¢ · diesel closes 2 AM ET on settle day, gas at midnight (2023 gas closed ~10 AM, after AAA posts) · settle decimals 3 before 2026, 4 in 2026 · gas monthly fee type `quadratic_with_maker_fees` · contracts per event: diesel 50K / 138K / 274K, gas 183K / 1.0M / 1.7M (2026). **Before 2026 gas weekly was ONE line per event (95 events)**; gas monthly had 6–10 lines.
- **Learned (market making by horizon; 10 AM snapshots, description only):** crowd range (σ) diesel 1.0¢ at 1 day → 3.6¢ (2–3 d) → 6.5¢ (4–7 d) → 21–39¢ (8+ d); gas 0.7 → 1.7 → 4.0 → 6.2 → 10.0¢. Typical miss diesel 0.36 → 0.98 → 3.9¢; gas 0.35 → 0.79 → 2.4 → 4.0 → 5.8¢. Weight on the 5-day futures move in the crowd's expected move: diesel 0.02 (1 d) → 0.13 (4–7 d) → 0.21 (15+ d); gas 0.03 → 0.15 → 0.29. Actual moves at 4–7 d lean on futures more than the crowd does (0.21 vs 0.13 diesel, 0.21 vs 0.15 gas): a hint, overlapping rows, 19 diesel events.
- **Did:** `backtest_master.py` now writes `contract_cards.csv` + two new COVERAGE sections on every rebuild; +17 columns (fee_type, strike_step_c, open/close times, days open, favorite line, holiday flags, previous ladder's closing miss, sister-fuel future, hub gaps, natgas) → 174 columns. Fixed: mixed timestamp formats had dropped 3 markets; LA diesel hub name. Inputs Map sheet column O = status of all 83 inputs: **41 in the master, 20 partly, 22 not collected.** New working rule in `CLAUDE.md` §0 (check the thing before building on it).
- **Biggest real gaps:** same-day futures at the noon / 3 PM / 6 PM snapshots (live only since 11/25) · rack prices · truckstops and state prices have no history · our own model forecast is not rebuilt for the 6 markets · 1 gas weekly event has Yes/No instead of a settle number (not in the master).
- **Next:** vet the state-level + older Kalshi series already pulled raw; then Dan's custom arrays.

### 2026-11-26 (7:05 PM) · Chat 6 · Master snapshots: open, close + five in-between marks; AAA post time seen
- **Decided (Dan):** keep the 3 busiest lines; snapshot at multiple times: open and close always, Claude picks the in-between marks from the research.
- **Did:** `tools/backtest_master.py` now writes 7 snapshots: open, 10 AM, noon, 3 PM, 6 PM, 10 PM, close (reasons in the RULEBOOK: bet time and morning volume, the noon and 6 PM clusters of unexplained moves, futures settle at 2:30 PM, Love's ~5 PM batch, evening volume). Master is now `backtest_master.csv.gz`: 576 events, 12,845 snapshots, 155 columns; 147,530 line-rows.
- **Learned:**
  - **AAA post time, first recorded flip:** between 3:17 and 3:32 AM ET on 2026-11-26 (gap G2; one observation). As-of rule: snapshots before 6 AM ET use the previous day's AAA.
  - 36 snapshots on older gas ladders fall on the settle day itself, after that post time → flagged `answer_may_be_public = 1`; exclude from tests.
  - Re-vet vs old daily panels: 114 diesel + 242 gas shared days, settle values identical, 10 AM crowd center gap 0.00¢.
  - Descriptive only (not a test): median crowd miss by snapshot. Diesel: open 0.30¢ · 10 AM 0.35 · noon 0.32 · 3 PM 0.33 · 6 PM 0.27 · 10 PM 0.24 · close 0.23. Gas: 0.40 · 0.39 · 0.35 · 0.26 · 0.21 · 0.20 · 0.18. Diesel's crowd sharpens between 3 PM and 6 PM; gas between noon and 3 PM.
- **Next:** vet the state-level and older Kalshi series now landing in `data/lake/kalshi/`; then Dan's custom arrays.

### 2026-11-26 (6:45 PM) · Chat 6 · Backtest master: both fuels × daily/weekly/monthly, Kalshi historical tier, wider inputs
- **Asked (Dan):** now is the raw data collection stage. Rebuild for weekly and monthly, go below AAA into the sub-components, reconcile into ONE backtest master for gas + diesel × 3 time slices with the 3 most liquid lines; source, reconcile and vet proactively. Also earlier this session: a phone command system (saved skill `kalshi`) and the two-pillar framing (phone playbook + market system).
- **Did:**
  - `tools/pull_kalshi_history.py` + `kalshi_history.yml`: every settled market + hourly candles from Kalshi's live AND historical tiers (`/historical/markets`, `/historical/markets/{t}/candlesticks`). Replaces `pull_horizon_ladders.py` (deleted with its workflow).
  - `tools/history_pull.py`: +50 EIA series (regional/state pump prices, storage by region, refinery runs, production, demand, imports/exports, LA gasoline, heating oil, jet, refiner resale) and a full-history daily futures pull.
  - `tools/backtest_master.py` → `data/lake/master/`: master table, per-line ladder snapshots, as-of-safe inputs, reconciled AAA, `COVERAGE.md`. The RULEBOOK is its docstring. Auto-rebuilds at the end of `kalshi_history.yml`.
  - Sheet: new tab "Backtest Master" (coverage copy). `CLAUDE.md` §4 + §6 updated (stage = raw data collection).
- **Learned:**
  - **The historical tier was the missing history.** Cutoff = 2026-09-27. Gas weekly 10 → 139 events (Oct 2023 on), gas monthly 2 → 34 (Dec 2023 on). Diesel started Aug 2026: 116 daily, 16 weekly, 3 monthly; that is everything. Gas daily: 23 days in 2023, 1 in 2024, none in 2025, 247 in 2026 (Kalshi did not run it).
  - Master v1: 574 events, 6,908 snapshots (10 AM / 6 PM / 10 PM ET on every open day), 152 columns, 77,329 line-rows, 73 inputs with data.
  - **Vetting:** vs the old daily panels, 113 diesel + 241 gas shared days: settle values identical, 10 AM crowd center median gap 0.00¢, none over 0.5¢. Internet Archive AAA rows (Current / Yesterday / Week Ago) match official settlements 100%. The sample bot's AAA file matches only ~50% (off by a day on many rows) → dropped. One weekly gas event (2026-07-13) settled 0.4¢ from the daily print.
  - Older gas weekly ladders are thin: crowd center found on 32% of snapshots, 3 liquid lines on 26%.
  - Yahoo blocks the browser-like user agent in `history_pull.py` (no `yahoo_*` file ever landed); the plain one in `backfill.py` works. Fixed for the new daily pull; the intraday pull still uses the old one.
  - The DBs' fill-blanks-only rule can freeze a partial-day futures bar (Brent 11/25: 87.43 in the diesel DB vs 90.47 in the gas DB). The master drops the newest 2 DB bars.
  - **Kalshi has 289 fuel-related series** (`data/lake/kalshi/_series_discovered.csv`): 100 state-level daily gas markets (`KXAAAGASD<ST>`, `KXAAAGASCD<ST>`), older `KXDIESEL` / `KXGAS` / `KXGAS-MONTH` / `KXGASD`, NJ weekly, TX monthly, AK diesel monthly, heating oil, jet fuel, Brent/WTI/natgas ladders, EIA inventory markets, a gas-station card-spend market.
- **Decided (Dan):** stage = raw data collection; gas and weekly/monthly are back in scope for data. After collection: custom arrays (regimes, Sharpe-style scoring, correlations).
- **Next:** (1) raw pull of the related + state series is queued in `kalshi_history.yml`; vet, then map the useful ones into the master. (2) `/historical/trades` for the trade tape before Sep 27. (3) State AAA history from the Internet Archive. (4) Fix the intraday Yahoo user agent. (5) Dan's open questions: what "3 high liquidity points" means beyond the 3 busiest lines; free-only data or paid station history.

### 2026-11-26 (3:45 AM) · Chat 6 · RESULTS: deep scan of every parameter (plan = the 3:10 AM entry below)
- **Did:** `tools/deep_scan.py` on diesel (114 days, 38 parameters, 13,891 priced bets) and gas (216 days Apr 7–Nov 25, 37 parameters, 31,564 bets). ~1,980 tests. Write-up: `research/2026-11-26_deep-scan.md`; tables: `research/backtests/deep_scan/`.
- **Learned:**
  - **Direction of the 10 AM miss: 0 parameters pass, both products.** Diesel had 6 pass the false-discovery filter on the first 60% of days; all 6 failed the last 40% (e.g. `ho_chg_3d` rho +0.47 → 0.00). One hint: `prev_info_gap_c` (yesterday's intraday drift), rho +0.31 / +0.42, gas +0.17.
  - **Size of the miss is predictable** (crowd's own range, expected change, momentum, rising regime ↑; weekends ↓ in gas). The crowd's range already carries it → sizing/skip tool, not an edge.
  - **Walk-forward model (all parameters):** predictions correlate with the miss out of sample (rho 0.26 both products) but adding them makes the error worse (diesel 0.73¢ → 0.90¢, gas 0.60¢ → 0.70¢). Bets: diesel −29%/$ (p 0.16), gas +2%/$ (p 0.87).
  - **Reliable losers:** 45 losing finds, 36 of them 3–25¢ long shots (about −70%). Gas YES at 10 AM loses in every band.
  - **Winners that passed:** 5, of which 3 are heavy-favorite loss-free streaks (+6–7%), 1 isolated hour cell. 6 more heavy-favorite cells were dropped by the binomial rule (streak only).
  - **Candidate (Part E, follow-up):** evening crowd overshoots a rising trend. Rising-most 5-day tercile, NO at 9–11 PM, lines ≥ 25¢: gas **+28%/$ (CI +17 to +39, 63 days, 184 bets, win 90% at 74¢)**; first 60% +33%, last 40% +20% (CI +2 to +40, 22 days); 5 of 6 months positive; YES mirror −38%. Diesel +27% (CI −8 to +64, 13 days, all Sep); YES −34% (CI −57 to −11).
- **Limits:** Part E came from the same days that suggested it; rising days clump (May, Jul, Sep); hourly candle quotes, fill size unknown; nothing to trade now (0 rising-most days in November).
- **Correction:** gap G5 said "only one regime". Diesel has ~21 strongly rising days (Aug–Sep). Fixed in the gaps file.
- **Decided (proposed):** current inputs cannot beat the 10 AM crowd; that question is closed until new inputs arrive. Keep the trend-fade as an open candidate and forward-test it at the next rising stretch.

### 2026-11-26 (3:10 AM) · Chat 6 · PLAN (written before running): deep scan of every parameter, diesel then gas
- **Asked (Dan):** as deep a backtest as possible on all parameters we have, all diesel days, then gas.
- **Risk:** a scan this wide WILL throw up lucky winners. So the rules are fixed here first.
- **Data:** `panel_daily` + hourly `kalshi_candles`, diesel (115 events) and gas (269 events). Bets bought at ask + taker fee 0.07·p·(1−p), spread ≤ 10¢, held to settlement. All stats clustered by day.
- **Part A (the main question):** which bet-time parameters predict the crowd's 10 AM miss (`aaa_settled − am10_crowd_forecast`, signed and absolute)? Spearman rank correlation per parameter.
- **Part B:** bet-level grid = parameter tercile × price band × side at 10 AM. **Part C:** hour of day × price band × side.
- **Part D:** walk-forward model using all parameters to shift the crowd's center; bet when model chance − cost ≥ 5¢.
- **What counts as a find:** (1) passes a false-discovery filter (Benjamini–Hochberg 10%) on the first 60% of days, AND (2) same sign with p < 0.05 on the last 40% (never used for selection), AND (3) same sign in the other product. Anything less = "hint". Primary number reported: how many cells pass vs how many luck alone would give.
- **Added 3:25 AM after the first run, before running it (follow-up, not independent):** Part A showed the crowd's CLOSE forecast overshoots the recent trend in gas (settled AAA lands back toward 'less change'), same sign in diesel. **Part E** = bet-level check at 9–11 PM: trend tercile (`aaa_chg_5d`) × price band × side, same find rules. Also: for bands ≥ 85¢ a t-test is fooled by loss-free streaks, so those cells must ALSO beat their own price on a day-level binomial test (p < 0.05). This rule is stricter, never looser.

### 2026-11-26 (3:00 AM) · Chat 6 · G1 first read: how big can a bet be?
- **Question (Dan):** what's the max bet; would $5–10K work? Deciding number: share of favorite-side quotes (ask 60–97¢) where the full amount fills, and the slip in cents.
- **Did:** Walked the recorded order book (KXDIESELD-26NOV26, 40 snapshots, 2:31 PM–11:57 PM ET 11/25, 78 favorite quotes) for $1K / $5K / $10K; summarized the trade tape (29.5K trades, 60 event days, top-3 lines).
- **Learned:** Book: median **$2,750 at the best price**, $3,770 within 2¢. $1K fills on 96% of quotes with 0 slip (median); $5K fits on 54% (median slip 0.7¢, mean 4.2¢); $10K on 17% (median 10.6¢). Depth is patchy: 7–9 PM the main favorite had almost nothing at the best price. Tape: median **$35K/day** traded (mean $38K, range $0.2K–$120K); favorite-side taker flow median $16K/day; median trade $2, 99th pct $990; 218 trades ≥ $1K on 35 days, only 3 ≥ $5K. Busiest hours 8–10 AM ET (36% of dollars) and 9–11 PM (20%).
- **Decided (proposed):** working cap ≈ **$1K per bet** (maybe $2–3K split across the day). $5–10K works as a bankroll, not as a bet.
- **Limits:** one afternoon/evening; that day's favorites sat at 92–94¢; no 10 AM book yet (recorder started 2:21 PM). Re-run after ~1 week.

### 2026-11-26 (2:15 AM) · Chat 6 · Audit: structure, handoff, truckstop scorecard, gaps
- **Did:** Read Chats 1–5 + the repo. Added `CLAUDE.md` §0 (start/end checklist, working rules, data-flow map) and rewrote §6 as the one live direction. Wrote `research/2026-11-26_gaps-and-direction.md` (13 ranked gaps). Built `tools/truckstop_test.py` → `research/engine_room/l3_truckstop_scorecard.csv`. `truckstops.yml` now saves after every hourly snapshot (was: once, after 5.5 h) and refreshes the scorecard. Takeaways: Chat 6 rows + master M28–M33.
- **Learned:**
  - **No large-sample truckstop backtest is possible.** No free archive of truckstop prices exists; recording began 11/25 (7 hourly snapshots so far). Only a forward test (grows daily) or bought history.
  - Truckstop day 1 (11/25, 3 PM–10 PM ET): Love's repriced in **one batch around 5 PM ET**: 13.6% of truck lanes and 17.4% of auto-diesel lanes cut, store-weighted average −1.02¢ (885 lane-prices). TA: no change (110 sites). Crowd forecast for 11/26 held at 5.7226 (−4.2¢ vs 5.7645) all evening → no visible reaction. n = 1 day.
  - The ~5 PM batch is a candidate for the 6 PM "mystery move" cluster (G4).
  - Our own notes disagree on what AAA diesel is built from: "9,000+ truckstops" vs "120–150K stations" (G3). Decides how much truck-lane prices can matter.
- **Decided (Dan):** limit-order / maker work is parked; keep it as a key finding (M28). Chat 6's job = question the work, fix structure, chart direction.
- **Decided (proposed):** one direction = "what does the 10 AM crowd miss, and when does it learn it?" Order: truckstop scorecard → size the prize (G1) → pin mystery moves to a clock (G4/G2). Other fronts paused until the scorecard has 10 scored days (~Dec 6).
- **Pre-registered test (L3.1):** primary number = correlation of `ts_move_c` with `surprise_10am_c` across scored days; needs ≥10 days to read, 20+ to PASS; compare with `surprise_close_c` to tell "new information" from "timing".
- **Found + fixed:** truckstop feed had a 4-hour hole (last snapshot 9:45 PM ET 11/25 → next 1:55 AM ET 11/26): the hand-started run ended and no new run was queued until the next shift change. Restarted by hand at 1:49 AM; verified the new job saved a snapshot + scorecard within minutes. Watch: if holes repeat between runs, have `truckstops.yml` start its own next run instead of waiting for the relay.
- **Note:** repo must stay PUBLIC for now: free GitHub minutes are unlimited only on public repos and the recorders use ~41,000 min/month (`live_recorder.yml` header).
- **Next:** G1 capacity check once the order book has ~1 week; first scorecard read ~Dec 6.

### 2026-11-26 (1:40 AM) · Maker vs taker on the real trade tape
- **Did:** Scored both sides of every recorded trade (`kalshi_trades`, top-3 lines/day; diesel 29K trades / 59 days, gas 75K / 29 days) against the AAA print. Taker pays ask + 0.07·P·(1−P); maker assumed 0 fee (daily series fee_type "quadratic"; checked 0.0175 maker fee too).
- **Learned:** Being the maker alone is NOT an edge here (opposite of the Bürgi et al. 300K-contract average): diesel makers −2.2%/day-avg (CI −9.3 to +8.4), gas makers −1.3% (CI −2.2 to −0.5). Takers who buy 40–90¢ favorites make money → makers get picked off on that side. But **makers who end up holding the favorite (60–97¢) made +6.2% in diesel, CI +1.4 to +10.4** (70–97¢: +6.7%, CI +1.9 to +10.5). By month: Sep +8.7%, **Oct −4.2%**, Nov +9.9%. Gas: −1.0% (CI −9.1 to +5.9).
- **Decided (candidate):** "Limit-order favorites" = first diesel result with a CI above zero, but regime-dependent (lost in October), gas doesn't confirm, and fills are queue-dependent. Needs: more days, the regime filter, and order-book queue checks before paper trading.

### 2026-11-26 (1:00 AM) · Which time band? Daily has the biggest provable timing ceiling
- **Did:** Measured how much each band's ladder sharpens before settlement, and the "ceiling" return if you knew the later ladder early (bet at early ask + fee when late mid − cost ≥ 5¢).
- **Learned:** Daily: knowing the 10 PM ladder at 10 AM → **+70% per $ diesel (67 days, CI +42 to +105), +79% gas (187 days, CI +59 to +103)**. Weekly: knowing the 1–2-days-out ladder at 5–7 days → +54% diesel (8 events), +41% gas (3). Monthly: +126% diesel on 2 events (driven by crude moves; nobody's model predicts 30 days: our best = "no change"). Share of the move the market already explains: daily ~67%, weekly 5–7d ~76%, monthly ~9–23%.
- **Decided (proposed to Dan):** focus band = **daily**. Model target = predict the **evening ladder** at 10 AM from station/rack data (not tomorrow's AAA directly). Weekly = second venue later; monthly = skip.

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

