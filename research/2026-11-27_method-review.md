# Method review: how a working prediction-market algo builder would run this (Chat 7, 2026-11-27)

Asked by Dan: step back, pull in outside guidance, and check that the build order is what a real algo tester
would follow. Everything under "Proposed" is Claude's proposal, not a decision, until Dan says so.

## 1. Verdict in three lines

- **The plumbing is at a professional standard.** One-way data flow, one master table, the no-peeking rule, join
  checks (spine), costs included, tests written before they run. Most hobby projects never get this far.
- **The research order is the jumbled part.** Three different kinds of edge are being chased in the same tables,
  the six markets have never been ranked on one common ruler, and the holdout has been looked at more than once.
- **No new data is needed to fix this.** It is mostly a re-labelling and a short new scorecard on top of what exists.

## 2. What the outside sources say (and what it means for us)

| Source | What it found | What it means here |
|---|---|---|
| Bürgi, Deng, Whelan, "Makers and Takers: The Economics of the Kalshi Prediction Market" (2025–26, 300K+ contracts) | Cheap contracts lose a lot after fees; expensive ones earn a small positive return. Makers do better than takers. Prices get more accurate near the close. | Our M60 (underdogs lose 33–58%) and M10/M57 (crowd sharpens through the day) are not special to fuel. They are the known Kalshi pattern. That is a sanity check passed, not an edge found. |
| Becker, "The Microstructure of Wealth Transfer in Prediction Markets" (72.1M Kalshi trades, Jun 2021–Nov 2025) | Takers lose about 1.1% per trade, makers gain it. Takers over-buy Yes; makers buying No do slightly better. The maker-taker gap is smallest in Finance (0.17 pts) and largest in media / world events (7+ pts). Before 2024 takers were the winners; pros arrived as volume grew. | (a) Our M63 (gas crowd leans high, No-favorites win more than priced) is the platform-wide Yes lean. (b) Finance-type markets are the tightest on the whole exchange, so expect small structural edges in fuel. (c) Our diesel tape shows takers winning (G4), the pre-2024 pattern: a thin market where informed takers still beat the makers. Worth its own test. |
| `Jon-Becker/prediction-market-analysis` (GitHub, MIT, about 36 GiB, Parquet) | Public data set of Kalshi + Polymarket markets and trades, plus one-script-per-analysis layout. | Candidate free source for the older gas trade tape (step 2d in CLAUDE.md §6). **Assumed, not checked:** that it holds our gas series and that this workspace can download it. Its measures (mispricing = win rate − price; return per $ risked; split by maker / taker) are the standard ruler to copy. |
| `evan-kolberg/prediction-market-backtesting` (GitHub, built on NautilusTrader) | Models fees, slippage, queue position for resting orders, latency. Polymarket runs; Kalshi side is not runnable because nobody has historical order books. | Confirms the engine choice. Confirms that **our own order-book recording is the scarce asset**: resting-order (maker) results cannot be trusted on history before 11/25. Its list (fees, slippage, queue, latency, limits) is the checklist for our execution layer. |
| Bailey and López de Prado, "The Deflated Sharpe Ratio" / backtest-overfitting papers | The more versions you try on the same data, the better the best one looks by luck alone. Count every trial and mark the winner down for it. | We have run about 3,300 cuts (1,980 deep scan + 1,328 slices) on at most 542 events. A count of trials has to sit next to every "lead". |
| QuantConnect research guide | Start from a cause-and-effect hypothesis; do not pick the best factors and re-test on the same period; walk forward. | Each ratio we build needs a one-line "why would this move AAA or the crowd" before it is tested. |
| Sports-betting practice: closing line value (CLV) | Pros grade a bet by whether the price later moved their way by the close, not by win or loss. Far less noisy. | Our close is 98–99% of the answer (M57). So "did the price move our way by the close" can grade an idea in weeks where win/loss needs many months. |
| Kalshi liquidity programs (help centre + CFTC filings) | Designated market makers get fee breaks; a separate program pays members for resting orders. | The market maker's quotes are partly shaped by quoting duties and rewards, not only by a pricing formula. **Not checked:** whether the fuel series are in a reward program. |

## 3. Where the project stands against that (verified in the repo this session)

1. **Events, not rows, are the sample.** 23,757 slice rows sit on 542 events: gas daily 271, gas weekly 140
   (only 45 with a real ladder, M45), diesel daily 117, gas monthly 34, diesel weekly 16, diesel monthly 3.
2. **Rough size needed.** For a favorite near 75¢, telling a 5-point edge from luck takes about 300 independent
   events; a 3-point edge about 830. So gas daily's +3.3 points (M63) is inside the noise today, and three of the
   six markets cannot prove or kill anything for a year or more.
3. **The holdout is used up.** `deep_scan.py` and `slice_scan.py` both hold out the same last 40% of events, and
   the ledger was read early vs late as well. Days after 11/27 are the only clean test left.
