#!/usr/bin/env python3
"""Market-maker equation v0 for all six markets (Engine Room L0, extends L0.1 which covered diesel daily only).

We cannot see the market makers' code. What we can recover is the RESPONSE: how the ladder's center, width and
shape move with inputs anyone can know. Four layers, fitted per fuel x time slice from data/lake/master/:

  A  center  crowd's expected move (c) = b0 + sum_k (b_k + c_k * days_to_settle) * input_k
             inputs: AAA 1-day and 5-day change, main future 1-day and 5-day change, retail-minus-wholesale gap vs
             its 60-day normal
  B  width   crowd range sigma (c) = a0 + a1 * sqrt(days_to_settle) + a2 * 20-day AAA jumpiness
  C  shape   each line's price = normal curve with that event's center and width; score = median |miss| per line
  D  cost    median spread by price level

Fit on the first 60% of events (by settle date), score on the last 40%. Plan was written to research/LOG.md first
(2026-11-27 4:00 PM). Description of pricing, not an edge test.
Writes research/engine_room/mm_model_scorecard.csv and mm_model_coefficients.csv.
"""
import math, pathlib, warnings
import numpy as np, pandas as pd

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER, OUT = ROOT / "data" / "lake" / "master", ROOT / "research" / "engine_room"
INPUTS = ["aaa_chg_1d_c", "aaa_chg_5d_c", "fut_main_chg_1d_c", "fut_main_chg_5d_c", "retail_gap_c"]


def ncdf(z):
    return 0.5 * (1 + np.vectorize(math.erf)(z / math.sqrt(2)))


def fit(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X1, y, rcond=None)[0]


def pred(b, X):
    return np.column_stack([np.ones(len(X)), X]) @ b


def main():
    m = pd.read_csv(MASTER / "backtest_master.csv.gz", low_memory=False)
    lines = pd.read_csv(MASTER / "ladder_snapshots.csv.gz", low_memory=False)
    m = m[(m.answer_may_be_public == 0) & m.crowd_center.notna()].copy()
    m["retail_gap_c"] = m.retail_minus_fut_vs_60d * 100
    m["days"] = m.hours_to_close.clip(lower=0) / 24 + 0.15           # + the gap between close and AAA's post
    score, coefs = [], []
    for (fuel, hz), g in m.groupby(["fuel", "horizon"]):
        g = g.dropna(subset=INPUTS + ["crowd_expected_change_c"]).sort_values("settle_date")
        evs = g.drop_duplicates("event").event.tolist()
        if len(evs) < 3:
            continue
        cut = set(evs[: max(1, int(len(evs) * 0.6))])
        tr, te = g[g.event.isin(cut)], g[~g.event.isin(cut)]
        row = {"fuel": fuel, "slice": hz, "events_fit": len(cut), "events_scored": len(evs) - len(cut), "rows_fit": len(tr), "rows_scored": len(te),
               "strike_step_c": g.strike_step_c.median()}
        # ---- A center
        def XA(d):
            base = d[INPUTS].values
            return np.column_stack([base, base * d[["days"]].values]) if hz != "daily" else base
        bA = fit(XA(tr), tr.crowd_expected_change_c.values)
        p = pred(bA, XA(te))
        y = te.crowd_expected_change_c.values
        row["center_explained_oos"] = round(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum(), 2) if len(te) > 5 else np.nan
        row["center_miss_c"] = round(np.median(np.abs(y - p)), 2)
        row["center_miss_if_no_model_c"] = round(np.median(np.abs(y)), 2)       # "crowd expects no change"
        names = INPUTS + ([f"{k} x days" for k in INPUTS] if hz != "daily" else [])
        for n, v in zip(["constant"] + names, bA):
            coefs.append({"fuel": fuel, "slice": hz, "layer": "A center", "term": n, "value": round(float(v), 4)})
        # ---- B width
        gb = g.dropna(subset=["crowd_sigma_c", "vol_20d_c"])
        trb, teb = gb[gb.event.isin(cut)], gb[~gb.event.isin(cut)]
        if len(trb) > 10 and len(teb) > 5:
            XB = lambda d: np.column_stack([np.sqrt(d.days.values), d.vol_20d_c.values])
            bB = fit(XB(trb), trb.crowd_sigma_c.values)
            pb = np.clip(pred(bB, XB(teb)), 0.05, None)
            yb = teb.crowd_sigma_c.values
            row["width_explained_oos"] = round(1 - ((yb - pb) ** 2).sum() / ((yb - yb.mean()) ** 2).sum(), 2)
            row["width_typical_c"] = round(np.median(yb), 2)
            row["width_miss_c"] = round(np.median(np.abs(yb - pb)), 2)
            for n, v in zip(["constant", "sqrt(days)", "aaa_jumpiness_20d"], bB):
                coefs.append({"fuel": fuel, "slice": hz, "layer": "B width", "term": n, "value": round(float(v), 4)})
        # ---- C shape: normal curve with the crowd's own center + width vs every quoted line (scored events only)
        ks = te.dropna(subset=["crowd_sigma_c"])[["event", "snapshot_et", "crowd_center", "crowd_sigma_c"]]
        l = lines.merge(ks, on=["event", "snapshot_et"])
        l = l[(l.yes_ask - l.yes_bid) <= 0.10 + 1e-9]
        if len(l) > 20:
            mid = (l.yes_bid + l.yes_ask) / 2
            model = 1 - ncdf((l.floor_strike - l.crowd_center) / (l.crowd_sigma_c / 100).clip(lower=1e-4))
            inside = (mid > 0.03) & (mid < 0.97)
            row["shape_line_miss_pts"] = round(float(np.median(np.abs(model - mid)[inside]) * 100), 2)
            row["shape_lines_scored"] = int(inside.sum())
            lean = (mid - model)[inside]                               # + = market prices YES richer than a bell curve
            row["shape_lean_low_lines_pts"] = round(float(lean[(model[inside] < 0.25)].median() * 100), 2)
            row["shape_lean_high_lines_pts"] = round(float(lean[(model[inside] > 0.75)].median() * 100), 2)
            # ---- D cost
            sp = (l.yes_ask - l.yes_bid)[inside]
            row["spread_mid_lines_c"] = round(float(sp[(mid[inside] > 0.3) & (mid[inside] < 0.7)].median() * 100), 1)
            row["spread_edge_lines_c"] = round(float(sp[(mid[inside] <= 0.3) | (mid[inside] >= 0.7)].median() * 100), 1)
        score.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    s = pd.DataFrame(score)
    s.to_csv(OUT / "mm_model_scorecard.csv", index=False)
    pd.DataFrame(coefs).to_csv(OUT / "mm_model_coefficients.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.T.to_string())
    c = pd.DataFrame(coefs)
    print(c[c.layer == "A center"].pivot_table(index="term", columns=["fuel", "slice"], values="value").round(3).to_string())
    print(c[c.layer == "B width"].pivot_table(index="term", columns=["fuel", "slice"], values="value").round(3).to_string())


if __name__ == "__main__":
    main()
