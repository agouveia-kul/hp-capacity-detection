# Iteration 07 — Transfer validation: does identifiability-guided hybridisation hold on a pool it was not selected on?

**Branch:** `iter/07-transfer`, from `main` **after the 06 close-out is merged**. The close-out adds the 2026-11-13 decisions, the nMAE metric (2026-11-16) and `scripts/paperb/metrics.py: nmae`.
**Type:** Part A is code, ≤ ~300 logic lines; if it is bigger, stop after Task 2 plus tests and propose a split. After Part A, **stop for the pre-run check** (`PART_A.md`). Then come the queued runs, then the results.
**Supersedes:** `iterations/07-transfer-notes.md`. Its points are folded in below; mark that file superseded in your first commit.
**Target:** capacity only (`HP_Peak`, in its harmonised form `HL` below).
**Pre-registration (hard rule 12):** the design and rules T1–T3 below are fixed on 2026-11-16, before any 07 run. Your first commit records them in DECISIONS.md.

## Why this iteration
06 ended with the pre-registered hybrid claim failing. The learned transferable scale (L4) did not pay. What paid within a pool was identifiability-guided **inputs** (L2: physics-derived features, for linear and TabPFN) and **target** (L3: a residual on the Paper A estimate, for linear). That choice was made after seeing 06's results. Alex decided on 2026-11-13 that the paper's method becomes L2/L3, labelled post hoc, and that 07 tests it confirmatorily on data it was not chosen on: the other pool.

07 also:
- closes axis T of the 06 record;
- measures the label-definition shift between the pools.

## Decisions this brief depends on (quote, do not reinterpret)
- `2026-11-13 | 06 | Decision 1: the paper's method becomes identifiability-guided hybridisation through the inputs and the target (L2 physics-derived features; L3 residual on the Paper A estimate), labelled post hoc in the paper; the learned transferable scale (L4) is reported as a pre-registered negative result … No revised L4 now; a revision is allowed only as a new rung pre-registered after 07 and tested on unseen data.`
- `2026-11-13 | 07 | The confirmatory test of the post hoc method is fixed in the 07 brief before any 07 run: L2 and L3 (per family) against L1 and L0 on transfer data …`
- `2026-11-13 | 06 | Decision 2: L5 is dropped (rule 3) and the R(i) label-free update row is not a deployment mode …`
- `2026-11-13 | 07 | Decision 3: 07 carries every rung with L4a as the only L4 variant; L4b is not carried … The 07 runtime estimate includes a CNN epoch cap and a timeout that fires on time; the own-load term and label harmonisation follow iterations/07-transfer-notes.md.`
- `2026-11-16 | metric | …` (both lines). The primary metric is nMAE per evaluation set; WAPE is secondary. The "better" rule uses a relative 5 % threshold.
- CLAUDE.md §4: *Transfer sets are never used for any fitting, selection or calibration unless the experiment is explicitly a domain-adaptation experiment and says so.*
- `2026-10-12 | 06 | …` (ladder, axes, rules, B1, CNN inherited hyperparameters on GB).

## Design (fixed now)

### Directions and pairing
- Two directions: **CH→GB** (source B\*, target GB-EoH main year) and **GB→CH**.
- Seeds 0–9 are paired. The models of source seed s are evaluated on the **06 A-arm test aggregates of target seed s**: the same substations and the same fillers as in 06.
- The two pools share no household, so every target household is unseen by the source models.

### Models (frozen)
- **ML rungs L1–L3:** the persisted 06 rung winners per pool, seed and family (A10 format, reload-checked in 06). No refit and no recalibration on the target.
- **L4:**
  - L4a only (Decision 3).
  - Where the persisted L4 winner is L4b (GB 11 and CH 20 of 30 family × seed), refit **L4a's inner-CV-best configuration** on the same source train set. Use the logged hyperparameters, no new search.
  - CNN refits train for the logged epoch count (no early-stopping search) and keep B1's three initialisations.
- **L5:** not carried (dropped in 06).
- **L0 physics:**
  - All rows are refit on the source train set per seed. This is deterministic and cheap, as in 06.
  - `slope_base` is refit too: its map was not persisted in 06.
- **Source quantities in pure transfer:**
  - the pilot m_h and κ;
  - s₀ (the fill slope);
  - the `slope_base` map;
  - the cross-fitted pilots inside the L3 base and L4.

  All come from the **source** train set.
- **Target T_design (L4a):** site metadata, label-free. Use the value 06 used for each pool, with its source checked (hard rule 11). The GB value (−3 °C, CIBSE London) is UNVERIFIED and London-only, with a site spread of −1.5 to −5.9 °C.

### Secondary rows (outside the rules; explicitly domain adaptation, label-free; labelled so in every table)
- **L0 target-s₀:** physics with s₀ from the **target** pool's train fillers. This is non-HP data only, no HP label.
- **`paperA_corr_own`:**
  - CH→GB: computed with the CH pilot.
  - GB→CH: not computable, because GB has no whole-house meters. Listed as n/a with that reason.
