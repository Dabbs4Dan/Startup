#!/usr/bin/env python3
"""Bankroll simulations on real KXDIESELD hourly prices (research only, not advice).
Sim A: $500 start, one favorite bet per day ($100 fixed), deterministic pick + 1,000 random picks.
Sim B: 30 winning days, no losses (best case), using real winning favorite bets from the table.
Prices: buy at hourly ask (+1c slippage) + Kalshi taker fee round_up(0.07*C*P*(1-P)).
"""
import sqlite3, collections, random, math, statistics as st, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
c = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
R = c.execute("""select c.event_date, c.end_et, c.hours_to_close, c.strike, c.yes_bid, c.yes_ask, c.spread,
   case when m.expiration_value > c.strike then 1 else 0 end, m.expiration_value
   from kalshi_candles c join kalshi_markets m on m.ticker=c.ticker
   where m.expiration_value is not null and c.yes_bid is not null and c.yes_ask is not null and c.period_min=60""").fetchall()
SLIP, STAKE, START, LO, HI = 0.01, 100.0, 500.0, 0.60, 0.85

def trade(p, stake, win):
    p = min(p + SLIP, 0.99)
    C = math.floor(stake / (p * 1.02))                      # leave room for fee
    fee = math.ceil(0.07 * C * p * (1 - p) * 100) / 100
    cost = C * p + fee
    return (C - cost if win else -cost), cost, fee, C, p

opts = collections.defaultdict(list)                          # day -> qualifying favorite bets
for e, t, h, k, b, a, s, y, f in R:
    if s > 0.10: continue
    for side, p, win in (("YES", a, y == 1), ("NO", 1 - b, y == 0)):
        if LO <= p <= HI:
            opts[e].append(dict(day=e, time=t, h=h, strike=k, side=side, price=p, win=win, final=f))
days = sorted(opts)

def run(pick):
    bank, path, log = START, [START], []
    for d in days:
        o = pick(opts[d]); stake = min(STAKE, bank)
        if stake < 1: path.append(bank); continue
        pnl, cost, fee, C, p = trade(o["price"], stake, o["win"])
        bank += pnl; path.append(round(bank, 2)); log.append({**o, "pnl": round(pnl, 2), "fee": fee, "contracts": C})
    return bank, path, log

# Deterministic: the favorite closest to 75c around 10 AM ET (first qualifying hour ≥ 10:00)
def det(L):
    am = [o for o in L if o["time"][11:13] >= "10"] or L
    return min(am, key=lambda o: (o["time"], abs(o["price"] - 0.75)))
bank_d, path_d, log_d = run(det)
wins = sum(1 for x in log_d if x["win"])
print(f"SIM A deterministic: {len(log_d)} days, {wins} wins / {len(log_d)-wins} losses, $500 -> ${bank_d:.2f}, fees paid ${sum(x['fee'] for x in log_d):.2f}")
big = sorted(log_d, key=lambda x: x["pnl"])[:3]
print("  worst days:", [(x['day'], x['side'], f"{x['strike']:.3f}", f"{x['price']:.2f}", x['pnl']) for x in big])
print("  typical win:", st.median([x['pnl'] for x in log_d if x['win']]))

random.seed(42)
finals, paths = [], []
for _ in range(1000):
    b, pth, _ = run(lambda L: random.choice(L)); finals.append(b); paths.append(pth)
finals.sort()
q = lambda p: finals[int(p * (len(finals) - 1))]
print(f"SIM A random x1000: median ${q(.5):.0f}, 10th pct ${q(.1):.0f}, 90th pct ${q(.9):.0f}, lost money in {sum(f<START for f in finals)/10:.0f}% of runs")
pct = lambda i, p: sorted(x[i] for x in paths)[int(p * 999)]
series = {"days": ["start"] + days, "deterministic": path_d,
          "p10": [pct(i, .1) for i in range(len(path_d))], "p50": [pct(i, .5) for i in range(len(path_d))], "p90": [pct(i, .9) for i in range(len(path_d))]}

# Sim B: 30 winning days, no losses — real winning bets, one per day
wdays = [d for d in days if any(o["win"] for o in opts[d])]
random.seed(7)
pick30 = random.sample(wdays, 30)
tot = 0; ex = []
for d in sorted(pick30):
    o = min([o for o in opts[d] if o["win"]], key=lambda o: abs(o["price"] - 0.75))
    pnl, cost, fee, C, p = trade(o["price"], STAKE, True); tot += pnl; ex.append((d, o["side"], o["strike"], round(p, 2), round(pnl, 2)))
print(f"SIM B: 30 wins, 0 losses, $100/bet -> profit ${tot:.2f} (avg ${tot/30:.2f}/day)")
print("  examples:", ex[:5])
# Break-even and loss math
for p in (0.65, 0.75, 0.85, 0.95):
    w, *_ = trade(p - SLIP, 100, True); l, *_ = trade(p - SLIP, 100, False)
    print(f"  @{int(p*100)}c: win +${w:.2f}, lose ${l:.2f}, need {100*-l/(w-l):.1f}% wins to break even")
(ROOT / "research" / "sims").mkdir(exist_ok=True, parents=True)
json.dump({"series": series, "log_deterministic": log_d}, open(ROOT / "research" / "sims" / "2026-11-24_favorites_sim.json", "w"), indent=1)
