#!/usr/bin/env python3
"""AAA change table (Dan, 2026-11-28): how the AAA number moves day to day, in size bands, and what the crowd did.

  research/engine_room/aaa_moves.csv          one row per fuel x day, all AAA history we hold (lab.aaa_moves)
  research/engine_room/aaa_moves_windows.csv  one row per weekly / monthly event: change from the open to the settle
  research/engine_room/aaa_moves_summary.csv  the grouped views (lab.aaa_moves_summary)

Bands are fixed, by percent change of the number: flat < 0.05%, small < 0.2%, medium < 0.5%, big < 1%, huge 1%+ (rise / drop).
Two groupings are kept apart: "heading in" = the change already posted when the market opens (usable before a bet) and
"came" = the change the market was betting on (hindsight). The event is the sample. Noise = 2 standard errors across days.
Cost = ask + taker fee 0.07*p*(1-p). Days after VAULT_AFTER are never read. Plan: research/LOG.md 2026-11-28.
Usage: python3 tools/aaa_moves.py
"""
import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
M, OUT = ROOT / "data/lake/master", ROOT / "research/engine_room"
VAULT_AFTER = "2026-11-27"
DAY_BOUNDS, WIN_BOUNDS = (0.05, 0.2, 0.5, 1.0), (0.25, 1.0, 2.5, 5.0)
SIZES = ("flat", "small", "medium", "big", "huge")
ORDER = ["1 huge drop", "2 big drop", "3 medium drop", "4 small drop", "5 flat", "6 small rise", "7 medium rise", "8 big rise", "9 huge rise"]


def band(pct, bounds=DAY_BOUNDS):
    if pd.isna(pct):
        return None
    i = int(np.searchsorted(bounds, abs(pct), side="right"))
    if i == 0:
        return "5 flat"
    return f"{5 + i} {SIZES[i]} rise" if pct > 0 else f"{5 - i} {SIZES[i]} drop"


def fee(p):
    return 0.07 * p * (1 - p)


def noise(v):
    v = pd.Series(v).dropna()
    return 2 * v.std() / np.sqrt(len(v)) if len(v) > 1 else np.nan


def days_table():
    a = pd.read_csv(M / "aaa_daily.csv", parse_dates=["date"])
    a = a[a.date <= VAULT_AFTER].sort_values(["fuel", "date"]).drop_duplicates(["fuel", "date"], keep="last")
    out = []
    for fuel, g in a.groupby("fuel"):
        s = g.set_index("date").value.asfreq("D")                      # missing days stay empty: no change is invented
        d = pd.DataFrame({"fuel": fuel, "aaa": s, "aaa_prev": s.shift(1)})
        d["chg_c"] = (d.aaa - d.aaa_prev) * 100
        d["chg_pct"] = (d.aaa / d.aaa_prev - 1) * 100
        d["band"] = d.chg_pct.map(band)
        d["weekday"] = d.index.day_name().str[:3]
        d["exact"] = g.set_index("date").source.reindex(d.index).astype(str).str.startswith("kalshi").values
        d["in_chg_c"], d["in_chg_pct"], d["in_band"] = d.chg_c.shift(1), d.chg_pct.shift(1), d.band.shift(1)   # heading in
        sign = np.sign(d.chg_c.where(d.chg_c.abs() > 0.1, 0))
        run, streak = 0, []
        for v in sign:                                                 # streak ending on this day (signed, flat or missing = 0)
            run = 0 if (pd.isna(v) or v == 0) else (run + v if np.sign(run) == v else v)
            streak.append(run)
        d["streak"] = streak
        d["in_streak"] = d.streak.shift(1)
        d["in_chg_5d_c"] = (d.aaa_prev - s.shift(6)) * 100
        d["chg_fri_to_mon_c"] = np.where(d.weekday == "Mon", (d.aaa - s.shift(3)) * 100, np.nan)
        d["chg_3d_c"] = (d.aaa - s.shift(3)) * 100
        out.append(d.reset_index().rename(columns={"index": "date"}))
    return pd.concat(out, ignore_index=True)


