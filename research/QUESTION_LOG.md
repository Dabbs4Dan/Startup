# Question log (quick questions on data we already hold)

Home of the `test` command. One question, one short answer, date and time stamped, newest first.
This is NOT a strategy test. It is Dan probing the data. A finding here is a **look-back**: it becomes a lead only
after it also holds on new days. Dan's reading copy: Google Sheet "Kalshi – Question Log" (same rows, newest on top). Sheet only, no Google Doc (Dan, 2026-11-28).

**How an answer is made:** `python3 tools/ask.py` on `data/lake/master/slices.csv.gz` (the 3 busiest lines of each
event at each time slot). The event is the sample. Cost = ask + taker fee. Noise = 2 standard errors across events.

**Guard rails (kept here, nowhere else):**
- **Trial count:** about 3,300 cuts were run before this log (deep scan 1,980 + slice scan 1,328). Each question adds 1; the bet grid (Q004) added its 2,424 readable cells. **Count now: 6,010.**
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

---

## Earlier answers from Chats 1-6, re-tested (Chat 7, 2026-11-28)

Answered questions from before this log existed that steer research and direction. Each keeps the time it was first found, so it sits after the live questions; each was re-run on the current master (m20261128-0345b9a1) at 03:32 AM ET on 2026-11-28 with `tools/retest_earlier.py` unless noted. The re-runs added about 60 cuts to the trial count.
Removed by Dan on 2026-11-28 (no re-test, not in this log; still in `master.csv`): crowd vs our forecast (M10), simple forecasts vs Kalshi (M15), nothing predicts the 10 AM miss (M35), market-maker copy (M54).

### P22 · first found 2026-11-27 05:30 PM, Chat 6 · Is the crowd's range too wide or too narrow?
- **Plain meaning:** The crowd gives a best guess plus a range around it. If the range is sized right, the real number should land inside about 68% of the time.
- **Then:** In all 6 markets the answer landed inside the crowd's range 78-88% of the time, so the range looked too wide.
- **Re-test (2026-11-28):** Daily markets at 10 AM: inside 81% (diesel, 83 days) and 78% (gas, 179 days); 77-86% at every time slot. Longer markets do not match: gas weekly 21%, diesel weekly 53%, gas monthly 55%.
- **Verdict:** HOLDS for the two daily markets. NOT confirmed for weekly and monthly.
- **Catch / what it means:** The old one-line weekly gas markets make the range unreliable there, so the weekly and monthly numbers need their own check. Costs are not in this; Q005 found the bigger error is where the ladder sits, not how wide it is.
- **Data:** M51; tools/retest_earlier.py

### P20 · first found 2026-11-27 05:15 PM, Chat 6 · What does the crowd know at the 8 AM open that we do not?
- **Plain meaning:** At the open nobody has traded yet today, so the crowd's first guess shows what it already knows. We compare its miss with the miss of simple forecasts built from what we hold.
- **Then:** Crowd within 0.25-0.4c at the open; best of our 4 suspects 0.40-0.44c.
- **Re-test (2026-11-28):** Last 40% of days, never used for fitting. Diesel (24 days): crowd 0.17c; ours 0.99c with yesterday's move, 0.83c adding futures. Gas (80 days): crowd 0.26c; ours 0.67c, 0.58c adding futures. 'No change' is 2.42c and 1.44c. Adding weekday or longer trends made ours worse.
- **Verdict:** HOLDS, and the gap is wider than before.
- **Catch / what it means:** This is also the measure of how sharp the crowd is against us. The missing input is still not found in any history we own.
- **Data:** M55, M56, M57; tools/retest_earlier.py

### P19 · first found 2026-11-27 03:45 PM, Chat 6 · What exactly decides who wins, and when can you trade?
- **Plain meaning:** The rule that pays every bet, and the hours the market is open.
- **Then:** All 6 markets pay on AAA's national average for one date; 530 of 531 events matched outside AAA prints.
- **Re-test (2026-11-28):** 580 of 581 events match the AAA number to a tenth of a cent. Gas daily closed at 11:59 PM ET on 247 of 267 events. Diesel daily closed at 11:59 PM in November (41 events) and 1:59 AM before that (76 events). AAA posted around 3:30 AM on the two nights we recorded.
- **Verdict:** SAME.
- **Catch / what it means:** Diesel's close time moved from 1:59 AM to 11:59 PM during the fall, so 'the close' is not the same clock time across the sample.
- **Data:** M43; SPINE.md

