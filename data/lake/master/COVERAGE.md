# Backtest master: coverage and vetting

Built by `tools/backtest_master.py` on 2026-11-26 23:29 UTC. Rules: see the docstring of that file.

## Market canvas (Kalshi ladders)

| series      | fuel   | horizon   |   events |   markets |   snapshots | first_settle   | last_settle   |   historical_tier_markets | note                   |
|:------------|:-------|:----------|---------:|----------:|------------:|:---------------|:--------------|--------------------------:|:-----------------------|
| KXDIESELD   | diesel | daily     |      116 |      2590 |         346 | 2026-08-03     | 2026-11-26    |                      1131 |                        |
| KXDIESELW   | diesel | weekly    |       16 |       436 |         327 | 2026-08-09     | 2026-11-23    |                       196 |                        |
| KXDIESELMON | diesel | monthly   |        3 |        77 |         271 | 2026-08-31     | 2026-10-31    |                        21 |                        |
| KXDIESELM   | diesel | monthly   |        0 |           |             |                |               |                           | no usable markets      |
| KXAAAGASD   | gas    | daily     |        0 |           |             |                |               |                           | not pulled / not found |
| KXAAAGASW   | gas    | weekly    |      139 |      1110 |        2462 | 2023-10-09     | 2026-11-23    |                       852 |                        |
| KXAAAGASM   | gas    | monthly   |       34 |       485 |        2725 | 2023-12-31     | 2026-10-31    |                       417 |                        |

## Master table by fuel and time slice

| fuel   | horizon   |   events |   snapshots | first_settle   | last_settle   | has_center   | has_3_liquid   | has_aaa_known   | has_main_future   |
|:-------|:----------|---------:|------------:|:---------------|:--------------|:-------------|:---------------|:----------------|:------------------|
| diesel | daily     |      116 |         346 | 2026-08-03     | 2026-11-26    | 84%          | 60%            | 100%            | 100%              |
| diesel | monthly   |        3 |         271 | 2026-08-31     | 2026-10-31    | 69%          | 61%            | 100%            | 100%              |
| diesel | weekly    |       16 |         327 | 2026-08-09     | 2026-11-23    | 84%          | 75%            | 100%            | 100%              |
| gas    | monthly   |       34 |        2725 | 2023-12-31     | 2026-10-31    | 80%          | 69%            | 95%             | 100%              |
| gas    | weekly    |      139 |        2462 | 2023-10-09     | 2026-11-23    | 32%          | 26%            | 98%             | 100%              |

## AAA national history (reconciled)

|   year |   ('days', 'diesel') |   ('days', 'gas') |
|-------:|---------------------:|------------------:|
|   2022 |                    1 |                 0 |
|   2023 |                    0 |                35 |
|   2024 |                  175 |               193 |
|   2025 |                  275 |               294 |
|   2026 |                  259 |               323 |

Source used per day: {"wayback_current": 627, "wayback_week_ago": 301, "db:kalshi_settlement": 270, "wayback_yesterday": 188, "kalshi_settlement": 116, "kalshi_weekly_settlement": 42, "kalshi_monthly_settlement": 10, "db:aaa_site": 1}

## Inputs (engine canvas)

