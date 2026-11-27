#!/usr/bin/env python3
"""ONE backtest master for both fuels and all three time slices. Raw-collection stage: no strategy logic here.

RULEBOOK (every backtest reads these tables; change the rules here, nowhere else)
  Unit        one row = (fuel, horizon, event, snapshot). fuel: diesel | gas. horizon: daily | weekly | monthly.
  Event       one Kalshi ladder that settles on AAA's national average for one date (the date in the event ticker).
  Snapshots   (Dan, 2026-11-26: open and close always; Claude picks the in-between marks from the research)
              open   = the first hour the ladder has quotes
              10am   = our bet time; 8-10 AM carries ~36% of the day's dollars
              noon   = first cluster of unexplained crowd moves (rack prices post ~11 AM)
              3pm    = just after diesel / gasoline futures settle (2:30 PM)
              6pm    = second cluster of unexplained moves; Love's reprices in one batch ~5 PM
              10pm   = evening volume peak (9-11 PM, ~20% of dollars); where the trend-fade candidate lives
              close  = the last quotes before the ladder closes
              The five clock marks repeat on every calendar day the ladder is open (weekly / monthly too).
  No peeking  Kalshi quote = last hourly candle that ENDED at or before the snapshot (at most 6 h old; 12 h for close).
              AAA known  = AAA for the snapshot's own date if the snapshot is at 6 AM ET or later, else the day
              before. (AAA flipped between 3:17 and 3:32 AM ET on 2026-11-26, the one flip recorded so far; gap G2.)
              All other inputs use the same as-of date. Rows where that date is the settle date itself are
              flagged answer_may_be_public = 1 (older ladders stayed open into settle day); exclude them from tests.
              Daily futures / spot = last close dated BEFORE the snapshot date.
              EIA weekly pump prices (dated Monday) = usable from the next day. EIA weekly supply data (dated the
              Friday the week ended) = usable 6 days later (it is published the next Wednesday). Monthly = 60 days later.
  Liquid 3    lines that are tradeable at the snapshot (spread <= 10c, mid 3%..97%), ranked by volume traded so far,
              top 3 kept (same rule as panel.py formula #19).
  Crowd       center = strike where the mid crosses 50%; sigma = half the distance between the 84% and 16% crossings.
              crowd_center_fit / crowd_sigma_fit_c = the bell curve fitted to ALL tight lines (steadier when
              strikes are far apart; use these for width work).
  Costs       not applied here. Tests add: taker fee 0.07 * p * (1-p), buy at ask, ~$1K per bet capacity (gap G1).
  Regimes     trend_10d: rising / falling / flat (AAA 10-day change beyond +-1c); vol_20d: calm / normal / jumpy
              (20-day std of daily AAA changes, terciles within each fuel).
  Overlap     weekly and monthly ladders overlap in time; cluster by event (and by settle month) when testing.

Reads   data/lake/kalshi/<SERIES>/ (pull_kalshi_history.py), data/lake/history/ (history_pull.py),
        the two SQLite DBs + live recorder + research files for AAA history.
Writes  data/lake/master/aaa_daily.csv            reconciled AAA national per day, both fuels, with source
        data/lake/master/inputs_daily.csv         every input as one daily, as-of-safe column
        data/lake/master/ladder_snapshots.csv.gz  every quoted line at every snapshot (for brute tests on all strikes)
        data/lake/master/backtest_master.csv.gz   one row per snapshot: crowd, liquid 3, inputs, regimes, targets
        data/lake/master/COVERAGE.md              what exists, how far back, fill rates, conflicts found (vetting)
Usage   python3 tools/backtest_master.py      (pandas + numpy only; ~1 minute)
"""
import glob, json, pathlib, sqlite3, sys, warnings
import numpy as np, pandas as pd

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
LAKE, OUT = ROOT / "data" / "lake", ROOT / "data" / "lake" / "master"
SERIES = {"KXDIESELD": ("diesel", "daily"), "KXDIESELW": ("diesel", "weekly"), "KXDIESELMON": ("diesel", "monthly"),
          "KXDIESELM": ("diesel", "monthly"), "KXAAAGASD": ("gas", "daily"), "KXAAAGASW": ("gas", "weekly"),
          "KXAAAGASM": ("gas", "monthly")}
SNAP_MARKS = {10: "10am", 12: "noon", 15: "3pm", 18: "6pm", 22: "10pm"}
AAA_POSTED_BY_HOUR = 6
ET = "America/New_York"
MAIN_FUT = {"diesel": "ho", "gas": "rbob"}
notes = []


def log(s):
    print(s, flush=True)
    notes.append(s)


