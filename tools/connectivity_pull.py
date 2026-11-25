"""Connectivity test, tier 2 (one-shot). Runs on GitHub (the runner can reach Yahoo/AAA; Claude's sandbox can't).

Pulls:
  1. Yahoo HO=F / BZ=F 5-minute bars for the control day (Mon 2026-11-23) -> 10:00 AM ET price.
  2. AAA state diesel tables for all 50 states + DC (current / yesterday / week / month / year ago).
  3. Truckstop probes: can we see a posted diesel price on Pilot / Love's / TA pages?
Writes research/connectivity/tier2_pull.json (raw, for Claude to read and put in the sheet).
"""
import json, re, time, datetime, urllib.request, os

OUT = "research/connectivity/tier2_pull.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
ET = datetime.timezone(datetime.timedelta(hours=-5))


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa
            err = str(e)
            time.sleep(2 * (i + 1))
    return None, err


def yahoo_5m(sym):
    p1 = int(datetime.datetime(2026, 11, 20, 0, 0, tzinfo=ET).timestamp())
    p2 = int(datetime.datetime(2026, 11, 24, 0, 0, tzinfo=ET).timestamp())
    st, body = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=5m&period1={p1}&period2={p2}")
    if st != 200:
        return {"status": st, "error": body[:300]}
    res = json.loads(body)["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    bars = []
    for ts, o, c in zip(res.get("timestamp", []), q["open"], q["close"]):
        t = datetime.datetime.fromtimestamp(ts, ET)
        bars.append([t.strftime("%Y-%m-%d %H:%M"), o, c])
    keep = [b for b in bars if b[0].startswith("2026-11-23") and ("09:30" <= b[0][11:] <= "10:30")]
    fri = [b for b in bars if b[0].startswith("2026-11-20")]
    mon = [b for b in bars if b[0].startswith("2026-11-23")]
    return {"status": 200, "n_bars": len(bars), "mon_0930_1030": keep,
            "fri_last": fri[-1] if fri else None, "mon_first": mon[0] if mon else None, "mon_last": mon[-1] if mon else None}


STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA "
          "RI SC SD TN TX UT VT VA WA WV WI WY").split()


def parse_tables(html):
    """Every table that has 'Current Avg' rows -> list of {row_label: [regular, mid, premium, diesel]}."""
    out = []
    for tb in re.findall(r"<table[^>]*>(.*?)</table>", html, re.S | re.I):
        if "Current Avg" not in tb:
            continue
        rows = {}
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S | re.I):
            cells = [re.sub(r"<[^>]+>|\s+", " ", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
            if cells and "Avg" in cells[0]:
                rows[cells[0]] = cells[1:]
        out.append(rows)
    return out


def aaa_states():
    res = {}
    for s in STATES:
        st, html = get(f"https://gasprices.aaa.com/?state={s}")
        if st != 200:
            res[s] = {"status": st, "error": html[:200]}
            continue
        m = re.search(r"Price as of\s*([0-9/]+)", html)
        res[s] = {"status": st, "as_of": m.group(1) if m else None, "tables": parse_tables(html)}
        time.sleep(1)
    return res


PROBES = {
    "loves_search": "https://www.loves.com/en/location-and-fuel-price-search",
    "pilot_fuel": "https://www.pilotflyingj.com/fuel-prices",
    "pilot_locations": "https://locations.pilotflyingj.com/us/tn/knoxville",
    "ta_locations": "https://www.ta-petro.com/location/all-locations",
    "gasbuddy_diesel": "https://www.gasbuddy.com/usa",
}


def probes():
    out = {}
    for k, u in PROBES.items():
        st, body = get(u)
        txt = body or ""
        prices = re.findall(r"[Dd]iesel[^$]{0,80}\$\s?([0-9]\.[0-9]{2,3})", txt)[:5]
        out[k] = {"url": u, "status": st, "len": len(txt), "diesel_prices_seen": prices,
                  "api_hints": sorted(set(re.findall(r"https?://[^\"' ]*api[^\"' ]*", txt)))[:10]}
    return out


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    result = {"pulled_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
              "yahoo": {s: yahoo_5m(s) for s in ("HO=F", "BZ=F")},
              "aaa_states": aaa_states(),
              "truckstop_probes": probes()}
    json.dump(result, open(OUT, "w"), indent=1)
    ok = sum(1 for v in result["aaa_states"].values() if v.get("tables"))
    print("yahoo:", {k: v.get("n_bars") for k, v in result["yahoo"].items()}, "| aaa states with tables:", ok)
