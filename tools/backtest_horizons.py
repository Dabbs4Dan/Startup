#!/usr/bin/env python3
"""Backtest across time horizons (diesel + gas). Usage: python3 tools/backtest_horizons.py

PART A - daily Kalshi ladders (KXDIESELD, KXAAAGASD) vs our models, bet at 10 AM ET the day before:
  A1 price check  : does a contract priced p win p of the time? (buy at ask + taker fee)
  A2 bias check   : market median (where the ladder crosses 50%) minus the AAA print
  A3 model vs mkt : walk-forward model probability per strike; bet when model - cost >= threshold
PART B - forecast accuracy on years of history, no Kalshi prices needed:
  B1 AAA daily prints  (diesel since 2024-07, gas since 2023-09), horizons 1 / 7 / 30 days
  B2 EIA weekly retail (since 1994),                               horizons 1 / 4 weeks
  Models: no change | momentum | wholesale gap (retail - wholesale vs its 60-day average) | gap + momentum

Rules: every fit is walk-forward (trained only on days before the forecast day); returns are clustered by day;
bootstrap 95% CIs. Wholesale = EIA NY Harbor spot (ULSD for diesel, gasoline for gas), value from 2 days
before the bet day so it was known at bet time.
"""
import sys, os, math, random, statistics as st, collections, datetime as dt, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from warehouse import connect

OUT = os.path.join(os.path.dirname(__file__), "..", "research", "backtests")
os.makedirs(OUT, exist_ok=True)
con = connect()
random.seed(1)

WHOLESALE = {"diesel": "ulsd_spot_nyh", "gas": "gasoline_spot_nyh"}
RETAIL_WEEKLY = {"diesel": "retail_diesel_us", "gas": "retail_regular_us"}
D = dt.timedelta


def fee(p):
    return math.ceil(0.07 * p * (1 - p) * 100) / 100


def boot_ci(xs, k=5000):
    if len(xs) < 3:
        return (float("nan"), float("nan"))
    m = sorted(st.mean(random.choices(xs, k=len(xs))) for _ in range(k))
    return m[int(0.025 * k)], m[int(0.975 * k)]


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def series(product):
    aaa = {r[0]: r[1] for r in con.sql(f"select date, value from aaa_daily where product='{product}'").fetchall()}
    wh = {r[0]: r[1] for r in con.sql(f"select date, value from spot_daily where series='{WHOLESALE[product]}'").fetchall()}
    return aaa, wh


def last_on_or_before(d, s, maxback=5):
    for i in range(maxback + 1):
        v = s.get(d - D(i))
        if v is not None:
            return v
    return None


def gap_feature(d, aaa, wh):
    """retail - wholesale at day d, minus its trailing 60-day average (needs >= 20 points)."""
    g0 = None
    a, w = aaa.get(d), last_on_or_before(d, wh)
    if a is None or w is None:
        return None
    g0 = a - w
    hist = []
    for i in range(1, 61):
        x = d - D(i)
        a2, w2 = aaa.get(x), last_on_or_before(x, wh)
        if a2 is not None and w2 is not None:
            hist.append(a2 - w2)
    if len(hist) < 20:
        return None
    return g0 - st.mean(hist)


def features(t, aaa, wh, h):
    """Known at day t (latest AAA print = t, wholesale up to t-1). Target = AAA(t+h) - AAA(t)."""
    a = aaa.get(t)
    a_back = aaa.get(t - D(h)) if h > 1 else aaa.get(t - D(1))
    gap = gap_feature(t - D(1), aaa, wh)  # wholesale lags a day
    w1, w6 = last_on_or_before(t - D(1), wh), last_on_or_before(t - D(6), wh)
    if None in (a, a_back, gap, w1, w6):
        return None
    return {"mom": a - a_back, "gap": gap, "wmove": w1 - w6}


MODELS = {
    "no change": [],
    "momentum": ["mom"],
    "wholesale gap": ["gap", "wmove"],
    "gap + momentum": ["gap", "wmove", "mom"],
}


def walk_forward(rows, cols, min_train=40):
    """rows: list of (date, feats, y). Returns list of (date, pred, resid_sd)."""
    out = []
    for i, (d, f, y) in enumerate(rows):
        train = [r for r in rows[:i] if r[0] < d]
        if len(train) < min_train:
            continue
        if not cols:
            out.append((d, 0.0, float(np.std([r[2] for r in train])) or 0.005, y))
            continue
        X = np.column_stack([np.ones(len(train))] + [[r[1][c] for r in train] for c in cols])
        Y = np.array([r[2] for r in train])
        b, *_ = np.linalg.lstsq(X, Y, rcond=None)
        res = Y - X @ b
        x = np.array([1.0] + [f[c] for c in cols])
        out.append((d, float(x @ b), float(np.std(res)) or 0.005, y))
    return out


