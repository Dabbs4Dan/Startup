#!/usr/bin/env python3
"""Deep scan: every bet-time parameter we store, diesel + gas, with a false-discovery filter and a holdout.
Plan was written to research/LOG.md BEFORE the first run (2026-11-26 3:10 AM, Chat 6). Do not loosen the rules after
seeing results; add new parameters instead and re-run.

  A  day level : which parameters predict the crowd's 10 AM miss (signed / absolute) and its miss at close?
  B  bet level : parameter tercile x price band x side, bought at 10 AM ask + fee, held to settlement
  C  bet level : hour of day x price band x side
  E  bet level : (follow-up) 9-11 PM, recent-trend tercile x price band x side
  D  model     : walk-forward ridge on all parameters shifts the crowd's center; bet when model chance - cost >= 5c

A "find" = passes Benjamini-Hochberg 10% on the first 60% of days AND same sign with p < 0.05 on the last 40%
AND same sign in the other product. Everything is clustered by day. Needs numpy, pandas, scipy.
Usage: python3 tools/deep_scan.py     -> research/backtests/deep_scan/*.csv + summary.json
"""
import json, math, pathlib, sqlite3, warnings
import numpy as np, pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "backtests" / "deep_scan"
DBS = {"diesel": ROOT / "data" / "kalshi_twins.db", "gas": ROOT / "data" / "gas" / "kalshi_gas.db"}
BANDS = [(0.03, 0.25), (0.25, 0.45), (0.45, 0.60), (0.60, 0.75), (0.75, 0.85), (0.85, 0.97)]
SPLIT, FDR, MIN_DAYS, EDGE_BAR = 0.60, 0.10, 12, 0.05
VAULT_AFTER = "2026-11-27"
BASE = ["weekend", "momentum_yday", "aaa_chg_3d", "aaa_chg_5d", "aaa_chg_7d", "aaa_chg_10d", "aaa_chg_20d", "streak_days",
        "ho_chg_1d", "ho_chg_3d", "ho_chg_5d", "ho_chg_4d_fit", "brent_last_close", "crude_slice", "refining_slice",
        "delivery_slice", "delivery_gap_vs_090", "am10_crowd_sigma_c", "am10_active_lines", "am10_total_volume",
        "model_gap_vs_crowd_am"]


def fee(p):
    return 0.07 * p * (1 - p)


def bh(pvals, q=FDR):
    """Benjamini-Hochberg: boolean mask of discoveries."""
    p = np.asarray(pvals, float)
    ok = np.isfinite(p)
    out = np.zeros(len(p), bool)
    idx = np.where(ok)[0]
    if not len(idx):
        return out
    order = idx[np.argsort(p[idx])]
    m = len(order)
    passed = p[order] <= q * (np.arange(1, m + 1) / m)
    if passed.any():
        out[order[: np.max(np.where(passed)[0]) + 1]] = True
    return out


