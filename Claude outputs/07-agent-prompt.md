You are the experiment agent for iteration 07 (transfer validation) of Paper B in `agouveia-kul/hp-capacity-detection` (owner and reviewer: Alex).

## Read first
- `CLAUDE.md` (the contract)
- `DECISIONS.md`: the latest lines override older text. Read 2026-11-13 and 2026-11-16 closely.
- The attached brief `07-transfer-validation.md`
- `results/iter06_hybrid_ladder/REVIEW.md`, including its post-review section
- `results/iter06_hybrid_ladder/PART_A.md`, for how the 06 models, pilots, L4 scales and the queue were built

## Setup
- Check that `main` contains the 06 close-out (`git log origin/main`: DECISIONS lines dated 2026-11-16 and `nmae` in `scripts/paperb/metrics.py`). If it does not, stop and say so.
- Then create `iter/07-transfer` from `main`.

## What to do now
**Part A only** (Tasks 0–4 of the brief). Then write `results/iter07_transfer/PART_A.md` and stop for the pre-run check. Do not start the full run.

## Hard constraints
- Pre-registration (hard rule 12): the rules T1–T3 and the design in the brief are fixed. Your first commit records them, with the identities of H\*, D\* and L0ref, in DECISIONS.md. If something in the brief cannot be done as written, stop and ask; do not reinterpret.
- **Do not compute or open any transfer error metric** (nMAE, WAPE, MAE on target labels) before the report script is committed. The quick run and the probe log runtime and validity counts only.
- The 06 persisted models under `results/iter06_hybrid_ladder/models/` are read-only inputs.
- Transfer targets are never used for fitting, selection or calibration. The only exceptions are the secondary rows the brief names (label-free, labelled as domain adaptation).
- **Data safety:**
  - never modify `data/` outside `data/_paperb/`;
  - never overwrite `models/`;
  - never print, log or commit tokens (`TABPFN_TOKEN`, `HF_TOKEN`). TabPFN-3.5 loads locally from `C:\tabpfn_cache` via `model_path`.
- **Scheduling:** long runs go through `scripts/paperb/run_queue.py`. Print the `scripts/schedule_overnight.ps1` command; Alex runs it. Never register scheduled tasks yourself. Ask first if the estimate exceeds 1 night.
- **OneDrive:**
  - Alex pauses OneDrive sync during runs; remind him in `PART_A.md`.
  - Never delete and recreate result folders under OneDrive.
- **References:** check them or mark them UNVERIFIED (hard rule 11). Never invent a citation or DOI.
- **Git:** commit to `iter/07-transfer` and push that branch only. Never merge.
- **CLAUDE.md:** edit only the parts Task 0 names. Show the diff in `PART_A.md`.
