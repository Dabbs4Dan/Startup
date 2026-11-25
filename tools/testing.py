#!/usr/bin/env python3
"""Testing framework v0 ("system bones"): slice the 60-day panel into tests, layer by layer.

Two betting units:
  DAY  = one Goldilocks favorite per day at 10 AM (Yes or No side priced 75-85c, the one closest to 80c).
  LINE = every line/side priced 60-97c at 10 AM that passes the liquidity filter (traded since open, spread <= 10c).
Buy at the ask + Kalshi taker fee 0.07*P*(1-P). Profit per bet = (1 if win) - price - fee.

Layers:  1 = standard health checks + favorite win/lose (Core)
         2 = one extra condition   (Core, or Computer = decision-tree split depth 1)
         3 = two extra conditions  (Core, or Computer = decision-tree split depth 2)
"What sticks out": inside the slice, compare every number column on WIN bets vs LOSS bets,
standardized gap = (mean_win - mean_loss) / spread of the column; top 3 shown. Needs >= 3 losses.

Writes table `testing_results` + data/exports/testing_results.csv.  Usage: python3 tools/testing.py [days=60]
"""
import sqlite3, csv, pathlib, sys, math, statistics as st, datetime as dt
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import product  # noqa: E402
con = sqlite3.connect(product.DB)
N_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
MIN_N = 15

cols = [d[1] for d in con.execute("PRAGMA table_info(panel_daily)")]
panel = [dict(zip(cols, r)) for r in con.execute("SELECT * FROM panel_daily WHERE aaa_settled IS NOT NULL ORDER BY event_date")]
START = sys.argv[2] if len(sys.argv) > 2 else None      # optional window: testing.py 0 2026-08-03 2026-09-25
END = sys.argv[3] if len(sys.argv) > 3 else ("2026-11-24" if product.PRODUCT == "diesel" else "9999-12-31")
if START:
    panel = [p for p in panel if START <= p["event_date"] <= END]
else:
    panel = [p for p in panel if p["event_date"] <= END][-N_DAYS:]
P = {p["event_date"]: p for p in panel}
fee = lambda p: 0.07 * p * (1 - p)

DAY_FEATS = {  # plain-English names for the "what sticks out" column
    "momentum_yday": "yesterday's AAA move", "aaa_chg_3d": "AAA 3-day change", "aaa_chg_10d": "AAA 10-day change",
    "streak_days": "up/down streak", "ho_chg_1d": "HO 1-day change", "ho_chg_3d": "HO 3-day change", "ho_chg_5d": "HO 5-day change",
    "delivery_gap_vs_090": "delivery slice gap", "refining_slice": "refining slice", "brent_last_close": "Brent price",
    "model_gap_vs_crowd_am": "model vs crowd gap", "am10_crowd_sigma_c": "crowd uncertainty (σ)", "am10_active_lines": "active lines",
    "am10_total_volume": "volume by 10 AM", "weekend": "weekend",
}
CENTS = {"momentum_yday", "aaa_chg_3d", "aaa_chg_10d", "ho_chg_1d", "ho_chg_3d", "ho_chg_5d", "delivery_gap_vs_090",
         "refining_slice", "model_gap_vs_crowd_am", "price", "spread"}
LINE_FEATS = {"price": "price paid", "z": "distance from crowd (σ)", "spread": "spread", "line_volume": "line volume by 10 AM",
              "model_agrees": "model agrees", "is_yes": "Yes side"}


# ---------- build bets ----------
def line_bets():
    out = []
    for E, p in P.items():
        bet = p["bet_day"]
        rows = con.execute("""SELECT strike, end_et, yes_bid, yes_ask, mid, spread, volume FROM kalshi_candles
                              WHERE event_date=? AND period_min=60 AND end_ts<=? ORDER BY strike, end_ts""",
                           (E, int(dt.datetime.fromisoformat(f"{bet} 10:00").replace(tzinfo=ZoneInfo("America/New_York")).timestamp()))).fetchall()
        L = {}
        for k, t, b, a, m, s, v in rows:
            d = L.setdefault(k, dict(vol=0.0)); d["vol"] += v or 0; d.update(bid=b, ask=a, mid=m, spread=s)
        res = dict(con.execute("SELECT strike, result FROM kalshi_markets WHERE event_date=?", (E,)))
        mu, sg = p["am10_crowd_forecast"], (p["am10_crowd_sigma_c"] or 0) / 100
        for k, d in L.items():
            if d["vol"] <= 0 or d["spread"] is None or d["spread"] > 0.10 or k not in res:
                continue
            for side, price in (("YES", d["ask"]), ("NO", None if d["bid"] is None else round(1 - d["bid"], 2))):
                if price is None or not (0.60 <= price <= 0.97):
                    continue
                win = (res[k] == "yes") == (side == "YES")
                mf = p["model_F"]
                agrees = None if mf is None else int((mf > k) == (side == "YES"))
                b = dict(event_date=E, strike=k, side=side, price=price, win=int(win), pnl=(1 if win else 0) - price - fee(price),
                         z=round(abs(k - mu) / sg, 2) if mu and sg else None, spread=d["spread"], line_volume=d["vol"],
                         model_agrees=agrees, is_yes=int(side == "YES"))
                b.update({f: p.get(f) for f in DAY_FEATS})
                out.append(b)
    return out


