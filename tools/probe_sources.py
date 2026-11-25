#!/usr/bin/env python3
"""One-shot discovery probe (runs on GitHub; this sandbox can't reach these sites).

1. Truckstops: open Love's / Pilot / TA fuel pages, download their JS bundles, list every API-looking URL and
   any fuel-price JSON endpoints that answer. Also tries known candidate endpoints directly.
2. Wayback (for L2 history): count archived snapshots of gasprices.aaa.com/?state=XX per state since 2023, and parse
   a sample so we know if old state tables can be read.
Output: research/engine_room/probe_<utc>.json (committed by the workflow).
"""
import datetime, json, pathlib, re, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "engine_room"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
STATES = "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()


def get(url, timeout=25, headers=None):
    try:
        req = urllib.request.Request(url, headers={**UA, **(headers or {})})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b"").decode("utf-8", "replace")[:400], {}
    except Exception as e:  # noqa
        return None, str(e)[:300], {}


PAGES = {
    "loves": "https://www.loves.com/en/location-and-fuel-price-search",
    "pilot": "https://www.pilotflyingj.com/fuel-prices",
    "ta": "https://www.ta-petro.com/location/all-locations",
}
CANDIDATES = [
    "https://www.loves.com/api/sitecore/StoreSearch/SearchStoresWithDetail?pageNumber=0&top=5&lat=35.4676&lng=-97.5164",
    "https://www.loves.com/api/fetch_stores",
    "https://apiservices.loves.com/api/stores/search?latitude=35.4676&longitude=-97.5164&radius=100",
    "https://apiservices.loves.com/locations",
    "https://www.pilotflyingj.com/api/fuel-prices",
    "https://www.pilotflyingj.com/fuel-prices.json",
    "https://locations.pilotflyingj.com/api/getAsyncLocations",
    "https://www.ta-petro.com/api/locations",
]


def truckstops():
    res = {}
    for name, url in PAGES.items():
        st, html, hdr = get(url)
        scripts = sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', html or "")))[:60]
        apis = set(re.findall(r'https?://[A-Za-z0-9.-]*(?:api|services|graphql|contentstack|algolia)[A-Za-z0-9./_?=&%-]*', html or ""))
        paths = set(re.findall(r'["\'](/api/[A-Za-z0-9/_.?=&-]+)["\']', html or ""))
        bundle_hits = {}
        for s in scripts:
            u = urllib.parse.urljoin(url, s)
            if not any(k in u for k in ("_next", "static", "chunk", "main", "app", "bundle", ".js")):
                continue
            bst, js, _ = get(u, timeout=20)
            if bst != 200 or not js:
                continue
            hits = set(re.findall(r'https?://[A-Za-z0-9.-]*(?:api|services|graphql|contentstack)[A-Za-z0-9./_?=&%{}$-]*', js))
            hits |= set(re.findall(r'["\'`](/api/[A-Za-z0-9/_.?=&{}$-]+)["\'`]', js))
            fuel = set(re.findall(r'["\'`]([^"\'`]{0,80}(?:[Ff]uel[Pp]rice|fuelprice|fuel_price|dieselPrice|DieselPrice)[^"\'`]{0,80})["\'`]', js))
            if hits or fuel:
                bundle_hits[u[-90:]] = {"api": sorted(hits)[:40], "fuel_strings": sorted(fuel)[:15]}
            time.sleep(0.3)
        res[name] = {"status": st, "len": len(html or ""), "scripts": len(scripts), "page_apis": sorted(apis)[:40],
                     "page_api_paths": sorted(paths)[:40], "bundles": bundle_hits,
                     "next_data": bool(re.search(r'__NEXT_DATA__', html or "")),
                     "diesel_in_html": re.findall(r"[Dd]iesel[^$<]{0,60}\$\s?([0-9]\.[0-9]{2,3})", html or "")[:10]}
    cand = {}
    for u in CANDIDATES:
        st, body, hdr = get(u, timeout=20, headers={"Accept": "application/json"})
        cand[u] = {"status": st, "type": hdr.get("Content-Type", ""), "len": len(body or ""), "head": (body or "")[:300]}
    res["candidates"] = cand
    return res


def wayback():
    out = {"per_state_2026": {}, "per_state_since_2023": {}}
    for s in STATES:
        q = ("https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com/%3Fstate%3D" + s +
             "&output=json&fl=timestamp,statuscode&filter=statuscode:200&from=2023&collapse=timestamp:8")
        st, body, _ = get(q, timeout=40)
        try:
            rows = json.loads(body)[1:]
        except Exception:  # noqa
            rows = []
        days = sorted({r[0][:8] for r in rows})
        out["per_state_since_2023"][s] = len(days)
        out["per_state_2026"][s] = len([d for d in days if d.startswith("2026")])
        if s == "TX":
            out["tx_days_sample"] = days[-25:]
        time.sleep(1)
    # common days: dates where >= 45 states have a snapshot
    return out


