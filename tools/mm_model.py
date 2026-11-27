#!/usr/bin/env python3
"""Market-maker equation for all six markets (Engine Room L0; v1, 2026-11-27).

We cannot see the market makers' code. What we can recover is the RESPONSE: how the ladder's center, width and
shape move with inputs anyone can know. This is the BASELINE COPY Dan wants; edges are later "tweaks" where the
copy and reality disagree.

  A  center   crowd's expected move (c). Two candidates, picked per market on the fit events only:
              A0 linear:        inputs (+ inputs x days for weekly / monthly)
              A1 pass-through:  yesterday's AAA move x how long momentum lasts (decay rho) + retail-vs-wholesale gap
                                and 5-day / 20-day futures moves x share reaching the pump by settle (1-exp(-days/tau))
  B  width    log(crowd width). Three candidates, picked per market on the fit events only:
              S1 time only   S2 + recent AAA jumpiness   S3 + expected move, yesterday's move, last miss, time of day
  C  shape    each line's price = bell curve with the crowd's own center and width; score = median |miss| per line
  D  cost     median spread by price level
  +  calibration: how often the settle lands inside the crowd's +-1 width (a well-sized bell curve gives 68%)

Fit on the first 60% of events (by settle date), score ONCE on the last 40%. Plans were written to research/LOG.md
first (2026-11-27, 4:00 PM and 4:30 PM). Description of pricing, not an edge test.
Writes research/engine_room/mm_model_scorecard.csv and mm_model_coefficients.csv.
"""
import math, pathlib, warnings
import numpy as np, pandas as pd

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER, OUT = ROOT / "data" / "lake" / "master", ROOT / "research" / "engine_room"
LIN = ["aaa_chg_1d_c", "aaa_chg_5d_c", "fut_main_chg_1d_c", "fut_main_chg_5d_c", "retail_gap_c"]
MARKS = ["open", "10am", "noon", "3pm", "6pm", "10pm"]


def ncdf(z):
    return 0.5 * (1 + np.vectorize(math.erf)(z / math.sqrt(2)))


def ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X1, y, rcond=None)[0]


def pr(b, X):
    return np.column_stack([np.ones(len(X)), X]) @ b


def r2(y, p):
    return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum() if len(y) > 5 and y.std() > 0 else np.nan


def split(g, share=0.6):
    evs = g.sort_values("settle_date").drop_duplicates("event").event.tolist()
    cut = set(evs[: max(1, int(len(evs) * share))])
    return g[g.event.isin(cut)], g[~g.event.isin(cut)], len(cut), len(evs) - len(cut)


# ---------------------------------------------------------------- layer A designs
def xa0(d, hz):
    base = d[LIN].values
    return base if hz == "daily" else np.column_stack([base, base * d[["days"]].values])


def xa1(d, rho, tau):
    days = d.days.values
    mom_len = (1 - rho ** np.maximum(days, 0.01)) / (1 - rho)          # how many days of yesterday's move carry forward
    reach = 1 - np.exp(-days / tau)                                    # share of a wholesale move that reaches the pump
    return np.column_stack([d.aaa_chg_1d_c.values * mom_len, d.retail_gap_c.values * reach, d.fut_main_chg_5d_c.values * reach,
                            d.fut_main_chg_20d_c.values * reach, days])


def xa2(d, hz):
    """Scale-free: every input divided by recent AAA jumpiness (target is divided the same way by the caller)."""
    base = d[LIN].values / d[["scale"]].values
    return base if hz == "daily" else np.column_stack([base, base * d[["days"]].values, d.days.values])


def interleaved(g, X, ycol, post=lambda d, p: p):
    evs = g.sort_values("settle_date").drop_duplicates("event").event.tolist()
    odd = set(evs[::2])
    a, b = g[g.event.isin(odd)], g[~g.event.isin(odd)]
    if len(a) < 10 or len(b) < 10:
        return np.nan
    return round(float(np.nanmean([r2(post(v, v[ycol].values) if False else v[ycol].values, pr(ols(X(u), u[ycol].values), X(v))) for u, v in ((a, b), (b, a))])), 2)


