# Gaps in our understanding + the one direction (Chat 6 audit, 2026-11-26)

Purpose: question the work so far, list what we still don't understand, and pick one high-impact path.
Read with `research/takeaways/master.csv` (what is true now). Status of each gap is tracked here; update in place.

## Verdict on the work so far

- **Real:** the data foundation, the crowd benchmark (it misses ~0.3¢ at 10 AM, ~0.1–0.17¢ at close), and the
  two-engine frame (worth vs price).
- **Not real yet:** any edge. Every model we built loses to the market at every horizon. The favorites rule is a
  November effect. The one result with a range above zero (limit-order favorites, +6.2%) came after dozens of cuts
  on 59 days, lost in October, and gas does not confirm it. **Parked by Dan 2026-11-26, kept as a key finding (M28).**
- **Pattern to break:** we keep adding fronts (gas twin, weekly/monthly, Nautilus, sample bots, 83 inputs, 13 strategy
  ideas) while the one deciding test only needs time. New fronts feel like progress and are not.

## The gaps (ranked by how much the answer changes what we do)

| # | Gap | Why it matters | How to close it | Status |
|---|---|---|---|---|
| G1 | **Is the prize big enough?** Diesel daily trades ~$52K/day, 63% in 3 lines. We have never sized how many dollars we could put on at the quoted price. | An 8% edge on $100/day is $8/day. If capacity is small, the whole project is a learning hobby, not income. That is fine, but we should know. | Order-book recordings (live since 11/25): dollars available within 1¢ of best price at 10 AM, noon, 6 PM. ~1 week of data. **First read 11/26 (one afternoon, favorites 60–97¢):** median $2.75K at the best price, $3.8K within 2¢; $1K fills clean on 96% of quotes, $5K fits on 54% (average slip ~4¢), $10K on 17% (~11¢). Tape: median $35K/day (top-3 lines), favorite-side taker flow $16K/day, 3 trades ≥ $5K in 60 days. Working cap ≈ $1K per bet. Still needed: 10 AM depth, more days. | ◐ first read |
| G2 | **What window of prices is in AAA's number, and when does it post?** We assume "yesterday's transactions". Not verified. | Decides whether evening truckstop prices on X−1 are *the answer* or only a hint. Sets the whole timing thesis. | `aaa_flips` log (1 week) + truckstop scorecard: which snapshot hour lines up best with next-day AAA. | ◐ recording |
| G3 | **How much of AAA diesel is truckstops at all?** Our own notes disagree: "9,000+ truckstops via fuel cards" (Chat 2) vs "up to 120–150K stations" (Chat 1). Love's + TA = ~700 sites. | If AAA is mostly ordinary gas stations selling auto diesel, truck-lane prices are a side signal and we need a retail source instead. | Re-read the OPIS methodology PDF for diesel specifically; compare Love's *auto* vs *truck* lane as predictors in the scorecard (both recorded). | ⬜ open |
| G4 | **Who are the informed takers?** Takers earn (+3.3%), makers lose (−2.2%). Someone trades on better information, around noon and 6 PM (184 "mystery moves"). | That is exactly the input we are missing. Find their source and we are level with them. | Line up mystery-move timestamps against: OPIS rack times (11 AM, 2 PM, 6 PM), Love's batch reprice (~5 PM ET, seen 11/25), EIA releases. | ⬜ open |
| G5 | **Thin on rising markets.** (Corrected 11/26: diesel does have ~21 strongly rising days, all Aug–Sep; gas has 63.) Kalshi diesel exists since Aug 2026. "Regime matters" has no written label rule and no rising-market test. | Any rule we find may be a falling-market rule. | Write the label rule once (e.g. 10-day AAA trend sign); use gas (270 days, includes a rise) + EIA weekly history as the rising-regime stand-in. | ⬜ open |
| G6 | **Sample size and too many cuts.** ~115 days, and we have tested dozens of slices. One "winner" by luck is expected. | Without a rule, we will fool ourselves again (already did: +8% → +3.3% not proven). | Pre-register: write the test in LOG.md *before* running it; one primary metric; holdout days never touched. Edge target 8–10% needs ~4–5 months. | ◐ rule added to CLAUDE.md §0 |
| G7 | **Exit rules.** The Chat 5 target is "predict the 10 PM ladder at 10 AM", which means selling before settlement and paying the spread twice. Most backtests hold to settlement. | The +70% "ceiling" may shrink a lot after a second spread; evening spreads are ~11¢. | Re-run the ceiling with exit at the 10 PM *bid* instead of settlement/mid. | ⬜ open |
| G8 | **Rack prices** (what stations pay). The link between futures and the pump; we see neither rack nor 10 AM futures history. | Likely the noon mystery move. | Corpay free candidate (Chat 5); Wishlist W1 for HO intraday. | ⬜ open |
| G9 | **Rockets and feathers were never measured.** Open item #2 since day one. | Up-moves pass through faster than down-moves; our formula uses one speed. | EIA weekly since 1994 + daily AAA (ryanfrigo file, Jan 2025→). | ⬜ open |
| G10 | **Calendar effects.** Weekends, holidays (today is Thanksgiving), month-ends, state tax-change dates. Weekend bets were 22/22 with no explanation. | Station repricing and fleet-card volume change on these days; AAA's sample changes. | Flag column in the scorecard once we have 3+ weekends. | ⬜ open |
| G11 | **Edge decay.** Diesel is a thin market; gas (13× busier) shows no favorites edge. A public bot (ryanfrigo) already models AAA. | Whatever we find may shrink as volume grows. | Track volume monthly; treat any thin-market edge as temporary. | ⬜ watch |
| G12 | **Rules of the road.** MNPI rule on paid OPIS-type data; Kalshi's API terms for bots; taxes on winnings. | Could block a data source or the bot itself. | Read Kalshi API/bot terms once; never buy data that is AAA's own input without a check. | ⬜ open |
| G13 | **No alarm when something dies.** Feed health exists, but nobody is told. The truckstop job used to save only at the end of a 5.5-hour run. | Silent gaps in the one dataset that matters. | Fixed 11/26: hourly saves. Still open: a phone alert when a feed goes STALE. | ◐ partly fixed |

