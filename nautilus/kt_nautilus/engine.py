"""Build a BacktestEngine with a simulated KALSHI venue and the project's data."""
from decimal import Decimal

from nautilus_trader.backtest import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model import AccountType, Currency, Money, OmsType, Venue

from . import VENUE_NAME, instruments as ins, loaders
from .fees import KalshiFeeModel

USD = Currency.from_str("USD")


def _fee_model():
    if KalshiFeeModel is not None:
        try:
            return KalshiFeeModel(), "kalshi_quadratic"
        except Exception:  # noqa
            pass
    from nautilus_trader.execution import MakerTakerFeeModel
    return MakerTakerFeeModel(Decimal("0"), Decimal("0")), "post_hoc"


def build(event_tickers, starting_usd=1000, include_live=True):
    try:
        engine = BacktestEngine(BacktestEngineConfig())
    except TypeError:
        engine = BacktestEngine()
    fee_model, fee_mode = _fee_model()
    try:
        engine.add_venue(Venue(VENUE_NAME), OmsType.NETTING, AccountType.CASH, [Money(starting_usd, USD)],
                         base_currency=USD, fee_model=fee_model)
    except Exception:  # noqa — engine rejected the Python fee subclass
        from nautilus_trader.execution import MakerTakerFeeModel
        fee_mode = "post_hoc"
        engine.add_venue(Venue(VENUE_NAME), OmsType.NETTING, AccountType.CASH, [Money(starting_usd, USD)],
                         base_currency=USD, fee_model=MakerTakerFeeModel(Decimal("0"), Decimal("0")))
    insts, meta = ins.load_instruments(event_tickers)
    for i in insts:
        engine.add_instrument(i)
    tickers = list(meta)
    tr = loaders.trades(tickers)
    cq = loaders.candle_quotes(tickers, 1)
    lq = loaders.live_quotes(tickers) if include_live else []
    data = tr + cq + lq
    if data:
        engine.add_data(data)
    counts = {"events": len(event_tickers), "instruments": len(insts), "trades": len(tr),
              "candle_quotes": len(cq), "live_quotes": len(lq), "fee_mode": fee_mode}
    return engine, meta, counts
