#!/usr/bin/env python3
"""ENGINE ROOM — prove we can rebuild each pricing algo before hunting patterns.

Layers (top = what we trade, bottom = what builds it):
  L0  Kalshi market maker   ladder at each moment  = crowd centre mu + wiggle sigma (+ spread layer)
  L1  AAA national          the number contracts settle on
  L2  OPIS roll-up          51 state averages  -> national
  L3  Inputs under OPIS     truckstop / rack / HO futures -> state averages

Algos built so far:
  L0.1 ladder_rebuild   fit a normal curve (mu, sigma) to the YES ladder at every hourly snapshot (lines with spread
                        <= 10c and 3-97%), predict every line's price from (mu, sigma), score the miss in cents.
  L0.2 ladder_moves     every hour where mu moved >= 0.3c. Each is a question: "which input moved?" Until intraday
                        inputs exist for that hour it is logged as UNEXPLAINED (the shopping list for data).
  L2.1 state_blend_vol  national = average of the 51 state prices weighted by EIA 2024 transportation fuel use
                        (diesel: distillate; gas: motor gasoline). Zero fitted parameters.
  L2.0 state_mean       plain average of states (the 'dumb' baseline L2.1 must beat).

Tables (same in the diesel DB and the gas DB; run with KT_PRODUCT=gas for the twin):
  algo_registry     one row per algo version: layer, what it explains, pass line
  inputs_asof       product, as-of date/time, input, value, when it became knowable (point-in-time, any length)
  algo_predictions  algo, target time, predicted vs actual, miss (cents), detail json
  algo_scorecard    algo x window: n, median |miss|, share within tolerance, pass/fail
Exports: <exports>/engine_room_scorecard.csv, engine_room_moves.csv
Usage: python3 tools/engine_room.py            (KT_PRODUCT=gas for the twin)
"""
import csv, datetime, json, math, pathlib, sqlite3, statistics, sys
from statistics import NormalDist
from zoneinfo import ZoneInfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import product  # noqa: E402

ROOT = product.ROOT
P = product.PRODUCT
ND = NormalDist()
WEIGHTS = {"diesel": ROOT / "research" / "engine_room" / "eia_transport_distillate_2024.csv",
           "gas": ROOT / "research" / "engine_room" / "eia_transport_gasoline_2024.csv"}

REGISTRY = [
    # id, layer, name, explains, pass_rule, tol_cents
    ("L0.1", "L0", "Ladder rebuild (normal curve)", "Every line's YES price at each snapshot from 2 numbers: centre mu + wiggle sigma",
     "median line miss <= 2.0c over all snapshots", 2.0),
    ("L0.2", "L0", "Ladder moves log", "Hours where the crowd centre moved >= 0.3c; each needs an input that explains it",
     "info only: share of moves explained by inputs (target 80%+)", None),
    ("L2.0", "L2", "State plain average (baseline)", "National AAA as a simple mean of 51 states",
     "baseline only", 0.10),
    ("L2.1", "L2", "State blend, EIA volume-weighted", "National AAA = states weighted by EIA 2024 transportation fuel use (0 fitted numbers)",
     "|miss| <= 0.10c on exact-date points (current + yesterday), >= 90% of points", 0.10),
]


def db():
    con = sqlite3.connect(product.DB)
    con.row_factory = sqlite3.Row
    return con


