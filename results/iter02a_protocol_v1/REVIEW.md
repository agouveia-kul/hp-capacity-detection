# Iteration 02a — Protocol v1: code and tests (no results)
**Goal:** Implement the approved protocol v1 (B\*/B pools, household splits, generator v1, Paper A physics, grouped CV, cluster bootstrap) with tests and a smoke run; fix F1, F2, F12, F13, F14.

**Branch / commit:** iter/02a-protocol-v1 @ b77bdbd (code); results committed on top. Branched from `main` (00 and 01 are merged).

**Changed:** new `scripts/paperb/` — `pools.py` 134, `run_benchmark.py` 138, `train.py` 116, `substations.py` 84, `physics.py` 66, `make_paperA_fixture.py` 53, `splits.py` 28, `uncertainty.py` 26, `__init__.py` 26; `scripts/legacy_fixes/hdh_hourly_ridge.py` 63. Total **734 logic lines**, over the ~700 budget (+5 %). Tests: `tests/test_protocol_v1.py` (151 lines, 13 tests) plus `tests/fixtures/paperA_fixture.npz` (0.9 MB). Configs: `protocol_v1{,_quick}.yaml`, `iter02a_timing.yaml`, `iter02a_hdh_ridge{,_quick}.yaml`. Also changed: CLAUDE.md §4/§5/§10 and `.gitignore` (CLAUDE.md and `iterations/` tracked; four csv exceptions), DECISIONS.md (+4), and one markdown cell above notebook cell 88. *Generated:* `results/iter02a_{smoke,timing,hdh_ridge,hdh_ridge_quick}/`; `data/_paperb/pools/` (B\* 68 MB, B 66 MB) and `data/_paperb/features/`.

**Results** (plumbing only, nothing interpreted; timing = 1 seed, full grid, 3 evals):

| quantity | legacy / iter 01 | iter 02a |
|---|---|---|
| B\* / B HP households (fill) | 86 / 47 envelope (1306) | 86 / 47 built, 0 coverage drops (fill 1291 / 1306) |
| substations per seed, train / test / inner | 460 / 130 / – (proposal) | B\*: 460 / 130 / 420; B: 240 / 75 / 260 (all 20 seeds) |
| distinct HP households actually used, train / test | – | B\*: 62 / 20 of 64 / 22 (stations with < 3 dropped) |
| net-load hinge inside observed T range | **8 %** (170 / 2160; T < 12 °C filter) | **100 %** net and HP fits (1010 subs); 2.0 % at a bound; median T_h 16.7 °C (5–95 %: 14.1–19.0) |
| Paper A fixture (6 households) | – | P_base, s_h, T_h, R², b_h, m_h, SF_cold, R²_SF within 1e-6 |
| F14 cell 88 (1000 test subs) | RMSE 55.22 kW, MAPE 19.59 %, α 10 (fit on test) | reproduced exactly; **train fit: 55.53 kW, 20.21 %, α 7.2** (R² 0.895 → 0.894) |
| HP_CoincPeak > HP_Peak | – | 382 / 1010 subs: 100 % at n_hp = 1, 49 % at 2, 18 % at 3, 0 % at ≥ 6 |
| smoke run (`protocol_v1_quick`) | – | 36 s (12 s with feature cache); `metrics.csv` 65 rows, no NaN |
| full 02b runtime (sequential, 50 evals) | 3–3.5 h (proposal: XGBoost, 1 target) | **≈ 141 h**. Per B\* seed: features 125 s. Per target: XGBoost 195 s, Ridge/EN/SVR/PLS 148 s, anchor-only 50 s, bootstrap 67 s, FFNN **2220 s**. B ≈ 0.57 × B\*. Without FFNN: 25 h |

