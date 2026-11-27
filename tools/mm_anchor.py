#!/usr/bin/env python3
"""Anchor engine: the market-maker equation with the heavy lifting done by big outside data.

Step 1 (no Kalshi data): fit the pump-price engine on real-world history.
  long engine  = EIA weekly pump price vs NY Harbor wholesale spot, 2006 on, 1-6 weeks ahead
  short engine = AAA daily vs front futures, 1-6 days ahead
  Each gives the expected move AND the range (size of its own misses, scaled by wholesale jumpiness).
  Rockets and feathers: the gap and the weekly wholesale move are split into up and down.
Step 2 (Kalshi, 2 dials per market per layer):
  crowd expected move = k0 + k1 * engine move        log(crowd range) = c0 + c1 * log(engine range)
Scores: last 40% of events in time order (engine fit only on earlier dates) and odd/even events.
Plan: research/LOG.md 2026-11-27 "anchor engine". Out: research/engine_room/mm_anchor_scorecard.csv, mm_anchor_engine.csv
"""
import pathlib
import numpy as np
import pandas as pd
from mm_model import ols, pr, r2, split, ncdf

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER, HIST, OUT = ROOT / "data/lake/master", ROOT / "data/lake/history", ROOT / "research/engine_room"
FUELS = {"gas": dict(retail="eia_retail_regular_us", spot="eia_gasoline_spot_nyh", fut="fut_rbob", aaa="aaa_gas"),
         "diesel": dict(retail="eia_retail_diesel_us", spot="eia_ulsd_spot_nyh", fut="fut_ho", aaa="aaa_diesel")}
LONG_X = ["dR7", "gap_up", "gap_dn", "dW7_up", "dW7_dn", "dW28"]
SHORT_X = ["chg1", "chg5", "gap_up", "gap_dn", "dW3", "dW7_up", "dW7_dn"]
LONG_START = "2006-07-01"


def ser(name):
    d = pd.read_csv(HIST / f"{name}.csv", parse_dates=["date"])
    return d.set_index("date")["value"].astype(float).sort_index() * 100       # cents


def wholesale_state(w):
    """w = wholesale in cents on a calendar-day grid (forward-filled)."""
    s = pd.DataFrame({"W": w})
    s["dW3"], s["dW7"], s["dW28"] = w - w.shift(3), w - w.shift(7), w - w.shift(28)
    s["vol"] = w.diff().abs().rolling(28, min_periods=14).mean() * 7 / 5          # average trading-day move
    s["dW7_up"], s["dW7_dn"] = s.dW7.clip(lower=0), s.dW7.clip(upper=0)
    return s


def long_panel(fuel):
    f = FUELS[fuel]
    r = ser(f["retail"])
    w = ser(f["spot"])
    cal = pd.date_range(w.index.min(), w.index.max() + pd.Timedelta(days=5))
    ws = wholesale_state(w.reindex(cal, method="ffill", limit=10))
    p = pd.DataFrame({"R": r})
    p = p.join(ws.shift(3), how="left")                                           # Monday knows wholesale through Friday
    p["dR7"] = p.R - p.R.shift(1)
    margin = p.R - p.W
    gap = margin - margin.shift(1).rolling(26, min_periods=12).mean()
    p["gap_up"], p["gap_dn"] = gap.clip(lower=0), gap.clip(upper=0)
    for h in range(1, 7):
        p[f"y{h}"] = p.R.shift(-h) - p.R
        p[f"t{h}"] = p.index + pd.Timedelta(days=7 * h)
    return p[p.index >= LONG_START]


def daily_state(fuel, inp):
    f = FUELS[fuel]
    a = (inp[f["aaa"]] * 100).ffill(limit=3)
    s = wholesale_state((inp[f["fut"]] * 100).ffill(limit=5))
    s["aaa"] = a
    s["chg1"], s["chg5"], s["dR7"] = a - a.shift(1), a - a.shift(5), a - a.shift(7)
    margin = a - s.W
    gap = margin - margin.shift(1).rolling(182, min_periods=60).mean()
    s["gap_up"], s["gap_dn"] = gap.clip(lower=0), gap.clip(upper=0)
    real = inp[f["aaa"]].notna()
    for h in range(1, 7):
        s[f"y{h}"] = (a.shift(-h) - a).where(real & real.shift(-h, fill_value=False))
        s[f"t{h}"] = s.index + pd.Timedelta(days=h)
    return s


def fit_engine(panel, xcols, cutoff):
    """Direct fit per horizon: move and size-of-miss, using only targets dated before `cutoff`."""
    eng = {}
    for h in range(1, 7):
        d = panel.dropna(subset=xcols + [f"y{h}", "vol"])
        d = d[d[f"t{h}"] < cutoff]
        if len(d) < 80:
            return None
        b = ols(d[xcols].values, d[f"y{h}"].values)
        miss = np.abs(d[f"y{h}"].values - pr(b, d[xcols].values))
        eng[h] = dict(b=b, s=ols(d[["vol"]].values, miss), n=len(d), r2=r2(d[f"y{h}"].values, pr(b, d[xcols].values)), mae=float(miss.mean()))
    return eng


