"""Pull the fuel slice out of Jon Becker's public Kalshi data set.

Source: github.com/Jon-Becker/prediction-market-analysis (MIT). One 36 GiB archive,
https://s3.jbecker.dev/data.tar.zst (zstd tar of Parquet: data/kalshi/{markets,trades}/, data/polymarket/...).
Every Kalshi market + every trade, Jun 2021 - Nov 2025. No order book.

The archive is far bigger than a GitHub runner's disk, so we never store it: we stream it,
open each Kalshi Parquet file one at a time, keep only the fuel rows, and throw the file away.

Kept (series = event_ticker before the first '-'):
  fuel = ^(KX)?(AAAGAS|GAS|DIESEL)   -> AAA gas daily/weekly/monthly/yearly + state gas, old GAS/GASD, diesel.
  (NATGAS and CPIGAS are not kept: different underlyings.)

Writes data/lake/becker/:
  fuel_markets.csv.gz     every fuel market (all columns from Becker's schema)
  fuel_trades.csv.gz      every trade on those markets (trade_id, ticker, count, yes_price, no_price, taker_side, created_time)
                          split into fuel_trades_<series>.csv.gz if one file would pass 90 MB
  kalshi_series_summary.csv  ALL Kalshi series: markets, volume, first/last close -> the all-Kalshi baseline
  MANIFEST.json           what ran, bytes read, row counts, date ranges per series

Run:  curl -sL https://s3.jbecker.dev/data.tar.zst | python3 tools/becker_pull.py
      (or: python3 tools/becker_pull.py path/to/data.tar.zst)
"""
import io, json, os, re, sys, tarfile, tempfile, time
from collections import defaultdict

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import zstandard

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "lake", "becker")
FUEL = r"^(KX)?(AAAGAS|GAS|DIESEL)"
FUEL_RE = re.compile(FUEL)
MAX_BYTES = 90 * 1024 * 1024


