# 05a Task 3 - analog mapping diagnostics (D1-D4; D5 below once the queue has run)

Source: `scripts/paperb/iter05a_report.py --part mapping`, pool `protocol_v1_1` (GB-EoH 2122), split seed 0: 2399 train fillers, map seed 0; stations with >= 3 HP homes: 15. Rule: `fill_analog.py` docstring (doy windows [30, 45, 60], tol 1.0 K, k = 3). Pre-registered flags: D1 s0 (a) vs (b) differ > 15 %, or > 5 % of days need |dT| > 1 K; D4 median |ds_h| > 10 % or median |d p99.9| > 10 % at any aggregate size.

## D1 - hockey stick of the train-filler aggregate (per dwelling)

| fit | station | N | s0 (kW/K) | T_h | P_base/N (kW) | r2 |
|---|---|---|---|---|---|---|
| (a) own LCL days vs HadCET | - | 2399 | 0.0127 | 15.4 | 0.337 | 0.847 |
| (b) mapped vs station T | G001 | 2399 | 0.0133 | 14.2 | 0.343 | 0.831 |
| (b) mapped vs station T | G002 | 2399 | 0.0132 | 14.9 | 0.338 | 0.802 |
| (b) mapped vs station T | G005 | 2399 | 0.0142 | 13.5 | 0.341 | 0.846 |
| (b) mapped vs station T | G006 | 2399 | 0.0133 | 14.2 | 0.343 | 0.814 |
| (b) mapped vs station T | G007 | 2399 | 0.0144 | 13.1 | 0.346 | 0.857 |
| (b) mapped vs station T | G008 | 2399 | 0.0126 | 15.9 | 0.335 | 0.809 |
| (b) mapped vs station T | G009 | 2399 | 0.0134 | 14 | 0.343 | 0.841 |
| (b) mapped vs station T | G010 | 2399 | 0.012 | 16.7 | 0.333 | 0.802 |
| (b) mapped vs station T | G011 | 2399 | 0.0122 | 16.2 | 0.336 | 0.801 |
| (b) mapped vs station T | G012 | 2399 | 0.0127 | 15.7 | 0.333 | 0.811 |
| (b) mapped vs station T | G013 | 2399 | 0.0122 | 16.2 | 0.335 | 0.843 |
| (b) mapped vs station T | G014 | 2399 | 0.0136 | 14.6 | 0.339 | 0.821 |
| (b) mapped vs station T | G016 | 2399 | 0.013 | 15.3 | 0.337 | 0.842 |
| (b) mapped vs station T | G018 | 2399 | 0.0137 | 14.2 | 0.341 | 0.827 |
| (b) mapped vs station T | G021 | 2399 | 0.0121 | 16 | 0.336 | 0.824 |
| (b) pooled over stations | 15 stations | 2399 | 0.0128 | 15.2 | 0.337 | 0.819 |

(a) vs pooled (b): +0.7 % -> **flag not raised**; stations beyond 15 %: none.

## D2 - temperature mismatch |T_London(d') - T_g(d)|

| median |dT| (K) | p95 |dT| (K) | share |dT| > 1 K | worst station share > 1 K |
|---|---|---|---|
| 0.157 | 0.778 | 0.0113 | 0.0273 |

-> **flag not raised**.

## D3 - day-of-year distance, widenings, reuse

| median ddoy | p95 ddoy | max ddoy | days widened to 45 | days widened to 60 | days without a candidate within tol | source days used per station (median) | max uses of one source day | mean uses per used source day |
|---|---|---|---|---|---|---|---|---|
| 15 | 29 | 60 | 64 | 27 | 62 | 245 | 8 | 1.5 |

## D4 - LCL self-test (held-out winter rebuilt from the other LCL days; 50 draws per size)

Relative differences are rebuilt / real - 1; T_h difference in K.

| winter | n | days | share_dT_gt1 | widened | median |rel_d_s_h| | median |d_T_h| | median |rel_d_P_base| | median |rel_d_p999| | median |rel_d_max| | median_ks | median_w_rel | median_rel_d_s_h | median_rel_d_p999 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2012/13 | 10 | 150 | 0.227 | 39 | 0.668 | 2.61 | 0.0663 | 0.0805 | 0.122 | 0.253 | 0.0552 | -0.64 | -0.0624 |
| 2012/13 | 40 | 150 | 0.227 | 39 | 0.577 | 0.732 | 0.0781 | 0.0527 | 0.0726 | 0.273 | 0.0422 | -0.577 | -0.0485 |
| 2012/13 | 120 | 150 | 0.227 | 39 | 0.602 | 0.749 | 0.0578 | 0.0653 | 0.0838 | 0.287 | 0.0361 | -0.602 | -0.0653 |
| 2013/14 | 10 | 119 | 0 | 1 | 0.993 | 1.04 | 0.0746 | 0.077 | 0.0682 | 0.244 | 0.0541 | 0.596 | 0.041 |
| 2013/14 | 40 | 119 | 0 | 1 | 0.842 | 0.671 | 0.0539 | 0.0453 | 0.0564 | 0.252 | 0.0331 | 0.842 | 0.0175 |
| 2013/14 | 120 | 119 | 0 | 1 | 0.69 | 0.435 | 0.0374 | 0.0358 | 0.0432 | 0.231 | 0.0252 | 0.69 | 0.0304 |

-> **flag RAISED**.