def layer_a(g, hz, row, coefs, key):
    need = LIN + ["fut_main_chg_20d_c", "exp_move", "aaa_absmove_20d_c"]
    g = g.dropna(subset=need).copy()
    g["scale"] = g.aaa_absmove_20d_c.clip(lower=0.1)
    g["exp_scaled"] = g.exp_move / g.scale
    tr, te, n_tr, n_te = split(g)
    row.update({"events_fit": n_tr, "events_scored": n_te})
    if n_tr < 5 or n_te < 3:
        row["center_note"] = "too few events to fit"
        return
    y, yt = tr.exp_move.values, te.exp_move.values
    inner_tr, inner_va, _, _ = split(tr, 0.7)
    best = ("A0 linear", None, r2(inner_va.exp_move.values, pr(ols(xa0(inner_tr, hz), inner_tr.exp_move.values), xa0(inner_va, hz))))
    for rho in (0.6, 0.8, 0.9):
        for tau in (5, 10, 20, 40):
            s = r2(inner_va.exp_move.values, pr(ols(xa1(inner_tr, rho, tau), inner_tr.exp_move.values), xa1(inner_va, rho, tau)))
            if pd.notna(s) and (pd.isna(best[2]) or s > best[2]):
                best = ("A1 pass-through", (rho, tau), s)
    s2 = r2(inner_va.exp_move.values, pr(ols(xa2(inner_tr, hz), inner_tr.exp_scaled.values), xa2(inner_va, hz)) * inner_va.scale.values)
    if pd.notna(s2) and (pd.isna(best[2]) or s2 > best[2]):
        best = ("A2 scale-free", "scaled", s2)
    if best[1] == "scaled":
        b = ols(xa2(tr, hz), tr.exp_scaled.values)
        p = pr(b, xa2(te, hz)) * te.scale.values
        row["center_explained_odd_even"] = interleaved(g, lambda d: xa2(d, hz), "exp_scaled")
    else:
        X = (lambda d: xa0(d, hz)) if best[1] is None else (lambda d: xa1(d, *best[1]))
        b = ols(X(tr), y)
        p = pr(b, X(te))
        row["center_explained_odd_even"] = interleaved(g, X, "exp_move")
    b2 = ols(xa2(tr, hz), tr.exp_scaled.values)
    row["center_explained_oos_scale_free"] = round(r2(yt, pr(b2, xa2(te, hz)) * te.scale.values), 2)
    b0 = ols(xa0(tr, hz), y)
    row.update({"center_form": best[0], "center_rho_tau": "" if not isinstance(best[1], tuple) else f"{best[1][0]} / {best[1][1]}",
                "center_explained_oos": round(r2(yt, p), 2), "center_explained_oos_v0": round(r2(yt, pr(b0, xa0(te, hz))), 2),
                "center_miss_c": round(np.median(np.abs(yt - p)), 2), "center_miss_no_model_c": round(np.median(np.abs(yt)), 2)})
    lin_names = LIN + ([f"{k} x days" for k in LIN] if hz != "daily" else [])
    names = lin_names if best[1] is None else ([f"{k} (per unit of jumpiness)" for k in lin_names] + ([] if hz == "daily" else ["drift per day"])) if best[1] == "scaled" else \
        ["yesterday's AAA move x momentum length", "retail gap x reach", "futures 5d move x reach", "futures 20d move x reach", "drift per day"]
    for n, v in zip(["constant"] + names, b):
        coefs.append({**key, "layer": "A center", "term": n, "value": round(float(v), 4)})


# ---------------------------------------------------------------- layer B designs
def xb(d, spec):
    cols = [np.log(d.days.values)]
    if spec == 4:
        return np.column_stack(cols + [np.log(d.aaa_absmove_5d_c.values + 0.05), np.log(d.recent_miss.values + 0.05)])
    if spec >= 2:
        cols += [np.log(d.aaa_absmove_5d_c.values + 0.05), np.log(d.aaa_absmove_20d_c.values + 0.05)]
    if spec >= 3:
        cols += [np.log(d.exp_move.abs().values + 0.1), np.log(d.aaa_chg_1d_c.abs().values + 0.05), np.log(d.prev_miss.abs().values + 0.05)]
        cols += [(d.snapshot == m).astype(float).values for m in MARKS]
    return np.column_stack(cols)


