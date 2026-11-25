# Diesel teardown — how Kalshi diesel is priced (2026-11-24)

## Layer 1 — the contract
- Series `KXDIESELD`, "Diesel prices tomorrow". Strikes like Above $6.245 / $6.250 / $6.255 ($0.005 apart).
- Resolves on AAA as the designated source (Public.com mirror of contract terms).
- AAA Gas Prices site "is updated daily by Oil Price Information Service (OPIS)".
- Settled-market check (Kalshi API): KXDIESELD-26NOV24-* expiration_value = 5.7982; AAA site current diesel 11/24/26 = $5.7982. ✅ match.
- Typical daily move: tiny. Example 2026-09-13: $6.2040 vs $6.1602 yesterday (4.4¢ = large day).

## Layer 2 — what builds the retail price (EIA)
- Four components: crude oil cost, refining costs & profits, distribution/marketing/retail costs & profits, taxes.
- Crude ≈ 50% of monthly avg U.S. retail on-highway diesel price 2004–2023 (EIA).
- EIA "Today in Energy" method: crude = Brent spot per gallon; refining (crack) = NY Harbor wholesale diesel − Brent; retail/distribution/taxes = U.S. avg retail − NY Harbor wholesale.
- EIA pump methodology: there is typically a lag between spot price changes and retail price changes, so refining and distribution slices swing; as retail "catches up", the distribution slice grows/shrinks back.
- Taxes: federal 24.4¢/gal; state taxes + fees avg 35.86¢/gal as of Jan 2026.
- EIA Jan 2026 breakdown (diesel $3.52): crude 41%, refining 18%, distribution & marketing 24%, taxes 17% (labels matched by page order; verify).

## Layer 3 — Nov 24, 2026 numbers
| Input | Value | Source |
|---|---|---|
| AAA diesel | $5.7982 | gasprices.aaa.com (11/24/26); = Kalshi settlement |
| AAA yesterday / week / month / year ago | 5.8182 / 5.9848 / 6.3374 / 3.7849 | AAA site |
| Brent | $90.76/bbl | tradingeconomics (Nov 24–25 quote) |
| NY Harbor ULSD | $3.6954/gal | tradingeconomics (CFD/OTC-based, not official) |

| Component | $ | % |
|---|---|---|
| Crude (90.76/42) | 2.1610 | 37.3 |
| Refining (3.6954 − 2.1610) | 1.5344 | 26.5 |
| Delivery + station (5.7982 − 3.6954 − 0.6026) | 1.5002 | 25.9 |
| Taxes (0.244 + 0.3586) | 0.6026 | 10.4 |

**Read:** delivery slice ~$1.50 vs ~$0.84 in Jan 2026 → stations haven't passed through the wholesale drop yet → retail likely keeps sliding (consistent with AAA −18.7¢ over the week).

## Shadow-engine design (independent of Kalshi)
1. Inputs: AAA daily (Kalshi settlements), Brent, ULSD, EIA weekly diesel.
2. Learn lag + asymmetry (rockets up / feathers down).
3. Predict tomorrow's AAA as a distribution.
4. Convert to probability per strike → compare to Kalshi bid/ask → trade signal.

## Sources
- https://www.eia.gov/energyexplained/index.php?page=diesel_prices
- https://www.eia.gov/petroleum/gasdiesel/pump_methodology.php
- https://www.eia.gov/todayinenergy/detail.php?id=68164
- https://www.eia.gov/energyexplained/diesel-fuel/factors-affecting-diesel-prices.php
- https://gasprices.aaa.com/
- https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXDIESELD&status=settled
- https://tradingeconomics.com/commodity/brent-crude-oil · https://tradingeconomics.com/commodity/heating-oil
- https://www.botforkalshi.com/blog/how-to-trade-oil-on-kalshi (lag edge idea)
