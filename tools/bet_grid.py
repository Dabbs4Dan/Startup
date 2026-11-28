#!/usr/bin/env python3
"""The full bet grid: every simple bet on the 3 busiest lines, all six markets, with a luck check. A look-back, not proof.

One cell = market x side bought (YES / NO) x price cut x time slot x line rank.
  price cut   5c bands of the price paid (0-5 ... 95-100), "X+" (paid X cents or more, X = 50..95), and "all"
  time slot   open, 10am, noon, 3pm, 6pm, 10pm, close, and "all"
  line rank   1, 2, 3 (busiest first) and "all"
Per cell (the EVENT is the sample: per-event mean first, then across events; cost = ask + taker fee):
  events, instances, win_pct, paid_c, needed_pct (break-even), edge_pts, noise_pts (2 standard errors across events =
  the smallest edge this cell can tell from luck), edge in the early and late halves, luck_p, read.
Luck check (Monte Carlo): replay every event N times in a world where the price paid IS the true chance (edge = 0
everywhere). One draw per event decides all its lines and time slots together, so the replays keep the real overlap
between cells. luck_p = share of replays whose edge in that cell is at least as far from zero, same direction.
  The summary compares how many cells look like winners / losers in the real data with how many luck alone makes.
A cell is a LEAD only if: 30+ events, luck_p under 1%, edge above 0, and above 0 in both the early and the late half.
Writes research/engine_room/bet_grid.csv, bet_grid_highlights.csv, bet_grid_summary.json.
Usage: python3 tools/bet_grid.py [--sims 1000]
"""
import argparse, json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
M, E = ROOT / "data/lake/master", ROOT / "research/engine_room"
MARKETS = ["gas daily", "gas weekly", "diesel daily", "gas monthly", "diesel weekly", "diesel monthly"]
SLOTS = ["open", "10am", "noon", "3pm", "6pm", "10pm", "close"]
MIN_EVENTS = 30


def bets():
    s = pd.read_csv(M / "slices.csv.gz", low_memory=False)
    yes_won = np.where(s.fav_side == "yes", s.fav_won, 1 - s.fav_won)
    out = []
    for side, ask, won in (("YES", s.yes_ask, yes_won), ("NO", s.no_ask, 1 - yes_won)):
        out.append(pd.DataFrame({"market": s.market, "event": s.event, "slot": s.snapshot, "line": s.line_rank, "block": s.block, "side": side,
                                 "paid": ask.values, "cost": (ask + 0.07 * ask * (1 - ask)).values, "won": np.asarray(won, float)}))
    b = pd.concat(out, ignore_index=True)
    b["ev"] = b.event.astype("category").cat.codes
    return b.sort_values(["ev"], kind="stable").reset_index(drop=True)


def ev_mean(x, ev):
    """per-event means of x (rows already sorted by event). x may be 1-D or (rows x sims)."""
    starts = np.flatnonzero(np.r_[True, ev[1:] != ev[:-1]])
    n = np.diff(np.r_[starts, len(ev)])
    return np.add.reduceat(x, starts, axis=0) / (n if x.ndim == 1 else n[:, None])