**Assumptions & deviations:**
- **Why CLAUDE.md was ignored.** The repo `.gitignore` gained `CLAUDE.md` and `iterations/` in f8eefa8 ("Update .gitignore", 02:01:54). That was 85 s before the GitHub Desktop stash (02:03:19). There is no global excludesfile and nothing in `.git/info/exclude`.
- **`stash@{0}` (kept, not dropped).** It holds 6 files: CLAUDE.md (older; superseded), `iterations/00-setup-baseline.md` (identical to the tracked copy), `results/iter00_baseline/models/{capacity_swiss.pkl, hockey_delta_calibration.json, xgb_selected_features.json}` and `results/iter00_baseline_quick/models/hockey_delta_calibration.json`. The four model files exist **only** in the stash.
- **SFH own-load dwellings.** They are drawn once at pool build (`pool.seed` 0), from clean single-family dwellings. Each one travels with its HP meter, so "same split, used once" holds for every seed.
- **Target choices.** `P_design` uses T_design = −8 °C at every station, because HEAPO stations are anonymised. For `r`, P_base is the base of the Paper A fit to the non-HP aggregate.
- **HDH baseline.** It keeps the fixed `HDH_THRESH` = 12 °C.
- **Paper A fit.** It is `fit_hockey_stick` on daily means over all days (`outputs._evaluate`, draft §II). The CH/DE feeders use no other variant, since a bathtub fit applies only with cooling. The fixture runs Paper A's own code (commit 56710ef) in a child process on B\* inputs, because Paper A stores no per-household fits.
- **FFNN.** It uses sklearn `MLPRegressor` with epoch-wise early stopping instead of legacy Keras, keeping the legacy grid. Reasons: deterministic, no TensorFlow, and the same stopping rule as XGBoost. y is standardised only for SVR and FFNN (legacy).
- **Inner CV.** Substations are built inside one fold. Iterative models fit on 2 folds and early-stop on the next one; the other models fit on 3.
- **Quick config.** Grid is size 10 × all six p; the anchor-only Linear baseline was added. `metrics.csv` also carries `n_pred_nan`, `mape_n_excluded` (F9) and bootstrap CI rows.

**Problems found:**
- **Bootstrap approximation.** Each replicate keeps only **29 %** of test substations on the full grid (39 % in the smoke run). Large-n_hp substations almost never survive, so CIs describe small feeders. The proposal's multiway product weights would avoid this.
- **HP_CoincPeak > HP_Peak** at n_hp ≤ 5. This is definitional: a raw maximum is compared with a sum of 99.9th percentiles. Flagged, not asserted.
- **Stations below 3 HP households.** HbsbG and z6I (1 household each) are never used. MqO has 2 test households, below 3, so it drops out of test and inner cells. The effective B\* test set is 20 households, and B's is 12.
- **Missing flags.** HEAPO has no backup-rod flag, so `has_hp_add` is NA for all 47 HEAPO households. `has_ewh_in_own_load` is True for 37 / 86 HP households and unknown for 17 (M9).
- **FFNN cost.** It takes 82 % of the runtime (≈ 15 s per hyperopt eval, patience 40).

**Decisions for Alex:**
1. **Paper A variant:** Paper A's daily-mean, all-days fit with latent T_h in (8, 20) °C, for both the s_h / P_design targets and the four baselines. Recommended: **keep it**. Alternative: add the legacy peak-tied min/max reduction as a second baseline for HP_Peak.
2. **Hinge inside the range:** 100 % of fits, 2 % at a bound (legacy 8 %). Recommended: **accept**, keep the bounds and report the at-bound share every run. Also switch the bootstrap to product weights in 02b.
3. **02b budget (≈ 141 h as specified):** Recommended plan, **≈ 7 h wall**:
   - run split seeds in parallel with 4 workers (≈ 20-line runner change; ≈ 0.8 GB each);
   - all non-FFNN models: 20 seeds on B\*, 10 on B;
   - FFNN: B\* only, 5 seeds, arms `none` + `size_peak`, 20 evals, patience 10.

   Alternative: drop FFNN entirely (≈ 5 h wall).
