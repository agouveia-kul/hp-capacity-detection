# Iteration 01 - design envelope

Source: `scripts/audit/design_envelope.py` (config `iter01_pool_audit`), counts from `pool_inventory.py` scans; no load series built. HP_Nameplate_el is marked feasible only with >= 20 nameplate HP households.

## Comparison

| option | HP train | HP test | resolution | max size test p=0.1 | max size test p=0.3 | max size test p=0.5 | max size test p=1.0 | nameplate HP hh (best station-window) | targets |
|---|---|---|---|---|---|---|---|---|---|
| A | 43 | 14 | 15-min | 14 | 14 | 12 | 6 | 2 (1) | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design |
| B | 35 | 12 | 15-min | 120 | 40 | 24 | 12 | 0 (0) | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design |
| B+ | 46 | 16 | 15-min | 160 | 53 | 32 | 16 | 0 (0) | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design |
| B* | 64 | 22 | 15-min | 160 | 53 | 32 | 16 | 1 (1) | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design |
| C | 37 | 12 | 15-min | 114 | 38 | 22 | 11 | 0 (0) | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design |
| D | 55 | 16 | daily | 118 | 39 | 23 | 11 | 37 (14) | HP_Count, s_h, r, P_design |

## Option A

HEAPO 2023 legacy pool (57); fill = other HP households' Other channel; 15-min. Distinct HP households: **train 43 / test 14** (seed 42); fill households: shared with HP pool.

