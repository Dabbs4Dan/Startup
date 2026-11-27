#!/usr/bin/env python3
"""One-off probe: what does the Internet Archive hold for live / daily pump-price sources? (2026-11-27, Chat 6)

Reads ONLY web.archive.org (never the source sites). For each candidate page: how many distinct days were saved since
2023, first / last day, saves per day, and a text sample around any price near the word "average" from 2 saved copies.
Also lists saved URLs on a few domains so we can find pages we did not think of.
Out: research/engine_room/archive_probe.csv, archive_probe_urls.csv
"""
import csv, json, pathlib, re, time, urllib.parse, urllib.request

OUT = pathlib.Path(__file__).resolve().parents[1] / "research/engine_room"
UA = {"User-Agent": "Mozilla/5.0 (kalshi-twins-research; personal research)"}
PAGES = [
    "gasbuddy.com/usa", "gasbuddy.com/", "gasbuddy.com/charts", "gasbuddy.com/gasprices", "gasbuddy.com/gaspricemap",
    "fuelinsights.gasbuddy.com/", "fuelinsights.gasbuddy.com/charts", "fuelinsights.gasbuddy.com/Home/US",
    "gasbuddy.com/gasprices/california", "gasbuddy.com/gasprices/texas",
    "twitter.com/GasBuddyGuy", "x.com/GasBuddyGuy",
    "tradingeconomics.com/united-states/gasoline-prices", "ycharts.com/indicators/us_gas_price",
    "ycharts.com/indicators/us_retail_diesel_price_aaa", "mapquest.com/gas-prices", "gasprices.aaa.com/",
    "gasprices.aaa.com/state-gas-price-averages/", "promiles.com/", "www.loves.com/api/fetch_stores",
    "www.loves.com/en/location-and-fuel-price-search", "www.ta-petro.com/location-and-fuel-prices", "pilotflyingj.com/fuel-prices",
    "www.eia.gov/petroleum/gasdiesel/", "www.cspdailynews.com/fuels", "www.opis.com/", "fuelgaugereport.aaa.com/",
    "www.gasprices.com/", "www.autoblog.com/gas-prices", "www.geico.com/save/gas-prices/", "www.truckstop.com/fuel-prices/",
    "www.dtn.com/", "www.fuelbuddy.com/", "gasprices.mapquest.com/", "www.costco.com/gasoline.html", "www.samsclub.com/fuel",
    "www.buc-ees.com/", "www.wawa.com/fuel", "www.speedway.com/", "www.circlek.com/fuel", "www.caseys.com/fuel",
    "www.kwiktrip.com/fuel", "www.sheetz.com/fuel", "www.racetrac.com/", "www.quiktrip.com/", "www.murphyusa.com/",
]
DOMAINS = {"gasbuddy.com": "(average|chart|usa|insight|trend|national|graphql|price)", "promiles.com": "(fuel|diesel|price)",
           "loves.com": "(api|fuel|price)", "ta-petro.com": "(api|fuel|price)", "pilotflyingj.com": "(api|fuel|price)",
           "pilotcompany.com": "(api|fuel|price)", "opisnet.com": "(average|retail|aaa)", "tcsfuel.com": "(price|fuel)",
           "truckersreport.com": "(fuel|diesel)", "truckmiles.com": "(fuel|diesel|price)", "fleetowner.com": "(fuel-price|diesel-price)"}


def get(url, timeout=40):
    for i in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa
            err = str(e)[:80]
            time.sleep(8 * (i + 1))
    return "ERR " + err


def cdx(params):
    body = get("https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(params))
    try:
        return json.loads(body)[1:]
    except Exception:  # noqa
        return None


def sample(ts, url):
    html = get(f"https://web.archive.org/web/{ts}id_/https://{url}", timeout=45)
    if html.startswith("ERR"):
        return html, 0
    text = re.sub(r"<script[^>]*>|</script>|<style.*?</style>|<[^>]+>", " ", html, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    hits = [m.start() for m in re.finditer(r"(?i)(national|u\.?s\.?a?\.?)\s+(average|avg)", text)] or \
           [m.start() for m in re.finditer(r"(?i)average", text)]
    for h in hits:
        seg = text[max(0, h - 60): h + 160]
        if re.search(r"\$?\d\.\d{2,3}", seg):
            return seg, len(html)
    m = re.search(r'(?i)"(national|usa?)[A-Za-z_]*(average|avg|price)[A-Za-z_]*"\s*:\s*"?\$?\d\.\d+', html)
    return (html[max(0, m.start() - 40): m.end() + 80] if m else "no price near 'average'"), len(html)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []

    def save():
        cols = sorted({k for r in rows for k in r}, key=lambda k: (k != "page", k))
        with (OUT / "archive_probe.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    for url in PAGES:
        # light lookups: one row per saved DAY since 2023, then one row per saved HOUR in 2026 (v2: v1 asked for every save and timed out)
        dd = cdx({"url": url, "output": "json", "fl": "timestamp", "from": "2023", "filter": "statuscode:200", "collapse": "timestamp:8", "limit": "2000"})
        r = {"page": url}
        if dd is None:
            r["note"] = "lookup failed"
        elif not dd:
            r["days_saved"] = 0
        else:
            days = sorted({s[0][:8] for s in dd})
            hh = cdx({"url": url, "output": "json", "fl": "timestamp", "from": "2026", "filter": "statuscode:200", "collapse": "timestamp:10", "limit": "9000"}) or []
            d26 = sum(d.startswith("2026") for d in days)
            r.update({"days_saved": len(days), "first": days[0], "last": days[-1], "days_2026": d26,
                      "days_2025": sum(d.startswith("2025") for d in days), "days_2024": sum(d.startswith("2024") for d in days),
                      "days_2023": sum(d.startswith("2023") for d in days),
                      "hours_saved_per_day_2026": round(len(hh) / max(1, d26), 1), "hours_of_day_seen_2026": len({h[0][8:10] for h in hh})})
            if len(days) >= 30:
                for k, t in (("sample_new", dd[-1][0]), ("sample_old", dd[len(dd) // 3][0])):
                    seg, size = sample(t, url)
                    r[k], r[k + "_ts"], r[k + "_bytes"] = seg[:240], t, size
                    time.sleep(2)
        rows.append(r)
        save()
        print(r, flush=True)
        time.sleep(1.5)
    urls = []
    for dom, pat in DOMAINS.items():
        got = cdx({"url": dom, "matchType": "domain", "output": "json", "fl": "original,timestamp", "from": "2024", "collapse": "urlkey",
                   "filter": ["statuscode:200", f"original:.*{pat}.*"], "limit": "400"})
        for o, t in (got or []):
            urls.append({"domain": dom, "url": o[:200], "one_save": t})
        print(dom, len(got or []), flush=True)
        time.sleep(4)
    with (OUT / "archive_probe_urls.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "url", "one_save"])
        w.writeheader()
        w.writerows(urls)


if __name__ == "__main__":
    main()