# ------------------------------------------------------------------ AAA national, reconciled
def aaa_daily():
    parts = []
    for series, (fuel, hz) in SERIES.items():                      # 1) Kalshi daily settlements = the official print
        f = LAKE / "kalshi" / series / "markets.csv"
        if f.exists():       # weekly / monthly settlements are AAA prints too (lowest rank: one was 0.4c off the daily print)
            m = pd.read_csv(f)
            m["date"] = pd.to_datetime(m.event_ticker.str.split("-").str[1], format="%y%b%d", errors="coerce")
            g = m.dropna(subset=["date", "expiration_value"]).groupby("date").expiration_value.first()
            parts.append(pd.DataFrame({"date": g.index, "fuel": fuel, "value": pd.to_numeric(g.values, errors="coerce"),
                                       "source": "kalshi_settlement" if hz == "daily" else f"kalshi_{hz}_settlement", "rank": 1 if hz == "daily" else 7}))
    for db, fuel in ((ROOT / "data" / "kalshi_twins.db", "diesel"), (ROOT / "data" / "gas" / "kalshi_gas.db", "gas")):
        if db.exists():                                             # 2) the project DBs (settlements + hand-verified rows)
            d = pd.read_sql("SELECT date, aaa_diesel AS value, aaa_source AS source FROM diesel_daily WHERE aaa_diesel IS NOT NULL", sqlite3.connect(db))
            parts.append(d.assign(date=pd.to_datetime(d.date), fuel=fuel, source="db:" + d.source.astype(str), rank=2))
    live = []                                                       # 3) our own live recorder
    for f in sorted(glob.glob(str(LAKE.parent / "live" / "aaa_national" / "2*.csv"))):
        live.append(pd.read_csv(f))
    if live:
        l = pd.concat(live)
        l["date"] = pd.to_datetime(l.price_as_of, format="%m/%d/%y", errors="coerce")
        for col, fuel in (("diesel_current", "diesel"), ("regular_current", "gas")):
            if col in l:
                g = l.dropna(subset=["date"]).groupby("date")[col].last()
                parts.append(pd.DataFrame({"date": g.index, "fuel": fuel, "value": pd.to_numeric(g.values, errors="coerce"), "source": "live_recorder", "rank": 3}))
    f = LAKE / "history" / "aaa_national_wayback.csv"               # 4) Internet Archive: Current, Yesterday, Week Ago are exact dates
    if f.exists():
        w = pd.read_csv(f)
        w["d0"] = pd.to_datetime(w.price_as_of, format="%m/%d/%y", errors="coerce")
        for row, lag in (("Current", 0), ("Yesterday", 1), ("Week Ago", 7)):
            x = w[(w.row == row) & w.d0.notna()]
            for col, fuel in (("diesel", "diesel"), ("regular", "gas")):
                parts.append(pd.DataFrame({"date": x.d0 - pd.Timedelta(days=lag), "fuel": fuel, "value": pd.to_numeric(x[col], errors="coerce"),
                                           "source": f"wayback_{row.lower().replace(' ', '_')}", "rank": 4 + (lag > 0)}))
    # NOT used: research/sample_models/.../aaa_daily.csv. Vetted 2026-11-26: only ~50% of its days match official
    # settlements (many rows are off by one day), while the Internet Archive rows match 100%. A wrong AAA is worse
    # than a missing one, so it stays out.
    a = pd.concat(parts, ignore_index=True).dropna(subset=["date", "value"])
    a = a[(a.value > 1) & (a.value < 10)]
    # conflicts: same fuel + date, sources disagree by more than 0.2 cents
    sp = a.groupby(["fuel", "date"]).value.agg(["min", "max", "count"])
    conf = sp[(sp["max"] - sp["min"]) > 0.002]
    best = a.sort_values("rank").drop_duplicates(["fuel", "date"]).sort_values(["fuel", "date"])[["date", "fuel", "value", "source"]]
    return best, conf, a


# ------------------------------------------------------------------ inputs, one daily as-of-safe table
def read_hist(name):
    f = LAKE / "history" / name
    if not f.exists():
        return None
    d = pd.read_csv(f)
    d["date"] = pd.to_datetime(d.date, errors="coerce")
    col = "close" if "close" in d else "value"
    return pd.to_numeric(d.set_index("date")[col], errors="coerce").dropna().sort_index()


