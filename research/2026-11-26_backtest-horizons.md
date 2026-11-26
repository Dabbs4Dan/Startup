# Backtest: daily vs weekly vs monthly (diesel + gas), 2026-11-26

Scripts: `tools/backtest_horizons.py` (daily ladders + history), `tools/backtest_horizon_ladders.py` (weekly/monthly ladders).
Data for weekly/monthly: `research/backtests/horizon_ladders/` (pulled on GitHub by `tools/pull_horizon_ladders.py`, workflow `horizon_ladders.yml`).
Raw results: `research/backtests/2026-11-26_horizons.json`, `research/backtests/2026-11-26_horizon_ladders.json`.

Method: models are walk-forward (fit only on targets already known at the snapshot). Bets buy at ask + Kalshi taker fee,
returns clustered by day (daily) or event (weekly/monthly), bootstrap 95% CI. Models: no change, momentum,
wholesale gap (retail − NYH spot vs its 60-day average, + 5-day wholesale move), gap + momentum. Wholesale = EIA NYH spot.

## 1. Daily ladders (bet 10 AM ET day before)

| | Diesel (112 days) | Gas (239 days) |
|---|---|---|
| Market median miss | 0.55¢ | 0.62¢ |
| Best model miss (gap + momentum) | 0.70¢ | 0.84¢ |
| Model bets, edge ≥5–8% | −14% to −52% per $ | −27% to −45% per $ |
| Market bias (median − print) | −0.11¢ (none) | +0.07¢ (none) |

Price check (buy at ask + fee): contracts under 20¢ lose heavily on both (CI excludes 0). Diesel 90–100¢: +4.0% [−0.6, +6.9];
70–80¢: +7.0% [−5.8, +18.8] → not proven. Gas favorites ≈ 0. (Splitting bias by the day's actual direction is a
look-ahead artifact, so it is not reported as a signal.)

## 2. Forecast accuracy on history (no Kalshi prices)

Mean miss, cents. AAA daily prints: diesel since 2024-07, gas since 2023-09. EIA weekly retail since 1994.

| Horizon | Diesel: no change → best | Gas: no change → best |
|---|---|---|
| 1 day (AAA) | 1.70 → 0.89 (gap+mom) | 1.47 → 0.85 (gap+mom) |
| 7 days (AAA) | 12.91 → 9.87 (gap+mom) | 9.29 → 6.77 (gap+mom) |
| 30 days (AAA) | 26.34 → 26.34 (no change best) | 27.99 → 25.45 (gap) |
| 1 week (EIA, 1994+) | 4.28 → 3.34 | 3.53 → 2.73 |
| 4 weeks (EIA, 1994+) | 13.08 → 12.15 | 10.97 → 9.99 |

Our signal beats "no change" by ~20–25% at 1 week, ~5–10% at 1 month.

## 3. Weekly + monthly ladders (only recent history is on the live API)

| Series | Events | Market miss 5–7 days out | Best model miss | Model bets |
|---|---|---|---|---|
| KXDIESELW | 10 (Sep 21 → Nov 23) | **2.52¢** | 7.79¢ | −62% to −66% per $ |
| KXAAAGASW | 10 | **1.84¢** | 5.58¢ | −3% to −15%, CI ±60–90 |
| KXDIESELMON | 2 | 4.83¢ (16–33d: 18.0¢) | worse | −19% to −35% |
| KXAAAGASM | 2 | 5.32¢ (16–33d: 16.9¢) | 17.1¢ at 16–33d | +21% to +39% on 2 events (noise) |

Example: KXDIESELW-26NOV23. On Nov 16 AAA was $5.9989; the ladder's median was $5.8121; the print was $5.8182.
The market priced the steady ~2.7¢/day decline a week ahead. Our models missed by 8¢+.

## Verdict

- The market beats every simple model at every horizon tested. The gap is largest on the weekly (3× more accurate).
- Our models are accurate vs "no change" but far behind the market. Simple momentum/gap features are already priced.
- Weekly/monthly history is thin (10 and 2 events). The monthly gas wins are 2 events: not evidence.
- Edge, if any, needs inputs the market doesn't have yet (truckstops, rack prices, timing), not better curve fitting.

Next: older weekly/monthly markets may be on Kalshi's historical endpoint (not tried yet). Re-run once truckstop and
Corpay rack data have 2–3 weeks.