def load(product):
    con = sqlite3.connect(DBS[product])
    p = pd.read_sql("SELECT * FROM panel_daily ORDER BY event_date", con)
    for c in p.columns:
        if c not in ("event_date", "bet_day", "weekday", "holiday", "holiday_week", "regime", "am10_time", "close_time",
                     "ho_last_close_date", "am10_goldilocks_bet", "close_goldilocks_bet"):
            p[c] = pd.to_numeric(p[c], errors="coerce")
    p = p[p.event_date.astype(str) <= VAULT_AFTER]          # vault: later days are never-looked-at (see backtest_master.py)
    p = p[p.am10_crowd_forecast.notna() & p.aaa_settled.notna()].reset_index(drop=True)
    # derived parameters, all known at 10 AM on the bet day
    p["crowd_exp_change_c"] = (p.am10_crowd_forecast - p.aaa_known) * 100
    mom_c = p.momentum_yday * (100 if p.momentum_yday.abs().median() < 0.2 else 1)
    p["crowd_lean_vs_momentum_c"] = p.crowd_exp_change_c - 0.73 * mom_c
    p["regime_rising"] = p.regime.astype(str).str.contains("rising").astype(float)
    p["regime_falling"] = p.regime.astype(str).str.contains("falling").astype(float)
    p["holiday_week_flag"] = (p.holiday_week.fillna("").astype(str).str.len() > 0).astype(float)
    dow = pd.to_datetime(p.bet_day).dt.dayofweek
    for i, n in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
        p[f"betday_{n}"] = (dow == i).astype(float)
    p["month_num"] = pd.to_datetime(p.bet_day).dt.month.astype(float)
    # yesterday's misses: assumes AAA posts before 10 AM (gap G2) -> flagged with a star in the output
    gap1 = pd.to_datetime(p.event_date).diff().dt.days == 1
    for src, dst in (("crowd_miss_am_c", "prev_miss_10am_c*"), ("crowd_miss_close_c", "prev_miss_close_c*"),
                     ("info_gap_c", "prev_info_gap_c*")):
        p[dst] = p[src].shift(1).where(gap1)
    p["prev_abs_miss_10am_c*"] = p["prev_miss_10am_c*"].abs()
    feats = [f for f in BASE if p[f].notna().sum() >= 30] + [
        "crowd_exp_change_c", "crowd_lean_vs_momentum_c", "regime_rising", "regime_falling", "holiday_week_flag",
        "betday_mon", "betday_tue", "betday_wed", "betday_thu", "betday_fri", "betday_sat", "betday_sun", "month_num",
        "prev_miss_10am_c*", "prev_miss_close_c*", "prev_info_gap_c*", "prev_abs_miss_10am_c*"]
    feats = [f for f in feats if p[f].nunique(dropna=True) > 1]
    p["miss_10am_c"] = p.crowd_miss_am_c
    p["abs_miss_10am_c"] = p.crowd_miss_am_c.abs()
    p["miss_close_c"] = p.crowd_miss_close_c
    p["is_disc"] = np.arange(len(p)) < int(len(p) * SPLIT)
    c = pd.read_sql("SELECT event_date, strike, end_et, yes_bid, yes_ask FROM kalshi_candles WHERE period_min=60 "
                    "AND yes_bid IS NOT NULL AND yes_ask IS NOT NULL", con)
    c["end_et"] = pd.to_datetime(c.end_et)
    c = c.merge(p[["event_date", "bet_day", "aaa_settled", "is_disc"]], on="event_date")
    c = c[(c.end_et.dt.strftime("%Y-%m-%d") == c.bet_day) & (c.yes_ask - c.yes_bid <= 0.10 + 1e-9)]
    c["hour"] = c.end_et.dt.hour
    yes = c.assign(side="YES", ask=c.yes_ask, win=(c.aaa_settled > c.strike).astype(float))
    no = c.assign(side="NO", ask=1 - c.yes_bid, win=(c.aaa_settled <= c.strike).astype(float))
    b = pd.concat([yes, no], ignore_index=True)
    b = b[(b.ask >= 0.03) & (b.ask <= 0.97)]
    b["cost"] = b.ask + fee(b.ask)
    b["ret"] = (b.win - b.cost) / b.cost
    b["band"] = ""
    for lo, hi in BANDS:
        b.loc[(b.ask >= lo) & (b.ask < hi + (1e-9 if hi == 0.97 else 0)), "band"] = f"{int(lo*100):02d}-{int(hi*100)}c"
    return p, feats, b[b.band != ""]


def day_t(bets):
    """Mean return per $ with days as the unit: (mean, t, p two-sided, n_days, n_bets)."""
    d = bets.groupby("event_date").ret.mean()
    if len(d) < 3 or d.std(ddof=1) == 0:
        return (d.mean() if len(d) else np.nan, np.nan, np.nan, len(d), len(bets))
    t, pv = stats.ttest_1samp(d, 0.0)
    return d.mean(), t, pv, len(d), len(bets)