def kalshi_daily():
    m = pd.read_csv(M / "backtest_master.csv.gz", low_memory=False)
    d = m[m.horizon == "daily"]
    w = d[d.snapshot.isin(["open", "10am", "10pm", "close"])].pivot_table(index=["fuel", "event", "settle_date"], columns="snapshot",
                                                                         values=["crowd_expected_change_c", "crowd_miss_c"], aggfunc="first")
    w.columns = [f"{'crowd_exp' if a.startswith('crowd_exp') else 'crowd_miss'}_{b}_c" for a, b in w.columns]
    w = w.reset_index()
    s = pd.read_csv(M / "slices.csv.gz", low_memory=False)
    s = s[s.horizon == "daily"].copy()
    yc, nc = s.yes_ask + fee(s.yes_ask), s.no_ask + fee(s.no_ask)
    s["yes_ret"] = np.where((s.yes_ask >= 0.03) & (s.yes_ask <= 0.97), (s.settled_yes - yc) / yc, np.nan)
    s["no_ret"] = np.where((s.no_ask >= 0.03) & (s.no_ask <= 0.97), ((1 - s.settled_yes) - nc) / nc, np.nan)
    for slot in ("10am", "10pm"):
        b = s[s.snapshot == slot].groupby("event").agg(**{f"yes_ret_{slot}": ("yes_ret", "mean"), f"no_ret_{slot}": ("no_ret", "mean"),
                                                         f"fav_ret_{slot}": ("ret_fav", "mean"), f"lines_{slot}": ("strike", "count")})
        w = w.merge(b.reset_index(), on="event", how="left")
    w["date"] = pd.to_datetime(w.settle_date)
    return w.drop(columns=["settle_date"]), m, s


def windows(m, s):
    o = m[(m.horizon != "daily") & (m.snapshot == "open")].copy()
    o["market"] = o.fuel + " " + o.horizon
    o["win_chg_c"] = o.change_to_settle_c
    o["win_chg_pct"] = o.change_to_settle_c / (o.aaa_known_filled * 100) * 100
    o["band"] = o.win_chg_pct.map(lambda v: band(v, WIN_BOUNDS))
    o["in_chg_5d_c"] = o.aaa_chg_5d_c
    o["in_dir"] = np.where(o.aaa_chg_5d_c > 0.5, "rising into it", np.where(o.aaa_chg_5d_c < -0.5, "falling into it", "flat into it"))
    f = s[s.horizon != "daily"].sort_values("snapshot_et")
    first = f.groupby("event").snapshot_et.transform("min")
    f = f[f.snapshot_et == first]
    yc, nc = f.yes_ask + fee(f.yes_ask), f.no_ask + fee(f.no_ask)
    f = f.assign(yes_ret=np.where((f.yes_ask >= 0.03) & (f.yes_ask <= 0.97), (f.settled_yes - yc) / yc, np.nan),
                 no_ret=np.where((f.no_ask >= 0.03) & (f.no_ask <= 0.97), ((1 - f.settled_yes) - nc) / nc, np.nan))
    b = f.groupby("event").agg(yes_ret_first=("yes_ret", "mean"), no_ret_first=("no_ret", "mean"), fav_ret_first=("ret_fav", "mean"))
    o = o.merge(b.reset_index(), on="event", how="left")
    keep = ["market", "fuel", "horizon", "event", "settle_date", "open_et", "aaa_known_filled", "win_chg_c", "win_chg_pct", "band", "in_chg_5d_c",
            "in_dir", "crowd_expected_change_c", "crowd_miss_c", "yes_ret_first", "no_ret_first", "fav_ret_first"]
    return o[keep].sort_values(["market", "settle_date"])


