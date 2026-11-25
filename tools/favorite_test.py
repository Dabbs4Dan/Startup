#!/usr/bin/env python3
"""Favorite-longshot test across every AAA-settled Kalshi series in the DB.
Bet rule: for each market, first hourly candle 10–18h before close with spread ≤10¢;
buy each side whose ask falls in a price bucket (YES at yes_ask, NO at 1−yes_bid); one bet per market/side.
Win = Kalshi `result`. Cost = price + taker fee 0.07·p·(1−p).
Outputs table `favorite_test` + data/exports/favorite_test.csv + printed summary."""
import sqlite3, pathlib, csv, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
fee = lambda p: 0.07 * p * (1 - p)
rows = con.execute("""SELECT m.series_ticker, m.event_date, c.ticker, c.end_ts, c.hours_to_close, c.yes_bid, c.yes_ask, c.spread, m.result
    FROM kalshi_candles c JOIN kalshi_markets m ON m.ticker = c.ticker
    WHERE c.period_min = 60 AND m.result IN ('yes','no') AND c.yes_bid IS NOT NULL AND c.yes_ask IS NOT NULL
      AND c.hours_to_close BETWEEN 10 AND 18 AND c.spread <= 0.10
    ORDER BY c.end_ts""").fetchall()

seen, bets = set(), []
for s, d, t, ts, h, b, a, sp, res in rows:
    for side, p, win in (("YES", a, res == "yes"), ("NO", 1 - b, res == "no")):
        if 0.02 <= p <= 0.98 and (t, side) not in seen:
            seen.add((t, side)); bets.append((s.replace("KX", ""), d[:4] if d else "?", p, win))

BUCKETS = [(0.02, .10), (.10, .25), (.25, .40), (.40, .60), (.60, .75), (.75, .85), (.85, .95), (.95, .99)]
out = []
def summarize(label, B):
    for lo, hi in BUCKETS:
        x = [(p, w) for p, w in B if lo <= p < hi]
        if len(x) < 15: continue
        n = len(x); w = sum(v for _, v in x); avgp = sum(p for p, _ in x) / n
        cost = sum(p + fee(p) for p, _ in x)
        out.append(dict(group=label, price_bucket=f"{int(lo*100)}-{int(hi*100)}c", bets=n, avg_price=round(avgp, 3),
                        win_rate=round(w / n, 3), edge_pts=round(100 * (w / n - avgp), 1), roi_after_fee=round((w - cost) / cost, 3)))

summarize("ALL", [(p, w) for _, _, p, w in bets])
for s in sorted({b[0] for b in bets}):
    summarize(s, [(p, w) for ss, _, p, w in bets if ss == s])
for y in sorted({b[1] for b in bets}):
    summarize(f"year {y}", [(p, w) for _, yy, p, w in bets if yy == y])

con.execute("DROP TABLE IF EXISTS favorite_test")
con.execute("CREATE TABLE favorite_test (grp, price_bucket, bets, avg_price, win_rate, edge_pts, roi_after_fee)")
con.executemany("INSERT INTO favorite_test VALUES (?,?,?,?,?,?,?)", [tuple(r.values()) for r in out])
con.commit()
with open(ROOT / "data" / "exports" / "favorite_test.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(f"bets={len(bets)} from {len({(b[0]) for b in bets})} series")
for r in out:
    print(f"{r['group']:>14} {r['price_bucket']:>7} n={r['bets']:5d} price={r['avg_price']:.2f} win={r['win_rate']:.2f} edge={r['edge_pts']:+5.1f}pts ROI={r['roi_after_fee']:+.3f}")
