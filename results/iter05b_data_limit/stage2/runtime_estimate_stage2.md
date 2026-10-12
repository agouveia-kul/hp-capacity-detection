# 05b Stage 2 runtime estimate from the probe (seed 0 of every arm)

Probe jobs: 43 of 43 done (18.5 job-h); missing (not in the estimate): none.

| arm | probe job-h (seed 0) | remaining job-h, lower | remaining job-h, upper |
|---|---|---|---|
| arm2_cpu | 0.1 | 2.1 | 2.1 |
| arm7_x05 | 1.1 | 3.9 | 9.5 |
| arm7_x15 | 0.8 | 3.0 | 7.3 |
| arm4 | 0.0 | 0.3 | 0.3 |
| arm4_o1 | 0.9 | 17.8 | 17.8 |
| arm4_bstar | 0.1 | 1.4 | 1.4 |
| arm4_bstar_o1a | 0.1 | 1.4 | 1.4 |
| arm4_bstar_o1b | 0.1 | 1.2 | 1.2 |
| arm3_spc10 | 1.0 | 4.2 | 9.4 |
| arm3_spc40 | 8.1 | 57.1 | 73.0 |
| arm5 | 3.2 | 59.8 | 60.0 |
| arm6 | 3.0 | 13.8 | 27.0 |

Remaining Stage 2 at 6 workers (TabPFN at most 3 at once): lower 166 job-h -> 28 h wall (1.2 continuous days, 2.9 nights); upper 211 job-h -> 35 h wall (1.5 continuous days, 3.7 nights).

Lower = feature evaluation and pilot paid once per (arm, design, seed) by the physics job; upper = probe times as measured (some family jobs redid them). Contention as in the probe (6 workers).