def apply_engine(short, long, st, hdays):
    """Engine move and range (cents) for rows of state `st` at horizon `hdays` (array of ints)."""
    move, rng = np.full(len(st), np.nan), np.full(len(st), np.nan)

    def one(eng, xcols, h, idx):
        return pr(eng[h]["b"], st.iloc[idx][xcols].values), 1.2533 * np.clip(pr(eng[h]["s"], st.iloc[idx][["vol"]].values), 0.05, None)
    for h in np.unique(hdays):
        idx = np.where(hdays == h)[0]
        if h <= 6:
            move[idx], rng[idx] = one(short, SHORT_X, int(max(h, 1)), idx)
        else:
            wk = min(h / 7, 6.0)
            lo, hi = int(np.floor(wk)), int(np.ceil(wk))
            m1, r1 = one(long, LONG_X, lo, idx)
            m2, r2_ = one(long, LONG_X, hi, idx)
            t = wk - lo
            move[idx], rng[idx] = m1 * (1 - t) + m2 * t, r1 * (1 - t) + r2_ * t
    return move, rng


def main():
    inp = pd.read_csv(MASTER / "inputs_daily.csv", parse_dates=["date"], low_memory=False).set_index("date")
    m = pd.read_csv(MASTER / "backtest_master.csv.gz", low_memory=False, parse_dates=["settle_date", "asof_date", "snapshot_date"])
    m = m[m.answer_may_be_public == 0].copy()
    m["center"] = m.crowd_center.fillna(m.crowd_center_fit)
    m["width"] = m.crowd_sigma_fit_c.fillna(m.crowd_sigma_c)
    m["exp_move"] = (m.center - m.aaa_known_filled) * 100
    m["lt"] = np.log(m.hours_to_close.clip(lower=0) / 24 + 0.15)
    m["h"] = (m.settle_date - m.asof_date).dt.days.clip(lower=1)
    lines = pd.read_csv(MASTER / "ladder_snapshots.csv.gz", low_memory=False)
    panels = {f: (long_panel(f), daily_state(f, inp)) for f in FUELS}
    score, engrows, dials = [], [], {}
    order = [("gas", "daily"), ("gas", "weekly"), ("gas", "monthly"), ("diesel", "daily"), ("diesel", "weekly"), ("diesel", "monthly")]
    for fuel, hz in order:
        g = m[(m.fuel == fuel) & (m.horizon == hz) & m.center.notna()].sort_values("settle_date").copy()
        lp, ds = panels[fuel]
        row = {"fuel": fuel, "slice": hz, "events": g.event.nunique(), "rows": len(g)}
        tr, te, n_tr, n_te = split(g)
        borrowed = n_tr < 5 or n_te < 3
        cutoff = g.snapshot_date.min() if borrowed else te.snapshot_date.min()
        short, long = fit_engine(ds, SHORT_X, cutoff), fit_engine(lp, LONG_X, cutoff)
        if short is None or long is None:
            row["note"] = "engine could not be fit"
            score.append(row)
            continue
        for name, eng in (("short (AAA daily, days ahead)", short), ("long (EIA weekly, weeks ahead)", long)):
            for h, e in eng.items():
                engrows.append({"fuel": fuel, "slice": hz, "engine": name, "ahead": h, "rows_fit": e["n"], "explained_in_fit": round(e["r2"], 2), "typical_miss_c": round(e["mae"], 2)})
        st = ds.reindex(g.asof_date.values)
        g["eng_move"], g["eng_range"] = apply_engine(short, long, st, g.h.values)
        g = g.dropna(subset=["eng_move", "eng_range", "exp_move"])
        g["lw"], g["le"] = np.log(g.width.clip(lower=0.03)), np.log(g.eng_range)
        row.update({"engine_rows_long": long[1]["n"], "engine_rows_short": short[1]["n"], "rows_with_engine": len(g)})
        if borrowed:
            k, c = dials.get(("gas", hz), (None, None))
            if k is not None:
                w = g.dropna(subset=["lw"])
                row.update({"note": "too few events: dials borrowed from gas, not proven", "events_scored": g.event.nunique(),
                            "center_explained_last40": round(r2(g.exp_move.values, pr(k, g[["eng_move"]].values)), 2),
                            "center_miss_c": round(float(np.median(np.abs(g.exp_move.values - pr(k, g[["eng_move"]].values)))), 2),
                            "width_explained_last40": round(r2(w.lw.values, pr(c, w[["le"]].values)), 2),
                            "width_typical_error_pct": round(float(np.median(np.abs(np.exp(pr(c, w[["le"]].values) - w.lw.values) - 1)) * 100))})
            score.append(row)
            continue
        tr, te, n_tr, n_te = split(g)
        k = ols(tr[["eng_move"]].values, tr.exp_move.values)
        p = pr(k, te[["eng_move"]].values)
        wtr, wte = tr.dropna(subset=["lw"]), te.dropna(subset=["lw"])
        c = ols(wtr[["le"]].values, wtr.lw.values)
        pw = pr(c, wte[["le"]].values)
        dials[(fuel, hz)] = (k, c)
        t2 = te[["event", "snapshot_et", "aaa_known_filled"]].copy()
        t2["c_model"], t2["w_model"] = te.aaa_known_filled.values + p / 100, np.exp(pr(c, te[["le"]].values)) / 100
        t2["w_flat"] = float(np.exp(wtr.lw.mean())) / 100
        l = lines.merge(t2, on=["event", "snapshot_et"])
        mid, sp = (l.yes_bid + l.yes_ask) / 2, l.yes_ask - l.yes_bid
        ok = (mid > 0.03) & (mid < 0.97) & (sp <= 0.10 + 1e-9)
        l, mid, sp = l[ok], mid[ok], sp[ok]
        if len(l) > 20:
            pm = 1 - ncdf((l.floor_strike - l.c_model) / l.w_model.clip(lower=1e-4))
            p0 = 1 - ncdf((l.floor_strike - l.aaa_known_filled) / l.w_flat)
            row.update({"lines_scored": len(l), "line_gap_pts": round(float(np.median(np.abs(pm - mid)) * 100), 1),
                        "line_gap_no_model_pts": round(float(np.median(np.abs(p0 - mid)) * 100), 1),
                        "typical_spread_pts": round(float(sp.median() * 100), 1),
                        "lines_inside_bid_ask_pct": round(float(((pm >= l.yes_bid - 1e-9) & (pm <= l.yes_ask + 1e-9)).mean() * 100)),
                        "lines_within_3pts_pct": round(float((np.abs(pm - mid) <= 0.03).mean() * 100)),
                        "lines_within_3pts_no_model_pct": round(float((np.abs(p0 - mid) <= 0.03).mean() * 100))})
        c3 = ols(wtr[["le", "lt"]].values, wtr.lw.values)
        pw3 = pr(c3, wte[["le", "lt"]].values)
        gw = g.dropna(subset=["lw"])
        evs = gw.sort_values("settle_date").drop_duplicates("event").event.tolist()
        a_, b_ = gw[gw.event.isin(set(evs[::2]))], gw[~gw.event.isin(set(evs[::2]))]
        row.update({"width3_dial_engine": round(float(c3[1]), 3), "width3_dial_time_left": round(float(c3[2]), 3),
                    "width3_explained_last40": round(r2(wte.lw.values, pw3), 2),
                    "width3_explained_odd_even": round(float(np.mean([r2(v.lw.values, pr(ols(u[["le", "lt"]].values, u.lw.values), v[["le", "lt"]].values)) for u, v in ((a_, b_), (b_, a_))])), 2),
                    "width3_typical_error_pct": round(float(np.median(np.abs(np.exp(pw3 - wte.lw.values) - 1)) * 100))})

        def odd_even(d, x, y):
            evs = d.sort_values("settle_date").drop_duplicates("event").event.tolist()
            a, b = d[d.event.isin(set(evs[::2]))], d[~d.event.isin(set(evs[::2]))]
            return round(float(np.mean([r2(v[y].values, pr(ols(u[[x]].values, u[y].values), v[[x]].values)) for u, v in ((a, b), (b, a))])), 2)
        truth = (te.settle_value - te.aaa_known_filled) * 100
        row.update({"events_fit": n_tr, "events_scored": n_te,
                    "center_dial_k0": round(float(k[0]), 3), "center_dial_k1": round(float(k[1]), 3),
                    "center_explained_last40": round(r2(te.exp_move.values, p), 2), "center_explained_odd_even": odd_even(g, "eng_move", "exp_move"),
                    "center_miss_c": round(float(np.median(np.abs(te.exp_move.values - p))), 2),
                    "width_dial_c0": round(float(c[0]), 3), "width_dial_c1": round(float(c[1]), 3),
                    "width_explained_last40": round(r2(wte.lw.values, pw), 2), "width_explained_odd_even": odd_even(g.dropna(subset=["lw"]), "le", "lw"),
                    "width_typical_error_pct": round(float(np.median(np.abs(np.exp(pw - wte.lw.values) - 1)) * 100)),
                    "width_error_if_no_model_pct": round(float(np.median(np.abs(np.exp(wtr.lw.mean() - wte.lw.values) - 1)) * 100)),
                    "hint_engine_miss_to_aaa_c": round(float(np.median(np.abs(truth - te.eng_move))), 2),
                    "hint_crowd_miss_to_aaa_c": round(float(np.median(np.abs(truth - te.exp_move))), 2),
                    "hint_engine_range_vs_actual_miss": round(float(np.median(te.eng_range) / max(np.median(np.abs(truth - te.eng_move)) * 1.4826, 1e-6)), 2)})
        score.append(row)
    s, e = pd.DataFrame(score), pd.DataFrame(engrows)
    s.to_csv(OUT / "mm_anchor_scorecard.csv", index=False)
    e.to_csv(OUT / "mm_anchor_engine.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.set_index(["fuel", "slice"]).T.to_string())
    print(e[e.slice == "weekly"].to_string(index=False))


if __name__ == "__main__":
    main()
