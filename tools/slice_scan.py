#!/usr/bin/env python3
"""Layer 2 + 3 on top of the backtest master: slice table, our own ratio layer, and the scan. All six markets.

Layer 2  data/lake/master/slices.csv.gz   one row per market x event x snapshot x busy line (1-3): favorite side (the side
         priced above 50%), cost (ask + taker fee), outcome label, return per $ for the favorite and for the underdog.
Layer 3  same file: our own ratios (conviction, trend score, futures shock, divergence, gap, engine-vs-crowd, ...).
Scan     research/engine_room/slice_scan.csv   every cell with fit-block and holdout returns, false-discovery filter,
         Sharpe-style score.   slice_scan_survivors.csv = cells that pass everything.
Rules: events are the sample (per-event mean first); first 60% of each market's events = fit, last 40% = holdout,
looked at once. Plan: research/LOG.md 2026-11-27 "slice table + ratio layer + scan".
"""
import pathlib
import numpy as np
import pandas as pd
from math import erf, sqrt
import mm_anchor as A

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER, OUT = ROOT / "data/lake/master", ROOT / "research/engine_room"
FEE = 0.07
TIME = {"open": "open", "10am": "morning", "noon": "morning", "3pm": "afternoon", "6pm": "afternoon", "10pm": "night", "close": "night"}
RATIOS = ["r_conviction", "r_trend_score", "r_fut_shock", "r_fut_minus_pump", "r_gap", "r_range_engine_vs_crowd", "r_disagree",
          "r_range_vs_jumpiness", "r_line_distance", "r_spread", "r_streak"]
LABELS = ["weekday", "vol_regime", "trend_10d", "holiday_within_3d"]


def engine_columns(m):
    """Engine move and range for every row, engine re-fit each quarter on earlier data only (walk-forward)."""
    inp = pd.read_csv(MASTER / "inputs_daily.csv", parse_dates=["date"], low_memory=False).set_index("date")
    m["eng_move"], m["eng_range"], m["wvol"] = np.nan, np.nan, np.nan
    for fuel in A.FUELS:
        lp, ds = A.long_panel(fuel), A.daily_state(fuel, inp)
        g = m[m.fuel == fuel]
        if g.empty:
            continue
        m.loc[g.index, "wvol"] = ds.vol.reindex(g.asof_date.values).values
        q = g.snapshot_date.dt.to_period("Q")
        for per in sorted(q.unique()):
            cut = per.start_time
            short, long = A.fit_engine(ds, A.SHORT_X, cut), A.fit_engine(lp, A.LONG_X, cut)
            rows = g[q == per]
            for eng_ok, mask in ((short is not None, rows.h <= 6), (long is not None, rows.h >= 7)):
                r = rows[mask]
                if not eng_ok or r.empty:
                    continue
                st = ds.reindex(r.asof_date.values)
                mv, rg = A.apply_engine(short or long, long or short, st, r.h.values)
                m.loc[r.index, "eng_move"], m.loc[r.index, "eng_range"] = mv, rg
    return m


