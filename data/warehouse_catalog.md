# Warehouse catalog (2026-11-28 09:01 UTC)

Go-live (start of 'since inception'): 2026-11-25 19:21:00 UTC

| role | dataset | slice | what it is | rows | first | last | rows since go-live |
|---|---|---|---|---|---|---|---|
| 🎯 Main (diesel) | aaa_daily | diesel | AAA national price per day (Kalshi settlements, live recorder, Internet Archive) | 446 | 2024-07-06 | 2026-11-27 | 2 |
| 🎯 Main (diesel) | state_prices | diesel | AAA price per state per day (daily recorder + Internet Archive state pages) | 648 | 2026-07-31 | 2026-11-27 |  |
| 🎯 Main (diesel) | ladder | diesel · candle_1m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 55506 | 2026-09-27 13:59 | 2026-11-27 17:18 | 834 |
| 🎯 Main (diesel) | ladder | diesel · candle_60m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 29436 | 2026-08-02 17:00 | 2026-11-27 18:00 | 196 |
| 🎯 Main (diesel) | ladder | diesel · live_5m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 10647 | 2026-11-25 19:21 | 2026-11-28 04:55 | 10647 |
| 🎯 Main (diesel) | trades | diesel | Every Kalshi trade | 29887 | 2026-09-27 12:32 | 2026-11-27 17:15 | 387 |
| 🎯 Main (diesel) | futures_bars | HO · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 17743 | 1980-01-02 19:00 | 2026-11-27 19:00 | 3 |
| 🎯 Main (diesel) | futures_bars | HO · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 738 | 2026-11-25 19:31 | 2026-11-28 08:00 | 738 |
| 🎯 Main (diesel) | futures_bars | HO · 1m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 5431 | 2026-11-19 05:00 | 2026-11-27 18:00 | 428 |
| 🎯 Main (diesel) | futures_bars | HO · 5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 12991 | 2026-09-18 04:00 | 2026-11-27 18:00 | 119 |
| 🎯 Main (diesel) | futures_bars | HO · 60m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13487 | 2024-07-08 04:00 | 2026-11-27 18:00 | 13 |
| 🎯 Main (diesel) | spot_daily | heating_oil_spot_nyh | EIA daily spot prices + NYMEX front-month settlements | 8835 | 1986-06-02 | 2026-11-24 |  |
| 🎯 Main (diesel) | spot_daily | ho_futures_m1 | EIA daily spot prices + NYMEX front-month settlements | 9894 | 1980-01-02 | 2024-04-05 |  |
| 🎯 Main (diesel) | spot_daily | jet_spot_gulf | EIA daily spot prices + NYMEX front-month settlements | 8086 | 1990-04-02 | 2026-11-24 |  |
| 🎯 Main (diesel) | spot_daily | ulsd_spot_gulf | EIA daily spot prices + NYMEX front-month settlements | 5129 | 2006-06-14 | 2026-11-24 |  |
| 🎯 Main (diesel) | spot_daily | ulsd_spot_la_carb | EIA daily spot prices + NYMEX front-month settlements | 6747 | 1996-04-17 | 2026-11-24 |  |
| 🎯 Main (diesel) | spot_daily | ulsd_spot_nyh | EIA daily spot prices + NYMEX front-month settlements | 5131 | 2006-06-14 | 2026-11-24 |  |
| 🎯 Main (diesel) | eia_weekly | crude_stocks_us_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | distillate_stocks_padd1_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | distillate_stocks_padd2_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | distillate_stocks_padd3_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | distillate_stocks_padd4_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | distillate_stocks_padd5_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | distillate_stocks_us_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | monthly_diesel_refiner_resale | EIA weekly retail diesel/gas by region + diesel inventories | 471 | 1983-01-15 | 2022-03-15 |  |
| 🎯 Main (diesel) | eia_weekly | retail_allgrades_us | EIA weekly retail diesel/gas by region + diesel inventories | 1756 | 1993-04-05 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_california | EIA weekly retail diesel/gas by region + diesel inventories | 1639 | 1995-07-03 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_central_atlantic | EIA weekly retail diesel/gas by region + diesel inventories | 1540 | 1997-05-26 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_lower_atlantic | EIA weekly retail diesel/gas by region + diesel inventories | 1540 | 1997-05-26 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_new_england | EIA weekly retail diesel/gas by region + diesel inventories | 1540 | 1997-05-26 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_padd1 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_padd2 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_padd3 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_padd4 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_padd5 | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_us | EIA weekly retail diesel/gas by region + diesel inventories | 1706 | 1994-03-21 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_diesel_west_coast_ex_ca | EIA weekly retail diesel/gas by region + diesel inventories | 781 | 2011-12-12 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_midgrade_us | EIA weekly retail diesel/gas by region + diesel inventories | 1670 | 1994-11-28 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | retail_premium_us | EIA weekly retail diesel/gas by region + diesel inventories | 1670 | 1994-11-28 | 2026-11-23 |  |
| 🎯 Main (diesel) | eia_weekly | weekly_distillate_demand_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 1868 | 1991-02-08 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | weekly_distillate_exports_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 860 | 2010-06-04 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | weekly_distillate_imports_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | weekly_distillate_production_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | weekly_refinery_crude_input_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| 🎯 Main (diesel) | eia_weekly | weekly_refinery_utilization_pct | EIA weekly retail diesel/gas by region + diesel inventories | 1882 | 1990-11-02 | 2026-11-20 |  |
| 🎯 Main (diesel) | orderbook |  | Kalshi order book depth (live only, no history exists) | 19388 | 2026-11-25 19:31 | 2026-11-28 04:45 | 19388 |
| 🎯 Main (diesel) | truckstop_diesel | loves | Truckstop posted diesel prices, Love's + TA (live only, Chat 4) | 74369 | 2026-11-25 20:20 | 2026-11-28 07:53 | 74369 |
| 🎯 Main (diesel) | truckstop_diesel | ta | Truckstop posted diesel prices, Love's + TA (live only, Chat 4) | 7257 | 2026-11-25 20:31 | 2026-11-28 07:53 | 7257 |
| 🎯 Main (diesel) | aaa_flips |  | Moments AAA's national number changed (live recorder) | 2 | 2026-11-26 08:32 | 2026-11-27 08:24 |  |
| 🎯 Main (diesel) | ho_at_10am |  | Diesel futures price at the 10 AM bet time, no peeking (live recorder) | 3 | 2026-11-26 | 2026-11-28 |  |
| 🔗 Shared input | futures_bars | BRENT · 60m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13722 | 2024-07-08 04:00 | 2026-11-27 18:00 | 13 |
| 🔗 Shared input | futures_bars | BRENT · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 738 | 2026-11-25 19:31 | 2026-11-28 08:00 | 738 |
| 🔗 Shared input | futures_bars | BRENT · 5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13186 | 2026-09-18 04:00 | 2026-11-27 18:00 | 136 |
| 🔗 Shared input | futures_bars | BRENT · 1m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 5586 | 2026-11-19 05:00 | 2026-11-27 18:00 | 500 |
| 🔗 Shared input | futures_bars | BRENT · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 6073 | 2007-07-30 19:00 | 2026-11-27 19:00 | 3 |
| 🔗 Shared input | futures_bars | NATGAS · 1m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 6644 | 2026-11-19 05:01 | 2026-11-27 18:00 | 622 |
| 🔗 Shared input | futures_bars | NATGAS · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 6592 | 2000-08-30 19:00 | 2026-11-27 19:00 | 1 |
| 🔗 Shared input | futures_bars | NATGAS · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 738 | 2026-11-25 19:31 | 2026-11-28 08:00 | 738 |
| 🔗 Shared input | futures_bars | NATGAS · 60m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13589 | 2024-07-08 04:00 | 2026-11-27 18:00 | 13 |
| 🔗 Shared input | futures_bars | NATGAS · 5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13508 | 2026-09-18 04:00 | 2026-11-27 18:00 | 146 |
| 🔗 Shared input | futures_bars | WTI · 5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13544 | 2026-09-18 04:00 | 2026-11-27 18:00 | 146 |
| 🔗 Shared input | futures_bars | WTI · 60m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13607 | 2024-07-08 04:00 | 2026-11-27 18:00 | 13 |
| 🔗 Shared input | futures_bars | WTI · 1m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 7048 | 2026-11-19 05:00 | 2026-11-27 18:00 | 726 |
| 🔗 Shared input | futures_bars | WTI · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 738 | 2026-11-25 19:31 | 2026-11-28 08:00 | 738 |
| 🔗 Shared input | futures_bars | WTI · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 6595 | 2000-08-23 19:00 | 2026-11-27 19:00 | 1 |
| 🔗 Shared input | spot_daily | brent_spot | EIA daily spot prices + NYMEX front-month settlements | 9137 | 1987-05-20 | 2026-11-24 |  |
| 🔗 Shared input | spot_daily | wti_spot | EIA daily spot prices + NYMEX front-month settlements | 9552 | 1986-01-02 | 2026-11-24 |  |
| ⛽ Side test (gas analog) | aaa_daily | gas | AAA national price per day (Kalshi settlements, live recorder, Internet Archive) | 570 | 2023-09-18 | 2026-11-27 | 2 |
| ⛽ Side test (gas analog) | state_prices | gas | AAA price per state per day (daily recorder + Internet Archive state pages) | 648 | 2026-07-31 | 2026-11-27 |  |
| ⛽ Side test (gas analog) | ladder | gas · candle_1m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 107372 | 2026-09-27 12:01 | 2026-11-27 16:38 | 1702 |
| ⛽ Side test (gas analog) | ladder | gas · live_5m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 8585 | 2026-11-25 19:31 | 2026-11-28 04:55 | 8585 |
| ⛽ Side test (gas analog) | ladder | gas · candle_60m | Kalshi Yes/No prices per strike (hourly, 1-min, 5-min live) | 50822 | 2023-09-17 21:00 | 2026-11-27 04:00 | 301 |
| ⛽ Side test (gas analog) | trades | gas | Every Kalshi trade | 223605 | 2026-09-27 12:00 | 2026-11-27 16:37 | 2687 |
| ⛽ Side test (gas analog) | futures_bars | RBOB · 5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 12904 | 2026-09-18 04:00 | 2026-11-27 18:00 | 125 |
| ⛽ Side test (gas analog) | futures_bars | RBOB · 60m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 13464 | 2024-07-08 04:00 | 2026-11-27 18:00 | 13 |
| ⛽ Side test (gas analog) | futures_bars | RBOB · 1d | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 11159 | 2000-11-01 19:00 | 2026-11-27 19:00 | 1 |
| ⛽ Side test (gas analog) | futures_bars | RBOB · 1m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 5708 | 2026-11-19 05:01 | 2026-11-27 18:00 | 465 |
| ⛽ Side test (gas analog) | futures_bars | RBOB · live_5m | Diesel/oil/gas futures (daily, hourly, 5-min, 1-min, live) | 738 | 2026-11-25 19:31 | 2026-11-28 08:00 | 738 |
| ⛽ Side test (gas analog) | spot_daily | gasoline_spot_gulf | EIA daily spot prices + NYMEX front-month settlements | 9247 | 1986-06-02 | 2026-11-24 |  |
| ⛽ Side test (gas analog) | spot_daily | gasoline_spot_la_rbob | EIA daily spot prices + NYMEX front-month settlements | 5655 | 2003-03-17 | 2026-11-24 |  |
| ⛽ Side test (gas analog) | spot_daily | gasoline_spot_nyh | EIA daily spot prices + NYMEX front-month settlements | 9186 | 1986-06-02 | 2026-11-24 |  |
| ⛽ Side test (gas analog) | spot_daily | rbob_futures_m1 | EIA daily spot prices + NYMEX front-month settlements | 4609 | 2005-10-03 | 2024-04-05 |  |
| ⛽ Side test (gas analog) | eia_weekly | gasoline_stocks_padd1_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | gasoline_stocks_padd2_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | gasoline_stocks_padd3_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | gasoline_stocks_padd4_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | gasoline_stocks_padd5_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | gasoline_stocks_us_kbbl | EIA weekly retail diesel/gas by region + diesel inventories | 1925 | 1990-01-05 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | monthly_regular_refiner_resale | EIA weekly retail diesel/gas by region + diesel inventories | 471 | 1983-01-15 | 2022-03-15 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_california | EIA weekly retail diesel/gas by region + diesel inventories | 1384 | 2000-05-22 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_central_atlantic | EIA weekly retail diesel/gas by region + diesel inventories | 1756 | 1993-04-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_colorado | EIA weekly retail diesel/gas by region + diesel inventories | 1382 | 2000-06-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_florida | EIA weekly retail diesel/gas by region + diesel inventories | 1227 | 2003-05-26 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_lower_atlantic | EIA weekly retail diesel/gas by region + diesel inventories | 1756 | 1993-04-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_massachusetts | EIA weekly retail diesel/gas by region + diesel inventories | 1227 | 2003-05-26 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_minnesota | EIA weekly retail diesel/gas by region + diesel inventories | 1382 | 2000-06-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_new_england | EIA weekly retail diesel/gas by region + diesel inventories | 1756 | 1993-04-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_new_york | EIA weekly retail diesel/gas by region + diesel inventories | 1382 | 2000-06-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_ohio | EIA weekly retail diesel/gas by region + diesel inventories | 1227 | 2003-05-26 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_padd1 | EIA weekly retail diesel/gas by region + diesel inventories | 1803 | 1992-05-11 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_padd2 | EIA weekly retail diesel/gas by region + diesel inventories | 1803 | 1992-05-11 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_padd3 | EIA weekly retail diesel/gas by region + diesel inventories | 1803 | 1992-05-11 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_padd4 | EIA weekly retail diesel/gas by region + diesel inventories | 1803 | 1992-05-11 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_padd5 | EIA weekly retail diesel/gas by region + diesel inventories | 1803 | 1992-05-11 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_texas | EIA weekly retail diesel/gas by region + diesel inventories | 1382 | 2000-06-05 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_us | EIA weekly retail diesel/gas by region + diesel inventories | 1887 | 1990-08-20 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_washington | EIA weekly retail diesel/gas by region + diesel inventories | 1227 | 2003-05-26 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | retail_regular_west_coast_ex_ca | EIA weekly retail diesel/gas by region + diesel inventories | 1489 | 1998-05-18 | 2026-11-23 |  |
| ⛽ Side test (gas analog) | eia_weekly | weekly_gasoline_demand_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 1868 | 1991-02-08 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | weekly_gasoline_imports_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 2304 | 1982-08-20 | 2026-11-20 |  |
| ⛽ Side test (gas analog) | eia_weekly | weekly_gasoline_production_kbd | EIA weekly retail diesel/gas by region + diesel inventories | 2289 | 1982-12-24 | 2026-11-20 |  |

