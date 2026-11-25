"""SXX · <strategy name>  (copy me — see the Google Sheet "Strategies" tab for the idea + pass/fail rule)

Rules for every strategy file:
- Decide only from data already seen (no peeking): use self.cache / the tick you were handed.
- Kalshi takes LIMIT orders only (no market orders). Use IOC limits at the ask to "take".
- Buying NO = selling YES on the same instrument (netting). Backtests can't open net-short NO yet (adapter limit).
- Size small; fills assume top-of-book depth (see loaders.QUOTE_SIZE).
"""
from nautilus_trader.model import OrderSide, TimeInForce  # noqa: F401
from nautilus_trader.trading import Strategy


class TemplateStrategy(Strategy):
    SHEET_ID = "SXX"

    def __init__(self, config=None):
        super().__init__(config)

    def on_start(self):
        ids = [i.id for i in self.cache.instruments()]
        self.subscribe_quotes(ids)

    def on_quote(self, quote):
        # Example (disabled): buy 10 YES with an IOC limit at the ask when your rule fires.
        # order = self.order_factory.limit(quote.instrument_id, OrderSide.BUY, Quantity.from_int(10),
        #                                  quote.ask_price, time_in_force=TimeInForce.IOC)
        # self.submit_order(order)
        pass