| input                            | kind    |   rows | first      | last       |   usable_after_days |
|:---------------------------------|:--------|-------:|:-----------|:-----------|--------------------:|
| aaa_diesel                       | daily   |    710 | 2022-11-28 | 2026-11-26 |                   0 |
| aaa_gas                          | daily   |    845 | 2023-09-18 | 2026-11-26 |                   0 |
| brent_spot                       | daily   |   9137 | 1987-05-20 | 2026-11-24 |                   1 |
| fut_brent                        | daily   |   9321 | 1987-05-20 | 2026-11-24 |                   1 |
| fut_ho                           | daily   |  10631 | 1980-01-02 | 2026-11-24 |                   1 |
| fut_natgas                       | daily   |      0 |            |            |                   1 |
| fut_rbob                         | daily   |   5346 | 2005-10-03 | 2026-11-24 |                   1 |
| fut_wti                          | daily   |   9552 | 1986-01-02 | 2026-11-24 |                   1 |
| gasoline_spot_gulf               | daily   |   9247 | 1986-06-02 | 2026-11-24 |                   1 |
| gasoline_spot_la_rbob            | daily   |   5655 | 2003-03-17 | 2026-11-24 |                   1 |
| gasoline_spot_nyh                | daily   |   9186 | 1986-06-02 | 2026-11-24 |                   1 |
| heating_oil_spot_nyh             | daily   |   8835 | 1986-06-02 | 2026-11-24 |                   1 |
| jet_spot_gulf                    | daily   |   8086 | 1990-04-02 | 2026-11-24 |                   1 |
| ulsd_spot_gulf                   | daily   |   5129 | 2006-06-14 | 2026-11-24 |                   1 |
| ulsd_spot_la_carb                | daily   |   6747 | 1996-04-17 | 2026-11-24 |                   1 |
| ulsd_spot_nyh                    | daily   |   5131 | 2006-06-14 | 2026-11-24 |                   1 |
| wti_spot                         | daily   |   9552 | 1986-01-02 | 2026-11-24 |                   1 |
| monthly_diesel_refiner_resale    | monthly |    471 | 1983-01-15 | 2022-03-15 |                  60 |
| monthly_regular_refiner_resale   | monthly |    471 | 1983-01-15 | 2022-03-15 |                  60 |
| crude_stocks_us_kbbl             | weekly  |   2304 | 1982-08-20 | 2026-11-20 |                   6 |
| distillate_stocks_padd1_kbbl     | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| distillate_stocks_padd2_kbbl     | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| distillate_stocks_padd3_kbbl     | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| distillate_stocks_padd4_kbbl     | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| distillate_stocks_padd5_kbbl     | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| distillate_stocks_us_kbbl        | weekly  |   2304 | 1982-08-20 | 2026-11-20 |                   6 |
| gasoline_stocks_padd1_kbbl       | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| gasoline_stocks_padd2_kbbl       | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| gasoline_stocks_padd3_kbbl       | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| gasoline_stocks_padd4_kbbl       | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| gasoline_stocks_padd5_kbbl       | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| gasoline_stocks_us_kbbl          | weekly  |   1925 | 1990-01-05 | 2026-11-20 |                   6 |
| retail_allgrades_us              | weekly  |   1756 | 1993-04-05 | 2026-11-23 |                   1 |
| retail_diesel_california         | weekly  |   1639 | 1995-07-03 | 2026-11-23 |                   1 |
| retail_diesel_central_atlantic   | weekly  |   1540 | 1997-05-26 | 2026-11-23 |                   1 |
| retail_diesel_lower_atlantic     | weekly  |   1540 | 1997-05-26 | 2026-11-23 |                   1 |
| retail_diesel_new_england        | weekly  |   1540 | 1997-05-26 | 2026-11-23 |                   1 |
| retail_diesel_padd1              | weekly  |   1706 | 1994-03-21 | 2026-11-23 |                   1 |
| retail_diesel_padd2              | weekly  |   1706 | 1994-03-21 | 2026-11-23 |                   1 |
| retail_diesel_padd3              | weekly  |   1706 | 1994-03-21 | 2026-11-23 |                   1 |
| retail_diesel_padd4              | weekly  |   1706 | 1994-03-21 | 2026-11-23 |                   1 |
| retail_diesel_padd5              | weekly  |   1706 | 1994-03-21 | 2026-11-23 |                   1 |
| retail_diesel_us                 | weekly  |   1706 | 1994-03-21 | 2026-11-23 |                   1 |
| retail_diesel_west_coast_ex_ca   | weekly  |    781 | 2011-12-12 | 2026-11-23 |                   1 |
| retail_midgrade_us               | weekly  |   1670 | 1994-11-28 | 2026-11-23 |                   1 |
| retail_premium_us                | weekly  |   1670 | 1994-11-28 | 2026-11-23 |                   1 |
| retail_regular_california        | weekly  |   1384 | 2000-05-22 | 2026-11-23 |                   1 |
| retail_regular_central_atlantic  | weekly  |   1756 | 1993-04-05 | 2026-11-23 |                   1 |
| retail_regular_colorado          | weekly  |   1382 | 2000-06-05 | 2026-11-23 |                   1 |
| retail_regular_florida           | weekly  |   1227 | 2003-05-26 | 2026-11-23 |                   1 |
| retail_regular_lower_atlantic    | weekly  |   1756 | 1993-04-05 | 2026-11-23 |                   1 |
| retail_regular_massachusetts     | weekly  |   1227 | 2003-05-26 | 2026-11-23 |                   1 |
| retail_regular_minnesota         | weekly  |   1382 | 2000-06-05 | 2026-11-23 |                   1 |
| retail_regular_new_england       | weekly  |   1756 | 1993-04-05 | 2026-11-23 |                   1 |
| retail_regular_new_york          | weekly  |   1382 | 2000-06-05 | 2026-11-23 |                   1 |
| retail_regular_ohio              | weekly  |   1227 | 2003-05-26 | 2026-11-23 |                   1 |
| retail_regular_padd1             | weekly  |   1803 | 1992-05-11 | 2026-11-23 |                   1 |
| retail_regular_padd2             | weekly  |   1803 | 1992-05-11 | 2026-11-23 |                   1 |
| retail_regular_padd3             | weekly  |   1803 | 1992-05-11 | 2026-11-23 |                   1 |
| retail_regular_padd4             | weekly  |   1803 | 1992-05-11 | 2026-11-23 |                   1 |
| retail_regular_padd5             | weekly  |   1803 | 1992-05-11 | 2026-11-23 |                   1 |
| retail_regular_texas             | weekly  |   1382 | 2000-06-05 | 2026-11-23 |                   1 |
| retail_regular_us                | weekly  |   1887 | 1990-08-20 | 2026-11-23 |                   1 |
| retail_regular_washington        | weekly  |   1227 | 2003-05-26 | 2026-11-23 |                   1 |
| retail_regular_west_coast_ex_ca  | weekly  |   1489 | 1998-05-18 | 2026-11-23 |                   1 |
| weekly_distillate_demand_kbd     | weekly  |   1868 | 1991-02-08 | 2026-11-20 |                   6 |
| weekly_distillate_exports_kbd    | weekly  |    860 | 2010-06-04 | 2026-11-20 |                   6 |
| weekly_distillate_imports_kbd    | weekly  |   2304 | 1982-08-20 | 2026-11-20 |                   6 |
| weekly_distillate_production_kbd | weekly  |   2304 | 1982-08-20 | 2026-11-20 |                   6 |
| weekly_gasoline_demand_kbd       | weekly  |   1868 | 1991-02-08 | 2026-11-20 |                   6 |
| weekly_gasoline_imports_kbd      | weekly  |   2304 | 1982-08-20 | 2026-11-20 |                   6 |
| weekly_gasoline_production_kbd   | weekly  |   2289 | 1982-12-24 | 2026-11-20 |                   6 |
| weekly_refinery_crude_input_kbd  | weekly  |   2304 | 1982-08-20 | 2026-11-20 |                   6 |
| weekly_refinery_utilization_pct  | weekly  |   1882 | 1990-11-02 | 2026-11-20 |                   6 |