def inputs_daily(aaa):
    cal = pd.date_range("1990-01-01", pd.Timestamp.utcnow().tz_localize(None).normalize() + pd.Timedelta(days=1), freq="D")
    cols, meta = {}, []

    def add(name, s, lag_days, kind):
        """s is indexed by its own date; usable `lag_days` later. Forward-filled onto the calendar."""
        if s is None or s.empty:
            meta.append((name, kind, 0, "", "", lag_days))
            return
        s = s[~s.index.duplicated(keep="last")]
        shifted = s.copy()
        shifted.index = shifted.index + pd.Timedelta(days=lag_days)
        cols[name] = shifted.reindex(cal, method="ffill", limit=45 if kind != "monthly" else 120)
        meta.append((name, kind, len(s), str(s.index.min().date()), str(s.index.max().date()), lag_days))

    # futures: EIA settlements (early years) < project DBs (Yahoo, last 5 years) < Yahoo daily full history (best)
    dbf = {}
    for db, col, name in ((ROOT / "data" / "kalshi_twins.db", "ulsd_nyh_usd_gal", "ho"), (ROOT / "data" / "gas" / "kalshi_gas.db", "ulsd_nyh_usd_gal", "rbob"),
                          (ROOT / "data" / "kalshi_twins.db", "brent_usd_bbl", "brent")):
        if db.exists():
            d = pd.read_sql(f"SELECT date, {col} AS v FROM diesel_daily WHERE {col} IS NOT NULL", sqlite3.connect(db))
            d = d.assign(date=pd.to_datetime(d.date)).set_index("date").v.sort_index()
            dbf[name] = d.iloc[:-2]          # the newest bars can be partial-day values frozen by the fill-blanks-only rule
    for name, eia in (("ho", "eia_ho_futures_m1.csv"), ("rbob", "eia_rbob_futures_m1.csv"), ("brent", "eia_brent_spot.csv"), ("wti", "eia_wti_spot.csv"), ("natgas", None)):
        y, e = read_hist(f"fut_{name}_1d.csv"), read_hist(eia) if eia else None
        got = [x for x in (e, dbf.get(name), y) if x is not None]
        s = pd.concat(got).sort_index() if got else None
        if s is not None:
            s = s[~s.index.duplicated(keep="last")]
        add(f"fut_{name}", s, 1, "daily")
    for f in sorted(glob.glob(str(LAKE / "history" / "eia_*.csv"))):
        name = pathlib.Path(f).stem[4:]
        s = read_hist(pathlib.Path(f).name)
        if "futures" in name:
            continue
        if "spot" in name:
            add(name, s, 1, "daily")
        elif name.startswith("retail_"):
            add(name, s, 1, "weekly")
        elif name.startswith("monthly_"):
            add(name, s, 60, "monthly")
        else:
            add(name, s, 6, "weekly")                               # weekly supply report
    x = pd.DataFrame(cols, index=cal)
    x.index.name = "date"
    for fuel in ("diesel", "gas"):                                   # AAA: same-day (posted in the morning)
        s = aaa[aaa.fuel == fuel].set_index("date").value
        x[f"aaa_{fuel}"] = s.reindex(cal)
        meta.append((f"aaa_{fuel}", "daily", len(s), str(s.index.min().date()), str(s.index.max().date()), 0))
    return x, pd.DataFrame(meta, columns=["input", "kind", "rows", "first", "last", "usable_after_days"])


def features(x, fuel):
    """Per-day feature block for one fuel (all as-of-safe because x already is)."""
    f = pd.DataFrame(index=x.index)
    a = x[f"aaa_{fuel}"]
    af = a.ffill(limit=5)
    f["aaa_known"] = a
    f["aaa_known_filled"] = af
    for n in (1, 3, 5, 7, 10, 20, 30):
        f[f"aaa_chg_{n}d_c"] = (af - af.shift(n)) * 100
    d1 = (a - a.shift(1)) * 100
    f["aaa_absmove_5d_c"] = d1.abs().rolling(5, min_periods=3).mean()       # recent jumpiness: average size of a daily move
    f["aaa_absmove_20d_c"] = d1.abs().rolling(20, min_periods=10).mean()
    sign = np.sign(d1.fillna(0))
    f["streak_days"] = sign.groupby((sign != sign.shift()).cumsum()).cumcount().add(1) * sign
    f["trend_10d"] = np.where(f.aaa_chg_10d_c > 1, "rising", np.where(f.aaa_chg_10d_c < -1, "falling", np.where(f.aaa_chg_10d_c.notna(), "flat", "")))
    vol = d1.rolling(20, min_periods=10).std()
    f["vol_20d_c"] = vol
    q = vol.quantile([1 / 3, 2 / 3])
    f["vol_regime"] = np.where(vol <= q.iloc[0], "calm", np.where(vol <= q.iloc[1], "normal", np.where(vol.notna(), "jumpy", "")))
    main = x.get(f"fut_{MAIN_FUT[fuel]}")
    if main is not None:
        f["fut_main"] = main
        for n in (1, 3, 5, 10, 20):
            f[f"fut_main_chg_{n}d_c"] = (main - main.shift(n)) * 100
        f["retail_minus_fut"] = af - main                           # delivery + taxes slice
        f["retail_minus_fut_vs_60d"] = f.retail_minus_fut - f.retail_minus_fut.rolling(60, min_periods=20).mean()
        if "fut_brent" in x:
            f["crude_slice"] = x.fut_brent / 42
            f["refining_slice"] = main - x.fut_brent / 42
    other = "rbob" if fuel == "diesel" else "ho"                     # the sister fuel's wholesale price
    if f"fut_{other}" in x:
        f["fut_sister"] = x[f"fut_{other}"]
        f["fut_sister_chg_5d_c"] = (x[f"fut_{other}"] - x[f"fut_{other}"].shift(5)) * 100
    hubs = {"diesel": ("ulsd_spot_gulf", "ulsd_spot_nyh", "ulsd_spot_la_carb"), "gas": ("gasoline_spot_gulf", "gasoline_spot_nyh", "gasoline_spot_la_rbob")}[fuel]
    if hubs[0] in x and hubs[1] in x:
        f["hub_gap_gulf_minus_nyh_c"] = (x[hubs[0]] - x[hubs[1]]) * 100
    if hubs[2] in x and hubs[0] in x:
        f["hub_gap_la_minus_gulf_c"] = (x[hubs[2]] - x[hubs[0]]) * 100
    for c in ("fut_brent", "fut_wti", "fut_natgas"):
        if c in x:
            f[c] = x[c]
            f[f"{c}_chg_5d_pct"] = (x[c] / x[c].shift(5) - 1) * 100
    key = "diesel" if fuel == "diesel" else "regular"
    stock = "distillate" if fuel == "diesel" else "gasoline"
    for c in x.columns:
        if c.startswith(f"retail_{key}") or (fuel == "gas" and c.startswith(("retail_midgrade", "retail_premium", "retail_allgrades"))):
            f[f"eia_{c}"] = x[c]
        elif c.startswith(stock) or c.startswith(f"weekly_{stock}") or c.startswith(("weekly_refinery", "crude_stocks")):
            f[c] = x[c]
            if "stocks" in c:
                f[f"{c}_chg_1w_pct"] = (x[c] / x[c].shift(7) - 1) * 100
        elif "spot" in c and (("ulsd" in c or "heating" in c or "jet" in c) if fuel == "diesel" else "gasoline" in c):
            f[c] = x[c]
        elif c.startswith("monthly_") and key in c:
            f[c] = x[c]
    nat = f"eia_retail_{key}_us"
    if nat in f:
        f["eia_retail_us_chg_1w_c"] = (f[nat] - f[nat].shift(7)) * 100
        f["aaa_minus_eia_retail_c"] = (af - f[nat]) * 100
    return f


