#!/usr/bin/env python3
"""Weekly + monthly Kalshi ladders vs our models (diesel KXDIESELW / KXDIESELMON, gas KXAAAGASW / KXAAAGASM).

Data: research/backtests/horizon_ladders/ (pulled on GitHub by tools/pull_horizon_ladders.py), daily candles at
05:00 UTC (= midnight ET). A candle ending on date X 05:00 UTC is a snapshot at the END of ET day s = X - 1.
Known then: AAA print for day s. Horizon h = settle date - s.
Model for horizon h is re-fit for every snapshot on history whose target was already known (t + h <= s).
Usage: python3 tools/backtest_horizon_ladders.py
"""
import csv, os, sys, math, collections, datetime as dt, statistics as st, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import backtest_horizons as bh

HERE = os.path.join(os.path.dirname(__file__), "..", "research", "backtests", "horizon_ladders")
SERIES = {"KXDIESELW": "diesel", "KXDIESELMON": "diesel", "KXAAAGASW": "gas", "KXAAAGASM": "gas"}
MON = {m: i for i, m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"], 1)}
D = dt.timedelta


def settle_date(ev):
    tail = ev.split("-")[1]
    return dt.date(2000 + int(tail[:2]), MON[tail[2:5]], int(tail[5:]))


def load(series):
    mk = {r["ticker"]: r for r in csv.DictReader(open(os.path.join(HERE, f"markets_{series}.csv")))}
    snaps = collections.defaultdict(list)   # (event, snapshot_date) -> [(strike, bid, ask)]
    for r in csv.DictReader(open(os.path.join(HERE, f"candles_{series}.csv"))):
        m = mk.get(r["ticker"])
        if not m or r["yes_bid"] in ("", "None") or r["yes_ask"] in ("", "None"):
            continue
        end = dt.datetime.strptime(r["end_utc"], "%Y-%m-%d %H:%M")
        s = (end - D(hours=5)).date() - D(days=1) if end.hour <= 5 else (end - D(hours=5)).date()
        snaps[(m["event_ticker"], s)].append((float(m["floor_strike"]), float(r["yes_bid"]), float(r["yes_ask"])))
    outcome = {m["event_ticker"]: float(m["expiration_value"]) for m in mk.values() if m["expiration_value"]}
    return snaps, outcome


def fit_predict(rows, cols, s, h):
    train = [r for r in rows if r[0] + D(h) <= s]
    if len(train) < 40:
        return None
    if not cols:
        return 0.0, float(np.std([r[2] for r in train]))
    X = np.column_stack([np.ones(len(train))] + [[r[1][c] for r in train] for c in cols])
    Y = np.array([r[2] for r in train])
    b, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return b, float(np.std(Y - X @ b))


def bucket(h):
    return "1-2d" if h <= 2 else "3-4d" if h <= 4 else "5-7d" if h <= 7 else "8-15d" if h <= 15 else "16-33d"


def run(series):
    product = SERIES[series]
    aaa, wh = bh.series(product)
    snaps, outcome = load(series)
    hist_rows = {}
    miss = collections.defaultdict(lambda: collections.defaultdict(list))
    bets = collections.defaultdict(lambda: collections.defaultdict(list))   # (model,thr) -> event -> returns
    for (ev, s), lad in sorted(snaps.items(), key=lambda x: x[0][1]):
        y = outcome.get(ev)
        h = (settle_date(ev) - s).days
        a0 = aaa.get(s)
        f = bh.features(s, aaa, wh, max(h, 1))
        if y is None or a0 is None or f is None or h < 1:
            continue
        m = bh.market_median(lad)
        if h not in hist_rows:
            rows = []
            for t in sorted(aaa):
                ft, yt = bh.features(t, aaa, wh, h), aaa.get(t + D(h))
                if ft is not None and yt is not None:
                    rows.append((t, ft, yt - aaa[t]))
            hist_rows[h] = rows
        bk = bucket(h)
        if m is not None:
            miss[bk]["market"].append(abs(m - y) * 100)
        for name, cols in bh.MODELS.items():
            fp = fit_predict(hist_rows[h], cols, s, h)
            if fp is None:
                continue
            b, sd = fp
            pred = 0.0 if not cols else float(np.array([1.0] + [f[c] for c in cols]) @ b)
            mu = a0 + pred
            if m is not None:
                miss[bk][name].append(abs(mu - y) * 100)
            for k, bid, ask in lad:
                if ask - bid > 0.10:
                    continue
                p_yes = 1 - bh.ncdf((k - mu) / max(sd, 0.003))
                for p_mod, price, win in ((p_yes, ask, y > k), (1 - p_yes, 1 - bid, not (y > k))):
                    if not (0.03 <= price <= 0.97):
                        continue
                    c = price + bh.fee(price)
                    for thr in (0.05, 0.08):
                        if p_mod - c >= thr:
                            bets[f"{name} | edge>={int(thr*100)}%"][ev].append(((1 - c) if win else -c) / c)
    out = {"events": len({e for e, _ in snaps}), "snapshots": len(snaps), "miss_by_horizon_c": {}, "bets": {}}
    for bk in ["1-2d", "3-4d", "5-7d", "8-15d", "16-33d"]:
        if bk in miss:
            out["miss_by_horizon_c"][bk] = {k: (round(st.mean(v), 2), len(v)) for k, v in miss[bk].items()}
    for key, evs in bets.items():
        er = [st.mean(v) for v in evs.values()]
        lo, hi = bh.boot_ci(er)
        out["bets"][key] = {"events": len(er), "bets": sum(len(v) for v in evs.values()),
                            "ret/$ (event-clustered)": round(100 * st.mean(er), 1),
                            "ci": (round(100 * lo, 1), round(100 * hi, 1))}
    return out


if __name__ == "__main__":
    rep = {}
    for s in SERIES:
        r = run(s)
        rep[s] = r
        print(f"\n===== {s} ({SERIES[s]}): {r['events']} events, {r['snapshots']} daily snapshots")
        print(" mean miss (cents, n) by days-to-settle:")
        for bk, v in r["miss_by_horizon_c"].items():
            print(f"   {bk:>6}", v)
        print(" bets (buy at ask + fee):")
        for k, v in sorted(r["bets"].items()):
            print("   ", k, v)
    json.dump(rep, open(os.path.join(HERE, "..", "2026-11-26_horizon_ladders.json"), "w"), indent=1, default=str)
