# Iteration 02b — Benchmark rerun under protocol v1

**Branch:** `iter/02b-benchmark-v1`, from `main` after 02a is merged.
**Type:** runs + results. Code changes are limited to the parallel runner, the across-split summary and the results tables/figures (target ≤ 300 logic lines).
**Target this iteration:** `HP_Peak` only (the legacy target), so the results stay comparable with legacy. Other targets come in iteration 03.

## Decisions this iteration implements (Alex, 2026-09-29)
1. **Physics fit:** Paper A's daily-mean, all-days fit with latent T_h in (8, 20) °C, as ported in 02a. No min/max variant.
2. **Uncertainty:** **no product weights and no within-split bootstrap.** Report the median ± std and the 5 %–90 % band across split seeds.
3. **Budget:** the agent's ≈ 7 h plan plus a legacy-pool arm (see Task 3).
4. **Stash:** restore the four iter-00 model files to disk, then drop `stash@{0}`.

## Task 0 — Bookkeeping
- **Stash.** Restore these files from the stash's untracked tree (`stash@{0}^3`):
  - `results/iter00_baseline/models/capacity_swiss.pkl`
  - `results/iter00_baseline/models/hockey_delta_calibration.json`
  - `results/iter00_baseline/models/xgb_selected_features.json`
  - `results/iter00_baseline_quick/models/hockey_delta_calibration.json`

  Record their MD5s, check that they exist on disk, then `git stash drop stash@{0}`. Do not restore the stash's CLAUDE.md or iterations file, since both are superseded.
- **DECISIONS.md:** add the four decisions above.
- **CLAUDE.md:**
  - §4: replace "Cluster uncertainty" with "Uncertainty = across-split summary (median, mean ± std, 5 %–90 %). No bootstrap unless an iteration says so."
  - §5: note "`HP_CoincPeak` definition to be revisited in 03 (raw max vs 99.9th pct)".
  - §10: add "HDH baseline uses fixed 12 °C base; fitted T_h median 16.7 °C (revisit in 03)".

## Task 1 — Parallel runner
- Run split seeds in parallel (4 workers). Cap threads per worker:
  - XGBoost `n_jobs` = floor(cores / workers);
  - `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` set before any import in each worker.
- **Determinism test:** the quick config with 1 worker and with 4 workers must give identical `metrics.csv` (value-exact). Add it to `tests/`.
- Leave the bootstrap code in place but switch it off in `protocol_v1.yaml` (`uncertainty.bootstrap: false`).

## Task 2 — Across-split summary
`scripts/paperb/summarise.py` takes `metrics.csv` and produces `summary.csv`.
- Group by `(pool, target, method, anchor, metric[, cell])`.
- Report `n_seeds, median, mean, std, q05, q90`.
- Take the band from config (`summary_band: [0.05, 0.90]`) so it can be changed without code edits.

## Task 3 — Runs
Run `quick` first. Then launch the full runs and report the actual wall time.

| Arm | Pool | Seeds | Models | Anchor arms |
|---|---|---|---|---|
| Main | B\* | 20 | XGBoost, Ridge, ElasticNet, SVR, PLS | none, size, size_peak |
| Main-FFNN | B\* | 5 | FFNN (20 evals, patience 10: **reduced budget, label it so**) | none, size_peak |
| Sensitivity | B | 10 | XGBoost, Ridge, ElasticNet, SVR, PLS | none, size, size_peak |
| Legacy-pool | A (57-household HEAPO 2023, protocol v1: no stacking, household-disjoint, grouped CV) | 10 | XGBoost | none, size_peak |

In every arm, also run:
- the anchor-only baselines (linear + XGBoost on `[size]`, `[peak]`, `[size, peak]`);
- the physics baselines (slope-only map, slope + base, calibrated delta, **fixed-base HDH** — label it so).

Metrics per seed:
- RMSE, MAE, MAPE (with the count of excluded zero targets) and R²;
- per (penetration bin × size bin) cell, not only overall;
- `n_hp_households`, `n_substations`;
- for physics methods, the share of fits at a T_h bound.

## Task 4 — Tables and figures (`results/iter02b_benchmark/`)
1. **Main table (B\*):** method × anchor. Show R² and MAPE as median [5 %–90 %] across seeds.
2. **Protocol effect table:** XGBoost (`size_peak`), best physics baseline and peak-only baseline across
   - legacy CSV (legacy protocol, pool A);
   - pool A under v1;
   - B\* under v1;
   - B under v1.

   This separates the stacking/leakage effect (legacy → A-v1) from the pool effect (A-v1 → B\*-v1).
3. **ML gain over anchor-only (F1):** ΔR² and ΔMAPE of each ML model against the best anchor-only baseline with the same anchor, per seed, then summarised. This is the number that measures what ML adds.
4. **Error vs penetration and vs size** for XGBoost, peak-only and the best physics baseline (B\*). This checks whether the legacy "niche" structure survives under v1.
5. **Figures:** one per table (PNG + PDF); box/strip plots across seeds; no single-seed point estimates.

## Out of scope
- Other targets, the daily arm, TCL classes (03).
- Transfer: WPuQ, FeederBW, UKPN (04).
- Feature-set changes, latent-base HDH, the `HP_CoincPeak` definition.
- Interpreting results beyond stating them. REVIEW.md reports numbers and flags surprises; the framing is decided in review.

## Acceptance criteria
- [ ] The stash is dropped after the 4 files are restored and their MD5s recorded.
- [ ] The determinism test (1 vs 4 workers) passes, and `pytest` passes overall.
- [ ] All four arms have completed, or a failed arm is listed with its reason. The actual wall time is reported.
- [ ] `metrics.csv`, `summary.csv`, the four tables and the figures are in `results/iter02b_benchmark/`.
- [ ] `data/` (outside `data/_paperb/`) and `models/` are unmodified.
- [ ] REVIEW.md is written using the §9 template. The decisions must cover at least:
  1. whether the ML gain over anchor-only is large enough to carry RQ2, or whether the paper leads with the anchor/identifiability result;
  2. whether FFNN stays in the paper;
  3. anything in the protocol-effect table that changes the plan for 03/04.
