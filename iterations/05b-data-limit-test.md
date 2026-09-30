# Iteration 05b — Is training data what holds ML back?

**Branch:** `iter/05b-data-limit`, from `main` after 05a is merged.
**Type:** code additions (≤ ~450 logic lines, Task 1: learning-curve fit, bias–variance columns, oracles, registry extension). If you exceed it, stop after Task 1e plus its tests, write a REVIEW for "05b-i" and wait, then runs (overnight) and results. The hypotheses and the decision rule below are **pre-registered**: they are fixed before any run, and they are not changed after results are seen.
05a's review may change the pool details. It does not change the rule.

## Question
On B\*, no ML configuration beat physics (03b). Is that because ML saw too few distinct HP households (≈ 62), or because net load does not identify capacity beyond what physics already extracts?

Three explanations, not mutually exclusive:
- **D (data):** ML error keeps falling with more distinct households and crosses physics.
- **S (synthetic sample):** ML error falls with more *substations* built from the same households (the limit is the generator's sample size, which is cheap to raise).
- **I (identifiability):** both ML and physics sit near a floor set by fill contamination of s_h and by household-to-household dispersion of the per-unit scale; more data doesn't move it.

## Model families
Linear models tend to plateau early, while flexible models are the ones that should keep improving with more data. Every family therefore gets the extra households. At each n and seed × draw, **one winner per family is chosen by inner-CV WAPE, never by test**, among its models × feature sets {netfit, both} × anchors {size, size_peak} × {direct-log, residual}:

| Family | Models (all on the tabular feature sets) |
|---|---|
| **Linear** | Linear, Ridge, Lasso, ElasticNet, PLS |
| **Kernel** | SVR (RBF); Kernel Ridge (RBF / Laplacian, tuned); Gaussian Process regression (ARD RBF + white noise, on log y; also report its predictive intervals) |
| **Trees** | XGBoost (residual variant shallow, max_depth ≤ 3); Random Forest; Extra Trees; CatBoost |
| **Neural** | FFNN at the protocol's standard budget (50 hyperopt evals, patience 20; not the reduced 02b budget); TabPFN (in-context foundation model for small tabular data; see Task 1e) |
| **Raw-series** (feature-free) | a small 1D-CNN on the substation's raw daily series (Task 1e); no hand-made features |

The raw-series family answers a separate question: **do the hand-made features lose information?** If it beats the other families at large n, the limit was features, not data or identifiability. Report it in its own row of the verdict table.

**"Reference set" is not a model filter.** Lasso direct/residual and XGBoost direct are the 03b reference set, named in the tables for continuity. Every model above stays in the pipeline and in every arm.

## Pre-registered decision rule
**Setup:**
- Pool GB-EoH 2021/22, test set fixed across n.
- At each n, take each family's inner-CV winner.
- Compare it with the best physics row at the same n: paired per seed × draw, ΔWAPE = family winner − physics.
- The rule is applied **per family**. The overall verdict is D if **any** family meets D; report which family, and note that 5 families were tested (multiplicity).
- If the raw-series family meets D, or beats every tabular family's winner at n = all under the 03b criterion, add the verdict **F (features)**.

**Verdicts:**
- **Data-limited (D)** if both hold:
  1. ML WAPE falls from n = 100 to n = all by ≥ 1 pp (median), with ≥ 80 % of seed × draws improving;
  2. at n = all, ML meets the 03b criterion (ΔWAPE < 0 in ≥ 80 % of seed × draws and median ΔWAPE ≤ −1 pp) — **or** the fitted asymptote (Task 1a) lies below the best physics WAPE in ≥ 80 % of seeds.
- **Not data-limited (I or features)** if ML WAPE changes by < 1 pp between n = 100 and n = all, **and** ML stays at or above the best physics row.
- **Inconclusive** otherwise. Then report n\*, the n at which the fitted curve reaches physics, as median [5–90 %] over seeds.
- **The S test** (Arm 3) is read separately. S holds if raising `substations_per_cell_train` from 10 to 40 at fixed n lowers ML WAPE by ≥ 1 pp (median, ≥ 80 % of seeds).

Apply the rule overall and per Paper A penetration bin. Report every verdict, whichever way it goes.

## Task 1 — Code additions
**a. Learning-curve fit** (`scripts/paperb/lc_fit.py`)
- Per seed, fit WAPE(n) = a + b·n^(−c) to the median over draws, with c ∈ (0, 2].
- Report a (asymptote), c and n\* as median [5–90 %] over seeds.
- Flag fits where c hits a bound or a < 0.

**b. Bias–variance columns.** For every model × n, log WAPE on:
- the **train** substations (in-sample);
- the **inner-CV** predictions;
- the **test** substations.

test − train is the variance proxy; a high train error is the bias proxy.

**c. Oracle diagnostics** (`scripts/paperb/oracle.py`). These use label-side information that a DSO does not have. They are **diagnostics only**: they never appear as competitors in the headline tables.
- **O1 — perfect disaggregation.** The HP-only aggregate replaces the net load:
  - physics: P̂ = s_h(HP aggregate) / m_h(pilot);
  - ML: netfit features of the HP aggregate + size, one inner-CV winner per family.
- **O2 — perfect scale.** P̂ = s_h(HP aggregate) / m_h(true), where m_h(true) is fitted on the substation's own HP members. What remains is fit noise.
- **Error decomposition** of `paperA_sh_mh`, per bin and per n_hp:
  - WAPE(net, pilot) − WAPE(O1) = **fill contamination**;
  - WAPE(O1) − WAPE(O2) = **scale (m_h) dispersion**;
  - WAPE(O2) = **fit noise**.
- **Per-unit dispersion floor:**
  - the household CV of `HP_Peak_i / s_h,i`;
  - at substation level, the CV of `HP_Peak / s_h(HP aggregate)` as a function of n_hp.

  This is the floor for any estimator built on s_h.

**d. Overnight runner.** Use the queue built in 05a (`scripts/paperb/run_queue.py`). Add the 05b arms to it in the priority order Arm 1 → Arm 2 → Arm 4 → Arm 3 → Arm 5 → Arm 6, so the most important results land first.

**e. Model registry extension** (`scripts/paperb/train.py`, new `scripts/paperb/models_rawseries.py`). Every new model runs inside the existing grouped inner CV, with seeded hyperopt (≤ 50 evals), with imputation and scaling fitted within folds, and with the direct-log and residual variants.
- **Kernel Ridge:** sklearn `KernelRidge`; tune alpha, gamma and the kernel (RBF / Laplacian).
- **GP regression:** sklearn `GaussianProcessRegressor` with an ARD RBF + WhiteKernel on the standardised log target, marginal-likelihood fit with `n_restarts_optimizer` ≥ 3 and a seed. Log the 5–95 % predictive interval coverage on test as an extra column; it is not used for selection.
- **Random Forest / Extra Trees:** sklearn; tune the number of trees, max_features, min_samples_leaf and max_depth.
- **CatBoost:** pin the version; tune depth, learning rate, l2_leaf_reg and the number of iterations; `thread_count` capped like XGBoost; `random_seed` set.
- **TabPFN:**
  - Use the **TabPFN-3.5 regressor**:
    - The `tabpfn` package must be ≥ 9.0.0 (the first release with 3.5 support). Pin the exact version in `requirements.txt`.
    - Select the model with `ModelVersion.V3_5` via `create_default_for_version()`, and verify the selection in a test.
    - The weights are licensed for non-commercial use. This work is non-commercial research (Alex, 2026-09-30); put the licence and version in `method_basis.md`.
    - Record the exact checkpoint file name, its SHA-256 and the package version in `config.yaml`.
  - **Weights:** Alex has access to the 3.5 weights on Hugging Face and downloads them himself.
    - Load them from the local checkpoint in `TABPFN_MODEL_CACHE_DIR`, so overnight jobs never touch the network.
    - If `TABPFN_MODEL_CACHE_DIR` is unset, or the regressor checkpoint is not there, stop and ask Alex. Do not download weights with his credentials yourself.
    - If the package still asks for a licence acceptance or `TABPFN_TOKEN` when the weights are local, stop and report the exact message.
  - **Secrets:** never print, log or commit any token (`HF_TOKEN`, `TABPFN_TOKEN`). Add `.env` to `.gitignore` if it is not there.
  - No hyperopt: it is in-context learning. Only the ensemble count is set (default), with a seed.
  - CPU only; check that train substations × features stay within its limits.
  - The first download needs a Prior Labs login or `TABPFN_TOKEN`. **Do not create accounts or accept licences yourself.** If no token is available, stop before the TabPFN jobs, print the instruction for Alex, and let the queue skip them until it is set.
  - Add the TabPFN citations to `method_basis.md` after checking them: Hollmann et al., Nature 2025 (TabPFN v2), plus the TabPFN-3 / 3.5 reference or technical report, if one exists.
- **Raw-series 1D-CNN** (PyTorch, deterministic, seeded):
  - Input per substation: 365 × 2 chronological daily mean net load (divided by the size anchor) and daily mean T, plus the size anchor as a scalar joined after pooling.
  - Architecture: 2–3 conv blocks → global average pooling → dense head.
  - Tune the width, kernel size, dropout, weight decay and learning rate (30 evals), with early stopping on a household-disjoint inner fold, never on the scored fold.
  - Output: log y (direct) or z (residual).
  - Record the parameter count, and flag it if it exceeds 10 × the number of train substations.
- Add `catboost`, `tabpfn` and (if not already present) `torch` to `requirements.txt` with pins. Report the install size.
- **LightGBM is deliberately left out**: it is too close to XGBoost, and leaf-wise growth overfits at this sample size.

**f. Tests:**
- the oracles never leak into non-oracle rows (a sentinel check);
- the LC fit recovers known (a, b, c) on synthetic curves;
- the train/inner/test WAPE columns are computed on disjoint sets;
- family selection uses inner-CV WAPE only (a sentinel test column must not change the choice);
- every new model: fit/predict round-trip on a toy set, identical output for identical seeds, preprocessing fitted only on training folds (leakage sentinel), and the residual composition ẑ = 0 → P̂_A;
- TabPFN: the loaded model reports version 3.5, the recorded checkpoint hash matches the file, and no token string appears in any output file (grep test).

## Task 2 — Runs
Run `configs/iter05b_quick.yaml` interactively first (it must pass before anything is scheduled). Then:
1. estimate the full runtime per arm from 05a's timing probe and the quick run;
2. commit;
3. hand Alex the scheduling command.

Runtime is not a constraint. The runs can span several nights, and REVIEW.md is written only after all arms have finished. Report the actual wall time of each arm.

| Arm | Pool / seeds | What |
|---|---|---|
| **1 — Learning curve** | GB-EoH 2021/22 / 10 seeds × 3 draws | n ∈ {16, 32, 62, 100, 200, all}: all physics rows; all five families, each with its full model × feature set × anchor × {direct-log, residual} grid (the raw-series family: anchor × {direct-log, residual}); the inner-CV winner per family is recorded, and all candidates are logged |
| **2 — Headline** | GB-EoH 2021/22 / 20 seeds, n = all | anchors {size, size_peak} × feature sets {netfit, both} × {direct-log, residual} × every model of the five families, plus all physics rows. Apply the 03b Task 6 criterion (16/20 seeds, median ≤ −1 pp) per configuration and per family winner |
| **3 — Households vs substations** | GB-EoH / 10 seeds × 1 draw | n ∈ {62, all} × `substations_per_cell_train` ∈ {10, 20, 40}: all five families (inner-CV winner) + physics rows |
| **4 — Oracles** | GB-EoH and B\* / 20 seeds | O1, O2, the decomposition and the dispersion floor |
| **5 — B\* under v1.1** | B\* / 20 seeds | physics rows + all five families (incl. FFNN at the full budget) with p = 0.8 added. Checks that the 03b conclusion holds on the new grid, and gives FFNN the fair test it did not get in 02b |
| **6 — Replication** | GB-EoH 2022/23 / 10 seeds, n = all | physics rows + all five families |

**No cuts for runtime.** If the estimate exceeds about 3 nights (~30 h), report it before scheduling and propose where to reduce. Alex decides.

## Task 3 — Tables and figures (`results/iter05b_data_limit/`)
1. **Learning-curve figure:**
   - WAPE vs n (distinct train HP households, log x-axis), GB-EoH;
   - B\*'s 03b curve overlaid, with n = 62 marked;
   - bands 5–90 % over seed × draws;
   - physics rows drawn as curves too, since their pilot also grows with n.
2. **Learning-curve table:** median [5–90] WAPE per n, ΔWAPE vs the best physics row, and the win share.
3. **Asymptote table:** a, c and n\* per family.
4. **Bias–variance table:** train / inner-CV / test WAPE per family and n. Also report which model won each family at each n (a win-frequency table).
5. **Arm 3 table:** WAPE per n × substations per cell.
6. **Error-decomposition figure:** stacked bars (fill contamination / scale dispersion / fit noise) per Paper A bin, for GB-EoH and B\*, with ML's and physics' actual WAPE marked.
7. **Headline tables for GB-EoH:** the 03b headline format, the ablation, and the criterion table overall and per bin.
8. **Verdict table:** each rule in the pre-registered section, its inputs, and its outcome (D / S / I / inconclusive), overall and per bin.

**Cautions to state in the results:**
- The configuration is selected by inner CV within each family; 5 families and many configurations are tested (multiplicity).
- The GB-EoH labels are 30-min, B\*'s are 15-min: compare gaps to physics across pools, not levels.
- Fillers are analog-mapped LCL households (2011–14, London), not same-year GB households. Quote 05a's D5 swap-test ΔWAPE next to every GB-EoH headline number as the bound on the fusion error.

## Out of scope
- Other targets and the daily arm (06).
- Transfer between pools (07).
- The simulator.
- New feature sets.
- Changing the decision rule after results.

## Acceptance criteria
- [ ] Task 1 is implemented with tests, and `pytest` passes.
- [ ] The quick config passed interactively. The arms are queued, and the scheduling command is printed for Alex.
- [ ] All arms have completed (possibly over several nights; `STATUS.md` shows 0 remaining), or the failed jobs are listed with their reason. Actual wall times are reported.
- [ ] `metrics.csv`, `summary.csv`, the tables and the figures are in `results/iter05b_data_limit/`.
- [ ] `data/` (outside `data/_paperb/`) and `models/` are unmodified.
- [ ] REVIEW.md follows the §9 template. The decisions must cover at least:
  1. **the verdict** under the pre-registered rule (D / S / I / inconclusive), overall and per bin;
  2. which error component dominates (the decomposition), and what that means for the paper's lead;
  3. whether GB-EoH becomes the headline pool for 06 and 07, or stays the second pool;
  4. the simulator go/no-go: worth building only if the verdict is D, or the S test holds and the generator can't supply more substations.
