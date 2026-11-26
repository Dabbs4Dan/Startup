#!/usr/bin/env python3
"""History puller: free long-history sources -> data/lake/history/*.csv (the warehouse's history zone).

Runs on GitHub (Claude's sandbox can't reach these sites). Every part fails soft and is safe to re-run.
  eia      EIA daily spot + NYMEX front-month settlements (since 1986-2006) and weekly retail diesel / gas by region
           -> eia_<series>.csv  (date, value)        [Inputs Map #33 HO, #36 Brent, #39 WTI, #40 RBOB, #43-45 spot, #63, #83]
  yahoo    HO/BZ/RB/CL/NG intraday bars: 60m (~2 years), 5m (~60 days), 1m (~7 days). MERGED into existing files,
           so running daily makes the minute history grow forever -> yahoo_<SYM>_<int>.csv
  wayback  AAA NATIONAL page snapshots from the Internet Archive (one per day). Each snapshot holds today / yesterday /
           week / month / year ago for regular, mid, premium, diesel -> aaa_national_wayback.csv
           (The state pages are handled by tools/wayback_states.py; this is the national number = Kalshi's target.)
  daily    Yahoo front-month futures, daily bars, full history (HO, RBOB, Brent, WTI, natgas) -> fut_<name>_1d.csv
Usage: python3 tools/history_pull.py [eia] [daily] [yahoo] [wayback] [--since 2019] [--max-minutes 200]
"""
import csv, datetime, io, json, pathlib, re, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lake" / "history"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

