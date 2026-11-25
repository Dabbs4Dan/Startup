# 🐚 NautilusTrader in kalshi-twins

**What it is:** the engine that runs every strategy 3 ways with the *same code*:
history replay (backtest) → Kalshi demo (paper) → real money.
**Status (2026-11-25):** installed, wired to our data, tested. **No strategy trades yet** (only `S00`, a replay check).

## Where it fits
```
recorders (GitHub)  →  SQLite + data/live/*.csv  →  kt_nautilus loaders  →  BacktestEngine (KALSHI sim venue)
                                                                        →  reports/ (JSON)  →  Sheet tabs
later:  same strategy class  →  live_demo_node.py (official Kalshi adapter, DEMO)  →  real money
```

## Files
| File | Job |
|---|---|
| `requirements.txt` | engine locked at `nautilus_trader==2.0.0rc9` (first line with the Kalshi adapter) |
| `kt_nautilus/instruments.py` | each KXDIESELD strike → `BinaryOption` `<ticker>.KALSHI` (same IDs as live) |
| `kt_nautilus/loaders.py` | `kalshi_trades` → TradeTick · 1-min `kalshi_candles` → QuoteTick · live recorder CSVs → QuoteTick |
| `kt_nautilus/fees.py` | Kalshi fee `ceil(0.07·C·P·(1−P))` per order, plugged into the sim venue |
| `kt_nautilus/catalog.py` | optional Parquet catalog (`data/nautilus_catalog/`, gitignored) |
| `kt_nautilus/engine.py` | builds the backtest engine for any list of events |
| `kt_nautilus/strategies/` | registry; IDs = Google Sheet **Strategies** tab. `_template.py` to start a new one |
| `run_backtest.py` | `--strategy S00 --events recent|all|<tickers>` → `reports/latest_<id>.json` |
| `selfcheck_fees.py` | buys 10 YES once, checks the engine charged the real Kalshi fee |
| `live_demo_node.py` | Kalshi DEMO node — built, **locked** (3 locks), never runs on GitHub |

## How it runs today (free, GitHub only)
- `.github/workflows/nautilus.yml` runs on any change here, by hand, **and at the end of every live-recorder shift (~6h)**,
  so the replay always includes the newest live snapshots.
- DIY scheduler: GitHub ignores `schedule:` on non-default branches, so the live recorder **relays** — each shift starts the
  next one, kicks Nautilus, and kicks the daily backfill if it hasn't run in 20h. Pause: commit `data/live/STOP`.

## Known gaps (fix before real money)
1. **Pre-release engine** (2.0 rc). Locked; upgrade only after re-running both checks.
2. **No historical order books** from the adapter → book history = our live recorder only (forward from Nov 25).
3. **History quotes have no size** (placeholder 1,000) → backtests on old days assume small orders. Live snapshots (from Nov 25) carry real top-of-book sizes.
4. **NO side:** buying NO = selling YES (netting). Backtests can't open net-short NO yet (adapter limit) → NO strategies need a mirrored "NO instrument" before testing.
5. **Limit orders only**, and the Kalshi order path requires `bypass=True` on the risk engine → every strategy needs its own kill switch.
6. **No auto-reconnect** live → a watchdog (stop → connect) is needed on the server.
7. **Settlement:** sim venue doesn't pay out $1/$0 at AAA settle yet → P&L uses `kalshi_markets.result` post-run (to add with the first real strategy).
8. **Live trading needs the always-on server** (Custom Build CB1). GitHub jobs stop after ~6h.
