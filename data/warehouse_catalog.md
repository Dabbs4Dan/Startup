# Warehouse catalog (2026-11-25 21:20 UTC)

Go-live (start of 'since inception'): 2026-11-25 19:21:00 UTC

| dataset | slice | what it is | rows | first | last | rows since go-live |
|---|---|---|---|---|---|---|
| aaa_daily | diesel | AAA national price per day (Kalshi settlements, live recorder, Internet Archive) | 116 | 2025-11-24 | 2026-11-25 | 0 |
| aaa_daily | gas | AAA national price per day (Kalshi settlements, live recorder, Internet Archive) | 269 | 2023-09-18 | 2026-11-25 | 0 |
| state_prices | diesel | AAA price per state per day (daily recorder + Internet Archive state pages) | 51 | 2026-11-25 | 2026-11-25 |  |
| ladder | diesel · live_5m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 441 | 2026-11-25 19:21 | 2026-11-25 20:51 | 441 |
| ladder | diesel · candle_60m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 29240 | 2026-08-02 17:00 | 2026-11-25 17:00 | 0 |
| ladder | diesel · candle_1m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 54672 | 2026-09-27 13:59 | 2026-11-25 18:37 | 0 |
| ladder | gas · live_5m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 323 | 2026-11-25 19:31 | 2026-11-25 20:51 | 323 |
| ladder | gas · candle_60m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 50459 | 2023-09-17 21:00 | 2026-11-25 04:00 | 0 |
| ladder | gas · candle_1m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 105795 | 2026-09-27 12:01 | 2026-11-25 20:50 | 125 |
| trades | diesel | Every Kalshi trade | 29500 | 2026-09-27 12:32 | 2026-11-25 18:32 | 0 |
| trades | gas | Every Kalshi trade | 221067 | 2026-09-27 12:00 | 2026-11-25 20:53 | 149 |
| futures_bars | BRENT · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 19 | 2026-11-25 19:31 | 2026-11-25 20:51 | 19 |
| futures_bars | BRENT · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 1258 | 2021-11-24 19:00 | 2026-11-25 19:00 | 0 |
| futures_bars | HO · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 11152 | 1980-01-02 19:00 | 2026-11-25 19:00 | 0 |
| futures_bars | HO · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 19 | 2026-11-25 19:31 | 2026-11-25 20:51 | 19 |
| futures_bars | NATGAS · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 19 | 2026-11-25 19:31 | 2026-11-25 20:51 | 19 |
| futures_bars | RBOB · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 19 | 2026-11-25 19:31 | 2026-11-25 20:51 | 19 |
| futures_bars | RBOB · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 4609 | 2005-10-03 19:00 | 2024-04-05 19:00 | 0 |
| futures_bars | WTI · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 19 | 2026-11-25 19:31 | 2026-11-25 20:51 | 19 |
| spot_daily | brent_spot | EIA daily spot prices + NYMEX front-month settlements | 9137 | 1987-05-20 | 2026-11-24 |  |
| spot_daily | gasoline_spot_gulf | EIA daily spot prices + NYMEX front-month settlements | 9247 | 1986-06-02 | 2026-11-24 |  |
| spot_daily | gasoline_spot_nyh | EIA daily spot prices + NYMEX front-month settlements | 9186 | 1986-06-02 | 2026-11-24 |  |
| spot_daily | ho_futures_m1 | EIA daily spot prices + NYMEX front-month settlements | 9894 | 1980-01-02 | 2024-04-05 |  |
| spot_daily | rbob_futures_m1 | EIA daily spot prices + NYMEX front-month settlements | 4609 | 2005-10-03 | 2024-04-05 |  |
| spot_daily | ulsd_spot_gulf | EIA daily spot prices + NYMEX front-month settlements | 5129 | 2006-06-14 | 2026-11-24 |  |
| spot_daily | ulsd_spot_la_carb | EIA daily spot prices + NYMEX front-month settlements | 6747 | 1996-04-17 | 2026-11-24 |  |
| spot_daily | ulsd_spot_nyh | EIA daily spot prices + NYMEX front-month settlements | 5131 | 2006-06-14 | 2026-11-24 |  |
| spot_daily | wti_spot | EIA daily spot prices + NYMEX front-month settlements | 9552 | 1986-01-02 | 2026-11-24 |  |
| eia_weekly | distillate_stocks_us_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| eia_weekly | retail_diesel_padd1 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| eia_weekly | retail_diesel_padd2 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| eia_weekly | retail_diesel_padd3 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| eia_weekly | retail_diesel_padd4 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| eia_weekly | retail_diesel_padd5 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| eia_weekly | retail_diesel_us | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| eia_weekly | retail_regular_us | EIA weekly retail diesel/gas by region + diesel inventories | 1887 | 1990-08-20 | 2026-11-23 |  |
| orderbook |  | Kalshi order book depth (live only, no history exists) | 848 | 2026-11-25 19:31 | 2026-11-25 20:51 | 848 |
| truckstop_diesel | loves | Truckstop posted diesel prices, Love's + TA (live only, Chat 4) | 2224 | 2026-11-25 20:20 | 2026-11-25 20:31 | 2224 |
| truckstop_diesel | ta | Truckstop posted diesel prices, Love's + TA (live only, Chat 4) | 110 | 2026-11-25 20:31 | 2026-11-25 20:31 | 110 |

## Feed health (2026-11-25 21:20 UTC)

| feed | last row (UTC) | expected every (min) | minutes since | status |
|---|---|---|---|---|
| Kalshi strikes, 5-min (live recorder) | 2026-11-25 20:51 | 15 | 29.0 | OK |
| Kalshi order book, 15-min (live recorder) | 2026-11-25 20:51 | 30 | 29.0 | OK |
| AAA national, 15-min (live recorder) | 2026-11-25 20:51 | 30 | 29.0 | OK |
| Futures quotes, 5-min (live recorder) | 2026-11-25 20:51 | 15 | 29.0 | OK |
| Love's truckstops, hourly (Chat 4) | 2026-11-25 20:31 | 90 | 49.0 | OK |
| TA truckstops, hourly (Chat 4) | 2026-11-25 20:31 | 90 | 49.0 | OK |
| Kalshi trades + 1-min candles (daily job) | 2026-11-25 20:53 | 2160 | 27.0 | OK |
| Kalshi hourly candles + settlements (daily job) | 2026-11-25 17:00 | 2160 | 261.0 | OK |
| AAA state prices (daily job) | 2026-11-25 12:00 | 2160 | 561.0 | OK |
| EIA spot prices (warehouse job) | 2026-11-24 20:00 | 5760 | 1521.0 | OK |
