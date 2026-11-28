#!/usr/bin/env python3
"""Open gap ratio: our first hand-built ratio (Dan, 2026-11-28). One per market, for all six markets.

  ratio = (crowd's line this morning - crowd's line at last night's close) / (AAA this morning - AAA yesterday)

  last night's close   daily: the previous day's market at its close.  weekly / monthly: the same market at 10 PM the day before.
  this morning         the 10 AM slot (the first slot with real two-sided quotes; at the 8 AM open half the days have none).
  crowd's line         the crowd center = where the ladder crosses 50%, built from the busy lines.
  AAA move             the new AAA number that posted overnight (about 3:30 AM ET) minus the one before.

How to read it. Daily: last night's close already sat on the number that just posted, so the ratio is the share of that move
the crowd expects AGAIN tomorrow (1.0 = same move again, 0 = no more, below 0 = a turn). Weekly / monthly: how far the crowd
moved its end-of-period guess for each 1c AAA moved overnight. Only days where AAA moved 0.3c or more get a ratio.

Out: research/engine_room/open_gap_ratio.csv (one row per market x event x day; lab.open_gap_ratio; joins slices on event +
snapshot_date) and open_gap_ratio_summary.csv (by market x ratio band: the crowd's miss and the 3 busy lines at 10 AM).
The event is the sample (per-event mean first). Cost = ask + fee. Vault days are not in the master, so they are not here.
"""
import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
M, OUT = ROOT / "data/lake/master", ROOT / "research/engine_room"
MIN_MOVE_C = 0.3
BANDS = [(-np.inf, 0, "1 below 0 (other way)"), (0, 0.5, "2 0 to 0.5"), (0.5, 1.0, "3 0.5 to 1"), (1.0, 1.5, "4 1 to 1.5"), (1.5, np.inf, "5 1.5 and up")]


def fee(p):
    return 0.07 * p * (1 - p)


def rband(r):
    if pd.isna(r):
        return "0 AAA barely moved"
    return next(n for lo, hi, n in BANDS if lo <= r < hi)


def noise(v):
    v = pd.Series(v).dropna()
    return 2 * v.std() / np.sqrt(len(v)) if len(v) > 1 else np.nan


def build():
    cols = ["fuel", "horizon", "series", "event", "settle_date", "snapshot", "snapshot_et", "snapshot_date", "crowd_center", "aaa_known_filled",
            "change_to_settle_c", "crowd_expected_change_c", "crowd_miss_c", "weekday"]
    m = pd.read_csv(M / "backtest_master.csv.gz", low_memory=False, usecols=cols)
    m["market"] = m.fuel + " " + m.horizon
    m["snapshot_date"] = pd.to_datetime(m.snapshot_date)
    m["settle_date"] = pd.to_datetime(m.settle_date)
    am = m[m.snapshot == "10am"].copy()
    rows = []
    # daily: this morning = 10 AM of event E (bet day = settle - 1); last night = close of the event that settles on the bet day
    d = am[am.horizon == "daily"]
    cl = m[(m.horizon == "daily") & (m.snapshot == "close")][["series", "settle_date", "crowd_center", "aaa_known_filled"]]
    cl = cl.rename(columns={"settle_date": "snapshot_date", "crowd_center": "center_last_night", "aaa_known_filled": "aaa_last_night"})
    rows.append(d.merge(cl, on=["series", "snapshot_date"], how="left"))
    # weekly / monthly: last night = the same event at 10 PM the day before
    w = am[am.horizon != "daily"]
    pm = m[(m.horizon != "daily") & (m.snapshot == "10pm")][["event", "snapshot_date", "crowd_center", "aaa_known_filled"]].copy()
    pm["snapshot_date"] = pm.snapshot_date + pd.Timedelta(days=1)
    pm = pm.rename(columns={"crowd_center": "center_last_night", "aaa_known_filled": "aaa_last_night"})
    rows.append(w.merge(pm, on=["event", "snapshot_date"], how="left"))
    g = pd.concat(rows, ignore_index=True)
    g = g.rename(columns={"crowd_center": "center_morning", "aaa_known_filled": "aaa_morning", "crowd_expected_change_c": "crowd_expected_c",
                          "change_to_settle_c": "came_c", "crowd_miss_c": "crowd_miss_10am_c"})
    g["aaa_move_c"] = (g.aaa_morning - g.aaa_last_night) * 100
    g["gap_c"] = (g.center_morning - g.center_last_night) * 100
    ok = g.aaa_move_c.abs() >= MIN_MOVE_C
    g["open_gap_ratio"] = np.where(ok, g.gap_c / g.aaa_move_c.where(ok), np.nan)
    g["ratio_band"] = np.where(g.gap_c.notna() & g.aaa_move_c.notna(), g.open_gap_ratio.map(rband), None)
    g["days_left"] = (g.settle_date - g.snapshot_date).dt.days
    s = pd.read_csv(M / "slices.csv.gz", low_memory=False, usecols=["event", "snapshot", "snapshot_date", "yes_ask", "no_ask", "settled_yes", "ret_fav", "strike"])
    s = s[s.snapshot == "10am"].copy()
    s["snapshot_date"] = pd.to_datetime(s.snapshot_date)
    yc, nc = s.yes_ask + fee(s.yes_ask), s.no_ask + fee(s.no_ask)
    s["yes_ret"] = np.where((s.yes_ask >= 0.03) & (s.yes_ask <= 0.97), (s.settled_yes - yc) / yc, np.nan)
    s["no_ret"] = np.where((s.no_ask >= 0.03) & (s.no_ask <= 0.97), ((1 - s.settled_yes) - nc) / nc, np.nan)
    b = s.groupby(["event", "snapshot_date"]).agg(yes_ret=("yes_ret", "mean"), no_ret=("no_ret", "mean"), fav_ret=("ret_fav", "mean"), busy_lines=("strike", "count")).reset_index()
    g = g.merge(b, on=["event", "snapshot_date"], how="left")
    keep = ["market", "fuel", "horizon", "event", "settle_date", "snapshot_date", "weekday", "days_left", "aaa_last_night", "aaa_morning", "aaa_move_c",
            "center_last_night", "center_morning", "gap_c", "open_gap_ratio", "ratio_band", "crowd_expected_c", "came_c", "crowd_miss_10am_c",
            "yes_ret", "no_ret", "fav_ret", "busy_lines"]
    return g[keep].sort_values(["market", "snapshot_date", "event"])