## Emptiest columns in the master (fill rate)

|                                         | filled   |
|:----------------------------------------|:---------|
| ulsd_spot_la_carb                       | 15%      |
| ulsd_spot_nyh                           | 15%      |
| weekly_distillate_demand_kbd            | 15%      |
| weekly_distillate_exports_kbd           | 15%      |
| weekly_distillate_imports_kbd           | 15%      |
| weekly_distillate_production_kbd        | 15%      |
| ulsd_spot_gulf                          | 15%      |
| eia_retail_diesel_west_coast_ex_ca      | 15%      |
| eia_retail_diesel_new_england           | 15%      |
| eia_retail_diesel_lower_atlantic        | 15%      |
| eia_retail_diesel_us                    | 15%      |
| eia_retail_diesel_padd5                 | 15%      |
| eia_retail_diesel_padd4                 | 15%      |
| eia_retail_diesel_padd3                 | 15%      |
| eia_retail_diesel_padd2                 | 15%      |
| eia_retail_diesel_padd1                 | 15%      |
| distillate_stocks_us_kbbl               | 15%      |
| distillate_stocks_us_kbbl_chg_1w_pct    | 15%      |
| heating_oil_spot_nyh                    | 15%      |
| jet_spot_gulf                           | 15%      |
| eia_retail_diesel_california            | 15%      |
| eia_retail_diesel_central_atlantic      | 15%      |
| distillate_stocks_padd5_kbbl_chg_1w_pct | 15%      |
| distillate_stocks_padd5_kbbl            | 15%      |
| distillate_stocks_padd2_kbbl            | 15%      |

## Checks

- **Kalshi quotes never newer than the snapshot:** PASS (built from candles ending at or before each snapshot)
- **diesel daily vs old panel (113 shared days):** settle values differ on 0 days; 10 AM crowd center: median gap 0.00c, 0 days over 0.5c
- **gas daily vs old panel (0 shared days):** settle values differ on 0 days; 10 AM crowd center: median gap nanc, 0 days over 0.5c
- **Kalshi settle value vs reconciled AAA:** 308 of 308 events have an AAA print for that date; 1 disagree by more than 0.05c
- **AAA sources that disagree (>0.2c) on the same day:** 1 fuel-days out of 1555
