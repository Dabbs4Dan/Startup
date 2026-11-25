# Reconstructing Kalshi's two "formulas" — N (price at bet) and F (settlement) — 2026-11-24

## Does anyone publish them?
| Question | Answer | Source |
|---|---|---|
| Does Kalshi publish a pricing model for N? | **No.** Prices come from a peer-to-peer order book. Every trade = maker (resting order) × taker. Designated market makers quote two-sided prices for reduced fees; their models are private. | Kalshi "Makers and Takers"; Market Maker Program; CFTC filings |
| Does Kalshi publish the settlement rule for F? | **Partly.** Market rule text: "If the Diesel Price on <date> is above $K, then the market resolves to Yes." Source = AAA (per contract terms on Public.com). An older weekly Kalshi diesel contract used **EIA** weekly data as Source Agency. ⚠️ The daily KXDIESELD rulebook/CFTC filing not yet found. | API rules_primary; CFTC filing rules0426231006 |
| Does AAA/OPIS publish how the AAA diesel number is built? | **Partly.** OPIS diesel = survey of 9,000+ truckstops/travel plazas via fuel cards (Comdata, TCH) + direct chain feeds; Retail Diesel files available 7:30 AM. ⚠️ NOT published: collection time window, station vs volume weighting, how states roll up to national. | OPIS Retail Pricing Methodology (2026-08) |
| Analogous public models? | **Yes — academic "rockets & feathers" error-correction models** (FTC Chesnes 2010; many diesel studies). Main finding: retail moves up fast, down slow; largest asymmetry is rack (terminal wholesale) → retail. | FTC WP302; Kreuz 2018; Totleben 2025 |

## Formula N — the crowd's price at bet time (reconstructed, 51 days)
```
mu_N (crowd's 10 AM forecast) ≈ AAA_today + 0.89 × (yesterday's AAA change)        R² = 0.69
N(YES on line K) ≈ chance that AAA > K, spread around mu_N with typical miss σ_N ≈ 0.35¢
                  + crowd bias layer (long shots overpriced, favorites underpriced)
                  + friction (bid/ask spread, taker fee 0.07·P·(1−P))
```
## Formula F — what AAA actually did (truth)
```
AAA_tomorrow − AAA_today ≈ 0.73 × (yesterday's AAA change)                      R² = 0.66
  … plus fundamentals: −6.7¢ × delivery slice($) + 1.8¢ × HO move on bet day($)  (R² 0.65 alone)
  … plus station-level price changes during the bet day (UNMEASURED — the gap)
mu_C (crowd at close) ≈ AAA_today + 0.77 × yesterday's change; median miss 0.11¢
```
**Key insight:** in the morning the crowd extrapolates momentum too hard (0.89 vs 0.73 actual). By close it has corrected (0.77)
and its miss drops from 0.35¢ → 0.11¢ using information we don't yet have.

## Shared components (inputs to both N and F) and what changes between them
| # | Component | In N? | In F? | Changes between bet & close? | Have data? |
|---|---|---|---|---|---|
| 1 | AAA today (anchor) | ✅ | ✅ | No | ✅ |
| 2 | Momentum (yesterday's change) | ✅ (0.89×) | ✅ (0.73×) | No — but weight differs (overreaction) | ✅ |
| 3 | Delivery slice (retail margin) | partly | ✅ | No | ✅ (futures proxy) |
| 4 | Wholesale futures HO (NY Harbor ULSD) | ✅ | ✅ | **Yes** — settles 2:30 PM ET | ✅ daily close only |
| 5 | Rack (terminal wholesale) prices | ? | ✅ (feeds station prices) | **Yes** — OPIS 11 AM / 2 PM snapshots | ❌ paid (OPIS) |
| 6 | Truckstop pump prices (actual OPIS input) | crowd may watch | ✅ **this IS F** | **Yes** — all day | ❌ → research Pilot/Love's/TA posted prices, GasBuddy |
| 7 | Taxes | ✅ | ✅ | No | ✅ constant |
| 8 | Crowd layer: bias, spread, fees, market makers | ✅ only | ❌ | Yes (spreads narrow midday) | ✅ candles |

## Flags for deeper research
1. ⚠️ Daily KXDIESELD CFTC rulebook (exact source + time-of-day definition of "Diesel Price on <date>").
2. ⚠️ OPIS collection window + weighting (which hours' prices make "tomorrow's" AAA number).
3. ⚠️ Free real-time truckstop diesel prices (Pilot Flying J, Love's, TA publish per-station prices online) → could be the missing #6.
4. ⚠️ Rack price proxy (free) for #5.
5. ⚠️ Longer history (68 days, one falling regime).
