# 05a Task 2 - GB-EoH household selection

Source: `scripts/paperb/pools/gb_eoh.py` (rules in its docstring), report `scripts/paperb/iter05a_report.py --part eoh`. Iteration 04 counted homes with a complete Nov-Mar season at >= 90 % (2021/22: 433, 2022/23: 371 / 370); 05a asks for a 12-month window at >= 95 % valid 30-min bins.

## GB-EoH 2122

Candidate windows (12 months from the 1st; `candidate` = the pre-specified Jun-Oct starts; Nov/Dec reported only):

| start | n_homes_cov | n_homes_cov90 | zero_run_bins | candidate | chosen |
|---|---|---|---|---|---|
| 2021-06-01 | 181 | 225 | 630 | True | False |
| 2021-07-01 | 213 | 275 | 534 | True | False |
| 2021-08-01 | 251 | 315 | 534 | True | False |
| 2021-09-01 | 280 | 355 | 534 | True | False |
| 2021-10-01 | 295 | 373 | 554 | True | True |
| 2021-11-01 | 307 | 388 | 541 | False | False |
| 2021-12-01 | 319 | 379 | 541 | False | False |

Eligible homes: **295** ({'ASHP': 172, 'HT-ASHP': 116, 'GSHP': 7}), 25 stations with homes (15 with >= 3). Window 2021-10-01 00:00:00 .. 2022-09-30 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 2, IQR 1-9, max 78
- HP_Peak per home (30-min 99.9th pct, kW): median 3.39, IQR 2.97-4.36, max 6.67; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.801, max 1; homes with any: 123
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.41, max 0.991
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 251; homes with any: 41

Weather groups (flag: > 5 % missing bins in the window or values outside [-30, 40] degC):

| station | missing_share | implausible_bins | n_homes_all | n_homes_eligible | flag |
|---|---|---|---|---|---|
| G000 | 0.00263 | 0 | 1 | 0 | False |
| G001 | 0.00588 | 0 | 164 | 72 | False |
| G002 | 0.0111 | 0 | 181 | 100 | False |
| G003 | 0.00708 | 0 | 5 | 0 | False |
| G004 | 0.0599 | 0 | 3 | 2 | True |
| G005 | 0.00537 | 0 | 5 | 3 | False |
| G006 | 0.0181 | 0 | 18 | 15 | False |
| G007 | 0.00297 | 0 | 10 | 8 | False |
| G008 | 0.00651 | 0 | 20 | 8 | False |
| G009 | 0.0874 | 0 | 50 | 27 | True |
| G010 | 0.00982 | 0 | 5 | 4 | False |
| G011 | 0.00217 | 0 | 15 | 6 | False |
| G012 | 0.00759 | 0 | 7 | 3 | False |
| G013 | 0.00131 | 0 | 22 | 13 | False |
| G014 | 0.00525 | 0 | 11 | 4 | False |
| G015 | 0.00805 | 0 | 2 | 1 | False |
| G016 | 0.0175 | 0 | 24 | 7 | False |
| G017 | 0.00742 | 0 | 1 | 1 | False |
| G018 | 0.0093 | 0 | 6 | 4 | False |
| G019 | 0.00845 | 0 | 3 | 2 | False |
| G020 | 0.00177 | 0 | 4 | 2 | False |
| G021 | 0.00599 | 0 | 9 | 7 | False |
| G022 | 0.0024 | 0 | 4 | 2 | False |
| G023 | 0.0168 | 0 | 4 | 1 | False |
| G024 | 0.0332 | 0 | 3 | 1 | False |
| G025 | 0.0226 | 0 | 1 | 0 | False |
| G026 | 0.058 | 0 | 1 | 0 | True |
| G027 | 1 | 0 | 1 | 0 | True |
| G028 | 0.0353 | 0 | 1 | 1 | False |
| G029 | 0.102 | 0 | 1 | 0 | True |
| G030 | 0.137 | 0 | 1 | 0 | True |
| G031 | 0.0238 | 0 | 1 | 1 | False |

