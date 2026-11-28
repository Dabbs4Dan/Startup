# Backtest master: coverage and vetting

Built by `tools/backtest_master.py` on 2026-11-28 09:10 UTC. Rules: see the docstring of that file.

## Market canvas (Kalshi ladders)

| series      | fuel   | horizon   |   events |   markets |   snapshots | first_settle   | last_settle   |   historical_tier_markets | note              |
|:------------|:-------|:----------|---------:|----------:|------------:|:---------------|:--------------|--------------------------:|:------------------|
| KXDIESELD   | diesel | daily     |      117 |      2611 |         816 | 2026-08-03     | 2026-11-27    |                      1173 |                   |
| KXDIESELW   | diesel | weekly    |       16 |       436 |         577 | 2026-08-09     | 2026-11-23    |                       196 |                   |
| KXDIESELMON | diesel | monthly   |        3 |        77 |         455 | 2026-08-31     | 2026-10-31    |                        21 |                   |
| KXDIESELM   | diesel | monthly   |        0 |           |             |                |               |                           | no usable markets |
| KXAAAGASD   | gas    | daily     |      271 |      4432 |        1790 | 2023-09-18     | 2026-11-27    |                      3238 |                   |
| KXAAAGASW   | gas    | weekly    |      140 |      1111 |        4469 | 2023-10-09     | 2026-11-23    |                       853 |                   |
| KXAAAGASM   | gas    | monthly   |       34 |       485 |        4683 | 2023-12-31     | 2026-10-31    |                       417 |                   |

## Contract cards: is each market the same thing? (rebuilt from raw files every run)

Settlement: every series settles on AAA's national average for ONE date (rule text: "If the Diesel Price on <date> is above $K" / "average regular gas prices ... on <date> according to AAA"). `same_number` counts events whose settle value equals an AAA print for that date that came from another source. The market design is what differs: days open, strike spacing, lines per event, close time, fees.

| fuel   | slice   | series      |   year |   events |   days_open |   lines_per_event |   strike_step_c |   closes_hours_after_settle_midnight_et | settles_on        |   contracts_per_event |   settle_decimals | fee_type                  |   checkable_vs_daily_aaa |   same_number |   different |   max_gap_c |
|:-------|:--------|:------------|-------:|---------:|------------:|------------------:|----------------:|----------------------------------------:|:------------------|----------------------:|------------------:|:--------------------------|-------------------------:|--------------:|------------:|------------:|
| diesel | daily   | KXDIESELD   |   2026 |      117 |         0.7 |                21 |             0.5 |                                     2   | every day         |                 50438 |                 4 | quadratic                 |                      117 |           117 |           0 |         0   |
| diesel | weekly  | KXDIESELW   |   2026 |       16 |         6.7 |                21 |             2   |                                     2   | Mon               |                137835 |                 4 | quadratic                 |                       16 |            16 |           0 |         0   |
| diesel | monthly | KXDIESELMON |   2026 |        3 |        32.7 |                21 |            10   |                                     2   | last day of month |                273791 |                 4 | quadratic                 |                        3 |             3 |           0 |         0   |
| gas    | daily   | KXAAAGASD   |   2023 |       23 |         1   |                 1 |                 |                                     9.9 | every day         |                    38 |                 3 | quadratic                 |                       23 |            23 |           0 |         0   |
| gas    | daily   | KXAAAGASD   |   2024 |        2 |         0.8 |                 1 |                 |                                     4.9 | every day         |                     0 |                 3 | quadratic                 |                        2 |             2 |           0 |         0   |
| gas    | daily   | KXAAAGASD   |   2026 |      247 |         0.7 |                17 |             0.5 |                                    -0   | every day         |                182977 |                 4 | quadratic                 |                      247 |           247 |           0 |         0   |
| gas    | weekly  | KXAAAGASW   |   2023 |       11 |         6   |                 1 |             5   |                                     9.9 | Mon               |                   201 |                 3 | quadratic                 |                        0 |             0 |           0 |             |
| gas    | weekly  | KXAAAGASW   |   2024 |       36 |         6.6 |                 1 |                 |                                    -0   | Mon               |                  3165 |                 3 | quadratic                 |                       25 |            25 |           0 |         0   |
| gas    | weekly  | KXAAAGASW   |   2025 |       48 |         6.6 |                 1 |             3   |                                    -0   | Mon               |                 20485 |                 3 | quadratic                 |                       31 |            31 |           0 |         0   |
| gas    | weekly  | KXAAAGASW   |   2026 |       45 |         6.6 |                24 |             2   |                                    -0   | Mon               |               1006028 |                 4 | quadratic                 |                       44 |            43 |           1 |         0.4 |
| gas    | monthly | KXAAAGASM   |   2023 |        1 |        30   |                 1 |                 |                                     9.9 | last day of month |                  4730 |                 3 | quadratic_with_maker_fees |                        0 |             0 |           0 |             |
| gas    | monthly | KXAAAGASM   |   2024 |       12 |        30.3 |                 6 |             5   |                                    -0   | last day of month |                 34439 |                 3 | quadratic_with_maker_fees |                        6 |             6 |           0 |         0   |
| gas    | monthly | KXAAAGASM   |   2025 |       11 |        30.6 |                10 |             5   |                                    -0   | last day of month |               2671086 |                 3 | quadratic_with_maker_fees |                       10 |            10 |           0 |         0   |
| gas    | monthly | KXAAAGASM   |   2026 |       10 |        30.6 |                35 |             8.7 |                                    -0   | last day of month |               1723078 |                 4 | quadratic_with_maker_fees |                        9 |             9 |           0 |         0   |

