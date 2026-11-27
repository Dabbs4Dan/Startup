#!/usr/bin/env python3
"""The spine: one page that says how every research table connects, and proves the joins really work.

Every table hangs off the same keys:  market -> event -> snapshot_et -> strike   (dates join to inputs by asof_date)
Run after any table is rebuilt. Out: data/lake/master/SPINE.md (read this before touching a table) + spine.csv
Two engines every test must declare:
  E1 settle engine   = hold to the end: did the line settle Yes or No vs the price paid (master, slices, ledger)
  E2 intraday engine = trade the price path between time slots, exit before the end (ladder_snapshots -> paths, planned)
"""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
M, E = ROOT / "data/lake/master", ROOT / "research/engine_room"
T = [  # name, path, layer, grain (key columns), built by, engine, what it is
    ("inputs_daily", M / "inputs_daily.csv", "L0 inputs", ["date"], "tools/backtest_master.py", "both", "outside inputs per day, already lagged to be safe"),
    ("aaa_daily", M / "aaa_daily.csv", "L0 inputs", ["date", "fuel"], "tools/backtest_master.py", "both", "the AAA answer per day, reconciled"),
    ("backtest_master", M / "backtest_master.csv.gz", "L1 master", ["event", "snapshot", "snapshot_et"], "tools/backtest_master.py", "both", "one row per event x time slot: crowd center, range, 3 busy lines, ~75 inputs"),
    ("ladder_snapshots", M / "ladder_snapshots.csv.gz", "L1 master", ["event", "snapshot", "snapshot_et", "floor_strike"], "tools/backtest_master.py", "E2 (and shape layer)", "every line's bid / ask at every time slot"),
    ("slices", M / "slices.csv.gz", "L2 slices + L3 ratios", ["event", "snapshot", "snapshot_et", "line_rank"], "tools/slice_scan.py", "E1", "favorite side, cost, outcome box, returns, our 11 ratios"),
    ("favorite_ledger", E / "favorite_ledger.csv", "L2 roll-up", ["market", "favorite", "price_band"], "tools/slice_scan.py", "E1", "plain count of the 4 boxes by price band, win % vs break-even"),
    ("favorite_ledger_by_time_and_line", E / "favorite_ledger_by_time_and_line.csv", "L2 roll-up", ["market", "favorite", "cut", "value"], "tools/slice_scan.py", "E1", "same count by time slot and by busy-line rank"),
    ("slice_scan", E / "slice_scan.csv", "L3 scan", ["market", "fav_side", "bet", "slice"], "tools/slice_scan.py", "E1", "every slice tested early vs late, false-winner filter"),
    ("mm_model_scorecard", E / "mm_model_scorecard.csv", "L4 market-maker copy", ["fuel", "slice"], "tools/mm_model.py", "both", "how well we copy center / range / shape / cost"),
    ("mm_anchor_scorecard", E / "mm_anchor_scorecard.csv", "L4 market-maker copy", ["fuel", "slice"], "tools/mm_anchor.py", "both", "copy built from big outside data + 2 dials; line price gap"),
    ("l3_truckstop_scorecard", E / "l3_truckstop_scorecard.csv", "live test", [], "tools/truckstop_test.py", "E1", "live: truckstop move vs what the crowd missed"),
]
SHEETS = [  # workbook, tab, role, fed from (database file), verdict (audit 2026-11-27)
    ("Build Board", "Takeaways – master", "what is true now", "research/takeaways/master.csv", "LIVE"),
    ("Build Board", "Takeaways – by chat", "each chat's closing table", "research/takeaways/by_chat.csv", "LIVE"),
    ("Build Board", "Favorite Ledger", "the 4 outcome boxes by price band", "research/engine_room/favorite_ledger.csv", "LIVE"),
    ("Build Board", "Backtest Master", "how far back each market and input goes", "data/lake/master/COVERAGE.md", "LIVE, refresh after each master rebuild (last 11/26)"),
    ("Build Board", "Board", "Dan's kanban of 21 build cards", "none (hand-kept)", "OVERLAPS CLAUDE.md section 6 and the Cards tab; not updated since the direction changed on 11/26"),
    ("Build Board", "Cards", "same 21 cards as a list", "none (hand-kept)", "DUPLICATE of Board"),
    ("Build Board", "Backtest – horizons", "old daily / weekly / monthly miss table", "legacy scripts (backtest_horizons*.py)", "SUPERSEDED by the master + mm_model scorecards"),
    ("Build Board", "Example – weather bot", "outside example", "none", "NOT CONNECTED (off-limits market)"),
    ("Build Board", "Example – MLB bot", "outside example", "none", "NOT CONNECTED (off-limits market)"),
    ("Inputs Map", "Inputs Map", "the 83 inputs and whether we hold each (column O)", "data/lake/master/inputs_daily.csv + COVERAGE.md", "LIVE"),
    ("Inputs Map", "Engine Room", "pricing layers L0-L3 scorecard", "tools/engine_room.py via tools/sheet_payload.py", "LIVE but missing L4 (market-maker copy: mm_model / mm_anchor scorecards)"),
    ("Inputs Map", "Warehouse", "every dataset + feed health", "data/warehouse_catalog.csv via tools/sheet_payload.py", "STALE since 11/25 (catalog not rebuilt; open oddity)"),
    ("Inputs Map", "Strategies", "strategy gates tied to nautilus code", "nautilus/", "LIVE, waits on proven bricks"),
    ("Inputs Map", "Bricks", "idea hopper from the first 60-day work", "none (hand-kept)", "OVERLAPS slice_scan survivors + favorite ledger leads; should be fed from them"),
    ("Inputs Map", "Testing", "old test tree (T1.1 ...)", "DB table from Chat 2-3", "SUPERSEDED by LOG plans + takeaways"),
    ("Inputs Map", "60 Day", "the first 60-day panel", "panel_daily in data/kalshi_twins.db", "SUPERSEDED by the master (kept as history)"),
    ("Inputs Map", "Connectivity", "one-day pipe test (Nov 23)", "none", "FROZEN history"),
    ("Inputs Map", "Formulas", "the 18 formulas in plain words", "research/2026-11-25_formulas-and-panel-columns.md", "REFERENCE"),
    ("Inputs Map", "Custom Build", "data that needs more than a daily job", "none (hand-kept)", "OVERLAPS Wishlist + CLAUDE.md section 6 step 2 + the gaps doc"),
    ("Inputs Map", "Wishlist", "data or systems to add later", "none (hand-kept)", "OVERLAPS Custom Build + section 6 step 2 + the gaps doc"),
]
PLANNED = [("paths", "L2 for E2", "event x strike x (time slot in -> time slot out)", "buy at one slot's ask, sell at a later slot's bid: the intraday engine's raw table. Not built yet (Dan: after the tracking datasets are nailed).")]


