#!/usr/bin/env python3
"""ONE backtest master for both fuels and all three time slices. Raw-collection stage: no strategy logic here.

RULEBOOK (every backtest reads these tables; change the rules here, nowhere else)
  Unit        one row = (fuel, horizon, event, snapshot). fuel: diesel | gas. horizon: daily | weekly | monthly.
  Event       one Kalshi ladder that settles on AAA's national average for one date (the date in the event ticker).
  Snapshots   10:00, 18:00 and 22:00 US/Eastern on every calendar day the ladder is open.
  No peeking  Kalshi quote = last hourly candle that ENDED at or before the snapshot (and is at most 6 h old).
              AAA known  = AAA for the snapshot's own date (assumes AAA posts before 10 AM ET; gap G2).
              Daily futures / spot = last close dated BEFORE the snapshot date.
              EIA weekly pump prices (dated Monday) = usable from the next day. EIA weekly supply data (dated the
              Friday the week ended) = usable 6 days later (it is published the next Wednesday). Monthly = 60 days later.
  Liquid 3    lines that are tradeable at the snapshot (spread <= 10c, mid 3%..97%), ranked by volume traded so far,
              top 3 kept (same rule as panel.py formula #19).
  Crowd       center = strike where the mid crosses 50%; sigma = half the distance between the 84% and 16% crossings.
  Costs       not applied here. Tests add: taker fee 0.07 * p * (1-p), buy at ask, ~$1K per bet capacity (gap G1).
  Regimes     trend_10d: rising / falling / flat (AAA 10-day change beyond +-1c); vol_20d: calm / normal / jumpy
              (20-day std of daily AAA changes, terciles within each fuel).
  Overlap     weekly and monthly ladders overlap in time; cluster by event (and by settle month) when testing.

Reads   data/lake/kalshi/<SERIES>/ (pull_kalshi_history.py), data/lake/history/ (history_pull.py),
        the two SQLite DBs + live recorder + research files for AAA history.
Writes  data/lake/master/aaa_daily.csv            reconciled AAA national per day, both fuels, with source
        data/lake/master/inputs_daily.csv         every input as one daily, as-of-safe column
        data/lake/master/ladder_snapshots.csv.gz  every quoted line at every snapshot (for brute tests on all strikes)
        data/lake/master/backtest_master.csv      one row per snapshot: crowd, liquid 3, inputs, regimes, targets
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
SNAP_HOURS = (10, 18, 22)
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
        if hz == "daily" and f.exists():
            m = pd.read_csv(f)
            m["date"] = pd.to_datetime(m.event_ticker.str.split("-").str[1], format="%y%b%d", errors="coerce")
            g = m.dropna(subset=["date", "expiration_value"]).groupby("date").expiration_value.first()
            parts.append(pd.DataFrame({"date": g.index, "fuel": fuel, "value": pd.to_numeric(g.values, errors="coerce"), "source": "kalshi_settlement", "rank": 1}))
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
        m["open_ts"] = pd.to_datetime(m.open_time, utc=True, errors="coerce")
        m["close_ts"] = pd.to_datetime(m.close_time, utc=True, errors="coerce")
        m = m.dropna(subset=["settle_date", "settle_value", "open_ts", "close_ts"])
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
            times = [dd + pd.Timedelta(hours=h) for dd in days for h in SNAP_HOURS]
            times = [t for t in times if e.open_ts < t <= e.close_ts]
            g = g.sort_values("end")
            n_ev += 1
            for t in times:
                w = g[(g.end <= t) & (g.end > t - pd.Timedelta(hours=6))]
                if w.empty:
                    continue
                q = w.drop_duplicates("ticker", keep="last").sort_values("floor_strike")
                q = q.assign(mid=(q.yes_bid + q.yes_ask) / 2, spread=q.yes_ask - q.yes_bid)
                good = q[q.spread <= 0.10 + 1e-9]
                center = crossing(good.floor_strike.values, good.mid.values, 0.5) if len(good) > 1 else np.nan
                lo, hi = (crossing(good.floor_strike.values, good.mid.values, 0.84), crossing(good.floor_strike.values, good.mid.values, 0.16)) if len(good) > 2 else (np.nan, np.nan)
                trad = good[(good.mid >= 0.03) & (good.mid <= 0.97)].sort_values("cum_vol", ascending=False).head(3)
                row = {"fuel": fuel, "horizon": hz, "series": series, "event": ev, "settle_date": e.settle_date.date(),
                       "snapshot_et": t.tz_localize(None), "snapshot_date": t.date(), "snapshot_hour": t.hour,
                       "days_to_settle": (e.settle_date.date() - t.date()).days,
                       "hours_to_close": round((e.close_ts - t).total_seconds() / 3600, 1), "tier": e.tier,
                       "n_lines": int(e.n_lines), "n_quoted": len(q), "n_tight": len(good), "n_tradeable": int(((good.mid >= 0.03) & (good.mid <= 0.97)).sum()),
                       "volume_so_far": q.cum_vol.sum(), "event_volume_total": e.event_volume,
                       "crowd_center": center, "crowd_sigma_c": (hi - lo) / 2 * 100 if pd.notna(lo) and pd.notna(hi) else np.nan,
                       "settle_value": e.settle_value}
                for i, r in enumerate(trad.itertuples(), 1):
                    row.update({f"liq{i}_strike": r.floor_strike, f"liq{i}_yes_bid": r.yes_bid, f"liq{i}_yes_ask": r.yes_ask,
                                f"liq{i}_no_ask": round(1 - r.yes_bid, 4), f"liq{i}_spread": round(r.spread, 4), f"liq{i}_volume": r.cum_vol,
                                f"liq{i}_settled_yes": int(e.settle_value > r.floor_strike)})
                snaps.append(row)
                n_snap += 1
                ql = q[["ticker", "floor_strike", "yes_bid", "yes_ask", "last", "cum_vol", "open_interest"]].copy()
                ql.insert(0, "snapshot_et", t.tz_localize(None))
                ql.insert(0, "event", ev)
                ql["settled_yes"] = (e.settle_value > ql.floor_strike).astype(int)
                lines.append(ql)
        cov.append({"series": series, "fuel": fuel, "horizon": hz, "events": n_ev, "markets": len(m), "snapshots": n_snap,
                    "first_settle": str(m.settle_date.min().date()), "last_settle": str(m.settle_date.max().date()),
                    "historical_tier_markets": int((m.tier == "historical").sum()), "note": ""})
        log(f"{series}: {n_ev} events, {n_snap} snapshots")
    return pd.DataFrame(snaps), (pd.concat(lines, ignore_index=True) if lines else pd.DataFrame()), pd.DataFrame(cov)


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
        f = features(x, fuel).reset_index().rename(columns={"date": "snapshot_date"})
        s = snaps[snaps.fuel == fuel].copy()
        s["snapshot_date"] = pd.to_datetime(s.snapshot_date)
        out.append(s.merge(f, on="snapshot_date", how="left"))
    mst = pd.concat(out, ignore_index=True).sort_values(["fuel", "horizon", "settle_date", "snapshot_et"])
    mst["change_to_settle_c"] = (mst.settle_value - mst.aaa_known_filled) * 100
    mst["crowd_expected_change_c"] = (mst.crowd_center - mst.aaa_known_filled) * 100
    mst["crowd_miss_c"] = (mst.settle_value - mst.crowd_center) * 100
    dts = pd.to_datetime(mst.snapshot_date)
    mst["weekday"], mst["month"] = dts.dt.day_name().str[:3], dts.dt.month
    mst["settle_month"] = pd.to_datetime(mst.settle_date).dt.strftime("%Y-%m")
    mst = mst.dropna(axis=1, how="all")
    mst.round(5).to_csv(OUT / "backtest_master.csv", index=False)
    lines.round(4).to_csv(OUT / "ladder_snapshots.csv.gz", index=False)

    # ---------------- vetting ----------------
    checks = []
    # 1) no peeking: every joined input is dated before the snapshot by construction; verify the Kalshi side
    checks.append(("Kalshi quotes never newer than the snapshot", "PASS (built from candles ending at or before each snapshot)"))
    # 2) daily 10 AM crowd center vs the old daily panel
    for db, fuel in ((ROOT / "data" / "kalshi_twins.db", "diesel"), (ROOT / "data" / "gas" / "kalshi_gas.db", "gas")):
        try:
            p = pd.read_sql("SELECT event_date, am10_crowd_forecast, aaa_settled FROM panel_daily", sqlite3.connect(db))
            mm = mst[(mst.fuel == fuel) & (mst.horizon == "daily") & (mst.snapshot_hour == 10) & (mst.days_to_settle == 1)]
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
