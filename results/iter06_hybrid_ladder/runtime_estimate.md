# 06 runtime estimate from the probe (seed 0 of every arm, draw 0; 6 workers x 3 threads)

Probe: 64 jobs done, 30.1 job-h in 6.2 h of wall time. Groups without a finished probe job (not in the estimate): none.

Job hours of the whole run per arm and family group (probe job x jobs of the group):

| arm | physics | linear | tabpfn | cnn | all |
|---|---|---|---|---|---|
| a_gb | 0.2 | 12.9 | 82.5 | 20.1 | 115.7 |
| a_ch | 0.2 | 3.2 | 22.4 | 36.6 | 62.3 |
| s_gb | 3.9 | 17.8 | 118.3 | 20.9 | 160.8 |
| r_x05 | 1.1 | 0.9 | 9.1 | 4.8 | 15.9 |
| r_x15 | 1.0 | 0.9 | 9.2 | 5.5 | 16.5 |
| r_rep | 0.8 | 0.7 | 3.9 | 4.4 | 9.7 |

Whole run 381 job-h; remaining after the probe 351 job-h, of which TabPFN 227 (at most 3 at once). Wall time at 6 workers: 76 h = 3.1 continuous days = 8.0 nights of 9.5 h.
