#!/usr/bin/env python3
"""60-day research panel: one row per diesel event (AAA settle day), every DAILY input as a column,
Kalshi state at two snapshots (10 AM bet time + last hour before close), point-in-time (no peeking).

Writes table `panel_daily` + data/exports/panel_daily.csv (all settled days; the Sheet shows the last 60).
Usage: python3 tools/panel.py

Snapshot rules (formula #19 "Top-3 liquid pairs"):
  - A line counts as tradeable if: traded at least once since open, spread <= 10c, 3% <= mid <= 97%.
  - Rank tradeable lines by volume traded since open (up to the snapshot). Keep the top 3.
  - Each line is one Yes/No pair: No ask = 1 - Yes bid, No bid = 1 - Yes ask.
Model F (formula #3, 10 AM no-peek version): HO's same-day move is unknown at 10 AM -> set to 0.
"""
import sqlite3, csv, pathlib, datetime as dt, math, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "data" / "kalshi_twins.db")
D = dt.date.fromisoformat
TAX = 0.6026
HOLIDAYS = {"2026-09-07": "Labor Day", "2026-10-12": "Columbus Day", "2026-11-11": "Veterans Day",
            "2026-11-26": "Thanksgiving", "2026-12-25": "Christmas", "2026-07-03": "July 4 (obs.)"}
HOLIDAY_WEEKS = {("2026-11-23", "2026-11-29"): "Thanksgiving week", ("2026-09-04", "2026-09-07"): "Labor Day weekend"}

aaa = dict(con.execute("SELECT date, aaa_diesel FROM diesel_daily WHERE aaa_diesel IS NOT NULL"))
ho = dict(con.execute("SELECT date, ulsd_nyh_usd_gal FROM diesel_daily WHERE ulsd_nyh_usd_gal IS NOT NULL AND ulsd_source LIKE 'yahoo%'"))
brent = dict(con.execute("SELECT date, brent_usd_bbl FROM diesel_daily WHERE brent_usd_bbl IS NOT NULL AND brent_source LIKE 'yahoo%'"))
ho_days, br_days = sorted(ho), sorted(brent)

# Optional: HO price at 10 AM ET from Yahoo 5-min bars (written by tools/pull_ho_intraday.py on GitHub)
ho10 = {}
p = ROOT / "research" / "connectivity" / "ho_10am.json"
if p.exists():
    ho10 = json.loads(p.read_text()).get("ho_10am", {})


def closes_before(days, series, d_iso, n):
    """Last n closes strictly before date d (what is known at 10 AM on d). Newest first."""
    xs = [x for x in days if x < d_iso][-n:][::-1]
    return [(x, series[x]) for x in xs]


def aaa_back(d_iso, k):
    x = (D(d_iso) - dt.timedelta(days=k)).isoformat()
    return aaa.get(x)


def ncdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def fit_ladder(rows):
    """rows [(strike, mid)] -> (mu, sigma) of a bell curve: P(>K) = 1 - Phi((K-mu)/sigma). Grid search, $ units."""
    rows = [(k, m) for k, m in rows if m is not None]
    if len(rows) < 3:
        return None, None
    ks = [k for k, _ in rows]
    best = None
    lo, hi = min(ks) - 0.01, max(ks) + 0.01
    for i in range(int((hi - lo) / 0.0002) + 1):
        mu = lo + i * 0.0002
        for s in (0.0005, 0.0008, 0.001, 0.0013, 0.0016, 0.002, 0.0025, 0.003, 0.0035, 0.004, 0.005, 0.006, 0.008, 0.01, 0.015):
            err = sum((m - (1 - ncdf((k - mu) / s))) ** 2 for k, m in rows)
            if best is None or err < best[0]:
                best = (err, mu, s)
    _, mu, s = best
    # refine sigma finely around best
    for s2 in [s * f for f in (0.8, 0.85, 0.9, 0.95, 1.05, 1.1, 1.15, 1.2)]:
        for dmu in (-0.0002, -0.0001, 0, 0.0001, 0.0002):
            err = sum((m - (1 - ncdf((k - (mu + dmu)) / s2))) ** 2 for k, m in rows)
            if err < best[0]:
                best = (err, mu + dmu, s2)
    return best[1], best[2]


def cross50(rows):
    rows = sorted((k, m) for k, m in rows if m is not None)
    for (k1, m1), (k2, m2) in zip(rows, rows[1:]):
        if m1 >= 0.5 > m2:
            return k1 + (k2 - k1) * (m1 - 0.5) / (m1 - m2) if m1 != m2 else k1
    return None


