# Iteration 01 - ML audit checks

Source: `scripts/audit/ml_audit_checks.py` (config `iter01_pool_audit_quick`); legacy caches in `data/` (read-only). Protocol = legacy.

## M1 Scale_peak vs HP_Peak

| set | n | corr(Scale_peak, HP_Peak) | corr(size, HP_Peak) | median HP_Peak / Scale_peak |
|---|---|---|---|---|
| HEAPO legacy test | 1080 | 0.948 | 0.655 | 0.737 |
| HEAPO legacy train | 1080 | 0.888 | 0.646 | 0.711 |
| WPuQ synthetic transfer | 400 | 0.895 | 0.469 | 0.8 |

Linear map HP_Peak ~ Scale_peak fitted on train, scored on test: **R2 = 0.891**.

Test corr(Scale_peak, HP_Peak) within each penetration level:

| HP_ratio | corr |
|---|---|
| 0.1 | 0.901 |
| 0.2 | 0.924 |
| 0.3 | 0.935 |
| 0.4 | 0.953 |
| 0.5 | 0.966 |
| 0.6 | 0.975 |
| 0.7 | 0.978 |
| 0.8 | 0.989 |
| 0.9 | 0.987 |
| 1.0 | 0.986 |

## M3 NaN / extreme values in the capacity feature matrix

| set | features | rows | NaN cells % | rows with any NaN | cols with any NaN | |value| > 1e3 cells |
|---|---|---|---|---|---|---|
| HEAPO train | all 274 (scale-free + 2 anchors) | 1080 | 0.0 | 0 | 0 | 3 |
| HEAPO train | 60 selected | 1080 | 0.0 | 0 | 0 | 3 |
| HEAPO test | all 274 (scale-free + 2 anchors) | 1080 | 0.0 | 0 | 0 | 0 |
| HEAPO test | 60 selected | 1080 | 0.0 | 0 | 0 | 0 |
| WPuQ synthetic | all 274 (scale-free + 2 anchors) | 400 | 0.0 | 0 | 0 | 0 |
| WPuQ synthetic | 60 selected | 400 | 0.0 | 0 | 0 | 0 |
| WPuQ real feeder | all 274 (scale-free + 2 anchors) | 1 | 0.0 | 0 | 0 | 0 |
| WPuQ real feeder | 60 selected | 1 | 0.0 | 0 | 0 | 0 |

## M4 HDD-bin weekday counts (thresholds 10 / 25 degree-hours per day)

| dataset | T_base | warm | mild | cold | extreme |
|---|---|---|---|---|---|
| HEAPO Hg 2023 | 12.0 | 67 | 30 | 20 | 143 |
| HEAPO Hg 2023 | 15.0 | 33 | 28 | 17 | 182 |
| HEAPO 8jB 2023 | 12.0 | 65 | 31 | 22 | 142 |
| HEAPO 8jB 2023 | 15.0 | 29 | 29 | 21 | 181 |
| HEAPO HbsbG 2023 | 12.0 | 78 | 26 | 10 | 146 |
| HEAPO HbsbG 2023 | 15.0 | 42 | 28 | 20 | 170 |
| HEAPO MqO 2023 | 12.0 | 44 | 26 | 24 | 166 |
| HEAPO MqO 2023 | 15.0 | 16 | 18 | 20 | 206 |
| WPuQ 2019 | 12.0 | 55 | 33 | 18 | 155 |
| WPuQ 2019 | 15.0 | 21 | 23 | 27 | 190 |
| FeederBW 2024 (feeder-mean T) | 12.0 | 67 | 35 | 14 | 146 |
| FeederBW 2024 (feeder-mean T) | 15.0 | 31 | 21 | 20 | 190 |

## M5 Hockey-stick fits (legacy settings: heating_season_thresh = T_base 12 CH / 15 DE, >= 20 days)

| set | reduction | fits | failed / <20 days | at lower bound 8 | at upper bound 20 | T_bal > max observed T (hinge outside data) | median T_bal | median max T |
|---|---|---|---|---|---|---|---|---|
| HEAPO legacy | min/max | 2160 | 0 | 25 | 57 | 1990 | 12.96 | 11.9 |
| HEAPO legacy | mean/mean | 2160 | 0 | 9 | 45 | 1974 | 12.74 | 11.9 |
| WPuQ synthetic | min/max | 400 | 0 | 1 | 1 | 22 | 12.17 | 14.8 |
| WPuQ synthetic | mean/mean | 400 | 0 | 1 | 2 | 57 | 13.47 | 14.97 |

## M6 Zero targets (MAPE excludes them)

| dataset | split | HP_Peak == 0 |
|---|---|---|
| HEAPO legacy | test | 0 of 1080 |
| HEAPO legacy | train | 0 of 1080 |
| WPuQ synthetic | transfer | 24 of 400 |

## M7 FeederBW metadata

| quantity | value |
|---|---|
| feeders in metadata | 200 |
| metadata date range | 2023-04-01 .. 2025-03-25 |
| feeders with a 2024 metadata row | 159 |
| feeders whose target falls back to a non-2024 row | 41 |
| feeders flagged elecheat_stable = False (start vs end 2024) | 54 |
|   of which only because no 2024 row (end missing) | 37 |
| feeders whose electric-heating kW changes over the full period | 43 |
| feeders whose HP kW changes over the full period | 41 |

## M9 Flags on HP members (their own non-HP load enters Total_Load)

| pool | n | 1_ewh | 1_hp-add | 2_hp_control | 2_wh_control |
|---|---|---|---|---|---|
| Kaiser paired (dwelling meter) | 26 | 13 | 0.0 | 2.0 | 2.0 |
| Kaiser paired (HP meter) | 26 | 7 | 2.0 | 2.0 | 2.0 |
| HEAPO legacy 57 (survey: DHW by electric water heater) | 57 | 28 (unknown 29) | - | - | - |

## M8 WPuQ raw coverage (HP and household both non-NaN, cal2019)

houses with >= 90 %: 32 of 37; min coverage 22.5 %. The legacy pool keeps 37.