## GB-EoH 2223

Candidate windows (12 months from the 1st; `candidate` = the pre-specified Jun-Oct starts; Nov/Dec reported only):

| start | n_homes_cov | n_homes_cov90 | zero_run_bins | candidate | chosen |
|---|---|---|---|---|---|
| 2022-06-01 | 293 | 355 | 2150 | True | False |
| 2022-07-01 | 289 | 353 | 2150 | True | False |
| 2022-08-01 | 283 | 350 | 2150 | True | False |
| 2022-09-01 | 279 | 339 | 2150 | True | False |
| 2022-10-01 | 244 | 315 | 2130 | True | True |
| 2022-11-01 | 0 | 143 | 2130 | False | False |
| 2022-12-01 | 0 | 0 | 2130 | False | False |

Eligible homes: **244** ({'ASHP': 134, 'HT-ASHP': 95, 'GSHP': 15}), 24 stations with homes (14 with >= 3). Window 2022-10-01 00:00:00 .. 2023-09-30 23:30:00 UTC.

- donor-filled days (gaps > 2 h): median 7, IQR 4-13, max 61
- HP_Peak per home (30-min 99.9th pct, kW): median 3.46, IQR 2.97-4.26, max 9.84; rated `HP_Size_kW` median 8.5, IQR 7-11.2, max 18
- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: median 0, IQR 0-0.536, max 1; homes with any: 88
- mean share of the peak bins' power drawn by immersion + back-up: median 0, IQR 0-0.244, max 0.99
- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): median 0, IQR 0-0, max 49; homes with any: 16

Weather groups (flag: > 5 % missing bins in the window or values outside [-30, 40] degC):

| station | missing_share | implausible_bins | n_homes_all | n_homes_eligible | flag |
|---|---|---|---|---|---|
| G000 | 0.013 | 0 | 2 | 0 | False |
| G001 | 0.0139 | 0 | 152 | 49 | False |
| G002 | 0.0198 | 0 | 158 | 84 | False |
| G003 | 0.014 | 0 | 51 | 28 | False |
| G004 | 0.0135 | 0 | 5 | 4 | False |
| G005 | 0.0233 | 0 | 18 | 10 | False |
| G006 | 0.0196 | 0 | 10 | 6 | False |
| G007 | 0.0132 | 0 | 17 | 5 | False |
| G008 | 0.107 | 0 | 5 | 2 | True |
| G009 | 0.0127 | 0 | 13 | 9 | False |
| G010 | 0.0128 | 0 | 6 | 2 | False |
| G011 | 0.0171 | 0 | 21 | 13 | False |
| G012 | 0.0148 | 0 | 9 | 6 | False |
| G013 | 0.0148 | 0 | 2 | 0 | False |
| G014 | 0.0147 | 0 | 4 | 1 | False |
| G015 | 0.0409 | 0 | 23 | 6 | False |
| G016 | 0.0122 | 0 | 1 | 1 | False |
| G017 | 0.0128 | 0 | 5 | 3 | False |
| G018 | 0.0144 | 0 | 3 | 2 | False |
| G019 | 0.0125 | 0 | 3 | 2 | False |
| G020 | 0.0143 | 0 | 9 | 4 | False |
| G021 | 0.0174 | 0 | 5 | 3 | False |
| G022 | 0.0149 | 0 | 4 | 1 | False |
| G023 | 0.131 | 0 | 1 | 0 | True |
| G024 | 0.0729 | 0 | 1 | 1 | True |
| G025 | 0.414 | 0 | 1 | 1 | True |
| G026 | 1 | 0 | 1 | 0 | True |
| G027 | 0.034 | 0 | 1 | 0 | False |
| G028 | 0.0139 | 0 | 1 | 1 | False |

## B*: 30-min vs 15-min HP_Peak

Per HP household, 99.9th pct of the 30-min mean / 99.9th pct of the 15-min series (gap-filled pool series): median **0.974** (IQR 0.916-0.993, n = 86); substation HP_Peak scales by about this factor.