def day_bets(lines):
    out = []
    for E in P:
        c = [b for b in lines if b["event_date"] == E and 0.75 <= b["price"] < 0.85]
        if c:
            out.append(min(c, key=lambda b: abs(b["price"] - 0.80)))
    return out


LB = line_bets()
DB = day_bets(LB)


# ---------- metrics ----------
def streak(bets):
    worst = cur = 0
    for b in sorted(bets, key=lambda b: (b["event_date"], b["strike"])):
        cur = cur + 1 if not b["win"] else 0
        worst = max(worst, cur)
    return worst


def sticks_out(bets):
    W = [b for b in bets if b["win"]]; L = [b for b in bets if not b["win"]]
    if len(L) < 3 or len(W) < 3:
        return f"too few losses to compare ({len(L)})"
    gaps = []
    for f, name in {**LINE_FEATS, **DAY_FEATS}.items():
        a = [b[f] for b in W if b.get(f) is not None]; c = [b[f] for b in L if b.get(f) is not None]
        allv = a + c
        if len(a) < 3 or len(c) < 3 or len(set(allv)) < 2:
            continue
        sd = st.pstdev(allv)
        if sd == 0:
            continue
        g = (st.mean(a) - st.mean(c)) / sd
        k = 100 if f in CENTS else 1
        gaps.append((abs(g), name + (" (¢)" if k == 100 else ""), st.mean(a) * k, st.mean(c) * k))
    gaps.sort(reverse=True)
    fmt = lambda x: f"{x:.2f}" if abs(x) < 10 else f"{x:.1f}" if abs(x) < 1000 else f"{x:,.0f}"
    return " · ".join(f"{n}: wins {fmt(a)} vs losses {fmt(c)}" for _, n, a, c in gaps[:3]) or "—"


def row(tid, layer, origin, parent, name, rule, unit, bets, note=""):
    n = len(bets); w = sum(b["win"] for b in bets)
    if n == 0:
        return dict(test_id=tid, layer=layer, origin=origin, parent=parent, name=name, rule=rule, unit=unit, n=0, wins=0, losses=0,
                    win_rate="", avg_price="", edge="", profit_per_100="", worst_streak="", sample_flag="⚠️ no bets", sticks_out="", note=note)
    cost = sum(b["price"] + fee(b["price"]) for b in bets)
    return dict(test_id=tid, layer=layer, origin=origin, parent=parent, name=name, rule=rule, unit=unit, n=n, wins=w, losses=n - w,
                win_rate=round(w / n, 3), avg_price=round(st.mean(b["price"] for b in bets), 3),
                edge=round(w / n - st.mean(b["price"] + fee(b["price"]) for b in bets), 3),
                profit_per_100=round(100 * sum(b["pnl"] for b in bets) / cost, 1), worst_streak=streak(bets),
                sample_flag="✅" if n >= MIN_N else f"⚠️ small (<{MIN_N})", sticks_out=sticks_out(bets), note=note)


R = []
first, last = min(P), max(P)
# ---------- LAYER 1: standard checks (Core) ----------
R.append(row("T1.1", 1, "Core", "", "Favorite win vs lose (one bet a day)", "Goldilocks 10 AM favorite, 75–85¢, closest to 80¢", "DAY", DB))
R.append(row("T1.2", 1, "Core", "", "Baseline: always bet every favorite line", "Every line/side 60–97¢ at 10 AM that passes the liquidity filter", "LINE", LB,
             "Every other test must beat this edge."))