def main(sims):
    b = bets()
    ver = json.load(open(M / "VERSION.json"))["version"] if (M / "VERSION.json").exists() else "unversioned"
    rng = np.random.default_rng(20261128)
    U = rng.random((b.ev.max() + 1, sims), dtype=np.float32)[b.ev.values]             # one draw per event per replay
    cost32 = b.cost.values.astype(np.float32)[:, None]
    yes = (b.side.values == "YES")[:, None]
    D = (np.where(yes, U < cost32, U > 1 - cost32).astype(np.float32) - cost32)      # replay edge per bet: won - cost
    del U
    d, ev, paidc = (b.won - b.cost).values, b.ev.values, (b.paid.values * 100).round(4)
    band = np.minimum((paidc // 5).astype(int), 19)
    cuts = [("all", "all", np.ones(len(b), bool))] + [("band", f"{5 * k}-{5 * k + 5}", band == k) for k in range(20)] + \
           [("at least", f"{x}+", paidc >= x - 1e-9) for x in range(50, 100, 5)]
    slots = [("all", np.ones(len(b), bool))] + [(s, b.slot.values == s) for s in SLOTS]
    lines = [("all", np.ones(len(b), bool))] + [(str(r), b.line.values == r) for r in (1, 2, 3)]
    early = b.block.values == "fit"
    rows, win_real, lose_real, lead1_real = [], 0, 0, 0
    win_sim, lose_sim, lead1_sim = np.zeros(sims), np.zeros(sims), np.zeros(sims)
    for mk in MARKETS:
        for side in ("YES", "NO"):
            base = (b.market.values == mk) & (b.side.values == side)
            for ctype, cname, cm in cuts:
                m1 = base & cm
                if not m1.any():
                    continue
                for sname, sm in slots:
                    m2 = m1 & sm
                    if not m2.any():
                        continue
                    for lname, lm in lines:
                        idx = np.flatnonzero(m2 & lm)
                        if not len(idx):
                            continue
                        e = ev_mean(d[idx], ev[idx])
                        n = len(e)
                        edge = e.mean() * 100
                        noise = 2 * e.std(ddof=1) / np.sqrt(n) * 100 if n > 1 else np.nan
                        r = {"market": mk, "side": side, "price_cut": cname, "cut_type": ctype, "slot": sname, "line": lname, "instances": len(idx), "events": n,
                             "win_pct": round(ev_mean(b.won.values[idx], ev[idx]).mean() * 100, 1), "paid_c": round(ev_mean(b.paid.values[idx], ev[idx]).mean() * 100, 1),
                             "needed_pct": round(ev_mean(b.cost.values[idx], ev[idx]).mean() * 100, 1), "edge_pts": round(edge, 1), "noise_pts": round(noise, 1) if n > 1 else np.nan}
                        for nm, hm in (("early", early[idx]), ("late", ~early[idx])):
                            if hm.any():
                                eh = ev_mean(d[idx][hm], ev[idx][hm])
                                r[f"{nm}_events"], r[f"edge_{nm}_pts"] = len(eh), round(eh.mean() * 100, 1)
                            else:
                                r[f"{nm}_events"], r[f"edge_{nm}_pts"] = 0, np.nan
                        if n >= MIN_EVENTS:
                            es = ev_mean(D[idx], ev[idx]).mean(axis=0) * 100                 # this cell's edge in each replay
                            tol = 1e-3                                                        # replays are float32: ties (e.g. every event won) must count as ties
                            p = float(((es >= edge - tol) if edge >= 0 else (es <= edge + tol)).mean())
                            r["luck_p"] = round(max(p, 1 / sims), 4)
                            hi, lo, hi1 = np.quantile(es, 0.975), np.quantile(es, 0.025), np.quantile(es, 0.99)
                            win_sim += es > hi; lose_sim += es < lo; lead1_sim += es > hi1
                            win_sim -= 0; hi, lo, hi1 = hi + tol, lo - tol, hi1 + tol
                            win_real += edge > hi; lose_real += edge < lo; lead1_real += edge > hi1
                            both = (r["early_events"] >= 10 and r["late_events"] >= 10 and r["edge_early_pts"] > 0 and r["edge_late_pts"] > 0)
                            r["read"] = ("LEAD" if (edge > 0 and p < 0.01 and both) else "winner-looking" if edge > hi else "loser" if edge < lo else "inside luck")
                        else:
                            r["luck_p"], r["read"] = np.nan, "too few events"
                        rows.append(r)
    g = pd.DataFrame(rows)
    g["master_version"] = ver
    g.to_csv(E / "bet_grid.csv", index=False)
    rd = g[g.events >= MIN_EVENTS]
    per = []
    for mk in MARKETS:
        a, r = g[g.market == mk], rd[rd.market == mk]
        per.append({"market": mk, "events": int(b[b.market == mk].event.nunique()), "cells_with_data": len(a), "cells_30plus_events": len(r), "cells_100plus_events": int((a.events >= 100).sum()),
                    "median_noise_pts_readable": round(float(r.noise_pts.median()), 1) if len(r) else None,
                    "cells_that_can_see_3pt_edge": int((r.noise_pts <= 3).sum()), "cells_that_can_see_5pt_edge": int((r.noise_pts <= 5).sum())})
    summ = {"master_version": ver, "replays": sims, "bets": len(b), "events": int(b.event.nunique()), "cells_with_data": len(g), "cells_readable_30plus": len(rd),
            "data_by_market": per,
            "luck_check": {"winner_looking_cells_real": int(win_real), "winner_looking_by_luck_mean": round(float(win_sim.mean()), 0), "winner_looking_by_luck_95pct": round(float(np.quantile(win_sim, 0.95)), 0),
                           "share_of_replays_with_as_many_winners": round(float((win_sim >= win_real).mean()), 3),
                           "loser_cells_real": int(lose_real), "loser_by_luck_mean": round(float(lose_sim.mean()), 0), "loser_by_luck_95pct": round(float(np.quantile(lose_sim, 0.95)), 0),
                           "share_of_replays_with_as_many_losers": round(float((lose_sim >= lose_real).mean()), 3),
                           "top1pct_cells_real": int(lead1_real), "top1pct_by_luck_mean": round(float(lead1_sim.mean()), 0), "top1pct_by_luck_95pct": round(float(np.quantile(lead1_sim, 0.95)), 0)},
            "leads": int((g["read"] == "LEAD").sum())}
    json.dump(summ, open(E / "bet_grid_summary.json", "w"), indent=1)
    keep = ["market", "side", "price_cut", "slot", "line", "events", "win_pct", "needed_pct", "edge_pts", "noise_pts", "edge_early_pts", "edge_late_pts", "luck_p", "read"]
    leads = rd[rd["read"] == "LEAD"].sort_values("luck_p").head(25)
    losers = rd[(rd["read"] == "loser") & (rd.luck_p <= 0.01)].sort_values("edge_pts").head(25)
    pd.concat([leads, losers])[keep].to_csv(E / "bet_grid_highlights.csv", index=False)
    print(json.dumps(summ, indent=1))
    pd.set_option("display.width", 250)
    print(leads[keep].to_string(index=False)); print(losers[keep].head(15).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sims", type=int, default=1000)
    main(ap.parse_args().sims)
