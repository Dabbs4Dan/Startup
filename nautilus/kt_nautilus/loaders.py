"""Project data -> Nautilus market data.

History (SQLite):
  kalshi_trades   -> TradeTick   (every fill: yes price, contracts, taker side)
  kalshi_candles  -> QuoteTick   (candle-close yes bid/ask; period 1 = minute, 60 = hourly)
Live recorder (GitHub shifts, data/live/kalshi_markets/YYYY-MM-DD.csv, every ~5 min):
  snapshots       -> QuoteTick   (yes bid/ask per open strike)
Sizes: live CSVs from 2026-11-25 carry real top-of-book sizes (yes_bid_size / yes_ask_size) and use them;
history candles have no size, so they carry a placeholder (QUOTE_SIZE). Fills in backtests therefore assume small orders — fine for $100-scale bets, NOT for size
tests (use the live order-book CSVs for those once enough history exists).
"""
import csv

from nautilus_trader.model import AggressorSide, Price, Quantity, QuoteTick, TradeId, TradeTick

from .common import LIVE, db, iso_to_ns, sec_to_ns
from .instruments import instrument_id

QUOTE_SIZE = Quantity(1000, 2)


def _px(x):
    return Price(round(min(max(float(x), 0.0), 1.0), 2), 2)


def _size(x):
    try:
        v = float(x)
        return Quantity(round(v, 2), 2) if v > 0 else QUOTE_SIZE
    except (TypeError, ValueError):
        return QUOTE_SIZE


def _quote(iid, bid, ask, ts, bid_size=None, ask_size=None):
    if bid is None or ask is None or bid == "" or ask == "":
        return None
    bid, ask = float(bid), float(ask)
    if not (0 <= bid <= ask <= 1) or ask == 0:      # skip empty / crossed books
        return None
    return QuoteTick(iid, _px(bid), _px(ask), _size(bid_size), _size(ask_size), ts, ts)


def trades(tickers):
    out = []
    if not tickers:
        return out
    with db() as con:
        rows = con.execute(
            f"SELECT trade_id, ticker, created_time, yes_price, count, taker_side FROM kalshi_trades "
            f"WHERE ticker IN ({','.join('?' * len(tickers))}) ORDER BY created_time", list(tickers)).fetchall()
    for r in rows:
        if r["yes_price"] is None or not r["count"]:
            continue
        ts = iso_to_ns(r["created_time"])
        side = AggressorSide.BUY if r["taker_side"] == "yes" else AggressorSide.SELL
        out.append(TradeTick(instrument_id(r["ticker"]), _px(r["yes_price"]), Quantity(round(float(r["count"]), 2), 2),
                             side, TradeId(str(r["trade_id"])[:36]), ts, ts))
    out.sort(key=lambda t: t.ts_event)      # created_time strings mix formats -> sort on real time
    return out


def candle_quotes(tickers, period_min=1):
    out = []
    if not tickers:
        return out
    with db() as con:
        rows = con.execute(
            f"SELECT ticker, end_ts, yes_bid, yes_ask FROM kalshi_candles WHERE period_min = ? AND "
            f"ticker IN ({','.join('?' * len(tickers))}) ORDER BY end_ts", [period_min, *tickers]).fetchall()
    for r in rows:
        q = _quote(instrument_id(r["ticker"]), r["yes_bid"], r["yes_ask"], sec_to_ns(r["end_ts"]))
        if q:
            out.append(q)
    return out


def live_quotes(tickers=None, days=None):
    """Quotes from the live recorder CSVs (the DIY 'live feed' until a server exists)."""
    out, folder = [], LIVE / "kalshi_markets"
    if not folder.exists():
        return out
    files = sorted(folder.glob("*.csv"))
    if days:
        files = [f for f in files if f.stem.split("_")[0] in set(days)]   # YYYY-MM-DD[_vN].csv
    want = set(tickers) if tickers else None
    for f in files:
        with f.open(newline="") as fh:
            for r in csv.DictReader(fh):
                if want and r.get("ticker") not in want:
                    continue
                q = _quote(instrument_id(r["ticker"]), r.get("yes_bid"), r.get("yes_ask"), iso_to_ns(r["ts_utc"]),
                           r.get("yes_bid_size"), r.get("yes_ask_size"))   # real top-of-book size when recorded
                if q:
                    out.append(q)
    return out