## The one direction

**Question:** what does the 10 AM crowd miss, and when during the day does it learn it?

1. **Truckstop scorecard** (running by itself). `research/engine_room/l3_truckstop_scorecard.csv`, one row per day:
   truckstop move vs the crowd's surprise at 10 AM and at close. First read at 10 scored days (~Dec 6), PASS needs 20+.
2. **Size the prize (G1).** Cheap, uses order-book recordings, and decides how much effort this deserves.
3. **Pin the mystery moves to a clock (G4 + G2).** Use the 5-min recordings and the AAA flip log.
4. Only then: models, strategies, Nautilus.

**Paused until step 1 reads out:** new strategy ideas, gas work beyond its daily pull, weekly/monthly ladders, Nautilus
strategies, limit-order favorites (parked, see M28).

## Why there is no large-sample truckstop backtest (asked 2026-11-26)

Truckstop prices are not archived anywhere free: Love's serves them from a live lookup that the Internet Archive does
not capture, and our recorder started 2026-11-25 (7 hourly snapshots when this was written). So a backtest over months
cannot be built from history. What exists instead:

- **Day 1 read (11/25):** Love's cut prices at ~15% of stores in one batch around 5 PM ET (about −6¢ at those stores,
  −1.0¢ averaged over all 885 lane-prices). TA changed nothing. The crowd's forecast for 11/26 sat at 5.7226 (−4.2¢)
  all evening and did not react. One day, so no conclusion; the batch timing is the useful part (see G4).
- **A forward test that grows daily** (the scorecard above). Honest and free; costs only calendar time.
- **Buying history** (OPIS / GasBuddy-type station data) would give a large sample today, but it costs money and
  must clear the MNPI check (G12) first.