BNAMES = {1: ["log(days left)"], 2: ["log(days left)", "jumpiness 5d", "jumpiness 20d"],
          3: ["log(days left)", "jumpiness 5d", "jumpiness 20d", "size of expected move", "size of yesterday's move", "size of last ladder's miss"] + [f"mark {m}" for m in MARKS],
          4: ["log(days left)", "jumpiness 5d", "crowd's own recent miss (last 5 ladders)"]}


def layer_b(g, row, coefs, key):
    g = g.dropna(subset=["width", "aaa_absmove_5d_c", "aaa_absmove_20d_c", "exp_move", "aaa_chg_1d_c"]).copy()
    g["prev_miss"] = g.prev_event_close_miss_c.fillna(g.prev_event_close_miss_c.abs().median()).fillna(0.3)
    g["recent_miss"] = g.recent_miss.fillna(g.recent_miss.median()).fillna(0.3)
    g["lw"] = np.log(g.width.clip(lower=0.03))
    tr, te, n_tr, n_te = split(g)
    row["width_rows_scored"] = len(te)
    if n_tr < 5 or n_te < 3 or len(te) < 20:
        row["width_note"] = "too few events to fit"
        return
    inner_tr, inner_va, _, _ = split(tr, 0.7)
    scores = {s: r2(inner_va.lw.values, pr(ols(xb(inner_tr, s), inner_tr.lw.values), xb(inner_va, s))) for s in (1, 2, 3, 4)}
    spec = max(scores, key=lambda s: -9 if pd.isna(scores[s]) else scores[s])
    b = ols(xb(tr, spec), tr.lw.values)
    p = pr(b, xb(te, spec))
    base = np.full(len(te), np.median(tr.lw.values))
    b4 = ols(xb(tr, 4), tr.lw.values)
    row["width_explained_oos_S4"] = round(r2(te.lw.values, pr(b4, xb(te, 4))), 2)
    row["width_S4_typical_error_pct"] = round(float(np.median(np.abs(np.exp(pr(b4, xb(te, 4)) - te.lw.values) - 1)) * 100))
    row["width_explained_odd_even_S4"] = interleaved(g, lambda d: xb(d, 4), "lw")
    for n, v in zip(["constant"] + BNAMES[4], ols(xb(g, 4), g.lw.values)):
        coefs.append({**key, "layer": "B width S4 (all rows)", "term": n, "value": round(float(v), 4)})
    row.update({"width_form": f"S{spec}", "width_explained_oos": round(r2(te.lw.values, p), 2),
                "width_typical_error_pct": round(float(np.median(np.abs(np.exp(p - te.lw.values) - 1)) * 100)),
                "width_error_if_no_model_pct": round(float(np.median(np.abs(np.exp(base - te.lw.values) - 1)) * 100)),
                "width_typical_c": round(float(np.median(te.width)), 2)})
    for n, v in zip(["constant"] + BNAMES[spec], b):
        coefs.append({**key, "layer": "B width", "term": n, "value": round(float(v), 4)})
    # plain-words facts from the time-only fit on ALL rows (how the six differ)
    b1 = ols(xb(g, 1), g.lw.values)
    b2 = ols(xb(g, 2), g.lw.values)
    step = g.strike_step_c.median()
    row.update({"width_time_power": round(float(b1[1]), 2), "width_at_1_day_c": round(float(np.exp(b1[0])), 2),
                "width_at_1_day_in_strike_steps": round(float(np.exp(b1[0]) / step), 2) if pd.notna(step) and step > 0 else np.nan,
                "width_at_7_days_c": round(float(np.exp(b1[0] + b1[1] * np.log(7))), 2),
                "width_jumpiness_pull": round(float(b2[2] + b2[3]), 2)})


