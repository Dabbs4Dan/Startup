#!/usr/bin/env python3
"""L3 truckstop test: do truckstop price moves on day X-1 explain what the crowd MISSES about day X's AAA?

Rebuilds one row per ET day from the raw live files (no DB, stdlib only, safe to re-run):
  data/live/truckstops/*.csv      -> how much posted diesel moved that day (per chain / lane)
  data/live/aaa_national/*.csv    -> AAA national per "price_as_of" date
  data/live/kalshi_markets/*.csv  -> crowd's forecast (50% crossing of the ladder) at 10 AM ET and at the last snapshot

Output: research/engine_room/l3_truckstop_scorecard.csv  (+ a summary line on stdout)

The test (read after >= 10 scored days, target 20+ per the Engine Room rule):
  surprise = actual AAA change - change the crowd expected
  Does `ts_move_c` (truckstop move on bet day) line up with `surprise_10am_c`? If yes, truckstops carry
  information the 10 AM crowd lacks. Compare with `surprise_close_c`: if the link is gone by close,
  the crowd learns it during the day and the edge is TIMING (bet before they do).
No peeking: ts_move_10am_c uses only snapshots up to 10:10 AM ET on the bet day.
"""
import csv, datetime, glob, pathlib, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "engine_room" / "l3_truckstop_scorecard.csv"
LANES = {"Diesel|DIESEL": "loves_truck", "Auto Diesel|AUTO DIESEL": "loves_auto", "Auto Diesel": "ta_auto"}
D = datetime.datetime


