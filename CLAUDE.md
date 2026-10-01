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

### Iteration plan (renumbered 2026-09-30, before iteration 05a)
- 03a / 03b — fair test of ML against the physics estimator (code / runs); done;
- 04 — data inventory for larger pools and HP-profile simulation feasibility; done;
- 05a / 05b — GB-EoH pool with analog-matched LCL filler (code) / is training data what holds ML back? (runs);
- 06 — other targets and the daily arm (RQ1), both pools;
- 07 — transfer (RQ3), incl. CH↔GB and the RHPP nameplate arm;
- 08–09 — change detection (RQ4), EoH multi-year panel;
- 10+ — freeze and draft.

**Current paper lead (03b; confirmed by Alex 2026-09-30, provisional until the 05b verdict):** identifiability-bounded learning. If 05b's verdict is D (data-limited), the lead is revisited. On B\*, no ML configuration beat the best physics row under the pre-registered criterion (§4).

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
7. **Smoke first; long runs overnight.** Every experiment script takes `--config` and has a `quick` config that runs in under about 5 minutes on a small subset. Run `quick` interactively before any long run.
   - Long runs (> 30 min) state their estimated runtime.
   - They go through the resumable job queue (`scripts/paperb/run_queue.py`, from 05a), which runs one job per (arm, seed, draw, n, family), skips finished jobs on relaunch and keeps the PC awake via `SetThreadExecutionState`.
   - They are scheduled overnight with `scripts/schedule_overnight.ps1`. **Never register a scheduled task yourself**: print the command, and Alex runs it.
   - Runtime is not a reason to cut arms. If a run needs more than ~3 nights, ask first.
8. **Seeds everywhere.** Every random operation takes an explicit seed from the config.
9. **Report honestly.** Report numbers that get worse. Never tune on test data. Never silently drop a failing case; list it.
10. **Hyperopt and every stochastic search must be seeded** (`HYPEROPT_FMIN_SEED` or `rstate`).
11. **Paper-facing methods need checked references.**
    - Any methodological choice that will appear in the paper (a data-fusion step, a matching rule, a statistical test, a label definition) must be backed by references that you have **retrieved and checked**: title, authors, year, venue, DOI or link.
    - Record them in the iteration's `method_basis.md` or in `references.bib`.
    - Mark anything not retrieved as **unverified**. Never invent a citation or a DOI.
    - If no precedent exists, say so explicitly.
12. **Pre-registration.** When an iteration states a decision rule or pass/fail thresholds, they are fixed before any run. Never change them after seeing results; report every outcome.

## 4. Evaluation protocol (target state)

Protocol v1 is official: `configs/protocol_v1.yaml` (implemented in iteration 02a, code in `scripts/paperb/`). Results produced before it are "legacy protocol" and must be labelled as such.

**Protocol v1.1** (from 05a) = v1 + p = 0.8 in the grid, for all pools; everything else is unchanged. `protocol_v1.yaml` is kept for reproducing 02b–03b.

**Pools:**

| Pool | Role | HP households | Resolution | Non-HP load |
|---|---|---|---|---|
| **B\*** | headline, CH | 86 (≈ 62 train / 20 test per seed), cal2023 | 15-min | same-year Kaiser/HEAPO fill, plus each HP home's own non-HP load |
| **GB-EoH** | second full-grid pool (from 05a) | non-hybrid homes with ≥ 90 % valid 30-min bins in a 12-month window (05a-ii R1/R2): main window Nov 2021 – Oct 2022, **384** homes (293 train / 92 test per seed, 275 / 81 used); **temporal replication** (another year, mostly the same homes: 272 of 319 shared) Oct 2022 – 28 Sep 2023, **319** homes | 30-min | flat-rate LCL households, analog-day matched (see `fill_analog.py`); one LCL household per dwelling, HP dwellings included |
| **B** | sensitivity | 47, KLO only | 15-min | as B\* |

Cross-pool comparisons use gaps to the best physics row, not absolute WAPE (label resolution differs).

