#!/usr/bin/env python3
"""Source of truth for the takeaway tables. Run to rewrite by_chat.csv and master.csv.
by_chat = frozen snapshot of each chat's closing takeaway table (append new chats, never edit old rows except Status).
master  = rolling, de-duplicated list (edit freely; newest evidence wins)."""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = "2026-11-26"

CHATS = {
    1: "Chat 1 - Setup & core research",
    2: "Chat 2 - OPIS & 60 day excel",
    3: "Chat 3 - Initial excel",
    4: "Chat 4 - Nautilus Trader",
    5: "Chat 5 - Sample models & backtest",
    6: "Chat 6 - Audit, structure & truckstop test",
}

# (chat, section, item, meaning, sketch, status, superseded_by)
BY_CHAT = [
    (1, "Market", "Kalshi pricing", "Each price is the crowd's chance and pays $1 if right. The fee is biggest near 50c. You profit only if you win more often than the price you paid.", "win % > price + fee", "Current", ""),
    (1, "Design", "Two engines", "Engine 1 = what the bet is really worth. Engine 2 = what the market charges. Trade only when the gap beats the costs.", "E1 - E2 > costs", "Current", ""),
    (1, "Diesel engine", "Price slices", "Pump price = crude + refining + taxes + delivery. The delivery slice is swollen, so pump prices have room to fall.", "37 / 27 / 10 / 26 %", "Current", ""),
    (1, "Diesel engine", "Retail lags", "Wholesale (HO futures) moves first. Pump prices catch up over days, falling slowly like feathers.", "HO down -> AAA down over days", "Current", ""),
    (1, "Model", "Our F formula", "Our guess for tomorrow from the delivery slice and HO moves. Misses about 0.6c; the crowd misses about 0.3c. An anchor, not an edge.", "AAA - squeeze +/- HO", "Current", ""),
    (1, "Market", "The crowd is sharp", "At 10 AM it misses by 0.34c, by close only 0.11c. It leans a bit too hard on yesterday's move.", "0.89x vs 0.73x", "Current", ""),
    (1, "Results", "Goldilocks zone", "Favorites priced 75-85c won about 90% while prices were falling. The rule broke when prices rose.", "works falling / fails rising", "Superseded", "C3-11 honest edge test"),
    (1, "Results", "Regime label", "Rising or falling over weeks decides which rules are on. Nov 23 was the 27th straight down day.", "10-day trend", "Current", ""),
    (1, "Results", "Weekend bets", "22 wins out of 22, but a small sample. Need to find out why.", "22/22", "Open", "C2: mixed in gas"),
    (1, "Results", "Where losses come from", "The crowd changes its mind after 10 AM and futures don't explain it. Top suspect: truckstop prices.", "10 AM -> noon jump", "Current", ""),
    (1, "Diesel engine", "Hidden state weights", "A plain average of states misses AAA by 3.9c. Back-solved region weights got within 0.2c.", "Midwest 48 / East 25 / West 13 / Gulf 8 / Rockies 6", "Superseded", "C4-06 fitted state weights"),
    (1, "Data", "Inputs Map", "83 inputs, each scored 1-4. Round 1 tests only 12 of them.", "13 must-haves / 12 test-first", "Current", ""),
    (1, "Data", "Connectivity", "Pulled every tier-1 and tier-2 input for Nov 23. Blocked: HO at 10 AM and truckstop prices.", "14 green / 9 yellow / 2 red", "Superseded", "C3-05 truckstops recording since Nov 25"),
    (1, "Rules", "No peeking", "Only use data known at 10 AM. The F formula broke this by using HO's end-of-day close.", "known-by-10 AM only", "Current", ""),
    (1, "Risk", "Risk math", "At about 75c one loss wipes out about 3 wins. Break-even win rate = the price you paid.", "1 loss = 3 wins", "Current", ""),
    (1, "Rules", "Insider rule", "Paid OPIS data could count as insider info. Check before using it.", "check first", "Current", ""),
    (2, "Diesel engine", "Edge thesis", "AAA is slow and smoothed; wholesale moves first, so tomorrow's AAA is partly visible today.", "wholesale down today -> AAA down next days", "Current", ""),
    (2, "Design", "North star", "Rebuild the market maker's model from inputs anyone can know. A move our inputs can't explain points to missing data.", "ladder = f(inputs) + spread", "Current", ""),
    (2, "Design", "Two engines", "Engine 1 = our forecast. Engine 2 = what the market charges. Trade only when the gap beats costs plus a buffer.", "worth 70c - cost 61c > 3c buffer", "Current", ""),
    (2, "System", "Engine Room", "Prove each layer before hunting patterns. The state blend rebuilds AAA within about 0.1c (2 days, needs 20).", "states -> national -> ladder", "Current", ""),
    (2, "Data", "Truckstop prices", "Love's and TA posted prices recorded hourly from Nov 25. Test: do yesterday's truckstop moves predict today's AAA?", "truckstop X-1 -> AAA X", "Current", ""),
    (2, "Market", "Crowd vs our model", "Crowd misses about 0.28c at 10 AM and 0.17c at close. Our model misses about 0.59c.", "crowd sharper", "Current", ""),
    (2, "Results", "Diesel favorites", "Lines priced 60-97c won more often than their price: about +8 per $100.", "90% win at 83c", "Superseded", "C3-11 honest edge test (+3.3%, CI includes 0)"),
    (2, "Results", "Gas favorites", "The same rule loses in gas (-2.5 per $100). Gas is about 13x busier and priced fairly.", "quiet = edge / busy = none", "Current", ""),
    (2, "Results", "Gas avoid rule B14", "Cheap 'price goes up' gas bets (YES at 83.5c or less) lose -18 to -30 per $100 in every window.", "YES <= 83.5c -> skip", "Current", ""),
    (2, "Results", "Regime matters", "Favorites paid in slow drops and struggled in fast rises. The multi-week trend matters more than one day.", "rising vs falling", "Current", ""),
    (2, "Risk", "Risk math", "At 80c each loss wipes out about 4 wins. Needed win rate = price + fee.", "80c -> need ~80% wins", "Current", ""),
    (2, "System", "Where it lives", "GitHub runs everything for free. Sheets (diesel + gas) hold 60 Day, Testing, Bricks, Strategies. Works from the phone.", "GitHub -> DB -> Sheets", "Current", ""),
    (2, "Gaps", "Biggest gaps", "No wholesale price history at 10 AM, no gas forecast model, only a few days of truckstop prices.", "data shopping list", "Current", ""),
    (3, "Design", "The goal", "Rebuild the market maker's view and be more right than the price, not just right.", "edge = our % - price - fee", "Current", ""),
    (3, "Design", "Two engines", "Engine 1 = our guess of tomorrow's AAA. Engine 2 = Kalshi's price + spread. Trade only when the gap beats costs.", "E1 - E2 > costs + buffer", "Current", ""),
    (3, "System", "L0-L3 layers", "How AAA is built, bottom to top. Prove each layer before looking for patterns.", "pumps -> states -> AAA -> Kalshi", "Current", ""),
    (3, "System", "Warehouse", "One place to search all data, diesel + gas, old + new. Each row tagged history or since go-live.", "history | go-live", "Current", ""),
    (3, "Data", "Live recorders", "Kalshi prices every 5 min, order book every 15, AAA change time, futures, truckstops hourly.", "5 min -> GitHub hourly", "Current", ""),
    (3, "System", "The relay", "GitHub jobs start each other, since timed jobs don't run on this branch.", "shift -> next shift -> daily jobs", "Current", ""),
    (3, "Data", "History pulled", "115 diesel days, about 270 gas days, decades of free EIA prices. AAA archive since 2019 loading.", "1980 -> 2026", "Current", ""),
    (3, "System", "Gas twin", "Side test with the same AAA engine, used to check ideas.", "diesel main / gas analog", "Current", ""),
    (3, "System", "Feed health", "Warehouse tab shows if any recorder goes quiet.", "OK / STALE", "Current", ""),
    (3, "System", "Silent breaks fixed", "Daily pull kept getting cancelled, two jobs overwrote one database, a job kept restarting.", "1 database = 1 writer", "Current", ""),
    (3, "Results", "Honest edge test", "Favorite bets: +3.3%, range -1.6% to +7.7%. Not proven. Only November worked.", "Aug + / Sep - / Oct - / Nov ++", "Current", ""),
    (3, "Market", "Score to beat", "The crowd misses tomorrow's AAA by about 0.3c at 10 AM. Our formula misses by 0.59c.", "ours 0.59c vs crowd 0.30c", "Current", ""),
    (3, "Results", "What's real", "Data foundation, the crowd benchmark, and the state blend (51 states -> AAA within about 0.07c).", "51 states -> 1 number", "Current", ""),
    (3, "Strategy", "Edge to chase", "Timing: today's truckstop and state prices might predict tomorrow's AAA before the crowd does.", "pumps X-1 -> AAA X", "Current", ""),
    (3, "System", "Sheet", "Warehouse + Wishlist tabs added. Claude writes them; no taps needed.", "phone-only", "Current", ""),
    (4, "Design", "North star", "Rebuild the market maker's model using the same inputs they watch.", "ladder = f(inputs) + spread", "Current", ""),
    (4, "System", "The algo ladder", "Four layers stacked from the bet down. Prove each one, bottom up.", "L0 Kalshi MM -> L1 AAA -> L2 state blend -> L3 truckstops", "Current", ""),
    (4, "System", "Engine Room", "An algo counts only after it passes on 20+ days. Patterns only use proven algos.", "prove -> then hunt patterns", "Current", ""),
    (4, "System", "3 storage layers", "Everything saved fits in one of three layers.", "Raw -> Rebuilt -> Results", "Current", ""),
    (4, "Strategy", "Slices -> Bricks -> Strategies", "Slice = an angle on the data. Brick = a finding that holds on unseen days. Strategy = bricks combined into a trade rule.", "slice -> brick -> law -> strategy", "Current", ""),
    (4, "Diesel engine", "L2 state blend", "National AAA = weighted mix of 51 states. Fixed weights miss ~0.41c; learned weights 0.14-0.37c (goal 0.10c). Gulf counts more than expected.", "sum(weight x state price)", "Current", ""),
    (4, "Market", "L0 price ladder", "A simple bell curve gets each line within about 2.1c. Close, not tight.", "center + wiggle", "Current", ""),
    (4, "Market", "Mystery moves", "184 hours where the crowd's forecast jumped and nothing we track explains it. Cluster around noon and 6 PM.", "move - known inputs = gap", "Current", ""),
    (4, "Data", "Truckstop recorder (L3)", "Love's (624 stores) and TA (120 sites), hourly. About 10c under AAA, which is fine; the test is whether their changes lead AAA.", "truckstop move today -> AAA tomorrow?", "Current", ""),
    (4, "System", "NautilusTrader", "One strategy file runs 3 ways. Installed and tested; no strategies coded yet.", "backtest -> demo -> live", "Current", ""),
    (4, "Strategy", "Strategies tab", "13 strategy ideas, each matched to a code slot. Only Dan moves one to the next stage.", "Idea -> Test -> Holdout -> Paper -> Live", "Current", ""),
    (4, "System", "DIY scheduler", "GitHub won't run timed jobs on this branch, so each job starts the next one.", "shift -> next shift -> daily pulls", "Current", ""),
    (4, "System", "Mobile-first", "Claude writes the sheets directly. No computer, no Allow-access taps.", "Claude -> Sheets", "Current", ""),
    (4, "Gaps", "Blocked / gaps", "Pilot has no open price feed. Live trading needs an always-on server. The repo is still public.", "locked", "Current", ""),
    (4, "Next", "Next", "Score the learned-weights version daily. After about 10 days of truckstop data: do truckstop moves predict AAA?", "L2 -> L3 -> L1 -> L0", "Current", ""),
    (5, "Learning", "Bollinger Bands", "Shows when a price is stretched vs its average. Pair with RSI, volume or a trend filter.", "avg +/- 2 x swing", "Current", ""),
    (5, "Market", "What a Kalshi bet is", "One bet with a price hurdle: be right AND pay less than the true chance, after fees.", "edge = your % - price - fee", "Current", ""),
    (5, "Design", "Bot design", "Engine 1 worth, Engine 2 market price, trade only when the gap beats costs + buffer, plus a safety belt.", "E1 - E2 > cost + buffer -> trade", "Current", ""),
    (5, "System", "Already built", "Order book recorder, fee + spread math, liquidity filter, backtest with real costs.", "", "Current", ""),
    (5, "Risk", "Edge needed", "About 2% makes 30%/year on paper, but 8-10% is needed to prove it in about 4-5 months. Under 3% is not worth it.", "2% -> 9 yrs to prove / 10% -> 5 months", "Current", ""),
    (5, "Learning", "Precedent", "Sports pros make 3-7%. Bigger edges show up in young niche markets with better or faster data.", "", "Current", ""),
    (5, "Results", "Favorites edge not proven", "+3.3% with a range including zero; looks like a November effect.", "", "Current", ""),
    (5, "Learning", "Sample models", "Weather bot (8% rule, Kelly), MLB bot (EV after fees, decision log, closing check), ryanfrigo (own AAA model, honest: no edge).", "Drive + GitHub research/sample_models", "Current", ""),
    (5, "Diesel engine", "Rockets & feathers", "Pump prices trail wholesale by 4-7 days; gaps close at about 2c/day.", "wholesale -(4-7d)-> pump", "Current", ""),
    (5, "Data", "Fleet fuel experts", "FreightWaves SONAR, DTN, and Corpay (free daily rack price + tomorrow's estimate by region).", "candidate rack input", "Current", ""),
    (5, "Results", "Horizon backtest", "Kalshi beats our simple models at every horizon. Daily 0.55c vs 0.70c; weekly 2.5c vs 7.8c.", "market > us", "Current", ""),
    (5, "Results", "Our signal is real", "Gap + momentum beats 'no change' by about 24% at 1 week (EIA data since 1994), but it's already priced.", "", "Current", ""),
    (5, "Strategy", "Focus band: daily", "Knowing the 10 PM price at 10 AM = +70-79% per $. Weekly second, monthly skip.", "10 AM -> 10 PM", "Current", ""),
    (5, "Strategy", "Model target", "Predict where the ladder will be at 10 PM using 10 AM data.", "", "Current", ""),
    (5, "Strategy", "Implied-variable method", "Back-solve hidden X = price - known inputs, then find outside data that predicts X before the ladder moves.", "price = known + X", "Current", ""),
    (5, "System", "Where it lives", "Build Board sheet (Drive), Sample Kalshi Models folder, GitHub research/sample_models + backtest write-up.", "", "Current", ""),
    (6, "Results", "KEY FINDING: limit-order favorites (found in Chat 5)", "Posting limit orders on the favorite side (60-97c) made +6.2% per $ in diesel, range +1.4% to +10.4%. First result with a range above zero. Lost in October; gas doesn't confirm; fills not guaranteed.", "seller + favorite", "Parked", "Dan parked it 2026-11-26"),
    (6, "Verdict", "No edge proven yet", "Data foundation and crowd benchmark are real. Every model loses to the market. The project kept adding fronts while the one deciding test only needs time.", "real base / no edge", "Current", ""),
    (6, "Strategy", "The one direction", "What does the 10 AM crowd miss, and when does it learn it? Order: truckstop scorecard, size the prize, pin mystery moves to a clock. Everything else paused.", "miss -> when -> why", "Current", ""),
    (6, "Results", "Truckstop day 1", "Nov 25: Love's cut about 15% of stores in one batch around 5 PM ET (about -6c each, -1c averaged). TA didn't move. The crowd's forecast didn't react. One day only.", "5 PM batch", "Open", ""),
    (6, "Data", "No truckstop history", "A large backtest can't be built: truckstop prices aren't archived anywhere free and recording began Nov 25. The scorecard grows one day at a time; buying history is the only shortcut.", "forward test only", "Current", ""),
    (6, "System", "Truckstop scorecard", "Scores itself every hour: truckstop move vs what the crowd missed at 10 AM and at close. First read at 10 scored days, PASS at 20+.", "ts move vs surprise", "Current", ""),
    (6, "System", "Hourly truckstop saves", "The truckstop job used to save only after 5.5 hours; a crash lost the run. Now it saves after every snapshot.", "save each hour", "Current", ""),
    (6, "System", "Session handoff", "CLAUDE.md section 0 = start and end checklist for every chat; section 6 = the one live direction. One home per fact; write the test before running it.", "read -> work -> log", "Current", ""),
    (6, "Risk", "Max bet size (first read)", "A $1K bet fills at the shown price (96% of favorite quotes). $5K fits only about half the time and moves the price; $10K rarely fits (17%). Whole market trades about $35K a day; only 3 trades over $5K in 60 days. One afternoon of order book so far; no 10 AM read yet.", "$1K ok / $5K hard / $10K no", "Open", ""),
    (6, "Results", "Deep scan: no morning edge", "About 1,980 tests on 114 diesel and 216 gas days. No stored parameter predicts which way the 10 AM crowd is wrong (0 of 38). The all-parameter model makes the forecast worse. Reliable results are losers: cheap long shots (3-25c) lose about 70%; gas YES at 10 AM loses in every band.", "0 of 38", "Current", ""),
    (6, "Results", "CANDIDATE: evening crowd overshoots a rise", "After the strongest 5-day rises, buying NO at 9-11 PM (lines 25c and up) made +28% per $ in gas (63 days, range +17% to +39%; last 40% of days +20%). Diesel same sign on 13 days. Found by a follow-up test; can't be tested now because prices are falling. Needs a forward test.", "rising -> NO in the evening", "Open", ""),
    (6, "Gaps", "13 understanding gaps", "Ranked list in research/2026-11-26_gaps-and-direction.md. Top 4: is the prize big enough, what window is in AAA's number, how much of AAA is truckstops, who are the informed takers.", "G1-G13", "Open", ""),
]

