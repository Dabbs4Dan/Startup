#!/usr/bin/env python3
"""Daily "story" table: what the market believed at bet time (N), what happened (F), and which
real-world inputs moved in between. Writes table `daily_story` + data/exports/daily_story.csv.

Timeline for event day E (AAA price that settles the market):
  E-1 08:00 ET  market opens. Known: AAA(E-1), futures closes up to E-2.
  E-1 10:00 ET  BET TIME (N). Market forecast mu_N = where the ladder crosses 50%.
  E-1 14:30 ET  NYMEX diesel futures (HO) settle -> new wholesale info for the day.
  E-1 23:00 ET  last hourly candle before close. Market forecast mu_C.
  E   morning   AAA posts AAA(E) = F. Settlement.
Usage: python3 tools/story.py
"""
import sqlite3, csv, pathlib, datetime as dt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
day = lambda s: dt.date.fromisoformat(s)

aaa = dict(con.execute("SELECT date, aaa_diesel FROM diesel_daily WHERE aaa_diesel IS NOT NULL"))
ho = dict(con.execute("SELECT date, ulsd_nyh_usd_gal FROM diesel_daily WHERE ulsd_nyh_usd_gal IS NOT NULL AND ulsd_source LIKE 'yahoo%'"))
brent = dict(con.execute("SELECT date, brent_usd_bbl FROM diesel_daily WHERE brent_usd_bbl IS NOT NULL AND brent_source LIKE 'yahoo%'"))
ho_days = sorted(ho)

def last_on_or_before(series_days, series, d):
    xs = [x for x in series_days if x <= d]
    return (xs[-1], series[xs[-1]]) if xs else (None, None)

def ho_close_before(d, back=0):
    """HO close on the latest trading day <= d, stepping back `back` trading days."""
    xs = [x for x in ho_days if x <= d]
    return ho[xs[-1 - back]] if len(xs) > back else None

def ladder_forecast(rows):
    """rows: [(strike, mid)] -> strike where P(>K) crosses 50% (linear interpolation)."""
    rows = sorted((k, m) for k, m in rows if m is not None)
    for (k1, m1), (k2, m2) in zip(rows, rows[1:]):
        if m1 >= 0.5 > m2:
            return k1 + (k2 - k1) * (m1 - 0.5) / (m1 - m2) if m1 != m2 else k1
    return None

out = []
events = [r[0] for r in con.execute("SELECT DISTINCT event_date FROM kalshi_markets WHERE expiration_value IS NOT NULL ORDER BY 1")]
for E in events:
    e = day(E); prev = (e - dt.timedelta(days=1)).isoformat(); prev2 = (e - dt.timedelta(days=2)).isoformat()
    F = con.execute("SELECT MAX(expiration_value) FROM kalshi_markets WHERE event_date=?", (E,)).fetchone()[0]
    def snap(hh):
        return con.execute("""SELECT strike, mid, yes_bid, yes_ask, spread FROM kalshi_candles
                              WHERE event_date=? AND period_min=60 AND end_et=?""", (E, f"{prev} {hh}")).fetchall()
    sN, sC = snap("10:00"), snap("23:00")
    muN = ladder_forecast([(r[0], r[1]) for r in sN]); muC = ladder_forecast([(r[0], r[1]) for r in sC])
    # the "bet": favorite line closest to 75c at 10 AM (same rule as sim_favorites.py)
    best = None
    for k, m, b, a, s in sN:
        if s is None or s > 0.10: continue
        for side, p, win in (("YES", a, F > k), ("NO", 1 - b, F <= k)):
            if 0.60 <= p <= 0.85 and (best is None or abs(p - 0.75) < abs(best[2] - 0.75)):
                best = (side, k, p, win)
    a_prev = aaa.get(prev)
    h1 = ho_close_before(prev); h2 = ho_close_before(prev2)          # HO close on bet day vs day before
    h7 = ho_close_before(prev2, 4)                                      # ~5 trading days before bet day
    b1 = last_on_or_before(sorted(brent), brent, prev)[1]
    deliv = (a_prev - h2 - 0.6026) if (a_prev and h2) else None        # delivery slice known at bet time
    r = dict(event_date=E, aaa_prev=a_prev, F_aaa=F,
             d_aaa=round(F - a_prev, 4) if a_prev else None,
             mu_N=round(muN, 4) if muN else None, mu_C=round(muC, 4) if muC else None,
             info_gap=round(muC - muN, 4) if muN and muC else None,
             miss_N=round(F - muN, 4) if muN else None, miss_C=round(F - muC, 4) if muC else None,
             bet_side=best[0] if best else None, bet_strike=best[1] if best else None,
             N_price=round(best[2], 2) if best else None, F_payout=(1 if best[3] else 0) if best else None,
             ho_bet_day_move=round(h1 - h2, 4) if h1 and h2 else None,
             ho_prior5_move=round(h2 - h7, 4) if h2 and h7 else None,
             delivery_at_bet=round(deliv, 4) if deliv else None, brent_bet_day=b1)
    out.append(r)

