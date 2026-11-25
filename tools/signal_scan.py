#!/usr/bin/env python3
"""Signal scan: which bet-time conditions push favorite win rates toward 90%?
Bets: every line/side priced 60–97¢ at the 10 AM ET candle the day before settlement (spread ≤10¢).
Features (all knowable at 10 AM): price, distance from crowd forecast in σ units, crowd σ, spread,
model agreement (walk-forward AAA formula fit ONLY on earlier days), wholesale move prior day, weekday.
Outputs win rate per feature bucket. Small sample → hints, not proof."""
import sqlite3, pathlib, datetime as dt, collections, numpy as np
from statistics import NormalDist
ROOT = pathlib.Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
nd = NormalDist(); fee = lambda p: 0.07 * p * (1 - p)
story = {r[0]: r for r in con.execute("""select event_date, aaa_prev, F_aaa, ho_bet_day_move, ho_prior5_move, delivery_at_bet
                                         from daily_story where aaa_prev is not null order by event_date""")}
days = sorted(story)

def fit_ladder(L):
    best = None
    for mu in np.arange(min(k for k, _ in L) - .01, max(k for k, _ in L) + .01, .0002):
        for s in (.001, .0015, .002, .0025, .003, .004, .005, .007):
            e = sum((1 - nd.cdf((k - mu) / s) - m) ** 2 for k, m in L)
            if best is None or e < best[0]: best = (e, mu, s)
    return best[1], best[2]

def model_center(E):
    tr = [story[d] for d in days if d < E and all(story[d][i] is not None for i in (3, 4, 5))]
    r = story[E]
    if len(tr) < 15 or any(r[i] is None for i in (3, 4, 5)): return None
    X = np.column_stack([np.ones(len(tr)), [t[5] for t in tr], [t[3] for t in tr], [t[4] for t in tr]])
    y = np.array([t[2] - t[1] for t in tr]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return r[1] + b @ np.array([1, r[5], r[3], r[4]])

bets = []
for E in days:
    prev = (dt.date.fromisoformat(E) - dt.timedelta(days=1)).isoformat()
    L = con.execute("""select c.strike, c.mid, c.yes_bid, c.yes_ask, c.spread, m.result from kalshi_candles c
        join kalshi_markets m on m.ticker=c.ticker where c.event_date=? and c.period_min=60 and c.end_et=?""",
        (E, f"{prev} 10:00")).fetchall()
    L = [x for x in L if x[1] is not None and x[0] is not None]
    if len(L) < 3: continue
    mu, sg = fit_ladder([(k, m) for k, m, *_ in L])
    mc = model_center(E)
    for k, m, b, a, sp, res in L:
        if sp is None or sp > 0.10: continue
        for side, p, win in (("YES", a, res == "yes"), ("NO", 1 - b, res == "no")):
            if 0.60 <= p <= 0.97:
                agree = None
                if mc is not None:
                    agree = bool(mc > k) if side == "YES" else bool(mc <= k)
                bets.append(dict(day=E, p=p, win=win, z=abs(k - mu) / sg, sigma=sg * 100, spread=sp,
                                 agree=agree, gap=(abs(mc - k) * 100 if mc is not None else None),
                                 ho=abs(story[E][3] or 0) * 100, wkday=dt.date.fromisoformat(prev).weekday() >= 5))
def show(name, key, buckets):
    print(f"\n{name}")
    for lab, f in buckets:
        x = [b for b in bets if b[key] is not None and f(b[key])]
        if len(x) < 8: continue
        w = sum(b["win"] for b in x); c = sum(b["p"] + fee(b["p"]) for b in x)
        print(f"  {lab:<28} bets={len(x):4d} days={len({b['day'] for b in x}):3d} win={100*w/len(x):5.1f}% avg price={100*np.mean([b['p'] for b in x]):4.1f}¢ ROI={100*(w-c)/c:+5.1f}%")
print(f"total favorite bets at 10 AM: {len(bets)} over {len({b['day'] for b in bets})} days, win {100*np.mean([b['win'] for b in bets]):.1f}%")
show("Price", "p", [("60-75¢", lambda v: v < .75), ("75-85¢", lambda v: .75 <= v < .85), ("85-97¢", lambda v: v >= .85)])
show("Distance from crowd forecast (σ units)", "z", [("<1σ (close call)", lambda v: v < 1), ("1-2σ", lambda v: 1 <= v < 2), (">=2σ (far)", lambda v: v >= 2)])
show("Crowd uncertainty σ (¢)", "sigma", [("tight <=0.25¢", lambda v: v <= .25), ("medium 0.25-0.4¢", lambda v: .25 < v <= .4), ("wide >0.4¢", lambda v: v > .4)])
show("Our model agrees with the favorite? (walk-forward)", "agree", [("YES agrees", lambda v: v is True), ("NO disagrees", lambda v: v is False)])
show("Model distance from line (¢), agree only", "gap", [("<0.5¢", lambda v: v < .5), ("0.5-1¢", lambda v: .5 <= v < 1), (">=1¢", lambda v: v >= 1)])
show("Wholesale move on bet day (¢, abs)", "ho", [("calm <5¢", lambda v: v < 5), ("medium 5-10¢", lambda v: 5 <= v < 10), ("big >=10¢", lambda v: v >= 10)])
show("Bet day", "wkday", [("weekday", lambda v: v is False), ("weekend", lambda v: v is True)])
combo = [b for b in bets if b["agree"] and b["gap"] is not None and b["gap"] >= 1 and b["z"] >= 1]
if combo:
    w = sum(b["win"] for b in combo); c = sum(b["p"] + fee(b["p"]) for b in combo)
    print(f"\nCOMBO model agrees by >=1¢ AND line >=1σ from crowd: bets={len(combo)} days={len({b['day'] for b in combo})} win={100*w/len(combo):.1f}% ROI={100*(w-c)/c:+.1f}%")
