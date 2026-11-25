#!/usr/bin/env python3
"""Risk / threshold calculator for N bets with budget B (research only).
Per bet: stake s = B/n, cost per $1 contract c = price + fee (fee = 0.07·p·(1−p)).
  win profit  = s·(1−c)/c        loss = −s
  P&L(L losses) = s·[(n−L)·(1−c)/c − L]
  Max losses allowed to break even  L* = n·(1−c)
  Required win rate                 = c
  Wins needed to recover L losses   W ≥ L·c/(1−c)
Monte Carlo uses REAL 10 AM favorite bets (60–85¢) from daily_story with their actual outcomes."""
import sqlite3, pathlib, random, statistics as st, math
ROOT = pathlib.Path(__file__).resolve().parent.parent
fee = lambda p: 0.07 * p * (1 - p)
def pnl(B, n, c, L): s = B / n; return s * ((n - L) * (1 - c) / c - L)

if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
    bets = [(p, w) for p, w in con.execute("select N_price, F_payout from daily_story where N_price is not null")]
    costs = [p + fee(p) for p, _ in bets]; c = st.mean(costs); q = st.mean(w for _, w in bets)
    B, n = 400, 30
    print(f"real bets={len(bets)}, avg price {st.mean(p for p,_ in bets):.3f}, avg cost incl fee {c:.3f}, historical win rate {q:.3f}")
    print(f"stake/bet ${B/n:.2f} | win +${(B/n)*(1-c)/c:.2f} | loss -${B/n:.2f} | break-even losses L* = {n*(1-c):.1f} of {n}")
    for L in range(0, 11): print(f"  losses={L:2d}  P&L=${pnl(B,n,c,L):8.2f}")
    print("wins needed to cover L losses:", {L: math.ceil(L * c / (1 - c)) for L in (1, 2, 3, 5)})
    # binomial chance of ending negative at historical win rate
    Lstar = n * (1 - c)
    p_neg = sum(math.comb(n, L) * (1 - q) ** L * q ** (n - L) for L in range(n + 1) if L > Lstar)
    print(f"binomial: chance of finishing negative after {n} bets at win rate {q:.2f} = {p_neg*100:.1f}%")
    random.seed(1); res = []
    for _ in range(10000):
        s = B / n; tot = 0
        for p, w in random.choices(bets, k=n):
            cc = p + fee(p); tot += s * (1 - cc) / cc if w else -s
        res.append(tot)
    res.sort(); qn = lambda x: res[int(x * (len(res) - 1))]
    print(f"Monte Carlo 10k x {n} real bets, ${B}: median ${qn(.5):.0f}, 10th ${qn(.1):.0f}, 90th ${qn(.9):.0f}, worst ${res[0]:.0f}, best ${res[-1]:.0f}, negative {sum(r<0 for r in res)/100:.1f}%")