def main():
    rows, tabs = [], {}
    for name, path, layer, grain, tool, eng, what in T:
        r = {"table": name, "layer": layer, "engine": eng, "grain": " x ".join(grain) or "see file", "built_by": tool, "file": str(path.relative_to(ROOT)), "what": what}
        if not path.exists():
            r["status"] = "MISSING"
        else:
            d = pd.read_csv(path, low_memory=False)
            if "snapshot_et" in d:
                d["snapshot_et"] = pd.to_datetime(d.snapshot_et, format="mixed")   # the builder writes two text styles; compare as times
            tabs[name] = d
            r.update({"rows": len(d), "columns": d.shape[1], "status": "ok"})
            if grain and all(g in d for g in grain):
                r["duplicate_keys"] = int(d.duplicated(grain).sum())
            if "event" in d:
                r["events"] = d.event.nunique()
            for c in ("settle_date", "date"):
                if c in d:
                    r["from"], r["to"] = str(d[c].min())[:10], str(d[c].max())[:10]
                    break
        rows.append(r)
    checks = []

    def chk(what, ok, total):
        checks.append({"check": what, "pass": int(ok), "of": int(total), "pct": round(100 * ok / max(total, 1), 1)})
    m, lad, sl, inp, aaa = (tabs.get(k) for k in ("backtest_master", "ladder_snapshots", "slices", "inputs_daily", "aaa_daily"))
    if m is not None:
        mk = set(zip(m.event, m.snapshot_et))
        if lad is not None:
            k = set(zip(lad.event, lad.snapshot_et))
            chk("ladder rows hang off a master row (event + time slot)", len(k & mk), len(k))
        if sl is not None:
            k = set(zip(sl.event, sl.snapshot_et))
            chk("slice rows hang off a master row (event + time slot)", len(k & mk), len(k))
            if lad is not None:
                lk = set(zip(lad.event, lad.snapshot_et, lad.floor_strike.round(4)))
                k = set(zip(sl.event, sl.snapshot_et, sl.strike.round(4)))
                chk("slice lines exist in the full ladder (event + time slot + strike)", len(k & lk), len(k))
        if inp is not None:
            d = set(inp.date.astype(str).str[:10])
            a = m.asof_date.astype(str).str[:10]
            chk("master rows whose as-of day exists in the inputs table", a.isin(d).sum(), len(a))
        if aaa is not None:
            ev = m.drop_duplicates("event")[["fuel", "settle_date", "settle_value"]].dropna()
            ev["date"] = ev.settle_date.astype(str).str[:10]
            j = ev.merge(aaa.assign(date=aaa.date.astype(str).str[:10]), on=["date", "fuel"], how="left")
            has = j.value.notna()
            chk("events whose settle day has an AAA number in aaa_daily", has.sum(), len(j))
            chk("of those, settle value equals the AAA number (to 0.1 cent)", ((j.value - j.settle_value).abs() < 0.0011)[has].sum(), has.sum())
    if m is not None:
        hr = {"10am": 10, "noon": 12, "3pm": 15, "6pm": 18, "10pm": 22}
        c = m[m.snapshot.isin(hr)]
        chk("clock-mark rows whose label matches the real hour (misses = the 2 days a year clocks change; known builder bug)", (c.snapshot_et.dt.hour == c.snapshot.map(hr)).sum(), len(c))
        chk("master rows that are a distinct moment (misses = the open landing on a clock mark, counted twice downstream)", len(m) - m.duplicated(["event", "snapshot_et"]).sum(), len(m))
    if sl is not None:
        led = tabs.get("favorite_ledger")
        if led is not None:
            a = led[(led.market == "ALL SIX") & (led.price_band == "all")].instances.sum()
            chk("ledger instance count equals slice rows", min(a, len(sl)), max(a, len(sl)))
    s = pd.DataFrame(rows)
    s.to_csv(M / "spine.csv", index=False)
    c = pd.DataFrame(checks)
    L = ["# The spine: how every research table connects", "",
         f"Built by `tools/spine.py` on {pd.Timestamp.utcnow():%Y-%m-%d %H:%M} UTC. Re-run after any table is rebuilt. Read this before adding a table.", "",
         "**One set of keys:** market → event → time slot (`snapshot_et`) → line (`strike`). Days join to inputs by `asof_date`.", "",
         "**Layers:** L0 inputs → L1 master → L2 slices (4 outcome boxes) → L3 our ratios + scan → L4 market-maker copy → takeaways (`research/takeaways/master.csv`).", "",
         "**Two engines (every test says which one it is):**",
         "- **E1 settle engine:** hold to the end. Did the line settle Yes or No vs the price paid.",
         "- **E2 intraday engine:** trade the price path between time slots and exit before the end.", "",
         "## Tables", "", "| Table | Layer | Engine | One row is | Rows | Events | From | To | Duplicate keys | Built by | File |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        g = lambda k: "" if pd.isna(r.get(k, float("nan"))) else r.get(k)
        L.append(f"| **{r['table']}** | {r['layer']} | {r['engine']} | {r['grain']} | {g('rows')} | {g('events')} | {g('from')} | {g('to')} | {g('duplicate_keys')} | `{r['built_by']}` | `{r['file']}` |")
    L += ["", "## Planned (not built)", ""] + [f"- **{n}** ({lay}): one row is {grain}. {what}" for n, lay, grain, what in PLANNED]
    L += ["", "## Join checks (do the tables really connect?)", "", "| Check | Pass | Of | % |", "|---|---|---|---|"] + [f"| {r.check} | {r['pass']} | {r.of} | {r.pct} |" for _, r in c.iterrows()]
    L += ["", "## Sheet tabs (read-only windows; audit 2026-11-27)", "", "| Workbook | Tab | Role | Fed from | Verdict |", "|---|---|---|---|---|"] + \
         [f"| {w} | {t} | {r} | `{f}` | {v} |" for w, t, r, f, v in SHEETS]
    L += ["", "## Rules", "", "- A new table must name its layer, its engine, and its key columns from the set above, and be added to `T` in `tools/spine.py`.",
          "- A new test writes its plan in `research/LOG.md` first, names the table and engine it reads, and lands its verdict in `research/takeaways/master.csv`.",
          "- Roll-ups (ledger, scan) are rebuilt from `slices`; never edited by hand.",
          "- **Database vs sheet:** these files are the database (query them through `tools/warehouse.py`, schema `lab`). Google Sheets tabs are read-only copies for Dan's phone; nothing is ever built or tested in a sheet.",
          "", "## Known issues (fix in the builder, then re-run everything downstream)", "",
          "- `snapshot_et` is written in two text styles; compare it as a time, not as text.",
          "- On the two days a year clocks change, the five clock marks sit one hour early (60 of 11,747 rows).",
          "- When a market opens exactly on a clock mark, that moment appears twice (open + the mark): 108 master rows, 133 slice rows (0.6%)."]
    (M / "SPINE.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[14:]))


if __name__ == "__main__":
    main()