for lo, hi in ((0.60, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 0.971)):
    R.append(row(f"T1.3-{int(lo*100)}", 1, "Core", "T1.2", f"Calibration: {int(lo*100)}–{min(97,int(hi*100))}¢ lines",
                 f"Does a {int(lo*100)}–{min(97,int(hi*100))}¢ line win that often?", "LINE", [b for b in LB if lo <= b["price"] < hi],
                 "Edge > 0 = crowd underprices these lines."))
for m in sorted({P[b["event_date"]]["month"] for b in LB}, key=lambda x: dt.datetime.strptime(x, "%b").month):
    R.append(row(f"T1.4-{m}", 1, "Core", "T1.2", f"Stability: {m}", f"Baseline bets in {m}", "LINE", [b for b in LB if P[b["event_date"]]["month"] == m]))
R.append(row("T1.5", 1, "Core", "T1.1", "Costs + streaks", "Same as T1.1; read the fee drag and worst losing streak", "DAY", DB,
             f"Fees ≈ {round(100*st.mean(fee(b['price']) for b in DB)/st.mean(b['price'] for b in DB),1) if DB else 0}% of each stake."))
R.append(dict(test_id="T1.6", layer=1, origin="Core", parent="", name="Fake-pattern guard (holdout rule)",
              rule="From the next phase, the last 3 weeks of any window stay hidden until a brick is proposed, then are checked once.",
              unit="RULE", n="", wins="", losses="", win_rate="", avg_price="", edge="", profit_per_100="", worst_streak="",
              sample_flag="", sticks_out="", note=f"Bones phase: tests below use all {len(P)} days ({first} → {last})."))

# ---------- LAYER 2 + 3: Core slices ----------
def add(tid, layer, parent, name, rule, unit, bets, origin="Core"):
    R.append(row(tid, layer, origin, parent, name, rule, unit, bets))

for side in ("YES", "NO"):
    add(f"T2.1-{side}", 2, "T1.1", f"Favorite on the {side} side", f"T1.1 bets where the favorite was {side}", "DAY", [b for b in DB if b["side"] == side])
    add(f"T2.2-{side}", 2, "T1.2", f"All favorite lines, {side} side", f"T1.2 bets on the {side} side", "LINE", [b for b in LB if b["side"] == side])
for lab, f in (("Weekend", lambda b: b["weekend"] == 1), ("Weekday", lambda b: b["weekend"] == 0)):
    add(f"T2.3-{lab}", 2, "T1.2", f"{lab} bet day", f"T1.2 bets placed on a {lab.lower()}", "LINE", [b for b in LB if f(b)])
for reg in ("feathers (falling)", "flat", "rockets (rising)"):
    add(f"T2.4-{reg.split()[0]}", 2, "T1.2", f"Regime: {reg}", f"10-day AAA change {'< −5¢' if 'fall' in reg else '> +5¢' if 'ris' in reg else 'within ±5¢'}", "LINE",
        [b for b in LB if b["aaa_chg_10d"] is not None and P[b["event_date"]]["regime"] == reg])
add("T2.5-agree", 2, "T1.2", "Model F agrees with the bet", "Model F (no peek) lands on the same side as the bet", "LINE", [b for b in LB if b["model_agrees"] == 1])
add("T2.5-disagree", 2, "T1.2", "Model F disagrees", "Model F lands on the other side", "LINE", [b for b in LB if b["model_agrees"] == 0])
add("T2.6-far", 2, "T1.2", "Line ≥ 1σ from crowd forecast", "Strike at least one crowd-wiggle away from the forecast", "LINE", [b for b in LB if b["z"] is not None and b["z"] >= 1])
add("T2.6-near", 2, "T1.2", "Line < 1σ from crowd forecast", "Strike close to the crowd forecast", "LINE", [b for b in LB if b["z"] is not None and b["z"] < 1])
add("T2.7-HOdown", 2, "T1.2", "Wholesale fell ≥ 5¢ last day", "HO 1-day change ≤ −5¢ (last close known at 10 AM)", "LINE", [b for b in LB if b["ho_chg_1d"] is not None and b["ho_chg_1d"] <= -0.05])
add("T2.7-HOup", 2, "T1.2", "Wholesale rose ≥ 5¢ last day", "HO 1-day change ≥ +5¢", "LINE", [b for b in LB if b["ho_chg_1d"] is not None and b["ho_chg_1d"] >= 0.05])
add("T2.8-tight", 2, "T1.2", "Tight spread (≤ 2¢)", "Liquid lines only", "LINE", [b for b in LB if b["spread"] <= 0.02])