### P18 · first found 2026-11-26 06:45 PM, Chat 6 · How far back does our data really go?
- **Plain meaning:** How many separate market days we have to test on. Each day counts once, however many prices it had.
- **Then:** Diesel 116 daily, 16 weekly, 3 monthly; gas weekly 139 (real ladder only from 2026), monthly 34.
- **Re-test (2026-11-28):** Diesel daily 117 events (110 with busy lines), weekly 16, monthly 3. Gas daily 269 (253), weekly 140 (128), monthly 34 (33). Gas daily ladders are Mar-Nov 2026 in practice (245 of 253).
- **Verdict:** SAME.
- **Catch / what it means:** Three of the six markets still cannot be tested (Q004). Hourly futures now reach back to July 2024 (Q009), which is longer than the Kalshi history itself.
- **Data:** M40, M45; master

### P17 · first found 2026-11-26 03:45 AM, Chat 6 · Does the evening crowd go too far after a strong run-up?
- **Plain meaning:** After pump prices have climbed for several days, the evening crowd prices in more climbing than actually comes. So betting NO ('it will not be above this line') at night pays more than its price says.
- **Then:** Gas: buying NO at 9-11 PM after the strongest 5-day rises made +28 per $100 over 63 days. Diesel same direction on 13 days.
- **Re-test (2026-11-28):** Gas daily, NO at 10 PM priced 25-97c. After the top fifth of 5-day rises (6.0c or more): +25.7 per $100 (noise 20.4, 43 days); first half +20.5, second half +30.6. After any 5-day rise: +23.4 (noise 13.5, 87 days). After a flat or falling 5 days: -7.5 (126 days). Diesel top fifth: +9.3 (noise 38.7, 18 days); first half +21.8, second half -3.1.
- **Verdict:** HOLDS in gas. NOT confirmed in diesel.
- **Catch / what it means:** Same days as the first finding, so this is a re-count, not new proof. Q005, Q007 and Q008 point the same way from other angles.
- **Data:** M36; tools/retest_earlier.py

### P15 · first found 2026-11-26 03:00 AM, Chat 6 · How big can one bet be?
- **Plain meaning:** How many dollars are sitting at the best price, ready to be bought, before our own order would push the price.
- **Then:** $1K fit at the shown price 96% of the time, $5K about half, $10K 17% (one afternoon).
- **Re-test (2026-11-28):** 3 days of the diesel order book, favorite side priced 60-97c, best price only. $1K fits 66% of the time overall: 78% from 10 AM to 6 PM, 39% from 10 PM to midnight, 29% from 8 to 10 AM. $5K fits 1-2%. $10K never.
- **Verdict:** CHANGED: smaller than first thought, and much thinner early and late.
- **Catch / what it means:** I count only the dollars at the single best price; the first read may have counted the next prices too. Gas has no order book recorded yet.
- **Data:** M34; tools/retest_earlier.py

### P14 · first found 2026-11-26 02:15 AM, Chat 6 · Do truckstop prices move before AAA does?
- **Plain meaning:** Truckstops post prices all day. If they move before the national number does, we would know tomorrow's answer early.
- **Then:** Day 1: Love's cut prices at about 15% of stores around 5 PM and the crowd did not react.
- **Re-test (2026-11-28):** Still 2 days scored, 2 waiting on AAA. Nov 25: truckstops -1.0c, AAA -4.0c. Nov 26: truckstops -1.9c, AAA -2.0c.
- **Verdict:** OPEN. Nothing to conclude from 2 days.
- **Catch / what it means:** First read at 10 scored days (about Dec 6); a pass needs 20+.
- **Data:** M30, M31; l3_truckstop_scorecard.csv

### P13 · first found 2026-11-26 01:40 AM, Chat 5 · Does posting limit orders on favorites work?
- **Plain meaning:** A limit order waits at your price until someone takes it. The question was whether waiting on the favorite side beats buying it outright.
- **Then:** Diesel +6.2 per $100 (range +1.4 to +10.4); lost in October; gas did not confirm.
- **Re-test (2026-11-28):** Trade record, before fees. Diesel makers who ended up holding favorites at 60-97c: +6.6 per $100 (noise 4.6, 61 days; October -4.2). Gas: -1.8 (noise 8.1, 31 days). New: takers who simply bought those same favorites did better: diesel +14.0, gas +4.5.
- **Verdict:** HOLDS as counted, but the meaning changed.
- **Catch / what it means:** It was the favorite side doing well in a falling stretch, not the limit order. Buying outright beat waiting. Stays parked.
- **Data:** M28, Q003; tools/retest_earlier.py

