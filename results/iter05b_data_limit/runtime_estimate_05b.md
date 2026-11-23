# 05b runtime estimate from the 05b timing probe

Probe: arm 2 (GB-EoH main, full v1.1 grid, every model x anchors {size, size_peak} x feature sets {netfit, both} x {direct-log, residual}), seed 0, one queue job per family, pilots cached: 27.7 job-hours for one full-size seed. Failed probe jobs (not in the estimate): none. B* = 0.11 x GB-EoH per seed (measured in 05a D5 on the 05a families; not re-measured for the new models).

| queue family | probe job hours (seed 0) | share of a seed | stage 1 job hours |
|---|---|---|---|
| gp | 8.72 | 31% | 239.6 |
| rawseries | 5.47 | 20% | 191.4 |
| catboost | 4.69 | 17% | 129.0 |
| trees | 3.91 | 14% | 107.3 |
| tabpfn | 2.54 | 9% | 69.9 |
| neural | 1.14 | 4% | 31.3 |
| linear | 0.53 | 2% | 14.4 |
| kernel | 0.46 | 2% | 12.7 |
| physics | 0.23 | 1% | 11.3 |

## Arms at 10 workers

| stage | arm | full-size seeds | job hours | wall h | nights |
|---|---|---|---|---|---|
| 1 | 1 learning curve (10 seeds x 2 draws x n in {16, 32, 62, 100, 200}; netfit x size) | 9.1 | 253.2 | 25.3 | 2.67 |
| 1 | 2 headline (20 seeds, n = all, full grid) | 20.0 | 553.8 | 55.4 | 5.83 |
| 2 | 7 filler uncertainty (10 seeds x factors 0.5, 1.5) | 20.0 | 553.8 | 55.4 | 5.83 |
| 2 | 4 oracles (GB-EoH 20 seeds, one extra family pass; B* physics only) | 20.0 | 554.3 | 55.4 | 5.83 |
| 2 | 3 households vs substations (10 seeds, n in {62, all} x spc {10, 40}) | 61.3 | 1697.8 | 169.8 | 17.87 |
| 2 | 5 B* under v1.1 (20 seeds, full grid) | 2.2 | 60.9 | 6.1 | 0.64 |
| 2 | 6 temporal replication (GB-EoH Oct 2022 - Sep 2023, 10 seeds) | 8.2 | 228.4 | 22.8 | 2.4 |

| stage | job hours | wall h | nights | continuous days |
|---|---|---|---|---|
| 1 | 807.0 | 80.7 | 8.5 | 3.4 |
| 2 | 3095.2 | 309.5 | 32.6 | 12.9 |

Stage 1 (arms 1 + 2): 81 h wall = 8.5 nights or 3.4 continuous days; the probe already paid 27.7 of its job-hours. Stage 2: 310 h wall = 32.6 nights or 12.9 continuous days.

Assumptions: cost proportional to the number of substations (the GP is cubic in the train substations and TabPFN's context grows with them, so arm 1 is overestimated for those two and arm 3 at spc 40 underestimated); wall = job hours / workers, although TabPFN runs at most 3 jobs at once; contention as in the probe (9 jobs at once).