## How the crowd prices by days to settlement (10 AM snapshots; description, not a test)

| fuel   | days_out   |   events |   rows |   crowd_range_c |   crowd_expected_move_c |   actual_move_c |   crowd_miss_c |
|:-------|:-----------|---------:|-------:|----------------:|------------------------:|----------------:|---------------:|
| diesel | 1          |      134 |    134 |            0.99 |                    1.2  |            1.57 |           0.37 |
| diesel | 2-3        |       19 |     37 |            3.64 |                    3.4  |            3.47 |           0.98 |
| diesel | 4-7        |       19 |     73 |            6.48 |                    5.15 |            7    |           3.87 |
| diesel | 8-14       |        3 |     21 |           20.79 |                    7.39 |            2.38 |          17    |
| diesel | 15+        |        3 |     46 |           39.02 |                   15.43 |           19.68 |          10.69 |
| gas    | 1          |      341 |    341 |            0.66 |                    1.01 |            0.7  |           0.33 |
| gas    | 2-3        |      165 |    309 |            1.68 |                    1.78 |            1.13 |           0.79 |
| gas    | 4-7        |      162 |    481 |            3.97 |                    3.36 |            2.3  |           2.32 |
| gas    | 8-14       |       32 |    206 |            6.17 |                    3.05 |            4.5  |           3.99 |
| gas    | 15+        |       34 |    440 |            9.96 |                    4.55 |            6.75 |           5.78 |

## Master table by fuel and time slice

| fuel   | horizon   |   events |   snapshots | first_settle   | last_settle   | has_center   | has_3_liquid   | has_aaa_known   | has_main_future   |
|:-------|:----------|---------:|------------:|:---------------|:--------------|:-------------|:---------------|:----------------|:------------------|
| diesel | daily     |      117 |         816 | 2026-08-03     | 2026-11-27    | 80%          | 56%            | 100%            | 100%              |
| diesel | monthly   |        3 |         455 | 2026-08-31     | 2026-10-31    | 69%          | 60%            | 100%            | 100%              |
| diesel | weekly    |       16 |         577 | 2026-08-09     | 2026-11-23    | 84%          | 73%            | 100%            | 100%              |
| gas    | daily     |      271 |        1790 | 2023-09-18     | 2026-11-27    | 87%          | 70%            | 99%             | 100%              |
| gas    | monthly   |       34 |        4683 | 2023-12-31     | 2026-10-31    | 79%          | 68%            | 95%             | 100%              |
| gas    | weekly    |      140 |        4469 | 2023-10-09     | 2026-11-23    | 31%          | 25%            | 98%             | 100%              |

