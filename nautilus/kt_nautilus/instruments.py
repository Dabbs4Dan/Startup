"""KXDIESELD market rows -> Nautilus BinaryOption instruments.

Instrument ID = '<market ticker>.KALSHI' — the same format the official Kalshi adapter uses live,
so a strategy written against history works unchanged on the demo/live venue.
One instrument per strike, priced in YES terms ($0.01 tick, 0.00–1.00). A NO bet = selling YES
(the adapter's netting model), see README "NO side".
"""
from nautilus_trader.model import (AssetClass, BinaryOption, Currency, InstrumentId, Price, Quantity,
                                   Symbol)

from .common import db, iso_to_ns
from . import VENUE_NAME

USD = Currency.from_str("USD")


def instrument_id(ticker):
    return InstrumentId.from_str(f"{ticker}.{VENUE_NAME}")


def make_binary(row):
    act = iso_to_ns(row["open_time"])
    exp = iso_to_ns(row["close_time"]) or act
    return BinaryOption(
        instrument_id=instrument_id(row["ticker"]),
        raw_symbol=Symbol(row["ticker"]),
        asset_class=AssetClass.ALTERNATIVE,
        currency=USD,
        activation_ns=act,
        expiration_ns=exp,
        price_precision=2,
        size_precision=2,                       # Kalshi now trades fractional contracts (0.01)
        price_increment=Price.from_str("0.01"),
        size_increment=Quantity.from_str("0.01"),
        ts_event=act,
        ts_init=act,
        outcome="Yes",
        description=f"AAA diesel above ${row['strike']:.3f} on {row['event_date']}",
        max_price=Price.from_str("0.99"),
        min_price=Price.from_str("0.01"),
        event_id=row["event_ticker"],
    )


def load_instruments(event_tickers=None, series="KXDIESELD"):
    """All markets (or just some events) from the kalshi_markets table."""
    q = ("SELECT ticker, event_ticker, event_date, strike, open_time, close_time, result, expiration_value "
         "FROM kalshi_markets WHERE series_ticker = ? AND open_time IS NOT NULL AND open_time != ''")
    args = [series]
    if event_tickers:
        q += f" AND event_ticker IN ({','.join('?' * len(event_tickers))})"
        args += list(event_tickers)
    with db() as con:
        rows = con.execute(q + " ORDER BY event_date, strike", args).fetchall()
    return [make_binary(r) for r in rows], {r["ticker"]: dict(r) for r in rows}


def list_events(series="KXDIESELD", settled_only=True):
    q = "SELECT DISTINCT event_ticker FROM kalshi_markets WHERE series_ticker = ?"
    if settled_only:
        q += " AND result IN ('yes','no')"
    with db() as con:
        return [r[0] for r in con.execute(q + " ORDER BY event_date", [series])]
