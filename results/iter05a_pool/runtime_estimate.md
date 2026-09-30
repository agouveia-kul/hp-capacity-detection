# 05a Task 6 - timing probe and runtime estimate

Probe: GB-EoH 2021/22 (pool `gb_eoh_2122r2`), seed 0, full v1.1 grid (7 penetrations x 5 sizes), feature sets {netfit, both} x anchors {size, size_peak} x {direct-log, residual}, FFNN at the full budget (50 evals, patience 20), 3875 substations. Four jobs ran together (5 workers x 5 threads); the neural job failed at its first attempt (a Windows `os.replace` race on the shared feature cache, fixed) and was rerun alone with 4 threads.

Measured (seconds, seed 0): F 1062, P 441, linear 1884, kernel 275, trees 618, neural 4302 (the physics job, 1302 s, contains F and one P); job wall times kernel 1547, linear 3160, neural 4743, physics 1302, trees 1892.

One full-size GB-EoH seed, all five families: 2.82 job-hours (0.85 h features + pilots + physics, 1.97 h model tuning). The pilot and cross-fit (441 s) are recomputed by every family job: caching it would save 0.49 h per seed (17 %).

## Estimate at 6 workers

| arm | full-size seeds | job hours | wall h | nights |
|---|---|---|---|---|
| D5 real + swap (B*, 10 seeds x 2 arms, 05a families) | 6.0 | 16.9 | 2.8 | 0.3 |
| 05b 1 learning curve (GB-EoH, 10 seeds x (3 draws x 5 n + all); n / 293 each) | 52.0 | 248.7 | 41.4 | 4.36 |
| 05b 2 headline (GB-EoH, 20 seeds, n = all) | 20.0 | 95.7 | 15.9 | 1.68 |
| 05b 3 households vs substations (10 seeds, n in {62, all} x spc {10, 20, 40}) | 84.8 | 405.8 | 67.6 | 7.12 |
| 05b 4 oracles (GB-EoH + B*, 20 seeds each, one extra family pass) | 26.0 | 124.4 | 20.7 | 2.18 |
| 05b 5 B* under v1.1 (20 seeds) | 6.0 | 28.7 | 4.8 | 0.5 |
| 05b 6 replication (GB-EoH 2022/23, 10 seeds) | 8.2 | 39.0 | 6.5 | 0.68 |

05b total: **942 job-hours, 157 h wall, 16.5 nights** (assuming the new 05b models double the tuning cost; without that factor: 9.7 nights). This is above the ~3-night threshold of the brief.

With the first three reductions listed below applied (pilot cached per design, 2 learning-curve draws, arm 3 with spc {10, 40}; FFNN and workers unchanged): 682 job-hours, 114 h wall, **12.0 nights** at 6 workers.

Assumptions: cost proportional to the number of substations; B* = 0.3 x GB-EoH; the 05b models and oracles are not measured; contention at 6 workers is taken as in the probe. Where a reduction would come from (not applied): cache the pilot per (seed, n, draw) design; 2 instead of 3 learning-curve draws; arm 3 with spc {10, 40}; FFNN in the learning curve only at n in {62, all}; more workers (RAM allows ~10).