**Pre-registered comparison criterion (03a).** ML "beats physics" only if both hold, overall and per Paper A penetration bin:
- the paired per-seed ΔWAPE against the best physics row is < 0 in ≥ 16 of 20 seeds (≥ 80 % of seed × draws for learning curves);
- the median ΔWAPE is ≤ −1 pp.

Paper A's penetration bins (≤ 15 / 15–35 / 35–65 / > 65 %) are always reported.

- **Household-disjoint splits.** Split households into train/test pools **before** building substations. No household may appear in both. Stratify HP households by weather station.
- **No stacking within a substation.** Each dwelling in a substation is a distinct household (`build_substations_norepl`). Feeder size and penetration are bounded by the pool, and those bounds are reported.
- **Grouped CV inside train.** Hyperparameter tuning and feature selection use folds built from household-disjoint sub-pools. Never use KFold over substations that share households.
- **Repeated splits.** Headline metrics are the mean ± spread over at least 10 independent household splits (seeds).
- **Uncertainty = across-split summary (median, mean ± std, 5 %–90 %).** No bootstrap unless an iteration says so.
- **Primary metric = WAPE** (Σ|ŷ − y| / Σy, as in Paper A); it comes first in `summary.csv` and in every table. MAPE and R² are secondary (decision 2026-09-29, 02b review).
- **Effective sample size.** Always report the number of distinct HP households behind each result.
- **Physics baselines are always reported next to ML:**
  - hockey-stick slope-only map;
  - slope + base;
  - calibrated delta (mean/mean, through origin);
  - HDH variant;
  - Paper A's estimators:
    - `paperA_sh_mh`: s_h / m_h with the all-train pilot;
    - `paperA_corr`: the non-TCL-corrected version, with s₀ from the train fill;
    - `paperA_cal`: bias-calibrated with the cross-fitted pilot.
