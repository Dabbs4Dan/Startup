"""Kalshi fee rule (quadratic): fee = ceil_to_cent(rate x contracts x P x (1 - P)) per order.
Taker rate 0.07; maker rate 0.0175 on series that charge makers (KXDIESELD: check fee_type before using).

`kalshi_fee()` is the plain-Python truth used everywhere (tests, reports).
`KalshiFeeModel` plugs the same rule into Nautilus' simulated venue. If the engine build in use doesn't
call Python fee subclasses, engine.py falls back to MakerTakerFeeModel(0, 0) and reports add
kalshi_fee() per fill afterwards (flagged in the run report as fee_mode).
"""
import math
from decimal import Decimal

TAKER_RATE = 0.07
MAKER_RATE = 0.0175


def kalshi_fee(price, contracts, rate=TAKER_RATE):
    raw = rate * contracts * price * (1 - price)
    return math.ceil(round(raw * 100, 6)) / 100


try:
    from nautilus_trader.execution import FeeModel
    from nautilus_trader.model import Money

    class KalshiFeeModel(FeeModel):
        def __new__(cls, rate=TAKER_RATE):
            obj = super().__new__(cls)
            obj.rate = rate
            return obj

        def get_commission(self, order, fill_quantity, fill_px, instrument):
            fee = kalshi_fee(float(fill_px), float(fill_quantity), self.rate)
            return Money(Decimal(str(fee)), instrument.quote_currency)
except Exception:  # noqa — engine not installed / API moved
    KalshiFeeModel = None
