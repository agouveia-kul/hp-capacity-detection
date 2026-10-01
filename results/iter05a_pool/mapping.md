# 05a Task 3 - analog mapping diagnostics (D1-D4; D5 below once the queue has run)

Source: `scripts/paperb/iter05a_report.py --part mapping`, pool `protocol_v1_1` (GB-EoH 2122r2), split seed 0: 2399 train fillers, map seed 0; stations with >= 3 HP homes: 16. Rule: `fill_analog.py` docstring (doy windows [30, 45, 60], tol 1.0 K, k = 3). Pre-registered flags: D1 s0 (a) vs (b) differ > 15 %, or > 5 % of days need |dT| > 1 K; D4 median |ds_h| > 10 % or median |d p99.9| > 10 % at any aggregate size.

## D1 - hockey stick of the train-filler aggregate (per dwelling)

| fit | station | N | s0 (kW/K) | T_h | P_base/N (kW) | r2 |
|---|---|---|---|---|---|---|
| (a) own LCL days vs HadCET | - | 2399 | 0.0115 | 17.6 | 0.334 | 0.843 |
| (b) mapped vs station T | G001 | 2399 | 0.0126 | 15.4 | 0.34 | 0.836 |
| (b) mapped vs station T | G002 | 2399 | 0.0128 | 15.9 | 0.337 | 0.824 |
| (b) mapped vs station T | G005 | 2399 | 0.0138 | 13.9 | 0.349 | 0.83 |
| (b) mapped vs station T | G006 | 2399 | 0.0125 | 15.6 | 0.341 | 0.842 |
| (b) mapped vs station T | G007 | 2399 | 0.0139 | 14.1 | 0.345 | 0.865 |
| (b) mapped vs station T | G008 | 2399 | 0.0122 | 17.3 | 0.333 | 0.812 |
| (b) mapped vs station T | G009 | 2399 | 0.0131 | 15.2 | 0.341 | 0.848 |
| (b) mapped vs station T | G010 | 2399 | 0.0116 | 17.5 | 0.336 | 0.793 |
| (b) mapped vs station T | G011 | 2399 | 0.0113 | 17.9 | 0.332 | 0.793 |
| (b) mapped vs station T | G012 | 2399 | 0.0121 | 16.6 | 0.337 | 0.786 |
| (b) mapped vs station T | G013 | 2399 | 0.0117 | 17 | 0.337 | 0.832 |
| (b) mapped vs station T | G014 | 2399 | 0.013 | 15.1 | 0.343 | 0.804 |
| (b) mapped vs station T | G016 | 2399 | 0.0116 | 17.3 | 0.334 | 0.821 |
| (b) mapped vs station T | G018 | 2399 | 0.0129 | 15.4 | 0.341 | 0.822 |
| (b) mapped vs station T | G021 | 2399 | 0.0117 | 17.2 | 0.335 | 0.824 |
| (b) mapped vs station T | G022 | 2399 | 0.0113 | 18 | 0.334 | 0.818 |
| (b) pooled over stations | 16 stations | 2399 | 0.0122 | 16.3 | 0.337 | 0.816 |

(a) vs pooled (b): +5.9 % -> **flag not raised**; stations beyond 15 %: G005, G007.

## D2 - temperature mismatch |T_London(d') - T_g(d)|

| median |dT| (K) | p95 |dT| (K) | share |dT| > 1 K | worst station share > 1 K |
|---|---|---|---|
| 0.168 | 0.745 | 0.0024 | 0.0164 |

-> **flag not raised**.

## D3 - day-of-year distance, widenings, reuse

| median ddoy | p95 ddoy | max ddoy | days widened to 45 | days widened to 60 | days without a candidate within tol | source days used per station (median) | max uses of one source day | mean uses per used source day | share of (station, day) nearest-T matches that change with HadCET |
|---|---|---|---|---|---|---|---|---|---|
| 16 | 29 | 60 | 59 | 12 | 14 | 246 | 10 | 1.5 | 0.942 |

