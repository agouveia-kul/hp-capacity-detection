# CLAUDE.md — hp-capacity-detection (Paper B)

Read this file fully at the start of every session. It is the contract for all work in this repository.

## 1. Purpose

This repository produces **Paper B**: *a hybrid, identifiability-guided estimator of thermostatically controlled load (TCL) / heat-pump (HP) installed capacity from aggregated LV net load and temperature. Physics-based estimation (Paper A) and data-driven estimation each have limits; the hybrid keeps the part that net load identifies (the heating slope) and learns only the part it does not (the scale m_h and a residual).* The contribution is a method, not a benchmark (Alex, 2026-10-09). Target: capacity only (`HP_Peak`).

The companion **Paper A** (repo `hp-sensitivity-paper`) establishes identifiability. Its main points:
- Absolute HP counts and N_total are **not** identifiable (scale ambiguity).
- The ratio r = s_h / P_base **is** identifiable.
- The hockey-stick / HDH thermal-sensitivity model is the physics estimator.
- The base temperature is latent.

Paper B uses Paper A as its theoretical bound and baseline; it must not duplicate it.

### Research questions (reframed as the ladder questions, 2026-10-09; iteration 06 brief)
The method is tested as a ladder. The same model families are used at every rung, so each rung isolates one ingredient.
- **Q1, physics and its limits (L0).** Where does Paper A's estimator stop: filler contamination, scale (m_h) dispersion, transfer of m_h? Evidence: 03b, 05b Arm 4.
- **Q2, data-driven estimation and its limits (L1, L2).** What do generic features, physics-derived features and raw series reach with each family? How many labelled HP households are needed (n\*), and how sensitive is the result to the fillers' temperature response? Evidence: 05b, 06.
- **Q3, the hybrid (L3, L4).** Does a physics-informed target (L3), and then a learned transferable scale m̂_h with an ML residual (L4, the proposed hybrid), pay off against L0 and against the best pure data-driven model, on accuracy, sample efficiency, robustness and transfer? Evidence: 06, 07.
- **Q4, ensemble (L5).** Does an ensemble of hybrid experts (plain average; r̂ gate) beat the hybrid? It is dropped from the method if it fails its rule. Evidence: 06.
- **Q5, transfer (axis T).** CH ↔ GB under harmonised labels, all rungs. Evidence: 07.
- **Q6, use case.** Can a change in capacity be detected and quantified over a multi-year horizon? Evidence: 08.

Iterations 00–05b use the earlier numbering (RQ1 targets vs identifiability, RQ2 value over physics, RQ3 transfer, RQ4 change detection). RQ1's other targets (HP count, nameplate, coincident peak, s_h, r, peak at design temperature) and the daily arm are dropped for now (2026-10-09).

### Iteration plan (renumbered 2026-10-09 with the storyline; DECISIONS.md)
- 03a / 03b — fair test of ML against the physics estimator (code / runs); done;
- 04 — data inventory for larger pools and HP-profile simulation feasibility; done;
- 05a / 05b — GB-EoH pool with analog-matched LCL filler (code) / is training data what holds ML back? (runs); done;
- 06 — the hybrid ladder (L0–L5; axes A, S, R), both pools;
- 07 — transfer validation (axis T; CH ↔ GB under harmonised labels, all rungs);
- 08 — change-detection use case (EoH multi-year panel);
- 09+ — freeze and draft.

**Paper storyline (Alex, 2026-10-09; replaces the earlier "paper lead"):**
1. the LV network and its DER are unobservable;
2. physics-based estimation (Paper A) has limits;
3. data-driven estimation (feature types × models) has other limits;
4. a **hybrid, identifiability-guided estimator** is the methodological contribution;
5. validation by transfer;
6. use case: detecting a change in capacity.

Target: capacity only.

**05b framing of the data-driven part (decision 2026-10-12).** The ML gain replicates across years (Arm 6, all three carried families) but is conditional on the fillers' temperature response (Arm 7: frozen linear 0/10 and TabPFN 5/10 at ×0.5; only the CNN holds) and absent at CH sample size (Arm 5: no family and 0/60 configurations beat physics). This frames the data-driven section and motivates the hybrid estimator; the A12 lead options (ii) and (iii) are not adopted. 05b verdict: D (linear, CNN) + F; the S test is formally met for the raw-series family only and is not robust. The simulator is a no-go.

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
6. **Merge and push only on Alex's request.** Commit to the iteration branch. Push it, or merge it into `main`, only when Alex asks for that (in the conversation, or in instructions he gives for the task, e.g. a handover); never on your own initiative. Alex reviews before any merge. (Amended 2026-10-06; was "Do not merge".)
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
| **B\*** | CH: the small-n regime, with real co-located own load | 86 (≈ 62 train / 20 test per seed), cal2023 | 15-min | same-year Kaiser/HEAPO fill, plus each HP home's own non-HP load |
| **GB-EoH** | GB: the large-n regime (full grid, from 05a) | non-hybrid homes with ≥ 90 % valid 30-min bins in a 12-month window (05a-ii R1/R2): main window Nov 2021 – Oct 2022, **384** homes (293 train / 92 test per seed, 274 / 81 used); **temporal replication** (another year, mostly the same homes: 272 of 319 shared) Oct 2022 – 28 Sep 2023, **319** homes | 30-min | flat-rate LCL households, analog-day matched (see `fill_analog.py`); one LCL household per dwelling, HP dwellings included |
| **B** | sensitivity | 47, KLO only | 15-min | as B\* |