- **Reference set for tables (from 03b).** These rows are always named in tables for continuity; they are **not a model filter**:
  - physics: `slope_base`, `paperA_corr`, `paperA_cal` (+ `paperA_sh_mh` as Paper A's row);
  - ML: netfit + Lasso [size] direct, Lasso residual, XGBoost direct.
- **Model families (from 05a/05b; all stay in the pipeline and in every arm):**
  - linear: Linear, Ridge, Lasso, ElasticNet, PLS;
  - kernel: SVR, Kernel Ridge, GP regression;
  - trees: XGBoost, Random Forest, Extra Trees, CatBoost;
  - neural: FFNN (full budget, 50 evals, patience 20), TabPFN (TabPFN-3.5, checkpoint `tabpfn-v3.5-20260909.safetensors` loaded via `model_path`, `tabpfn` ≥ 9.0.0; non-commercial licence, fine for this research). The weights are downloaded by Alex from Hugging Face into `TABPFN_MODEL_CACHE_DIR` and loaded locally. Never print or commit tokens.
  - raw-series: 1D-CNN on the daily net-load and T series (feature-free check).

  The models added in 05b are used from 05b on; 05a's D5 uses the families as they stand in 05a.

  Compare families by **one inner-CV winner per family**, never by test. `XGBoost_mono` is retired.
- **Transfer sets are never used for any fitting, selection or calibration** unless the experiment is explicitly a domain-adaptation experiment and says so.

## 5. Target definitions (use these names)

| Name | Definition |
|---|---|
| `HP_Peak` | Sum over HP members of the per-household 99.9th percentile of HP draw. Non-coincident observed peak; includes backup-rod draw. Resolution and channel per pool: B\* uses the **15-min** HP submeter; GB-EoH uses the **30-min whole heating-system electricity** (compressor + backup + immersion + pumps). Primary target. |
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
| `scripts/paperb/` | Protocol v1 pipeline: `substations.py` (cells, members, labels), `splits.py` (household splits, grouped inner folds), `physics.py` (hockey stick, Paper A estimators), `features_netfit.py`, `train.py` (model registry), `residual.py`, `learning_curve.py`, `metrics.py` (WAPE), `tables.py`, `summarise.py`, `run_benchmark.py` (entry point, `--config`). New in 05a: `pools/gb_eoh.py`, `fill_analog.py`, `run_queue.py` (resumable job queue), `d4_diagnostics.py`, `envelopes_v11.py`, `iter05a_report.py` (audit reports); `scripts/schedule_overnight.ps1`. |
| `scripts/audit/` | Read-only audit code (01 pool audit, 04 inventory: `eoh_convert.py`, `inventory_v2.py`, `envelope_v2.py`, `hplib_check.py`). |
| `configs/` | `protocol_v1.yaml`, per-iteration configs (`iterNN_quick.yaml` for smoke runs), pool configs (`pool_*.yaml`, from 05a). |
| `tests/` | pytest suite; `slow` tests are skipped by default (`pytest -m slow` runs them). Run as `.venv\Scripts\python -m pytest`. |
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
- **Electrification of Heat (EoH), UKDS SN 9050:** `9050csv_cleansed_data_set{1..4}_*.zip` (originals, never touch). The 30-min parquet conversion is in `_paperb/pools_raw/eoh/`, and the docs are in `_paperb/raw/eoh/`. The USmart Property/Design/Installation table (supplied by Alex, licence not on disk; original `9bbf3b4f-*.csv`) is copied to `_paperb/raw/eoh/eoh_property_design_installation.csv`: `HP_Installed`, `HP_Size_kW`, `MCS_SHLoad`, postcode district `Postcode_1`. There is no whole-house meter; the 30 weather groups (identical outdoor-T series) serve as stations.
- **Low Carbon London (LCL):** `LCL_2013.zip` = UKDS SN 7857 ed. 2: 4,173 flat-rate (`consumption_n.csv`, Std) + 1,025 time-of-use (`consumption_d.csv`) households, 30-min UTC, plus an appliance survey. Filler = Std only, kept 3,199 (coverage ≥ 90 % over Jul 2012 – Feb 2014, no half-hour > 10 kWh, no zero run ≥ 24 h). **Survey answer columns are shifted by one against `survey_questions.csv`** (answer column Qk holds question Q(k+1)): central-heating fuel is column Q246, portable electric heaters column Q303 (Q304 = TVs). Sensitivity filler set: `gas_ch & no_heater` = 777 households (s₀ 0.0075 kW/K vs 0.0120 for all Std, Heathrow, Jul 2012 – Jun 2013). **Temperature for LCL (05a-ii R4): London Heathrow daily mean, Meteostat bulk `daily/03772.csv.gz`** in `_paperb/raw/meteostat/` (CC BY-NC 4.0); HadCET (`hadcet/meantemp_daily_totals.txt`, Central England) is kept only as the comparison column `T_hadcet` (Heathrow is 1.2 K warmer on average, r = 0.984). Meteostat's station list confirms 03772 = London Heathrow Airport (WMO 03772, ICAO EGLL, 51.48 N, 0.45 W, 24 m).
- **EoH window and coverage rule (05a-ii R1/R2/R5/R8 and review decisions):** a home is eligible with ≥ 90 % valid 30-min bins in the window (gaps ≤ 2 h interpolated, longer ones donor days of the same home and day type; filled days are counted). Main window = the start month (1 Jun 2021 – 1 Jan 2022) with the most eligible homes (Nov 2021). Replication = Oct 2022 – 29 Sep 2023 (the data stop on 29 Sep 2023; the window is clipped to the last full day, 28 Sep, so it has 363 days), called a temporal replication; fallback Sep 2022 – Aug 2023 only if it gives < 300 homes (it gave 319). Weather groups with > 5 % missing T are filled from the best-correlated group (≥ 0.98, linear fit) or dropped. A zero run ≥ 6 h is missing only if it is an electricity-meter dropout (heat output in or within 12 h of the run while electricity reads ~0); runs without heat are real switch-offs. Homes whose electricity reads < 0.02 kW on > 5 % of their heat bins (> 1 kW) are excluded (`silent_elec_max`).
- **Other HP data:** `rhpp_daily.parquet`, `rhpp_sites.parquet`, `RHPP_GB.zip`, `lcl_heatpump/`, `neea_*.parquet`, `bpa_hphc/`, `nrel_ccashp/`, `cofactor_ds1/`, `carleton/`, `15minuteFluvius.csv`.
- **Paper B caches (writable):** `_paperb/`: features, pools_raw, raw docs, iteration caches.
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
- **Fixed HDD base.** Windowed-HDD features use a fixed national T_base (12 °C CH, 15 °C DE). The HDH baseline uses the fixed 12 °C base too, while the fitted T_h has median 16.7 °C (revisit in 03). *03a:* this bin misalignment is addressed by the new `netfit` feature set (latent T_h per substation, θ bins referenced to the fitted T_h); the legacy windowed-HDD set is kept unchanged as feature set `whdd`.
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
  - **Fixed in 03b** (protocol v1 code, `scripts/paperb/`; `paperA_*` estimators report `HP_Peak` only): residual targets and the bias calibration use cross-fitted pilots (household-disjoint from the substation); Berchtoldstag is a `netfit` holiday; WAPE is also reported in Paper A's penetration bins (`pbin...` cells).
- **Data issues found in 04 (GB pools):**
  - **EoH:** 3 empty property files; the hybrid boiler counter is unreliable (hybrids are excluded); heat-meter dropouts are recorded as 0, not missing; the UKDA summary dates differ from the file contents for 187 of 739 homes (use the files); `HP_Installed` / `HP_Size_kW` are only in the USmart property table (on disk since 04, see §7).
  - **Fill s₀ (kW/K per dwelling):** B\* 0.0055; LCL 0.0133. The "gas-only" LCL subset (0.0070) has unverified provenance: use it only if 05a traces it to a documented label.
  - **The > 65 % penetration bin** is grid-limited (p = 1.0 only) under v1; v1.1 adds p = 0.8.
  - **hplib** under-predicts EoH HP electricity (daily WAPE 21.7 %, bias −19.7 %) and over-predicts SPF by +27.5 %. The simulator is deferred until the 05b verdict.
- **Found in 05a / 05a-ii:**
  - **LCL survey column shift.** The answer columns of `survey_answers.csv` are shifted by one against `survey_questions.csv`. Iteration 04's "0 portable heaters" filter (answer column Q304) selected 0 TVs. **Paper A's `_lcl_base` (`hp-sensitivity-paper`, `scripts/outputs.py`) applies the shift to Q248 but not to Q304, so its clean / heater-rich LCL splits carry the same bug**; it is being checked separately in the Paper A repo and was not changed here.
  - **D4 (05a-ii Task A), flag "filler-variability-limited".** A single winter's filler slope is intrinsically unstable (real 2012/13 → 2013/14 change 52–78 %), of the same size as the D4 rebuild error: classified intrinsic filler variability, and the mapping is accepted. The capacity-equivalent error that this natural year-to-year variability of real non-HP households' temperature response puts on any estimator exceeds 5 % of `HP_Peak` for p ≤ 0.5 (`d4_diagnostics.md`): those penetrations (Paper A bins ≤ 15, 15–35, 35–65 %) are marked **filler-variability-limited** in every GB-EoH table. It is a floor for any estimator, not a defect of the pool. 05b includes the filler-uncertainty arm (fillers' temperature response ×0.5, ×1.5).
  - **EoH meter dropout.** Home EOH0836 has a silent electricity meter (≈ 0 kW while delivering 8–10 kW of heat) for Feb – Apr 2023; it caused the jump in zero-run bins in 2022/23 and is not eligible in the Oct 2022 window. EOH2291 (15 % silent) is excluded from the main window by the `silent_elec_max` rule.
