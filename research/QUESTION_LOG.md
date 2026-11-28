# Question log (quick questions on data we already hold)

Home of the `test` command. One question, one short answer, date and time stamped, newest first.
This is NOT a strategy test. It is Dan probing the data. A finding here is a **look-back**: it becomes a lead only
after it also holds on new days. Dan's reading copy: Google Sheet "Kalshi – Question Log" (same rows, newest on top). Sheet only, no Google Doc (Dan, 2026-11-28).

**How an answer is made:** `python3 tools/ask.py` on `data/lake/master/slices.csv.gz` (the 3 busiest lines of each
event at each time slot). The event is the sample. Cost = ask + taker fee. Noise = 2 standard errors across events.

**Guard rails (kept here, nowhere else):**
- **Trial count:** about 3,300 cuts were run before this log (deep scan 1,980 + slice scan 1,328). Each question adds 1; the bet grid (Q004) added its 2,424 readable cells. **Count now: 5,950.**
- **Baselines any idea must beat:** (1) the crowd's own price, (2) "no change", (3) "skip the long shots".
- **Vault:** events that settle after 2026-11-27 have never been looked at. Only they can turn a look-back into a lead.
- **Read of a result:** "edge beyond noise" = bigger than its noise band; "inside noise" = luck not ruled out; under 30 events = too few.

---

### Q009 · 2026-11-28 03:15 AM ET · Hourly futures: can we get them, and does Q008 hold hour by hour?
- **Asked by Dan:** "why do we have futures once a day? How do they see many rises a day?" and "how can we backtest or retrieve the intraday futures?"
- **Data answer:** we were never limited to the days we recorded. The free hourly history existed; our pull was blocked by a bug (browser-like user agent). Fixed 11/28: hourly gas (RBOB) and diesel (HO) futures since Jul 8 2024, 5-minute bars since Sep 18 2026, refreshed daily (`data/lake/history/yahoo_*`).
- **Same hours:** the futures move in the same hours as a crowd rise does not tell right from wrong. Gas daily rises: futures up in those hours -8.2 (noise 10.0), futures down -5.2 (noise 10.9).
- **Yesterday's futures, checked with this second source (previous trading day, 2 PM to 2 PM):** gas daily holds and is stronger. Rises after futures rose (67 days): crowd up 0.40c, truth 0.60c, with the rise +1.6. Rises after futures did not rise (64 days): crowd up 0.36c, truth 0.21c, with -19.9 (noise 9.4), against +14.2. Drops after futures fell (70 days): with the drop +11.3 (noise 6.9).
- **Diesel daily does NOT hold with this source:** rises after futures rose -11.3 (noise 15.4, 24 days), after futures did not rise -9.1 (noise 11.3, 29 days). Q008's diesel split is unproven.
- **Worst gas case:** yesterday's futures not up but today's futures up so far (19 days): with the rise -31.6 (noise 19.8). Reads as the crowd chasing a same-day jump that has not reached the pumps yet. Small sample.
- **Catch:** look-back; about 40 more cuts; groups of 8 to 70 days. Front-month futures roll once a month, which can add a false jump on roll days.
- **Data:** `python3 tools/swing_hourly.py`. Master m20261128-0345b9a1.

### Q008 · 2026-11-28 03:02 AM ET · Why are the big rises wrong? What was happening on those days?
- **Asked by Dan:** "Yes why rises" (follow-up to Q007).
- **Answer:** a big crowd rise is right when wholesale futures rose the day before, and wrong when they did not. Rises with no wholesale reason behind them are the crowd chasing.
- **Gas daily, big rises (131 days):** futures rose the day before (44 days): crowd moved up 0.43c, truth ended 0.71c up, AAA rose the next day 69% of the time, betting with the rise +2.9 (noise 10.2). Futures did not rise (87 days): crowd up 0.35c, truth only 0.24c, AAA rose 44% of the time, betting with the rise -14.9 (noise 8.4), betting against it +9.2.
- **Diesel daily, big rises (52 days):** futures rose (20 days): crowd up 0.60c, truth 0.97c, AAA rose 83%, with +2.7. Futures did not rise (35 days): with -16.7 (noise 12.2), against +11.3.
- **Worst case:** gas daily, rising 10-day trend and no futures rise (31 days): crowd up 0.41c, truth 0.09c, with -30.4 (noise 12.0), against +24.3.
- **Late night (10 PM and close) rises with no futures rise:** gas daily -19.3 (noise 12.9, 45 nights); diesel daily -22.6 (noise 18.3, 18 nights).
- **Drops, for balance:** gas daily drops after futures fell (47 days): crowd down 0.36c, truth 0.59c down, betting with the drop +11.8 (noise 7.5). The crowd does not go far enough on backed drops.
- **Not the cause:** whether AAA itself rose that morning (with-the-rise edge -5.5 vs -5.7 in gas).
- **Why this is usable:** the futures number is the previous trading day's close, known before the market opens. It is a fundamental check on a crowd move, which fits the plan (forecast picks the bet, leans check it).
- **Catch:** look-back; about 70 more cuts read; groups are 20 to 87 days. "Did not rise" includes weekends and holidays when futures did not trade.
- **Data:** `python3 tools/swing_why.py` (reads `swing_cohort.csv`, the master, `inputs_daily.csv`). Master m20261128-0345b9a1.

