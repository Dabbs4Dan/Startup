# AAA diesel formula teardown (2026-11-25)

## How AAA builds the number (layers)
- L0 Kalshi settles on AAA national average diesel for the date.
- L1 National = weighted average of state averages. Test 11/24: simple mean of 51 state diesel averages = $5.8350 vs national $5.7982 (−3.7¢) → national is weighted (likely station count / volume), weights unpublished.
- L2 State average = average of station prices from OPIS: fleet-card swipes (WEX) + direct feeds, "up to 120–130K stations" (AAA). Reflects previous day's transactions (secondary source). Diesel-specific: OPIS truckstop survey 9,000+ sites (Comdata, TCH) — unclear which feeds AAA diesel.
- L3 Station price = rack (terminal wholesale) + freight + taxes + station margin.
- L4 Rack = spot/futures (NY Harbor / Gulf Coast / Chicago / LA) + regional basis.

## Today (11/24 AAA = $5.7982) by certainty
| Piece | $ | Status |
|---|---|---|
| Crude (Brent/42) | 2.1610 | Known (Yahoo/tradingeconomics) |
| Refining (NYH ULSD − crude) | 1.5344 | Partly (NYH futures ≠ regional racks) |
| Taxes (24.4¢ fed + 35.86¢ avg state) | 0.6026 | Partly (state mix depends on unknown weights) |
| Delivery + station margin (leftover) | 1.5002 | Partly (freight + margin + basis mixed) |
| National weighting effect | −3.7¢ vs simple state mean | Unknown weights |

## Backtest of F formula (ΔAAA = a + b·Delivery + c·HO day + d·HO prior 5d), 67 days
| Test | Median miss | ≤0.5¢ | ≤1¢ | Right half-cent bin |
|---|---|---|---|---|
| In-sample | 0.56¢ | 43% | 79% | 19/67 |
| Out-of-sample (train Sep–Oct, test Oct–Nov) | 0.64¢ | 41% | 65% | 8/34 |
| Out-of-sample (reverse) | 0.64¢ | 33% | 70% | 7/33 |
| "No change" baseline | 1.46¢ | | | |
| Kalshi crowd 10 AM | 0.34¢ | | | |
| Kalshi crowd close | 0.11¢ | | | |
Coefficients unstable between halves (delivery −0.054 vs −0.096). Formula captures the trend (2.6× better than no-change) but is ~2× worse than the crowd at 10 AM → not tradeable alone. Nov 25's exact match was partly luck.

## Sub-formulas to solve
1. National weights per state (collect daily state averages ≥ 60 days, solve by regression; or use EIA on-highway diesel sales by state).
2. Timing window: which day's/hours' transactions feed "price as of D".
3. Station margin dynamics (rockets & feathers): up vs down speed.
4. Regional basis: Gulf Coast / Chicago / LA vs NY Harbor.

## Other external sources to dig into next
AAA daily state + metro averages · EIA weekly on-highway diesel by region (PADD) · EIA daily spot (NYH, Gulf Coast, LA CARB ULSD) · OPIS rack averages (paid) + free rack proxies · Pilot / Love's / TA posted truckstop prices · GasBuddy diesel averages · fuel-card indexes (WEX, Comdata, Mudflap) · state fuel-tax change calendar · EIA weekly distillate inventories (Wed) · CME HO intraday (delayed).
