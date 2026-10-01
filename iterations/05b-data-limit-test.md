# Iteration 05b — Is training data what holds ML back?

**Branch:** `iter/05b-data-limit`, from `main` after 05a is merged.
**Type:** code additions first (≤ ~450 logic lines, Task 1: learning-curve fit, bias–variance columns, oracles, registry extension). If you exceed the budget, stop after Task 1e plus its tests, write a REVIEW for "05b-i", and wait. Then come the runs, in two stages (Task 2), and the results.

The hypotheses and the decision rule below are **pre-registered**: they are fixed before any run and not changed after results are seen. This brief was amended on 2026-10-01, after the 05a-ii-a review and before any 05b run; the amendments are marked **[A]**.

## Amendments from the 05a-ii-a review (Alex, 2026-10-01) — record them in DECISIONS.md
- **[A1] Pools.**
  - Main: GB-EoH Nov 2021 – Oct 2022 (≥ 90 % coverage, the 2 silent-electricity homes excluded).
  - Replication: Oct 2022 – 29 Sep 2023, one day short of 12 months, which is accepted. If that gives < 300 homes, use Sep 2022 – Aug 2023 instead.
  - Call the replication a **temporal replication** (another year, mostly the same homes), never an independent sample.
- **[A2] Flag name.** The 05a D4 flag is called **"filler-variability-limited"**, never "fusion-limited". The rule is unchanged: bins whose capacity-equivalent error from natural year-to-year filler variability exceeds 5 % of HP_Peak (p ≤ 0.5, i.e. Paper A bins ≤ 15, 15–35 and 35–65 %).
  - It marks the floor that real non-HP households' temperature response puts on **any** estimator. It is not a defect of the GB-EoH pool.
  - Mark these bins in every GB-EoH table.