## D4 - LCL self-test (held-out winter rebuilt from the other LCL days; 50 draws per size)

Relative differences are rebuilt / real - 1; T_h difference in K.

| winter | n | days | share_dT_gt1 | widened | median |rel_d_s_h| | median |d_T_h| | median |rel_d_P_base| | median |rel_d_p999| | median |rel_d_max| | median_ks | median_w_rel | median_rel_d_s_h | median_rel_d_p999 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2012/13 | 10 | 150 | 0.16 | 38 | 0.728 | 4.23 | 0.0577 | 0.0697 | 0.1 | 0.25 | 0.0547 | -0.662 | -0.0468 |
| 2012/13 | 40 | 150 | 0.16 | 38 | 0.533 | 1.12 | 0.0468 | 0.0494 | 0.0691 | 0.263 | 0.0469 | -0.533 | -0.0425 |
| 2012/13 | 120 | 150 | 0.16 | 38 | 0.579 | 1.1 | 0.0443 | 0.056 | 0.0656 | 0.283 | 0.0402 | -0.579 | -0.056 |
| 2013/14 | 10 | 119 | 0 | 1 | 0.998 | 0.734 | 0.0861 | 0.072 | 0.0816 | 0.256 | 0.0574 | -0.0667 | 0.0166 |
| 2013/14 | 40 | 119 | 0 | 1 | 0.468 | 0.649 | 0.0377 | 0.0369 | 0.0564 | 0.252 | 0.0316 | 0.276 | 0.0138 |
| 2013/14 | 120 | 119 | 0 | 1 | 0.304 | 0.265 | 0.0167 | 0.0323 | 0.0444 | 0.231 | 0.0256 | 0.249 | 0.0264 |

-> **flag RAISED**.


## D5 - B* swap test (swapped - real, WAPE pp; median over 10 seeds)

Source: `scripts/paperb/iter05a_report.py --part d5` on `results/iter05a_pool/overnight/d5_{real,swap}/`. Pre-registered flag: |median dWAPE| > 2 pp for any physics row or family winner, overall or in any bin.

### Physics rows

| key | all | pbin<=15 | pbin15-35 | pbin35-65 | pbin>65 |
|---|---|---|---|---|---|
| calibrated_delta|none|-|-|- | 1.89 | 4.13 | 0.91 | -0.29 | -0.28 |
| hdh|none|-|-|- | 1.69 | 2.99 | 0.78 | -0.52 | 0.13 |
| paperA_cal|none|-|-|- | 1.03 | -0.06 | 1.04 | 0.01 | 1.63 |
| paperA_corr_cal|none|-|-|- | -0.73 | -0.34 | -1.89 | -1.69 | 0 |
| paperA_corr|none|-|-|- | -7.26 | -5.37 | -8.28 | -7.54 | -7.13 |
| paperA_sh_mh|none|-|-|- | -11.2 | -13.7 | -10.6 | -10.9 | -8.14 |
| slope_base|none|-|-|- | -0.16 | -0.37 | 0.36 | -0.26 | -0.28 |
| slope_only|none|-|-|- | 1.33 | 1.91 | 0.69 | -0.09 | -1.15 |

### Family winners (inner-CV WAPE per seed and arm)

| family | all | pbin<=15 | pbin15-35 | pbin35-65 | pbin>65 |
|---|---|---|---|---|---|
| kernel | -0.71 | 0.33 | 1.59 | 2 | -0.65 |
| linear | -0.33 | 0.12 | -1 | 1.53 | 1.79 |
| neural | -0.42 | -0.68 | 2.6 | -2.39 | 1.48 |
| trees | -0.74 | 1.58 | 0.74 | -0.79 | -0.74 |

-> **flag RAISED**.

### Median P_hat / y by grid penetration (physics rows)