## AAA national history (reconciled)

|   year |   ('days', 'diesel') |   ('days', 'gas') |
|-------:|---------------------:|------------------:|
|   2022 |                    1 |                 0 |
|   2023 |                    0 |                35 |
|   2024 |                  175 |               194 |
|   2025 |                  275 |               294 |
|   2026 |                  261 |               324 |

Source used per day: {"wayback_current": 627, "kalshi_settlement": 389, "wayback_week_ago": 303, "wayback_yesterday": 186, "kalshi_weekly_settlement": 42, "kalshi_monthly_settlement": 10, "db:aaa_site": 1, "live_recorder": 1}

## Inputs (engine canvas)

| input                            | kind    |   rows | first      | last       |   usable_after_days |
|:---------------------------------|:--------|-------:|:-----------|:-----------|--------------------:|
| aaa_diesel                       | daily   |    712 | 2022-11-28 | 2026-11-28 |                   0 |
| aaa_gas                          | daily   |    847 | 2023-09-18 | 2026-11-27 |                   0 |
| brent_spot                       | daily   |   9137 | 1987-05-20 | 2026-11-24 |                   1 |
| fut_brent                        | daily   |   9346 | 1987-05-20 | 2026-11-27 |                   1 |
| fut_ho                           | daily   |  11163 | 1980-01-02 | 2026-11-27 |                   1 |
| fut_natgas                       | daily   |   6592 | 2000-08-30 | 2026-11-27 |                   1 |
| fut_rbob                         | daily   |   6728 | 2000-11-01 | 2026-11-27 |                   1 |
| fut_wti                          | daily   |   9931 | 1986-01-02 | 2026-11-27 |                   1 |
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
| distillate_stocks_padd3_kbbl            | 14%      |
| distillate_stocks_padd3_kbbl_chg_1w_pct | 14%      |
| distillate_stocks_padd4_kbbl            | 14%      |
| distillate_stocks_padd4_kbbl_chg_1w_pct | 14%      |
| distillate_stocks_padd5_kbbl            | 14%      |
| distillate_stocks_padd5_kbbl_chg_1w_pct | 14%      |
| distillate_stocks_us_kbbl               | 14%      |
| distillate_stocks_us_kbbl_chg_1w_pct    | 14%      |
| heating_oil_spot_nyh                    | 14%      |
| jet_spot_gulf                           | 14%      |
| eia_retail_diesel_california            | 14%      |
| eia_retail_diesel_central_atlantic      | 14%      |
| eia_retail_diesel_lower_atlantic        | 14%      |
| eia_retail_diesel_new_england           | 14%      |
| eia_retail_diesel_padd1                 | 14%      |
| eia_retail_diesel_padd2                 | 14%      |
| eia_retail_diesel_padd3                 | 14%      |
| eia_retail_diesel_padd4                 | 14%      |
| eia_retail_diesel_padd5                 | 14%      |
| eia_retail_diesel_us                    | 14%      |
| eia_retail_diesel_west_coast_ex_ca      | 14%      |
| ulsd_spot_gulf                          | 14%      |
| ulsd_spot_la_carb                       | 14%      |
| ulsd_spot_nyh                           | 14%      |
| weekly_distillate_demand_kbd            | 14%      |

## Checks

- **Kalshi quotes never newer than the snapshot:** PASS (built from candles ending at or before each snapshot)
- **diesel daily vs old panel (115 shared days):** settle values differ on 0 days; 10 AM crowd center: median gap 0.00c, 0 days over 0.5c
- **gas daily vs old panel (187 shared days):** settle values differ on 0 days; 10 AM crowd center: median gap 0.00c, 0 days over 0.5c
- **Kalshi settle value vs reconciled AAA:** 581 of 581 events have an AAA print for that date; 1 disagree by more than 0.05c
- **AAA sources that disagree (>0.2c) on the same day:** 1 fuel-days out of 1559
