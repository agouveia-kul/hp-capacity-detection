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