con.execute("DROP TABLE IF EXISTS daily_story")
cols = list(out[0])
con.execute(f"CREATE TABLE daily_story ({', '.join(cols)})")
con.executemany(f"INSERT INTO daily_story VALUES ({','.join('?'*len(cols))})", [tuple(r[c] for c in cols) for r in out])
con.commit()
with open(ROOT / "data" / "exports" / "daily_story.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)

# ---------- analysis ----------
def ols(y, X, names):
    X = np.column_stack([np.ones(len(y))] + X); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ b; r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(zip(["const"] + names, np.round(b, 4))), round(float(r2), 3)

ok = [r for r in out if r["d_aaa"] is not None and r["ho_bet_day_move"] is not None and r["ho_prior5_move"] is not None and r["delivery_at_bet"] is not None]
y = np.array([r["d_aaa"] for r in ok])
X = [np.array([r["ho_bet_day_move"] for r in ok]), np.array([r["ho_prior5_move"] for r in ok]), np.array([r["delivery_at_bet"] for r in ok])]
print(f"[1] WHY AAA moved (n={len(ok)}): d_aaa ~ HO move on bet day + HO prior 5 days + delivery slice")
print("   ", *ols(y, X, ["ho_bet_day", "ho_prior5", "delivery"]))
ok2 = [r for r in ok if r["info_gap"] is not None and r["miss_N"] is not None]
print(f"[2] What the market LEARNED during the day (n={len(ok2)}): info_gap ~ HO move on bet day")
print("   ", *ols(np.array([r["info_gap"] for r in ok2]), [np.array([r["ho_bet_day_move"] for r in ok2])], ["ho_bet_day"]))
print("    miss at bet time ~ HO bet-day move + prior5 + delivery")
print("   ", *ols(np.array([r["miss_N"] for r in ok2]), [np.array([r[k] for r in ok2]) for k in ("ho_bet_day_move", "ho_prior5_move", "delivery_at_bet")], ["ho_bet_day", "ho_prior5", "delivery"]))
bets = [r for r in out if r["N_price"] is not None]
W = [r for r in bets if r["F_payout"] == 1]; L = [r for r in bets if r["F_payout"] == 0]
avg = lambda rows, k: round(float(np.mean([abs(r[k]) for r in rows if r[k] is not None])) * 100, 2)
print(f"[3] Bets: {len(W)} wins / {len(L)} losses")
for k in ("miss_N", "info_gap", "ho_bet_day_move", "d_aaa"):
    print(f"    avg |{k}| (cents): wins {avg(W, k)}  losses {avg(L, k)}")
print("    losing days:", [(r["event_date"], r["bet_side"], r["bet_strike"], r["N_price"], r["mu_N"], r["F_aaa"], r["ho_bet_day_move"]) for r in L])

# ---------- win / loss split (placeholder for trend extraction; formula columns added once agreed) ----------
con.execute("DROP VIEW IF EXISTS v_win_loss")
con.execute("""CREATE VIEW v_win_loss AS
    SELECT CASE F_payout WHEN 1 THEN 'WIN' WHEN 0 THEN 'LOSS' END AS outcome, *
    FROM daily_story WHERE F_payout IS NOT NULL ORDER BY outcome, event_date""")
con.commit()
cur = con.execute("SELECT * FROM v_win_loss")
with open(ROOT / "data" / "exports" / "win_loss.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow([d[0] for d in cur.description]); w.writerows(cur.fetchall())