def part_a(product, p, feats):
    rows = []
    for tgt in ("miss_10am_c", "abs_miss_10am_c", "miss_close_c"):
        for f in feats:
            r = {"product": product, "target": tgt, "param": f}
            for name, m in (("disc", p.is_disc), ("hold", ~p.is_disc), ("all", p.is_disc | True)):
                x = p.loc[m, [f, tgt]].dropna()
                if len(x) >= MIN_DAYS and x[f].nunique() > 1:
                    rho, pv = stats.spearmanr(x[f], x[tgt])
                else:
                    rho, pv = np.nan, np.nan
                r.update({f"rho_{name}": rho, f"p_{name}": pv, f"n_{name}": len(x)})
            rows.append(r)
    a = pd.DataFrame(rows)
    a["fdr_disc"] = bh(a.p_disc)
    a["hold_confirms"] = (np.sign(a.rho_disc) == np.sign(a.rho_hold)) & (a.p_hold < 0.05)
    return a


def cells(product, b, label):
    rows = []
    for key, g in b.groupby(["cell", "band", "side"]):
        r = {"product": product, "grid": label, "cell": key[0], "band": key[1], "side": key[2]}
        dd = g.groupby("event_date").agg(win=("win", "mean"), cost=("cost", "mean"))       # day-level win vs price paid
        r.update({"day_win_rate": dd.win.mean(), "avg_cost": dd.cost.mean(), "losing_days": int((dd.win < 1).sum()),
                  "binom_p": stats.binomtest(int(round(dd.win.sum())), len(dd), min(dd.cost.mean(), 0.999), alternative="greater").pvalue})
        for name, gg in (("disc", g[g.is_disc]), ("hold", g[~g.is_disc]), ("all", g)):
            m, t, pv, nd, nb = day_t(gg)
            r.update({f"ret_{name}": m, f"t_{name}": t, f"p_{name}": pv, f"days_{name}": nd, f"bets_{name}": nb})
        rows.append(r)
    out = pd.DataFrame(rows)
    out.loc[out.days_disc < MIN_DAYS, "p_disc"] = np.nan
    out["fdr_disc"] = bh(out.p_disc)
    out["hold_confirms"] = (np.sign(out.ret_disc) == np.sign(out.ret_hold)) & (out.p_hold < 0.05) & (out.days_hold >= 8)
    return out


def part_b(product, p, feats, b):
    b10 = b[b.hour == 10]
    parts = []
    for f in feats:
        v = p[["event_date", f, "is_disc"]].dropna()
        if v[f].nunique() <= 3:
            lab = v[f].map(lambda x: f"{f}={x:g}")
        else:
            q1, q2 = v.loc[v.is_disc, f].quantile([1 / 3, 2 / 3])     # cut points from discovery days only
            if q1 == q2:
                continue
            lab = np.where(v[f] <= q1, f"{f}:low", np.where(v[f] <= q2, f"{f}:mid", f"{f}:high"))
        parts.append(b10.merge(pd.DataFrame({"event_date": v.event_date, "cell": lab}), on="event_date"))
    return cells(product, pd.concat(parts, ignore_index=True), "B param x band x side @10AM")


def part_c(product, b):
    bb = b[(b.hour >= 9) & (b.hour <= 23)].copy()
    bb["cell"] = bb.hour.map(lambda h: f"hour={h:02d}")
    return cells(product, bb, "C hour x band x side")


def part_e(product, p, b):
    """Follow-up (LOG 3:25 AM): at 9-11 PM, does fading the recent trend pay? trend tercile x band x side."""
    v = p[["event_date", "aaa_chg_5d", "is_disc"]].dropna()
    q1, q2 = v.loc[v.is_disc, "aaa_chg_5d"].quantile([1 / 3, 2 / 3])
    lab = np.where(v.aaa_chg_5d <= q1, "trend5d:falling-most", np.where(v.aaa_chg_5d <= q2, "trend5d:middle", "trend5d:rising-most"))
    bb = b[b.hour.isin([21, 22, 23])].merge(pd.DataFrame({"event_date": v.event_date, "cell": lab}), on="event_date")
    bb = bb.sort_values("hour").drop_duplicates(["event_date", "strike", "side"], keep="last")   # one bet per line/side/day
    return cells(product, bb, "E close-hours trend x band x side")


