#!/usr/bin/env python3
"""Truckstop pump-price recorder (L3 input: what AAA/OPIS build state averages from).

Love's: https://www.loves.com/api/fetch_stores = every store in one JSON (found by tools/probe_sources.py).
TA:     https://www.ta-petro.com/api/locations/coordinates/?  (seen in their JS; tried, fail-soft)
Pilot:  no public price endpoint found yet (Contentstack CMS only).

Output (one file per ET day, append-only, raw):
  data/live/truckstops/YYYY-MM-DD.csv  ts_utc, chain, store, state, city, lat, lon, product, price, price_ts
  data/live/truckstops/_schema_<chain>.json  first-store field names (so a changed feed is easy to spot)
Usage: python3 tools/truckstops.py [--loop-minutes 330 --every 60]
"""
import argparse, csv, datetime, json, pathlib, sys, time, urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "live" / "truckstops"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Referer": "https://www.loves.com/en/location-and-fuel-price-search"}
DIESEL_WORDS = ("diesel", "dsl", "ulsd")


def get_json(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def first(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return None


def loves():
    data = get_json("https://www.loves.com/api/fetch_stores")
    stores = data.get("stores", data if isinstance(data, list) else [])
    OUT.mkdir(parents=True, exist_ok=True)
    if stores:
        s0 = stores[0]
        (OUT / "_schema_loves.json").write_text(json.dumps(
            {"n_stores": len(stores), "keys": sorted(s0.keys()),
             "fuel_sample": next((s.get("fuelPrices") for s in stores if s.get("fuelPrices")), None)}, indent=1)[:20000])
    rows = []
    for s in stores:
        fp = s.get("fuelPrices") or s.get("FuelPrices") or []
        for f in fp if isinstance(fp, list) else []:
            prod = str(first(f, "productName", "ProductName", "name", "fuelType") or "")
            price = first(f, "cashPrice", "price", "Price", "currentPrice", "retailPrice", "creditPrice")
            if price in (None, "", 0):
                continue
            rows.append(["loves", first(s, "number", "storeNumber", "id"), first(s, "state", "stateCode"),
                         first(s, "city"), first(s, "latitude"), first(s, "longitude"), prod, price,
                         first(f, "lastPriceChangeDateTime", "lastUpdated", "effectiveDate", "updatedAt", "priceDate")])
    return rows, len(stores)


def ta():
    rows = []
    try:
        data = get_json("https://www.ta-petro.com/api/locations/coordinates/?")
        locs = data if isinstance(data, list) else data.get("locations", data.get("data", []))
        if locs:
            (OUT / "_schema_ta.json").write_text(json.dumps({"n": len(locs), "keys": sorted(locs[0].keys()) if isinstance(locs[0], dict) else str(locs[0])[:300]}, indent=1))
    except Exception as e:  # noqa
        (OUT / "_schema_ta.json").write_text(json.dumps({"error": str(e)[:300]}))
    return rows


def snapshot():
    utc = datetime.datetime.now(datetime.timezone.utc)
    day = utc.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    ts = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    out, report = [], {}
    for name, fn in (("loves", loves), ("ta", ta)):
        try:
            res = fn()
            rows, n = res if isinstance(res, tuple) else (res, None)
            out += rows
            diesel = [r for r in rows if any(w in str(r[6]).lower() for w in DIESEL_WORDS)]
            report[name] = {"stores": n, "price_rows": len(rows), "diesel_rows": len(diesel)}
        except Exception as e:  # noqa
            report[name] = {"error": str(e)[:200]}
    if out:
        OUT.mkdir(parents=True, exist_ok=True)
        p = OUT / f"{day}.csv"
        new = not p.exists()
        with p.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["ts_utc", "chain", "store", "state", "city", "lat", "lon", "product", "price", "price_ts"])
            w.writerows([[ts, *r] for r in out])
    print(ts, json.dumps(report))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop-minutes", type=int, default=0)
    ap.add_argument("--every", type=int, default=60)
    a = ap.parse_args()
    end = time.time() + a.loop_minutes * 60
    while True:
        snapshot()
        if time.time() + a.every * 60 > end:
            break
        time.sleep(a.every * 60)


if __name__ == "__main__":
    main()