def snapshot(E, until_et):
    """As-of state of every line at time `until_et` ('YYYY-MM-DD HH:MM'): latest candle <= time + volume since open."""
    rows = con.execute("""SELECT strike, end_et, yes_bid, yes_ask, mid, spread, volume, open_interest
                          FROM kalshi_candles WHERE event_date=? AND period_min=60 AND end_et<=? ORDER BY strike, end_et""",
                       (E, until_et)).fetchall()
    lines = {}
    for k, t, b, a, m, s, v, oi in rows:
        L = lines.setdefault(k, dict(strike=k, vol=0.0))
        L["vol"] += v or 0
        L.update(t=t, bid=b, ask=a, mid=m, spread=s, oi=oi)
    return lines


def pairs_block(lines, result, tag):
    out = {}
    ok = [L for L in lines.values() if L["vol"] > 0 and L["spread"] is not None and L["spread"] <= 0.10
          and L["mid"] is not None and 0.03 <= L["mid"] <= 0.97]
    out[f"{tag}_active_lines"] = len(ok)
    out[f"{tag}_total_volume"] = round(sum(L["vol"] for L in lines.values()))
    top = sorted(ok, key=lambda L: -L["vol"])[:3]
    for i in range(3):
        L = top[i] if i < len(top) else None
        pre = f"{tag}_pair{i+1}"
        out[f"{pre}_strike"] = L["strike"] if L else None
        out[f"{pre}_yes_bid"] = L["bid"] if L else None
        out[f"{pre}_yes_ask"] = L["ask"] if L else None
        out[f"{pre}_no_ask"] = round(1 - L["bid"], 2) if L and L["bid"] is not None else None
        out[f"{pre}_spread"] = L["spread"] if L else None
        out[f"{pre}_volume"] = round(L["vol"]) if L else None
        out[f"{pre}_settled"] = (("YES" if result[L["strike"]] == "yes" else "NO") if L and L["strike"] in result else None)
    return out


