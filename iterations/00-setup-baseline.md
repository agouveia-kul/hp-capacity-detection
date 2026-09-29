# Iteration 00 — Setup and baseline reproduction

**Branch:** `iter/00-baseline` (from current `HEAD`)
**Type:** infrastructure only. **No methodological changes**: do not fix any known issue from CLAUDE.md §10, even if it is obvious.

## Goal
Make the current results reproducible from scripts in this repo, and record the exact facts of the legacy pipeline. That record is the reference point every later iteration is compared against.

## Tasks

### 1. Repository scaffolding
- Create `results/`, `configs/`, `tests/`, `iterations/`. This file already lives in `iterations/`.
- Add `results/**/models/` and large intermediate files to `.gitignore`. Commit `metrics.csv`, `config.yaml`, `REVIEW.md` and figures.
- Add `data/_paperb/` handling: scripts create it if missing. Never write elsewhere in `data/`.

### 2. Recover the missing scripts
The notebook refers to these scripts, which are not in `scripts/`:
`regenerate_substations_pooled.py`, `train_swiss_capacity.py`, `benchmark_capacity_models.py`, `feature_select_xgb.py`, `evaluate_xgb_hockey_ci.py`, `wpuq_penetration_sweep.py`, `hockey_variants_compare.py`, `hockey_delta_calibrated.py`, `penetration_calibrated_delta.py`, `swiss_penetration_sweep.py`.

Search in this order:
1. `git log --all --diff-filter=D --name-only` and `git log --all -- '*<name>'` in this repo;
2. the sibling repos `hp-sensitivity-paper` and `NILM` (local clones, or GitHub `agouveia-kul/*`);
3. the `data/` folder and the rest of the Desktop.

For each script:
- **Found:** copy it into `scripts/legacy/` **unchanged**. Adapt only import paths if strictly required, and list every such edit.
- **Not found:** reconstruct it in `scripts/legacy/` from the notebook markdown and code, as faithfully as possible. Put a header comment `# RECONSTRUCTED — not the original` on it.

Produce `scripts/legacy/SOURCES.md`: a table of script → found where / reconstructed → edits made.

### 3. Reproduce the legacy results
Re-run the legacy evaluation and write outputs to `results/iter00_baseline/`, never to `data/`.

- Prefer **evaluation-only** runs using the existing models in `models/` and the existing caches (`substations_data_pooled.pkl`, `_X_swiss_pooled.pkl`, etc.).
- Retrain only where no saved model exists. State the estimated runtime first; use the `quick` config first.

Legacy files to reproduce, compared against the copies in `data/`:

| Legacy file (`data/`) | Produced by |
|---|---|
| `capacity_model_benchmark.csv` | benchmark_capacity_models |
| `capacity_wpuq_real_feeder.csv` | benchmark_capacity_models |
| `xgb_feature_selection_cv.csv` | feature_select_xgb |
| `xgb_hockey_ci_metrics.csv` | evaluate_xgb_hockey_ci |
| `hockey_variants_transfer.csv` | hockey_variants_compare |
| `hockey_delta_calibrated.csv` | hockey_delta_calibrated |
| `wpuq_penetration_sweep.csv` | wpuq_penetration_sweep |
| `penetration_calibrated_delta.csv` | penetration_calibrated_delta |
| `swiss_penetration_sweep.csv` | swiss_penetration_sweep |

Write a `scripts/compare_to_legacy.py` that diffs each reproduced file against its legacy copy. It reports the max absolute and relative difference per metric column and flags anything above 1 % relative. Also emit the results in the long `metrics.csv` format (CLAUDE.md §8), tagged `protocol=legacy`.

If a result cannot be reproduced within 1 %, **do not tune it until it matches**. Report the gap and the most likely cause (seed, library version, cache version, reconstructed script).

### 4. Legacy facts table
Write `results/iter00_baseline/facts.md`, with each fact computed from the data or cache (not copied from notebook text):
- **HP households:** number of distinct HP households in each pool (HEAPO 2023, Swiss/Kaiser paired, combined, WPuQ), per weather station. Resolve the 81-vs-57 discrepancy.
- **Split sizes:** train/test HP households and fill households in the pooled design, plus the split seed(s) used.
- **Substation design:** number of substations per split; size and penetration grid; whether draws are with replacement. For a 120-dwelling, 100 %-penetration train substation, report the mean number of times each HP profile appears.
- **Target statistics:** HP_Peak distribution, and per-HP robust-peak median per dataset (HEAPO, Swiss, WPuQ).
- **Coverage:** years and date ranges used per dataset.
- **Protocol overlap:** how many HEAPO protocol households with `Normpoint_ElectricPower` are in the 2023 HP pool.

### 5. Environment record
Write `results/iter00_baseline/environment.txt` containing:
- the Python version;
- `pip freeze`, diffed against `requirements.txt`;
- the xgboost, scikit-learn, numpy and pandas versions;
- the git commit hash.

### 6. Tests (minimal)
Create `tests/test_legacy_facts.py`. It asserts the facts from task 4 that later iterations must not change silently: pool sizes, and the legacy split being reproducible from its seed. Run it with `pytest`.

## Out of scope
- Any fix to known issues (splits, replacement, CV, bootstrap, targets, T_base).
- New datasets, new targets, new models.
- Notebook edits.

## Acceptance criteria
- [ ] Every one of the 10 scripts is present in `scripts/legacy/` and documented in `SOURCES.md`.
- [ ] Every legacy file in task 3 was either reproduced within 1 % or has its gap explained.
- [ ] `facts.md` is complete and computed from data.
- [ ] `pytest` passes.
- [ ] Nothing in `data/` or `models/` was modified (`git status` of this repo is clean outside intended paths; check the modification times of the legacy files in `data/`).
- [ ] `results/iter00_baseline/REVIEW.md` is written using the CLAUDE.md §9 template. The decisions section should at least cover:
  - which reproduced numbers become the official legacy baseline;
  - whether reconstructed scripts are trusted.

Then stop and wait for review.