EIA = {  # series id: (frequency letter for hist_xls, short name)
    "EER_EPD2F_PE1_Y35NY_DPG": ("d", "ho_futures_m1"),          # NYMEX ULSD (HO) front month settle $/gal
    "EER_EPMRR_PE1_Y35NY_DPG": ("d", "rbob_futures_m1"),        # NYMEX RBOB front month settle
    "EER_EPD2DXL0_PF4_Y35NY_DPG": ("d", "ulsd_spot_nyh"),        # NY Harbor ULSD spot
    "EER_EPD2DXL0_PF4_RGC_DPG": ("d", "ulsd_spot_gulf"),         # Gulf Coast ULSD spot
    "EER_EPD2DC_PF4_Y05LA_DPG": ("d", "ulsd_spot_la_carb"),      # LA CARB ULSD spot
    "EER_EPMRU_PF4_Y35NY_DPG": ("d", "gasoline_spot_nyh"),       # NY Harbor conventional gasoline
    "EER_EPMRU_PF4_RGC_DPG": ("d", "gasoline_spot_gulf"),        # Gulf Coast conventional gasoline
    "RBRTE": ("d", "brent_spot"),
    "RWTC": ("d", "wti_spot"),
    "EMD_EPD2D_PTE_NUS_DPG": ("w", "retail_diesel_us"),          # EIA weekly on-highway diesel (Mondays)
    "EMD_EPD2D_PTE_R10_DPG": ("w", "retail_diesel_padd1"),
    "EMD_EPD2D_PTE_R20_DPG": ("w", "retail_diesel_padd2"),
    "EMD_EPD2D_PTE_R30_DPG": ("w", "retail_diesel_padd3"),
    "EMD_EPD2D_PTE_R40_DPG": ("w", "retail_diesel_padd4"),
    "EMD_EPD2D_PTE_R50_DPG": ("w", "retail_diesel_padd5"),
    "EMM_EPMR_PTE_NUS_DPG": ("w", "retail_regular_us"),
    "WDISTUS1": ("w", "distillate_stocks_us_kbbl"),              # weekly distillate inventories
    # ---- added 2026-11-26 (Chat 6): sub-components of the pump price, free stand-ins for OPIS-style inputs ----
    # wholesale hubs (daily)
    "EER_EPMRR_PF4_Y05LA_DPG": ("d", "gasoline_spot_la_rbob"),
    "EER_EPD2F_PF4_Y35NY_DPG": ("d", "heating_oil_spot_nyh"),
    "EER_EPJK_PF4_RGC_DPG": ("d", "jet_spot_gulf"),
    # pump prices by region (weekly): diesel sub-regions
    "EMD_EPD2D_PTE_R1X_DPG": ("w", "retail_diesel_new_england"),
    "EMD_EPD2D_PTE_R1Y_DPG": ("w", "retail_diesel_central_atlantic"),
    "EMD_EPD2D_PTE_R1Z_DPG": ("w", "retail_diesel_lower_atlantic"),
    "EMD_EPD2D_PTE_R5XCA_DPG": ("w", "retail_diesel_west_coast_ex_ca"),
    "EMD_EPD2D_PTE_SCA_DPG": ("w", "retail_diesel_california"),
    # pump prices by region (weekly): regular gasoline
    "EMM_EPMR_PTE_R10_DPG": ("w", "retail_regular_padd1"),
    "EMM_EPMR_PTE_R20_DPG": ("w", "retail_regular_padd2"),
    "EMM_EPMR_PTE_R30_DPG": ("w", "retail_regular_padd3"),
    "EMM_EPMR_PTE_R40_DPG": ("w", "retail_regular_padd4"),
    "EMM_EPMR_PTE_R50_DPG": ("w", "retail_regular_padd5"),
    "EMM_EPMR_PTE_R1X_DPG": ("w", "retail_regular_new_england"),
    "EMM_EPMR_PTE_R1Y_DPG": ("w", "retail_regular_central_atlantic"),
    "EMM_EPMR_PTE_R1Z_DPG": ("w", "retail_regular_lower_atlantic"),
    "EMM_EPMR_PTE_R5XCA_DPG": ("w", "retail_regular_west_coast_ex_ca"),
    "EMM_EPMR_PTE_SCA_DPG": ("w", "retail_regular_california"),
    "EMM_EPMR_PTE_STX_DPG": ("w", "retail_regular_texas"),
    "EMM_EPMR_PTE_SFL_DPG": ("w", "retail_regular_florida"),
    "EMM_EPMR_PTE_SNY_DPG": ("w", "retail_regular_new_york"),
    "EMM_EPMR_PTE_SOH_DPG": ("w", "retail_regular_ohio"),
    "EMM_EPMR_PTE_SMN_DPG": ("w", "retail_regular_minnesota"),
    "EMM_EPMR_PTE_SCO_DPG": ("w", "retail_regular_colorado"),
    "EMM_EPMR_PTE_SWA_DPG": ("w", "retail_regular_washington"),
    "EMM_EPMR_PTE_SMA_DPG": ("w", "retail_regular_massachusetts"),
    "EMM_EPMM_PTE_NUS_DPG": ("w", "retail_midgrade_us"),
    "EMM_EPMP_PTE_NUS_DPG": ("w", "retail_premium_us"),
    "EMM_EPM0_PTE_NUS_DPG": ("w", "retail_allgrades_us"),
    # storage (weekly)
    "WDISTP11": ("w", "distillate_stocks_padd1_kbbl"),
    "WDISTP21": ("w", "distillate_stocks_padd2_kbbl"),
    "WDISTP31": ("w", "distillate_stocks_padd3_kbbl"),
    "WDISTP41": ("w", "distillate_stocks_padd4_kbbl"),
    "WDISTP51": ("w", "distillate_stocks_padd5_kbbl"),
    "WGTSTUS1": ("w", "gasoline_stocks_us_kbbl"),
    "WGTSTP11": ("w", "gasoline_stocks_padd1_kbbl"),
    "WGTSTP21": ("w", "gasoline_stocks_padd2_kbbl"),
    "WGTSTP31": ("w", "gasoline_stocks_padd3_kbbl"),
    "WGTSTP41": ("w", "gasoline_stocks_padd4_kbbl"),
    "WGTSTP51": ("w", "gasoline_stocks_padd5_kbbl"),
    "WCESTUS1": ("w", "crude_stocks_us_kbbl"),
    # refining + demand + trade (weekly)  -> names start with weekly_ so the warehouse's eia_weekly view picks them up
    "WPULEUS3": ("w", "weekly_refinery_utilization_pct"),
    "WCRRIUS2": ("w", "weekly_refinery_crude_input_kbd"),
    "WDIRPUS2": ("w", "weekly_distillate_production_kbd"),
    "WGFRPUS2": ("w", "weekly_gasoline_production_kbd"),
    "WDIUPUS2": ("w", "weekly_distillate_demand_kbd"),
    "WGFUPUS2": ("w", "weekly_gasoline_demand_kbd"),
    "WDIIMUS2": ("w", "weekly_distillate_imports_kbd"),
    "WDIEXUS2": ("w", "weekly_distillate_exports_kbd"),
    "WGTIMUS2": ("w", "weekly_gasoline_imports_kbd"),
    # refiner resale price = closest free stand-in for the rack price (monthly)
    "EMA_EPD2D_PWG_NUS_DPG": ("m", "monthly_diesel_refiner_resale"),
    "EMA_EPMR_PWG_NUS_DPG": ("m", "monthly_regular_refiner_resale"),
}
YAHOO_DAILY = {"HO=F": "ho", "RB=F": "rbob", "BZ=F": "brent", "CL=F": "wti", "NG=F": "natgas"}
YAHOO = ["HO=F", "BZ=F", "RB=F", "CL=F", "NG=F"]
YAHOO_RANGES = [("60m", "730d"), ("5m", "60d"), ("1m", "7d")]


