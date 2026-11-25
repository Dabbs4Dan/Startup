# Formula registry + master-panel column plan (2026-11-25)

## Table 1 — Formulas (status: ✅ working · ◐ partial · ⬜ unsolved)
| # | Name | Formula | Status |
|---|---|---|---|
| 1 | AAA price build | AAA = Brent/42 + (ULSD − Brent/42) + Taxes + Delivery | ✅ |
| 2 | Delivery slice | Delivery = AAA − ULSD − $0.6026 | ✅ |
| 3 | F: tomorrow's AAA | AAA_tmrw = AAA − 6.72%×(Delivery − $0.90) + 1.83¢×ΔHO_today − 1.30¢×ΔHO_5d + station surprise | ◐ |
| 4 | Momentum (crowd vs truth) | Crowd μ_10AM ≈ AAA + 0.89×ΔAAA_yday · Truth ≈ AAA + 0.73×ΔAAA_yday | ◐ |
| 5 | N: Kalshi line price | P(YES at K) = 1 − Φ((K − μ)/σ) + bias + spread + fee | ◐ |
| 6 | Half-cent box chance | P(box) = P(>low) − P(>high) · crowd forecast = K where P = 50% | ✅ |
| 7 | Kalshi fee | fee = roundup(0.07 × C × P × (1−P)) (maker 0.0175×) | ✅ |
| 8 | Payout multiple | Payout per $1 = 1 ÷ (P + fee) | ✅ |
| 9 | Break-even win rate | Need win rate > c = P + fee | ✅ |
| 10 | Risk / P&L calculator | P&L = (B/n)×[(n−L)(1−c)/c − L] · max losses L* = n(1−c) · wins per loss = c/(1−c) · chance negative = P(Binomial(n,1−q) > L*) | ✅ |
| 11 | Goldilocks zone | Bet favorites 75¢ ≤ P < 85¢ at 10 AM; edge = win rate − c (held Sep–Nov, failed Aug–Sep rise) | ◐ |
| 12 | Liquidity filter | Keep line if volume > 0 AND spread ≤ 10¢ AND 3% ≤ P ≤ 97% | ✅ |
| 13 | Distance score | z = |K − μ| ÷ σ | ✅ |
| 14 | Info gap / miss | Info gap = μ_close − μ_bet · miss = AAA_actual − μ | ✅ |
| 15 | N→F→Z | Profit only if Z (win rate) > average(N + fee) | ✅ |
| 16 | National roll-up | AAA_national = Σ w_state × State_avg (weights unknown; plain mean off by 3.7¢) | ⬜ |
| 17 | Station price | Station = Rack + Freight + State tax + Margin | ⬜ |
| 18 | Regime detector | Rising ("rockets") vs falling ("feathers") multi-day trend → switch rules on/off | ⬜ |

## Table 2 — Master-panel columns (ease 1 = easy, 2 = tough, 3 = real work; Parent = has sub-parts)
See chat reply 2026-11-25 3:05 AM; same list below.
| Column | Ease | Parent? | Source |
|---|---|---|---|
| AAA national diesel today | 1 | No | AAA site / Kalshi settlement |
| AAA 1-day change | 1 | No | computed |
| AAA 5/10/20-day trend (regime) | 1 | No | computed |
| Day of week / weekend / holiday flag | 1 | No | calendar |
| AAA state diesel averages (51) | 2 | Yes | AAA state page |
| AAA metro averages | 2 | Yes | AAA metro pages |
| AAA regular gas national (sister signal) | 1 | No | AAA / Kalshi gas settlements |
| AAA post time (flip time) | 2 | No | AAA site tracker |
| NY Harbor ULSD futures (HO) daily close | 1 | No | Yahoo HO=F |
| HO 1-day / 5-day change | 1 | No | computed |
| HO price at bet time / 2:30 PM settle | 2 | No | delayed futures feed |
| Brent crude | 1 | No | Yahoo BZ=F |
| WTI crude | 1 | No | Yahoo CL=F |
| RBOB gasoline futures | 1 | No | Yahoo RB=F |
| Crack spread (refining slice) | 1 | No | computed |
| Delivery slice | 1 | No | computed |
| Gulf Coast ULSD spot | 2 | No | EIA / FRED |
| Chicago & LA (CARB) ULSD spot | 2 | Yes | EIA |
| Rack prices by terminal | 3 | Yes | OPIS (paid; MNPI check) |
| Truckstop posted prices (Pilot, Love's, TA) | 3 | Yes | chain websites (ToS check) |
| GasBuddy diesel average | 2 | No | GasBuddy |
| Cash vs credit price gap | 2 | No | chain websites |
| Station margin | 3 | Yes | computed (needs rack + pump) |
| Federal excise tax | 1 | No | constant 24.4¢ |
| State taxes + change calendar | 2 | Yes | EIA / state revenue sites |
| EIA weekly retail diesel (Mon) | 1 | No | EIA |
| EIA weekly distillate inventories (Wed) | 1 | No | EIA |
| Refinery utilization / outages | 2 | Yes | EIA / news |
| Season / heating-oil demand | 2 | No | calendar, EIA |
| Freight / trucking demand index | 3 | Yes | ATA, Cass |
| Supply shocks (pipelines, hurricanes) | 3 | Yes | news |
| U.S. dollar index | 1 | No | Yahoo DX-Y.NYB |
| Model F forecast | 1 | Yes | computed (formula 3) |
| Model gap vs line | 1 | No | computed |
| Regime label | 1 | No | computed (formula 18) |
| Strike ladder (21 lines) | 1 | Yes | Kalshi API |
| Settlement value + result | 1 | No | Kalshi API |
| Daily volume + open interest per line | 1 | No | Kalshi API |
| Open / close / early-close times | 1 | No | Kalshi API |
| **Intraday (Kalshi)** | | | |
| YES bid / ask per line (hourly) | 1 | No | Kalshi candlesticks |
| YES bid / ask per line (minute) | 2 | No | Kalshi candlesticks (1-min) |
| YES/NO % split (mid) | 1 | No | computed |
| Spread per line | 1 | No | computed |
| Crowd forecast μ (50% crossing) | 1 | No | computed |
| Crowd wiggle σ | 1 | No | computed |
| Half-cent box chances | 1 | Yes | computed |
| Volume per hour | 1 | No | Kalshi candlesticks |
| Open interest change per hour | 1 | No | Kalshi candlesticks |
| Trades / fills (count, size, side) | 2 | Yes | Kalshi trades endpoint |
| Order book depth (each price level) | 2 | Yes | Kalshi orderbook (must record live) |
| Price jumps vs news timestamps | 2 | Yes | computed |
| Maker vs taker flow | 3 | Yes | not fully public |
