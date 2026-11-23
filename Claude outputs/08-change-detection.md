# Iteration 08 — Use case: can a change in HP capacity on an LV feeder be detected and quantified between two heating years?

**Branch:** `iter/08-change-detection`, from `main` after 07 is merged. If 07b-i has not finished on its own branch, run this after it, so that the checkout is not shared.
**Type:**
- **Part A:** code, ≤ ~300 logic lines. Then **stop for the pre-run check** (`PART_A.md`).
- **Part B:** runs, then results.

No model is trained: inference with frozen 06 models plus physics. Expect less than one night.
**Pre-registration (hard rule 12):** the design and rules D and Q below are fixed on 2026-11-18, before any 08 run. Your first commit records them in DECISIONS.md.

## Why
The paper's use case (storyline step 6): a DSO wants to know whether HP capacity on a feeder has grown, and by how much, from aggregated net load and temperature alone.
- 07 showed that absolute estimates carry pool-specific biases, mostly through s₀.
- A change estimated as a difference between years, on the same feeder with the same estimator, cancels any bias that is stable across those years.

08 tests detection and quantification within GB-EoH. There are two heating years with mostly the same homes: main Nov 2021 – Oct 2022 and replication Oct 2022 – 28 Sep 2023 (272 shared homes).

## Decisions this depends on (quote)
- `2026-11-18 | 08 | Decision 3: …` (two estimators, no single primary, differences between years).
- `2026-11-18 | plan | Decision 1: …` (the reframing).
- `2026-11-16 | metric | …` (nMAE primary; the "better" rule). **From 07's review:** WAPE is always shown beside nMAE.
- `2026-10-12 | 05b | …` (Arm 6: the ML gain replicates across years).
- CLAUDE.md §4 (household-disjoint, no stacking, seeds 0–9, Paper A bins).

## Design (fixed now)
### Households and halves
- For each seed s (0–9), take the **06 A-GB test HP households of seed s** that have valid data in both years (≥ 90 % 30-min coverage in each window). Report the count.
- Split them, and the seed's test fillers, into two household-disjoint **halves** (seeded, stratified by weather group).
- Thresholds are calibrated on one half and evaluated on the other, then the halves swap (two-fold cross-calibration). An evaluation half never contributes to its own threshold.

### Paired feeders
- **Year 1:** N dwellings, k₁ = round(p₁ N) HP homes. Each HP dwelling has its LCL filler as non-HP load (as in 05a/06).
- **Year 2:** the same dwellings, with the same HP homes and the same LCL filler households. The fillers are analog-matched to year-2 days with the 05b Arm 6 / 06 R(ii) machinery.
- **Uptake:** Δk = round(Δp N) of the year-1 non-HP dwellings become HP dwellings. Each keeps its LCL filler and gains the HP electricity of a new HP home drawn from the same half, not already in the feeder. N stays constant.
- **Grid:**
  - N ∈ {20, 40, 80};
  - p₁ ∈ {0.05, 0.1, 0.2, 0.3, 0.5};
  - Δp ∈ {0 (null), 0.05, 0.1, 0.2};
  - Δk ≥ 1 is required.

  The feeders per cell follow the 06 generator rules (no stacking). Infeasible cells go to `dropped_cells.csv`, with the envelope reported.
