# Iteration 02b — Benchmark rerun under protocol v1
**Goal:** Rerun the HP_Peak benchmark under protocol v1 (parallel seeds, across-split summary, no bootstrap) on pools B\*, B and legacy pool A, and report what ML adds over anchor-only and physics baselines.

**Branch / commit:** iter/02b-benchmark-v1 @ 9bfa9ab (code); tables/figures/results committed on top. Branched from `main` (02a merged).

**Changed:** ≈ **540 logic lines** (over the ~300 target; splits cleanly into runner/summary/pool A ≈ 265 and `tables.py` 275): `run_benchmark.py` +151/−70, `tables.py` 275 (new), `summarise.py` 35 (new), `pools.py` +36 (pool A), `__init__.py` +23 (deep-merge config, `--set`), `splits.py`/`substations.py`/`train.py` ≈ 25. Tests: `test_parallel_runner.py` (determinism), +1 pool-A test (33 pass). Configs: `iter02b_{main,ffnn,sens_b,legacy_a,quick}.yaml`; `protocol_v1.yaml` +`uncertainty`, `parallel`. Also CLAUDE.md §4/§5/§10, DECISIONS.md (+4), `.gitignore`. *Generated:* `results/iter02b_benchmark/` (four `arm_*` dirs, `metrics.csv` 95 k rows, `summary.csv`, 4 tables csv+md, 5 figures png+pdf), `results/iter02b_quick/`, `data/_paperb/pools/a_2023*`, `data/_paperb/features/`.

**Results** (HP_Peak, test; median [5 %–90 %] over split seeds; R² / MAPE %; legacy = one split, seed 42). **Wall time: 82 min in total** (A 394 s, main 3418 s, B 948 s, FFNN 156 s), not the ≈ 7 h planned.

| | legacy CSV (pool A, stacked) | A under v1 (10 seeds) | **B\* v1 (20)** | B v1 (10) |
|---|---|---|---|---|
| XGBoost [size_peak] | 0.934 / 17.9 | 0.03 [−2.7–0.5] / 56.6 | **0.858** [0.66–0.90] / **47.8** [38–59] | 0.49 [−0.2–0.7] / 59.6 |
| best physics (by R²) | 0.932 / 29.3 (min/max slope+base) | 0.55 / 37.9 (cal. delta) | **0.896** [0.74–0.94] / 36.4 (slope+base) | 0.44 / 54.1 |
| peak-only (Linear [peak]) | 0.891 / n/a | −0.08 / 104.8 | 0.542 [0.35–0.70] / 65.2 | −0.77 / 78.3 |
| Linear [size+peak] | – | −1.36 / 118.8 | 0.839 / 58.4 | 0.48 / 64.3 |
| test HP hh / test substations | 28 / 1080 | 11 / 40 | 20 / 130 | 12 / 75 |

- **B\* ML vs anchor-only (ΔR², same anchor):** `size_peak`: XGBoost −0.018 [−0.15–0.10], ElasticNet +0.001, others ≤ 0; ML better in 25–50 % of seeds; ΔMAPE XGBoost −7.6 pp. `size`: +0.6 (baseline is size-only, R² 0.07). `none`: −0.08…−0.17.
- **Physics vs ML (B\*):** slope-only MAPE 34.9 %, HDH (fixed 12 °C) 35.3 %, calibrated delta 36.4 %; best ML MAPE 47.8 % (XGBoost `size_peak`). T_h at a bound in 2.3 % of test fits.
- **FFNN (reduced budget, 5 seeds):** R² 0.56 (none) / 0.61 (size_peak), MAPE 79 / 89 %. Worse than every anchor-only [size+peak] model.
- **Niche (B\*, MAPE by p):** XGBoost 78 % at p = 0.05, 51 % at 0.1, 18–22 % at p ≥ 0.3; slope+base 52 / 36 / 14–19 %. By size: XGBoost 60 % (10) → 23 % (120). Error falls with p and size for all three; physics is lower in every bin.

**Assumptions & deviations:**
- **Stash not dropped.** The four model files are restored byte-identical to the stash blobs (MD5s in `stash_restore_md5.txt`), but the auto-mode classifier blocked `git stash drop`, so `stash@{0}` still exists. Also, `stash@{0}^3` does not exist; the files are in the stash commit's own tree.
- **BLAS pinned to 1 thread** (`parallel.blas_threads`), XGBoost `n_jobs` = floor(28 / 4) = 7. With BLAS threads = floor(cores/workers), Ridge differed between 1 and 4 workers at 1e-14; pinned, `metrics.csv` is value-identical (test). Workers are always spawned processes.
- `metrics.csv` gets an extra column `cell` (`all` or `p<p>|n<size>`); `summary.csv` groups also by `arm` (= exp_id) so FFNN and main rows stay apart; `summary_band` sits under `uncertainty:`. Each arm's anchor-only/physics rows are identical across arms for shared seeds (checked, 6030/6030 exact).
- **Pool A:** the 57 iter-00 households (80 % coverage rule, no re-check), fill = the split's HP households' Other channel, never both roles in one substation. Best baseline in tables 2–3 is chosen by median (table 2) or per-seed (table 3) test R², which favours the baseline.
- FFNN arm: `max_evals_by_model {FFNN: 20}`, patience 10, anchors none + size_peak; its anchor-only rows use 50 evals.

**Problems found:**
- **Pool A cannot reproduce the legacy grid under v1.** A test substation is capped at the 14 test households: only size 10, p ≤ 0.3, 2 stations, 40 substations from ~11 households. Legacy → A-v1 mixes stacking/leakage with this grid change; the control "B\* on A's cells" (size 10, p ≤ 0.3) gives XGBoost 0.23 / 70 %, physics 0.44.
- **Seed spread is large** where test households are few: B (12 test HP households) R² 5 %–90 % = −0.16…0.66; B\* 0.66…0.90.
- **FFNN early-stops after 4–14 epochs** (patience 10, ~1 s/eval), so the reduced budget may under-train it.
- No failed fits, NaN predictions or zero targets in any arm; `HP_CoincPeak > HP_Peak` in 38 % of B\* substations (definitional, 03).

**Decisions for Alex:**
1. **Does the paper lead with anchor/identifiability instead of ML gain?** With `size_peak`, ML ≈ Linear on [size, peak] (ΔR² ≈ 0) and physics is at least as good on HP_Peak. Recommended: **lead with the anchor/identifiability result**; carry RQ2 only on targets where physics has structure (s_h, r, P_design in 03).
2. **Keep FFNN?** Recommended: **drop it from the main tables** (footnote it). Alternative: rerun full budget (50 evals, patience 40, 5 seeds, ~1 h).
3. **Plan for 03/04:** legacy 0.934 is not comparable (stacking, sizes up to 120). Recommended: **B\* with 20 seeds is the only headline pool**, report B and the restricted-cell control as sensitivity, and drop pool A from later iterations. Also decide the stash (`git stash drop 'stash@{0}'`).