def build():
    m = pd.read_csv(MASTER / "backtest_master.csv.gz", low_memory=False, parse_dates=["settle_date", "asof_date", "snapshot_date"])
    m = m[m.answer_may_be_public == 0].copy()
    m["market"] = m.fuel + " " + m.horizon
    m["center"] = m.crowd_center.fillna(m.crowd_center_fit)
    m["width"] = m.crowd_sigma_fit_c.fillna(m.crowd_sigma_c)
    m["exp_move"] = (m.center - m.aaa_known_filled) * 100
    m["h"] = (m.settle_date - m.asof_date).dt.days.clip(lower=1)
    m = engine_columns(m)
    w = m.width.clip(lower=0.05)
    m["r_conviction"] = m.exp_move.abs() / w
    m["r_trend_score"] = m.aaa_chg_5d_c / (m.aaa_absmove_20d_c.clip(lower=0.05) * sqrt(5))
    m["r_fut_shock"] = m.fut_main_chg_5d_c / (m.wvol.clip(lower=0.2) * sqrt(5))
    m["r_fut_minus_pump"] = m.fut_main_chg_5d_c - m.aaa_chg_5d_c
    m["r_gap"] = m.retail_minus_fut_vs_60d * 100
    m["r_range_engine_vs_crowd"] = m.eng_range / w
    m["r_disagree"] = (m.eng_move - m.exp_move) / w
    m["r_range_vs_jumpiness"] = w / m.aaa_absmove_20d_c.clip(lower=0.05)
    m["r_streak"] = m.streak_days
    m["time_of_day"] = m.snapshot.map(TIME)
    m["days_left"] = pd.cut(m.h, [0, 1, 3, 7, 999], labels=["1", "2-3", "4-7", "8+"]).astype(str)
    keep = ["market", "fuel", "horizon", "series", "event", "settle_date", "snapshot", "snapshot_et", "snapshot_date", "time_of_day", "days_left", "h",
            "hours_to_close", "aaa_known_filled", "settle_value", "center", "width", "exp_move", "eng_move", "eng_range"] + \
           [c for c in RATIOS if c in m] + LABELS
    parts = []
    for n in (1, 2, 3):
        p = m[keep].copy()
        p["line_rank"] = n
        for c in ("strike", "yes_bid", "yes_ask", "no_ask", "spread", "volume", "settled_yes"):
            p[c] = m[f"liq{n}_{c}"]
        parts.append(p)
    s = pd.concat(parts, ignore_index=True).dropna(subset=["strike", "yes_bid", "yes_ask", "no_ask", "settled_yes"])
    s = s[(s.yes_ask - s.yes_bid) <= 0.10 + 1e-9]
    mid = (s.yes_bid + s.yes_ask) / 2
    s = s[(mid - 0.5).abs() > 1e-9].copy()
    mid = (s.yes_bid + s.yes_ask) / 2
    s["fav_side"] = np.where(mid > 0.5, "yes", "no")
    fav_ask = np.where(s.fav_side == "yes", s.yes_ask, s.no_ask)
    dog_ask = np.where(s.fav_side == "yes", s.no_ask, s.yes_ask)
    s = s[(fav_ask > 0.5 - 1e-9) & (fav_ask < 1) & (dog_ask > 0) & (dog_ask < 1)].copy()
    fav_ask = np.where(s.fav_side == "yes", s.yes_ask, s.no_ask)
    dog_ask = np.where(s.fav_side == "yes", s.no_ask, s.yes_ask)
    s["fav_cost"] = fav_ask + FEE * fav_ask * (1 - fav_ask)
    s["dog_cost"] = dog_ask + FEE * dog_ask * (1 - dog_ask)
    s["fav_won"] = ((s.fav_side == "yes") == (s.settled_yes.astype(float) > 0.5)).astype(int)
    s["outcome"] = np.where(s.fav_won == 1, "favorite won as ", "favorite lost as ") + s.fav_side.str.capitalize()
    s["ret_fav"] = (s.fav_won - s.fav_cost) / s.fav_cost
    s["ret_dog"] = ((1 - s.fav_won) - s.dog_cost) / s.dog_cost
    s["price_band"] = pd.cut(fav_ask, [0.499, 0.6, 0.7, 0.8, 0.9, 1.0], labels=["50-60", "60-70", "70-80", "80-90", "90+"]).astype(str)
    s["r_line_distance"] = ((s.strike - s.center) * 100).abs() / s.width.clip(lower=0.05)
    s["r_spread"] = s.spread
    # fit / holdout by event order inside each market
    s["block"] = "fit"
    for mk, g in s.groupby("market"):
        evs = g.sort_values("settle_date").drop_duplicates("event").event.tolist()
        s.loc[g.index[g.event.isin(set(evs[int(len(evs) * 0.6):]))], "block"] = "holdout"
    return s


def pval(t):
    return 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))


def cell_stats(g, col):
    out = {}
    for blk in ("fit", "holdout"):
        e = g[g.block == blk].groupby("event")[col].mean()
        n = len(e)
        mean = e.mean() if n else np.nan
        sd = e.std() if n > 1 else np.nan
        t = mean / (sd / sqrt(n)) if n > 1 and sd and sd > 0 else np.nan
        out.update({f"{blk}_events": n, f"{blk}_ret_per_$": round(mean, 4) if n else np.nan, f"{blk}_t": round(t, 2) if pd.notna(t) else np.nan})
        if blk == "fit":
            out["fit_p"] = pval(t) if pd.notna(t) else np.nan
            out["fit_win_rate"] = round(g[g.block == blk].groupby("event").fav_won.mean().mean(), 3) if n else np.nan
    e = g.groupby("event")[col].mean()
    span = max((g.settle_date.max() - g.settle_date.min()).days, 30) / 365.25
    out["sharpe_style_all"] = round(e.mean() / e.std() * sqrt(len(e) / span), 2) if len(e) > 2 and e.std() > 0 else np.nan
    return out