| method | p_grid | d5_real | d5_swap | change |
|---|---|---|---|---|
| calibrated_delta | 0.05 | 1.6 | 1.64 | 0.042 |
| calibrated_delta | 0.1 | 1.22 | 1.23 | 0.006 |
| calibrated_delta | 0.2 | 1.05 | 1.05 | 0.008 |
| calibrated_delta | 0.3 | 0.996 | 1.02 | 0.02 |
| calibrated_delta | 0.5 | 0.996 | 0.991 | -0.005 |
| calibrated_delta | 0.8 | 0.933 | 0.948 | 0.015 |
| calibrated_delta | 1 | 0.909 | 0.931 | 0.022 |
| hdh | 0.05 | 1.38 | 1.36 | -0.022 |
| hdh | 0.1 | 1.1 | 1.09 | -0.006 |
| hdh | 0.2 | 0.943 | 0.941 | -0.002 |
| hdh | 0.3 | 0.947 | 0.921 | -0.026 |
| hdh | 0.5 | 0.965 | 0.94 | -0.024 |
| hdh | 0.8 | 0.916 | 0.922 | 0.005 |
| hdh | 1 | 0.901 | 0.924 | 0.024 |
| paperA_cal | 0.05 | 1.44 | 1.43 | -0.01 |
| paperA_cal | 0.1 | 1.09 | 1.1 | 0.012 |
| paperA_cal | 0.2 | 0.951 | 0.936 | -0.015 |
| paperA_cal | 0.3 | 0.922 | 0.92 | -0.002 |
| paperA_cal | 0.5 | 0.905 | 0.879 | -0.026 |
| paperA_cal | 0.8 | 0.845 | 0.832 | -0.013 |
| paperA_cal | 1 | 0.851 | 0.855 | 0.003 |
| paperA_corr | 0.05 | 1.16 | 1.01 | -0.142 |
| paperA_corr | 0.1 | 1.1 | 1 | -0.097 |
| paperA_corr | 0.2 | 1.13 | 1.04 | -0.088 |
| paperA_corr | 0.3 | 1.17 | 1.07 | -0.094 |
| paperA_corr | 0.5 | 1.22 | 1.1 | -0.121 |
| paperA_corr | 0.8 | 1.18 | 1.06 | -0.125 |
| paperA_corr | 1 | 1.2 | 1.09 | -0.105 |
| paperA_corr_cal | 0.05 | 1.11 | 1.06 | -0.047 |
| paperA_corr_cal | 0.1 | 1.07 | 1.07 | -0 |
| paperA_corr_cal | 0.2 | 1.1 | 1.1 | 0.006 |
| paperA_corr_cal | 0.3 | 1.14 | 1.13 | -0.015 |
| paperA_corr_cal | 0.5 | 1.19 | 1.17 | -0.02 |
| paperA_corr_cal | 0.8 | 1.14 | 1.13 | -0.01 |
| paperA_corr_cal | 1 | 1.16 | 1.17 | 0.01 |
| paperA_sh_mh | 0.05 | 2.1 | 1.91 | -0.188 |
| paperA_sh_mh | 0.1 | 1.6 | 1.49 | -0.111 |
| paperA_sh_mh | 0.2 | 1.39 | 1.27 | -0.119 |
| paperA_sh_mh | 0.3 | 1.33 | 1.23 | -0.1 |
| paperA_sh_mh | 0.5 | 1.3 | 1.19 | -0.115 |
| paperA_sh_mh | 0.8 | 1.24 | 1.12 | -0.118 |
| paperA_sh_mh | 1 | 1.23 | 1.13 | -0.101 |
| slope_base | 0.05 | 1.19 | 1.16 | -0.028 |
| slope_base | 0.1 | 1.08 | 1.07 | -0.001 |
| slope_base | 0.2 | 1.04 | 1.05 | 0.015 |
| slope_base | 0.3 | 1.03 | 1.07 | 0.04 |
| slope_base | 0.5 | 1.05 | 1.09 | 0.042 |
| slope_base | 0.8 | 1 | 1.05 | 0.042 |
| slope_base | 1 | 1.02 | 1.06 | 0.047 |
| slope_only | 0.05 | 1.32 | 1.31 | -0.009 |
| slope_only | 0.1 | 1.07 | 1.05 | -0.015 |
| slope_only | 0.2 | 0.93 | 0.926 | -0.004 |
| slope_only | 0.3 | 0.95 | 0.93 | -0.02 |
| slope_only | 0.5 | 0.964 | 0.952 | -0.012 |
| slope_only | 0.8 | 0.915 | 0.92 | 0.006 |
| slope_only | 1 | 0.939 | 0.943 | 0.004 |