def et(ts_utc):
    """UTC ISO string -> naive ET datetime (zoneinfo if available, else fixed -5h)."""
    t = D.strptime(ts_utc[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return t.astimezone(ZoneInfo("America/New_York")).replace(tzinfo=None)
    except Exception:
        return (t - datetime.timedelta(hours=5)).replace(tzinfo=None)


def rows(pattern):
    for f in sorted(glob.glob(str(ROOT / pattern))):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh):
                yield r


def truckstop_days():
    """{et_date: {lane: {snapshot_time: {store: price}}}}"""
    out = {}
    for r in rows("data/live/truckstops/2*.csv"):
        lane = LANES.get(r["product"]) if r["chain"] in ("loves", "ta") else None
        if not lane or (lane == "ta_auto") != (r["chain"] == "ta"):
            continue
        try:
            p = float(r["price"])
        except ValueError:
            continue
        t = et(r["ts_utc"])
        snap = t.replace(minute=0, second=0)
        out.setdefault(t.date(), {}).setdefault(lane, {}).setdefault(snap, {})[r["store"]] = p
    return out


def move(snaps, upto=None, base=None):
    """Average change in cents across stores in both the baseline and the last snapshot (<= upto).
    Baseline = yesterday's last snapshot when we have it (so overnight moves count), else today's first."""
    ts = sorted(t for t in snaps if upto is None or t <= upto)
    if len(ts) < (1 if base else 2):
        return None, None, len(ts), 0
    a, b = base or snaps[ts[0]], snaps[ts[-1]]
    both = [s for s in a if s in b]
    if not both:
        return None, None, len(ts), 0
    ch = [(b[s] - a[s]) * 100 for s in both]
    return round(statistics.fmean(ch), 3), round(sum(1 for c in ch if abs(c) > 1e-9) / len(ch), 3), len(ts), len(both)


def aaa_by_date():
    out = {}
    for r in rows("data/live/aaa_national/2*.csv"):
        try:
            d = D.strptime(r["price_as_of"], "%m/%d/%y").date()
            out[d] = float(r["diesel_current"])
        except (ValueError, KeyError):
            continue
    return out


def crowd_centers():
    """{settle_date: (center at 10 AM ET on bet day, center at last snapshot)} for KXDIESELD."""
    ladders = {}
    for r in rows("data/live/kalshi_markets/2*.csv"):
        if not r.get("event", "").startswith("KXDIESELD-"):
            continue
        try:
            mid = (float(r["yes_bid"]) + float(r["yes_ask"])) / 2
            k = float(r["strike"])
        except ValueError:
            continue
        ladders.setdefault(r["event"], {}).setdefault(r["ts_et"], []).append((k, mid))

    def center(lad):
        lad = sorted(lad)
        for (k0, m0), (k1, m1) in zip(lad, lad[1:]):
            if m0 >= 0.5 > m1:
                return k0 + (m0 - 0.5) / (m0 - m1) * (k1 - k0)
        return None

    out = {}
    for ev, snaps in ladders.items():
        try:
            settle = D.strptime(ev.split("-")[1], "%y%b%d").date()
        except ValueError:
            continue
        bet_day = settle - datetime.timedelta(days=1)
        ts = sorted(snaps)
        cut = f"{bet_day} 10:10"
        early = [t for t in ts if f"{bet_day} 09:30" <= t <= cut]
        out[settle] = (center(snaps[early[-1]]) if early else None, center(snaps[ts[-1]]), ts[-1])
    return out


def c(x, nd=2):
    return "" if x is None else round(x, nd)


def main():
    ts, aaa, crowd = truckstop_days(), aaa_by_date(), crowd_centers()
    out = []
    for day in sorted(ts):
        nxt = day + datetime.timedelta(days=1)
        a0, a1 = aaa.get(day), aaa.get(nxt)
        c10, ccl, clast = crowd.get(nxt, (None, None, ""))
        row = {"bet_day": day, "settle_day": nxt}
        ten = D.combine(day, datetime.time(10, 10))
        moves = []
        prev = ts.get(day - datetime.timedelta(days=1), {})
        for lane in ("loves_truck", "loves_auto", "ta_auto"):
            pv = prev.get(lane, {})
            base = pv[max(pv)] if pv else None
            m, share, n_snap, n_store = move(ts[day].get(lane, {}), base=base)
            m10, _, _, _ = move(ts[day].get(lane, {}), upto=ten, base=base)
            row.update({f"{lane}_move_c": c(m, 3), f"{lane}_share_changed": c(share, 3),
                        f"{lane}_move_10am_c": c(m10, 3), f"{lane}_stores": n_store, f"{lane}_snaps": n_snap})
            if m is not None and lane != "ta_auto":
                moves.append((m, n_store))
        tsm = sum(m * n for m, n in moves) / sum(n for _, n in moves) if moves else None
        row["ts_move_c"] = c(tsm, 3)                      # Love's all lanes, store-weighted, full ET day
        row["aaa_bet_day"] = c(a0, 4)
        row["crowd_10am"] = c(c10, 4)
        row["crowd_close"] = c(ccl, 4)
        row["crowd_last_snapshot_et"] = clast
        row["aaa_settle"] = c(a1, 4)
        chg = (a1 - a0) * 100 if a0 and a1 else None
        row["aaa_change_c"] = c(chg)
        row["surprise_10am_c"] = c(chg - (c10 - a0) * 100) if chg is not None and c10 else ""
        row["surprise_close_c"] = c(chg - (ccl - a0) * 100) if chg is not None and ccl else ""
        row["status"] = "scored" if chg is not None and ccl else ("waiting for AAA" if a1 is None else "partial")
        out.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()) if out else ["bet_day"])
        w.writeheader()
        w.writerows(out)
    scored = [r for r in out if r["status"] == "scored" and r["ts_move_c"] != "" and r["surprise_close_c"] != ""]
    msg = f"L3 truckstop scorecard: {len(out)} day(s), {len(scored)} scored"
    if len(scored) >= 5:
        xs = [float(r["ts_move_c"]) for r in scored]
        for col in ("surprise_10am_c", "surprise_close_c", "aaa_change_c"):
            ys = [float(r[col]) for r in scored if r[col] != ""]
            if len(ys) == len(xs) and statistics.pstdev(xs) > 0 and statistics.pstdev(ys) > 0:
                msg += f" | corr(ts_move, {col}) = {statistics.correlation(xs, ys):+.2f}"
    msg += " | verdict needs >= 10 scored days (20+ to PASS)" if len(scored) < 10 else ""
    print(msg)


if __name__ == "__main__":
    sys.exit(main())