### P12 · first found 2026-11-26 01:00 AM, Chat 5 · Which time span has the most to win?
- **Plain meaning:** If you could see the 10 PM price at 10 AM, how much could you make? It is a ceiling: the most any forecast could ever earn in that market.
- **Then:** Daily: +70-79 per $100. Weekly second. Monthly not worth it.
- **Re-test (2026-11-28):** Perfect foresight, 10 AM to 10 PM. Daily: +68.7 per $100 before costs, +42.3 after paying the ask, selling at the bid and both fees. Weekly: +26.3, then +8.4. Monthly: +16.7, then +3.1.
- **Verdict:** HOLDS: daily has the most room. Costs remove about 40% of it.
- **Catch / what it means:** A ceiling is not a forecast. It says where a good forecast would pay most, which is the daily markets.
- **Data:** M03; tools/retest_earlier.py

### P11 · first found 2026-11-26 (no time logged), Chat 5 · How big an edge do we need, and how long to prove it?
- **Plain meaning:** A small edge takes many bets before it can be told apart from luck. This sets the target worth chasing.
- **Then:** Aim for 8-10% per bet (provable in 4-5 months); under 3% is not worth it.
- **Re-test (2026-11-28):** Bets needed to tell the edge from luck: 8% needs about 120 by the textbook math and about 56 using the real day-to-day swing of a diesel favorite bet. 3% needs about 860 and about 400.
- **Verdict:** HOLDS.
- **Catch / what it means:** At one bet a day, 8% takes 2 to 4 months and 3% takes more than a year. Most of the look-back edges in this log are 3 to 8 points.
- **Data:** M17, M18; tools/retest_earlier.py

### P09 · first found 2026-11-26 12:20 AM, Chat 5 · How fast do wholesale price moves reach the pump?
- **Plain meaning:** Wholesale futures move first and pump prices follow. A public Kalshi bot measured the delay; we checked it on our own data.
- **Then:** The public bot found pump prices trail futures by 4-7 days and close the gap at about 2c a day. Its own live record showed no edge (58% wins where prices implied 60%).
- **Re-test (2026-11-28):** Our data since Jan 2025. For each 1c futures move, the pump price has moved 0.07c after 1 day, 0.23c after 3, 0.46c after 7 and 0.66c after 14 (diesel; gas is nearly the same: 0.05, 0.21, 0.45, 0.66). The biggest single-day effect comes 2 to 3 days later. The same-day effect is about zero.
- **Verdict:** HOLDS, and sharper.
- **Catch / what it means:** This is a fundamental input for the forecast and it explains Q009: today's futures say nothing about tomorrow's AAA, while moves from 2-3 days ago are still arriving.
- **Data:** M08, M25; tools/retest_earlier.py

### P08 · first found 2026-11-25 11:50 PM, Chat 4 · Can we rebuild AAA's national number from the state prices?
- **Plain meaning:** AAA's national price is a blend of the 51 state prices with weights nobody publishes. If we can copy the blend, we can track the number ourselves.
- **Then:** Fitted weights missed by 0.14-0.37c against a goal of 0.10c.
- **Re-test (2026-11-28):** No new data since. The fitted blend misses by 0.36c on the 13 days where all 51 states are known; 31% of days are inside the goal.
- **Verdict:** OPEN, unchanged.
- **Catch / what it means:** Free state history is thin, so this firms up slowly.
- **Data:** M09; algo_scorecard L2.1

### P07 · first found 2026-11-25 06:20 PM, Chat 3 · Is the diesel favorites edge real?
- **Plain meaning:** The favorite is the side priced above 50c. The claim was that diesel favorites win more often than their price says.
- **Then:** First count +8 per $100; the stricter test +3.3 with a range of -1.6 to +7.7. Only November made money.
- **Re-test (2026-11-28):** Favorites priced 60-97c at 10 AM, each day once: +1.5 per $100 (noise 7.1, 73 days). By month: Aug +8.9, Sep -9.7, Oct -9.5, Nov +15.7. Falling trend +4.4 points (37 days); rising trend -3.2 (33 days).
- **Verdict:** HOLDS: not proven. It is a falling-market effect.
- **Catch / what it means:** Q001 counted all time slots and got +2.6 points for favorites at 75c+; this 10 AM count is smaller and well inside its noise.
- **Data:** M12, Q001; tools/retest_earlier.py

