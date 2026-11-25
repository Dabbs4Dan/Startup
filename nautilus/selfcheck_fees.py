#!/usr/bin/env python3
"""Self-check: does the simulated KALSHI venue charge the real Kalshi fee?

Runs ONE settled event with a throwaway test strategy that buys 10 YES once (IOC limit at the ask),
then compares the engine's commission with kalshi_fee(). Not a strategy — a meter check.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from nautilus_trader.model import OrderSide, Quantity, TimeInForce  # noqa: E402
from nautilus_trader.trading import Strategy  # noqa: E402
from kt_nautilus import instruments as ins  # noqa: E402
from kt_nautilus.common import REPORTS  # noqa: E402
from kt_nautilus.engine import build  # noqa: E402
from kt_nautilus.fees import kalshi_fee  # noqa: E402


class BuyOnce(Strategy):
    def __init__(self):
        super().__init__(None)
        self.sent = False
        self.fills = []

    def on_start(self):
        self.subscribe_quotes([i.id for i in self.cache.instruments()])

    def on_quote(self, q):
        ask = float(q.ask_price)
        if not self.sent and 0.30 <= ask <= 0.90 and float(q.bid_price) > 0:
            self.sent = True
            self.submit_order(self.order_factory.limit(q.instrument_id, OrderSide.BUY, Quantity(10, 2),
                                                       q.ask_price, time_in_force=TimeInForce.IOC))

    def on_order_filled(self, e):
        self.fills.append({"px": float(e.last_px), "qty": float(e.last_qty), "fee": float(e.commission.as_double())})


def main():
    ev = ins.list_events(settled_only=True)[-1]
    engine, _, counts = build([ev], include_live=False)
    s = BuyOnce()
    engine.add_strategy(s)
    engine.run()
    engine.dispose()
    rows = [dict(f, expected=kalshi_fee(f["px"], f["qty"])) for f in s.fills]
    ok = bool(rows) and all(abs(r["fee"] - r["expected"]) < 1e-9 for r in rows)
    out = {"event": ev, "fee_mode": counts["fee_mode"], "fills": rows, "pass": ok}
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "selfcheck_fees.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