def roll(view, scope, g, key, cols):
    """One summary block: per group n, share, then the asked columns as mean (+ noise for *_ret and miss)."""
    rows, tot = [], len(g)
    for k, x in g.groupby(key, dropna=True, observed=True):
        r = {"view": view, "scope": scope, "group": k, "days": len(x), "share_pct": round(100 * len(x) / tot, 1)}
        for name, (col, how) in cols.items():
            v = x[col].dropna() if col in x else pd.Series(dtype=float)
            if how == "mean":
                r[name] = round(v.mean(), 2) if len(v) else np.nan
            elif how == "absmean":
                r[name] = round(v.abs().mean(), 2) if len(v) else np.nan
            elif how == "per100":
                r[name] = round(100 * v.mean(), 1) if len(v) else np.nan
                r[name + "_noise"] = round(100 * noise(v), 1) if len(v) > 1 else np.nan
                r[name + "_n"] = len(v)
            elif how == "noise":
                r[name] = round(noise(v), 2)
            elif how == "up":
                r[name] = round(100 * (v > 0.1).mean(), 0) if len(v) else np.nan
            elif how == "down":
                r[name] = round(100 * (v < -0.1).mean(), 0) if len(v) else np.nan
            elif how == "flat":
                r[name] = round(100 * (v.abs() <= 0.1).mean(), 0) if len(v) else np.nan
            elif how == "n":
                r[name] = len(v)
        rows.append(r)
    return rows