def setup(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS algo_registry (algo_id TEXT PRIMARY KEY, layer TEXT, name TEXT, explains TEXT,
        pass_rule TEXT, tol_cents REAL, product TEXT, updated_utc TEXT);
    CREATE TABLE IF NOT EXISTS inputs_asof (product TEXT, asof TEXT, input TEXT, value REAL, knowable_at TEXT,
        source TEXT, PRIMARY KEY (product, asof, input));
    CREATE TABLE IF NOT EXISTS algo_predictions (algo_id TEXT, product TEXT, target TEXT, predicted REAL,
        actual REAL, miss_cents REAL, detail TEXT, run_utc TEXT, PRIMARY KEY (algo_id, product, target));
    CREATE TABLE IF NOT EXISTS algo_scorecard (algo_id TEXT, product TEXT, window TEXT, n INTEGER,
        median_abs_miss_c REAL, share_within_tol REAL, verdict TEXT, note TEXT, run_utc TEXT,
        PRIMARY KEY (algo_id, product, window));
    """)
    now = utcnow()
    for r in REGISTRY:
        con.execute("INSERT OR REPLACE INTO algo_registry VALUES (?,?,?,?,?,?,?,?)", (*r, P, now))


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save_pred(con, algo, target, pred, actual, detail, run):
    miss = None if pred is None or actual is None else round((pred - actual) * 100, 4)
    con.execute("INSERT OR REPLACE INTO algo_predictions VALUES (?,?,?,?,?,?,?,?)",
                (algo, P, target, pred, actual, miss, json.dumps(detail), run))
    return miss


def score(con, algo, window, misses, tol, note=""):
    misses = [abs(m) for m in misses if m is not None]
    n = len(misses)
    med = round(statistics.median(misses), 4) if n else None
    share = round(sum(m <= tol for m in misses) / n, 3) if n and tol is not None else None
    MIN_N = 20                                   # never call a pass on a handful of points
    if not n:
        verdict = "⬜ no data"
    elif share is not None and share >= 0.9:
        verdict = "✅ PASS" if n >= MIN_N else f"◐ promising (n={n}, need {MIN_N})"
    else:
        verdict = "❌ not yet"
    con.execute("INSERT OR REPLACE INTO algo_scorecard VALUES (?,?,?,?,?,?,?,?,?)",
                (algo, P, window, n, med, share, verdict, note, utcnow()))
    return n, med, share, verdict


# ---------------------------------------------------------------- L2: state blend
LOOKBACK = {"diesel_current": 0, "diesel_yesterday": 1, "diesel_week_ago": 7}   # exact-day offsets we trust
FUZZY = {"diesel_month_ago": "month", "diesel_year_ago": "year"}                # calendar offsets (date less certain)


def target_date(asof_day, col):
    if col in LOOKBACK:
        return asof_day - datetime.timedelta(days=LOOKBACK[col])
    if FUZZY[col] == "month":
        m, y = asof_day.month - 1 or 12, asof_day.year - (asof_day.month == 1)
        return asof_day.replace(year=y, month=m, day=min(asof_day.day, 28 if m == 2 else 30))
    return asof_day.replace(year=asof_day.year - 1)


def parse_asof(s):
    m, d, y = s.split("/")
    return datetime.date(2000 + int(y), int(m), int(d))


def load_gas_state_csvs(con):
    """Gas twin: state REGULAR prices are saved by daily_recorders.py as one CSV per day -> load into this DB."""
    folder = ROOT / "research" / "engine_room" / "aaa_states_gas"
    if P != "gas" or not folder.exists():
        return
    con.execute("""CREATE TABLE IF NOT EXISTS aaa_state_daily (pulled_date TEXT, as_of TEXT, state TEXT,
        diesel_current REAL, diesel_yesterday REAL, diesel_week_ago REAL, diesel_month_ago REAL, diesel_year_ago REAL,
        PRIMARY KEY (as_of, state))""")
    num = lambda x: float(x) if x not in ("", None) else None
    for f in sorted(folder.glob("*.csv")):
        for r in csv.DictReader(f.open()):
            con.execute("INSERT OR REPLACE INTO aaa_state_daily VALUES (?,?,?,?,?,?,?,?)",
                        (r["pulled_date"], r["as_of"], r["state"], num(r["current"]), num(r["yesterday"]),
                         num(r["week_ago"]), num(r["month_ago"]), num(r["year_ago"])))


def run_l2(con, run):
    load_gas_state_csvs(con)
    if not con.execute("SELECT name FROM sqlite_master WHERE name='aaa_state_daily'").fetchone():
        for a in ("L2.0", "L2.1"):
            score(con, a, "all", [], 0.10, "no state data yet (recorder saves it daily)")
        return {}
    w = {r["state"]: float(r["transport_kbbl"]) for r in csv.DictReader(WEIGHTS[P].open())}
    nat = dict(con.execute("SELECT date, aaa_diesel FROM diesel_daily WHERE aaa_diesel IS NOT NULL"))
    rows = con.execute("SELECT * FROM aaa_state_daily WHERE as_of IS NOT NULL ORDER BY pulled_date").fetchall()
    points = {}                                   # target date -> (states dict, kind, knowable_at); newest pull wins
    for r in rows:
        try:
            day = parse_asof(r["as_of"])
        except Exception:  # noqa
            continue
        for col in list(LOOKBACK) + list(FUZZY):
            v = r[col]
            if v is None:
                continue
            t = target_date(day, col).isoformat()
            kind = "exact" if col in ("diesel_current", "diesel_yesterday") else ("week" if col == "diesel_week_ago" else FUZZY[col])
            points.setdefault(t, {"states": {}, "kind": kind, "knowable": r["pulled_date"]})
            points[t]["states"][r["state"]] = v
            con.execute("INSERT OR REPLACE INTO inputs_asof VALUES (?,?,?,?,?,?)",
                        (P, t, f"aaa_state_{r['state']}", v, r["pulled_date"], f"AAA state page ({col})"))
    out = {"L2.0": {}, "L2.1": {}}
    for t, pt in sorted(points.items()):
        st = pt["states"]
        if len(st) < 45:
            continue
        actual = nat.get(t)
        mean = sum(st.values()) / len(st)
        ww = {s: w[s] for s in st if s in w}
        blend = sum(st[s] * ww[s] for s in ww) / sum(ww.values())
        d = {"kind": pt["kind"], "n_states": len(st), "knowable_at": pt["knowable"]}
        out["L2.0"][t] = (save_pred(con, "L2.0", t, round(mean, 4), actual, d, run), pt["kind"])
        out["L2.1"][t] = (save_pred(con, "L2.1", t, round(blend, 4), actual, d, run), pt["kind"])
    for a in ("L2.0", "L2.1"):
        exact = [m for m, k in out[a].values() if k == "exact"]
        allm = [m for m, _ in out[a].values()]
        score(con, a, "exact-date points", exact, 0.10, "current + yesterday columns (date certain)")
        score(con, a, "all points", allm, 0.10, "incl. week / month / year-ago columns (dates approximate)")
    return out


# ---------------------------------------------------------------- L0: ladder rebuild
def fit_ladder(lines):
    """lines: [(strike, mid)] -> (mu, sigma) from probit regression: z = Phi^-1(1-p) = (K - mu) / sigma."""
    pts = [(k, ND.inv_cdf(1 - min(max(p, 0.03), 0.97))) for k, p in lines]
    if len(pts) < 2:
        return None
    n = len(pts)
    mk = sum(k for k, _ in pts) / n
    mz = sum(z for _, z in pts) / n
    sxx = sum((k - mk) ** 2 for k, _ in pts)
    if sxx == 0:
        return None
    b = sum((k - mk) * (z - mz) for k, z in pts) / sxx
    if b <= 0:
        return None
    a = mz - b * mk
    return -a / b, 1 / b


def run_l0(con, run):
    settle = dict(con.execute("SELECT event_date, MAX(expiration_value) FROM kalshi_markets "
                              "WHERE expiration_value IS NOT NULL GROUP BY event_date"))
    rows = con.execute("SELECT event_date, end_ts, strike, yes_bid, yes_ask FROM kalshi_candles WHERE period_min = 60 "
                       "AND yes_bid IS NOT NULL AND yes_ask IS NOT NULL ORDER BY event_date, end_ts").fetchall()
    snaps = {}
    for r in rows:
        snaps.setdefault((r["event_date"], r["end_ts"]), []).append(r)
    misses, moves, last = [], [], {}
    con.execute("DELETE FROM algo_predictions WHERE product=? AND algo_id IN ('L0.1','L0.2')", (P,))
    for (ev, ts), lines in sorted(snaps.items()):
        usable = [(r["strike"], (r["yes_bid"] + r["yes_ask"]) / 2) for r in lines
                  if r["yes_ask"] - r["yes_bid"] <= 0.10 and 0.03 <= (r["yes_bid"] + r["yes_ask"]) / 2 <= 0.97]
        fit = fit_ladder(usable)
        if not fit:
            continue
        mu, sig = fit
        if not (0.0001 <= sig <= 0.05):
            continue
        errs = [abs((1 - ND.cdf((k - mu) / sig)) - p) * 100 for k, p in usable]
        line_miss = statistics.median(errs)
        misses.append(line_miss)
        t_iso = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        con.execute("INSERT OR REPLACE INTO algo_predictions VALUES (?,?,?,?,?,?,?,?)",
                    ("L0.1", P, f"{ev}|{t_iso}", round(mu, 5), settle.get(ev), round(line_miss, 3),
                     json.dumps({"sigma_c": round(sig * 100, 3), "n_lines": len(usable),
                                 "mu_vs_settle_c": round((mu - settle[ev]) * 100, 3) if settle.get(ev) else None}), run))
        prev = last.get(ev)
        if prev and ts - prev[0] <= 3600 * 2 and abs(mu - prev[1]) * 100 >= 0.3:
            ny = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).astimezone(ZoneInfo("America/New_York"))
            mv = {"event": ev, "time_utc": t_iso, "hour_et": ny.hour, "mu_from": round(prev[1], 4), "mu_to": round(mu, 4),
                  "move_c": round((mu - prev[1]) * 100, 2), "explained_by": None,
                  "status": "UNEXPLAINED (no intraday inputs stored for this hour yet)"}
            moves.append(mv)
            con.execute("INSERT OR REPLACE INTO algo_predictions VALUES (?,?,?,?,?,?,?,?)",
                        ("L0.2", P, f"{ev}|{t_iso}", round(mu, 5), round(prev[1], 5), mv["move_c"], json.dumps(mv), run))
        last[ev] = (ts, mu)
    score(con, "L0.1", "all hourly snapshots", misses, 2.0, "median line miss per snapshot, cents")
    n = len(moves)
    con.execute("INSERT OR REPLACE INTO algo_scorecard VALUES (?,?,?,?,?,?,?,?,?)",
                ("L0.2", P, "all hours", n, None, 0.0 if n else None, "🔎 info",
                 f"{n} moves >= 0.3c; 0 explained yet (needs intraday HO / rack / truckstop inputs)", utcnow()))
    return misses, moves


def export(con):
    product.EXPORTS.mkdir(parents=True, exist_ok=True)
    rows = con.execute("SELECT s.algo_id, r.layer, r.name, s.window, s.n, s.median_abs_miss_c, s.share_within_tol, "
                       "s.verdict, r.pass_rule, s.note FROM algo_scorecard s JOIN algo_registry r USING (algo_id) "
                       "WHERE s.product=? ORDER BY s.algo_id, s.window", (P,)).fetchall()
    with (product.EXPORTS / "engine_room_scorecard.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["algo", "layer", "name", "window", "n", "median_abs_miss_c", "share_within_tol", "verdict", "pass_rule", "note"])
        w.writerows([tuple(r) for r in rows])
    pts = con.execute("SELECT algo_id, target, predicted, actual, miss_cents, detail FROM algo_predictions "
                      "WHERE product=? AND algo_id IN ('L2.0','L2.1') ORDER BY target DESC, algo_id", (P,)).fetchall()
    with (product.EXPORTS / "engine_room_l2_points.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "algo", "kind", "predicted_national", "actual_aaa", "miss_cents", "n_states", "knowable_at"])
        for a, t, pr, ac, m, d in pts:
            d = json.loads(d)
            w.writerow([t, a, d.get("kind"), pr, ac, m, d.get("n_states"), d.get("knowable_at")])
    mv = con.execute("SELECT detail FROM algo_predictions WHERE algo_id='L0.2' AND product=? ORDER BY target", (P,)).fetchall()
    with (product.EXPORTS / "engine_room_moves.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event", "time_utc", "hour_et", "mu_from", "mu_to", "move_c", "status"])
        for (d,) in mv:
            d = json.loads(d)
            w.writerow([d["event"], d["time_utc"], d["hour_et"], d["mu_from"], d["mu_to"], d["move_c"], d["status"]])
    return rows


def main():
    con = db()
    setup(con)
    run = utcnow()
    run_l2(con, run)
    _, moves = run_l0(con, run)
    con.commit()
    for r in export(con):
        print(" | ".join("" if x is None else str(x) for x in tuple(r)[:8]))
    if moves:
        by_hour = {}
        for m in moves:
            by_hour[m["hour_et"]] = by_hour.get(m["hour_et"], 0) + 1
        print("L0.2 moves by hour (ET):", dict(sorted(by_hour.items())))


if __name__ == "__main__":
    main()
