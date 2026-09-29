# Iteration 03a — Fair test of ML against the physics estimator: code and tests

**Branch:** `iter/03a-fair-test-code`, from `main` after 02b is merged.
**Type:** implementation plus tests, with a smoke run only. **No results are interpreted** (that is 03b).
**Size budget:** ~600 logic lines, excluding tests. If you exceed it, stop after Tasks 1–3 plus their tests, write the REVIEW for "03a-i", and wait.

## Why this iteration
02b showed that on `HP_Peak` (B\*, 20 seeds):
- the physics baselines beat every ML model (slope-only MAPE 35 % vs XGBoost 48 %);
- ML adds ≈ 0 R² over a linear model on [size, peak].

Before the paper concludes that ML adds nothing, ML must get a fair test. It needs:
- the physics quantities as features;
- models suited to ~60 independent households;
- residual learning on top of the physics estimate;
- Paper A's own estimator (s_h / m_h) as the reference;
- a learning curve that shows whether the limit is data or features.

03a builds all of this; 03b runs it.

## Decisions carried into this iteration (from the 02b review, 2026-09-29)
- **FFNN** leaves the main tables. Keep the code, but switch it off by default (`models.ffnn: false`).
- **Pools:** B\* (20 seeds) is the only headline pool; B is a sensitivity arm; pool A is dropped from later iterations.
- **WAPE** (Σ|ŷ − y| / Σy) becomes the primary metric, for comparability with Paper A. MAPE and R² stay as secondary metrics.
- **The paper's lead** (identifiability vs ML gain) is decided after 03b, not now.
- **Iteration plan renumbered:**

| Iteration | Content |
|---|---|
| 03a/03b | Fair test |
| 04 | Other targets + daily arm (RQ1) |
| 05 | Transfer (RQ3) |
| 06–07 | Change detection (RQ4) |
| 08+ | Freeze and draft |

## Task 0 — Bookkeeping (first commit)
- **DECISIONS.md:** add the decisions above.
- **CLAUDE.md:**
  - §4: add WAPE as the primary metric.
  - §1: add the renumbered iteration plan as a short list.
  - §10: note that the fixed-T_base bin misalignment (T_base 12 °C vs fitted T_h median 16.7 °C) is addressed by the new feature set, and that the legacy windowed-HDD set is kept unchanged as `whdd`.
- **Stash:** check whether `stash@{0}` still exists and report it. **Do not drop it**; Alex does that manually.

## Task 1 — Paper A estimator (`scripts/paperb/physics.py`)
1. **Port the SF fit** from `hp-sensitivity-paper` **unchanged**:
   - SF(t) = aggregated HP load / installed capacity, with Paper A's capacity definition;
   - daily means, the same fit function and bounds.
2. **Capacity definition.** Check Paper A's definition of P^max (eq. `pk`: which percentile, which resolution) against `HP_Peak`. If they differ, report the difference and compute the estimator against `HP_Peak`. Also report, in the REVIEW, the error against Paper A's definition on a quick subset.
3. **Estimator `paperA_sh_mh`.** P̂ = s_h(net-load fit of the substation) / m_h(pilot).
   - The pilot is the **aggregated train-split HP households of the same seed**.
   - Variant `paperA_sh_mh_station`: a station-matched pilot, used when there are ≥ 10 train HP households at that station; otherwise it falls back to the full pilot, and the fallbacks are counted.
4. **Fixture test.** Using Paper A's own code on its own Kloten inputs, reproduce the pilot m_h reported in its draft (≈ 0.0187 for one split, or whatever the committed Paper A results contain) within 1e-6.
5. **Invalid estimates.** When s_h ≤ 0 or the fit fails, P̂ is invalid. Handle it with an explicit rule (predict 0 and count it). Never drop it silently.

## Task 2 — Net-load fit feature set `netfit` (`scripts/paperb/features_netfit.py`)
For each substation, fit Paper A's net-load hockey stick (the 02a port) three times:
- `all`: all days;
- `wd`: weekdays that are not holidays;
- `we`: weekends plus public holidays.

Holidays come from the `holidays` package, `country="CH", subdiv="ZH"`. Pin it in `requirements.txt`.

Features per fit (prefix `nf_{all|wd|we}_`):
- `s_h`, `T_h`, `P_base`, `R2_h`, `n_heat_days`, `at_bound` (0/1);
- `cold_resp` = s_h · (T_h − T_q05), where T_q05 is the 5th percentile of daily mean temperature;
- `r_hat` = s_h / P_base.

Cross-fit features:
- `nf_ratio_sh_we_wd` = s_h(we) / s_h(wd);
- `nf_ratio_Pbase_we_wd`.

Feeder-referenced temperature features: mean daily load in three θ bins, where θ = (T_h − T) / (T_h − T_q05) with T_h from the `all` fit (θ ≤ 0 / 0–0.5 / > 0.5). Normalise each bin by P_base.

