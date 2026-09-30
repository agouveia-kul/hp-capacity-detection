# 05a Task 2 - GB-EoH household selection (rebuilt in 05a-ii under R1, R2, R5, R8)

Source: `scripts/paperb/pools/gb_eoh.py` (rules in its docstring), report `scripts/paperb/iter05a_report.py --part eoh`. Iteration 04 counted homes with a complete Nov-Mar season at >= 90 % (2021/22: 433, 2022/23: 371); 05a-i used a 12-month window at >= 95 % (295 / 244); 05a-ii uses >= 90 % (R1) and flexible month-aligned windows (R2). Main: starts 1 Jun 2021 - 1 Jan 2022. Replication: any start whose 12 months end on or before 29 Sep 2023.

## GB-EoH 2122r2 (main)

Candidate windows (12 months from the 1st; `n_homes_cov90` = homes at >= 90 % valid bins after the zero-run rule, `n_homes_cov95` = at >= 95 % as in 05a-i; `chosen` = most homes at the pool's `coverage_min`):

| start | end | n_homes_cov | n_homes_cov90 | n_homes_cov95 | zero_run_bins | chosen |
|---|---|---|---|---|---|---|
| 2021-06-01 | 2022-05-31 | 225 | 225 | 181 | 140 | False |
| 2021-07-01 | 2022-06-30 | 275 | 275 | 213 | 44 | False |
| 2021-08-01 | 2022-07-31 | 315 | 315 | 251 | 44 | False |
| 2021-09-01 | 2022-08-31 | 355 | 355 | 280 | 44 | False |
| 2021-10-01 | 2022-09-30 | 373 | 373 | 295 | 44 | False |
| 2021-11-01 | 2022-10-31 | 388 | 388 | 307 | 31 | True |
| 2021-12-01 | 2022-11-30 | 379 | 379 | 319 | 31 | False |
| 2022-01-01 | 2022-12-31 | 376 | 376 | 315 | 31 | False |

Eligible homes (after dropping stations that cannot be filled): **385** ({'ASHP': 218, 'HT-ASHP': 153, 'GSHP': 14}), 26 stations with homes (16 with >= 3). Window 2021-11-01 00:00:00 .. 2022-10-31 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 5, IQR 1-21, max 74
- HP_Peak per home (30-min 99.9th pct, kW): median 3.42, IQR 2.96-4.21, max 6.67; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.706, max 1; homes with any: 154
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.365, max 0.991
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 282; homes with any: 47
- **electricity silent while heat is delivered** (share of bins with Q_hp > 1 kW that have P_ws < 0.02 kW; not caught by the exact-zero rule): homes above 1 %: 2, above 5 %: 1 (E:EOH2291 15%); kept in the pool and listed here (not dropped silently)

R5, stations with > 5 % missing T bins in the window (filled from the best-correlated unflagged group with a linear fit on the overlapping days if corr >= 0.98, else dropped with its homes):

| station | missing_share | donor | corr | a | b | n_days_fit | n_bins_filled | action | n_homes_all |
|---|---|---|---|---|---|---|---|---|---|
| G004 | 0.0575 | G001 | 0.963 | nan | nan | nan | nan | dropped | 3 |
| G009 | 0.0873 | G001 | 0.984 | 0.41 | 0.97 | 329 | 1.51e+03 | filled | 50 |
| G024 | 0.0865 | G017 | 0.996 | 0.292 | 1.03 | 334 | 1.5e+03 | filled | 3 |
| G026 | 0.0692 | G005 | 0.949 | nan | nan | nan | nan | dropped | 1 |
| G027 | 1 | nan | nan | nan | nan | nan | nan | dropped | 1 |
| G029 | 0.177 | G018 | 0.969 | nan | nan | nan | nan | dropped | 1 |
| G030 | 0.0525 | G003 | 0.944 | nan | nan | nan | nan | dropped | 1 |

Weather groups (flag: > 5 % missing bins in the window before filling, or values outside [-30, 40] degC):

| station | missing_share | implausible_bins | n_homes_all | n_homes_eligible | flag |
|---|---|---|---|---|---|
| G000 | 0.0028 | 0 | 1 | 0 | False |
| G001 | 0.00559 | 0 | 164 | 99 | False |
| G002 | 0.0139 | 0 | 181 | 122 | False |
| G003 | 0.00674 | 0 | 5 | 2 | False |
| G004 | 0.0575 | 0 | 3 | 0 | True |
| G005 | 0.00485 | 0 | 5 | 3 | False |
| G006 | 0.0175 | 0 | 18 | 17 | False |
| G007 | 0.00325 | 0 | 10 | 10 | False |
| G008 | 0.00651 | 0 | 20 | 12 | False |
| G009 | 0.0873 | 0 | 50 | 37 | True |
| G010 | 0.0106 | 0 | 5 | 5 | False |
| G011 | 0.002 | 0 | 15 | 11 | False |
| G012 | 0.00731 | 0 | 7 | 3 | False |
| G013 | 0.00114 | 0 | 22 | 17 | False |
| G014 | 0.00531 | 0 | 11 | 6 | False |
| G015 | 0.00731 | 0 | 2 | 1 | False |
| G016 | 0.0175 | 0 | 24 | 11 | False |
| G017 | 0.00679 | 0 | 1 | 1 | False |
| G018 | 0.00885 | 0 | 6 | 5 | False |
| G019 | 0.00828 | 0 | 3 | 2 | False |
| G020 | 0.00205 | 0 | 4 | 2 | False |
| G021 | 0.00582 | 0 | 9 | 9 | False |
| G022 | 0.0024 | 0 | 4 | 4 | False |
| G023 | 0.0143 | 0 | 4 | 1 | False |
| G024 | 0.0865 | 0 | 3 | 2 | True |
| G025 | 0.0227 | 0 | 1 | 1 | False |
| G026 | 0.0692 | 0 | 1 | 0 | True |
| G027 | 1 | 0 | 1 | 0 | True |
| G028 | 0.0353 | 0 | 1 | 1 | False |
| G029 | 0.177 | 0 | 1 | 0 | True |
| G030 | 0.0525 | 0 | 1 | 0 | True |
| G031 | 0.0233 | 0 | 1 | 1 | False |

## GB-EoH 2223r2 (replication, rule as written)

Candidate windows (12 months from the 1st; `n_homes_cov90` = homes at >= 90 % valid bins after the zero-run rule, `n_homes_cov95` = at >= 95 % as in 05a-i; `chosen` = most homes at the pool's `coverage_min`):

| start | end | n_homes_cov | n_homes_cov90 | n_homes_cov95 | zero_run_bins | chosen |
|---|---|---|---|---|---|---|
| 2020-11-01 | 2021-10-31 | 24 | 24 | 16 | 109 | False |
| 2020-12-01 | 2021-11-30 | 33 | 33 | 28 | 109 | False |
| 2021-01-01 | 2021-12-31 | 45 | 45 | 32 | 109 | False |
| 2021-02-01 | 2022-01-31 | 69 | 69 | 48 | 109 | False |
| 2021-03-01 | 2022-02-28 | 95 | 95 | 73 | 109 | False |
| 2021-04-01 | 2022-03-31 | 139 | 139 | 108 | 109 | False |
| 2021-05-01 | 2022-04-30 | 181 | 181 | 130 | 140 | False |
| 2021-06-01 | 2022-05-31 | 225 | 225 | 181 | 140 | False |
| 2021-07-01 | 2022-06-30 | 275 | 275 | 213 | 44 | False |
| 2021-08-01 | 2022-07-31 | 315 | 315 | 251 | 44 | False |
| 2021-09-01 | 2022-08-31 | 355 | 355 | 280 | 44 | False |
| 2021-10-01 | 2022-09-30 | 373 | 373 | 295 | 44 | False |
| 2021-11-01 | 2022-10-31 | 388 | 388 | 307 | 31 | True |
| 2021-12-01 | 2022-11-30 | 379 | 379 | 319 | 31 | False |
| 2022-01-01 | 2022-12-31 | 376 | 376 | 315 | 31 | False |
| 2022-02-01 | 2023-01-31 | 376 | 376 | 306 | 301 | False |
| 2022-03-01 | 2023-02-28 | 372 | 372 | 300 | 1150 | False |
| 2022-04-01 | 2023-03-31 | 361 | 361 | 295 | 1942 | False |
| 2022-05-01 | 2023-04-30 | 359 | 359 | 293 | 2488 | False |
| 2022-06-01 | 2023-05-31 | 355 | 355 | 293 | 2488 | False |
| 2022-07-01 | 2023-06-30 | 353 | 353 | 289 | 2488 | False |
| 2022-08-01 | 2023-07-31 | 350 | 350 | 283 | 2488 | False |
| 2022-09-01 | 2023-08-31 | 339 | 339 | 279 | 2488 | False |

Eligible homes (after dropping stations that cannot be filled): **388** ({'ASHP': 218, 'HT-ASHP': 156, 'GSHP': 14}), 26 stations with homes (16 with >= 3). Window 2021-11-01 00:00:00 .. 2022-10-31 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 5, IQR 1-21, max 74
- HP_Peak per home (30-min 99.9th pct, kW): median 3.43, IQR 2.96-4.21, max 6.67; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.706, max 1; homes with any: 154
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.364, max 0.991
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 282; homes with any: 47
- **electricity silent while heat is delivered** (share of bins with Q_hp > 1 kW that have P_ws < 0.02 kW; not caught by the exact-zero rule): homes above 1 %: 2, above 5 %: 1 (E:EOH2291 15%); kept in the pool and listed here (not dropped silently)

R5, stations with > 5 % missing T bins in the window (filled from the best-correlated unflagged group with a linear fit on the overlapping days if corr >= 0.98, else dropped with its homes):

| station | missing_share | donor | corr | a | b | n_days_fit | n_bins_filled | action | n_homes_all |
|---|---|---|---|---|---|---|---|---|---|
| G019 | 0.125 | G004 | 1 | -0.0123 | 1 | 317 | 2.17e+03 | filled | 4 |
| G024 | 0.0865 | G016 | 0.996 | 0.292 | 1.03 | 334 | 1.5e+03 | filled | 3 |
| G026 | 0.0692 | G005 | 0.949 | nan | nan | nan | nan | dropped | 1 |
| G028 | 0.177 | G017 | 0.969 | nan | nan | nan | nan | dropped | 1 |
| G029 | 0.0525 | G003 | 0.944 | nan | nan | nan | nan | dropped | 1 |

Weather groups (flag: > 5 % missing bins in the window before filling, or values outside [-30, 40] degC):

| station | missing_share | implausible_bins | n_homes_all | n_homes_eligible | flag |
|---|---|---|---|---|---|
| G000 | 0.0028 | 0 | 1 | 0 | False |
| G001 | 0.00559 | 0 | 164 | 99 | False |
| G002 | 0.0139 | 0 | 181 | 122 | False |
| G003 | 0.00674 | 0 | 5 | 2 | False |
| G004 | 0.00103 | 0 | 49 | 40 | False |
| G005 | 0.00485 | 0 | 5 | 3 | False |
| G006 | 0.0175 | 0 | 18 | 17 | False |
| G007 | 0.00325 | 0 | 10 | 10 | False |
| G008 | 0.00651 | 0 | 20 | 12 | False |
| G009 | 0.0106 | 0 | 5 | 5 | False |
| G010 | 0.002 | 0 | 15 | 11 | False |
| G011 | 0.00731 | 0 | 8 | 3 | False |
| G012 | 0.00114 | 0 | 22 | 17 | False |
| G013 | 0.00531 | 0 | 11 | 6 | False |
| G014 | 0.00731 | 0 | 2 | 1 | False |
| G015 | 0.0175 | 0 | 24 | 11 | False |
| G016 | 0.00679 | 0 | 1 | 1 | False |
| G017 | 0.00885 | 0 | 6 | 5 | False |
| G018 | 0.00828 | 0 | 3 | 2 | False |
| G019 | 0.125 | 0 | 4 | 0 | True |
| G020 | 0.00205 | 0 | 4 | 2 | False |
| G021 | 0.00582 | 0 | 9 | 9 | False |
| G022 | 0.0024 | 0 | 4 | 4 | False |
| G023 | 0.0143 | 0 | 4 | 1 | False |
| G024 | 0.0865 | 0 | 3 | 2 | True |
| G025 | 0.0227 | 0 | 1 | 1 | False |
| G026 | 0.0692 | 0 | 1 | 0 | True |
| G027 | 0.0353 | 0 | 1 | 1 | False |
| G028 | 0.177 | 0 | 1 | 0 | True |
| G029 | 0.0525 | 0 | 1 | 0 | True |
| G030 | 0.0233 | 0 | 1 | 1 | False |

## GB-EoH 2223sep (replication, latest admissible start (alternative))

Candidate windows (12 months from the 1st; `n_homes_cov90` = homes at >= 90 % valid bins after the zero-run rule, `n_homes_cov95` = at >= 95 % as in 05a-i; `chosen` = most homes at the pool's `coverage_min`):

| start | end | n_homes_cov | n_homes_cov90 | n_homes_cov95 | zero_run_bins | chosen |
|---|---|---|---|---|---|---|
| 2022-09-01 | 2023-08-31 | 339 | 339 | 279 | 2488 | True |

Eligible homes (after dropping stations that cannot be filled): **338** ({'ASHP': 186, 'HT-ASHP': 137, 'GSHP': 15}), 26 stations with homes (17 with >= 3). Window 2022-09-01 00:00:00 .. 2023-08-31 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 6, IQR 1-17, max 84
- HP_Peak per home (30-min 99.9th pct, kW): median 3.49, IQR 2.99-4.47, max 9.84; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.605, max 1; homes with any: 126
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.261, max 0.99
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 178; homes with any: 31
- **electricity silent while heat is delivered** (share of bins with Q_hp > 1 kW that have P_ws < 0.02 kW; not caught by the exact-zero rule): homes above 1 %: 0, above 5 %: 0 (-); kept in the pool and listed here (not dropped silently)

R5, stations with > 5 % missing T bins in the window (filled from the best-correlated unflagged group with a linear fit on the overlapping days if corr >= 0.98, else dropped with its homes):

| station | missing_share | donor | corr | a | b | n_days_fit | n_bins_filled | action | n_homes_all |
|---|---|---|---|---|---|---|---|---|---|
| G008 | 0.0975 | G009 | 0.995 | 0.611 | 0.98 | 324 | 1.69e+03 | filled | 5 |
| G023 | 0.12 | G021 | 0.996 | -1.26 | 0.978 | 320 | 2.08e+03 | filled | 1 |
| G024 | 0.0619 | G021 | 0.998 | 0.734 | 0.969 | 343 | 1.07e+03 | filled | 1 |
| G025 | 0.336 | G004 | 0.963 | nan | nan | nan | nan | dropped | 1 |

Weather groups (flag: > 5 % missing bins in the window before filling, or values outside [-30, 40] degC):

| station | missing_share | implausible_bins | n_homes_all | n_homes_eligible | flag |
|---|---|---|---|---|---|
| G000 | 0.00188 | 0 | 2 | 0 | False |
| G001 | 0.00308 | 0 | 151 | 77 | False |
| G002 | 0.0118 | 0 | 148 | 109 | False |
| G003 | 0.00303 | 0 | 50 | 36 | False |
| G004 | 0.00274 | 0 | 4 | 4 | False |
| G005 | 0.0123 | 0 | 18 | 16 | False |
| G006 | 0.00885 | 0 | 10 | 7 | False |
| G007 | 0.0024 | 0 | 17 | 11 | False |
| G008 | 0.0975 | 0 | 5 | 3 | True |
| G009 | 0.00171 | 0 | 13 | 10 | False |
| G010 | 0.002 | 0 | 6 | 4 | False |
| G011 | 0.00177 | 0 | 21 | 17 | False |
| G012 | 0.00417 | 0 | 8 | 8 | False |
| G013 | 0.00371 | 0 | 2 | 1 | False |
| G014 | 0.00588 | 0 | 4 | 2 | False |
| G015 | 0.0203 | 0 | 21 | 8 | False |
| G016 | 0.00108 | 0 | 1 | 1 | False |
| G017 | 0.002 | 0 | 5 | 5 | False |
| G018 | 0.00497 | 0 | 3 | 3 | False |
| G019 | 0.00194 | 0 | 3 | 2 | False |
| G020 | 0.00348 | 0 | 9 | 6 | False |
| G021 | 0.00519 | 0 | 5 | 3 | False |
| G022 | 0.00422 | 0 | 4 | 1 | False |
| G023 | 0.12 | 0 | 1 | 1 | True |
| G024 | 0.0619 | 0 | 1 | 1 | True |
| G025 | 0.336 | 0 | 1 | 0 | True |
| G026 | 0.0205 | 0 | 1 | 1 | False |
| G027 | 0.00303 | 0 | 1 | 1 | False |

## Overlap of the replication windows with the main window

Main window starts 2021-11-01. The rule as written (best window ending by 29 Sep 2023, any month) picks **2021-11-01**: the main window itself, so it is no replication (overlap 12 months; 385 of 388 homes shared). The latest admissible start, **2022-09-01** (339 homes), overlaps the main window by about 2 months and shares 290 of its 338 homes. No fully disjoint 12-month window exists in the data (Oct 2020 - 29 Sep 2023).

## B*: 30-min vs 15-min HP_Peak

Per HP household, 99.9th pct of the 30-min mean / 99.9th pct of the 15-min series (gap-filled pool series): median **0.974** (IQR 0.916-0.993, n = 86); substation HP_Peak scales by about this factor.

