# 05a Task 4 - envelopes under protocol v1.1

Source: `scripts/paperb/envelopes_v11.py`; the real generator on 20 split seeds, grid of `configs/protocol_v1_1.yaml` (sizes x p in {0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0}). Median (min-max over seeds). Target: >= 20 test substations in every Paper A bin.

## B* (cal2023, 15 min)

HP households in the pool: 86; stations: 5.

| quantity | median | min | max |
|---|---|---|---|
| HP train (pool) | 64 | 64 | 64 |
| HP test (pool) | 22 | 22 | 22 |
| dropped cells | 605 | 605 | 605 |
| HP train used | 62 | 62 | 62 |
| train substations | 500 | 500 | 500 |
| HP test used | 20 | 20 | 20 |
| test substations | 135 | 135 | 135 |
| test n, p <=15 % | 75 | 75 | 75 |
| test n, p 15-35 % | 40 | 40 | 40 |
| test n, p 35-65 % | 10 | 10 | 10 |
| test n, p >65 % | 10 | 10 | 10 |

Bins with fewer than 20 test substations in the worst seed: ['35-65 %', '>65 %']; in the median seed: ['35-65 %', '>65 %'].

## GB-EoH 2021/22 main (Nov 2021 - Oct 2022)

HP households in the pool: 385; stations: 26.

| quantity | median | min | max |
|---|---|---|---|
| HP train (pool) | 293 | 293 | 293 |
| HP test (pool) | 92 | 92 | 92 |
| dropped cells | 3.46e+03 | 3.46e+03 | 3.46e+03 |
| HP train used | 275 | 275 | 275 |
| train substations | 2.08e+03 | 2.08e+03 | 2.08e+03 |
| HP test used | 81 | 81 | 81 |
| test substations | 455 | 455 | 455 |
| test n, p <=15 % | 265 | 265 | 265 |
| test n, p 15-35 % | 125 | 125 | 125 |
| test n, p 35-65 % | 30 | 30 | 30 |
| test n, p >65 % | 35 | 35 | 35 |

Bins with fewer than 20 test substations in the worst seed: none; in the median seed: none.

## GB-EoH replication as written (= main window)

HP households in the pool: 388; stations: 26.

| quantity | median | min | max |
|---|---|---|---|
| HP train (pool) | 295 | 295 | 295 |
| HP test (pool) | 93 | 93 | 93 |
| dropped cells | 3.45e+03 | 3.45e+03 | 3.45e+03 |
| HP train used | 277 | 277 | 277 |
| train substations | 2.08e+03 | 2.08e+03 | 2.08e+03 |
| HP test used | 82 | 82 | 82 |
| test substations | 455 | 455 | 455 |
| test n, p <=15 % | 265 | 265 | 265 |
| test n, p 15-35 % | 125 | 125 | 125 |
| test n, p 35-65 % | 30 | 30 | 30 |
| test n, p >65 % | 35 | 35 | 35 |

Bins with fewer than 20 test substations in the worst seed: none; in the median seed: none.

## GB-EoH replication, latest start (Sep 2022 - Aug 2023)

HP households in the pool: 338; stations: 26.

| quantity | median | min | max |
|---|---|---|---|
| HP train (pool) | 256 | 256 | 256 |
| HP test (pool) | 82 | 82 | 82 |
| dropped cells | 3.47e+03 | 3.47e+03 | 3.47e+03 |
| HP train used | 239 | 239 | 239 |
| train substations | 1.96e+03 | 1.96e+03 | 1.96e+03 |
| HP test used | 66 | 66 | 66 |
| test substations | 385 | 385 | 385 |
| test n, p <=15 % | 215 | 215 | 215 |
| test n, p 15-35 % | 110 | 110 | 110 |
| test n, p 35-65 % | 30 | 30 | 30 |
| test n, p >65 % | 30 | 30 | 30 |

Bins with fewer than 20 test substations in the worst seed: none; in the median seed: none.