### Q007 · 2026-11-28 02:59 AM ET · The biggest intraday price swings on the busy lines: is there a pattern?
- **Asked by Dan:** "look into instances in the biggest spread swing across the 6 topics and 3 most liquid markets whether yes no fav not favorite, analyze a cohort of just the biggest spread swings intraday and identify some sort of trend or pattern." Read as: the biggest price moves of a line between two time slots.
- **Cohort:** a busy line's YES price moving 15+ points between neighboring time slots, spread 10c or less at both ends. 2,237 swings: gas daily 707 (190 of 251 days had one), gas weekly 670, gas monthly 338, diesel daily 235 (76 of 109 days), diesel weekly 219, diesel monthly 68.
- **Pattern 1, after a big swing YES is left too high, whichever way it moved.** Gas daily, bets priced 50-95c: buying YES on calm lines -3.6; after a big rise -7.1; after a big drop -18.0 (noise 12.6, 58 events). Buying NO: calm +1.1; after a rise +3.5; after a drop +5.1 (noise 5.9, 124 events). The crowd does not drop far enough on down news and goes a bit too far on up news.
- **Pattern 2, big rises are the wrong ones.** Betting with a big rise lost in every market: gas daily -7.9 (noise 6.6), gas weekly -15.0 (9.5), gas monthly -16.4 (13.2), diesel daily -9.1 (9.3). Betting with a big drop: gas daily +4.5, gas weekly +3.5, gas monthly +4.5, diesel daily +1.7 (all inside noise). Worst case: a big rise during a rising 10-day trend in gas daily, -17.8 (noise 9.8, 55 events).
- **Pattern 3, time of day.** Midday swings were right (gas daily noon to 3 PM +5.8, 3 PM to 6 PM +6.8; diesel daily noon to 3 PM +13.5, noise 7.7, 21 events). The last two hours were wrong: 10 PM to close swings were about 80% upward, and betting against them made +15 points in gas daily (33 nights) and +11 in diesel daily (15 nights). Small samples.
- **Pattern 4, no follow-through.** After a big swing the price moved only about 1 more point in the same direction by the next slot. There is nothing to chase.
- **Pattern 5, diesel.** Diesel's favorite edge sits on calm lines (buying YES 50-95c on calm lines +6.7, noise 5.1, 76 events) and is gone after a swing.
- **Catch:** look-back; about 80 cuts were read here; most single cells are inside their noise. What repeats across markets is the direction (rises overshoot, drops fall short). Quotes carry no size.
- **Data:** `python3 tools/swing_cohort.py` -> `research/engine_room/swing_cohort.csv` (`lab.swing_cohort`). Master m20261128-0345b9a1.