- **Expected own-load effect, GB→CH:** CH aggregates contain each HP home's own non-HP load. Its slope is ≈ 0.018 kW/K, 3.3 × a filler's (05a D5). GB models never saw such a load, so expect a bias upward. Report the bias by bin.

### Inputs on the target (the source's feature pipeline applied to target aggregates)
- **GB→CH:** CH target aggregates **and labels are rebuilt at 30 min** (mean of the two 15-min values), matching the GB models' training resolution.
- **CH→GB:** GB exists at 30 min only.
  - Daily-mean inputs (`netfit`, `rawphys` scalars, the CNN's daily series) do not depend on resolution.
  - Peak-based inputs (the `size_peak` anchor, any peak column) see 30-min peaks where the CH models were trained on 15-min ones.
  - Measure the shift on CH train aggregates: the median ratio of 30-min to 15-min net-aggregate peak. Report it; **do not correct it**. Flag every `size_peak`-anchored winner.
- **Calendar:** CH is calendar 2023; GB runs Nov 2021 – Oct 2022.
  - Part A checks whether the CNN input, the `whdd` windows or any other feature depends on calendar position or series length.
  - If one does, align by day of year. Write the rule into `PART_A.md` before any transfer prediction is scored.
  - Holiday flags (`netfit`) are the **target** region's.

### Labels: the harmonised label `HL` (from the 05a D5 diagnosis)
- **Definition:** `HP_Peak` at 30-min resolution, **HP unit only** (compressor + backup heater + pumps), DHW immersion excluded. This is the per-household 99.9th percentile, summed over the HP members.
- **CH:** the 15-min HP submeter averaged to 30 min. CH electric water heaters sit in the own non-HP load, not in the submeter, so CH needs no further change.
- **GB:** whole heating-system electricity **minus the immersion channel**, at 30 min.
- **If the EoH immersion channel is missing or unusable, stop and report.** Do not substitute another definition.

### Label mapping (pre-registered)
- Each source model predicts its own **native** label (CH: 15-min submeter; GB: 30-min whole system incl. immersion).
- **Headline prediction:** c_src · ŷ, where c_src = median over the **source train** substations of the seed of HL / native label. Source labels only, per seed.
- **Sensitivity rows:** ŷ uncorrected vs HL; ŷ vs the target's native label.
- **Report** c and its 5–90 % spread per pool and per bin. This is the size of the definitional shift (07 notes).

### In-pool reference and transfer gap
- **In-pool reference:** the target pool's own 06 test predictions (persisted `predictions.csv`) × c_tgt (from target **train** labels, in-pool), scored against HL.
- **Transfer gap:** nMAE(transfer) − nMAE(in-pool) on the same target set, per rung, family and seed.

### Metric
- **nMAE** = mean|ŷ − y| / max(y) × 100 % per evaluation set: one seed × direction cell. Per Paper A bin, it uses the bin's own substations and maximum. Report the normaliser max(y) (kW) beside each cell.
- **WAPE** is secondary.
- Paper A bins are always reported. GB targets mark the † bins and quote the 05a D5 deltas.
- Report the number of distinct HP households in source train and target test.

## Pre-registered rules
**"Better":**
- the paired per-seed Δ nMAE is < 0 in ≥ 8 of 10 seeds; **and**
- the median per-seed relative difference (nMAE_A − nMAE_B) / nMAE_B is ≤ −5 %.

"Worse" is the mirror. Anything else is "no difference". The overall reading (the whole target set) decides; per-bin results are reported.

**Comparators.** Fixed from 06 logs only, before any transfer prediction. Task 0 writes their identities into DECISIONS.md.
- **H\*** (the 06 method): the {rung, family} in {L2, L3} × {linear, TabPFN, CNN} with the lowest median inner-CV WAPE over seeds **on the source pool**.
- **D\*** (pure data-driven): the same, over L1 × families.
- **L0ref:** the source pool's 06 L0 reference (`slope_base` on both pools), refit per seed.

**T1 — confirmatory: the method vs pure data-driven.** Compare H\* with D\* per direction.
- **Confirmed:** better in both directions.
- **Partly confirmed:** better in one direction, no difference in the other.
- **Not confirmed:** no difference in both.
- **Refuted:** worse in either direction.

**T2 — the method vs physics.** Compare H\* with L0ref per direction; report better / no difference / worse. "Beats physics under transfer" if better in both directions.

**T3 — closes the 06 record on axis T.**
- Per family and direction: L2 vs L1, L3 vs L2, L4a vs L3.
- The 06 hybrid (L4a, best family by source inner-CV WAPE) vs D\*.
- 06 rule 2 stays failed on (a), whatever T shows.

**Multiplicity:**
- primary: T1 and T2 × 2 directions = 4 comparisons;
- T3: 3 steps × 3 families × 2 directions, plus 2.

Selection never uses transfer data. No 07 result changes the 06 record. A revised method is a new rung, pre-registered after 07 and tested on unseen data (Decision 1).

**Honesty note (state it in the REVIEW):**
- H\* and D\* were selected in-pool, and their in-pool test results are known.
- The transfer targets were never used by any selection.
- c uses source labels only.
- T_design is metadata.

## Part A — Code
### Task 0 — Bookkeeping (first commit)
- Add this brief as `iterations/07-transfer-validation.md`. Mark `07-transfer-notes.md` superseded.
- Append to DECISIONS.md:
  - the design and rules T1–T3 (one line each, as in 06's pre-registration lines);
  - the identities of H\*, D\* and L0ref per source pool, with their median inner-CV WAPE.
- Update CLAUDE.md:
  - §5: add `HL` to the target table;
  - §4: one paragraph on the 07 transfer protocol (frozen models, source quantities, c mapping, secondary rows).
- `method_basis.md` (hard rule 11): retrieve and check references for transfer evaluation under dataset shift, for label harmonisation across measurement definitions, and for max-normalised MAE. Mark anything not retrieved UNVERIFIED.

### Task 1 — Label audit (labels only; no model, no prediction)
- Build HL for both pools.
- Compute c per seed (median, 5–90 %) overall and per bin.
- Compute the CH 30/15-min net-peak ratio.
- Compute the GB immersion share of `HP_Peak` by bin.
- Write `results/iter07_transfer/label_harmonisation.md`. Stop if the immersion channel fails.

### Task 2 — Transfer evaluator (`scripts/paperb/transfer.py`)
- Load the persisted source models.
- Build target features with the source pipeline (resolution, calendar, holidays as above).
- Predict, apply c, refit the physics rows on source, add the secondary rows. Write `predictions.csv` in the 06 format, plus `direction` and `label_def` columns.
- Tests:
  - **(a) No target label reaches any fit:** permuting the target labels leaves every prediction bit-identical.
  - **(b) c comes from source train rows only.**
  - **(c) Round trip:** applying a pool's models to its own 06 test set through `transfer.py`, with c = 1 and native labels, reproduces the 06 predictions (|ΔWAPE| ≤ 0.001 pp).
  - **(d) Resolution:** the 30-min rebuild of CH aggregates leaves daily-mean features unchanged.
  - **(e) Pairing:** seed pairing is s→s.

### Task 3 — L4a refits and job limits
- Refit L4a for the family × seed cells whose persisted L4 winner is L4b (logged configuration, hyperparameters and epoch count).
- Add a **hard per-job timeout:** a watchdog that ends the process within 5 min of the limit. In 06 the async timeout fired up to 2.5 h late. Test it.
- Every CNN fit in 07 has a fixed epoch cap (the logged count).

### Task 4 — Queue, quick, probe
- `configs/iter07*.yaml`. Quick run interactively (< ~5 min). Probe seed 0 in both directions.
- **The probe logs runtime and validity counts only** (NaN, invalid ŝ, failed loads). Do not compute or open any transfer error metric before the report script is committed.
- Estimate the wall time (workers × threads ≤ physical cores) and print the scheduling command (`scripts/schedule_overnight.ps1`; Alex runs it). Ask first if > 1 night.
- Write `PART_A.md`: assumptions, every rule written during Part A, the estimate. **Stop for the pre-run check.**

## Part B — Runs and outputs (`results/iter07_transfer/`)
**Before reading any result,** commit the report script (`iter07_report.py`). Its docstring fixes any open choice.

1. **Transfer table:**
   - rows: L0 (all physics rows) and L1–L4a × family, plus the secondary rows;
   - columns: direction × {nMAE, transfer gap}, median [5–90 %], per Paper A bin (†);
   - HP households (source train / target test) and the normaliser.
2. **T1/T2 table:** comparators, per-seed counts, median relative differences, outcomes.
3. **T3 step table**, as 06's step table.
4. **Label table:** c per pool and bin; the resolution ratio; the immersion share; the uncorrected and native-label sensitivity rows.
5. **Figures:**
   - nMAE vs rung per direction, with the in-pool level marked;
   - the transfer gap by rung and bin;
   - c distributions.

## Out of scope
- **Retraining on harmonised pools:** a possible 07b, decided after this REVIEW.
- Target-side recalibration of ML models; domain adaptation beyond the L0 target-s₀ row.
- The RHPP nameplate arm and the FeederBW real feeders (a possible 07b); the concurrent-filler validation.
- Transfer to the replication year. New rungs or a revised L4. L5. Change detection (08). Paper text.

## Acceptance criteria
- [ ] Task 0 committed first (brief, DECISIONS incl. H\*/D\*/L0ref, CLAUDE.md §4/§5, references checked or UNVERIFIED).
- [ ] Task 1 label audit done. Tasks 2–4 done with tests; `pytest` passes; round trip (c) passes.
- [ ] Quick run, probe and estimate in `PART_A.md`. Stopped for the pre-run check.
- [ ] After go:
  - all jobs done or failures listed;
  - report script committed before reading;
  - REVIEW.md (§9) with tables 1–4.
- [ ] `data/` (outside `_paperb/`) and `models/` untouched. 06 persisted models read only. Push only to your branch; never merge.
- [ ] REVIEW decisions cover:
  1. the T1 outcome and what the paper's method section can then claim;
  2. whether 07b (harmonised retraining, or FeederBW real feeders) is needed for the validation section;
  3. what 08 (change detection) should use as its estimator.
