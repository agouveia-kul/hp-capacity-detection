# CLAUDE.md — hp-capacity-detection (Paper B)

Read this file fully at the start of every session. It is the contract for all work in this repository.

## 1. Purpose

This repository produces **Paper B**: *what data-driven (ML) methods can and cannot recover about thermostatically controlled load (TCL) / heat-pump (HP) installed capacity from aggregated LV net load and temperature, and where they beat a physics estimator.*

The companion **Paper A** (repo `hp-sensitivity-paper`) establishes identifiability. Its main points:
- Absolute HP counts and N_total are **not** identifiable (scale ambiguity).
- The ratio r = s_h / P_base **is** identifiable.
- The hockey-stick / HDH thermal-sensitivity model is the physics estimator.
- The base temperature is latent.

Paper B uses Paper A as its theoretical bound and baseline; it must not duplicate it.

### Research questions
- **RQ1 — targets vs identifiability.** How well do ML models predict each target:
  - HP count;
  - nameplate kW (HEAPO protocols subset);
  - observed non-coincident peak (current `HP_Peak`);
  - coincident peak;
  - thermal sensitivity s_h (kW/K);
  - ratio r;
  - peak at design temperature.

  Each is run with and without the scale anchor (dwelling count / feeder peak). Does performance track identifiability?
- **RQ2 — value over physics.** On identifiable targets, does ML beat the hockey-stick / HDH / calibrated-delta estimators? Look at COP curvature, backup rods, blocking/control windows and DHW. Can TCL types (HP, backup rod, storage, direct, EWH) be told apart in aggregate?
- **RQ3 — transfer.** Test CH → DE (FeederBW real feeders; WPuQ as a stress test) and a third domain (UKPN / RHPP / others). Compare raw-series vs physics-feature vs hybrid models, and fixed vs latent T_base.
- **RQ4 — change detection.** Over a multi-year horizon with a given uptake probability, can capacity change be detected (minimum detectable change at a fixed false-alarm rate, detection delay) and quantified (relative, and registry-anchored absolute)?

## 2. Environment

- Windows. Python 3.12 in `.venv`. Dependencies in `requirements.txt`. Record any new dependency there, with a version pin.
- `data/` is a **directory junction** to the shared folder `C:\Users\VENANCIA\OneDrive - VITO\Desktop\NILM-data`, which is also used by `hp-sensitivity-paper` and `NILM`.
- The folder is on OneDrive. Avoid writing multi-GB files in tight loops, and prefer parquet over pickle for new tables.

## 3. Hard rules

1. **Never modify, overwrite or delete anything already in `data/`.** Raw datasets and existing caches are shared with other repos.
   - New caches go to `data/_paperb/` (create it if missing).
   - New results go to `results/` inside this repo.
2. **Never overwrite files in `models/`.** New trained models go to `results/<exp_id>/models/`.
3. **Logic lives in `scripts/` (and `src/`), not in the notebook.**
   - `HeatPumpDetection_clean.ipynb` is display-only.
   - Do not add computation cells to it, and do not re-execute its heavy cells.
   - If a notebook cell holds logic that is needed, port it to a script first and leave the cell unchanged.
4. **No methodological change without a stated reason** in the iteration's `REVIEW.md`. Changing a target definition, split, sampling scheme, feature set or metric counts as methodological.
5. **One iteration = one branch = one question.**
   - Branch name: `iter/NN-short-slug`.
   - Keep the reviewed diff small, about 300 lines of new or changed logic. Files copied unchanged, and generated results, don't count, but list them.
   - If the work is bigger, stop and propose a split.
6. **Do not merge.** Commit to the iteration branch and push it. Alex reviews and merges.
7. **Smoke first.** Every experiment script takes `--config` and has a `quick` config that runs in under about 5 minutes on a small subset. Run `quick` before any long run. Long runs (> 30 min) need the estimated runtime stated before launching.
8. **Seeds everywhere.** Every random operation takes an explicit seed from the config.
9. **Report honestly.** Report numbers that get worse. Never tune on test data. Never silently drop a failing case; list it.
10. **Hyperopt and every stochastic search must be seeded** (`HYPEROPT_FMIN_SEED` or `rstate`).

## 4. Evaluation protocol (target state)

Protocol v1 is official: `configs/protocol_v1.yaml` (implemented in iteration 02a, code in `scripts/paperb/`). Results produced before it are "legacy protocol" and must be labelled as such.