Size anchors: `size`, `peak`, as before.

- Keep the set small (≈ 25–30 columns) and document every column in a table in the module docstring.
- A weekend fit with fewer than `MIN_HEATING_DAYS` heating days is NaN, and `n_heat_days` records why. Imputation uses the train median, inside the pipeline (never fitted on test).
- Feature-set options for runs: `whdd` (legacy windowed-HDD, unchanged), `netfit`, `both`.

## Task 3 — Model registry (`scripts/paperb/train.py`)
- Add `LinearRegression` and `Lasso`, alongside Ridge, ElasticNet, SVR, PLS and XGBoost. Every model is tuned with the existing grouped inner CV; Linear has nothing to tune.
- Linear-family models get a pipeline of imputer → scaler, fitted inside the folds.
- Add `target_transform: none | log`. Log models predict log(y) and back-transform with exp, **without** a smearing correction (note this in the docstring).
- Add an XGBoost option `monotone_sh: true`: a +1 monotone constraint on every `nf_*_s_h` and `nf_*_cold_resp` column, and 0 elsewhere.

## Task 4 — Residual learning (`scripts/paperb/residual.py`)
- The target is z = log(y) − log(P̂_A), where P̂_A is `paperA_sh_mh` with the seed's pilot.
- A model predicts ẑ, and the final prediction is ŷ = P̂_A · exp(ẑ).
- Residual models: Ridge, Lasso and ElasticNet, tuned with regularisation strength allowed up to "all-zero", plus XGBoost with a shallow configuration (max_depth ≤ 3, strong regularisation).
- The zero-residual model, i.e. P̂_A itself, is always reported next to them.
- Substations with an invalid P̂_A (Task 1.5) are excluded from residual training and are scored with the fallback rule. Report their count.

## Task 5 — Learning-curve harness (`scripts/paperb/learning_curve.py`)
- Within each split seed, subsample the **train HP households** to n ∈ {16, 32, 48, all}, with 3 subsample draws per n.
- Rebuild the train substations and the inner folds from the subsample only, under the same generator rules. Record cells that become infeasible.
- **The test set stays identical** across n.
- The Paper A pilot uses the same subsample, so the estimator and the ML models see the same labelled households.
- Output the usual `metrics.csv` rows, with the extra columns `n_train_hp` and `lc_draw`.

## Task 6 — Metrics and summary
- Add `wape` to `compute_metrics`, and make it the first metric in `summary.csv` and in all tables.
- In `tables.py`, add an ablation table: rows are feature set × {direct, residual} × model; columns are WAPE / MAPE / R² as median [5 %–90 %].

## Task 7 — Tests (`tests/test_fair_test.py`)
- The holiday calendar marks the known ZH holidays of 2023, and the `wd`/`we` partition is disjoint and covers every day.
- The Paper A estimator fixture reproduces Paper A's committed m_h.
- Round trips: the log transform, and the residual composition ŷ = P̂_A·exp(ẑ) with ẑ = 0 reproducing P̂_A exactly.
- The monotone constraints are set only on the intended columns.
- Learning-curve subsamples are subsets of the train HP households, the test membership is identical across n, and the pilot equals the subsample.
- WAPE matches a hand-computed example.
- The imputer and scaler are fitted only on training folds (check with a leakage sentinel feature).

## Task 8 — Smoke run
Run `configs/iter03_quick.yaml`:
- 1 seed and a small grid;
- feature sets `whdd`, `netfit`, `both`, direct and residual;
- models Linear, Ridge and XGBoost;
- the Paper A estimator;
- one learning-curve point (n = 16, 1 draw).

Report the runtime and extrapolate the 03b budget. The proposed 03b plan is:
- B\* with 20 seeds, three feature sets × {direct, residual} × 7 models × 2 target transforms;
- the learning curve for the best model of each family, plus the Paper A estimator;
- B with 10 seeds for the main configuration only.

If the full plan exceeds 8 h wall time, propose cuts, e.g. log-transform only or fewer models on `whdd`.

## Out of scope
- Full runs and interpretation (03b).
- Other targets and the daily arm (04).
- Transfer (05).
- Notebook edits.
- Changing the API of `hp_common.py`, `hp_pools.py`, `hp_capacity.py` or `heapo.py`.

## Acceptance criteria
- [ ] DECISIONS.md and CLAUDE.md are updated, and the stash status is reported.
- [ ] Tasks 1–6 are implemented, and `pytest` passes, including the Paper A m_h fixture.
- [ ] The smoke run completes and writes a valid `metrics.csv` with WAPE.
- [ ] `data/` (outside `data/_paperb/`) and `models/` are unmodified.
- [ ] REVIEW.md follows the §9 template. The decisions must cover at least:
  1. the pilot definition: all train HP households vs station-matched;
  2. the handling of invalid Paper A estimates;
  3. the Paper A vs `HP_Peak` capacity-definition difference, if any;
  4. the 03b budget and grid.
