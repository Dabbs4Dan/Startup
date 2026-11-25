#!/usr/bin/env python3
"""Backtest the AAA 'F' formula: ΔAAA = a + b·Delivery + c·HO bet-day move + d·HO prior-5d move.
In-sample + two out-of-sample splits; compares to 'no change' and to the Kalshi crowd (10 AM, close)."""
import sqlite3, pathlib, numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
c = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
R = c.execute("""select event_date,aaa_prev,F_aaa,ho_bet_day_move,ho_prior5_move,delivery_at_bet,mu_N,mu_C from daily_story
 where aaa_prev is not null and ho_bet_day_move is not null and ho_prior5_move is not null and delivery_at_bet is not null order by event_date""").fetchall()
def design(rows):
    return np.column_stack([np.ones(len(rows)), [r[5] for r in rows], [r[3] for r in rows], [r[4] for r in rows]]), np.array([r[2] - r[1] for r in rows])
def evaluate(train, test, label):
    X, y = design(train); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    Xt, yt = design(test); pred = Xt @ b; err = np.abs(pred - yt) * 100
    hits = sum(int(np.floor((r[1] + p) / 0.005)) == int(np.floor(r[2] / 0.005)) for r, p in zip(test, pred))
    cN = [abs(r[6] - r[2]) * 100 for r in test if r[6]]; cC = [abs(r[7] - r[2]) * 100 for r in test if r[7]]
    print(f"{label}: n={len(test)} coefs(const,deliv,HOday,HO5)={np.round(b,4)}")
    print(f"   model median miss {np.median(err):.2f}c | <=0.25c {np.mean(err<=0.25)*100:.0f}% | <=0.5c {np.mean(err<=0.5)*100:.0f}% | <=1c {np.mean(err<=1)*100:.0f}% | right half-cent bin {hits}/{len(test)}")
    print(f"   no-change miss {np.median(np.abs(yt))*100:.2f}c | crowd 10AM {np.median(cN):.2f}c | crowd close {np.median(cC):.2f}c")
    return b, pred
h = len(R) // 2
evaluate(R, R, "IN-SAMPLE")
evaluate(R[:h], R[h:], "OUT-OF-SAMPLE (train 1st half, test 2nd)")
evaluate(R[h:], R[:h], "OUT-OF-SAMPLE (train 2nd half, test 1st)")
b, pred = evaluate(R, R, "examples")
print("date | AAA prev | model | actual | crowd 10AM | crowd close")
for r, p in list(zip(R, pred))[::6]:
    print(" ", r[0], r[1], round(r[1] + p, 4), r[2], r[6] and round(r[6], 4), r[7] and round(r[7], 4))