def main():
    d = days_table()
    k, m, s = kalshi_daily()
    d = d.merge(k.drop(columns=["event"]), on=["fuel", "date"], how="left")
    d["next_chg_c"] = d.groupby("fuel").chg_c.shift(-1)
    d["carry"] = np.where(d.chg_c.abs() > 0.1, d.next_chg_c / d.chg_c, np.nan)
    d = d[d.aaa.notna()]
    d.round(4).to_csv(OUT / "aaa_moves.csv", index=False)
    w = windows(m, s)
    w.round(4).to_csv(OUT / "aaa_moves_windows.csv", index=False)

    R = []
    x = d[d.chg_c.notna()]
    for fuel, g in x.groupby("fuel"):
        R += roll("1 size of the day's change", fuel, g, "band", {"avg_change_c": ("chg_c", "mean"), "avg_change_pct": ("chg_pct", "mean")})
        wk = g.assign(weekday=pd.Categorical(g.weekday, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], ordered=True))
        cols = {"avg_change_c": ("chg_c", "mean"), "avg_size_c": ("chg_c", "absmean"), "up_pct": ("chg_c", "up"), "down_pct": ("chg_c", "down"), "flat_pct": ("chg_c", "flat")}
        R += roll("2 weekday of the new number", fuel, wk, "weekday", cols)
        R += roll("2 weekday of the new number", fuel + " (Kalshi-settled days only)", wk[wk.exact], "weekday", cols)
        nx = {"next_avg_change_c": ("next_chg_c", "mean"), "next_up_pct": ("next_chg_c", "up"), "next_down_pct": ("next_chg_c", "down"),
              "next_flat_pct": ("next_chg_c", "flat"), "next_avg_size_c": ("next_chg_c", "absmean"), "avg_change_c": ("chg_c", "mean")}
        R += roll("3 what came the next day, by today's band", fuel, g[g.next_chg_c.notna()], "band", nx)
        st = g[g.next_chg_c.notna()].assign(run=lambda t: t.streak.clip(-6, 6).map(lambda v: "no run" if v == 0 else f"{abs(int(v))}{'+' if abs(v) == 6 else ''} days {'up' if v > 0 else 'down'}"))
        R += roll("4 what came next, by length of the run so far", fuel, st, "run", nx)
        mon = g[(g.weekday == "Mon") & g.chg_fri_to_mon_c.notna()]
        R.append({"view": "5 Friday to Monday", "scope": fuel, "group": "Fri number to Mon number (3 days)", "days": len(mon), "avg_change_c": round(mon.chg_fri_to_mon_c.mean(), 2),
                  "avg_size_c": round(mon.chg_fri_to_mon_c.abs().mean(), 2), "up_pct": round(100 * (mon.chg_fri_to_mon_c > 0.1).mean()), "down_pct": round(100 * (mon.chg_fri_to_mon_c < -0.1).mean())})
        mid = g[(g.weekday == "Thu") & g.chg_3d_c.notna()]
        R.append({"view": "5 Friday to Monday", "scope": fuel, "group": "Mon number to Thu number (3 days, for scale)", "days": len(mid), "avg_change_c": round(mid.chg_3d_c.mean(), 2),
                  "avg_size_c": round(mid.chg_3d_c.abs().mean(), 2), "up_pct": round(100 * (mid.chg_3d_c > 0.1).mean()), "down_pct": round(100 * (mid.chg_3d_c < -0.1).mean())})
        fri = g[g.weekday == "Fri"].assign(fri_dir=lambda t: np.where(t.chg_c > 0.1, "Friday rose", np.where(t.chg_c < -0.1, "Friday fell", "Friday flat")))
        fm = g.set_index("date").chg_fri_to_mon_c
        fri = fri.assign(weekend_c=fri.date.map(lambda t: fm.get(t + pd.Timedelta(days=3), np.nan)))
        R += roll("5 Friday to Monday", fuel + ": weekend move by what Friday did", fri[fri.weekend_c.notna()], "fri_dir",
                  {"avg_change_c": ("weekend_c", "mean"), "avg_size_c": ("weekend_c", "absmean"), "up_pct": ("weekend_c", "up"), "down_pct": ("weekend_c", "down")})
        kd = g[g.crowd_exp_10am_c.notna()]
        cc = {"heading_in_c": ("in_chg_c", "mean"), "crowd_expected_c": ("crowd_exp_10am_c", "mean"), "came_c": ("chg_c", "mean"),
              "crowd_miss_c": ("crowd_miss_10am_c", "mean"), "crowd_miss_noise_c": ("crowd_miss_10am_c", "noise"), "crowd_miss_size_c": ("crowd_miss_10am_c", "absmean"),
              "yes_per100": ("yes_ret_10am", "per100"), "no_per100": ("no_ret_10am", "per100"), "fav_per100": ("fav_ret_10am", "per100")}
        R += roll("6 crowd at 10 AM, by the change heading in (known before the bet)", fuel + " daily", kd[kd.in_band.notna()], "in_band", cc)
        R += roll("7 crowd at 10 AM, by the change that came (hindsight)", fuel + " daily", kd, "band", cc)
        wd = kd.assign(weekday=pd.Categorical(kd.weekday, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], ordered=True))
        R += roll("8 crowd at 10 AM, by weekday of the number being bet on", fuel + " daily", wd, "weekday", cc)
        kn = g[g.crowd_exp_10pm_c.notna()]
        cn = {"heading_in_c": ("in_chg_c", "mean"), "crowd_expected_c": ("crowd_exp_10pm_c", "mean"), "came_c": ("chg_c", "mean"),
              "crowd_miss_c": ("crowd_miss_10pm_c", "mean"), "crowd_miss_noise_c": ("crowd_miss_10pm_c", "noise"), "crowd_miss_size_c": ("crowd_miss_10pm_c", "absmean"),
              "yes_per100": ("yes_ret_10pm", "per100"), "no_per100": ("no_ret_10pm", "per100"), "fav_per100": ("fav_ret_10pm", "per100")}
        R += roll("6b crowd at 10 PM, by the change heading in", fuel + " daily", kn[kn.in_band.notna()], "in_band", cn)
    wc = {"window_change_c": ("win_chg_c", "mean"), "crowd_expected_c": ("crowd_expected_change_c", "mean"), "crowd_miss_c": ("crowd_miss_c", "mean"),
          "crowd_miss_noise_c": ("crowd_miss_c", "noise"), "crowd_miss_size_c": ("crowd_miss_c", "absmean"),
          "yes_per100": ("yes_ret_first", "per100"), "no_per100": ("no_ret_first", "per100"), "fav_per100": ("fav_ret_first", "per100")}
    for mk, g in w.groupby("market"):
        R += roll("9 weekly / monthly: change from the open to the settle (hindsight)", mk, g[g.band.notna()], "band", wc)
        R += roll("9b weekly / monthly: by the trend heading in (known at the open)", mk, g, "in_dir", wc)
    S = pd.DataFrame(R)
    S.to_csv(OUT / "aaa_moves_summary.csv", index=False)
    print(f"aaa_moves: {len(d)} fuel-days, {int(d.chg_c.notna().sum())} with a 1-day change; windows: {len(w)} events; summary rows: {len(S)}")
    return d, w, S


if __name__ == "__main__":
    main()