def fetch(url, timeout=60, tries=3, binary=False):
    err = ""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                b = r.read()
                return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code in (403, 404):
                break
            time.sleep(20 * (i + 1) if e.code == 429 else 3)
        except Exception as e:  # noqa
            err = str(e)
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{err} :: {url[:100]}")


def write_rows(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ---------------- EIA ----------------

def pull_eia():
    import xlrd  # pip install xlrd
    ok = fails = 0
    for sid, (freq, name) in EIA.items():
        if fails >= 3 and ok == 0:
            print("eia: 3 failures in a row and no success -> site looks blocked from here, skipping the rest")
            break
        try:
            book = xlrd.open_workbook(file_contents=fetch(f"https://www.eia.gov/dnav/pet/hist_xls/{sid}{freq}.xls",
                                                          binary=True, timeout=25, tries=2))
            sh = book.sheet_by_name("Data 1")
            rows = []
            for r in range(3, sh.nrows):
                d, v = sh.cell_value(r, 0), sh.cell_value(r, 1)
                if d == "" or v in ("", None):
                    continue
                dt = xlrd.xldate_as_datetime(d, book.datemode).date().isoformat()
                rows.append([dt, v])
            write_rows(OUT / f"eia_{name}.csv", ["date", "value"], rows)
            print(f"eia {name}: {len(rows)} rows {rows[0][0] if rows else ''} -> {rows[-1][0] if rows else ''}", flush=True)
            ok += 1
        except Exception as e:  # noqa
            fails += 1
            print(f"eia {name}: FAILED {e}", flush=True)
        time.sleep(1)
    print(f"eia: {ok}/{len(EIA)} series")


# ---------------- Yahoo intraday ----------------

def pull_yahoo():
    """Bars are saved per symbol/interval/MONTH (yahoo_HO_5m_2026-11.csv) so no file outgrows GitHub's limits."""
    yfails = 0
    for sym in YAHOO:
        for interval, rng in YAHOO_RANGES:
            s = sym.replace("=F", "")
            try:
                body, last = None, None
                for host in ("query1", "query2"):
                    try:
                        body = json.loads(fetch(f"https://{host}.finance.yahoo.com/v8/finance/chart/{sym}?interval={interval}&range={rng}",
                                                tries=1, timeout=20))
                        break
                    except Exception as e:  # noqa
                        last = e
                        time.sleep(15)
                if body is None:
                    raise last
                res = body["chart"]["result"][0]
                q = res["indicators"]["quote"][0]
                by_month = {}
                for i, ts in enumerate(res.get("timestamp") or []):
                    c = q["close"][i]
                    if c is None:
                        continue
                    k = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    by_month.setdefault(k[:7], {})[k] = [k, q["open"][i], q["high"][i], q["low"][i], c, q["volume"][i]]
                total = 0
                for month, new in by_month.items():
                    path = OUT / f"yahoo_{s}_{interval}_{month}.csv"
                    have = {r[0]: r for r in csv.reader(path.open())} if path.exists() else {}
                    have.pop("ts_utc", None)
                    have.update(new)                      # merge: history keeps growing past Yahoo's window
                    write_rows(path, ["ts_utc", "open", "high", "low", "close", "volume"], [have[k] for k in sorted(have)])
                    total += len(new)
                print(f"yahoo {sym} {interval}: {total} bars across {len(by_month)} month file(s)", flush=True)
                yfails = 0
            except Exception as e:  # noqa
                print(f"yahoo {sym} {interval}: FAILED {str(e)[:120]}", flush=True)
                yfails += 1
                if yfails >= 4:
                    print("yahoo: 4 failures in a row -> blocked from here right now, skipping the rest")
                    return
            time.sleep(12)


# ---------------- Yahoo daily, full history ----------------

def pull_daily():
    """Front-month futures, one daily bar per day as far back as Yahoo has -> fut_<name>_1d.csv (fills the RBOB gap
    after EIA stopped publishing NYMEX settlements in April 2024)."""
    for sym, name in YAHOO_DAILY.items():
        try:
            body = None
            for host in ("query1", "query2"):
                try:
                    body = json.loads(fetch(f"https://{host}.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=max", tries=2, timeout=30))
                    break
                except Exception as e:  # noqa
                    last = e
                    time.sleep(10)
            if body is None:
                raise last
            res = body["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            rows = []
            for i, ts in enumerate(res.get("timestamp") or []):
                if q["close"][i] is None:
                    continue
                d = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date().isoformat()
                rows.append([d, q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]])
            write_rows(OUT / f"fut_{name}_1d.csv", ["date", "open", "high", "low", "close", "volume"], rows)
            print(f"daily {sym}: {len(rows)} rows {rows[0][0] if rows else ''} -> {rows[-1][0] if rows else ''}", flush=True)
        except Exception as e:  # noqa
            print(f"daily {sym}: FAILED {str(e)[:120]}", flush=True)
        time.sleep(8)


# ---------------- Wayback: AAA national ----------------

WB_COLS = ["snapshot_ts", "price_as_of", "row", "regular", "mid", "premium", "diesel"]


def parse_national(html):
    asof = re.search(r"Price as of\s*([0-9/]+)", html)
    out = []
    for tb in re.findall(r"<table[^>]*>(.*?)</table>", html, re.S | re.I):
        if "Current Avg" not in tb:
            continue
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S | re.I):
            cells = [re.sub(r"<[^>]+>|\s+", " ", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
            if len(cells) >= 5 and "Avg" in cells[0]:
                nums = [c.replace("$", "").strip() for c in cells[1:5]]
                out.append([cells[0].replace(" Avg.", "").replace(" Avg", "")] + nums)
        break                                     # first table = national
    return (asof.group(1) if asof else None), out


def pull_wayback(since, max_minutes):
    path = OUT / "aaa_national_wayback.csv"
    done = set()
    if path.exists():
        done = {r["snapshot_ts"] for r in csv.DictReader(path.open())}
    else:
        write_rows(path, WB_COLS, [])
    t_end = time.time() + max_minutes * 60
    cdx = fetch("https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com/&output=json&fl=timestamp,statuscode"
                f"&filter=statuscode:200&collapse=timestamp:8&from={since}", timeout=120)
    snaps = [r[0] for r in json.loads(cdx)[1:]]
    todo = [s for s in snaps if s not in done]
    print(f"wayback national: {len(snaps)} daily snapshots since {since}, {len(done)} saved, {len(todo)} to go")
    n = bad = 0
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        for s in reversed(todo):                  # newest first: most useful days land first
            if time.time() > t_end:
                break
            try:
                asof, rows = parse_national(fetch(f"https://web.archive.org/web/{s}id_/https://gasprices.aaa.com/", timeout=45, tries=2))
                for r in rows:
                    w.writerow([s, asof] + r)
                if not rows:
                    w.writerow([s, asof, "NO_TABLE", "", "", "", ""])   # remember it, don't retry forever
                    bad += 1
                n += 1
                if n % 50 == 0:
                    f.flush()
                    print(f"  ... {n} snapshots read (latest {s})", flush=True)
            except Exception as e:  # noqa
                bad += 1
                if "429" in str(e):
                    time.sleep(60)
            time.sleep(1.5)
    print(f"wayback national: read {n} snapshots this run ({bad} without a table/failed); "
          f"{len(todo) - n} left for the next run")


if __name__ == "__main__":
    args = sys.argv[1:]
    since = args[args.index("--since") + 1] if "--since" in args else "2019"
    maxm = int(args[args.index("--max-minutes") + 1]) if "--max-minutes" in args else 200
    parts = [a for a in args if a in ("eia", "daily", "yahoo", "wayback")] or ["eia", "daily", "yahoo", "wayback"]
    OUT.mkdir(parents=True, exist_ok=True)
    for p in parts:
        try:
            {"eia": pull_eia, "daily": pull_daily, "yahoo": pull_yahoo, "wayback": lambda: pull_wayback(since, maxm)}[p]()
        except Exception as e:  # noqa
            print(f"{p}: FAILED {e}")
