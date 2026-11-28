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

---

## Earlier answers, backfilled from Chats 1-6 (added 2026-11-28, Chat 7)

Answered questions from before this log existed that steer research and direction (Dan, 11/28: include the substantial ones, stamped with when they were first found, so they sit after the live questions). Pulled from `research/takeaways/master.csv`, `research/LOG.md` and the earlier chats. Not new tests, so the trial count is unchanged. Newest first. "Since / catch" says whether the Q-numbered questions changed the picture.

| # | First found (ET) | Question | Answer | Numbers | Since / catch | Source |
|---|---|---|---|---|---|---|
| P22 | 2026-11-27 05:30 PM, Chat 6 | Is the crowd's range too wide or too narrow? | Too wide. The crowd is less sure than it should be. | The final AAA number lands inside the crowd's own range 78-88% of the time, where a well-sized range would give 68%. | A hint only. Costs are not in it. Tonight's Q005 found the bigger error is where the ladder sits (level), not how wide it is. | M51 |
| P21 | 2026-11-27 05:20 PM, Chat 6 | Can we copy the market maker's prices yet? | Not closely enough. We get the center of the ladder mostly right but each line is still far off. | Center explained: 63-84% on days never seen. Each line: 6-16 points off, while the bid-ask gap is only 2-4 points. | Open. On half-cent ladders, a half-cent center miss moves a line about 15 points, so the center has to get much tighter. | M48, M53, M54 |
| P20 | 2026-11-27 05:15 PM, Chat 6 | What does the crowd know at 8 AM that we do not? | Something worth about half our miss, and we have not found it in any history we own. | At the open the crowd is within 0.25-0.4c. Best of our 4 suspects (yesterday's move, last 7 moves, weekday, wholesale): 0.40-0.44c. | Open. By midnight the crowd explains 98-99% of the next AAA move, which looks like a live station-price feed that has no free history. | M55, M56, M57 |
| P19 | 2026-11-27 03:45 PM, Chat 6 | What exactly decides who wins, and when can you trade? | Every one of the 6 markets pays on AAA's national average for one date. The daily market opens 8 AM ET the day before and closes 11:59 PM. AAA posts the answer around 3:30 AM. | Checked against outside AAA prints: 530 of 531 events identical. Weekly pays on Monday's number, monthly on the last day of the month. Lines are half a cent apart in the daily markets. | Still true. The app's '10 PM' label is not the open. | M43; contract cards in COVERAGE.md |
| P18 | 2026-11-26 06:45 PM, Chat 6 | How far back does our data really go? | Diesel only since Aug 2026. Gas goes back to 2023 but with holes. | Diesel: 116 daily, 16 weekly, 3 monthly events. Gas weekly: 139 events since Oct 2023, but a real ladder only from 2026 (45 events). Gas daily did not run in 2025. | Still true. It is why 3 of the 6 markets cannot be tested yet (Q004). | M40, M45 |
| P17 | 2026-11-26 03:45 AM, Chat 6 | Does the evening crowd go too far after a strong run-up? | Yes, as a candidate. Buying NO at 9-11 PM after the strongest 5-day rises paid well in gas. | Gas: +28% per $ over 63 days (range +17% to +39%); the last 40% of days still +20%. Diesel: same direction on 13 days. | Found by a follow-up test, so not proof. Tonight's Q005, Q007 and Q008 point the same way from three other angles. | M36 |
| P16 | 2026-11-26 03:45 AM, Chat 6 | Does anything we store predict which way the 10 AM crowd is wrong? | No. Nothing did. | About 1,980 tests on 114 diesel and 216 gas days: 0 of 38 inputs worked. The only reliable results were losers: long shots at 3-25c lose about 70%. | Still true for the 10 AM miss. Tonight's Q008 found something for a different moment: big rises with no futures behind them. | M35 |
| P15 | 2026-11-26 03:00 AM, Chat 6 | How big can one bet be? | About $1,000. Bigger bets move the price. | $1K fits at the shown price 96% of the time, $5K about half the time, $10K 17%. The whole diesel market trades about $35K a day. | One afternoon of order book only. Gas depth is not recorded yet. | M34 |
| P14 | 2026-11-26 02:15 AM, Chat 6 | Do truckstop prices move before AAA does? | Not answered yet. This is the main live test. | Day 1 (Nov 25): Love's cut prices at about 15% of its stores around 5 PM ET, and the crowd did not react. 2 days scored so far. | First read at 10 scored days (about Dec 6). A pass needs 20+. | M30, M31 |
| P13 | 2026-11-26 01:40 AM, Chat 5 | Does posting limit orders on favorites work? | It was the first result with a range above zero, but it is parked. | Diesel: +6.2% per $, range +1.4% to +10.4%. | It lost in October, gas does not confirm it, and fills are not guaranteed. Tonight's Q003 found takers beating makers on our trade record, which cuts against it. | M28, Q003 |
| P12 | 2026-11-26 01:00 AM, Chat 5 | Which time span has the most to win? | Daily. Weekly is second. Monthly is not worth it yet. | Knowing the 10 PM price at 10 AM would be worth +70-79% per $. | That is a ceiling with perfect foresight. Selling before the end means paying the spread twice, which was never taken off. | M03 |
| P11 | 2026-11-26 (no time logged), Chat 5 | How big an edge do we need, and how long to prove it? | Aim for 8-10% per bet. Under 3% is not worth the effort. | 8-10% can be proven in about 4-5 months. At 75-80c, one loss wipes out about 3-4 wins. | Still the target. Pro sports bettors make 3-7% long term, so 8-10% is the top of what is realistic. | M17, M18 |
| P10 | 2026-11-26 12:45 AM, Chat 5 | Do our simple forecasts beat Kalshi at any time span? | No. The market beat our simple models on daily, weekly and monthly markets. | Our signal does beat 'no change' by about 24% at one week (data since 1994), but traders already price it in. | Still true. It is why the forecast needs a new input, not more math on the same inputs. | M15, M16 |
| P09 | 2026-11-26 12:20 AM, Chat 5 | Has anyone done this before, and is it realistic? | Yes in other small markets, and one public bot already models AAA. That bot shows no measured edge. | The public bot won 58% of the time where prices implied 60%. It found pump prices trail futures by 4-7 days and close the gap at about 2c a day. | Useful warning: its streak-only model showed a fake 40-point edge that vanished once wholesale prices were added. | M08, M25 |
| P08 | 2026-11-25 11:50 PM, Chat 4 | Can we rebuild AAA's national number from the state prices? | Almost. A fitted blend of the 51 states lands close, but not yet inside the goal. | Fitted weights miss by 0.14-0.37c. Goal: 0.10c. | Open. Free state history is thin, so this firms up slowly. | M09 |
| P07 | 2026-11-25 06:20 PM, Chat 3 | Is the diesel favorites edge real? | Not proven. The first count said +8 per $100. The stricter test said +3.3% with a range that includes zero, and only November made money. | Strict test range: -1.6% to +7.7%. By month: Aug up, Sep down, Oct down, Nov up a lot. | Tonight's Q001 (each day counted once): +2.6 points, just beyond its noise, on one falling stretch. Still a look-back. | M12, Q001 |
| P06 | 2026-11-25 04:50 PM, Chat 2 | Does the same favorite rule work in gas? | No. Gas is about 13 times busier and priced close to fair. Cheap 'price goes up' YES bets lose in gas in every window tested. | Gas favorites: -2.5 per $100. Gas YES at 83.5c or less: -18 to -30 per $100. | Still true and now wider: tonight's Q004 shows YES overpriced in gas at almost every price. | M13, Q004 |
| P05 | 2026-11-25 (no time logged), Chat 4 | Are there crowd moves that nothing we track explains? | Yes, 184 of them, bunched around noon and 6 PM. | 184 hours where the crowd moved and none of our inputs did. | Open. Tonight's Q009 showed futures in the same hours do not explain crowd rises either, so the missing input is something else. | M11 |
| P04 | 2026-11-25 03:00 AM, Chat 1 | Did the 75-85c favorite rule survive days it had never seen? | No. It worked while prices slid slowly and broke when prices climbed fast. | Earlier days: 90% wins, +11.8%. Unseen days (Aug to mid Sep, a fast rise): 81% wins, +0.9%. One bet a day went from +9% to -21%. | Lesson kept: the multi-week trend decides which rules work. Yesterday's direction alone does not. | M14 |
| P03 | 2026-11-25 12:20 AM, Chat 1 | Who makes the AAA number, and can we get their data? | A data company called OPIS builds it from 9,000+ truckstops. Their method is not published and their data is paid. We use free stand-ins: truckstop chain websites and wholesale futures. | Love's (624 stores) and TA (120) are recorded hourly since Nov 25. | Still true. Paid OPIS data may count as insider information under Kalshi's rules, so check before ever buying it. | M20, M22 |
| P02 | 2026-11-24 11:55 PM, Chat 1 | How sharp is the crowd compared with our own forecast? | The crowd is about twice as good as us, and it gets sharper all day. | Crowd miss: 0.3-0.55c at 10 AM, 0.1-0.17c by the close. Our formula: 0.6-0.7c. Re-run tonight (Q006): 0.34-0.37c at 10 AM, 0.19c at the close. | Still true. This is the bar our forecast has to clear. | M10, M55, Q006 |
| P01 | 2026-11-24 11:55 PM, Chat 1 | Does the morning crowd lean too hard on yesterday's price move? | Yes, a little. But it is not a trade by itself. | Crowd at 10 AM = today's AAA + 0.89 x yesterday's move. The truth was 0.73 x. By the close the crowd is at 0.77 x. | Fitted on 51 days. A momentum-only forecast failed after big wholesale moves. Tonight's Q007-Q009 found the same habit in bigger form: the crowd chases rises. | M12, M15, M35 |
