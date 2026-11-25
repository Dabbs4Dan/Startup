#!/usr/bin/env python3
"""Replay events through NautilusTrader with one registered strategy.

  python3 nautilus/run_backtest.py                       # S00 plumbing check, last 3 settled events + live data
  python3 nautilus/run_backtest.py --events all
  python3 nautilus/run_backtest.py --strategy S01 --events KXDIESELD-26NOV24
Writes nautilus/reports/latest_<strategy>.json (committed, so the sheet / other sessions can read it).
"""
import argparse, datetime, json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nautilus_trader  # noqa: E402
from kt_nautilus import PINNED_VERSION, instruments as ins  # noqa: E402
from kt_nautilus.common import REPORTS  # noqa: E402
from kt_nautilus.engine import build  # noqa: E402
from kt_nautilus.strategies import REGISTRY  # noqa: E402


def iso(ns):
    return datetime.datetime.fromtimestamp(ns / 1e9, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ") if ns else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="S00")
    ap.add_argument("--events", nargs="*", default=["recent"])
    ap.add_argument("--recent", type=int, default=3)
    ap.add_argument("--no-live", action="store_true")
    a = ap.parse_args()

    settled = ins.list_events(settled_only=True)
    every = ins.list_events(settled_only=False)
    if a.events == ["all"]:
        events = settled
    elif a.events == ["recent"]:
        events = settled[-a.recent:] + [e for e in every if e not in settled]   # + open events (live data)
    else:
        events = a.events
    t0 = time.time()
    engine, meta, counts = build(events, include_live=not a.no_live)
    strat = REGISTRY[a.strategy]()
    engine.add_strategy(strat)
    engine.run()
    stats = getattr(strat, "stats", {})
    report = {
        "run_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_version": nautilus_trader.__version__, "pinned": PINNED_VERSION,
        "version_ok": nautilus_trader.__version__ == PINNED_VERSION,
        "strategy": a.strategy, "seconds": round(time.time() - t0, 1), "loaded": counts,
        "replayed": {ev: {"quotes": s["quotes"], "trades": s["trades"], "first": iso(s["first_ns"]),
                          "last": iso(s["last_ns"])} for ev, s in sorted(stats.items())},
    }
    rq = sum(s["quotes"] for s in stats.values())
    rt = sum(s["trades"] for s in stats.values())
    report["check"] = {"quotes_in": counts["candle_quotes"] + counts["live_quotes"], "quotes_replayed": rq,
                       "trades_in": counts["trades"], "trades_replayed": rt,
                       "pass": rq == counts["candle_quotes"] + counts["live_quotes"] and rt == counts["trades"]}
    try:
        report["orders"] = len(engine.cache.orders())
    except Exception:  # noqa
        pass
    engine.dispose()
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"latest_{a.strategy}.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("engine_version", "loaded", "check", "seconds")}, indent=2))
    print("wrote", out.relative_to(REPORTS.parents[1]))
    sys.exit(0 if report["check"]["pass"] else 1)


if __name__ == "__main__":
    main()