add("T3.1-YES-fall", 3, "T2.2-YES", "YES side × falling regime", "Yes bets when 10-day AAA change < −5¢", "LINE",
    [b for b in LB if b["side"] == "YES" and P[b["event_date"]]["regime"] == "feathers (falling)"])
add("T3.1-NO-fall", 3, "T2.2-NO", "NO side × falling regime", "No bets when 10-day AAA change < −5¢", "LINE",
    [b for b in LB if b["side"] == "NO" and P[b["event_date"]]["regime"] == "feathers (falling)"])
add("T3.2-far-agree", 3, "T2.6-far", "≥ 1σ away × model agrees", "Far from crowd forecast AND model agrees", "LINE",
    [b for b in LB if b["z"] is not None and b["z"] >= 1 and b["model_agrees"] == 1])
add("T3.3-weekend-7585", 3, "T2.3-Weekend", "Weekend × 75–85¢", "Weekend bet day AND price 75–85¢", "LINE",
    [b for b in LB if b["weekend"] == 1 and 0.75 <= b["price"] < 0.85])

# ---------- Computer slices: decision tree (depth 2) ----------
try:
    from sklearn.tree import DecisionTreeClassifier
    feats = list(LINE_FEATS) + [f for f in DAY_FEATS if f != "weekend"] + ["weekend"]
    feats = [f for f in feats if any(b.get(f) is not None for b in LB)]   # drop columns this product does not have
    X, y, keep = [], [], []
    for b in LB:
        v = [b.get(f) for f in feats]
        if any(x is None for x in v):
            continue
        X.append(v); y.append(b["win"]); keep.append(b)
    tree = DecisionTreeClassifier(max_depth=2, min_samples_leaf=MIN_N, random_state=0).fit(X, y)
    t = tree.tree_
    names = {**LINE_FEATS, **DAY_FEATS}
    def walk(node, conds, depth, parent_id):
        if t.feature[node] < 0 or depth == 2:
            return
        f, thr = feats[t.feature[node]], t.threshold[node]
        for kid, op in ((t.children_left[node], "≤"), (t.children_right[node], ">")):
            c2 = conds + [(f, op, thr)]
            sel = [b for b in keep if all((b[ff] <= th) if o == "≤" else (b[ff] > th) for ff, o, th in c2)]
            tid = f"C{depth + 2}.{len([r for r in R if r['origin'] == 'Computer']) + 1}"
            rule = " AND ".join(f"{names[ff]} {o} {th*100:.1f}¢" if ff in CENTS else f"{names[ff]} {o} {th:.3g}" for ff, o, th in c2)
            R.append(row(tid, depth + 2, "Computer", parent_id, f"Tree split: {rule}", rule, "LINE", sel))
            walk(kid, c2, depth + 1, tid)
    walk(0, [], 0, "T1.2")
except Exception as e:  # noqa
    R.append(dict(test_id="C-err", layer=2, origin="Computer", parent="", name=f"decision tree failed: {e}", rule="", unit="", n="",
                  wins="", losses="", win_rate="", avg_price="", edge="", profit_per_100="", worst_streak="", sample_flag="", sticks_out="", note=""))

keys = list(R[0])
TABLE = "testing_results" if not START else "testing_results_unseen"
if START:
    con.execute(f"DROP TABLE IF EXISTS {TABLE}")
    con.execute(f"CREATE TABLE {TABLE} ({', '.join(keys)})")
    con.executemany(f"INSERT INTO {TABLE} VALUES ({','.join('?' * len(keys))})", [tuple(r.get(k) for k in keys) for r in R])
    con.commit()
    with open(product.EXPORTS / f"{TABLE}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(R)
    print(f"{TABLE}: {len(R)} tests | {len(DB)} day bets | {len(LB)} line bets | {first} -> {last}")
    sys.exit(0)
con.execute("DROP TABLE IF EXISTS testing_results")
con.execute(f"CREATE TABLE testing_results ({', '.join(keys)})")
con.executemany(f"INSERT INTO testing_results VALUES ({','.join('?' * len(keys))})", [tuple(r.get(k) for k in keys) for r in R])
con.commit()
with open(product.EXPORTS / "testing_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(R)
print(f"testing_results: {len(R)} tests | {len(DB)} day bets | {len(LB)} line bets | {first} -> {last}")