### Every spec

| key | all | pbin<=15 | pbin15-35 | pbin35-65 | pbin>65 |
|---|---|---|---|---|---|
| ElasticNet|size_peak|both|direct|log | 0.81 | -0.93 | -1.57 | 1.74 | -2.96 |
| ElasticNet|size_peak|both|residual|log | -0.01 | -0.58 | -0.18 | 3.46 | 2.61 |
| ElasticNet|size_peak|netfit|direct|log | -0.41 | -0.76 | 0.01 | 0.39 | -3.73 |
| ElasticNet|size_peak|netfit|residual|log | 1.3 | 1.03 | 1.76 | 0.84 | 0.92 |
| ElasticNet|size|both|direct|log | -1.05 | -1.56 | -0.43 | -1.54 | -4.03 |
| ElasticNet|size|both|residual|log | -0.01 | -0.39 | -0.18 | 3.46 | 2.61 |
| ElasticNet|size|netfit|direct|log | -1.43 | -1.92 | 0.49 | 0.18 | -3.83 |
| ElasticNet|size|netfit|residual|log | 1.13 | 1.02 | 1.7 | 0.79 | 0.75 |
| FFNN|size_peak|both|direct|log | 2.36 | 2.41 | -0.66 | 0.11 | -0.45 |
| FFNN|size_peak|netfit|direct|log | 1.57 | -0.55 | 1.82 | 1.28 | -1.36 |
| FFNN|size|both|direct|log | 4.38 | 3.25 | -0.67 | 0.91 | 8.97 |
| FFNN|size|netfit|direct|log | 1 | 0.1 | 1.46 | -0.76 | 2.92 |
| Lasso|size_peak|both|direct|log | -0.09 | -1.71 | -0.78 | 1.57 | -1.67 |
| Lasso|size_peak|both|residual|log | -1.5 | -1.78 | -1.55 | 1.63 | 1.83 |
| Lasso|size_peak|netfit|direct|log | -0.01 | 0.84 | 0.19 | 1.5 | -2.13 |
| Lasso|size_peak|netfit|residual|log | 1.31 | 0.91 | 1.76 | 1.09 | 0.88 |
| Lasso|size|both|direct|log | -1 | -2.93 | -0.27 | -0.19 | -1.65 |
| Lasso|size|both|residual|log | -1.49 | -1.78 | -1.55 | 1.65 | 1.83 |
| Lasso|size|netfit|direct|log | -0.43 | -0.3 | -0.24 | 2.13 | -4.67 |
| Lasso|size|netfit|residual|log | 1.23 | 0.78 | 1.73 | 0.95 | 0.96 |
| Linear|size_peak|both|direct|log | -0.1 | -0.37 | -2.77 | -2.78 | 10.2 |
| Linear|size_peak|netfit|direct|log | 1.19 | -2.33 | 4 | -0.56 | 3.8 |
| Linear|size|both|direct|log | -0.02 | -0.79 | -1.8 | -3.2 | 10.1 |
| Linear|size|netfit|direct|log | 1.06 | -0.76 | -0.58 | 2.78 | 4.68 |
| PLS|size_peak|both|direct|log | -1 | -0.55 | -2.23 | 1.26 | 2.71 |
| PLS|size_peak|netfit|direct|log | -0.44 | -1.18 | -0.87 | 1.76 | -1.45 |
| PLS|size|both|direct|log | -0.96 | 0.46 | -1.88 | 1.48 | 4.15 |
| PLS|size|netfit|direct|log | -0.34 | -1.01 | 2.17 | 1.14 | -1.76 |
| Ridge|size_peak|both|direct|log | 0.83 | -0.85 | -1.71 | -0.54 | -0.26 |
| Ridge|size_peak|both|residual|log | -1.04 | 0.35 | -1.18 | 1.35 | -2.09 |
| Ridge|size_peak|netfit|direct|log | -0.83 | -0.38 | 0.67 | -0.82 | -5.45 |
| Ridge|size_peak|netfit|residual|log | -0.06 | 0.07 | 0.79 | -1.03 | -2.98 |
| Ridge|size|both|direct|log | 0.43 | -0.58 | -2.32 | -0.25 | 0.25 |
| Ridge|size|both|residual|log | -1.03 | 0.35 | -1.19 | 1.35 | -2.06 |
| Ridge|size|netfit|direct|log | -2.18 | -1.1 | -0.83 | -2.32 | -6.43 |
| Ridge|size|netfit|residual|log | 0.65 | 0.34 | 0.89 | -1.28 | -2.51 |
| SVR|size_peak|both|direct|log | -1.78 | -2.06 | -0.13 | 6.62 | -4.89 |
| SVR|size_peak|netfit|direct|log | 1.04 | -0.78 | 1.75 | 3.51 | 4.07 |
| SVR|size|both|direct|log | 0.48 | -2.58 | 0.86 | 8.19 | -1.86 |
| SVR|size|netfit|direct|log | 1.17 | 0.99 | 2.38 | 4.65 | 1.63 |
| XGBoost|size_peak|both|direct|log | -0.68 | -1.01 | 2.04 | -0.74 | -1.4 |
| XGBoost|size_peak|both|residual|log | -0.94 | 0.14 | 1.17 | -1.23 | -2.8 |
| XGBoost|size_peak|netfit|direct|log | -0.65 | 0.07 | 0.42 | -1.54 | -0.31 |
| XGBoost|size_peak|netfit|residual|log | -1.5 | -1.55 | -1.54 | -1.29 | -3 |
| XGBoost|size|both|direct|log | 0.57 | 1.7 | 2.32 | -0.83 | -2.34 |
| XGBoost|size|both|residual|log | -0.78 | 0.65 | -0.19 | -0.81 | -4.17 |
| XGBoost|size|netfit|direct|log | -1.18 | -0.84 | -1.93 | -0.27 | -0.73 |
| XGBoost|size|netfit|residual|log | -0.48 | -1.06 | -0.26 | -1.58 | -1.49 |
| anchor_only_Linear|peak|-|direct|none | 3.36 | 2.6 | 0.45 | 4.17 | 6.66 |
| anchor_only_Linear|size+peak|-|direct|none | 1.96 | 2.51 | -0.85 | -3.07 | -2.09 |
| anchor_only_Linear|size|-|direct|none | 0 | 0 | 0 | 0 | 0 |
| anchor_only_XGBoost|peak|-|direct|none | 2.12 | 2.96 | -0.03 | 0.03 | 5.02 |
| anchor_only_XGBoost|size+peak|-|direct|none | 3.27 | 3.78 | -2.9 | 2.02 | 3.27 |
| anchor_only_XGBoost|size|-|direct|none | 0 | 0 | 0 | 0 | 0 |
| calibrated_delta|none|-|-|- | 1.89 | 4.13 | 0.91 | -0.29 | -0.28 |
| hdh|none|-|-|- | 1.69 | 2.99 | 0.78 | -0.52 | 0.13 |
| paperA_cal|none|-|-|- | 1.03 | -0.06 | 1.04 | 0.01 | 1.63 |
| paperA_corr_cal|none|-|-|- | -0.73 | -0.34 | -1.89 | -1.69 | 0 |
| paperA_corr|none|-|-|- | -7.26 | -5.37 | -8.28 | -7.54 | -7.13 |
| paperA_sh_mh|none|-|-|- | -11.2 | -13.7 | -10.6 | -10.9 | -8.14 |
| slope_base|none|-|-|- | -0.16 | -0.37 | 0.36 | -0.26 | -0.28 |
| slope_only|none|-|-|- | 1.33 | 1.91 | 0.69 | -0.09 | -1.15 |

