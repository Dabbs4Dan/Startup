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

**Free AAA history hack:** Kalshi's settled KXDIESELD markets carry `expiration_value` = the exact AAA number (verified 5.7982 = AAA site).

---

## 6. Open questions / next steps

| # | Item | Status |
|---|---|---|
| 1 | Confirm backfill ran on GitHub; check row counts | ✅ 2026-11-24 |
| 2 | Lag study: how many days for a ULSD move to reach AAA? Up vs. down speed (rockets & feathers)? | ⬜ |
| 3 | Find the exact time AAA posts each day and when Kalshi's market opens/closes | ⬜ |
| 4 | Turn the forecast into odds per strike; compare with Kalshi prices (backtest on history) | ⬜ |
| 5 | Add gas (KXAAAGASD) to the same table once diesel works | ⬜ |
| 6 | Find a real-time / official ULSD source (manual Nov 24 values came from tradingeconomics CFDs; Yahoo HO=F futures used for history) | ⬜ |
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