4. **Three kinds of edge are mixed in one set of tables:**
   - **A. Structure:** the crowd's habits (long shots and Yes overpriced). M28, M60, M63, M64.
   - **B. Information:** knowing the AAA number sooner (truckstops, live station prices). M22, M30, M55–M57.
   - **C. Path:** the price route between time slots (engine E2). M36, the planned `paths` table.
   They need different data, different tests and different pass marks.
5. **The market-maker copy is scored on the wrong ruler for edge.** "How close are we to their price" (6–16 points
   off) matters for engine E2. For engine E1 the question is "does our number beat their number at predicting the
   result". On that ruler we know the answer today: no (0.6–0.7¢ vs 0.3–0.4¢, M55).
6. **Fills.** Old quotes have no size, the engine cannot open No positions yet, and settlement payout is added
   after the run (nautilus README gaps 3, 4, 7). Taker tests at the recorded ask are sound. Limit-order results
   (M28) are not, before 11/25.
7. **Prize size** is about $1K per bet (G1). Any plan should be honest that this caps the dollars.

## 4. Proposed: the build ladder (each rung has a pass mark; no skipping)

| Rung | What | Mostly exists? | Pass mark |
|---|---|---|---|
| 1. Lock the canvas | Fix the 3 builder bugs, stamp the master with a version, run the spine checks automatically after every rebuild | Yes | Spine 100%, every result names the master version it read |
| 2. Market scorecard (the common ruler) | One row per market: events, win rate vs price by band, cost to trade (spread + fee), dollars at the best price, maker vs taker result, crowd miss by time slot | Pieces exist (ledger, G1, M10, G4); never side by side | A ranked list of the six; test on the top two, keep recording all six |
| 3. Guard rails | Trial ledger (every test ever run, counted), baselines every idea must beat (the crowd's own price; "no change"; "fade long shots"), forward vault = days after 11/27 | Rule exists; ledger and vault do not | No result is called a lead without its trial count and a baseline |
| 4. Track A: structure | Taker tests first. Maker (limit order) tests only on recorded order books. Forward paper test of the best pre-written rule | Ledger + scan built | Positive after costs on vault days, 30+ events |
| 5. Track B: information | Truckstop scorecard keeps running. Our fair-value number scored against the crowd at each time slot, plus CLV | Scorecard running | Beats the crowd's miss at any one slot on vault days |
| 6. Track C: path (E2) | `paths` table from recorded books; the market-maker copy is scored here | Planned | 30+ days of recorded book first |
| 7. Engine | Nautilus: paper, then tiny live | Installed | Only for a rule that passed rung 4, 5 or 6 |

## 5. Proposed: the standard measures (the ruler)

1. **Calibration gap:** win rate minus price, by price band (have: favorite ledger).
2. **Return per $ after fees,** averaged per event first, then across events (have).
3. **Skill vs the crowd:** our miss divided by the crowd's miss at the same time slot (have in cents; make it one number).
4. **CLV:** did the price move our way by the close (new; cheap; from the master).
5. **Cost hurdle:** spread + fee per bet. **Capacity:** dollars at the best price (have for diesel; extend to gas).
6. **Maker vs taker result** from the trade tape (have for diesel, G4; extend).
7. **Line position:** (line − crowd center) ÷ crowd width, and hours to settle, so lines compare across markets.
8. **Honesty numbers on every result:** events (not rows), trials run so far, which master version.

Inputs to build first, each with a cause: pump margin (AAA − wholesale − tax), wholesale change over 1 / 3 / 5 / 10
days with up and down split (rockets and feathers, G9), recent AAA momentum, day of week and holiday, the crowd's
own state (center, width, lean, spread, taker Yes vs No dollars).

## 6. Proposed: clean-system changes (each names what it replaces)

- Trial ledger file replaces the superseded Testing table / tab.
- Market scorecard replaces "Backtest – horizons" and feeds the Bricks tab.
- Track tag (A / B / C) is one new column in `master.csv`, not a new file.
- Legacy scripts named in CLAUDE.md §6 move to `tools/legacy/` (no workflow uses them; check before moving).
- Stale-feed alert (G13) closes the "catalog stale since 11/25" oddity.

## 7. Where this differs from decisions already made (Dan to rule)

- "All six equally" (11/27): proposed change to **record all six, test on the top two** from the scorecard.
- Build order L2 → L3 → L4 → own formula: proposed to put the **market scorecard and guard rails before more L3
  ratios**, and to score L4 on "beats their price" for E1.
- North star (§3b) stays. The market maker's price remains the thing to explain; this only changes how we grade it.

## Sources

- https://cepr.org/voxeu/columns/economics-kalshi-prediction-market
- https://www.ifo.de/en/cesifo/publications/2026/working-paper/makers-and-takers-economics-kalshi-prediction-market
- https://jbecker.dev/research/prediction-market-microstructure
- https://github.com/Jon-Becker/prediction-market-analysis
- https://github.com/evan-kolberg/prediction-market-backtesting
- https://papers.ssrn.com/abstract=2460551
- https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/research-guide
- https://blockworks.co/news/predicting-trading-insights
- https://help.kalshi.com/en/articles/13823851
