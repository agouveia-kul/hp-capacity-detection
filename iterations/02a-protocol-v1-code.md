# Iteration 02a — Protocol v1: code and tests (no results)

**Branch:** `iter/02a-protocol-v1`. Branch from `main` if iterations 00 and 01 are merged; otherwise branch from `iter/01-pool-audit` and say so in REVIEW.md.
**Type:** implementation plus tests. It includes a smoke run only; **no benchmark results are interpreted** (that is iteration 02b).
**Size budget:** ~700 logic lines, excluding tests. If you exceed it, stop after Tasks 1–4 plus their tests, write the REVIEW for "02a-i", and wait.

## Decisions this iteration implements (Alex, 2026-09-29)
1. **Pool:** B\* is the main 15-min arm (86 HP households, cal2023, including the 15 Kaiser SFH HP meters paired with an unused clean dwelling). B (KLO-only, 47) is a sensitivity arm. C is not adopted; cal2024 is reserved for RQ4.
2. **Daily arm:** yes, as a secondary arm. It is **built in iteration 03**, not here. `HP_Nameplate_el` leaves the substation benchmark and becomes a household-level check (nameplate / observed peak distribution).
3. **Fixes now:** F1, F2, F12, F13, F14. Defer F3–F8 to 03, and F10/F11 to the transfer iteration.
4. **Split:** 02a is code (this file); 02b reruns the benchmark.

## Task 0 — Bookkeeping (first commit)
- **Version-control the contract.** Remove `CLAUDE.md` (and any pattern that catches `iterations/` or `DECISIONS.md`) from `.gitignore`. Commit CLAUDE.md **with** the local §2/§3/§10 edits from iteration 01. Find out why it was ignored (a global gitignore? the repo `.gitignore`?) and report it.
- **Do not drop `stash@{0}`.** List its contents in REVIEW.md so Alex can decide what to do with it.
- **Update `DECISIONS.md`** with the four decisions above.
- **Update CLAUDE.md:**
  - §4: "Protocol v1 is official: `configs/protocol_v1.yaml`."
  - §5: add `HP_Nameplate_el` = household-level only.
  - §10: mark F1/F2/F12/F13/F14 as "fixed in 02a" once their tests pass.

## Task 1 — `configs/protocol_v1.yaml`
Turn `protocol_v1_proposal.yaml` into the approved config. It must contain:
- the pool option (`bstar` | `b`);
- the calendar year (2023);
- a 75/25 household-disjoint split stratified by station, with 20 split seeds;
- the size × penetration grid capped by the design envelope;
- substations per cell;
- K = 4 grouped inner folds for tuning;
- a household-cluster bootstrap with B = 2000;
- anchor arms `none | size | size_peak`;
- the target list `HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design`;
- the quick-config overrides.

## Task 2 — Pools (`scripts/paperb/pools.py`)
- Write `build_pool_bstar()` and `build_pool_b()`. They return HP members (HP series plus own non-HP series), the clean fill pool (Kaiser cal2023 dwellings with no TCL flag and not paired), station per household, and a household metadata table. The metadata columns are `source, station, has_hp_add, has_ewh_in_own_load (M9), has_protocol, n_valid_days`.
- Reuse `hp_pools` / `heapo` readers, but **do not change their API**. They are shared with hp-sensitivity-paper. New logic goes in `scripts/paperb/`.
- Cache to `data/_paperb/pools/<name>_2023.parquet`, in long or wide format, whichever is smaller. Do not use pickle.
- Check coverage properly: ≥ 90 % valid samples before interpolation. This is the F11 lesson; apply it here even though the WPuQ fix itself is deferred.

## Task 3 — Splits (`scripts/paperb/splits.py`)
- `household_splits(pool, seeds, test_frac=0.25, stratify='station')` returns train/test household sets per seed. HP households and fill households are split independently.
- `grouped_inner_folds(train_households, k=4, seed)` returns household-disjoint folds, which later generate household-disjoint inner substations.

## Task 4 — Substation generator v1 (`scripts/paperb/substations.py`) — fixes F12
- For each (split seed, split, size, penetration) cell, draw substations with:
  - no household twice in a substation;
  - no HP-member/fill overlap;
  - all HP members from one station;
  - fill drawn from the same split's fill pool.
- **No silent truncation.** An infeasible cell raises (or is skipped with an explicit entry in `dropped_cells.csv` under a config flag).
- Store the **membership only** (member ids, station, size, p) plus targets. Build aggregate series lazily in feature extraction, and cache features as parquet in `data/_paperb/features/`. Do not repeat the 1.8 GB legacy pickle.
- Compute targets per substation:
  - `HP_Peak` (legacy definition);
  - `HP_CoincPeak`;
  - `HP_Count`;
  - `s_h`, `r`, `P_design`, from the Task 5 physics fit applied to the aggregated **HP submeter** and non-HP series;
  - the anchors `size` and `peak` (observed max of the net aggregate).