def summarize(g):
    R = []
    u = g[g.ratio_band.notna()]
    for mk, x in u.groupby("market"):
        r = x.open_gap_ratio.dropna()
        y = x[x.open_gap_ratio.notna()]
        R.append({"market": mk, "group": "ALL days with a ratio", "events": y.event.nunique(), "days": len(y), "ratio_median": round(r.median(), 2) if len(r) else np.nan,
                  "ratio_25": round(r.quantile(.25), 2) if len(r) else np.nan, "ratio_75": round(r.quantile(.75), 2) if len(r) else np.nan,
                  "link_gap_vs_aaa_move": round(y.gap_c.corr(y.aaa_move_c, method="spearman"), 2) if len(y) > 5 else np.nan,
                  "link_ratio_vs_crowd_miss": round(y.open_gap_ratio.corr(y.crowd_miss_10am_c, method="spearman"), 2) if len(y) > 5 else np.nan})
        for direction, z in (("AAA rose overnight", x[x.aaa_move_c >= MIN_MOVE_C]), ("AAA fell overnight", x[x.aaa_move_c <= -MIN_MOVE_C])):
            for bnd, q in z.groupby("ratio_band"):
                e = q.groupby("event").agg(ratio=("open_gap_ratio", "mean"), aaa_move_c=("aaa_move_c", "mean"), crowd_expected_c=("crowd_expected_c", "mean"),
                                           came_c=("came_c", "mean"), miss=("crowd_miss_10am_c", "mean"), yes=("yes_ret", "mean"), no=("no_ret", "mean"), fav=("fav_ret", "mean"))
                R.append({"market": mk, "group": f"{direction} | ratio {bnd[2:]}", "events": len(e), "days": len(q), "ratio_avg": round(e.ratio.mean(), 2),
                          "aaa_move_c": round(e.aaa_move_c.mean(), 2), "crowd_expected_c": round(e.crowd_expected_c.mean(), 2), "came_c": round(e.came_c.mean(), 2),
                          "crowd_miss_c": round(e.miss.mean(), 2), "crowd_miss_noise_c": round(noise(e.miss), 2),
                          "yes_per100": round(100 * e.yes.mean(), 1), "yes_noise": round(100 * noise(e.yes), 1), "no_per100": round(100 * e.no.mean(), 1), "no_noise": round(100 * noise(e.no), 1),
                          "fav_per100": round(100 * e.fav.mean(), 1), "fav_noise": round(100 * noise(e.fav), 1), "events_with_bets": int(e.fav.notna().sum())})
    return pd.DataFrame(R)


def main():
    g = build()
    g.round(4).to_csv(OUT / "open_gap_ratio.csv", index=False)
    S = summarize(g)
    S.to_csv(OUT / "open_gap_ratio_summary.csv", index=False)
    print(f"open_gap_ratio: {len(g)} market-days, {int(g.open_gap_ratio.notna().sum())} with a ratio; summary rows {len(S)}")
    return g, S


if __name__ == "__main__":
    main()