def main():
    m = pd.read_csv(MASTER / "backtest_master.csv.gz", low_memory=False)
    lines = pd.read_csv(MASTER / "ladder_snapshots.csv.gz", low_memory=False)
    m = m[m.answer_may_be_public == 0].copy()
    m["retail_gap_c"] = m.retail_minus_fut_vs_60d * 100
    m["days"] = m.hours_to_close.clip(lower=0) / 24 + 0.15           # + the gap between close and AAA's post
    m["center"] = m.crowd_center.fillna(m.crowd_center_fit)          # crossing first (v0's measure); bell fit fills gaps
    m["width"] = m.crowd_sigma_fit_c.fillna(m.crowd_sigma_c)
    m["exp_move"] = (m.center - m.aaa_known_filled) * 100
    m["miss"] = (m.settle_value - m.center) * 100
    # the crowd's own average closing miss over its last 5 settled ladders (known once those ladders have settled)
    cl = m[m.snapshot == "close"].drop_duplicates(["series", "event"]).sort_values(["series", "settle_date"])
    cl["recent_miss"] = cl.groupby("series").miss.transform(lambda v: v.abs().shift(1).rolling(5, min_periods=2).mean())
    m = m.merge(cl[["series", "event", "recent_miss"]], on=["series", "event"], how="left")
    score, coefs = [], []
    for (fuel, hz), g in m.groupby(["fuel", "horizon"]):
        g = g[g.center.notna()].sort_values("settle_date")
        key = {"fuel": fuel, "slice": hz}
        row = {**key, "events": g.event.nunique(), "rows": len(g), "strike_step_c": g.strike_step_c.median()}
        layer_a(g, hz, row, coefs, key)
        layer_b(g, row, coefs, key)
        # calibration: one row per event and day (10am), settle vs the crowd's own bell curve
        c = g[(g.snapshot == "10am") & g.width.notna()]
        z = (c.miss / c.width).replace([np.inf, -np.inf], np.nan).dropna()
        if len(z) > 15:
            row.update({"calib_rows": len(z), "calib_events": c.event.nunique(), "settle_inside_1_width_pct": round(float((z.abs() <= 1).mean() * 100)),
                        "settle_outside_2_widths_pct": round(float((z.abs() > 2).mean() * 100))})
        # shape + cost on the scored events
        _, te, _, _ = split(g)
        ks = te.dropna(subset=["width"])[["event", "snapshot_et", "center", "width"]]
        l = lines.merge(ks, on=["event", "snapshot_et"])
        l = l[(l.yes_ask - l.yes_bid) <= 0.10 + 1e-9]
        if len(l) > 20:
            mid = (l.yes_bid + l.yes_ask) / 2
            model = 1 - ncdf((l.floor_strike - l.center) / (l.width / 100).clip(lower=1e-4))
            inside = (mid > 0.03) & (mid < 0.97)
            lean = (mid - model)[inside]
            sp = (l.yes_ask - l.yes_bid)[inside]
            row.update({"shape_line_miss_pts": round(float(np.median(np.abs(model - mid)[inside]) * 100), 2),
                        "shape_lean_low_lines_pts": round(float(lean[model[inside] < 0.25].median() * 100), 2),
                        "shape_lean_high_lines_pts": round(float(lean[model[inside] > 0.75].median() * 100), 2),
                        "spread_mid_lines_c": round(float(sp[(mid[inside] > 0.3) & (mid[inside] < 0.7)].median() * 100), 1),
                        "spread_edge_lines_c": round(float(sp[(mid[inside] <= 0.3) | (mid[inside] >= 0.7)].median() * 100), 1)})
        score.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    s = pd.DataFrame(score)
    s.to_csv(OUT / "mm_model_scorecard.csv", index=False)
    c = pd.DataFrame(coefs)
    c.to_csv(OUT / "mm_model_coefficients.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 200)
    print(s.T.to_string())
    for layer in ("A center", "B width", "B width S4 (all rows)"):
        print(c[c.layer == layer].pivot_table(index="term", columns=["fuel", "slice"], values="value", sort=False).round(3).to_string())


if __name__ == "__main__":
    main()