- **Household-disjoint splits.** Split households into train/test pools **before** building substations. No household may appear in both. Stratify HP households by weather station.
- **No stacking within a substation.** Each dwelling in a substation is a distinct household (`build_substations_norepl`). Feeder size and penetration are bounded by the pool, and those bounds are reported.
- **Grouped CV inside train.** Hyperparameter tuning and feature selection use folds built from household-disjoint sub-pools. Never use KFold over substations that share households.
- **Repeated splits.** Headline metrics are the mean ± spread over at least 10 independent household splits (seeds).
- **Uncertainty = across-split summary (median, mean ± std, 5 %–90 %).** No bootstrap unless an iteration says so.
- **Effective sample size.** Always report the number of distinct HP households behind each result.
- **Physics baselines are always reported next to ML:**
  - hockey-stick slope-only map;
  - slope + base;
  - calibrated delta (mean/mean, through origin);
  - HDH variant.
- **Transfer sets are never used for any fitting, selection or calibration** unless the experiment is explicitly a domain-adaptation experiment and says so.

## 5. Target definitions (use these names)

| Name | Definition |
|---|---|
| `HP_Peak` | Sum over HP members of the per-household 99.9th percentile of 15-min HP submeter draw. Non-coincident observed peak; includes backup-rod draw. (Current legacy target.) |
| `HP_CoincPeak` | Max of the aggregated HP submeter series of the substation. Definition to be revisited in 03 (raw max vs 99.9th pct). |
| `HP_Count` | Number of HP households in the substation. |
| `HP_Nameplate_el` | HEAPO `HeatPump_Installation_Normpoint_ElectricPower`. **Household-level only** (nameplate vs observed-peak distribution); not a substation benchmark target (decision 2026-09-29). |
| `s_h` | Hockey-stick slope (kW/K) fitted on the aggregated **HP submeter** series (ground truth). |
| `r` | `s_h / P_base`, where P_base is from the non-HP aggregate. |
| `P_design` | Hockey-stick extrapolation of the HP aggregate at the local design temperature. |
| FeederBW `HP_kW`, `ElecHeat_kW` | Registered kW from `feeder_metadata.csv` (`hc.feederbw_targets`). Noisy registry labels. |

## 6. Code map

| Path | Role |
|---|---|
| `scripts/hp_common.py` | Hockey-stick / HDH / bathtub fits, constants (`T_BALANCE_BOUNDS`, `HEATING_SEASON_THRESH`, `HDH_THRESH`). Shared with Paper A; keep API-compatible. |
| `scripts/hp_pools.py` | Household pools: HEAPO, Swiss (Kaiser et al.), combined, WPuQ; `filter_pool_electric_heating`, `restrict_pool`. |
| `scripts/hp_capacity.py` | Windowed-HDD features, `build_substations_norepl`, `household_pool_split`, WPuQ/FeederBW builders, `tune_xgb_cv`, metrics. |
| `src/heapo.py` | HEAPO loader (smart meter, weather, protocols). |
| `models/` | Legacy trained models (read-only). |
| `results/<exp_id>/` | All new outputs (see §7). |
| `iterations/` | Instructions for each iteration (`NN-*.md`) — read the current one. |
| `DECISIONS.md` | Append-only log of Alex's resolved decisions (`date \| iteration \| decision \| rationale`). Read it before starting an iteration; append a line when a review decision is resolved. |

## 7. Data map (paths relative to `data/`)

- **HEAPO:** `heapo_data/`. Smart meter (15-min, daily); `meta_data/`; `reports/protocols.csv` (410 protocols, 391 with HeatingCapacity). Coverage per household: `_heapo_daily_coverage.parquet`.
- **Swiss / Kaiser et al. 2026:** `Swiss_dataset/`: `metadata.csv` (TCL flags `1_*`, control/tariff `2_*`), `smart_meter_data/`, `tariff_data.csv`, `weather_2020-2029.csv` (MeteoSwiss KLO). Covers 2023–2024.
- **WPuQ:** `2019_data_15min.hdf5`, `2020_data_15min.hdf5`, `*_weather.hdf5`.
- **FeederBW:** `FeederBW/` (200 feeders, 2023-04 → 2025-03, `feeder_metadata.csv`, `weather_data.parquet`).
- **UKPN:** `ukpn-smart-meter-consumption-lv-feeder.csv`, `ukpn-smart-meter-consumption-substation.csv`, `ukpn-low-carbon-technologies-secondary.csv`.
- **Other HP data:** `rhpp_daily.parquet`, `rhpp_sites.parquet`, `RHPP_GB.zip`, `lcl_heatpump/`, `neea_*.parquet`, `bpa_hphc/`, `nrel_ccashp/`, `cofactor_ds1/`, `carleton/`, `15minuteFluvius.csv`.
- **Legacy Paper-B caches (read-only):** `substations_data_pooled.pkl`, `_X_swiss_pooled.pkl`, `_combined_pool_cache.pkl`, `_swiss_pool_cache.pkl`, `_design_pool_cache.pkl`, `_wpuq_pool_cache.pkl`, `capacity_*.csv`, `xgb_*.csv`, `hockey_*.csv`, `*_penetration_*.csv`.