def part_e_pooled(product, p, b):
    """Robustness view of Part E: all lines priced >= 25c pooled, by trend x side, with bootstrap ranges and months."""
    v = p[["event_date", "aaa_chg_5d", "is_disc"]].dropna()
    q1, q2 = v.loc[v.is_disc, "aaa_chg_5d"].quantile([1 / 3, 2 / 3])
    v["trend"] = np.where(v.aaa_chg_5d <= q1, "falling-most", np.where(v.aaa_chg_5d <= q2, "middle", "rising-most"))
    bb = b[b.hour.isin([21, 22, 23]) & (b.ask >= 0.25)].merge(v[["event_date", "trend"]], on="event_date")
    bb = bb.sort_values("hour").drop_duplicates(["event_date", "strike", "side"], keep="last")
    rng, rows = np.random.default_rng(1), []
    for (tr, side), g in bb.groupby(["trend", "side"]):
        for name, gg in (("all", g), ("first60", g[g.is_disc]), ("last40", g[~g.is_disc])):
            d = gg.groupby("event_date").ret.mean()
            if len(d) < 5:
                continue
            bs = [rng.choice(d.values, len(d)).mean() for _ in range(4000)]
            rows.append({"product": product, "trend_5d": tr, "side": side, "window": name, "ret_per_$": d.mean(),
                         "ci_lo": np.percentile(bs, 2.5), "ci_hi": np.percentile(bs, 97.5), "days": len(d), "bets": len(gg),
                         "win_rate": gg.win.mean(), "avg_cost": gg.cost.mean(),
                         "months_positive": f"{int((gg.groupby(gg.event_date.str[:7]).ret.mean() > 0).sum())}/{gg.event_date.str[:7].nunique()}"})
    return pd.DataFrame(rows)