Pool per split / window / station (mean over 20 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | cal2023 | 8jB | 6.0 | 6.0 | 14.0 |
| test | cal2023 | HbsbG | 1.0 | 1.0 | 14.0 |
| test | cal2023 | Hg | 5.0 | 5.0 | 14.0 |
| test | cal2023 | MqO | 2.0 | 2.0 | 14.0 |
| train | cal2023 | 8jB | 20.0 | 20.0 | 43.0 |
| train | cal2023 | HbsbG | 2.0 | 2.0 | 43.0 |
| train | cal2023 | Hg | 16.0 | 16.0 | 43.0 |
| train | cal2023 | MqO | 4.0 | 4.0 | 43.0 |
| train | cal2023 | z6I | 1.0 | 1.0 | 43.0 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | 8jB cal2023 | 20.0 | 43 | 43 | 43 | 40 | 28 | 20 |
| test | 8jB cal2023 | 6.0 | 14 | 14 | 14 | 12 | 8 | 6 |

Saturation at representative cells (test split, best station):

| size | p | n_hp | log10 #HP combos (test) | HP overlap of 2 random subs (n_hp/H) |
|---|---|---|---|---|
| 20 | 0.1 | 2 | infeasible | - |
| 20 | 0.3 | 6 | infeasible | - |
| 20 | 0.5 | 10 | infeasible | - |
| 20 | 1.0 | 20 | infeasible | - |
| 50 | 0.1 | 5 | infeasible | - |
| 50 | 0.3 | 15 | infeasible | - |
| 50 | 0.5 | 25 | infeasible | - |
| 50 | 1.0 | 50 | infeasible | - |
| 100 | 0.1 | 10 | infeasible | - |
| 100 | 0.3 | 30 | infeasible | - |
| 100 | 0.5 | 50 | infeasible | - |
| 100 | 1.0 | 100 | infeasible | - |

Targets:

| target | feasible | HP households |
|---|---|---|
| HP_Peak | yes | 57 |
| HP_CoincPeak | yes | 57 |
| HP_Count | yes | 57 |
| HP_Nameplate_el | no | 2 |
| s_h | yes | 57 |
| r | yes | 57 |
| P_design | yes | 57 |

## Option B

HEAPO 8jB/KLO + Kaiser paired, cal2023; fill = Kaiser clean cal2023; 15-min. Distinct HP households: **train 35 / test 12** (seed 42); fill households: 1306.

Pool per split / window / station (mean over 20 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | cal2023 | KLO | 12.0 | 12.0 | 326.0 |
| train | cal2023 | KLO | 35.0 | 35.0 | 980.0 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | KLO cal2023 | 35.0 | 350 | 175 | 116 | 70 | 50 | 35 |
| test | KLO cal2023 | 12.0 | 120 | 60 | 40 | 24 | 17 | 12 |

Saturation at representative cells (test split, best station):

| size | p | n_hp | log10 #HP combos (test) | HP overlap of 2 random subs (n_hp/H) |
|---|---|---|---|---|
| 20 | 0.1 | 2 | 1.8 | 0.17 |
| 20 | 0.3 | 6 | 3.0 | 0.5 |
| 20 | 0.5 | 10 | 1.8 | 0.83 |
| 20 | 1.0 | 20 | infeasible | - |
| 50 | 0.1 | 5 | 2.9 | 0.42 |
| 50 | 0.3 | 15 | infeasible | - |
| 50 | 0.5 | 25 | infeasible | - |
| 50 | 1.0 | 50 | infeasible | - |
| 100 | 0.1 | 10 | 1.8 | 0.83 |
| 100 | 0.3 | 30 | infeasible | - |
| 100 | 0.5 | 50 | infeasible | - |
| 100 | 1.0 | 100 | infeasible | - |

Targets:

| target | feasible | HP households |
|---|---|---|
| HP_Peak | yes | 47 |
| HP_CoincPeak | yes | 47 |
| HP_Count | yes | 47 |
| HP_Nameplate_el | no | 0 |
| s_h | yes | 47 |
| r | yes | 47 |
| P_design | yes | 47 |

## Option B+

B + Kaiser single-family HP meters without a dwelling meter (their own non-HP load is not observed); 15-min. Distinct HP households: **train 46 / test 16** (seed 42); fill households: 1306.

Pool per split / window / station (mean over 20 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | cal2023 | KLO | 16.0 | 16.0 | 326.0 |
| train | cal2023 | KLO | 46.0 | 46.0 | 980.0 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | KLO cal2023 | 46.0 | 460 | 230 | 153 | 92 | 65 | 46 |
| test | KLO cal2023 | 16.0 | 160 | 80 | 53 | 32 | 22 | 16 |

Saturation at representative cells (test split, best station):

| size | p | n_hp | log10 #HP combos (test) | HP overlap of 2 random subs (n_hp/H) |
|---|---|---|---|---|
| 20 | 0.1 | 2 | 2.1 | 0.12 |
| 20 | 0.3 | 6 | 3.9 | 0.38 |
| 20 | 0.5 | 10 | 3.9 | 0.62 |
| 20 | 1.0 | 20 | infeasible | - |
| 50 | 0.1 | 5 | 3.6 | 0.31 |
| 50 | 0.3 | 15 | 1.2 | 0.94 |
| 50 | 0.5 | 25 | infeasible | - |
| 50 | 1.0 | 50 | infeasible | - |
| 100 | 0.1 | 10 | 3.9 | 0.62 |
| 100 | 0.3 | 30 | infeasible | - |
| 100 | 0.5 | 50 | infeasible | - |
| 100 | 1.0 | 100 | infeasible | - |

Targets:

| target | feasible | HP households |
|---|---|---|
| HP_Peak | yes | 62 |
| HP_CoincPeak | yes | 62 |
| HP_Count | yes | 62 |
| HP_Nameplate_el | no | 0 |
| s_h | yes | 62 |
| r | yes | 62 |
| P_design | yes | 62 |

## Option B*

B+ plus HEAPO 15-min HP households at the other stations (fill = Kaiser clean, any station); cal2023; 15-min. Distinct HP households: **train 64 / test 22** (seed 42); fill households: 1306.

Pool per split / window / station (mean over 20 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | cal2023 | Hg | 4.0 | 4.0 | 326.0 |
| test | cal2023 | KLO | 16.0 | 16.0 | 326.0 |
| test | cal2023 | MqO | 2.0 | 2.0 | 326.0 |
| train | cal2023 | HbsbG | 1.0 | 1.0 | 980.0 |
| train | cal2023 | Hg | 12.0 | 12.0 | 980.0 |
| train | cal2023 | KLO | 46.0 | 46.0 | 980.0 |
| train | cal2023 | MqO | 4.0 | 4.0 | 980.0 |
| train | cal2023 | z6I | 1.0 | 1.0 | 980.0 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | KLO cal2023 | 46.0 | 460 | 230 | 153 | 92 | 65 | 46 |
| test | KLO cal2023 | 16.0 | 160 | 80 | 53 | 32 | 22 | 16 |

Saturation at representative cells (test split, best station):

| size | p | n_hp | log10 #HP combos (test) | HP overlap of 2 random subs (n_hp/H) |
|---|---|---|---|---|
| 20 | 0.1 | 2 | 2.1 | 0.12 |
| 20 | 0.3 | 6 | 3.9 | 0.38 |
| 20 | 0.5 | 10 | 3.9 | 0.62 |
| 20 | 1.0 | 20 | infeasible | - |
| 50 | 0.1 | 5 | 3.6 | 0.31 |
| 50 | 0.3 | 15 | 1.2 | 0.94 |
| 50 | 0.5 | 25 | infeasible | - |
| 50 | 1.0 | 50 | infeasible | - |
| 100 | 0.1 | 10 | 3.9 | 0.62 |
| 100 | 0.3 | 30 | infeasible | - |
| 100 | 0.5 | 50 | infeasible | - |
| 100 | 1.0 | 100 | infeasible | - |

Targets:

| target | feasible | HP households |
|---|---|---|
| HP_Peak | yes | 86 |
| HP_CoincPeak | yes | 86 |
| HP_Count | yes | 86 |
| HP_Nameplate_el | no | 1 |
| s_h | yes | 86 |
| r | yes | 86 |
| P_design | yes | 86 |

## Option C

B + cal2024 household-years (split by household); fill = Kaiser clean same year; 15-min. Distinct HP households: **train 37 / test 12** (seed 42); fill households: 1330.

Pool per split / window / station (mean over 20 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | cal2023 | KLO | 11.4 | 11.4 | 325.8 |
| test | cal2024 | KLO | 6.2 | 6.2 | 251.8 |
| train | cal2023 | KLO | 35.6 | 35.6 | 980.2 |
| train | cal2024 | KLO | 17.8 | 17.8 | 748.2 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | KLO cal2023 | 35.6 | 356 | 178 | 118 | 71 | 50 | 35 |
| test | KLO cal2023 | 11.4 | 114 | 57 | 38 | 22 | 16 | 11 |

Saturation at representative cells (test split, best station):

| size | p | n_hp | log10 #HP combos (test) | HP overlap of 2 random subs (n_hp/H) |
|---|---|---|---|---|
| 20 | 0.1 | 2 | 1.7 | 0.18 |
| 20 | 0.3 | 6 | 2.7 | 0.53 |
| 20 | 0.5 | 10 | 1.0 | 0.88 |
| 20 | 1.0 | 20 | infeasible | - |
| 50 | 0.1 | 5 | 2.7 | 0.44 |
| 50 | 0.3 | 15 | infeasible | - |
| 50 | 0.5 | 25 | infeasible | - |
| 50 | 1.0 | 50 | infeasible | - |
| 100 | 0.1 | 10 | 1.0 | 0.88 |
| 100 | 0.3 | 30 | infeasible | - |
| 100 | 0.5 | 50 | infeasible | - |
| 100 | 1.0 | 100 | infeasible | - |

Targets:

| target | feasible | HP households |
|---|---|---|
| HP_Peak | yes | 49 |
| HP_CoincPeak | yes | 49 |
| HP_Count | yes | 49 |
| HP_Nameplate_el | no | 0 |
| s_h | yes | 49 |
| r | yes | 49 |
| P_design | yes | 49 |

## Option D

HEAPO all stations daily HP (daily file or 15-min aggregated) + Kaiser paired (hp); HEAPO total-only daily + Kaiser 1_hp-in-meter (hp_countonly); fill = Kaiser clean; daily; windows 2023/24 and cal2023. Distinct HP households: **train 55 / test 16** (seed 42); fill households: 1346.

Pool per split / window / station (mean over 20 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | 2023/24 | HbsbG | 0.0 | 7.8 | 313.4 |
| test | 2023/24 | Hg | 0.0 | 77.8 | 313.4 |
| test | 2023/24 | KLO | 5.2 | 145.4 | 313.4 |
| test | 2023/24 | MqO | 0.0 | 1.8 | 313.4 |
| test | 2023/24 | ceOxS | 0.0 | 7.0 | 313.4 |
| test | 2023/24 | sV3mR | 0.0 | 4.0 | 313.4 |
| test | 2023/24 | wDD | 0.0 | 4.0 | 313.4 |
| test | 2023/24 | z6I | 0.0 | 8.7 | 313.4 |
| test | cal2023 | HbsbG | 0.2 | 7.3 | 326.9 |
| test | cal2023 | Hg | 3.5 | 75.9 | 326.9 |
| test | cal2023 | KLO | 11.8 | 155.6 | 326.9 |
| test | cal2023 | MqO | 1.4 | 3.0 | 326.9 |
| test | cal2023 | ceOxS | 0.0 | 6.6 | 326.9 |
| test | cal2023 | sV3mR | 0.0 | 3.8 | 326.9 |
| test | cal2023 | wDD | 0.0 | 2.9 | 326.9 |
| test | cal2023 | z6I | 0.3 | 6.8 | 326.9 |
| train | 2023/24 | HbsbG | 0.0 | 23.2 | 942.6 |
| train | 2023/24 | Hg | 0.0 | 228.2 | 942.6 |
| train | 2023/24 | KLO | 16.8 | 438.6 | 942.6 |
| train | 2023/24 | MqO | 0.0 | 5.4 | 942.6 |
| train | 2023/24 | ceOxS | 0.0 | 20.0 | 942.6 |
| train | 2023/24 | sV3mR | 0.0 | 13.0 | 942.6 |
| train | 2023/24 | wDD | 0.0 | 13.0 | 942.6 |
| train | 2023/24 | z6I | 0.0 | 25.3 | 942.6 |
| train | cal2023 | HbsbG | 0.8 | 20.7 | 979.1 |
| train | cal2023 | Hg | 12.5 | 229.1 | 979.1 |
| train | cal2023 | KLO | 35.2 | 464.4 | 979.1 |
| train | cal2023 | MqO | 4.6 | 10.0 | 979.1 |
| train | cal2023 | ceOxS | 0.0 | 17.4 | 979.1 |
| train | cal2023 | sV3mR | 0.0 | 11.2 | 979.1 |
| train | cal2023 | wDD | 0.0 | 10.1 | 979.1 |
| train | cal2023 | z6I | 0.7 | 19.2 | 979.1 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | KLO cal2023 | 35.2 | 352 | 176 | 117 | 70 | 50 | 35 |
| test | KLO cal2023 | 11.8 | 118 | 59 | 39 | 23 | 16 | 11 |
| train incl. count-only | KLO cal2023 | 464.4 | 1087 | 1223 | 1398 | 928 | 663 | 464 |
| test incl. count-only | KLO cal2023 | 155.6 | 363 | 408 | 467 | 311 | 222 | 155 |

Saturation at representative cells (test split, best station):

| size | p | n_hp | log10 #HP combos (test) | HP overlap of 2 random subs (n_hp/H) |
|---|---|---|---|---|
| 20 | 0.1 | 2 | 1.7 | 0.17 |
| 20 | 0.3 | 6 | 2.7 | 0.51 |
| 20 | 0.5 | 10 | 1.0 | 0.85 |
| 20 | 1.0 | 20 | infeasible | - |
| 50 | 0.1 | 5 | 2.7 | 0.42 |
| 50 | 0.3 | 15 | infeasible | - |
| 50 | 0.5 | 25 | infeasible | - |
| 50 | 1.0 | 50 | infeasible | - |
| 100 | 0.1 | 10 | 1.0 | 0.85 |
| 100 | 0.3 | 30 | infeasible | - |
| 100 | 0.5 | 50 | infeasible | - |
| 100 | 1.0 | 100 | infeasible | - |

Targets:

| target | feasible | HP households |
|---|---|---|
| HP_Peak | no | 71 |
| HP_CoincPeak | no | 71 |
| HP_Count | yes | 1099 |
| HP_Nameplate_el | no | 37 |
| s_h | yes | 71 |
| r | yes | 71 |
| P_design | yes | 71 |

## Proposal grid (configs/protocol_v1_proposal.yaml: sizes [10, 20, 40, 80, 120], p [0.05, 0.1, 0.2, 0.3, 0.5, 1.0], keep n_hp <= 0.75 x H, >= 3 HP per station)

| option | split | window | station | H | cells kept | substations |
|---|---|---|---|---|---|---|
| B* | test | cal2023 | Hg | 4 | 7 | 35 |
| B* | test | cal2023 | KLO | 16 | 19 | 95 |
| B* | train | cal2023 | Hg | 12 | 15 | 150 |
| B* | train | cal2023 | KLO | 46 | 24 | 240 |
| B* | train | cal2023 | MqO | 4 | 7 | 70 |
| D (submetered) | test | 2023/24 | KLO | 5 | 7 | 35 |
| D (submetered) | test | cal2023 | Hg | 3 | 6 | 30 |
| D (submetered) | test | cal2023 | KLO | 11 | 15 | 75 |
| D (submetered) | train | 2023/24 | KLO | 16 | 19 | 190 |
| D (submetered) | train | cal2023 | Hg | 12 | 15 | 150 |
| D (submetered) | train | cal2023 | KLO | 35 | 24 | 240 |
| D (submetered) | train | cal2023 | MqO | 4 | 7 | 70 |

Total substations per split seed: B* test: 130, B* train: 460, D (submetered) test: 140, D (submetered) train: 650