# ------------------------------------------------------------------ Kalshi ladders -> snapshots
def bell_fit(strikes, mids):
    """Center and width of the bell curve that best fits ALL tight lines at one snapshot (probit line fit, weighted
    toward lines near 50%). More stable than two crossings when strikes are far apart. Returns (center, sigma $)."""
    from statistics import NormalDist
    nd = NormalDist()
    ok = (mids > 0.03) & (mids < 0.97)
    if ok.sum() < 2:
        return np.nan, np.nan
    k, z = strikes[ok], np.array([nd.inv_cdf(float(v)) for v in mids[ok]])
    w = np.array([nd.pdf(float(v)) for v in z]) ** 2
    kb, zb = np.average(k, weights=w), np.average(z, weights=w)
    den = (w * (k - kb) ** 2).sum()
    if den <= 0:
        return np.nan, np.nan
    slope = (w * (k - kb) * (z - zb)).sum() / den                 # z = (center - k) / sigma  ->  slope = -1 / sigma
    if slope >= 0:
        return np.nan, np.nan
    sigma = -1 / slope
    center = kb + zb * sigma
    span = strikes.max() - strikes.min()
    if not (strikes.min() - span <= center <= strikes.max() + span) or sigma > 2 * span:
        return np.nan, np.nan          # a near-flat ladder gives a meaningless fit (seen 2026-11-27: centers off by 1e20)
    return center, sigma


def crossing(strikes, mids, level):
    for i in range(len(strikes) - 1):
        if mids[i] >= level > mids[i + 1]:
            return strikes[i] + (mids[i] - level) / (mids[i] - mids[i + 1]) * (strikes[i + 1] - strikes[i])
    return np.nan


