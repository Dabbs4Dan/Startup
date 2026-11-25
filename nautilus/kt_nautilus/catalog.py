"""Write instruments + market data to a ParquetDataCatalog (Nautilus' standard on-disk format).

Rebuilt from SQLite + live CSVs on demand, so it never needs committing (gitignored).
Usage: python3 nautilus/build_catalog.py [--events KXDIESELD-26NOV24 ...] [--live]
"""
import shutil

from nautilus_trader.persistence import ParquetDataCatalog

from .common import CATALOG
from . import instruments as ins, loaders


def _by_instrument(ticks):
    groups = {}
    for t in ticks:
        groups.setdefault(str(t.instrument_id), []).append(t)
    return [sorted(g, key=lambda t: t.ts_event) for g in groups.values()]


def build(event_tickers=None, include_live=True, fresh=True):
    if fresh and CATALOG.exists():
        shutil.rmtree(CATALOG)
    CATALOG.mkdir(parents=True, exist_ok=True)
    cat = ParquetDataCatalog(str(CATALOG))
    insts, meta = ins.load_instruments(event_tickers)
    tickers = list(meta)
    counts = {"instruments": len(insts), "trades": 0, "candle_quotes": 0, "live_quotes": 0}
    if insts:
        cat.write_instruments(insts) if hasattr(cat, "write_instruments") else cat.write_data(insts)
    tr = loaders.trades(tickers)
    for group in _by_instrument(tr):              # catalog wants one instrument per write
        cat.write_trade_ticks(group, skip_disjoint_check=True)
    cq = loaders.candle_quotes(tickers, 1)
    lq = loaders.live_quotes(tickers) if include_live else []          # only strikes we have instruments for
    quotes = sorted(cq + lq, key=lambda q: q.ts_event)
    for group in _by_instrument(quotes):
        cat.write_quote_ticks(group, skip_disjoint_check=True)
    counts.update(trades=len(tr), candle_quotes=len(cq), live_quotes=len(lq))
    return cat, counts
