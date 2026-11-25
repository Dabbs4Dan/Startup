#!/usr/bin/env python3
"""L2 history booster: read OLD AAA state pages from the Internet Archive (Wayback Machine).

Each archived gasprices.aaa.com/?state=XX page shows that day's state table (current / yesterday / week / month /
year ago) for Regular and Diesel. One pass = history for BOTH twins. Kalshi settlements give the national answer
(diesel since Aug 2026, gas since 2023), so every recovered day is a new L2 test point.

Output: research/engine_room/wayback_states/<STATE>.csv (append, de-duplicated by snapshot):
  snapshot_ts, as_of, state, grade(regular|diesel), current, yesterday, week_ago, month_ago, year_ago
Resumable: skips snapshots already saved. Usage: python3 tools/wayback_states.py [FROM_YYYYMMDD] [--max-minutes 300]
"""
import csv, json, pathlib, re, sys, time, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from connectivity_pull import parse_tables, STATES  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "engine_room" / "wayback_states"
UA = {"User-Agent": "kalshi-twins research (github.com/Dabbs4Dan/Startup)"}
COLS = ["snapshot_ts", "as_of", "state", "grade", "current", "yesterday", "week_ago", "month_ago", "year_ago"]
LABELS = ["Current Avg.", "Yesterday Avg.", "Week Ago Avg.", "Month Ago Avg.", "Year Ago Avg."]


def get(url, timeout=45, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa
            if "429" in str(e) or "503" in str(e):
                time.sleep(20 * (i + 1))
            else:
                time.sleep(3 * (i + 1))
    return None


def num(x):
    try:
        return float(str(x).replace("$", "").strip())
    except Exception:  # noqa
        return None


def snapshots(state, since):
    q = (f"https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com/%3Fstate%3D{state}&output=json"
         f"&fl=timestamp&filter=statuscode:200&from={since}&collapse=timestamp:8")
    body = get(q, timeout=60)
    try:
        return [r[0] for r in json.loads(body)[1:]]
    except Exception:  # noqa
        return None


def main():
    since = next((a for a in sys.argv[1:] if a.isdigit()), "20260801")
    max_min = int(sys.argv[sys.argv.index("--max-minutes") + 1]) if "--max-minutes" in sys.argv else 300
    stop_at = time.time() + max_min * 60
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for s in STATES:
        path = OUT / f"{s}.csv"
        done = set()
        if path.exists():
            done = {r["snapshot_ts"] for r in csv.DictReader(path.open())}
        snaps = snapshots(s, since)
        time.sleep(2)
        if snaps is None:
            report[s] = "cdx failed"
            continue
        todo = [t for t in snaps if t not in done]
        new = 0
        with path.open("a", newline="") as f:
            w = csv.writer(f)
            if not done:
                w.writerow(COLS)
            for t in todo:
                if time.time() > stop_at:
                    break
                html = get(f"https://web.archive.org/web/{t}id_/https://gasprices.aaa.com/?state={s}")
                time.sleep(1.2)
                if not html:
                    continue
                m = re.search(r"Price as of\s*([0-9/]+)", html)
                tabs = parse_tables(html)
                if not tabs:
                    continue
                tb = tabs[0]
                for grade, idx in (("regular", 0), ("diesel", 3)):
                    vals = [num(tb.get(l, [None] * 4)[idx]) if len(tb.get(l, [])) > idx else None for l in LABELS]
                    if any(v is not None for v in vals):
                        w.writerow([t, m.group(1) if m else "", s, grade, *vals])
                new += 1
                f.flush()
        report[s] = {"archived": len(snaps), "new": new, "already": len(done)}
        print(s, report[s], flush=True)
        if time.time() > stop_at:
            print("time budget reached; rerun to continue")
            break
    (OUT / "_last_run.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
