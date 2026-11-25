#!/usr/bin/env python3
"""Kalshi DEMO trading node — built, but OFF.

Same strategy classes as the backtest, connected to Kalshi's demo exchange through Nautilus' official
Kalshi adapter (nautilus_trader 2.0.0rc9). It will NOT start unless all 3 locks are open:
  1. ENABLED = True below (flipped only after Dan approves a strategy for paper trading)
  2. env KALSHI_DEMO_API_KEY_ID + KALSHI_DEMO_PRIVATE_KEY (PEM text) — stored as secrets, never in the repo
  3. --i-understand flag on the command line
It refuses to run on GitHub Actions (jobs stop after ~6h, the adapter has no auto-reconnect) — this is
meant for the always-on server (Custom Build CB1).

Adapter limits to remember: limit orders only (no market orders); the order path needs the risk engine
bypassed (bypass=True) → our OWN kill switch (KILL_* below) must sit inside every strategy; no automatic
reconnect after a disconnect (needs a watchdog: stop() then connect()).

  python3 nautilus/live_demo_node.py --strategy S01 --check      # config check only, no connection
"""
import argparse, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

ENABLED = False                   # lock 1
ENVIRONMENT = "DEMO"              # never PRODUCTION from this file
KILL_MAX_DAILY_LOSS_USD = 25      # our own guard rails (risk engine is bypassed for Kalshi)
KILL_MAX_CONTRACTS_PER_ORDER = 20


def open_instrument_ids(series="KXDIESELD"):
    """Today's open strikes from Kalshi's public API (no key needed). The adapter needs explicit IDs."""
    import json, urllib.request
    from kt_nautilus.instruments import instrument_id
    base = "https://demo-api.kalshi.co" if ENVIRONMENT == "DEMO" else "https://api.elections.kalshi.com"
    url = f"{base}/trade-api/v2/markets?series_ticker={series}&status=open&limit=200"
    with urllib.request.urlopen(url, timeout=20) as r:
        return [instrument_id(m["ticker"]) for m in json.load(r).get("markets", [])]


def build_node(strategy_id, instrument_ids=None):
    from nautilus_trader.adapters.kalshi import (KalshiDataClientConfig, KalshiDataClientFactory, KalshiEnvironment,
                                                 KalshiExecutionClientConfig, KalshiExecutionClientFactory)
    from nautilus_trader.common import Environment
    from nautilus_trader.live import LiveNode, LiveRiskEngineConfig
    from nautilus_trader.model import TraderId
    from kt_nautilus.strategies import REGISTRY

    key_id, pem = os.environ.get("KALSHI_DEMO_API_KEY_ID"), os.environ.get("KALSHI_DEMO_PRIVATE_KEY")
    env = KalshiEnvironment.DEMO
    ids = instrument_ids if instrument_ids is not None else open_instrument_ids()
    data_cfg = KalshiDataClientConfig(api_key_id=key_id, private_key=pem, environment=env, instrument_ids=ids)
    exec_cfg = KalshiExecutionClientConfig(api_key_id=key_id, private_key=pem, environment=env)
    node = (LiveNode.builder("kalshi-twins-demo", TraderId("KTWINS-001"), Environment.LIVE)
            .with_risk_engine_config(LiveRiskEngineConfig(bypass=True))
            .add_data_client(None, KalshiDataClientFactory(), data_cfg)
            .add_exec_client(None, KalshiExecutionClientFactory(), exec_cfg)
            .build())
    node.add_strategy(REGISTRY[strategy_id]())
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="S00")
    ap.add_argument("--check", action="store_true", help="validate imports/config only; never connects")
    ap.add_argument("--i-understand", action="store_true")
    a = ap.parse_args()

    import nautilus_trader
    from nautilus_trader.adapters import kalshi  # noqa: F401  (proves the adapter is present)
    from kt_nautilus import PINNED_VERSION
    from kt_nautilus.strategies import REGISTRY
    status = {
        "engine": nautilus_trader.__version__, "pinned": PINNED_VERSION, "kalshi_adapter": True,
        "strategy_registered": a.strategy in REGISTRY, "enabled": ENABLED, "environment": ENVIRONMENT,
        "demo_keys_present": bool(os.environ.get("KALSHI_DEMO_API_KEY_ID") and os.environ.get("KALSHI_DEMO_PRIVATE_KEY")),
        "on_github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
    }
    print(status)
    if a.check:
        return
    if not (ENABLED and status["demo_keys_present"] and a.i_understand) or status["on_github_actions"]:
        sys.exit("🔒 Demo node is locked (see the 3 locks at the top of this file). Nothing was started.")
    node = build_node(a.strategy)
    try:
        node.run()
    finally:
        node.dispose()


if __name__ == "__main__":
    main()