# (section, item, meaning, sketch, source_chats, status)
MASTER = [
    ("Strategy", "North star", "Rebuild the market maker's model from inputs anyone can know. A price move our inputs can't explain points to missing data.", "ladder = f(inputs) + spread", "1,2,3,4,5", "Current"),
    ("Strategy", "Two engines", "Engine 1 = what it's worth. Engine 2 = what Kalshi charges. Trade only when the gap beats costs plus a buffer. Add a safety belt.", "E1 - E2 > cost + buffer", "1,2,3,5", "Current"),
    ("Strategy", "Focus band: daily", "Knowing the 10 PM price at 10 AM = +70-79% per $. Weekly second, monthly skip.", "10 AM -> 10 PM", "5", "Current"),
    ("Strategy", "Model target", "Predict where the ladder will be at 10 PM using 10 AM data, not tomorrow's AAA directly.", "", "5", "Current"),
    ("Strategy", "Implied variable X", "Back-solve the hidden piece: X = price - known inputs. Then find data that predicts X early.", "price = known + X", "5", "Current"),
    ("Strategy", "Edge to chase: timing", "Today's truckstop, state and rack prices might predict tomorrow's AAA before the crowd does.", "pumps X-1 -> AAA X", "3,4,5", "Current"),
    ("Diesel engine", "Price slices", "Pump price = crude + refining + taxes + delivery. Delivery slice swollen, so prices have room to fall.", "37 / 27 / 10 / 26 %", "1", "Current"),
    ("Diesel engine", "Retail lags wholesale", "Futures move first; pumps catch up over 4-7 days at about 2c/day (rockets & feathers).", "HO down -> AAA down over days", "1,2,5", "Current"),
    ("Diesel engine", "State blend (L2)", "51 state prices -> national AAA. Fitted weights miss 0.14-0.37c (goal 0.10c).", "sum(weight x state)", "1,3,4", "Current"),
    ("Market", "The crowd is sharp", "Misses about 0.3-0.55c at 10 AM and 0.1-0.17c by close. Our formula misses about 0.6-0.7c.", "crowd > us", "1,2,3,5", "Current"),
    ("Market", "Mystery moves", "184 hours where the crowd moved and nothing we track explains it; cluster around noon and 6 PM.", "move - known = gap", "1,4", "Current"),
    ("Results", "Favorites edge: not proven", "Chat 2 said +8 per $100; stricter test: +3.3%, range -1.6% to +7.7%. Newest wins: not an edge.", "Aug + / Sep - / Oct - / Nov ++", "2,3,5", "Current"),
    ("Results", "Gas avoid rule B14", "Cheap 'price goes up' gas bets (YES <= 83.5c) lose in every window tested.", "YES <= 83.5c -> skip", "2", "Current"),
    ("Results", "Regime matters", "Rules that work in slow drops fail in fast rises; watch the multi-week trend.", "rising vs falling", "1,2", "Current"),
    ("Results", "Horizon backtest", "Kalshi beats our simple models daily, weekly and monthly.", "market > us", "5", "Current"),
    ("Results", "Our signal is real", "Beats 'no change' by about 24% at 1 week (since 1994), but traders already price it.", "", "5", "Current"),
    ("Risk", "Risk math", "At 75-80c one loss wipes out about 3-4 wins. Break-even win rate = price paid + fee.", "1 loss = 3 wins", "1,2", "Current"),
    ("Risk", "Edge target", "Aim for 8-10% per bet (provable in about 4-5 months). Under 3% isn't worth it.", "", "5", "Current"),
    ("Rules", "No peeking", "Only use data known at bet time.", "known-by-10 AM only", "1", "Current"),
    ("Rules", "Insider rule", "Check whether paid OPIS data counts as insider info before using it.", "check first", "1", "Current"),
    ("System", "Data foundation", "Warehouse, live recorders (5-min Kalshi, order book, AAA flips, futures), relay scheduler, feed health.", "GitHub -> DB -> Sheets", "2,3,4", "Current"),
    ("System", "Truckstop recorder (L3)", "Love's (624) and TA (120) hourly since Nov 25. Test: do they lead AAA?", "pumps X-1 -> AAA X", "2,3,4", "Current"),
    ("System", "Engine Room", "An algo only counts after passing 20+ days.", "prove -> then patterns", "2,3,4", "Current"),
    ("System", "NautilusTrader", "One strategy file: backtest -> demo -> live. Installed, no strategies coded.", "test -> demo -> live", "4", "Current"),
    ("System", "Sample models", "Weather, MLB and ryanfrigo bots (ryanfrigo has its own AAA model). Drive + GitHub.", "", "5", "Current"),
    ("Gaps", "Data gaps", "No HO price at 10 AM history, few truckstop days, no rack prices (Corpay = free candidate).", "", "2,4,5", "Open"),
    ("Gaps", "Blocked", "No Pilot feed. Live trading needs an always-on server (~$5-6/mo). Repo still public.", "", "2,4", "Open"),
    # New rows go at the END so M-numbers never shift.
    ("Results", "KEY FINDING: limit-order favorites (parked)", "Posting limit orders on the favorite side (60-97c) made +6.2% per $ in diesel, range +1.4% to +10.4%. First result with a range above zero. Lost in October, gas doesn't confirm, fills not guaranteed. Parked by Dan Nov 26; revisit after the truckstop test.", "seller + favorite", "5,6", "Parked"),
    ("Strategy", "The one direction", "What does the 10 AM crowd miss, and when does it learn it? Order: truckstop scorecard, size the prize, pin mystery moves to a clock. Other fronts paused.", "miss -> when -> why", "6", "Current"),
    ("Results", "Truckstop day 1", "Nov 25: Love's cut about 15% of stores in one batch around 5 PM ET (about -6c each, -1c averaged). TA didn't move. The crowd's forecast didn't react. One day only.", "5 PM batch", "6", "Open"),
    ("System", "Truckstop scorecard", "Scores itself every hour: truckstop move vs what the crowd missed. No large backtest is possible (no free truckstop history). First read at 10 scored days, PASS at 20+.", "ts move vs surprise", "6", "Current"),
    ("System", "Session handoff", "CLAUDE.md section 0 = start/end checklist for every chat; section 6 = the one live direction. One home per fact; write the test before running it.", "read -> work -> log", "6", "Current"),
    ("Gaps", "13 understanding gaps", "Ranked in research/2026-11-26_gaps-and-direction.md. Top 4: is the prize big enough, what window is in AAA's number, how much of AAA is truckstops, who are the informed takers.", "G1-G13", "6", "Open"),
    ("Risk", "Max bet size (first read)", "A $1K bet fills at the shown price (96% of favorite quotes). $5K fits only about half the time and moves the price; $10K rarely fits (17%). Whole market trades about $35K a day; only 3 trades over $5K in 60 days. One afternoon of order book so far; no 10 AM read yet.", "$1K ok / $5K hard / $10K no", "6", "Open"),
    ("Results", "Deep scan: no morning edge", "About 1,980 tests on 114 diesel and 216 gas days. No stored parameter predicts which way the 10 AM crowd is wrong (0 of 38). The all-parameter model makes the forecast worse. Reliable results are losers: cheap long shots (3-25c) lose about 70%; gas YES at 10 AM loses in every band.", "0 of 38", "6", "Current"),
    ("Results", "CANDIDATE: evening crowd overshoots a rise", "After the strongest 5-day rises, buying NO at 9-11 PM (lines 25c and up) made +28% per $ in gas (63 days, range +17% to +39%; last 40% of days +20%). Diesel same sign on 13 days. Found by a follow-up test; can't be tested now because prices are falling. Needs a forward test.", "rising -> NO in the evening", "6", "Open"),
]


def write():
    seen = {}
    with open(os.path.join(HERE, "by_chat.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "chat", "chat_title", "section", "item", "what_it_means", "sketch", "status", "superseded_by", "saved"])
        for c, sec, item, mean, sk, status, sup in BY_CHAT:
            seen[c] = seen.get(c, 0) + 1
            w.writerow([f"C{c}-{seen[c]:02d}", c, CHATS[c], sec, item, mean, sk, status, sup, SAVED])
    with open(os.path.join(HERE, "master.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "section", "item", "what_it_means", "sketch", "source_chats", "status", "last_updated"])
        for i, (sec, item, mean, sk, src, status) in enumerate(MASTER, 1):
            w.writerow([f"M{i:02d}", sec, item, mean, sk, src, status, SAVED])


if __name__ == "__main__":
    write()
    if "--json" in sys.argv:
        for name in ("by_chat.csv", "master.csv"):
            print(json.dumps(list(csv.reader(open(os.path.join(HERE, name)))), ensure_ascii=False))