def series_of(arr):
    return pc.list_element(pc.split_pattern(arr, "-", max_splits=1), 0)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    src = open(sys.argv[1], "rb") if len(sys.argv) > 1 else sys.stdin.buffer
    reader = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(src, read_size=1 << 20)
    tar = tarfile.open(fileobj=reader, mode="r|")

    markets, trades = [], []
    summary = defaultdict(lambda: {"markets": 0, "volume": 0, "first_close": None, "last_close": None})
    stats = {"files_seen": 0, "kalshi_market_files": 0, "kalshi_trade_files": 0,
             "kalshi_trade_rows_scanned": 0, "kalshi_market_rows_scanned": 0, "bytes_kalshi": 0}

    for m in tar:
        stats["files_seen"] += 1
        name = m.name
        if not (m.isfile() and "kalshi/" in name and name.endswith(".parquet")):
            continue
        kind = "markets" if "/markets/" in name else "trades" if "/trades/" in name else None
        if kind is None:
            continue
        stats["bytes_kalshi"] += m.size
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=True) as tmp:
            f = tar.extractfile(m)
            while True:
                chunk = f.read(1 << 22)
                if not chunk:
                    break
                tmp.write(chunk)
            tmp.flush()
            try:
                pf = pq.ParquetFile(tmp.name)
            except Exception as e:
                print(f"skip {name}: {e}", flush=True)
                continue
            for i in range(pf.num_row_groups):
                tb = pf.read_row_group(i)
                if kind == "markets":
                    stats["kalshi_market_rows_scanned"] += tb.num_rows
                    ser = series_of(tb["event_ticker"])
                    # all-Kalshi summary
                    for s, v, c in zip(ser.to_pylist(), tb["volume"].to_pylist(),
                                       tb["close_time"].cast(pa.string()).to_pylist()):
                        d = summary[s]
                        d["markets"] += 1
                        d["volume"] += v or 0
                        if c:
                            c = c[:10]
                            d["first_close"] = c if d["first_close"] is None else min(d["first_close"], c)
                            d["last_close"] = c if d["last_close"] is None else max(d["last_close"], c)
                    keep = pc.match_substring_regex(ser, FUEL)
                    if pc.any(keep).as_py():
                        markets.append(tb.filter(keep))
                else:
                    stats["kalshi_trade_rows_scanned"] += tb.num_rows
                    keep = pc.match_substring_regex(tb["ticker"], FUEL)
                    if pc.any(keep).as_py():
                        trades.append(tb.filter(keep))
        stats[f"kalshi_{'market' if kind == 'markets' else 'trade'}_files"] += 1
        if stats["kalshi_trade_files"] % 50 == 1 or kind == "markets":
            print(f"{time.time()-t0:7.0f}s {name} | trades kept {sum(t.num_rows for t in trades):,}", flush=True)

    if not markets and not trades:
        sys.exit("No Kalshi fuel rows found: archive layout changed? Nothing written.")

    mk = pa.concat_tables(markets, promote_options="permissive") if markets else None
    tr = pa.concat_tables(trades, promote_options="permissive") if trades else None

    import pyarrow.csv as pcsv, gzip

    def write_csv(table, path):
        buf = io.BytesIO()
        pcsv.write_csv(table, buf)
        with gzip.open(path, "wb", compresslevel=9) as g:
            g.write(buf.getvalue())
        return os.path.getsize(path)

    files = {}
    if mk is not None:
        mk = mk.sort_by([("event_ticker", "ascending"), ("ticker", "ascending")])
        files["fuel_markets.csv.gz"] = write_csv(mk, os.path.join(OUT, "fuel_markets.csv.gz"))

    per_series = {}
    if tr is not None:
        tr = tr.append_column("series", series_of(tr["ticker"]))
        tr = tr.sort_by([("series", "ascending"), ("created_time", "ascending")])
        path = os.path.join(OUT, "fuel_trades.csv.gz")
        size = write_csv(tr, path)
        if size > MAX_BYTES:  # GitHub blocks files over 100 MB: split by series
            os.remove(path)
            for s in pc.unique(tr["series"]).to_pylist():
                part = tr.filter(pc.equal(tr["series"], s))
                fn = f"fuel_trades_{s}.csv.gz"
                files[fn] = write_csv(part, os.path.join(OUT, fn))
        else:
            files["fuel_trades.csv.gz"] = size
        ct = tr["created_time"].cast(pa.string())
        for s in pc.unique(tr["series"]).to_pylist():
            mask = pc.equal(tr["series"], s)
            c = pc.filter(ct, mask)
            per_series[s] = {"trades": int(pc.sum(mask.cast(pa.int64())).as_py()),
                             "contracts": int(pc.sum(pc.filter(tr["count"], mask)).as_py() or 0),
                             "first": pc.min(c).as_py()[:10], "last": pc.max(c).as_py()[:10]}

    with open(os.path.join(OUT, "kalshi_series_summary.csv"), "w") as f:
        f.write("series,markets,volume,first_close,last_close,fuel\n")
        for s, d in sorted(summary.items(), key=lambda kv: -kv[1]["volume"]):
            f.write(f"{s},{d['markets']},{d['volume']},{d['first_close'] or ''},{d['last_close'] or ''},"
                    f"{1 if FUEL_RE.match(s or '') else 0}\n")

    manifest = {
        "source": "https://s3.jbecker.dev/data.tar.zst (github.com/Jon-Becker/prediction-market-analysis, MIT)",
        "pulled_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "filter": FUEL, "seconds": round(time.time() - t0),
        "fuel_markets": 0 if mk is None else mk.num_rows,
        "fuel_trades": 0 if tr is None else tr.num_rows,
        "kalshi_series_total": len(summary), "files_written_bytes": files,
        "trades_by_series": per_series, **stats,
    }
    with open(os.path.join(OUT, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