### Q006 · 2026-11-28 02:56 AM ET · Is betting in the morning less accurate or less profitable than in the evening? (re-run of an earlier finding)
- **Asked by Dan:** "There was a test we saw that betting in morning was less profitable or accurate than evening? I'd like to also recreate that just for the sake of logging - or perhaps now the results will be different."
- **Answer:** accuracy: yes, in both daily markets the crowd gets sharper all day. Profit: yes in gas, no in diesel.
- **Accuracy (median crowd miss, cents):** gas daily: open 0.42, 10 AM 0.34, noon 0.35, 3 PM 0.27, 6 PM 0.21, 10 PM 0.20, close 0.19. Diesel daily: open 0.30, 10 AM 0.37, noon 0.30, 3 PM 0.28, 6 PM 0.24, 10 PM 0.23, close 0.19.
- **Profit ($100 a day on every favorite priced 50c+, per day):** gas daily: open -$4.38, 10 AM -$2.90, noon -$2.35, 3 PM -$3.04, 6 PM +$1.09, 10 PM +$1.25, close +$1.33. Diesel daily: open +$5.75, 10 AM +$3.98, noon +$2.46, 3 PM +$5.23, 6 PM +$7.90, 10 PM +$5.72, close -$1.15.
- **Edge in points (noise about 3 at every slot):** gas daily -3.1, -1.9, -1.7, -1.9, +1.1, +0.9, +1.1. Diesel daily +4.4, +3.2, +2.4, +3.6, +6.0, +4.6, -0.6.
- **Same or different from before:** same shape. Earlier notes said 0.3-0.55c at 10 AM (M10); now 0.34-0.37c. One difference: the close miss is 0.19c here against 0.12-0.13c in M57, which used a different center measure. Not chased yet.
- **Catch:** look-back. In gas no single slot is beyond its noise; the morning-to-evening swing of about 4 points is the finding. Diesel is 66-101 events from one falling stretch.
- **Data:** `tools/ask.py --min 50 --slot <slot>` and the crowd center in `slices.csv.gz`. Master m20261128-0345b9a1.

### Q005 · 2026-11-28 02:47 AM ET · Gas daily NO-favorite late evening: what are we buying, why does it win, and what would it have paid?
- **Asked by Dan:** "when a no trend is No, what are we buying here? ... WHY is that favorable? ... Is a surface level edge just an opportunity to buy on the best intraday spread change? Is it to buy on signals that display certainty on confidence bounds?"
- **What is bought:** one NO contract on a line such as "gas above $4.370 tomorrow?". Example, Oct 10 2026 at 10 PM: today's AAA $4.3718, crowd center $4.3674, NO cost 86c (86.8c with fee), AAA came in at $4.3669, NO paid $1. It is one side bought outright and held to the morning, not a spread.
- **Why it wins (level, not spread, not width):** late in the evening the crowd's whole ladder sits a little too high: +0.05c at 10 PM (2 standard errors), +0.10c at the close (4 standard errors), nothing at 3 PM. Lines are half a cent apart and the crowd's range is about 0.45c, so a tenth of a cent is worth about 9 points on the nearest lines. NO-favorites win more than priced and YES-favorites lose more than priced: that is a shifted level, not a wrong width. Spreads are not better at night (3.2 points vs 2.7 at 6 PM).
- **Where the lean comes from:** when the crowd moved down between 3 PM and the close it was still 0.14c too high (84 days); when it moved up it ended 0.09c too high (100 days). Gas fell on 62% of days. The same lines' NO price drops about 2c between 10 PM and the close (82.6c to 80.7c) while NO wins 90%.
- **In dollars ($100 a night, NO-favorites priced 50-97c, 2026):** 10 PM: 200 nights, won 85.5% of nights, +$1,592 total, +$7.96 a night (noise 5.03), average win +$21, average loss -$69, worst night -$100, deepest dip -$347, November -$137. 6 PM: +$4.79 a night (noise 5.77, inside noise). Close: +$10.96 a night (upper bound; the last second cannot be traded). The same rule on YES at 10 PM lost $960.
- **Catch:** look-back on scanned days; no size data for late quotes; one loss wipes out about 3 wins; one season only (Mar-Nov 2026).
- **Data:** `slices.csv.gz` + `ladder_snapshots.csv.gz`, gas daily 2026. Master m20261128-0345b9a1.

