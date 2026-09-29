# Iteration 01 - design envelope

Source: `scripts/audit/design_envelope.py` (config `iter01_pool_audit_quick`), counts from `pool_inventory.py` scans; no load series built. HP_Nameplate_el is marked feasible only with >= 20 nameplate HP households.

## Comparison

| option | HP train | HP test | resolution | max size test p=0.1 | max size test p=0.3 | max size test p=0.5 | max size test p=1.0 | nameplate HP hh (best station-window) | targets |
|---|---|---|---|---|---|---|---|---|---|
| A | 43.0 | 14.0 | 15-min | 14.0 | 14.0 | 12.0 | 6.0 | 2 (1) | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design |
| B | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| B+ | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| B* | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| C | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| D | 1.0 | 0.0 | daily | 3.0 | 1.0 | 0.0 | 0.0 | 2 (1) | HP_Count, s_h, r, P_design |

## Option A

HEAPO 2023 legacy pool (57); fill = other HP households' Other channel; 15-min. Distinct HP households: **train 43 / test 14** (seed 42); fill households: shared with HP pool.

Pool per split / window / station (mean over 3 split seeds):

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

HEAPO 8jB/KLO + Kaiser paired, cal2023; fill = Kaiser clean cal2023; 15-min. **No HP households in this pool.**

## Option B+

B + Kaiser single-family HP meters without a dwelling meter (their own non-HP load is not observed); 15-min. **No HP households in this pool.**

## Option B*

B+ plus HEAPO 15-min HP households at the other stations (fill = Kaiser clean, any station); cal2023; 15-min. **Too few HP households to populate both splits.**

## Option C

B + cal2024 household-years (split by household); fill = Kaiser clean same year; 15-min. **No HP households in this pool.**

## Option D

HEAPO all stations daily HP (daily file or 15-min aggregated) + Kaiser paired (hp); HEAPO total-only daily + Kaiser 1_hp-in-meter (hp_countonly); fill = Kaiser clean; daily; windows 2023/24 and cal2023. Distinct HP households: **train 1 / test 0** (seed 42); fill households: 17.

Pool per split / window / station (mean over 3 split seeds):

| split | window | station | H | H_all | F |
|---|---|---|---|---|---|
| test | 2023/24 | Hg | 0.0 | 1.0 | 4.0 |
| test | 2023/24 | KLO | 0.0 | 3.0 | 4.0 |
| test | 2023/24 | ceOxS | 0.0 | 1.0 | 4.0 |
| test | cal2023 | Hg | 0.3 | 1.0 | 4.0 |
| test | cal2023 | KLO | 0.0 | 3.0 | 4.0 |
| test | cal2023 | ceOxS | 0.0 | 1.0 | 4.0 |
| train | 2023/24 | HbsbG | 0.0 | 1.0 | 13.0 |
| train | 2023/24 | Hg | 0.0 | 3.3 | 13.0 |
| train | 2023/24 | KLO | 0.0 | 8.0 | 13.0 |
| train | 2023/24 | ceOxS | 0.0 | 2.0 | 13.0 |
| train | 2023/24 | z6I | 0.0 | 2.0 | 13.0 |
| train | cal2023 | HbsbG | 0.0 | 1.0 | 13.0 |
| train | cal2023 | Hg | 0.7 | 4.0 | 13.0 |
| train | cal2023 | KLO | 0.0 | 8.0 | 13.0 |
| train | cal2023 | ceOxS | 0.0 | 2.0 | 13.0 |
| train | cal2023 | z6I | 0.0 | 2.0 | 13.0 |

Max feeder size (best station, no household twice):

| split | station/window | H | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=0.7 | p=1.0 |
|---|---|---|---|---|---|---|---|---|
| train | Hg cal2023 | 0.7 | 7 | 3 | 2 | 1 | 1 | 0 |
| test | Hg cal2023 | 0.3 | 3 | 1 | 1 | 0 | 0 | 0 |
| train incl. count-only | KLO 2023/24 | 8.0 | 14 | 16 | 18 | 16 | 11 | 8 |
| test incl. count-only | KLO 2023/24 | 3.0 | 4 | 5 | 5 | 6 | 4 | 3 |

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
| HP_Peak | no | 1 |
| HP_CoincPeak | no | 1 |
| HP_Count | yes | 22 |
| HP_Nameplate_el | no | 2 |
| s_h | yes | 1 |
| r | yes | 1 |
| P_design | yes | 1 |

## Proposal grid (configs/protocol_v1_proposal.yaml: sizes [10, 20, 40, 80, 120], p [0.05, 0.1, 0.2, 0.3, 0.5, 1.0], keep n_hp <= 0.75 x H, >= 3 HP per station)

|  |
|

Total substations per split seed: none (no station reaches the minimum pool)
