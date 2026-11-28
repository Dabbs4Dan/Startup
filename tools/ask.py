#!/usr/bin/env python3
"""Quick questions on data we already hold (the `test` command). Not a strategy test: a plain count, one answer.

Reads data/lake/master/slices.csv.gz (the 3 busiest lines of every event at every time slot; the favorite is the side
priced above 50c). The EVENT is the sample: per-event mean first, then the mean across events. Cost = ask + taker fee.
  win %       how often the picked side won
  paid        average ask price in cents;  break-even = ask + fee (the win % needed to make nothing)
  edge        win % minus break-even, in points;  noise = 2 standard errors across events (edge inside noise = luck not ruled out)
Usage  python3 tools/ask.py --min 75                      favorites priced 75c or more, every market
       python3 tools/ask.py --min 85 --side yes           YES favorites at 85c or more
       python3 tools/ask.py --min 60 --max 80 --side no --market "gas daily" --slot close
       --pick underdog   look at the other side instead      --json  machine output
"""
import argparse, json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
M = ROOT / "data/lake/master"
ORDER = ["gas daily", "gas weekly", "diesel daily", "gas monthly", "diesel weekly", "diesel monthly"]


def answer(min_c=50, max_c=100, side=None, market=None, slot=None, pick="favorite"):
    s = pd.read_csv(M / "slices.csv.gz", low_memory=False)
    fav_ask = np.where(s.fav_side == "yes", s.yes_ask, s.no_ask)
    s = s[(fav_ask * 100 >= min_c - 1e-9) & (fav_ask * 100 <= max_c + 1e-9)].assign(fav_ask=lambda d: np.where(d.fav_side == "yes", d.yes_ask, d.no_ask))
    if side:
        s = s[s.fav_side == side]
    if slot:
        s = s[s.snapshot == slot]
    if pick == "underdog":
        s = s.assign(won=1 - s.fav_won, paid=np.where(s.fav_side == "yes", s.no_ask, s.yes_ask), cost=s.dog_cost)
    else:
        s = s.assign(won=s.fav_won, paid=s.fav_ask, cost=s.fav_cost)
    s["edge"] = (s.won - s.cost) * 100
    rows = []
    for mk in [m for m in ORDER if (market is None or m == market)]:
        g = s[s.market == mk]
        if g.empty:
            continue
        e = g.groupby("event").agg(won=("won", "mean"), paid=("paid", "mean"), cost=("cost", "mean"), edge=("edge", "mean"))
        n = len(e)
        rows.append({"market": mk, "events": n, "instances": len(g), "win_pct": round(100 * e.won.mean(), 1), "paid_c": round(100 * e.paid.mean(), 1),
                     "break_even_pct": round(100 * e.cost.mean(), 1), "edge_pts": round(e.edge.mean(), 1),
                     "noise_pts": round(2 * e.edge.std() / np.sqrt(n), 1) if n > 1 else None,
                     "read": "too few events" if n < 30 else ("edge beyond noise" if abs(e.edge.mean()) > 2 * e.edge.std() / np.sqrt(n) else "inside noise")})
    ver = json.load(open(M / "VERSION.json"))["version"] if (M / "VERSION.json").exists() else "unversioned"
    return pd.DataFrame(rows), ver


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=50); ap.add_argument("--max", type=float, default=100)
    ap.add_argument("--side", choices=["yes", "no"]); ap.add_argument("--market"); ap.add_argument("--slot")
    ap.add_argument("--pick", choices=["favorite", "underdog"], default="favorite"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    df, ver = answer(a.min, a.max, a.side, a.market, a.slot, a.pick)
    print(df.to_json(orient="records") if a.json else df.to_string(index=False))
    print("master", ver)