def scan(s):
    cells = []

    def add(g, kind, desc, key):
        for bet, col in (("favorite", "ret_fav"), ("underdog", "ret_dog")):
            if g[g.block == "fit"].event.nunique() < 8:
                continue
            cells.append({"kind": kind, **key, "slice": desc, "bet": bet, "rows": len(g), **cell_stats(g, col)})
    for mk, gm in s.groupby("market"):
        for side, gs in gm.groupby("fav_side"):
            key = {"market": mk, "fav_side": side}
            add(gs, "base", "all", key)
            for c in ("time_of_day", "days_left", "price_band", "line_rank", "weekday", "vol_regime", "trend_10d", "holiday_within_3d"):
                for v, g in gs.groupby(c):
                    add(g, "base" if c in ("time_of_day", "days_left", "price_band", "line_rank") else "label", f"{c} = {v}", key)
            for (a, b), g in gs.groupby(["time_of_day", "price_band"]):
                add(g, "base", f"time_of_day = {a} & price_band = {b}", key)
            for r in RATIOS:
                fit = gs[(gs.block == "fit")][r].dropna()
                if fit.nunique() < 6:
                    continue
                lo, hi = fit.quantile([1 / 3, 2 / 3])
                third = pd.cut(gs[r], [-np.inf, lo, hi, np.inf], labels=["low third", "middle third", "high third"])
                for v, g in gs.groupby(third, observed=True):
                    add(g, "ratio", f"{r} = {v} (cuts {lo:.2f} / {hi:.2f})", key)
    c = pd.DataFrame(cells)
    # Benjamini-Hochberg at 10% on fit-block p-values, cells with 20+ fit events only
    c["passes_filter"] = False
    ok = c[(c.fit_events >= 20) & c.fit_p.notna()].sort_values("fit_p")
    n = len(ok)
    if n:
        thr = (np.arange(1, n + 1) / n) * 0.10
        hit = np.where(ok.fit_p.values <= thr)[0]
        if len(hit):
            c.loc[ok.index[: hit.max() + 1], "passes_filter"] = True
    c["survivor"] = c.passes_filter & (c.holdout_events >= 20) & (c["fit_ret_per_$"] > 0) & (c["holdout_ret_per_$"] > 0)
    c["tested_cells_20plus"] = n
    return c


def ledger(s):
    """Plain historical count: favorite side x price band x won/lost, with win % against the break-even its price implies."""
    s = s.copy()
    s["fav_ask"] = np.where(s.fav_side == "yes", s.yes_ask, s.no_ask)
    rows = []

    def one(g, mk, side, band):
        def edge(d):
            return round((d.fav_won.mean() - d.fav_cost.mean()) * 100, 1) if len(d) else np.nan
        n, w = len(g), int(g.fav_won.sum())
        rows.append({"market": mk, "favorite": side.capitalize(), "price_band": band, "instances": n, "events": g.event.nunique(),
                     "favorite_won": w, "favorite_lost": n - w, "win_pct": round(w / n * 100, 1),
                     "avg_price_paid_c": round(g.fav_ask.mean() * 100, 1), "break_even_pct": round(g.fav_cost.mean() * 100, 1),
                     "edge_pts": edge(g), "return_per_$_pct": round(g.ret_fav.mean() * 100, 1), "avg_bid_ask_pts": round(g.spread.mean() * 100, 1),
                     "early_events": g[g.block == "fit"].event.nunique(), "edge_early_pts": edge(g[g.block == "fit"]),
                     "late_events": g[g.block == "holdout"].event.nunique(), "edge_late_pts": edge(g[g.block == "holdout"])})
        r = rows[-1]
        r["lead"] = "yes" if min(r["early_events"], r["late_events"]) >= 20 and r["edge_early_pts"] > 0 and r["edge_late_pts"] > 0 else \
            ("avoid" if min(r["early_events"], r["late_events"]) >= 20 and r["edge_early_pts"] < 0 and r["edge_late_pts"] < 0 else "")
    bands = ["50-60", "60-70", "70-80", "80-90", "90+"]
    for mk in ["ALL SIX"] + sorted(s.market.unique()):
        gm = s if mk == "ALL SIX" else s[s.market == mk]
        for side in ("yes", "no"):
            gs = gm[gm.fav_side == side]
            if gs.empty:
                continue
            one(gs, mk, side, "all")
            for b in bands:
                g = gs[gs.price_band == b]
                if len(g):
                    one(g, mk, side, b)
    return pd.DataFrame(rows)


def main():
    s = build()
    led = ledger(s)
    led.to_csv(OUT / "favorite_ledger.csv", index=False)
    pd.set_option("display.width", 250)
    print(led.to_string(index=False))
    s.to_csv(MASTER / "slices.csv.gz", index=False, compression="gzip")
    c = scan(s)
    OUT.mkdir(parents=True, exist_ok=True)
    c.sort_values(["survivor", "fit_p"], ascending=[False, True]).to_csv(OUT / "slice_scan.csv", index=False)
    c[c.survivor].to_csv(OUT / "slice_scan_survivors.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 70)
    print("slice rows", len(s), "x", s.shape[1], "| events", s.event.nunique())
    print(s.groupby("market").agg(rows=("event", "size"), events=("event", "nunique"), fav_win=("fav_won", "mean"), fav_cost=("fav_cost", "mean"),
                                  ret_fav=("ret_fav", "mean"), ret_dog=("ret_dog", "mean")).round(3).to_string())
    print(s.groupby(["market", "outcome"]).size().unstack(fill_value=0).to_string())
    print("cells", len(c), "| tested (20+ fit events)", int(c.tested_cells_20plus.max()), "| pass filter", int(c.passes_filter.sum()), "| survivors", int(c.survivor.sum()))
    show = ["market", "fav_side", "bet", "slice", "fit_events", "fit_ret_per_$", "fit_t", "holdout_events", "holdout_ret_per_$", "holdout_t", "sharpe_style_all"]
    print(c[c.passes_filter].sort_values("fit_p")[show].head(40).to_string(index=False))


if __name__ == "__main__":
    main()
