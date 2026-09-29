# Iteration 00 - legacy facts (computed by `scripts/legacy_facts.py`)

## HP households per pool

| pool | HP households | consumers | per station (HP) |
|---|---|---|---|
| heapo_2023_legacy (data/_regen_prep.pkl) | 57 |  | 8jB: 26; Hg: 21; MqO: 6; HbsbG: 3; z6I: 1 |
| heapo_design (data/_design_pool_cache.pkl) | 57 | 58 | 8jB: 26; Hg: 21; MqO: 6; HbsbG: 3; z6I: 1 |
| swiss_kaiser_paired (data/_swiss_pool_cache.pkl) | 24 | 1644 | KLO: 24 |
| combined (data/_combined_pool_cache.pkl) | 81 | 1702 | KLO: 50; Hg: 21; MqO: 6; HbsbG: 3; z6I: 1 |
| wpuq (data/_wpuq_pool_cache.pkl) | 37 |  | WPUQ: 37 |

**81 vs 57 resolved.** Every legacy capacity result (all 10 scripts) is trained and tested on the **57-household HEAPO 2023 pool** (`data/_regen_prep.pkl`, same HP set as `_design_pool_cache.pkl`). 81 is the HP count of the *combined* HEAPO+Swiss pool (57 + 24), which the legacy capacity scripts never load. Notebook cell 160 ("81-household dataset") is wrong; cell 178 ("57") is right. The "Swiss" in legacy names (`swiss_penetration_sweep`, `capacity_swiss.pkl`, `_X_swiss_pooled.pkl`) means HEAPO (Swiss households), not the Kaiser et al. dataset.

## Split

- `household_pool_split(seed=42, test_frac=0.5)`: train 29 / test 28 HP households.
- per station: train 8jB: 12; Hg: 12; HbsbG: 3; MqO: 1; z6I: 1; test 8jB: 14; Hg: 9; MqO: 5.
- HP households actually used in substations (stations with >= 3 in the split): train 27, test 28.
- fill households used: train 29, test 28.
- train/test overlap (any role): 0; legacy members consistent with the seed-42 split: True.

## Substation design

- substations: train: 1080; test: 1080; sizes 10..120 step 10; penetration 0.1..1.0 step 0.1; 9 replicates per (split, pen, size) cell.
- HP draws: with replacement, from the substation's weather-station pool of the split. Fill draws: with replacement, from the whole split pool (all 57 are HP households; fill contributes their 'Other' channel).
- stations used: train ['8jB', 'HbsbG', 'Hg'], test ['8jB', 'Hg', 'MqO']; substations per station: train Hg: 481; 8jB: 479; HbsbG: 120, test 8jB: 556; Hg: 315; MqO: 209.
- **120-dwelling, 100 %-penetration train substations** (n=9): 10.0 distinct HP profiles on average, so **each HP profile appears 16.7 times** on average.
- substations where a household is both an HP member and a fill member: 1786 of 2160.
- replay of the seed-42 draws reproduces the legacy membership: meta True, members True; HP_Peak recomputed from members, max |diff| = 2.27e-13 kW.

Mean appearances per HP profile (n_hp / distinct), by size:

| size | train | test |
|---|---|---|
| 10 | 1.34 | 1.42 |
| 20 | 1.65 | 1.85 |
| 30 | 2.09 | 2.2 |
| 40 | 2.96 | 2.67 |
| 50 | 3.74 | 3.48 |
| 60 | 3.7 | 3.66 |
| 70 | 4.75 | 4.42 |
| 80 | 4.47 | 4.42 |
| 90 | 5.5 | 5.1 |
| 100 | 6.69 | 6.11 |
| 110 | 6.87 | 6.77 |
| 120 | 8.29 | 6.76 |

Synthetic WPUQ set: 400 substations, sizes [10, 37], 24 with zero HP, with replacement from 37 houses (HP and fill); mean appearances per HP profile 1.07.

## Targets

- HP_Peak quantiles (kW), train: 0.0: 2.8; 0.05: 20.1; 0.25: 62.4; 0.5: 145.5; 0.75: 269.6; 0.95: 503.9; 1.0: 755.2
- HP_Peak quantiles (kW), test: 0.0: 3.6; 0.05: 23.3; 0.25: 79.1; 0.5: 179.7; 0.75: 343.7; 0.95: 595.1; 1.0: 962.1
- mean test HP_Peak by penetration: 0.1: 41.9; 0.2: 86.4; 0.3: 127.7; 0.4: 169.2; 0.5: 212.8; 0.6: 254.7; 0.7: 295.9; 0.8: 329.0; 0.9: 382.0; 1.0: 423.3
- median HP_CoincPeak / HP_Peak over all substations: 0.791
- per-HP robust (q99.9) peak median: HEAPO (57): 4.79; Swiss/Kaiser (24): 5.37; WPUQ (37): 5.98 kW
- real WPUQ feeder HP_Peak: 238.5 kW

## Coverage

| dataset | start | end | note |
|---|---|---|---|
| HEAPO legacy | 2023-01-01 00:00 UTC | 2023-12-31 23:45 UTC | 15 min; household kept if >80% of 2023 rows |
| Swiss/Kaiser pool | 2023-01-01 00:00:00+00:00 | 2023-12-31 23:45:00+00:00 | not used by the 10 legacy capacity scripts |
| WPUQ | 2019-01-01 00:00:00+00:00 | 2019-12-31 23:45:00+00:00 | 2019 only (2020 file unused) |
| FeederBW | - | - | not used by the 10 legacy scripts (only a housing-units printout) |

## HEAPO protocol overlap

- 410 protocol rows; 85 have `Normpoint_ElectricPower`, covering 67 households with a Household_ID.
- of these, **2** are in the 57-household 2023 pool (train 1, test 1).
- for comparison, households in the pool with any `HeatingCapacity` protocol entry: 10.
