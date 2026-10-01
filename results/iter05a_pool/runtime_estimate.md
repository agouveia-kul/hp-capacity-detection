# 05a Task 6 - timing probe, D5 and the 05b runtime estimate

Probe: GB-EoH main window (pool `gb_eoh_2122r2`, before the silent-home exclusion), seed 0, full v1.1 grid (7 penetrations x 5 sizes), feature sets {netfit, both} x anchors {size, size_peak} x {direct-log, residual}, FFNN at the full budget (50 evals, patience 20), 3875 substations. Four jobs ran together (5 workers x 5 threads); the neural job failed at its first attempt (a Windows `os.replace` race on the shared feature cache, fixed) and was rerun alone with 4 threads.

Measured (seconds, seed 0): F 1062, P 441, linear 1884, kernel 275, trees 618, neural 4302 (the physics job, 1302 s, contains F and one P); job wall times kernel 1547, linear 3160, neural 4743, physics 1302, trees 1892.
 One full-size GB-EoH seed, all five 05a families, uncached pilots: 2.82 job-hours.

**D5 as run** (6 workers x 4 threads, 105 jobs, all done, none failed): 1.5 h wall, d5_real 3.22 job-h (0.32 per seed), d5_swap 4.62 job-h. My pre-run estimate of 17 job-hours (B* = 0.3 x GB-EoH) was 2x too high: measured B* = 0.11 x GB-EoH per seed. This ratio is used below.

## 05b estimate (amended brief, A4 reductions applied) at 6 workers

| stage | arm | full-size seeds | job hours | wall h | nights |
|---|---|---|---|---|---|
| 1 | 1 learning curve (GB-EoH main, 10 seeds x (2 draws x 5 n + all); netfit x size) | 39.9 | 53.7 | 8.9 | 0.94 |
| 1 | 2 headline (GB-EoH main, 20 seeds, n = all, full grid) | 20.0 | 85.9 | 14.3 | 1.51 |
| 2 | 7 filler uncertainty (10 seeds x factors 0.5, 1.5) | 20.0 | 85.9 | 14.3 | 1.51 |
| 2 | 4 oracles (GB-EoH 20 seeds, one extra family pass; B* physics only) | 20.2 | 86.7 | 14.5 | 1.52 |
| 2 | 3 households vs substations (10 seeds, n in {62, all} x spc {10, 40}) | 61.3 | 263.3 | 43.9 | 4.62 |
| 2 | 5 B* under v1.1 (20 seeds, full grid) | 2.3 | 9.8 | 1.6 | 0.17 |
| 2 | 6 temporal replication (GB-EoH Oct 2022 - Sep 2023, 10 seeds) | 8.2 | 35.4 | 5.9 | 0.62 |

| stage | job hours | wall h | nights | continuous days |
|---|---|---|---|---|
| 1 | 139.6 | 23.2 | 2.4 | 1.0 |
| 2 | 481.1 | 80.2 | 8.4 | 3.3 |

Stage 1 (arms 1 + 2): 23 h wall = 2.4 nights or 1.0 continuous days. Stage 2 (arms 7, 4, 3, 5, 6): 80 h wall = 8.4 nights or 3.3 continuous days. Without the assumed doubling for the new models: 6.0 nights in total.

Assumptions: cost proportional to the number of substations; the 05b models, the oracles and arm 7's filler scaling are not measured; contention at 6 workers as in the probe; more workers (RAM allows ~10) would shorten it.
