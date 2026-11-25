-- Kalshi Twins research database (SQLite)
-- File: data/kalshi_twins.db   |   Rebuild: python3 tools/build_db.py
-- Rule: raw inputs live in tables; derived math lives in views (always consistent).

-- One row per calendar day. Inputs only.
CREATE TABLE IF NOT EXISTS diesel_daily (
    date              TEXT PRIMARY KEY,   -- YYYY-MM-DD (ET date the AAA price is "as of")
    aaa_diesel        REAL,               -- AAA national avg diesel $/gal (= Kalshi KXDIESELD settlement value)
    aaa_source        TEXT,               -- e.g. kalshi_settlement | aaa_site | manual
    brent_usd_bbl     REAL,               -- Brent crude spot $/barrel
    brent_source      TEXT,               -- e.g. fred:DCOILBRENTEU | manual:tradingeconomics
    ulsd_nyh_usd_gal  REAL,               -- NY Harbor ULSD wholesale $/gal
    ulsd_source       TEXT,               -- e.g. fred:DDFUELNYH | manual:tradingeconomics
    eia_weekly_diesel REAL,               -- EIA weekly U.S. on-highway diesel $/gal (Mondays only)
    tax_federal       REAL DEFAULT 0.244, -- federal diesel excise $/gal
    tax_state_avg     REAL DEFAULT 0.3586,-- EIA avg state taxes+fees $/gal (as of Jan 2026)
    notes             TEXT,
    updated_at        TEXT
);

-- Every Kalshi diesel market (each strike of each day). Raw, for strategy research.
CREATE TABLE IF NOT EXISTS kalshi_markets (
    ticker            TEXT PRIMARY KEY,   -- e.g. KXDIESELD-26NOV24-T5.795
    series_ticker     TEXT,               -- KXDIESELD
    event_ticker      TEXT,               -- KXDIESELD-26NOV24
    event_date        TEXT,               -- YYYY-MM-DD parsed from event ticker
    strike            REAL,               -- e.g. 5.795 ("Above $5.795")
    status            TEXT,
    result            TEXT,               -- yes | no | '' (unsettled)
    expiration_value  REAL,               -- AAA value the market settled on
    last_price        REAL,               -- $ (0-1)
    yes_bid           REAL,
    yes_ask           REAL,
    volume            REAL,
    open_interest     REAL,
    open_time         TEXT,
    close_time        TEXT,
    raw_json          TEXT,               -- full API payload, so nothing is ever lost
    pulled_at         TEXT
);

-- Where every number comes from.
CREATE TABLE IF NOT EXISTS sources (
    key               TEXT PRIMARY KEY,
    description       TEXT,
    url               TEXT,
    cadence           TEXT,
    notes             TEXT
);

-- Research log mirror (CLAUDE.md is the human copy; this is the queryable copy).
CREATE TABLE IF NOT EXISTS research_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              TEXT,
    topic             TEXT,
    finding           TEXT,
    source            TEXT
);

-- THE MAIN VIEW: the 4-part diesel price breakdown (EIA "Today in Energy" method).
-- crude = Brent/42 ; refining = ULSD - crude ; taxes = fed + state ; delivery = AAA - ULSD - taxes
DROP VIEW IF EXISTS v_diesel_breakdown;
CREATE VIEW v_diesel_breakdown AS
SELECT
    date,
    aaa_diesel,
    brent_usd_bbl,
    ulsd_nyh_usd_gal,
    ROUND(brent_usd_bbl / 42.0, 4)                                        AS crude_comp,
    ROUND(ulsd_nyh_usd_gal - brent_usd_bbl / 42.0, 4)                     AS refining_comp,
    ROUND(tax_federal + tax_state_avg, 4)                                 AS taxes_comp,
    ROUND(aaa_diesel - ulsd_nyh_usd_gal - (tax_federal + tax_state_avg), 4) AS delivery_comp,
    ROUND(100.0 * (brent_usd_bbl / 42.0) / aaa_diesel, 1)                 AS crude_pct,
    ROUND(100.0 * (ulsd_nyh_usd_gal - brent_usd_bbl / 42.0) / aaa_diesel, 1) AS refining_pct,
    ROUND(100.0 * (tax_federal + tax_state_avg) / aaa_diesel, 1)          AS taxes_pct,
    ROUND(100.0 * (aaa_diesel - ulsd_nyh_usd_gal - tax_federal - tax_state_avg) / aaa_diesel, 1) AS delivery_pct,
    ROUND(aaa_diesel - LAG(aaa_diesel) OVER (ORDER BY date), 4)           AS aaa_change_1d
FROM diesel_daily
ORDER BY date;
