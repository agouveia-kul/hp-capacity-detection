# 05a Task 2 - GB-EoH household selection (rebuilt in 05a-ii under R1, R2, R5, R8)

Source: `scripts/paperb/pools/gb_eoh.py` (rules in its docstring), report `scripts/paperb/iter05a_report.py --part eoh`. Iteration 04 counted homes with a complete Nov-Mar season at >= 90 % (2021/22: 433, 2022/23: 371); 05a-i used a 12-month window at >= 95 % (295 / 244); 05a-ii uses >= 90 % (R1) and flexible month-aligned windows (R2). Main: starts 1 Jun 2021 - 1 Jan 2022. Temporal replication (review decision of 2026-10-01): Oct 2022 - 28 Sep 2023, the last full day of data (363 days); fallback Sep 2022 - Aug 2023 only if it gave < 300 homes. Homes whose electricity is silent on > 5 % of their heat bins are excluded.

## GB-EoH 2122r3 (main)

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

Eligible homes (after dropping stations that cannot be filled): **384** ({'ASHP': 217, 'HT-ASHP': 153, 'GSHP': 14}), 26 stations with homes (16 with >= 3). Window 2021-11-01 00:00:00 .. 2022-10-31 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 5, IQR 1-21, max 71
- HP_Peak per home (30-min 99.9th pct, kW): median 3.43, IQR 2.96-4.21, max 6.67; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.71, max 1; homes with any: 154
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.37, max 0.991
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 282; homes with any: 47
- **electricity silent while heat is delivered** (share of bins with Q_hp > 1 kW that have P_ws < 0.02 kW; not caught by the exact-zero rule): homes above 1 %: 1, above 5 %: 0 (-); homes above 5 % are excluded from the pool; excluded here: E:EOH2291 (15%)

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
| G002 | 0.0139 | 0 | 181 | 121 | False |
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

## GB-EoH 2223r3 (temporal replication)

Candidate windows (12 months from the 1st; `n_homes_cov90` = homes at >= 90 % valid bins after the zero-run rule, `n_homes_cov95` = at >= 95 % as in 05a-i; `chosen` = most homes at the pool's `coverage_min`):

| start | end | n_homes_cov | n_homes_cov90 | n_homes_cov95 | zero_run_bins | chosen |
|---|---|---|---|---|---|---|
| 2022-10-01 | 2023-09-28 | 320 | 320 | 255 | 2488 | True |

Eligible homes (after dropping stations that cannot be filled): **319** ({'ASHP': 176, 'HT-ASHP': 127, 'GSHP': 16}), 24 stations with homes (17 with >= 3). Window 2022-10-01 00:00:00 .. 2023-09-28 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 8, IQR 3-20, max 89
- HP_Peak per home (30-min 99.9th pct, kW): median 3.48, IQR 2.98-4.46, max 9.84; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.529, max 1; homes with any: 117
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.248, max 0.99
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 150; homes with any: 25
- **electricity silent while heat is delivered** (share of bins with Q_hp > 1 kW that have P_ws < 0.02 kW; not caught by the exact-zero rule): homes above 1 %: 0, above 5 %: 0 (-); homes above 5 % are excluded from the pool; excluded here: none

R5, stations with > 5 % missing T bins in the window (filled from the best-correlated unflagged group with a linear fit on the overlapping days if corr >= 0.98, else dropped with its homes):

| station | missing_share | donor | corr | a | b | n_days_fit | n_bins_filled | action | n_homes_all |
|---|---|---|---|---|---|---|---|---|---|
| G008 | 0.103 | G009 | 0.995 | 0.6 | 0.978 | 320 | 1.67e+03 | filled | 5 |
| G023 | 0.126 | G021 | 0.997 | -1.21 | 0.973 | 316 | 2.08e+03 | filled | 1 |
| G024 | 0.0678 | G021 | 0.998 | 0.789 | 0.962 | 339 | 1.07e+03 | filled | 1 |
| G025 | 0.41 | G004 | 0.956 | nan | nan | nan | nan | dropped | 1 |

Weather groups (flag: > 5 % missing bins in the window before filling, or values outside [-30, 40] degC):

| station | missing_share | implausible_bins | n_homes_all | n_homes_eligible | flag |
|---|---|---|---|---|---|
| G000 | 0.00752 | 0 | 2 | 0 | False |
| G001 | 0.00844 | 0 | 151 | 68 | False |
| G002 | 0.0144 | 0 | 148 | 110 | False |
| G003 | 0.00855 | 0 | 50 | 33 | False |
| G004 | 0.00809 | 0 | 4 | 4 | False |
| G005 | 0.0179 | 0 | 18 | 15 | False |
| G006 | 0.0142 | 0 | 10 | 7 | False |
| G007 | 0.00775 | 0 | 17 | 9 | False |
| G008 | 0.103 | 0 | 5 | 3 | True |
| G009 | 0.00723 | 0 | 13 | 10 | False |
| G010 | 0.00735 | 0 | 6 | 4 | False |
| G011 | 0.0117 | 0 | 21 | 16 | False |
| G012 | 0.00941 | 0 | 8 | 7 | False |
| G013 | 0.00935 | 0 | 2 | 1 | False |
| G014 | 0.0093 | 0 | 4 | 2 | False |
| G015 | 0.0356 | 0 | 21 | 8 | False |
| G016 | 0.00671 | 0 | 1 | 1 | False |
| G017 | 0.00735 | 0 | 5 | 5 | False |
| G018 | 0.00901 | 0 | 3 | 3 | False |
| G019 | 0.00706 | 0 | 3 | 2 | False |
| G020 | 0.00884 | 0 | 9 | 5 | False |
| G021 | 0.0119 | 0 | 5 | 3 | False |
| G022 | 0.00947 | 0 | 4 | 1 | False |
| G023 | 0.126 | 0 | 1 | 0 | True |
| G024 | 0.0678 | 0 | 1 | 1 | True |
| G025 | 0.41 | 0 | 1 | 0 | True |
| G026 | 0.0287 | 0 | 1 | 0 | False |
| G027 | 0.00849 | 0 | 1 | 1 | False |

## Overlap of the temporal replication with the main window

Main window 2021-11-01 - 2022-10-31; replication 2022-10-01 - 2023-09-28 (320 homes at >= 90 % before dropping unfillable stations). The windows overlap by 1 month; 272 of the 319 replication homes are also in the main pool (384 homes): another year, mostly the same homes, not an independent sample. No fully disjoint 12-month window exists in the data (Oct 2020 - 29 Sep 2023).

## B*: 30-min vs 15-min HP_Peak

Per HP household, 99.9th pct of the 30-min mean / 99.9th pct of the 15-min series (gap-filled pool series): median **0.974** (IQR 0.916-0.993, n = 86); substation HP_Peak scales by about this factor.