There is no single headline dataset (decision 2026-10-12): B\* and GB-EoH are reported side by side. Cross-pool comparisons use gaps to the best physics row, not absolute WAPE (label resolution differs).

**Pre-registered comparison criterion (03a).** ML "beats physics" only if both hold, overall and per Paper A penetration bin:
- the paired per-seed ΔWAPE against the best physics row is < 0 in ≥ 16 of 20 seeds (≥ 80 % of seed × draws for learning curves);
- the median ΔWAPE is ≤ −1 pp.

Paper A's penetration bins (≤ 15 / 15–35 / 35–65 / > 65 %) are always reported.

**The hybrid ladder, its four axes and the claim rule (06; pre-registered 2026-10-09, `iterations/06-hybrid-ladder.md`, DECISIONS.md 2026-10-12).** Families: the carried ones (linear, TabPFN, CNN). At each rung a family's configuration is chosen by inner-CV WAPE among that rung's configurations only.

| Rung | Adds | Configurations |
|---|---|---|
| L0 | physics | `paperA_corr`, `paperA_corr_own`, `paperA_cal`, `slope_base`; the best by median WAPE is the L0 reference |
| L1 | pure data-driven | tabular `whdd` + scale features, direct-log; CNN `raw` + scale, direct-log. No hockey-stick fit, no Paper A quantity |
| L2 | physics-derived features | tabular {`netfit`, `both`} × {size, size_peak}, direct-log; CNN `rawphys` (raw + ŝ, P_base, T_h, N after pooling), direct-log |
| L3 | physics-informed target | L2 inputs, mode `residual`: z = log y − log P̂_A |
| L4 | learned transferable scale (**the proposed hybrid**) | P̂ = ŝ / m̂_h · exp(f_θ(x)), ŝ = max(s_h(net) − N·s₀, 0). `l4a`: m̂_h = κ / (T̂_h − T_design), κ from the pilot. `l4b`: m̂_h = g(covariates), a regularised regression of log m_h. m̂_h is cross-fitted; the L4 row is the inner-CV winner of {`l4a`, `l4b`} |
| L5 | ensemble of hybrid experts | L5a: plain average of the families' L4 predictions. L5b: gate on r̂ = ŝ / P_base(net), edges and per-bin weights learned on out-of-fold inner-CV predictions |

- **Axes.**
  - **A, accuracy:** GB main and CH (B\*), n = all, seeds 0–9; WAPE overall and per Paper A bin (†).
  - **S, sample efficiency:** GB learning curve at n ∈ {32, 62, 100, all}, 10 seeds × 2 draws; primary point n = 62; n\* (where a rung reaches L0) also reported.
  - **R, robustness:** (i) the frozen n = all models on test aggregates with fillers ×0.5 and ×1.5, as the degradation ΔWAPE vs ×1.0; (ii) the same rung refit on the temporal replication year.
  - **T, transfer:** evaluated in 07; 06 persists every rung's per-seed models for it.
- **"Better" on an axis:** paired per-seed ΔWAPE < 0 in ≥ 8 of 10 seeds (≥ 80 % of seed × draws on S) **and** median ΔWAPE ≤ −1 pp. On R the degradation is compared, not the level.
- **Rule 1, ladder steps:** per family and dataset, each rung against the one below (L2 vs L1, L3 vs L2, L4 vs L3) on A, S and R: better / worse / no difference.
- **Rule 2, the hybrid claim:** the hybrid = L4 with its best family; the best pure data-driven model = the best of L1 / L2 over the families (both by inner-CV WAPE). The claim holds if (a) on A the hybrid's median WAPE is at most 1 pp above the best pure data-driven model (GB, overall) **and** (b) the hybrid is better on at least two of S, R, T. It is closed in 07. The hybrid vs L0 is reported on every axis.
- **Rule 3, L5:** an ensemble form is kept only if it beats L4 by median ≤ −1 pp and in ≥ 8/10 seeds, overall or in the † bins, on GB. Otherwise it is a negative result and not part of the method.
- Multiplicity (5 rungs × 3 families × 2 datasets × 3 axes) is stated with every table.

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
    - `paperA_cal`: bias-calibrated with the cross-fitted pilot;
    - `paperA_corr_own` (05b, A7): label-free; the pilot scale m_h′ comes from the pilot homes' whole-house load minus n_pilot · s₀, so the HP homes' own non-HP response is folded into the scale. It needs whole-house meters on the pilot homes.