## 8. Results contract

Every experiment writes `results/<exp_id>/` containing:
- `config.yaml` — full config, including seeds and git commit hash;
- `metrics.csv` — long format: `exp_id, split_seed, dataset, target, method, anchor, metric, value, n_substations, n_hp_households`;
- `figures/` — PNG and PDF;
- `log.txt` — runtime, warnings, dropped cases.

## 9. End of every iteration: `REVIEW.md`

Write `results/<iter_id>/REVIEW.md`. It must fit on one page and follow this template exactly:

```
# Iteration NN — <title>
**Goal:** one sentence.
**Branch / commit:** iter/NN-slug @ <hash>
**Changed:** files + lines of logic added/changed (copied files and results listed separately)
**Results:** one table, compared with the previous iteration / legacy numbers
**Assumptions & deviations:** bullet list (anything not specified in the iteration instructions)
**Problems found:** bullet list (bugs, surprises, data issues)
**Decisions for Alex:** 2–3 numbered questions with a recommended option each
```

Then stop and wait for review. Do not start the next iteration.

## 10. Known issues (from the 2026-09-28 audit; fixed in later iterations, do not fix ad hoc)

- **Stacked duplicate households.** The benchmark pool draws with replacement, so households are stacked within a substation. `build_wpuq_substations` also draws with replacement from 37 houses.
- **Leaky tuning and selection.** XGBoost tuning (`tune_xgb_cv`) and feature selection use KFold over substations, so folds share households.
- **Bootstrap CIs too narrow.** They resample substations, not households.
- **Single year and single split.** Swiss/HEAPO pools cover calendar 2023 only, with one household split seed.
- **Unfiltered backup rods.** `hp-add` (backup rod) households are not filtered, so rod draw sits inside `HP_Peak`. EWH, storage and direct-heating households are excluded from pools, so they are not available as labelled classes.
- **Fixed HDD base.** Windowed-HDD features use a fixed national T_base (12 °C CH, 15 °C DE). The HDH baseline uses the fixed 12 °C base too, while the fitted T_h has median 16.7 °C (revisit in 03).
- **Missing scripts.** About ten scripts referenced by the notebook are missing from `scripts/` (iteration 0 recovers them).
- **Small HP pool (pinned in iteration 00).** Every legacy capacity result uses the **57-household HEAPO 2023 pool**, split 29 train / 28 test. Only **27** households effectively seed train substations (stations with < 3 households in a split are skipped). 81 is the combined HEAPO + Kaiser pool, which no legacy script loads; "Swiss" in legacy names means HEAPO.
- **Stacking factor.** In 120-dwelling, 100 %-penetration train substations each HP profile appears **16.7×** on average.
- **HP/fill overlap.** In **1786 of 2160** legacy substations a household is both an HP member and a fill member.
- **Selection instability.** Feature selection is seed-dependent: k\* = 60 (legacy, unseeded) vs 40 (hyperopt seed 42), with the gain shrinking to +3.9 % RMSE.
- **Leaky CV confirmed.** Within-train CV RMSE ≈ 20 kW vs 44–55 kW on test.
- **Fixed in 02a** (tests in `tests/test_protocol_v1.py` pass; audit ids from `results/iter01_pool_audit/ml_audit.md`). These fixes live in the protocol v1 code (`scripts/paperb/`); legacy scripts and legacy numbers are unchanged.
  - **F1** anchor-only baselines (linear, XGBoost on `[size]`, `[peak]`, `[size, peak]`) and the `none | size | size_peak` anchor arms.
  - **F2** physics fit = Paper A's (daily means, all days, latent T_h in (8, 20) °C); the hinge lies inside the observed temperature range.
  - **F12** substation generator v1: no truncation; infeasible cells raise or are listed in `dropped_cells.csv`.
  - **F13** early stopping on a household-disjoint training fold, never on the scored fold (`tune_grouped_cv`).
  - **F14** notebook cell 88 refitted on train (`scripts/legacy_fixes/hdh_hourly_ridge.py`); the cell is marked LEGACY.