- **Labels (GB native `HP_Peak`, per year):**
  - C₁ and C₂;
  - **ΔC_added** = Σ of the new homes' year-2 `HP_Peak` (the change of interest);
  - ΔC_total = C₂ − C₁ (it includes the existing homes' natural change, reported).

### Estimators
Each estimator is applied to both years of each feeder, with the same model.

| id | estimator | role |
|---|---|---|
| E1 | TabPFN L2: the persisted 06 A-GB rung winner of seed s, frozen (trained on main-year train households only) | pre-registered |
| E2 | `paperA_corr` with **local s₀ per year** (from the seed's train fillers matched to that year; label-free) and the year-1 train pilot m_h | pre-registered |
| E3 | `paperA_sh_mh` (no s₀ correction: differencing may cancel s₀ by itself) | reference |
| E4 | L1 TabPFN, frozen 06 winner (the best-transferring ML row in 07) | reference |

The 07b estimator is added later only if 07b confirms it.

### Statistics
- **Change estimate:** Δ̂ = P̂₂ − P̂₁ (kW).
- **Detection is one-sided:** flag if Δ̂ > τ. τ is the 95th percentile of Δ̂ on the **null feeders of the calibration half**, per seed, estimator and N.
- **Reported:** the realised false-alarm rate on the evaluation half; power at each Δp; MDC = the smallest Δp with power ≥ 0.8 (pooled, and per N and p₁).
- **Quantification error** on Δp > 0 feeders: |Δ̂ − ΔC_added|.
  - nMAE, normalised by the set's max ΔC_added;
  - WAPE;
  - signed bias.

  Report it per Paper A bin of p₁ (†).

## Pre-registered rules
- **D (detection), E1 vs E2.** Measure power at Δp = 0.1, pooled with equal weight per feasible (N, p₁) cell.
  - **Better:** higher power in ≥ 8/10 seeds and median difference ≥ 5 pp. "Worse" is the mirror; otherwise no difference.
  - An estimator whose realised false-alarm rate exceeds 10 % (pooled) is flagged **miscalibrated**. Its power is reported but not compared.
- **Q (quantification), E1 vs E2.** Compare the error of Δ̂ against ΔC_added, pooled over Δp > 0, with the 07 "better" rule: ≥ 8/10 seeds and median relative difference ≤ −5 % on nMAE. The same verdict holds in WAPE.
- **Feasibility statement (reported, not a comparison).** For each estimator, report the MDC and whether quantification nMAE is below the in-pool absolute-estimate nMAE of the same estimator (06). This answers whether differencing helps.
- **Multiplicity:** two primary comparisons. Everything else is reported.

**Honesty note:**
- E1/E4 were selected and trained in 06 on main-year train households; year 2 and the test households are unseen by them.
- Thresholds use only the other half.
- 2022/23 was the energy-crisis winter, so behavioural change in the existing homes is part of the null, and is reported, not removed.

## Part A — Code
### Task 0 — Bookkeeping (first commit)
- Add this brief as `iterations/08-change-detection.md`.
- DECISIONS.md: the design, rules D and Q, and the estimator identities (one line each).
- CLAUDE.md §4: one paragraph on the 08 protocol.
- `method_basis.md`: references for change detection by threshold on a null distribution, and for MDC/power at a fixed false-alarm rate. Checked, or UNVERIFIED.

### Task 1 — Paired-feeder generator (`scripts/paperb/change_feeders.py`)
Year-1/year-2 memberships, uptake, labels and halves.

Tests:
- no household in both halves;
- year-2 members ⊇ year-1 members;
- new HP homes never already in the feeder;
- N constant;
- ΔC_added equals the sum of the new homes' year-2 peaks;
- no stacking.

### Task 2 — Evaluator (`scripts/paperb/change_eval.py`)
- Apply E1–E4 to both years: load the frozen models, build features with the 06 pipeline, compute local s₀ per year.
- Thresholds on the calibration half; swap halves.
- Tests:
  - a threshold never uses evaluation-half feeders;
  - E1 on year-1 feeders made of 06 test substations reproduces the 06 predictions (|ΔWAPE| ≤ 0.001 pp);
  - permuting labels leaves Δ̂ bit-identical.

### Task 3 — Queue, quick, probe, estimate
- `configs/iter08*.yaml`. Quick run (< ~5 min). Probe seed 0.
- **Runtime and validity counts only:** no detection or error metric is computed or opened before the report script is committed.
- Print the scheduling command; Alex runs it.
- Write `PART_A.md` (the envelope, every rule written in Part A). **Stop.**

## Part B — Outputs (`results/iter08_change_detection/`)
Commit the report script **before reading any result**.
1. **Detection table:** realised false-alarm rate, power by Δp, and MDC per estimator, pooled and per (N, p₁ bin).
2. **Quantification table:** nMAE and WAPE of Δ̂, bias, and the in-pool absolute-estimate nMAE for comparison.
3. **Rules table** (D, Q).
4. **Null-drift table:** Δ̂ on null feeders vs ΔC_total, by bin.
5. **Figures:**
   - power curves (power vs Δp) per estimator;
   - the Δ̂ vs ΔC_added scatter;
   - null Δ̂ distributions.

## Out of scope
- A CH arm (Kaiser cal2024); registry-anchored absolute change.
- Sequential detection and detection delay: one change per two annual windows, so delay is not defined here.
- More than two years; retraining; new estimators beyond E1–E4; paper text.

## Acceptance
- [ ] Task 0 first; Tasks 1–3 with tests; `pytest` passes; quick, probe and estimate in `PART_A.md`; stopped for the pre-run check.
- [ ] After go: all jobs done or failures listed; report script committed before reading; REVIEW.md (§9). Its decisions cover:
  1. what the use-case section can claim (MDC, quantification);
  2. whether a CH arm (cal2024) is worth adding;
  3. whether the 07b estimator, if confirmed, is added to 08.
- [ ] `data/` untouched (outside `_paperb/`), `models/` untouched, 06 models read-only. Push to the branch only; never merge. Never print or commit tokens.