def loves_deep():
    """Find how the Love's page asks for prices: grep their JS for search_stores / fuelPrices and try it."""
    st, html, _ = get(PAGES["loves"])
    out = {"snippets": [], "tries": {}}
    for src in sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', html or ""))):
        u = urllib.parse.urljoin(PAGES["loves"], src)
        bst, js, _ = get(u, timeout=20)
        if bst != 200 or not js:
            continue
        for key in ("search_stores", "fuelPrices", "fetch_stores", "FuelPrice"):
            for m in re.finditer(key, js):
                out["snippets"].append({"file": u[-40:], "key": key, "ctx": js[max(0, m.start() - 400): m.start() + 400]})
                if len([x for x in out["snippets"] if x["key"] == key]) > 4:
                    break
    for u, body in (("https://www.loves.com/api/search_stores", None),
                    ("https://www.loves.com/api/search_stores?StoreNumbers=5", None),
                    ("https://www.loves.com/api/search_stores?storeNumbers=5,10", None)):
        try:
            req = urllib.request.Request(u, headers={**UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as r:
                out["tries"][u] = {"status": r.status, "head": r.read().decode("utf-8", "replace")[:600]}
        except urllib.error.HTTPError as e:
            out["tries"][u] = {"status": e.code, "head": (e.read() or b"").decode("utf-8", "replace")[:300]}
        except Exception as e:  # noqa
            out["tries"][u] = {"error": str(e)[:200]}
    return out


def deep(name, page, extra_urls=()):
    """Generic deep look: every script (incl. modules / inline), API-looking strings near 'fuel' / 'price'."""
    st, html, _ = get(page)
    out = {"status": st, "len": len(html or ""), "script_srcs": [], "inline_json_keys": [], "hits": [], "tries": {}}
    srcs = sorted(set(re.findall(r'<script[^>]*\bsrc=["\']([^"\']+)', html or "")))
    srcs += sorted(set(re.findall(r'<link[^>]+rel=["\']modulepreload["\'][^>]+href=["\']([^"\']+)', html or "")))
    out["script_srcs"] = srcs[:60]
    for m in re.finditer(r'(window\.__[A-Z_]+__|__NUXT__|__INITIAL_STATE__|"fuelPrices"|dieselPrice|fuel_price)', html or ""):
        out["inline_json_keys"].append((html or "")[max(0, m.start() - 200): m.start() + 300])
        if len(out["inline_json_keys"]) > 5:
            break
    for src in srcs:
        u = urllib.parse.urljoin(page, src)
        bst, js, _ = get(u, timeout=25)
        if bst != 200 or not js:
            continue
        for m in re.finditer(r'(?i)(fuel ?prices?|diesel|/api/[a-z0-9/_-]*(?:fuel|price|location|store)[a-z0-9/_?=&{}$-]*)', js):
            ctx = js[max(0, m.start() - 250): m.start() + 250]
            if "http" in ctx or "/api" in ctx or "fetch(" in ctx or "graphql" in ctx:
                out["hits"].append({"file": u[-60:], "ctx": ctx})
            if len(out["hits"]) > 25:
                break
    for u in extra_urls:
        sst, body, hdr = get(u, timeout=25, headers={"Accept": "application/json"})
        out["tries"][u] = {"status": sst, "type": hdr.get("Content-Type", ""), "len": len(body or ""), "head": (body or "")[:500], "prices": re.findall(r"\$\s?([0-9]\.[0-9]{2,3})", body or "")[:20],
                          "diesel_ctx": [body[max(0, m.start()-150): m.start()+150] for m in re.finditer(r"(?i)diesel", body or "")][:4]}
    return out


def main():
    if "--deep" in sys.argv:
        t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%MZ")
        res = {
            "pilot": deep("pilot", "https://www.pilotflyingj.com/fuel-prices", [
                "https://www.pilotflyingj.com/api/locations", "https://www.pilotflyingj.com/api/stores",
                "https://www.pilotflyingj.com/fuel-prices/__data.json",
                "https://www.pilotflyingj.com/fuel-prices/__data.json?x-sveltekit-invalidated=01",
                "https://locations.pilotflyingj.com/__data.json"]),
            "ta": deep("ta", "https://www.ta-petro.com/location/all-locations", [
                "https://www.ta-petro.com/api/locations/coordinates/?",
                "https://www.ta-petro.com/api/locations/coordinates/?lat=36.16&lon=-86.78",
                "https://www.ta-petro.com/api/locations/coordinates/?lat=41.5&lon=-87.9",
                "https://www.ta-petro.com/location/tn/nashville"]),
            
        }
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"probe_deep_{t0}.json").write_text(json.dumps(res, indent=1))
        for k, v in res.items():
            print("=====", k, v["status"], v["len"], "scripts", len(v["script_srcs"]))
            print(" srcs:", v["script_srcs"][:12])
            for x in v["inline_json_keys"][:3]: print(" inline:", x[:400].replace("\n", " "))
            for h in v["hits"][:10]: print(" hit", h["file"], "::", h["ctx"][:400].replace("\n", " "))
            for u, t in v["tries"].items(): print(" try", t["status"], t["type"][:25], t["len"], u, "| prices", t["prices"][:10]); [print("   diesel:", c.replace("\n", " ")[:300]) for c in t["diesel_ctx"][:3]]
        return
    if "--loves" in sys.argv:
        t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%MZ")
        res = loves_deep()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"probe_loves_{t0}.json").write_text(json.dumps(res, indent=1))
        print(json.dumps(res["tries"], indent=1)[:3000])
        for sn in res["snippets"][:12]:
            print("----", sn["key"], sn["file"]); print(sn["ctx"][:800])
        return
    t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%MZ")
    res = {"run_utc": t0, "truckstops": truckstops(), "wayback": wayback()}
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"probe_{t0}.json"
    p.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: (v if k != "truckstops" else {n: {kk: vv for kk, vv in d.items() if kk in ("status", "len", "diesel_in_html")}
                                                     for n, d in v.items() if n != "candidates"}) for k, v in res.items()}, indent=1)[:4000])
    print(json.dumps(res["truckstops"]["candidates"], indent=1)[:3000])


if __name__ == "__main__":
    main()
