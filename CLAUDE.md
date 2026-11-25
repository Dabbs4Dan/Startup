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

---

## 4. Where everything lives (the map)

| What | Path | Notes |
|---|---|---|
| **Main database** | `data/kalshi_twins.db` | SQLite. The one place for data. |
| Schema (all tables + views) | `data/schema.sql` | Read this to know every column. |
| **Easy-view tables** | `data/exports/*.csv` | Auto-exported copies. GitHub shows them as tables. |
| Build/refresh DB | `tools/build_db.py` | Creates tables, seeds hand-verified rows. Safe to re-run. |
| Pull history | `tools/backfill.py` | Kalshi + Yahoo futures (+FRED backup). Fills blanks only, never overwrites. |
| Auto-runner | `.github/workflows/backfill.yml` | Static now. Uncomment `schedule` to go live daily. |
| Deep research notes | `research/` | One dated file per topic. |
| This brain | `CLAUDE.md` | Log at the bottom, newest first. |

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

### Static → live (plug & play)

1. Open `.github/workflows/backfill.yml`, uncomment the 2 `schedule` lines, push. Done: daily at 6:17 AM ET.
2. To add a market (e.g. gas): add its series ticker to `SERIES` in `tools/backfill.py`.

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
Strikes are $0.005 apart. Market opens ~10 PM ET the night before.

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

**Free AAA history hack:** Kalshi's settled KXDIESELD markets carry `expiration_value` = the exact AAA number (verified 5.7982 = AAA site).

---

## 6. Open questions / next steps

| # | Item | Status |
|---|---|---|
| 1 | Confirm backfill ran on GitHub; check row counts | ✅ 2026-11-24 |
| 2 | Lag study: how many days for a ULSD move to reach AAA? Up vs. down speed (rockets & feathers)? | ⬜ |
| 3 | Find the exact time AAA posts each day (Kalshi open/close ✅: 8 AM → 11:59 PM ET day before) | ◐ |
| 4 | Turn the forecast into odds per strike; compare with Kalshi prices (backtest on history) | ⬜ |
| 5 | Add gas (KXAAAGASD) to the same table once diesel works | ⬜ |
| 6 | Find a real-time / official ULSD source (manual Nov 24 values came from tradingeconomics CFDs; Yahoo HO=F futures used for history) | ⬜ |
| 8 | Minute-level candles for near-money strikes (hourly done) | ⬜ |
| 9 | Edge test: does our engine's morning forecast beat the market's morning ladder? | ⬜ |
| 7 | Longer AAA history: Kalshi only goes back to 2026-09-18. FRED (EIA weekly diesel) times out from GitHub runners; try EIA direct or run from Mac | ⬜ |

---

## 7. Log (newest first — add a new dated block on top, never edit old ones)

Template:
```
### YYYY-MM-DD · short title
- **Did:** …
- **Learned:** …
- **Decided:** …
- **Next:** …
```

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

## 8. Related places

- Google Drive "Kalshi Twins – Trading Brain" (Dan's personal Google account) — human-level tracking, earlier pairs-trading research (SPY vs US Large Cap perps).
- Mac folder `~/Documents/kalshi-twins` — earlier Claude Code home base (Kalshi demo API key lives there, never commit keys).
- Kalshi demo: https://demo.kalshi.co (API: external-api.demo.kalshi.co).