def part_d(product, p, feats, b):
    """Walk-forward ridge on all parameters -> predicted miss shifts the crowd center."""
    b10 = b[b.hour == 10]
    X = p[feats].astype(float)
    y = p.miss_10am_c.values
    pred = np.full(len(p), np.nan)
    sig = np.full(len(p), np.nan)
    start = max(40, int(len(p) * 0.35))
    for t in range(start, len(p)):
        tr = X.iloc[:t]
        med, sd = tr.median(), tr.std(ddof=0).replace(0, 1)
        Z = ((tr.fillna(med) - med) / sd).fillna(0).values
        z = ((X.iloc[[t]].fillna(med) - med) / sd).fillna(0).values
        yt = y[:t]
        A = Z.T @ Z + 25.0 * np.eye(Z.shape[1])
        w = np.linalg.solve(A, Z.T @ (yt - yt.mean()))
        pred[t] = float((z @ w)[0] + yt.mean())
        sig[t] = float(np.std(yt - (Z @ w + yt.mean())))
    m = np.isfinite(pred)
    res = {"product": product, "oos_days": int(m.sum())}
    if m.sum() >= 10:
        rho, pv = stats.spearmanr(pred[m], y[m])
        res.update({"oos_rho_pred_vs_miss": rho, "oos_p": pv,
                    "crowd_mae_c": float(np.abs(y[m]).mean()), "crowd_plus_model_mae_c": float(np.abs(y[m] - pred[m]).mean())})
    q = p.assign(pred=pred, sig=sig)[["event_date", "am10_crowd_forecast", "pred", "sig"]].dropna()
    bb = b10.merge(q, on="event_date")
    for label, shift in (("model", bb.pred), ("control_no_shift", 0.0)):
        center = bb.am10_crowd_forecast + shift / 100
        pyes = 1 - stats.norm.cdf((bb.strike - center) / (bb.sig / 100))
        pm = np.where(bb.side == "YES", pyes, 1 - pyes)
        take = bb[(pm - bb.cost) >= EDGE_BAR]
        mret, t, pv, nd, nb = day_t(take)
        res.update({f"{label}_ret": mret, f"{label}_t": t, f"{label}_p": pv, f"{label}_days": nd, f"{label}_bets": nb})
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    A, G, D, EP, meta = [], [], [], [], {}
    for product in ("diesel", "gas"):
        p, feats, b = load(product)
        meta[product] = {"days": len(p), "first": p.event_date.min(), "last": p.event_date.max(),
                         "disc_days": int(p.is_disc.sum()), "hold_days": int((~p.is_disc).sum()),
                         "params": len(feats), "bets_10am": int((b.hour == 10).sum()), "bets_all_hours": len(b)}
        A.append(part_a(product, p, feats))
        G.append(part_b(product, p, feats, b))
        G.append(part_c(product, b))
        G.append(part_e(product, p, b))
        EP.append(part_e_pooled(product, p, b))
        D.append(part_d(product, p, feats, b))
    a, g = pd.concat(A, ignore_index=True), pd.concat(G, ignore_index=True)
    # cross-product confirmation
    for df, keys, val in ((a, ["target", "param"], "rho_all"), (g, ["grid", "cell", "band", "side"], "ret_all")):
        other = df[keys + ["product", val]].copy()
        other["product"] = other["product"].map({"diesel": "gas", "gas": "diesel"})
        df["other_product"] = df.merge(other.rename(columns={val: "o"}), on=keys + ["product"], how="left")["o"].values
        base = "rho_disc" if val == "rho_all" else "ret_disc"
        df["other_same_sign"] = np.sign(df[base]) == np.sign(df["other_product"])
        df["FIND"] = df.fdr_disc & df.hold_confirms & df.other_same_sign
        if "binom_p" in df:      # heavy favorites: a loss-free streak fools the t-test -> must also beat its own price
            df["streak_only"] = df.FIND & (df.ret_disc > 0) & df.band.isin(["85-97c"]) & ~(df.binom_p < 0.05)
            df["FIND"] = df.FIND & ~df.streak_only
        df["verdict"] = np.where(df.FIND, "FIND", np.where(df.fdr_disc & df.hold_confirms, "holds in one product",
                                 np.where(df.fdr_disc, "failed holdout", np.where(df.hold_confirms & (df.p_disc < 0.05), "hint", ""))))
    a.round(4).to_csv(OUT / "A_params_vs_crowd_miss.csv", index=False)
    g.round(4).to_csv(OUT / "BC_bet_grid.csv", index=False)
    pd.DataFrame(D).round(4).to_csv(OUT / "D_walkforward_model.csv", index=False)
    pd.concat(EP, ignore_index=True).round(4).to_csv(OUT / "E_pooled_trend_fade.csv", index=False)
    summ = {"meta": meta, "rules": {"split": SPLIT, "fdr": FDR, "min_days": MIN_DAYS, "edge_bar": EDGE_BAR}}
    for name, df in (("A", a), ("B", g[g.grid.str.startswith("B")]), ("C", g[g.grid.str.startswith("C")]), ("E", g[g.grid.str.startswith("E")])):
        for product in ("diesel", "gas"):
            x = df[df["product"] == product]
            tested = int(x.p_disc.notna().sum())
            summ[f"{name}_{product}"] = {
                "tested": tested, "raw_p_under_05_disc": int((x.p_disc < 0.05).sum()), "expected_by_luck": round(tested * 0.05, 1),
                "pass_fdr": int(x.fdr_disc.sum()), "pass_fdr_and_holdout": int((x.fdr_disc & x.hold_confirms).sum()),
                "FIND": int(x.FIND.sum()), "hints": int((x.verdict == "hint").sum())}
            if "ret_disc" in x:
                summ[f"{name}_{product}"].update({"FIND_winners": int((x.FIND & (x.ret_disc > 0)).sum()),
                                                  "FIND_losers": int((x.FIND & (x.ret_disc < 0)).sum()),
                                                  "streak_only_dropped": int(x.get("streak_only", pd.Series(False, index=x.index)).sum())})
    summ["D"] = D
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1, default=float))
    print(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