## Feed health (2026-11-28 09:01 UTC)

| feed | last row (UTC) | expected every (min) | minutes since | status |
|---|---|---|---|---|
| Kalshi strikes, 5-min (live recorder) | 2026-11-28 04:55 | 15 | 245.0 | OK (market closed overnight) |
| Kalshi order book, 15-min (live recorder) | 2026-11-28 04:45 | 30 | 255.0 | OK (market closed overnight) |
| AAA national, 15-min (live recorder) | 2026-11-28 08:00 | 30 | 60.0 | OK |
| Futures quotes, 5-min (live recorder) | 2026-11-28 08:00 | 15 | 60.0 | OK |
| Love's truckstops, hourly (Chat 4) | 2026-11-28 07:53 | 90 | 68.0 | OK |
| TA truckstops, hourly (Chat 4) | 2026-11-28 07:53 | 90 | 68.0 | OK |
| Kalshi trades + 1-min candles (daily job) | 2026-11-27 17:15 | 2160 | 946.0 | OK |
| Kalshi hourly candles + settlements (daily job) | 2026-11-27 18:00 | 2160 | 901.0 | OK |
| AAA state prices (daily job) | 2026-11-27 12:00 | 2160 | 1261.0 | OK |
| EIA spot prices (warehouse job) | 2026-11-24 20:00 | 5760 | 5101.0 | OK |