events = [r[0] for r in con.execute("SELECT DISTINCT event_date FROM kalshi_markets WHERE expiration_value IS NOT NULL ORDER BY 1")]
out = []
for E in events:
    bet = (D(E) - dt.timedelta(days=1)).isoformat()
    F = con.execute("SELECT MAX(expiration_value) FROM kalshi_markets WHERE event_date=?", (E,)).fetchone()[0]
    result = dict(con.execute("SELECT strike, result FROM kalshi_markets WHERE event_date=?", (E,)))
    a0, a1 = aaa.get(bet), aaa_back(bet, 1)
    r = dict(event_date=E, bet_day=bet, weekday=D(bet).strftime("%a"), weekend=int(D(bet).weekday() >= 5),
             holiday=HOLIDAYS.get(bet, ""), holiday_week=next((v for (s, e), v in HOLIDAY_WEEKS.items() if s <= bet <= e), ""),
             month=D(bet).strftime("%b"))
    # --- target + momentum + trend (all known at bet time) ---
    r.update(aaa_known=a0, aaa_settled=F, aaa_change=round(F - a0, 4) if a0 else None,
             momentum_yday=round(a0 - a1, 4) if a0 and a1 else None)
    for k in (3, 5, 7, 10, 20):
        ak = aaa_back(bet, k)
        r[f"aaa_chg_{k}d"] = round(a0 - ak, 4) if a0 and ak else None
    streak, sign = 0, None
    d = D(bet)
    while True:
        x, y = aaa.get(d.isoformat()), aaa.get((d - dt.timedelta(days=1)).isoformat())
        if x is None or y is None or x == y:
            break
        sg = 1 if x > y else -1
        if sign is None:
            sign = sg
        if sg != sign:
            break
        streak += 1
        d -= dt.timedelta(days=1)
    r["streak_days"] = streak * (sign or 0)
    c10 = r["aaa_chg_10d"]
    r["regime"] = None if c10 is None else ("rockets (rising)" if c10 > 0.05 else "feathers (falling)" if c10 < -0.05 else "flat")
    # --- wholesale + slices (last closes known at 10 AM on bet day) ---
    hc = closes_before(ho_days, ho, bet, 6)
    bc = closes_before(br_days, brent, bet, 1)
    h_last = hc[0][1] if hc else None
    r.update(ho_last_close=h_last, ho_last_close_date=hc[0][0] if hc else None,
             ho_chg_1d=round(hc[0][1] - hc[1][1], 4) if len(hc) > 1 else None,
             ho_chg_3d=round(hc[0][1] - hc[3][1], 4) if len(hc) > 3 else None,
             ho_chg_5d=round(hc[0][1] - hc[5][1], 4) if len(hc) > 5 else None,
             ho_chg_4d_fit=round(hc[0][1] - hc[4][1], 4) if len(hc) > 4 else None,
             ho_10am=ho10.get(bet), brent_last_close=bc[0][1] if bc else None)
    if a0 and h_last and bc:
        crude = bc[0][1] / 42
        r.update(crude_slice=round(crude, 4), refining_slice=round(h_last - crude, 4), taxes=TAX,
                 delivery_slice=round(a0 - h_last - TAX, 4), delivery_gap_vs_090=round(a0 - h_last - TAX - 0.90, 4))
    else:
        r.update(crude_slice=None, refining_slice=None, taxes=TAX, delivery_slice=None, delivery_gap_vs_090=None)
    # --- Model F (no peek): AAA - 6.72% x (delivery - 0.90) + 0 x HO today - 1.30c/$ x HO prior move ---
    # "prior move" = same window the formula was fitted on in story.py (last known close vs 4 closes earlier)
    if a0 and r["delivery_slice"] is not None and r["ho_chg_4d_fit"] is not None:
        r["model_F"] = round(a0 - 0.0672 * (r["delivery_slice"] - 0.90) - 0.0130 * r["ho_chg_4d_fit"], 4)
    else:
        r["model_F"] = None
    # --- Kalshi: 10 AM + close ---
    last_t = con.execute("SELECT MAX(end_et) FROM kalshi_candles WHERE event_date=? AND end_et<=?", (E, f"{E} 01:00")).fetchone()[0]
    for tag, t in (("am10", f"{bet} 10:00"), ("close", last_t)):
        lines = snapshot(E, t) if t else {}
        mids = [(L["strike"], L["mid"]) for L in lines.values()]
        mu50 = cross50(mids)
        mu, sg = fit_ladder(mids) if lines else (None, None)
        r[f"{tag}_time"] = t[11:] if t else None
        r[f"{tag}_crowd_forecast"] = round(mu50, 4) if mu50 else (round(mu, 4) if mu else None)
        r[f"{tag}_crowd_sigma_c"] = round(sg * 100, 3) if sg else None
        # favorite in the Goldilocks zone (75-85c) on either side
        fav = None
        for L in lines.values():
            if L["spread"] is None or L["spread"] > 0.10 or L["vol"] <= 0:
                continue
            for side, pr in (("YES", L["ask"]), ("NO", None if L["bid"] is None else 1 - L["bid"])):
                if pr is not None and 0.75 <= pr < 0.85 and (fav is None or abs(pr - 0.80) < abs(fav[2] - 0.80)):
                    won = (result.get(L["strike"]) == "yes") == (side == "YES")
                    fav = (side, L["strike"], round(pr, 2), "WIN" if won else "LOSS")
        r[f"{tag}_goldilocks_bet"] = f"{fav[0]} >{fav[1]:.3f} @{int(round(fav[2]*100))}c → {fav[3]}" if fav else ""
        r.update(pairs_block(lines, result, tag))
    r["model_gap_vs_crowd_am"] = round(r["model_F"] - r["am10_crowd_forecast"], 4) if r["model_F"] and r["am10_crowd_forecast"] else None
    r["crowd_miss_am_c"] = round((F - r["am10_crowd_forecast"]) * 100, 2) if r["am10_crowd_forecast"] else None
    r["crowd_miss_close_c"] = round((F - r["close_crowd_forecast"]) * 100, 2) if r["close_crowd_forecast"] else None
    r["model_miss_c"] = round((F - r["model_F"]) * 100, 2) if r["model_F"] else None
    r["info_gap_c"] = round((r["close_crowd_forecast"] - r["am10_crowd_forecast"]) * 100, 2) if r["close_crowd_forecast"] and r["am10_crowd_forecast"] else None
    out.append(r)

cols = list(out[0])
con.execute("DROP TABLE IF EXISTS panel_daily")
con.execute(f"CREATE TABLE panel_daily ({', '.join(cols)})")
con.executemany(f"INSERT INTO panel_daily VALUES ({','.join('?' * len(cols))})", [tuple(r.get(c) for c in cols) for r in out])
con.commit()
with open(ROOT / "data" / "exports" / "panel_daily.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(out)
print(f"panel_daily: {len(out)} rows x {len(cols)} cols ({out[0]['event_date']} -> {out[-1]['event_date']})")
