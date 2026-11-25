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


def post_json(url, body, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={**UA, "Content-Type": "application/json;charset=utf-8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


BODY_VARIANTS = [   # request shapes to try for /api/search_stores (page JS POSTs JSON; exact keys unknown)
    lambda la, lo: {"latitude": la, "longitude": lo, "radius": 300},
    lambda la, lo: {"latitude": la, "longitude": lo, "radiusInMiles": 300},
    lambda la, lo: {"lat": la, "lng": lo, "radius": 300},
    lambda la, lo: {"Latitude": la, "Longitude": lo, "Radius": 300},
    lambda la, lo: {"latitude": la, "longitude": lo},
]


def loves():
    """fetch_stores = every store (no prices). search_stores (POST, near a point) = stores WITH fuelPrices.
    We search near one store per ~150-mile grid cell so every store is covered, de-duplicated by store number."""
    stores = get_json("https://www.loves.com/api/fetch_stores").get("stores", [])
    cells = {}
    for st in stores:
        try:
            la, lo = float(st["latitude"]), float(st["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        cells.setdefault((round(la / 2), round(lo / 2.5)), (la, lo))
    url = "https://www.loves.com/api/search_stores"
    variant, seen, rows, tried = None, {}, [], []
    for la, lo in cells.values():
        for v in ([variant] if variant else BODY_VARIANTS):
            try:
                res = post_json(url, v(la, lo))
            except Exception as e:  # noqa
                tried.append(str(e)[:80])
                continue
            got = res.get("stores", res if isinstance(res, list) else [])
            if got and any((g.get("fuelPrices") or (g.get("site") or {}).get("fuelPrices")) for g in got):
                variant = v
                for g in got:
                    seen[first(g, "number", "storeNumber", "siteId", "id")] = g
                break
        time.sleep(0.5)
    OUT.mkdir(parents=True, exist_ok=True)
    sample = next(iter(seen.values()), None)
    (OUT / "_schema_loves.json").write_text(json.dumps(
        {"all_stores": len(stores), "grid_cells": len(cells), "stores_with_prices": len(seen),
         "body_used": variant(0, 0) if variant else None, "errors_sample": tried[:5],
         "store_keys": sorted(sample.keys()) if sample else None,
         "fuel_sample": (sample.get("fuelPrices") or (sample.get("site") or {}).get("fuelPrices")) if sample else None},
        indent=1)[:20000])
    for num_, g in seen.items():
        fp = g.get("fuelPrices") or (g.get("site") or {}).get("fuelPrices") or []
        for f in fp:
            price = first(f, "cashPrice", "creditPrice", "price")
            if price in (None, "", 0):
                continue
            rows.append(["loves", num_, first(g, "state", "stateCode"), first(g, "city"), first(g, "latitude"),
                         first(g, "longitude"), f"{first(f, 'fuelType') or ''}|{first(f, 'productName', 'displayName') or ''}",
                         price, first(f, "lastPriceChangeDateTime", "lastCheckInDateTime")])
    return rows, len(seen)


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