### Q004 · 2026-11-28 02:40 AM ET · The big grid: every YES / NO price, every time slot, 3 busiest lines, all 6 markets. Do we even have the data for it?
- **Asked by Dan:** "How can we test all of the % of yes no and across all times of the open market across the 6 things we're trading, within the 3 highest liquidity market options?" and "do we have enough DATA to really test this?"
- **Answer on data:** enough to map the big patterns in three markets, not enough to prove small edges in narrow cells, and nothing at all for diesel weekly and monthly.
- **Data numbers:** 10,748 cells have data; 2,424 (23%) have 30+ events; only 233 (2%) can tell a 3-point edge from luck. A typical readable cell only sees edges bigger than about 6 points. Readable cells: gas daily 923, gas weekly 767, diesel daily 562, gas monthly 172, diesel weekly 0, diesel monthly 0. Gas daily's ladders are really Mar-Nov 2026 (245 of 253 events).
- **Answer on the grid:** the clear pattern is on the losing side. Buying YES is overpriced in gas at almost every price (gas daily -5 to -17 points between 25c and 90c; gas weekly -8 to -25). Long shots lose in all three markets. Buying NO is fair to positive.
- **Luck check (1,000 replays of a fair market):** losers: 276 cells vs 52 by luck (only 2 replays in 1,000 had as many), so the losing pattern is real. Winners: 77 cells vs 44 by luck (131 replays in 1,000 had as many), so winners as a group are not beyond luck.
- **One candidate worth a forward test:** gas daily, buy the NO-favorite late in the evening. At the close: 209 events, wins 92.0% vs 84.0% needed (+8.1, noise 3.3). At 10 PM, NO at 75c+: +5.6 on 183 events. Positive in 7 of 8 full months (Apr-Oct 2026), negative in Nov (-6.3, 18 events).
- **Catch:** look-back on days already scanned (Chat 6 saw the same lean, M64). Old quotes carry no size, so we do not know how many dollars could be bought late at night. The 42 "LEAD" cells are mostly this one pattern counted many times.
- **Data:** `python3 tools/bet_grid.py` -> `research/engine_room/bet_grid.csv` (all cells; database view `lab.bet_grid`), `bet_grid_summary.json`, `bet_grid_highlights.csv`. Sheet tab "Big grid". Master m20261128-0345b9a1.

### Q003 · 2026-11-28 01:20 AM ET · Do takers or makers win in our two daily markets?
- **Asked by Dan:** "Are you sure takers beat makers overall? Double check that."
- **Answer:** On Kalshi as a whole, makers win (Becker 2026: takers lose about 1.1% per trade). In OUR two daily fuel markets it is the other way round: takers win.
- **Numbers (before fees, profit per $ risked):** diesel daily takers +5.6%, makers -6.8% (61 days, noise 4.8, takers ahead on 70% of days). Gas daily takers +2.7%, makers -1.9% (31 days, noise 3.1, 68% of days).
- **Catch:** short tape (diesel from Sep 27, gas from Oct 27). Diesel is just beyond its noise; gas is inside it. Fees not taken off.
- **Data:** `kalshi_trades` in both databases, via `tools/market_scorecard.py`. Master m20261128-0345b9a1.

### Q002 · 2026-11-28 01:20 AM ET · If YES is priced 85c or more, how often does it win?
- **Asked by Dan:** "a rule like ... YES is always over 85%".
- **Answer:** It wins about 90-96% of the time, but in gas that is LESS than the price paid. In diesel it is about fair.
- **Numbers:** gas daily 90.4% wins vs 93.7% needed (edge -3.4, noise 3.2, 237 events: beyond noise, a loser). Gas weekly 90.1% vs 94.0% (edge -3.8, noise 5.5, 73 events). Diesel daily 95.9% vs 94.8% (edge +1.1, noise 3.0, 108 events).
- **Mirror (NO at 85c or more):** about fair everywhere: gas daily +0.9, gas weekly +1.0, gas monthly +1.7, diesel daily -0.6 (all inside noise).
- **Catch:** look-back on days already scanned.
- **Data:** `python3 tools/ask.py --min 85 --side yes` (and `--side no`). Master m20261128-0345b9a1.

### Q001 · 2026-11-28 01:20 AM ET · What % of favorites priced 75c or more win?
- **Asked by Dan:** "when there is a confident YES/NO bound over 75% in a liquid market, what % of the time did that win".
- **Answer:** About 9 times in 10. The question that matters is whether that beats the price paid. It does in diesel daily only.
- **Numbers (win % vs % needed to break even):** diesel daily 95.3 vs 92.7 (edge +2.6, noise 2.0, 110 events: beyond noise). Gas daily 90.8 vs 90.8 (edge 0.0, 253 events). Gas weekly 90.3 vs 91.5 (edge -1.2, 127 events). Gas monthly 88.3 vs 90.9 (33 events). Diesel weekly 94.8 vs 91.4 (15 events, too few). Diesel monthly: 3 events.
- **By side:** gas YES-favorites lose (daily -3.3, weekly -10.2 beyond noise); gas NO-favorites are about fair (+0.9 daily). Diesel YES +2.0, NO 0.0 (both inside noise).
- **Other side of the same bets (the long shot):** loses 4.5 to 7.5 points in gas daily, gas weekly and diesel daily (all beyond noise).
- **Catch:** diesel is 110 events from one stretch (Aug-Nov 2026, mostly falling prices), and these days were already scanned. Look-back until it holds on new days.
- **Data:** `python3 tools/ask.py --min 75` (add `--side yes`, `--side no`, `--pick underdog`). Master m20261128-0345b9a1.
