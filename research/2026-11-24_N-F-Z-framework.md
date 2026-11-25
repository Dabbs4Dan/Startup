# N → F → Z backtest framework + "why AAA moved" (2026-11-24)

## The formula (cleaned up from Dan's N / F / Z idea)
For each day d and one chosen line K (e.g. "AAA above $6.310"):
- **N_d** = price of the side we buy at bet time (10 AM ET, day before) = market's probability then.
- **F_d** = settlement: 1 if our side wins (AAA lands on our side of K), else 0.
- **Gap per bet** = F_d − N_d → win pays (1 − N_d), loss costs N_d (+ fee).
- **Z** = win rate = wins ÷ days bet. Profitable only if **Z > average(N + fee)** (break-even).
- **Information gap I_d** = μ_close − μ_bet: how far the market's own forecast moved between our bet and close.
  Our job = find a source S_d, available at bet time, that predicts I_d (what the market learns later in the day).

## The two formulas
**1) Price at bet time (what built N):** market ladder at 10 AM. Its forecast μ_N already includes AAA today,
yesterday's wholesale moves and the delivery slice: regressing the 10 AM miss on those inputs explains only ~5% (R² 0.049) → public fundamentals are already priced in.

**2) The closing number (what built F) — AAA engine fit on 67 days:**
```
AAA_tomorrow − AAA_today ≈ 6.06¢ − 6.72¢ × DeliverySlice($) + 1.83¢ × HO move on bet day($) − 1.30¢ × HO move prior 5 days($)
R² = 0.65 (explains ~65% of daily moves)
```
Plain read: when the delivery slice is $1.50, pump prices fall ~4¢/day; they stop falling near a ~$0.90 slice.
(HO prior-5 sign is unstable — treat as noise until more data.)

## The gap (where we lose)
- Fixed favorite rule (~75¢ line at 10 AM): 38 wins / 10 losses on days with full data.
- Losing days: market's 10 AM forecast missed by 0.80¢ (wins: 0.29¢); market forecast moved 0.73¢ during the day (wins: 0.31¢).
- Wholesale futures moves explain only ~2% of that intraday move (R² 0.021) → the market learns from something else during the day.
- Prime suspect: **station-level retail prices** — the actual input to AAA. OPIS captures ~5M prices/day from up to 150K stations and supplies AAA; OPIS also publishes rack (wholesale-at-terminal) snapshots at 11 AM and 2 PM.

## Next sources to test (leading indicators)
1. GasBuddy / crowd station diesel prices during day E−1.
2. AAA state-level averages (do some states update first?).
3. OPIS rack price snapshots (paid) — check free proxies.
4. EIA weekly diesel (Mondays) as a slow anchor.

Files: `tools/story.py` → table `daily_story`, export `data/exports/daily_story.csv`.
