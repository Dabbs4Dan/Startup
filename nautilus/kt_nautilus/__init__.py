"""kalshi-twins x NautilusTrader bridge.

Turns the project's own data (SQLite + live recorder CSVs) into Nautilus objects, so any strategy
can be replayed on history (backtest) and later run unchanged on the Kalshi demo / live venue.

Pinned engine: nautilus_trader==2.0.0rc9 (first line with the official Kalshi adapter).
Modules:
  instruments  KXDIESELD markets  -> BinaryOption instruments  (<ticker>.KALSHI, same IDs the live adapter uses)
  loaders      kalshi_trades      -> TradeTick
               kalshi_candles     -> QuoteTick (candle-close yes bid/ask)
               data/live/kalshi_markets/*.csv -> QuoteTick (live recorder snapshots, every ~5 min)
  fees         Kalshi quadratic taker fee: ceil(0.07 x C x P x (1-P)) to the cent, per order
  catalog      writes everything to a ParquetDataCatalog (data/nautilus_catalog, rebuilt each run, not committed)
  engine       builds a BacktestEngine with a KALSHI venue for one or many events
  strategies   registry: one file per strategy, IDs match the Google Sheet "Strategies" tab
"""
PINNED_VERSION = "2.0.0rc9"
VENUE_NAME = "KALSHI"