## Task 5 — Physics estimators aligned with Paper A (`scripts/paperb/physics.py`) — fixes F2
- Find the current hockey-stick / HDH fit in `hp-sensitivity-paper`, including latent T_base, the day filter and the bounds. **Port it unchanged**; do not design a new fit. If Paper A uses several variants, report them and use the one its paper draft states.
- Add a fixture test showing that the ported function reproduces Paper A's outputs on ≥ 5 households, within 1e-6.
- Report the fraction of fits with the hinge inside the observed temperature range: legacy 8 %, and the new value.
- Provide estimators with a `fit(train) / predict(X)` API:
  - slope-only map;
  - slope + base;
  - calibrated delta (through origin, mean/mean);
  - HDH variant.
- Leave `hp_common.py` untouched.

## Task 6 — Model training utilities (`scripts/paperb/train.py`) — fixes F13, supports F1
- **`tune_grouped_cv(model_name, X, y, groups=inner_fold_id, seed)`**:
  - seeded hyperopt;
  - early stopping on an inner validation subset of the training folds, **never on the scored fold**;
  - the final model refit on all train at the median best iteration.
- **Models:** XGBoost, Ridge, ElasticNet, SVR, FFNN, PLS, same as the legacy set. Use the same API for each.
- **`feature_matrix(features, anchor)`** for anchor ∈ {none, size, size_peak}.
- **Anchor-only baselines (F1):** a linear model and an XGBoost model on `[size]`, `[peak]` and `[size, peak]` only.

## Task 7 — Uncertainty (`scripts/paperb/uncertainty.py`)
- `cluster_bootstrap(metric_fn, df, cluster='hp_household', B, seed)`. It resamples test HP households and recomputes the metric on the substations whose members are all in the resample. Document that approximation.
- `across_split_summary(metrics)` returns the mean, sd and 5–95 % range over split seeds.

## Task 8 — F14 (notebook cell 88)
- Port the hourly HDH-sensitivity Ridge to `scripts/legacy_fixes/hdh_hourly_ridge.py`, fitted on **train** and scored on test. Report old vs new numbers in the REVIEW.
- In the notebook, the only permitted edit is a markdown cell directly above cell 88: "LEGACY — fitted on test (F14); superseded by scripts/legacy_fixes/hdh_hourly_ridge.py." Make no other notebook changes.

## Task 9 — Tests (`tests/test_protocol_v1.py`)
At minimum:
- no household in both train and test, for every seed;
- no duplicate household in any substation;
- no HP/fill overlap;
- the HP members of a substation share a station;
- infeasible cells raise;
- inner folds are household-disjoint;
- the same seed gives identical memberships, targets and hyperopt trials;
- the physics fixture matches Paper A;
- the bootstrap resamples households, not substations;
- targets are non-negative and `HP_CoincPeak ≤ HP_Peak` (flag violations rather than assert, if the robust-peak definition allows them).

## Task 10 — Smoke run
Run `scripts/paperb/run_benchmark.py --config configs/protocol_v1_quick.yaml` end to end:
- 1 split seed, 1 small cell per penetration, target `HP_Peak`, XGBoost with 5 hyperopt evaluations, and the slope-only physics estimator;
- output to `results/iter02a_smoke/` in the §8 format.

**Do not interpret the numbers.** Report the runtime, and extrapolate the full 02b runtime for B\* + B × 20 seeds × all models × 3 anchor arms. If the full run is estimated at more than 12 h, propose reductions, e.g. fewer seeds for the non-XGB models.

## Out of scope
- Benchmark results and legacy comparison (02b).
- Daily arm and RQ1 target analysis (03).
- Transfer sets (04).
- F3–F8, F10, F11.
- Any edit to `hp_common.py`, `hp_pools.py`, `hp_capacity.py` or `heapo.py` APIs.

## Acceptance criteria
- [ ] CLAUDE.md and DECISIONS.md are tracked by git; the stash contents are listed.
- [ ] Tasks 1–8 are implemented, and `pytest` passes, including the Paper A fixture.
- [ ] The smoke run completes and writes a valid `metrics.csv`.
- [ ] `data/` (outside `data/_paperb/`) and `models/` are unmodified.
- [ ] REVIEW.md is written using the §9 template. Decisions must cover at least:
  1. whether the Paper A fit variant chosen is the right one;
  2. whether the hinge-inside-range fraction is acceptable;
  3. the full-run budget for 02b (seeds × models).
