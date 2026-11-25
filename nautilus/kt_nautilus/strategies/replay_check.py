"""S00 · Replay check (plumbing only — never places orders).

Subscribes to every loaded KXDIESELD instrument and counts what the engine replays: quotes, trades,
first/last timestamps per event. If these counts match the catalog, data -> engine -> strategy works.
"""
from collections import defaultdict

from nautilus_trader.trading import Strategy


class ReplayCheck(Strategy):
    SHEET_ID = "S00"

    def __init__(self, config=None):
        super().__init__(config)
        self.stats = defaultdict(lambda: {"quotes": 0, "trades": 0, "first_ns": None, "last_ns": None})

    def on_start(self):
        ids = [i.id for i in self.cache.instruments()]
        if ids:
            self.subscribe_quotes(ids)
            self.subscribe_trades(ids)

    def _touch(self, iid, ts, kind):
        ev = str(iid).rsplit("-T", 1)[0]
        s = self.stats[ev]
        s[kind] += 1
        s["first_ns"] = ts if s["first_ns"] is None else min(s["first_ns"], ts)
        s["last_ns"] = ts if s["last_ns"] is None else max(s["last_ns"], ts)

    def on_quote(self, quote):
        self._touch(quote.instrument_id, quote.ts_event, "quotes")

    def on_trade(self, trade):
        self._touch(trade.instrument_id, trade.ts_event, "trades")