### P06 · first found 2026-11-25 04:50 PM, Chat 2 · Does the same favorite rule work in gas?
- **Plain meaning:** Gas pays on the same kind of AAA number, so it is a second place to check any diesel idea.
- **Then:** Gas favorites -2.5 per $100. Gas YES at 83.5c or less lost 18-30 per $100 in every window.
- **Re-test (2026-11-28):** Gas daily favorites 60-97c at 10 AM: -0.8 per $100 (noise 4.8, 169 days). Gas daily YES-favorites at 83.5c or less: -18.7 per $100 at 10 AM (noise 16.5, 76 days), -13.7 across all slots (noise 8.4, 217 days). Gas weekly: -27.3 (noise 16.0, 59 days).
- **Verdict:** HOLDS.
- **Catch / what it means:** Q004 widened it: YES is overpriced in gas at almost every price.
- **Data:** M13, Q004; tools/retest_earlier.py

### P05 · first found 2026-11-25 (no time logged), Chat 4 · Are there crowd moves that nothing we track explains?
- **Plain meaning:** Times when the Kalshi prices jumped but none of our inputs moved. Each one hints at information the crowd has and we lack.
- **Then:** 184 hours where the crowd moved and nothing we tracked did, bunched around noon and 6 PM.
- **Re-test (2026-11-28):** 478 big crowd moves in the two daily markets, now checked against hourly futures. Futures moved the same way in the same hours on only 50% of them in diesel (120 moves) and 42% in gas (358 moves). Most happen between noon and 6 PM.
- **Verdict:** HOLDS: about half of big moves have no futures move behind them.
- **Catch / what it means:** Futures were the obvious suspect and they do not explain it (Q009). The next suspects are station prices and truckstop repricing.
- **Data:** M11, Q007, Q009; swing_hourly.py

### P04 · first found 2026-11-25 03:00 AM, Chat 1 · Did the 75-85c favorite rule survive days it had never seen?
- **Plain meaning:** An early rule said: buy the favorite when it costs 75-85c. We then tried it on older days it was not built from.
- **Then:** Days it was built on: 90% wins, +11.8%. Unseen days in a fast rise: 81% wins, +0.9%.
- **Re-test (2026-11-28):** At 10 AM, each day once: 35 days, 84.3% wins, +2.7 points (noise 11.9). Falling trend +9.3 (20 days); rising trend -11.5 (12 days). By month per $100: Sep -10.4, Oct -11.5, Nov +24.4.
- **Verdict:** HOLDS: it depends on the trend, so it is not a rule.
- **Catch / what it means:** Only 35 days carry a 75-85c favorite at 10 AM. The lesson stands: the multi-week trend decides which simple rules work.
- **Data:** M14; tools/retest_earlier.py

### P03 · first found 2026-11-25 12:20 AM, Chat 1 · Who makes the AAA number, and can we get their data?
- **Plain meaning:** AAA does not compute its own price. Knowing who does tells us which raw inputs matter.
- **Then:** A data company, OPIS, builds it from 9,000+ truckstops. Method unpublished, data paid.
- **Re-test (2026-11-28):** A fact, so nothing to re-run. Our free stand-in is recording: Love's and TA truckstop prices, 4 days so far.
- **Verdict:** SAME.
- **Catch / what it means:** Paid OPIS data may count as insider information under Kalshi's rules; check before ever buying it.
- **Data:** M20, M22

### P01 · first found 2026-11-24 11:55 PM, Chat 1 · Does the morning crowd lean too hard on yesterday's price move?
- **Plain meaning:** If AAA fell 2c yesterday, how much more fall does the crowd expect tomorrow, and how much really comes?
- **Then:** Crowd at 10 AM expected 0.89 of yesterday's move to repeat; the truth was 0.73 (51 diesel days).
- **Re-test (2026-11-28):** Diesel at 10 AM (87 days): crowd 0.84, truth 0.91. Gas at 10 AM (180 days): crowd 0.79, truth 0.73.
- **Verdict:** CHANGED. In diesel the crowd no longer over-follows; it slightly under-follows. In gas it over-follows a little.
- **Catch / what it means:** Not an edge by itself. The bigger crowd habit is in Q007-Q009: chasing rises that futures do not back.
- **Data:** M12, M15, M35; tools/retest_earlier.py