- **[A3] Filler-uncertainty arm.** Arm 7 (below) is required by the 05a D4 rule.
- **[A4] Runtime reductions.** The scientific content is unchanged:
  - cache the Paper A pilot per (seed, draw, n) and reuse it across family jobs;
  - Arm 1 uses netfit × size only (03b's best feature set and anchor), with 2 draws;
  - Arm 3 uses `substations_per_cell_train` ∈ {10, 40};
  - Arm 4 on B\* is physics-only.
- **[A5] Staged runs.** Stage 1 = Arms 1 + 2, then a short interim REVIEW. Stage 2 = Arms 3–7, after Alex's go.
- **[A7] Co-located non-HP response (from the 05a D5 diagnosis, `d5_paperA_diagnostic.md`).** On B\*, the HP homes' **own** non-HP load has a temperature slope ≈ 3.3 × a filler home's (0.018 vs 0.005 kW/K; partly electric water heaters, M9). It scales with n_hp, not N, and neither `paperA_sh_mh` nor `paperA_corr` removes it. Two additions follow, both physics-only:
  - **Split the B\* error decomposition (Arm 4).** Fill contamination becomes two parts:
    - (i) **fillers' response**: oracle O1a replaces only the fillers' load with zero-temperature-response load (each filler's daily-mean deviation from its own temperature fit removed, P_base kept);
    - (ii) **HP homes' own non-HP response**: O1b does the same for the HP homes' own non-HP load only.

    O1 (both removed) stays as before. Report (i) and (ii) per bin. On GB-EoH, (ii) is structurally absent: each HP dwelling's own load is a random LCL filler. State that.
  - **A new label-free physics row, `paperA_corr_own`.** Pilot m_h′ = [s_h(pilot HP homes' **whole-house** load, i.e. HP + own non-HP) − n_pilot · s₀] / P_pilot, and P̂ = max(s_h − N·s₀, 0) / m_h′.
    - The co-located response is thereby folded into the per-unit scale. It needs whole-house meters on the pilot homes (smart meters), and no substation labels.
    - Cross-fitted pilots and the s₀ estimate are as for `paperA_corr`. Invalid estimates → 0, counted.
    - On GB-EoH, `paperA_corr_own` uses the pilot homes' HP load + their assigned filler's load. Because that filler is random, it should approximately equal `paperA_corr`; report both, as a check.
  - **Run it** in Arms 1, 2, 4, 5, 6 and 7 with the other physics rows. It joins the physics rows from which the best physics row is chosen for the criterion. Adding it before any run is pre-registration-safe.
  - **Test:** on a toy pool where the own load has a known slope k per HP home, `paperA_corr_own` recovers capacity within 1 %, while `paperA_corr` is biased by k / m_h per HP home.
- **[A6] Continuous running.** The schedule may also run in the daytime at below-normal priority. Add a `-Continuous` switch to `schedule_overnight.ps1` that omits `-StopAt`. Alex chooses per stage.

## Question
On B\*, no ML configuration beat physics (03b). Is that because ML saw too few distinct HP households (≈ 62), or because net load does not identify capacity beyond what physics already extracts?

Three explanations, not mutually exclusive:
- **D (data):** ML error keeps falling with more distinct households and crosses physics.
- **S (synthetic sample):** ML error falls with more *substations* built from the same households (the limit is the generator's sample size, which is cheap to raise).
- **I (identifiability):** both ML and physics sit near a floor set by fill contamination of s_h and by household-to-household dispersion of the per-unit scale; more data doesn't move it.

## Model families
Linear models tend to plateau early, while flexible models are the ones that should keep improving with more data. Every family therefore gets the extra households. At each n and seed × draw, **one winner per family is chosen by inner-CV WAPE, never by test**, among its models × feature sets {netfit, both} × anchors {size, size_peak} × {direct-log, residual} (Arm 1 uses netfit × size × {direct-log, residual} only, per [A4]):

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

**d. Overnight runner.** Use the queue built in 05a (`scripts/paperb/run_queue.py`). Stage 1: Arm 1 → Arm 2. Stage 2: Arm 7 → Arm 4 → Arm 3 → Arm 5 → Arm 6. Add the pilot cache ([A4]): key (pool, seed, draw, n), atomic writes, and a test that the cached pilot equals a fresh one. Add the `-Continuous` switch ([A6]).

**e. Model registry extension** (`scripts/paperb/train.py`, new `scripts/paperb/models_rawseries.py`). Every new model runs inside the existing grouped inner CV, with seeded hyperopt (≤ 50 evals), with imputation and scaling fitted within folds, and with the direct-log and residual variants.
- **Kernel Ridge:** sklearn `KernelRidge`; tune alpha, gamma and the kernel (RBF / Laplacian).
- **GP regression:** sklearn `GaussianProcessRegressor` with an ARD RBF + WhiteKernel on the standardised log target, marginal-likelihood fit with `n_restarts_optimizer` ≥ 3 and a seed. Log the 5–95 % predictive interval coverage on test as an extra column; it is not used for selection.
- **Random Forest / Extra Trees:** sklearn; tune the number of trees, max_features, min_samples_leaf and max_depth.
- **CatBoost:** pin the version; tune depth, learning rate, l2_leaf_reg and the number of iterations; `thread_count` capped like XGBoost; `random_seed` set.
- **TabPFN:**
  - Use the **TabPFN-3.5 regressor**:
    - The `tabpfn` package must be ≥ 9.0.0 (the first release with 3.5 support). Pin the exact version in `requirements.txt`.
    - Load the local checkpoint explicitly: `TabPFNRegressor(model_path=<TABPFN_MODEL_CACHE_DIR>/tabpfn-v3.5-20260909.safetensors)`. One checkpoint serves both regression and classification, so this is the right file. Do not use the `_multiclass` file.
    - The `-fast-` checkpoint (`ModelVersion.V3_5_FAST`) is out of scope.
    - Verify in a test that the loaded model is this file.
    - The weights are licensed for non-commercial use. This work is non-commercial research (Alex, 2026-09-30); put the licence and version in `method_basis.md`.
    - Record the checkpoint file name (`tabpfn-v3.5-20260909.safetensors`), its SHA-256 and the package version in `config.yaml`.
    - Licence: research and limited internal evaluation only; no commercial or production use of the model or its outputs. State this in `method_basis.md`.
  - **Weights:** Alex has access to the 3.5 weights on Hugging Face and downloads them himself.
    - Load them from the local checkpoint in `TABPFN_MODEL_CACHE_DIR`, so overnight jobs never touch the network.
    - If `TABPFN_MODEL_CACHE_DIR` is unset, or the regressor checkpoint is not there, stop and ask Alex. Do not download weights with his credentials yourself.
    - If the package still asks for a licence acceptance or `TABPFN_TOKEN` when the weights are local, stop and report the exact message.
  - **Secrets:** never print, log or commit any token (`HF_TOKEN`, `TABPFN_TOKEN`). Add `.env` to `.gitignore` if it is not there.
  - No hyperopt: it is in-context learning. Only the ensemble count is set (default), with a seed.
  - CPU only; check that train substations × features stay within its limits.
  - **Do not create accounts or accept licences yourself.** If the local checkpoint cannot be loaded, stop before the TabPFN jobs, print the reason for Alex, and let the queue skip them until it is fixed.
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
- Arm 7 scaling: the scaled fillers' fitted s₀ equals factor × the original (within 2 %) and P_base is unchanged (within 1 %);
- the cached pilot equals a freshly computed one;
- family selection uses inner-CV WAPE only (a sentinel test column must not change the choice);
- every new model: fit/predict round-trip on a toy set, identical output for identical seeds, preprocessing fitted only on training folds (leakage sentinel), and the residual composition ẑ = 0 → P̂_A;
- TabPFN: the loaded model reports version 3.5, the recorded checkpoint hash matches the file, and no token string appears in any output file (grep test).

## Task 2 — Runs
Run `configs/iter05b_quick.yaml` interactively first (it must pass before anything is scheduled). Then:
1. estimate the full runtime per arm from 05a's timing probe and the quick run;
2. commit;
3. hand Alex the scheduling command.

Runtime is not a constraint, but use the [A4] reductions, and re-estimate after them. Report the actual wall time of each arm.

**Stage 1 (Arms 1 + 2).** When it finishes, write `results/iter05b_data_limit/REVIEW_stage1.md`, one page in the §9 template, containing:
- the D verdict per family and overall, and F if it applies (the rule needs Arms 1–2 only);
- the learning-curve figure;
- the headline criterion table, with the filler-variability-limited bins marked.

Then stop, and wait for Alex's go for Stage 2.

**Stage 2 (Arms 3–7)** in this order: Arm 7 → Arm 4 → Arm 3 → Arm 5 → Arm 6. Arm 4's B\* part includes the [A7] split. The final REVIEW.md comes after Stage 2. Its decisions must also cover: does `paperA_corr_own` close the gap to the label-calibrated rows on B\* (overall and per bin)?

| Arm | Pool / seeds | What |
|---|---|---|
| **1 — Learning curve** [stage 1] | GB-EoH main / 10 seeds × **2** draws | n ∈ {16, 32, 62, 100, 200, all}: all physics rows; all five families, each with all its models × **netfit × size** × {direct-log, residual} (the raw-series family: size × {direct-log, residual}); the inner-CV winner per family is recorded, and all candidates are logged |
| **2 — Headline** [stage 1] | GB-EoH main / 20 seeds, n = all | anchors {size, size_peak} × feature sets {netfit, both} × {direct-log, residual} × every model of the five families, plus all physics rows. Apply the 03b Task 6 criterion (16/20 seeds, median ≤ −1 pp) per configuration and per family winner |
| **3 — Households vs substations** [stage 2] | GB-EoH main / 10 seeds × 1 draw | n ∈ {62, all} × `substations_per_cell_train` ∈ **{10, 40}**: all five families (inner-CV winner) + physics rows |
| **4 — Oracles** [stage 2] | GB-EoH main / 20 seeds (all of O1–O2 incl. ML-on-O1); **B\* / 20 seeds, physics only** (O1/O2 physics, decomposition, dispersion floor) | O1, O2, the decomposition and the dispersion floor |
| **5 — B\* under v1.1** [stage 2] | B\* / 20 seeds | physics rows + all five families (incl. FFNN at the full budget) with p = 0.8 added. Checks that the 03b conclusion holds on the new grid, and gives FFNN the fair test it did not get in 02b |
| **6 — Temporal replication** [stage 2] | GB-EoH Oct 2022 – Sep 2023 ([A1]) / 10 seeds, n = all | physics rows + all five families |
| **7 — Filler uncertainty** [stage 2] | GB-EoH main / 10 seeds, n = all | the fillers' temperature response scaled ×0.5 and ×1.5: scale each filler household's load deviation from its own daily-mean–temperature fit below its T_h, so that s₀ scales by the factor while P_base and the profile shape are kept. Run all physics rows (including `paperA_corr` with s₀ estimated from the scaled train fillers, and separately with the unscaled s₀, i.e. a mis-specified correction) + all five families. Report ΔWAPE vs ×1.0 per bin |

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
- Fillers are analog-mapped LCL households (2011–14, London), not same-year GB households. Quote 05a's D5 swap-test ΔWAPE next to every GB-EoH headline number as the bound on the fusion error. Mark the filler-variability-limited bins ([A2]), and quote Arm 7's sensitivity in the final REVIEW.

## Out of scope
- Other targets and the daily arm (06).
- Transfer between pools (07).
- The simulator.
- New feature sets.
- Changing the decision rule after results.

## Acceptance criteria
- [ ] Task 1 is implemented with tests, and `pytest` passes.
- [ ] The quick config passed interactively. The arms are queued, and the scheduling command is printed for Alex.
- [ ] Stage 1 is done, and `REVIEW_stage1.md` is written; Alex has given the go for Stage 2.
- [ ] All arms have completed (possibly over several nights; `STATUS.md` shows 0 remaining), or the failed jobs are listed with their reason. Actual wall times are reported.
- [ ] `metrics.csv`, `summary.csv`, the tables and the figures are in `results/iter05b_data_limit/`.
- [ ] `data/` (outside `data/_paperb/`) and `models/` are unmodified.
- [ ] REVIEW.md follows the §9 template. The decisions must cover at least:
  1. **the verdict** under the pre-registered rule (D / S / I / inconclusive), overall and per bin;
  2. which error component dominates (the decomposition), and what that means for the paper's lead;
  3. whether GB-EoH becomes the headline pool for 06 and 07, or stays the second pool;
  4. the simulator go/no-go: worth building only if the verdict is D, or the S test holds and the generator can't supply more substations.
