#!/usr/bin/env python3
"""Market scorecard: the six markets side by side on ONE ruler. Layer "L2 roll-up" in the spine. No strategy logic.

One row per market (fuel x daily / weekly / monthly). Reads only tables that already exist:
  slices.csv.gz            favorites / underdogs on the 3 busy lines (cost = ask + taker fee, outcome)
  backtest_master.csv.gz   the crowd's miss at the open and at the close
  kalshi_trades (2 DBs)    who wins, taker or maker (daily markets only; tape starts 2026-09-27 diesel, 2026-10-27 gas)
  data/live/kalshi_orderbook/   dollars resting at the best price (daily markets only; recorded since 2026-11-25)
Rules: the EVENT is the sample (per-event mean first, then the mean across events). "noise" = 2 standard errors across
events; an edge smaller than its noise is not told apart from luck. Measures follow the public Kalshi studies
(Becker 2026; Burgi, Deng, Whelan 2025): win rate minus price, return per $ risked, split by maker / taker.
Writes research/engine_room/market_scorecard.csv (+ prints it). Usage: python3 tools/market_scorecard.py
"""
import glob, json, pathlib, sqlite3
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
M, E = ROOT / "data/lake/master", ROOT / "research/engine_room"
ORDER = ["gas daily", "gas weekly", "diesel daily", "gas monthly", "diesel weekly", "diesel monthly"]


def ev_stat(g, col):
    """per-event mean first, then mean and 2 standard errors across events (in the unit of col)"""
    e = g.groupby("event")[col].mean()
    n = len(e)
    return (e.mean(), 2 * e.std() / np.sqrt(n) if n > 1 else np.nan, n)


def tape(db, fuel):
    """taker vs maker, contract-weighted, before fees: profit per $ risked. Clustered by event day for the noise band."""
    con = sqlite3.connect(db)
    t = pd.read_sql("SELECT t.ticker, t.event_date, t.yes_price, t.no_price, t.count, t.taker_side, m.result FROM kalshi_trades t "
                    "JOIN kalshi_markets m ON m.ticker = t.ticker WHERE m.result IN ('yes','no')", con)
    if t.empty:
        return {}
    tp = np.where(t.taker_side == "yes", t.yes_price, t.no_price)
    won = (t.taker_side == t.result).astype(float)
    t["t_cost"], t["t_pnl"] = t["count"] * tp, t["count"] * (won - tp)
    t["m_cost"], t["m_pnl"] = t["count"] * (1 - tp), -t["count"] * (won - tp)
    d = t.groupby("event_date")[["t_cost", "t_pnl", "m_cost", "m_pnl"]].sum()
    tr, mr = d.t_pnl / d.t_cost, d.m_pnl / d.m_cost
    return {"tape_days": len(d), "tape_from": t.event_date.min(), "tape_dollars_per_day": round(d.t_cost.add(d.m_cost).median() / 2 + 0, 0),
            "taker_ret_pct": round(100 * d.t_pnl.sum() / d.t_cost.sum(), 2), "maker_ret_pct": round(100 * d.m_pnl.sum() / d.m_cost.sum(), 2),
            "taker_ret_noise_pct": round(100 * 2 * tr.std() / np.sqrt(len(d)), 2), "taker_days_positive_pct": round(100 * (d.t_pnl > 0).mean(), 0)}


def depth(series):
    """dollars resting at the best price on the favorite side (ask above 50c), per line per snapshot. Live recordings only."""
    fs = sorted(glob.glob(str(ROOT / "data/live/kalshi_orderbook/*.csv")))
    if not fs:
        return {}
    ob = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    ob = ob[ob.event.str.startswith(series + "-")]
    if ob.empty:
        return {}
    best = ob.sort_values("price").groupby(["ts_utc", "ticker", "side"]).tail(1)       # best bid on each side
    best = best.assign(ask_other=1 - best.price, dollars=best.contracts * (1 - best.price))  # hitting that bid = buying the other side at 1 - bid
    fav = best[(best.ask_other > 0.5) & (best.ask_other <= 0.97)]
    if fav.empty:
        return {}
    return {"depth_days": ob.ts_et.str[:10].nunique(), "depth_median_$_at_best": round(fav.dollars.median(), 0),
            "depth_share_1k_fits_pct": round(100 * (fav.dollars >= 1000).mean(), 0)}


def main():
    s = pd.read_csv(M / "slices.csv.gz", low_memory=False)
    m = pd.read_csv(M / "backtest_master.csv.gz", low_memory=False)
    m = m[m.answer_may_be_public == 0].assign(market=lambda d: d.fuel + " " + d.horizon)
    ver = json.load(open(M / "VERSION.json"))["version"] if (M / "VERSION.json").exists() else "unversioned"
    s["fav_edge"] = (s.fav_won - s.fav_cost) * 100
    rows = []
    for mk in ORDER:
        g, gm = s[s.market == mk], m[m.market == mk]
        if gm.empty:
            continue
        r = {"market": mk, "events_total": gm.event.nunique(), "events_with_busy_lines": g.event.nunique(),
             "first_settle": str(gm.settle_date.min())[:10], "last_settle": str(gm.settle_date.max())[:10]}
        if len(g):
            e, noise, n = ev_stat(g, "fav_edge")
            r.update({"fav_win_pct": round(100 * g.groupby("event").fav_won.mean().mean(), 1), "fav_break_even_pct": round(100 * g.groupby("event").fav_cost.mean().mean(), 1),
                      "fav_edge_pts": round(e, 1), "fav_edge_noise_pts": round(noise, 1)})
            for side in ("yes", "no"):
                gs = g[g.fav_side == side]
                if gs.event.nunique() >= 5:
                    e, noise, n = ev_stat(gs, "fav_edge")
                    r.update({f"{side}_fav_events": n, f"{side}_fav_edge_pts": round(e, 1), f"{side}_fav_edge_noise_pts": round(noise, 1)})
            r["underdog_ret_pct"] = round(100 * g.groupby("event").ret_dog.mean().mean(), 0)
            fa = np.where(g.fav_side == "yes", g.yes_ask, g.no_ask)
            r["bid_ask_pts"] = round(100 * g.groupby("event").spread.mean().mean(), 1)
            r["fee_pts"] = round(100 * float(np.mean(0.07 * fa * (1 - fa))), 1)
        for snap in ("open", "close"):
            x = gm[gm.snapshot == snap].drop_duplicates("event").crowd_miss_c.abs()
            r[f"crowd_miss_{snap}_c"] = round(x.median(), 2) if len(x) else np.nan
        r["contracts_per_event_median"] = round(gm.drop_duplicates("event").event_volume_total.median(), 0)
        if mk == "diesel daily":
            r.update(tape(ROOT / "data/kalshi_twins.db", "diesel")); r.update(depth("KXDIESELD"))
        if mk == "gas daily":
            r.update(tape(ROOT / "data/gas/kalshi_gas.db", "gas")); r.update(depth("KXAAAGASD"))
        n = r["events_with_busy_lines"]
        r["can_test"] = "test now" if n >= 100 else ("too few events: record only" if n < 50 else "thin: hints only")
        r["master_version"] = ver
        rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(E / "market_scorecard.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(out.T.to_string())


if __name__ == "__main__":
    main()
