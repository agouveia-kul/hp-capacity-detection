# Iteration 07, Task 1 — label harmonisation (labels only; no model, no prediction)

Code: `scripts/paperb/labels_hl.py` (household HL caps), `scripts/paperb/iter07_labels.py` (this audit). Tables:
`labels/label_audit.csv` (per pool × seed × split × bin: median, 5 %, 90 %, n), `labels/household_caps.csv`.
Household caps cache: `data/_paperb/iter07/hl_caps_{bstar,gb_eoh}.parquet`. Memberships = the 06 A-arm ones, rebuilt from the
06 arm configs (test sets: 135 CH and 455 GB substations per seed, as in 06).

## HL, as built
- **Native labels reproduced exactly** before HL is formed: the replayed CH and GB label code gives each household's `hp_peak`
  with max |difference| ≤ 1e-6 kW (86 CH and 384 GB households; asserted in `household_caps`).
- **CH (B\*)**: HL = the 15-min HP submeter averaged to 30 min, on 30-min bins whose two samples are both raw-valid; 99.9th pct.
  Household HL / native: median 0.974, mean 0.939, range 0.652–1.078 (a value above 1 is possible: the percentile is taken on a
  different set of bins).
- **GB-EoH**: HL = P_ws − P_ih at 30 min, clipped at 0, on bins where both are valid (P_ih rescaled like P_ws, valid with ≥ 12 of
  15 two-minute diffs), on P_ws's zero-run-masked valid bins; 99.9th pct.
  - 247 of 384 homes have an immersion channel. On them HL / native has median 0.966, mean 0.909, min 0.317. 57,778 bins (1.4 % of
    their valid P_ws bins) lack P_ih and are left out of HL; 16 homes miss more than 1 %. P_ih exceeds P_ws by more than 0.05 kW
    in 7,640 bins (clipped).
  - 137 homes have no P_ih reading in the window. The data dictionary says a blank immersion field means no immersion heater
    is present, so these get immersion 0 and HL = native.
  - **Cross-check against the property table's `MCS_Immersion` (design annual immersion energy):**

    | | MCS_Immersion = 0 | > 0 |
    |---|---|---|
    | no P_ih channel | 97 | **40** |
    | P_ih channel | 64 | 183 |

    40 homes without a channel have a design immersion load. They may hold an unmetered immersion heater (then their HL is
    overstated), or none in use. They carry 10.3 % of the summed native peak. Giving them the median HL / native of the
    channel-and-MCS > 0 homes (0.958) would lower the GB HL total by 0.46 %. Handling: immersion 0, as the dictionary reads;
    flagged for Alex. **This is not the brief's stop condition:** the channel exists and is usable for 247 homes, and the
    ambiguity is bounded and small.

## c = HL / native (per substation; c_src = the seed's median over its train substations)
Median over seeds [range of the seed medians] (5 %–90 % of the substations, median over seeds).

| pool | cell | c_src (train) | spread | test (not used for mapping) |
|---|---|---|---|---|
| CH | all | 0.942 [0.931, 0.965] | 0.847–0.988 | 0.953 [0.892, 0.973] |
| CH | ≤ 15 % | 0.947 [0.938, 0.972] | 0.835–0.995 | 0.959 |
| CH | 15–35 % | 0.944 [0.925, 0.958] | 0.866–0.981 | 0.944 |
| CH | 35–65 % | 0.943 [0.928, 0.960] | 0.888–0.971 | 0.951 |
| CH | > 65 % | 0.937 [0.924, 0.965] | 0.896–0.965 | 0.952 |
| GB | all | 0.955 [0.953, 0.958] | 0.776–1.000 | 0.959 [0.942, 0.976] |
| GB † | ≤ 15 % | 0.966 [0.962, 0.971] | 0.723–1.000 | 0.969 |
| GB † | 15–35 % | 0.951 [0.947, 0.956] | 0.799–1.000 | 0.955 |
| GB † | 35–65 % | 0.946 [0.942, 0.950] | 0.819–0.990 | 0.954 |
| GB | > 65 % | 0.950 [0.943, 0.956] | 0.856–0.982 | 0.956 |

The definitional shift is about 4–6 % of `HP_Peak` in both pools, with the same sign: CH loses the 15→30-min averaging, GB the
immersion. Under the headline mapping a CH model's prediction is scaled by ≈ 0.94, a GB model's by ≈ 0.955. † = the
filler-variability-limited GB bins (05a D4).

## CH 30/15-min net-aggregate peak ratio (train substations; input shift for `size_peak`, reported, not corrected)
Median 0.944 [seed range 0.939–0.949]; 5 %–90 % 0.862–0.983; by bin 0.944 / 0.945 / 0.944 / 0.950 (≤ 15 / 15–35 / 35–65 / > 65 %).
A CH `size_peak` model applied to GB therefore sees a peak about 5.5 % lower than its training peaks for the same aggregate.
`size_peak`-anchored CH rung winners (the models applied CH→GB; persisted manifests, seeds 0–9), flagged in every table:

| rung | linear | TabPFN | CNN |
|---|---|---|---|
| L1 | 10 | 10 | 3 |
| L2 | 8 | 3 | 4 |
| L3 | 3 | 2 | 2 |
| L4 (persisted; L4a refits set in Task 3) | 4 | 3 | 2 |

GB→CH gets no such shift: the CH target aggregates are rebuilt at 30 min, the GB models' training resolution.

## GB immersion share of HP_Peak (1 − HL / native; substation level)
Train, median over seeds: all 4.5 % (5–90 %: 0–17.4 %); ≤ 15 % 3.4 %, 15–35 % 4.9 %, 35–65 % 5.5 %, > 65 % 5.0 %.
Test: all 4.2 %; 3.1 / 4.5 / 4.6 / 4.4 %.