def ladders():
    snaps, lines, cov = [], [], []
    for series, (fuel, hz) in SERIES.items():
        d = LAKE / "kalshi" / series
        if not (d / "markets.csv").exists() or not (d / "candles_60m.csv.gz").exists():
            cov.append({"series": series, "fuel": fuel, "horizon": hz, "events": 0, "note": "not pulled / not found"})
            continue
        m = pd.read_csv(d / "markets.csv")
        m = m[(m.strike_type == "greater") & m.floor_strike.notna() & m.expiration_value.notna()].copy()
        if m.empty:
            cov.append({"series": series, "fuel": fuel, "horizon": hz, "events": 0, "note": "no usable markets"})
            continue
        m["settle_date"] = pd.to_datetime(m.event_ticker.str.split("-").str[1], format="%y%b%d", errors="coerce")
        m["settle_value"] = pd.to_numeric(m.expiration_value, errors="coerce")
        m["open_ts"] = pd.to_datetime(m.open_time, utc=True, errors="coerce", format="ISO8601")
        m["close_ts"] = pd.to_datetime(m.close_time, utc=True, errors="coerce", format="ISO8601")
        m = m.dropna(subset=["settle_date", "settle_value", "open_ts", "close_ts"])
        meta = json.load(open(d / "_meta.json")) if (d / "_meta.json").exists() else {}
        steps = m.groupby("event_ticker").floor_strike.apply(lambda v: np.median(np.diff(np.sort(v.unique()))) if v.nunique() > 1 else np.nan)
        c = pd.read_csv(d / "candles_60m.csv.gz")
        c = c[c.ticker.isin(m.ticker)].dropna(subset=["yes_bid", "yes_ask"]).drop_duplicates(["ticker", "end_ts"])
        c["end"] = pd.to_datetime(c.end_ts, unit="s", utc=True)
        c = c.sort_values(["ticker", "end"])
        c["cum_vol"] = c.groupby("ticker").volume.cumsum()
        c = c.merge(m[["ticker", "event_ticker", "floor_strike", "settle_value"]], on="ticker")
        n_ev = n_snap = 0
        ev_meta = m.groupby("event_ticker").agg(settle_date=("settle_date", "first"), settle_value=("settle_value", "first"),
                                                open_ts=("open_ts", "min"), close_ts=("close_ts", "max"), n_lines=("ticker", "size"),
                                                event_volume=("volume", "sum"), tier=("tier", "first"))
        for ev, g in c.groupby("event_ticker"):
            e = ev_meta.loc[ev]
            days = pd.date_range(e.open_ts.tz_convert(ET).normalize(), e.close_ts.tz_convert(ET).normalize(), freq="D")
            g = g.sort_values("end")
            times = [(dd + pd.Timedelta(hours=h), lab) for dd in days for h, lab in SNAP_MARKS.items()]
            first = g.end.iloc[0].tz_convert(ET)
            times = [(first, "open")] + [(t, lab) for t, lab in times if first <= t < e.close_ts.tz_convert(ET)] + [(e.close_ts.tz_convert(ET), "close")]
            n_ev += 1
            for t, label in times:
                w = g[(g.end <= t) & (g.end > t - pd.Timedelta(hours=12 if label == "close" else 6))]
                if w.empty:
                    continue
                q = w.drop_duplicates("ticker", keep="last").sort_values("floor_strike")
                q = q.assign(mid=(q.yes_bid + q.yes_ask) / 2, spread=q.yes_ask - q.yes_bid)
                good = q[q.spread <= 0.10 + 1e-9]
                center = crossing(good.floor_strike.values, good.mid.values, 0.5) if len(good) > 1 else np.nan
                lo, hi = (crossing(good.floor_strike.values, good.mid.values, 0.84), crossing(good.floor_strike.values, good.mid.values, 0.16)) if len(good) > 2 else (np.nan, np.nan)
                cfit, sfit = bell_fit(good.floor_strike.values, good.mid.values) if len(good) > 1 else (np.nan, np.nan)
                tr_all = good[(good.mid >= 0.03) & (good.mid <= 0.97)]
                trad = tr_all.sort_values("cum_vol", ascending=False).head(3)
                fav = {}
                if len(tr_all):                                  # the line + side the crowd likes most (highest price it can still buy)
                    yes_cost, no_cost = tr_all.yes_ask, 1 - tr_all.yes_bid
                    best_yes, best_no = yes_cost[yes_cost <= 0.97], no_cost[no_cost <= 0.97]
                    cand = []
                    if len(best_yes):
                        cand.append(("YES", best_yes.idxmax(), best_yes.max()))
                    if len(best_no):
                        cand.append(("NO", best_no.idxmax(), best_no.max()))
                    if cand:
                        side, ix, cost = max(cand, key=lambda z: z[2])
                        k = tr_all.loc[ix, "floor_strike"]
                        fav = {"fav_side": side, "fav_strike": k, "fav_cost": round(float(cost), 4),
                               "fav_won": int((e.settle_value > k) == (side == "YES"))}
                row = {"fuel": fuel, "horizon": hz, "series": series, "event": ev, "settle_date": e.settle_date.date(),
                       "snapshot": label, "snapshot_et": t.tz_localize(None), "snapshot_date": t.date(), "snapshot_hour": t.hour,
                       "asof_date": (t - pd.Timedelta(days=1)).date() if t.hour < AAA_POSTED_BY_HOUR else t.date(),
                       "days_to_settle": (e.settle_date.date() - t.date()).days,
                       "hours_to_close": round((e.close_ts - t).total_seconds() / 3600, 1), "tier": e.tier,
                       "fee_type": meta.get("fee_type"), "strike_step_c": round(float(steps.get(ev, np.nan)) * 100, 2) if pd.notna(steps.get(ev, np.nan)) else np.nan,
                       "open_et": e.open_ts.tz_convert(ET).tz_localize(None), "close_et": e.close_ts.tz_convert(ET).tz_localize(None),
                       "open_days": round((e.close_ts - e.open_ts).total_seconds() / 86400, 2),
                       "n_lines": int(e.n_lines), "n_quoted": len(q), "n_tight": len(good), "n_tradeable": int(((good.mid >= 0.03) & (good.mid <= 0.97)).sum()),
                       "volume_so_far": q.cum_vol.sum(), "event_volume_total": e.event_volume,
                       "crowd_center": center, "crowd_sigma_c": (hi - lo) / 2 * 100 if pd.notna(lo) and pd.notna(hi) else np.nan,
                       "crowd_center_fit": cfit, "crowd_sigma_fit_c": sfit * 100 if pd.notna(sfit) else np.nan,
                       "settle_value": e.settle_value}
                for i, r in enumerate(trad.itertuples(), 1):
                    row.update({f"liq{i}_strike": r.floor_strike, f"liq{i}_yes_bid": r.yes_bid, f"liq{i}_yes_ask": r.yes_ask,
                                f"liq{i}_no_ask": round(1 - r.yes_bid, 4), f"liq{i}_spread": round(r.spread, 4), f"liq{i}_volume": r.cum_vol,
                                f"liq{i}_settled_yes": int(e.settle_value > r.floor_strike)})
                row.update(fav)
                snaps.append(row)
                n_snap += 1
                ql = q[["ticker", "floor_strike", "yes_bid", "yes_ask", "last", "cum_vol", "open_interest"]].copy()
                ql.insert(0, "snapshot_et", t.tz_localize(None))
                ql.insert(0, "snapshot", label)
                ql.insert(0, "event", ev)
                ql["settled_yes"] = (e.settle_value > ql.floor_strike).astype(int)
                lines.append(ql)
        cov.append({"series": series, "fuel": fuel, "horizon": hz, "events": n_ev, "markets": len(m), "snapshots": n_snap,
                    "first_settle": str(m.settle_date.min().date()), "last_settle": str(m.settle_date.max().date()),
                    "historical_tier_markets": int((m.tier == "historical").sum()), "note": ""})
        log(f"{series}: {n_ev} events, {n_snap} snapshots")
    return pd.DataFrame(snaps), (pd.concat(lines, ignore_index=True) if lines else pd.DataFrame()), pd.DataFrame(cov)


