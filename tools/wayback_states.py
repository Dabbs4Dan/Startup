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


NAMES = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT",
 "Delaware":"DE","District of Columbia":"DC","Washington DC":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID",
 "Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
 "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE",
 "Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC",
 "North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI",
 "South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA",
 "Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}


def all_states_mode(since, stop_at):
    """ONE archived page = all 51 states (current Regular / Mid / Premium / Diesel) -> 51x faster than per-state pages."""
    import datetime, html as H
    url = "gasprices.aaa.com/state-gas-price-averages/"
    q = (f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&fl=timestamp"
         f"&filter=statuscode:200&from={since}&collapse=timestamp:8")
    body = get(q, timeout=90)
    try:
        snaps = [r[0] for r in json.loads(body)[1:]]
    except Exception:  # noqa
        print("CDX failed:", (body or "")[:200]); return
    path = OUT / "_all_states.csv"
    done = {r["snapshot_ts"] for r in csv.DictReader(path.open())} if path.exists() else set()
    print(f"all-states page: {len(snaps)} archived days since {since}, {len(done)} already saved", flush=True)
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if not done:
            w.writerow(COLS)
        for t in snaps:
            if t in done or time.time() > stop_at:
                continue
            page = get(f"https://web.archive.org/web/{t}id_/https://{url}")
            time.sleep(2)
            if not page:
                print(t, "fetch failed", flush=True); continue
            m = re.search(r"(?:Price as of|as of)\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})", page)
            as_of = m.group(1) if m else ""
            if as_of.count("/") == 2 and len(as_of.split("/")[2]) == 4:
                mm, dd, yy = as_of.split("/"); as_of = f"{mm}/{dd}/{yy[2:]}"
            if not as_of:   # fall back to snapshot date (UTC) -- flagged in grade column
                d = datetime.datetime.strptime(t[:8], "%Y%m%d"); as_of = d.strftime("%m/%d/%y"); flag = "~"
            else:
                flag = ""
            n = 0
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
                cells = [H.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
                if len(cells) >= 5 and cells[0] in NAMES:
                    vals = [num(c) for c in cells[1:5]]
                    st = NAMES[cells[0]]
                    w.writerow([t, as_of, st, "regular" + flag, vals[0], "", "", "", ""])
                    w.writerow([t, as_of, st, "diesel" + flag, vals[3], "", "", "", ""])
                    n += 1
            f.flush()
            print(t, as_of, "states:", n, flush=True)


def main():
    if "--all-states" in sys.argv:
        since = next((a for a in sys.argv[1:] if a.isdigit()), "20260801")
        max_min = int(sys.argv[sys.argv.index("--max-minutes") + 1]) if "--max-minutes" in sys.argv else 300
        OUT.mkdir(parents=True, exist_ok=True)
        all_states_mode(since, time.time() + max_min * 60)
        return
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