# ------------------------------------------------------------------ PART B: forecast accuracy on history
def part_b_daily(product):
    aaa, wh = series(product)
    days = sorted(aaa)
    res = {}
    for h in (1, 7, 30):
        rows = []
        for t in days:
            y_end = aaa.get(t + D(h))
            f = features(t, aaa, wh, h)
            if y_end is None or f is None:
                continue
            rows.append((t, f, y_end - aaa[t]))
        res[h] = {}
        for name, cols in MODELS.items():
            wf = walk_forward(rows, cols)
            if not wf:
                continue
            mae = st.mean(abs(p - y) for _, p, _, y in wf) * 100
            res[h][name] = (round(mae, 2), len(wf))
    return res


def part_b_weekly(product):
    rows_raw = con.sql(f"select date, value from eia_weekly where series='{RETAIL_WEEKLY[product]}' order by date").fetchall()
    wh_s = {r[0]: r[1] for r in con.sql(f"select date, value from spot_daily where series='{WHOLESALE[product]}'").fetchall()}
    dates = [r[0] for r in rows_raw]
    val = dict(rows_raw)
    res = {}
    for hw in (1, 4):
        rows = []
        for i, t in enumerate(dates):
            if i < 12 or i + hw >= len(dates):
                continue
            w1, w2 = last_on_or_before(t - D(1), wh_s), last_on_or_before(t - D(8), wh_s)
            gaps = []
            for j in range(1, 9):
                wj = last_on_or_before(dates[i - j] - D(1), wh_s)
                if wj is not None:
                    gaps.append(val[dates[i - j]] - wj)
            if w1 is None or w2 is None or len(gaps) < 5:
                continue
            f = {"mom": val[t] - val[dates[i - hw]], "gap": (val[t] - w1) - st.mean(gaps), "wmove": w1 - w2}
            rows.append((t, f, val[dates[i + hw]] - val[t]))
        res[hw] = {}
        for name, cols in MODELS.items():
            wf = walk_forward(rows, cols, min_train=104)
            if wf:
                res[hw][name] = (round(st.mean(abs(p - y) for _, p, _, y in wf) * 100, 2), len(wf))
    return res


# ------------------------------------------------------------------ PART A: daily ladders vs market
def ladders(product):
    df = con.sql(f"""
      WITH s AS (SELECT event_date, strike, yes_bid, yes_ask,
                 (ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York') AS ts_et
                 FROM ladder WHERE product='{product}' AND source='candle_60m')
      SELECT event_date, strike, yes_bid, yes_ask FROM s
      WHERE ts_et::DATE = event_date - INTERVAL 1 DAY AND strftime(ts_et, '%H') = '10'
        AND yes_bid IS NOT NULL AND yes_ask IS NOT NULL""").fetchall()
    by = collections.defaultdict(list)
    for e, k, b, a in df:
        by[e].append((float(k), float(b), float(a)))
    return by


def market_median(lad):
    pts = sorted((k, (b + a) / 2) for k, b, a in lad if a - b <= 0.10)
    for (k1, m1), (k2, m2) in zip(pts, pts[1:]):
        if m1 >= 0.5 >= m2 and m1 != m2:
            return k1 + (m1 - 0.5) / (m1 - m2) * (k2 - k1)
    return None


