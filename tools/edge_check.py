#!/usr/bin/env python3
"""Honest edge check (quant standard): favorite bets at 10 AM ET, buy at ask + Kalshi fee, settled on AAA.
Returns are clustered BY DAY (lines on one day are not independent), bootstrap 95% CI, split by month.
An edge is only real if the CI excludes 0 AND it holds in more than one month/regime. Usage: python3 tools/edge_check.py"""
import sys, math, random
sys.path.insert(0, __import__('os').path.dirname(__file__))
from warehouse import connect
con = connect()
df = con.sql("""
WITH settle AS (SELECT date, value AS aaa FROM aaa_daily WHERE product='diesel'),
snap AS (
  SELECT l.event_date, l.strike, l.yes_bid, l.yes_ask, l.volume,
         (l.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York') AS ts_et
  FROM ladder l WHERE l.product='diesel' AND l.source='candle_60m'),
at10 AS (
  SELECT * FROM snap
  WHERE ts_et::DATE = event_date - INTERVAL 1 DAY AND strftime(ts_et, '%H') = '10'
    AND yes_bid IS NOT NULL AND yes_ask IS NOT NULL AND yes_ask - yes_bid <= 0.10)
SELECT a.event_date, a.strike, a.yes_bid, a.yes_ask, s.aaa
FROM at10 a JOIN settle s ON s.date = a.event_date
""").df()
bets = []
for r in df.itertuples():
    yes_win = r.aaa > r.strike
    for side, price, win in (("YES", r.yes_ask, yes_win), ("NO", 1 - r.yes_bid, not yes_win)):
        if 0.60 <= price <= 0.97:
            fee = math.ceil(0.07 * price * (1 - price) * 100) / 100
            cost = price + fee
            pnl = (1 - cost) if win else -cost          # per 1 contract
            bets.append((r.event_date, side, price, cost, win, pnl / cost))   # return per $ staked
import collections, statistics as st
days = collections.defaultdict(list)
for b in bets: days[b[0]].append(b[5])
day_ret = [st.mean(v) for v in days.values()]
n_days, n_bets = len(day_ret), len(bets)
mean = st.mean(day_ret); sd = st.stdev(day_ret); t = mean / (sd / math.sqrt(n_days))
random.seed(1)
boot = sorted(st.mean(random.choices(day_ret, k=n_days)) for _ in range(5000))
wins = sum(b[4] for b in bets)
print(f"bets {n_bets} on {n_days} days | win {wins/n_bets:.1%} | avg cost {st.mean(b[3] for b in bets):.3f}")
print(f"return per $ (day-clustered): mean {mean:+.2%}  t={t:.2f}  95% CI [{boot[125]:+.2%}, {boot[4875]:+.2%}]")
# by month
bym = collections.defaultdict(list)
for d, v in days.items(): bym[str(d)[:7]].append(st.mean(v))
print("by month:", {k: f"{st.mean(v):+.1%} ({len(v)}d)" for k, v in sorted(bym.items())})
# worst losing streak in $ per day
neg = sum(1 for x in day_ret if x < 0)
print(f"losing days {neg}/{n_days}")
