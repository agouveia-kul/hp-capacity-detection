# Prompt for the 07b-i agent

You are the experiment agent for iteration 07b-i (a read-only audit of unseen targets) of Paper B in `agouveia-kul/hp-capacity-detection` (owner and reviewer: Alex).

## Read first
- `CLAUDE.md`.
- `DECISIONS.md`: the latest lines override older text. Read the 2026-11-18 lines closely.
- The attached brief `07b-i-unseen-target-audit.md`.
- `results/iter07_transfer/REVIEW.md`, including its post-review section.
- `results/iter04_inventory/`: the earlier data inventory.

## Setup
- Check that `main` contains the 07 close-out: the DECISIONS lines dated 2026-11-18. If it does not, stop.
- Create `iter/07b-i-target-audit` from `main`. Your first commit adds the brief as `iterations/07b-i-unseen-target-audit.md`.

## Hard constraints
- **Blindness:** compute no estimator, prediction or error metric on any candidate dataset (see the brief). If a step would need one, stop and ask.
- **Data safety:** never modify `data/` outside `data/_paperb/` and never overwrite `models/`. Never print, log or commit tokens.
- **Downloads:** list anything that needs downloading; Alex does it.
- **References:** checked or UNVERIFIED (hard rule 11); never invent a citation or DOI.
- **Git:** commit and push only `iter/07b-i-target-audit`; never merge.
- When finished, write `REVIEW.md` (§9) and stop.

---

# Prompt for the 08 agent

You are the experiment agent for iteration 08 (change-detection use case) of Paper B in `agouveia-kul/hp-capacity-detection` (owner and reviewer: Alex).

## Read first
- `CLAUDE.md`.
- `DECISIONS.md`, with the 2026-11-16 and 2026-11-18 lines closely.
- The attached brief `08-change-detection.md`.
- `results/iter06_hybrid_ladder/PART_A.md` and `results/iter06_hybrid_ladder/REVIEW.md` (the persisted models, pilots, the replication-year machinery of R(ii)).
- `results/iter07_transfer/REVIEW.md`.

## Setup
- Check that `main` contains the 07 close-out (DECISIONS lines dated 2026-11-18). If it does not, stop.
- Check that no other agent is working in this checkout (07b-i). If one is, stop and say so.
- Create `iter/08-change-detection` from `main`.

## What to do now
Part A only (Tasks 0–3). Then write `results/iter08_change_detection/PART_A.md` and stop for the pre-run check. Do not start the full run.

## Hard constraints
- **Pre-registration (hard rule 12):** the design and rules D and Q are fixed. Your first commit records them, with the estimator identities, in DECISIONS.md. If something cannot be done as written, stop and ask; do not reinterpret.
- **Do not compute or open any detection or error metric** before the report script is committed. The quick run and the probe log runtime and validity counts only.
- The 06 persisted models are read-only. No training.
- **Data safety:** never modify `data/` outside `data/_paperb/`; never overwrite `models/`; never print or commit tokens. TabPFN-3.5 loads locally from `C:\tabpfn_cache`.
- **Long runs:** use `scripts/paperb/run_queue.py`. Print the `scripts/schedule_overnight.ps1` command; Alex runs it or asks you to launch it detached. Never register scheduled tasks.
- **OneDrive:** remind Alex in `PART_A.md` to pause OneDrive during runs. Never delete and recreate result folders under OneDrive.
- **References:** checked or UNVERIFIED; never invent a citation.
- **Git:** commit and push only `iter/08-change-detection`; never merge.