- **Reference set for tables (from 03b).** These rows are always named in tables for continuity; they are **not a model filter**:
  - physics: `slope_base`, `paperA_corr`, `paperA_corr_own` (from 05b: the best physics row on B\*, 19.3 %), `paperA_cal` (+ `paperA_sh_mh` as Paper A's row);
  - ML: netfit + Lasso [size] direct, Lasso residual, XGBoost direct.
- **Model families (from 05a/05b; all stay in the pipeline and in every arm):**
  - linear: Linear, Ridge, Lasso, ElasticNet, PLS;
  - kernel: SVR, Kernel Ridge (GP regression implemented but not run from 05b, A8);
  - trees: XGBoost, Random Forest, Extra Trees (CatBoost implemented but not run from 05b, A8);
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
| `scripts/paperb/` | Protocol v1 pipeline: `substations.py` (cells, members, labels), `splits.py` (household splits, grouped inner folds), `physics.py` (hockey stick, Paper A estimators), `features_netfit.py`, `train.py` (model registry), `residual.py`, `learning_curve.py`, `metrics.py` (WAPE), `tables.py`, `summarise.py`, `run_benchmark.py` (entry point, `--config`). New in 05a: `pools/gb_eoh.py`, `fill_analog.py`, `run_queue.py` (resumable job queue), `d4_diagnostics.py`, `envelopes_v11.py`, `iter05a_report.py` (audit reports); `scripts/schedule_overnight.ps1`. New in 06: `scale_model.py` (ladder rungs, L4 scale models `l4a` / `l4b`, cross-fitted), `ensemble.py` (L5a average, L5b r̂ gate); feature set `rawphys` (CNN + net-load fit scalars), `refit.by_rung` persistence (`persist.py`), queue keys `after`, `threads`, `group`, `fixed_params` (`run_queue.py`). |
| `scripts/audit/` | Read-only audit code (01 pool audit, 04 inventory: `eoh_convert.py`, `inventory_v2.py`, `envelope_v2.py`, `hplib_check.py`). |
| `configs/` | `protocol_v1.yaml`, per-iteration configs (`iterNN_quick.yaml` for smoke runs), pool configs (`pool_*.yaml`, from 05a). 06: queue `iter06.yaml` (arms `a_gb`, `a_ch`, `s_gb`, `r_x05`, `r_x15`, `r_rep`), its probe and quick versions, arm configs `iter06_{a_gb,a_ch,r_shift,r_rep}.yaml`. |
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
- **Found in 05b:**
  - **CNN retraining instability.** The raw-series CNN retrained with the same spec, hyperparameters and epoch count gives a different model on another device or thread count. CPU against GPU over 20 seeds: per-seed ΔWAPE std 3.2 pp, median +0.3 pp, seeds 8 and 9 collapse (+8.7 and +10.8 pp, 27 % WAPE). Seed 0 on the same CPU: −0.89 pp with 14 threads, −0.55 pp with 4. On a fixed device and thread count it is deterministic. Stage 1's CNN rows are GPU-trained; Stage 2's CNN deltas are paired with the CPU reference arm `arm2_cpu`. Read CNN differences of about 1 pp with this noise in mind (the S test).
  - **Oracle O2 is an identity.** m_h(true) is fitted on the same HP aggregate whose slope it divides, so `oracle_O2` returns the label. The error decomposition has two informative terms, fill contamination and scale dispersion; "fit noise" is not reported as a component (decision 2026-10-12).
  - **Queue lessons.** Keep workers × threads ≤ the physical cores: 6 workers × 4 threads on 20 cores, at below-normal priority, ran jobs 1.5–13 × slower than the one-seed probe (Stage 2 took 71 h against an estimate of 23–35 h). The queue has no per-job timeout yet: a CNN job can spin for hours (13.1 h in Stage 2; 4.2 h in the probe against 471 s alone). A seed's family jobs that start before its physics job has filled the caches redo the feature evaluation and the pilot.
  - **Used HP households.** GB-EoH main 274 train / 81 test, replication 226 / 61, B\* 62 / 20. Stage 1's REVIEW wrote 292 / 81 (292 is the train split, not the households inside substations).
