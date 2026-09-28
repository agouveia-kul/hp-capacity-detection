# Iteration 00 — Setup and baseline reproduction
**Goal:** Reproduce the legacy capacity results from scripts in this repo and pin the facts of the legacy pipeline (protocol = legacy).
**Branch / commit:** iter/00-baseline @ ff6bde8 (code); results committed on top.
**Changed:** new logic in `scripts/run_legacy.py` (116), `scripts/legacy_facts.py` (237, ~90 of them markdown rendering), `scripts/compare_to_legacy.py` (142), `scripts/legacy_eval_only.py` (46), `scripts/record_environment.py` (43), `tests/test_legacy_facts.py` (73) = **~660 logic lines**, plus `configs/iter00_{quick,full}.yaml`, `.gitignore`, `requirements.txt` (+pytest==8.3.3). *Copied unchanged:* 10 scripts in `scripts/legacy/` (+`SOURCES.md`). *Generated:* `results/iter00_baseline/` (metrics.csv, compare_to_legacy.*, facts.*, environment.txt, logs/, reproduced/, figures/), `results/iter00_baseline_quick/`, `data/_paperb/iter00/*.parquet` (2 small extracts).

**Results:** legacy file (`data/`) vs reproduced. Full run 35 min, hyperopt seeded with `HYPEROPT_FMIN_SEED=42` (the legacy runs were unseeded).

| legacy file | status | key number: legacy → reproduced |
|---|---|---|
| hockey_variants_transfer, hockey_delta_calibrated, xgb_hockey_ci_metrics, wpuq_penetration_sweep (+variants), penetration_calibrated_delta, swiss_penetration_sweep | **exact** (max rel. diff 0) | XGB HEAPO-test MAPE 18.8 → 18.8; cal. delta 22.4 → 22.4; real-feeder slope-only 234 → 234 kW |
| xgb_feature_selection_cv | eval-only **exact**; full rerun **gap** (≤ 9 % mean, 35 % std) | k\* 60 → **40**; selected test RMSE 44.0 → 53.0, R² 0.945 → 0.919, WPUQ R² 0.735 → 0.624 |
| capacity_model_benchmark | 6/7 models **exact** (incl. FFNN); **XGBoost gap** | XGB test R² 0.934 → 0.913; WPUQ R² 0.727 → 0.594; WPUQ MAPE 41 → 55 % |
| capacity_wpuq_real_feeder | exact except **XGBoost** | XGB 128.9 → 166.3 kW (true 238.5) |
| (no legacy CSV) models/capacity_swiss.pkl, evaluation-only | recorded | saved XGB test R² 0.907; retrained 0.947; Ridge 0.834 = 0.834 |

Every gap sits only in rows produced by `hc.tune_xgb_cv` (unseeded `hyperopt.fmin`). When the legacy hyperparameters are reused, the same rows reproduce exactly.

**Assumptions & deviations:**
- The scripts run through a runner that redirects their hard-coded writes (`data/`, `models/`, `paper/`) to `results/` and `data/_paperb/`. Reads use the **legacy** `models/xgb_selected_features.json`, so downstream scripts are evaluation-only. `data/` and `models/` are unmodified (manifest + MD5 identical before/after).
- `regenerate_substations_pooled` was run with `--dry-run` only. It was not fully rebuilt, because that would write a 1.8 GB file. Instead, `legacy_facts.replay_membership` replays its RNG draws. This reproduces the legacy membership of all 2160 substations exactly, and HP_Peak to 2e-13 kW.
- I added `legacy_eval_only.py` (not in the instructions) to separate hyperopt randomness from data/code drift.
- The diff is ~660 logic lines, over the ~300 guideline. The task list (runner + compare + facts + env + tests) did not fit in 300.
- The `n_hp_households` values in metrics.csv (test 28, train-CV 27, WPUQ 37) are pool-level distinct counts.

**Problems found:**
- **81 vs 57:** every legacy result uses the **57-household HEAPO 2023 pool**, split 29 train / 28 test. 81 is the combined HEAPO + Swiss/Kaiser pool, which none of the legacy scripts load. Notebook cell 160 is wrong. "Swiss" in legacy names means HEAPO.
- **Effective training pool:** only 27 HP households seed train substations (MqO and z6I have < 3 in train); train uses stations {8jB, HbsbG, Hg}, test uses {8jB, Hg, MqO}.
- **Stacking:** in 120-dwelling, 100 % train substations each HP profile appears 16.7× on average. 1786/2160 substations have a household that is both an HP member and a fill member.
- **Selection unstable:** the "274 → 60 features improves everything" result depends on the hyperopt seed. With seed 42, k\* = 40 (37 of those 40 are in the legacy 60), and the gain shrinks to +3.9 % RMSE.
- **Leaky CV:** within-train CV RMSE is ≈ 20 kW vs 44–55 kW on test, consistent with the KFold leakage in §10.
- **Protocols:** only **2** of the 57 pool households have `Normpoint_ElectricPower` (10 have any HeatingCapacity). So `HP_Nameplate_el` is not usable on the legacy pool.
- **Coincident peak:** median HP_CoincPeak / HP_Peak = 0.79.

**Decisions for Alex:**
1. **Official legacy baseline?** Recommended: use the **legacy CSVs in `data/`** (the 7 exact files are identical anyway), and quote the seed-42 rerun as a single-seed spread for the XGBoost rows. Alternative: switch to the seeded rerun, which is reproducible now.
2. **Trust the recovered scripts?** None are reconstructed; all are byte-identical to git `309eaaf^` and `NILM/OLD/`, and 7/9 outputs match exactly. Recommended: **trust them**, and treat every XGBoost-tuned legacy number as single-seed.
3. **Diff size (~660 lines):** accept it as infrastructure (recommended), or should I split it into 00a (runner + compare) and 00b (facts + tests)?