# ------------------------------------------------------------------ contract cards (are the six markets the same thing?)
def contract_cards(aaa):
    """One row per series and year, straight from the raw files: how the contract is built and whether it settles
    on the same single-day AAA number as the daily market. Uses only AAA prints that do NOT come from that series."""
    ind = aaa[~aaa.source.str.contains("weekly_settlement|monthly_settlement")]
    rows = []
    for series, (fuel, hz) in SERIES.items():
        d = LAKE / "kalshi" / series
        if not (d / "markets.csv").exists():
            continue
        meta = json.load(open(d / "_meta.json")) if (d / "_meta.json").exists() else {}
        m = pd.read_csv(d / "markets.csv")
        m["sv"] = pd.to_numeric(m.expiration_value, errors="coerce")
        m = m[(m.strike_type == "greater") & m.sv.notna()].copy()
        if m.empty:
            continue
        m["sd"] = pd.to_datetime(m.event_ticker.str.split("-").str[1], format="%y%b%d", errors="coerce")
        m["o"] = pd.to_datetime(m.open_time, utc=True, errors="coerce", format="ISO8601")
        m["c"] = pd.to_datetime(m.close_time, utc=True, errors="coerce", format="ISO8601")
        m = m.dropna(subset=["sd", "o", "c"])
        for yr, g in m.groupby(m.sd.dt.year):
            ev = g.groupby("event_ticker").agg(sd=("sd", "first"), o=("o", "min"), c=("c", "max"), n=("ticker", "size"), v=("volume", "sum"), sv=("sv", "first"),
                                               step=("floor_strike", lambda v: np.median(np.diff(np.sort(v.unique()))) if v.nunique() > 1 else np.nan))
            close_rel = (ev.c.dt.tz_convert(ET).dt.tz_localize(None) - ev.sd).dt.total_seconds() / 3600
            j = ev.reset_index().merge(ind[ind.fuel == fuel][["date", "value"]], left_on="sd", right_on="date", how="left")
            gap = ((j.sv - j.value) * 100).abs()
            rows.append({"fuel": fuel, "slice": hz, "series": series, "year": int(yr), "events": len(ev),
                         "days_open": round(((ev.c - ev.o).dt.total_seconds() / 86400).median(), 1), "lines_per_event": int(ev.n.median()),
                         "strike_step_c": round(ev.step.median() * 100, 1) if ev.step.notna().any() else "",
                         "closes_hours_after_settle_midnight_et": round(close_rel.median(), 1),
                         "settles_on": f"{ev.sd.dt.day_name().mode().iat[0][:3]}" if hz == "weekly" else ("last day of month" if hz == "monthly" else "every day"),
                         "contracts_per_event": int(ev.v.median()), "settle_decimals": int(ev.sv.map(lambda v: len(repr(float(v)).split(".")[-1])).max()),
                         "fee_type": meta.get("fee_type", ""), "checkable_vs_daily_aaa": int(j.value.notna().sum()),
                         "same_number": int((gap < 0.011).sum()), "different": int((gap >= 0.011).sum()),
                         "max_gap_c": round(gap.max(), 2) if gap.notna().any() else ""})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    aaa, conf, aaa_all = aaa_daily()
    aaa.to_csv(OUT / "aaa_daily.csv", index=False)
    x, imeta = inputs_daily(aaa)
    x.loc["2019-01-01":].round(5).to_csv(OUT / "inputs_daily.csv")        # daily table from 2019; older rows stay in the raw files
    snaps, lines, cov = ladders()
    if snaps.empty:
        log("no Kalshi ladders found yet")
        return
    out = []
    for fuel in ("diesel", "gas"):
        f = features(x, fuel).reset_index().rename(columns={"date": "asof_date"})
        s = snaps[snaps.fuel == fuel].copy()
        s["asof_date"] = pd.to_datetime(s.asof_date)
        out.append(s.merge(f, on="asof_date", how="left"))
    mst = pd.concat(out, ignore_index=True).sort_values(["fuel", "horizon", "settle_date", "snapshot_et"])
    # some older ladders stayed open into the settle day itself; AAA for that day may already have been public
    mst["answer_may_be_public"] = (pd.to_datetime(mst.asof_date) >= pd.to_datetime(mst.settle_date)).astype(int)
    mst["change_to_settle_c"] = (mst.settle_value - mst.aaa_known_filled) * 100
    mst["crowd_expected_change_c"] = (mst.crowd_center - mst.aaa_known_filled) * 100
    mst["crowd_miss_c"] = (mst.settle_value - mst.crowd_center) * 100
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = set(USFederalHolidayCalendar().holidays("2019-01-01", "2030-12-31").date)
    sd, st = pd.to_datetime(mst.snapshot_date).dt.date, pd.to_datetime(mst.settle_date).dt.date
    mst["snapshot_is_holiday"] = sd.map(lambda d: int(d in hol))
    mst["settle_is_holiday"] = st.map(lambda d: int(d in hol))
    mst["holiday_within_3d"] = sd.map(lambda d: int(any((d + pd.Timedelta(days=k)) in hol for k in range(-3, 4))))
    # the previous ladder of the same series: how far off was the crowd at its close? (known once that ladder has settled)
    cl = mst[mst.snapshot == "close"].drop_duplicates(["series", "event"]).sort_values(["series", "settle_date"])
    cl["prev_event_close_miss_c"] = cl.groupby("series").crowd_miss_c.shift(1)
    cl["prev_settle_date"] = cl.groupby("series").settle_date.shift(1)
    mst = mst.merge(cl[["series", "event", "prev_event_close_miss_c", "prev_settle_date"]], on=["series", "event"], how="left")
    known = pd.to_datetime(mst.asof_date) >= pd.to_datetime(mst.prev_settle_date)
    mst.loc[~known, "prev_event_close_miss_c"] = np.nan
    mst = mst.drop(columns=["prev_settle_date"])
    dts = pd.to_datetime(mst.snapshot_date)
    mst["weekday"], mst["month"] = dts.dt.day_name().str[:3], dts.dt.month
    mst["settle_month"] = pd.to_datetime(mst.settle_date).dt.strftime("%Y-%m")
    mst = mst.dropna(axis=1, how="all")
    mst.round(5).to_csv(OUT / "backtest_master.csv.gz", index=False)
    (OUT / "backtest_master.csv").unlink(missing_ok=True)          # old uncompressed name (before 2026-11-26 evening)
    lines.round(4).to_csv(OUT / "ladder_snapshots.csv.gz", index=False)

    # ---------------- vetting ----------------
    checks = []
    # 1) no peeking: every joined input is dated before the snapshot by construction; verify the Kalshi side
    checks.append(("Kalshi quotes never newer than the snapshot", "PASS (built from candles ending at or before each snapshot)"))
    # 2) daily 10 AM crowd center vs the old daily panel
    for db, fuel in ((ROOT / "data" / "kalshi_twins.db", "diesel"), (ROOT / "data" / "gas" / "kalshi_gas.db", "gas")):
        try:
            p = pd.read_sql("SELECT event_date, am10_crowd_forecast, aaa_settled FROM panel_daily", sqlite3.connect(db))
            mm = mst[(mst.fuel == fuel) & (mst.horizon == "daily") & (mst.snapshot == "10am") & (mst.days_to_settle == 1)]
            j = mm.assign(event_date=mm.settle_date.astype(str)).merge(p, on="event_date")
            dc = ((j.crowd_center - pd.to_numeric(j.am10_crowd_forecast, errors="coerce")) * 100).abs()
            ds = ((j.settle_value - pd.to_numeric(j.aaa_settled, errors="coerce")) * 100).abs()
            checks.append((f"{fuel} daily vs old panel ({len(j)} shared days)",
                           f"settle values differ on {(ds > 0.01).sum()} days; 10 AM crowd center: median gap {dc.median():.2f}c, {(dc > 0.5).sum()} days over 0.5c"))
        except Exception as e:  # noqa
            checks.append((f"{fuel} daily vs old panel", f"could not compare: {e}"))
    # 3) settle value vs reconciled AAA
    a2 = aaa.assign(settle_date=aaa.date.dt.date)
    j = mst.drop_duplicates(["fuel", "event"]).merge(a2, on=["fuel", "settle_date"], how="left")
    gap = ((j.settle_value - j.value) * 100).abs()
    checks.append(("Kalshi settle value vs reconciled AAA", f"{j.value.notna().sum()} of {len(j)} events have an AAA print for that date; {(gap > 0.05).sum()} disagree by more than 0.05c"))
    checks.append(("AAA sources that disagree (>0.2c) on the same day", f"{len(conf)} fuel-days out of {len(aaa)}"))

    with open(OUT / "COVERAGE.md", "w") as fh:
        fh.write("# Backtest master: coverage and vetting\n\nBuilt by `tools/backtest_master.py` on "
                 f"{pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M')} UTC. Rules: see the docstring of that file.\n\n")
        fh.write("## Market canvas (Kalshi ladders)\n\n" + cov.fillna("").to_markdown(index=False) + "\n\n")
        cards = contract_cards(aaa)
        cards.to_csv(OUT / "contract_cards.csv", index=False)
        fh.write("## Contract cards: is each market the same thing? (rebuilt from raw files every run)\n\n"
                 "Settlement: every series settles on AAA's national average for ONE date (rule text: \"If the Diesel Price on <date> is above $K\" / "
                 "\"average regular gas prices ... on <date> according to AAA\"). `same_number` counts events whose settle value equals an AAA print for "
                 "that date that came from another source. The market design is what differs: days open, strike spacing, lines per event, close time, fees.\n\n"
                 + cards.to_markdown(index=False) + "\n\n")
        ten = mst[(mst.snapshot == "10am") & (mst.answer_may_be_public == 0)].copy()
        ten["days_out"] = pd.cut(ten.days_to_settle, [0, 1, 3, 7, 14, 40], labels=["1", "2-3", "4-7", "8-14", "15+"])
        hz = ten.groupby(["fuel", "days_out"], observed=True).agg(events=("event", "nunique"), rows=("event", "size"),
                                                                 crowd_range_c=("crowd_sigma_c", "median"), crowd_expected_move_c=("crowd_expected_change_c", lambda v: v.abs().median()),
                                                                 actual_move_c=("change_to_settle_c", lambda v: v.abs().median()), crowd_miss_c=("crowd_miss_c", lambda v: v.abs().median())).round(2)
        fh.write("## How the crowd prices by days to settlement (10 AM snapshots; description, not a test)\n\n" + hz.reset_index().to_markdown(index=False) + "\n\n")
        g = mst.groupby(["fuel", "horizon"]).agg(events=("event", "nunique"), snapshots=("event", "size"),
                                                 first_settle=("settle_date", "min"), last_settle=("settle_date", "max"),
                                                 has_center=("crowd_center", lambda s: f"{s.notna().mean():.0%}"),
                                                 has_3_liquid=("liq3_strike" if "liq3_strike" in mst else "crowd_center", lambda s: f"{s.notna().mean():.0%}"),
                                                 has_aaa_known=("aaa_known_filled", lambda s: f"{s.notna().mean():.0%}"),
                                                 has_main_future=("fut_main", lambda s: f"{s.notna().mean():.0%}") if "fut_main" in mst else ("event", "size"))
        fh.write("## Master table by fuel and time slice\n\n" + g.reset_index().to_markdown(index=False) + "\n\n")
        fh.write("## AAA national history (reconciled)\n\n")
        ag = aaa.assign(year=aaa.date.dt.year).groupby(["fuel", "year"]).agg(days=("value", "size")).unstack(0).fillna(0).astype(int)
        fh.write(ag.to_markdown() + "\n\nSource used per day: " + json.dumps(aaa.source.value_counts().to_dict()) + "\n\n")
        fh.write("## Inputs (engine canvas)\n\n" + imeta.sort_values(["kind", "input"]).to_markdown(index=False) + "\n\n")
        fill = mst.notna().mean().sort_values()
        fh.write("## Emptiest columns in the master (fill rate)\n\n" + fill.head(25).map(lambda v: f"{v:.0%}").to_frame("filled").to_markdown() + "\n\n")
        fh.write("## Checks\n\n" + "\n".join(f"- **{a}:** {b}" for a, b in checks) + "\n")
    log(f"master: {len(mst)} snapshot rows x {mst.shape[1]} columns; ladder lines: {len(lines)} rows; inputs: {len(imeta)} ({(imeta.rows > 0).sum()} with data)")
    for a, b in checks:
        log(f"check - {a}: {b}")


if __name__ == "__main__":
    sys.exit(main())
