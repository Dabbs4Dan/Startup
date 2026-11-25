"""Which market twin the tools are working on. Set env KT_PRODUCT=gas to run the gas twin; default = diesel.

Each product has its own database + exports folder, so the twins never mix.
Table/column names are shared on purpose (same code runs both):
  in the GAS database, diesel_daily.aaa_diesel = AAA national REGULAR GAS average, and
  diesel_daily.ulsd_nyh_usd_gal = RBOB gasoline futures (RB=F). View `gas_daily` gives readable names.
"""
import os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCT = os.environ.get("KT_PRODUCT", "diesel").lower()

CFG = {
    "diesel": dict(
        label="diesel", db=ROOT / "data" / "kalshi_twins.db", exports=ROOT / "data" / "exports",
        series=["KXDIESELD"], wholesale_symbol="HO=F", wholesale_name="NY Harbor ULSD futures (HO)",
        tax=0.6026,                      # EIA Jan 2026: 24.4c federal + 35.86c avg state (project value)
        normal_delivery=0.90,            # delivery slice "normal" (fixed)
        model_f=dict(k_delivery=0.0672, k_ho_today=0.0183, k_ho_prior=0.0130),   # fitted on diesel (story.py)
        candle_hours=48, unseen=("2026-08-03", "2026-09-25"),
    ),
    "gas": dict(
        label="gas", db=ROOT / "data" / "gas" / "kalshi_gas.db", exports=ROOT / "data" / "gas" / "exports",
        series=["KXAAAGASD", "AAAGASD"], wholesale_symbol="RB=F", wholesale_name="RBOB gasoline futures (RB)",
        tax=0.5167,                      # EIA Jan 2026: 18.40c federal + 33.27c avg state (check state holidays!)
        normal_delivery=None,            # None = use trailing 90-day median of the delivery slice (point-in-time)
        model_f=None,                    # not fitted for gas yet -> model columns stay blank
        candle_hours=20, unseen=None,    # unseen window chosen after the first pull
        trades_keep_days=30,             # gas trades ~3.7K/day: keep 30 event days in the DB, older -> data/gas/archive/*.csv.gz
    ),
}
C = CFG[PRODUCT]
DB = C["db"]
EXPORTS = C["exports"]
SERIES = C["series"]
DB.parent.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(parents=True, exist_ok=True)


def series_like():
    """SQL fragment that keeps only this product's tickers (both new KX* and old tickers)."""
    return " OR ".join(f"ticker LIKE '{s}-%'" for s in SERIES)