def part_a(product):
    aaa, wh = series(product)
    lads = ladders(product)
    out = {"days": 0}
    # A1 price check
    buckets = collections.defaultdict(lambda: [0, 0, 0.0])
    day_ret_all = collections.defaultdict(list)
    for e, lad in lads.items():
        y = aaa.get(e)
        if y is None:
            continue
        for k, b, a in lad:
            if a - b > 0.10:
                continue
            for price, win in ((a, y > k), (1 - b, not (y > k))):
                if 0.05 <= price <= 0.95:
                    c = price + fee(price)
                    bk = min(int(price * 10), 9)
                    buckets[bk][0] += 1
                    buckets[bk][1] += int(win)
                    buckets[bk][2] += c
                    day_ret_all[(e, bk)].append(((1 - c) if win else -c) / c)
    a1 = []
    for bk in sorted(buckets):
        n, w, csum = buckets[bk]
        drs = collections.defaultdict(list)
        for (e, b2), v in day_ret_all.items():
            if b2 == bk:
                drs[e].append(st.mean(v))
        dr = [st.mean(v) for v in drs.values()]
        lo, hi = boot_ci(dr)
        a1.append({"price": f"{bk*10}-{bk*10+10}c", "bets": n, "win%": round(100 * w / n, 1),
                   "cost%": round(100 * csum / n, 1), "ret/$": round(100 * st.mean(dr), 1),
                   "ci": (round(100 * lo, 1), round(100 * hi, 1))})
    out["A1"] = a1
    # A2 bias check
    miss, miss_fall, miss_rise = [], [], []
    for e, lad in lads.items():
        y, y0 = aaa.get(e), aaa.get(e - D(1))
        m = market_median(lad)
        if y is None or m is None:
            continue
        miss.append((m - y) * 100)
        if y0 is not None:
            (miss_fall if y < y0 else miss_rise).append((m - y) * 100)
    out["A2"] = {"n": len(miss), "mean_miss_c": round(st.mean(miss), 2), "abs_miss_c": round(st.mean(map(abs, miss)), 2),
                 "falling_days": (len(miss_fall), round(st.mean(miss_fall), 2) if miss_fall else None),
                 "rising_days": (len(miss_rise), round(st.mean(miss_rise), 2) if miss_rise else None)}
    # A3 model vs market. Bet day = e-1 at 10 AM; latest print known = AAA(e-1). Target = AAA(e) - AAA(e-1).
    all_days = sorted(aaa)
    rows = []
    for t in all_days:
        f = features(t, aaa, wh, 1)
        y1 = aaa.get(t + D(1))
        if f is not None and y1 is not None:
            rows.append((t, f, y1 - aaa[t]))
    a3 = {}
    for name, cols in MODELS.items():
        preds = {d + D(1): (aaa[d] + p, sd) for d, p, sd, _ in walk_forward(rows, cols)}
        mae_model, mae_mkt = [], []
        for thr in (0.05, 0.08):
            day_rets = collections.defaultdict(list)
            for e, lad in lads.items():
                y = aaa.get(e)
                if y is None or e not in preds:
                    continue
                mu, sd = preds[e]
                for k, b, a in lad:
                    if a - b > 0.10:
                        continue
                    p_yes = 1 - ncdf((k - mu) / max(sd, 0.002))
                    for p_mod, price, win in ((p_yes, a, y > k), (1 - p_yes, 1 - b, not (y > k))):
                        if not (0.03 <= price <= 0.97):
                            continue
                        c = price + fee(price)
                        if p_mod - c >= thr:
                            day_rets[e].append(((1 - c) if win else -c) / c)
            dr = [st.mean(v) for v in day_rets.values()]
            nb = sum(len(v) for v in day_rets.values())
            lo, hi = boot_ci(dr)
            a3[f"{name} | edge>={int(thr*100)}%"] = {"bet_days": len(dr), "bets": nb, "ret/$": round(100 * st.mean(dr), 1) if dr else None,
                               "ci": (round(100 * lo, 1), round(100 * hi, 1)) if dr else None}
        for e, lad in lads.items():
            y, m = aaa.get(e), market_median(lad)
            if y is not None and m is not None and e in preds:
                mae_model.append(abs(preds[e][0] - y) * 100)
                mae_mkt.append(abs(m - y) * 100)
        if mae_model:
            a3[f"{name} | miss"] = {"days": len(mae_model), "model_miss_c": round(st.mean(mae_model), 2),
                                  "market_miss_c": round(st.mean(mae_mkt), 2)}
    out["A3"] = a3
    out["days"] = len([e for e in lads if aaa.get(e) is not None])
    out["range"] = (str(min(lads)), str(max(lads)))
    return out


if __name__ == "__main__":
    report = {}
    for product in ("diesel", "gas"):
        print(f"\n================ {product.upper()} ================")
        a = part_a(product)
        report[product] = {"A": a}
        print(f"PART A daily ladders, {a['days']} days {a['range']}")
        print(" A1 price check (buy at ask + fee, day-clustered):")
        for r in a["A1"]:
            print("   ", r)
        print(" A2 bias:", a["A2"])
        print(" A3 model vs market:")
        for k, v in a["A3"].items():
            print("   ", k, v)
        bd = part_b_daily(product)
        bw = part_b_weekly(product)
        report[product]["B_daily"] = bd
        report[product]["B_weekly"] = bw
        print(" PART B1 AAA daily history, mean miss in cents (n):")
        for h, v in bd.items():
            print(f"   {h:>2}d", v)
        print(" PART B2 EIA weekly since 1994, mean miss in cents (n):")
        for h, v in bw.items():
            print(f"   {h}w", v)
    with open(os.path.join(OUT, "2026-11-26_horizons.json"), "w") as fh:
        json.dump(report, fh, default=str, indent=1)
