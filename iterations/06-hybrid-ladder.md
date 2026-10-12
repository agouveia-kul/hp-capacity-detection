# Iteration 06 — The hybrid ladder: does learning only the non-identified part pay off?

**Branch:** `iter/06-hybrid-ladder`, from `main` **after 05b is reviewed and merged** (05b's frozen configurations, Stage 2 machinery and A12 must be on `main`).
**Type:** code (Part A, ≤ ~400 logic lines; if bigger, stop after Task 3 plus tests, write REVIEW "06-i", and wait), then queued runs, then results.
**Supersedes** `iterations/06-other-targets.md` (draft of 2026-10-09, never started). **Target: capacity only** (`HP_Peak` = $P_{\mathrm{TCL}}^{\max}$).
**Pre-registration (hard rule 12):** the ladder, the axes and the claim rule below are fixed on 2026-10-09, before any 06 run. Your first commit records them in DECISIONS.md.

## Why this iteration
The paper's storyline changed on 2026-10-09 (Alex). The flow is now:
1. the LV network and its DER are unobservable;
2. the physics estimator (Paper A) has limits;
3. data-driven estimation (several feature types and models) has other limits;
4. a **hybrid, identifiability-guided estimator** is the methodological contribution;
5. transfer validates it;
6. detecting a change in capacity is the use case.

06 builds and tests the hybrid as a **ladder**. The same model families are used at every rung, so each rung isolates one ingredient.

## Decisions this brief depends on (quote, do not reinterpret)
- **Storyline, method, plan (Alex, 2026-10-09):**
  - the contribution is the hybrid estimator, with three parts:
    - (i) the identified part: the corrected slope ŝ = max(s_h(net) − N·s₀, 0), with the own-load term of `paperA_corr_own` where it applies;
    - (ii) a transferable scale m̂_h: pilot, or learned (**L4 included**);
    - (iii) an ML residual for what physics misses;
  - the target is capacity only, for now;
  - the ensemble rung L5 is tested, and **dropped from the method if it fails** its rule;
  - the plan: 06 hybrid ladder → 07 transfer validation → 08 change-detection use case → 09+ freeze and draft;
  - other targets and the daily arm are dropped for now.
- `2026-10-05 | 05b | Amendment A10 …`: carried families linear, TabPFN, CNN; frozen per-seed configurations; physics rows always.
- `2026-10-06 | 05b | Amendment A11 …`: TabPFN and CNN on machine A's CPU.
- `2026-10-01 | 05a-ii | D4 verdict …`: mark the filler-variability-limited bins (†).
- `2026-10-09 | 05b | A12 …`: its outcome sets how the data-driven results are framed (section "Data-driven estimation"). 06 does not depend on it.

## The ladder (fixed now)
**Families:** the carried families (linear, TabPFN, CNN), where a rung applies to them. At each rung, each family's configuration is chosen by inner-CV WAPE among that rung's configurations only, never by test.

| Rung | Name | What it adds | Configurations |
|---|---|---|---|
| **L0** | Physics | Paper A estimators | `paperA_corr`, `paperA_corr_own`, `paperA_cal`, `slope_base` (all rows; the best by median WAPE is the L0 reference) |
| **L1** | Pure data-driven | generic features, direct target | tabular: `whdd` + scale features (N, observed peak), direct-log. CNN: raw series + scale scalar, direct-log. **No hockey-stick fit, no Paper A quantity** in the inputs |
| **L2** | + physics-derived features | netfit features | tabular: {netfit, both} × {size, size_peak}, direct-log. CNN: raw series + (ŝ, P_base, T_h, N) joined after pooling (new), direct-log |
| **L3** | + physics-informed target | residual on the physics estimate | L2 inputs, residual mode, z = log y − log P̂_A (as in 05b) |
| **L4** | + learned transferable scale (**the proposed hybrid**) | P̂ = ŝ / m̂_h · exp(f_θ(x)) | **L4a:** design-temperature normalisation m̂_h = κ / (T̂_h − T_design), with κ from the pilot (one parameter). **L4b:** m̂_h = g(covariates), a small regularised regression of log m_h on aggregate covariates (T̂_h, T_design, r̂, climate statistics of T), fitted on train aggregates (label m_h = s_h(HP aggregate) / HP_Peak). The residual f_θ (L2 inputs) is fitted on top. **m̂_h is cross-fitted** on the inner folds, so the residual's training targets are out-of-sample (as 03b Task 3). The L4 reported row is the inner-CV winner of {L4a, L4b} per family |
| **L5** | Ensemble of hybrid experts | combination | **L5a:** plain average of the families' L4 predictions (no learned weights). **L5b:** gate on r̂ = ŝ / P_base(net) (identifiable, label-free), with bin edges and per-bin weights learned on **out-of-fold** inner-CV predictions |

## The four axes (fixed now)
- **A, accuracy:** GB main, n = all, 10 seeds (0–9): WAPE overall and per Paper A bin (†). CH (B\*), n = all, 10 seeds.
- **S, sample efficiency:** GB learning curve at n ∈ {32, 62, 100, all}, 10 seeds × 2 draws (same designs as 05b Arm 1). Primary point: n = 62 (the CH regime). Also report n\* (the n at which a rung reaches L0).
- **R, robustness:** (i) the frozen n = all models applied to test aggregates with fillers ×0.5 and ×1.5 (05b Arm 7 machinery), as the degradation ΔWAPE vs ×1.0; (ii) the same rung on the temporal replication year (05b Arm 6 machinery), refit there.
- **T, transfer:** evaluated in 07 (CH ↔ GB, harmonised labels). 06 saves every rung's models per seed for it (the A10 persistence format).

## Pre-registered rules
"Better" on an axis means paired per-seed ΔWAPE < 0 in ≥ 8 of 10 seeds (≥ 80 % of seed × draws on S) **and** median ΔWAPE ≤ −1 pp. For R, compare the degradation instead of the level.

1. **Ladder steps.** For each family and dataset, compare each rung with the one below (L2 vs L1, L3 vs L2, L4 vs L3) on axes A, S and R. Report each step as better / worse / no difference.
2. **The hybrid claim.**
   - *The hybrid* = L4 with its best family. *Best pure data-driven* = the best of L1/L2 over the families. Both are chosen by inner-CV WAPE.
   - The claim **holds** if:
     - (a) on A, the hybrid's median WAPE is at most 1 pp above the best pure data-driven model (GB, overall); **and**
     - (b) the hybrid is better on at least **two** of S, R, T.
   - 06 reports (a), S and R. The claim is closed in 07, when T is in. If (a) holds and the hybrid is already better on S and R, the claim holds regardless of T.
   - Also report the hybrid vs L0 on every axis.
3. **L5.** An ensemble form is **kept** only if it beats the hybrid (L4) by median ≤ −1 pp and in ≥ 8/10 seeds, overall or in the † bins, on GB. Otherwise L5 is reported as a negative result and is **not** part of the method.

Multiplicity: 5 rungs × 3 families × 2 datasets × 3 axes; state it. Selection is always by inner CV.

**Honesty note:** L2 and L3 configurations on GB at n = all exist among the logged 05b Stage 1 candidates, and their aggregate ablation may already have been seen. Reuse those logs (no rerun needed), but say so in the REVIEW. Every other cell of the ladder is new.

## Part A — Code
### Task 0 — Bookkeeping (first commit)
- Append to DECISIONS.md:
  - the storyline/method/plan decision, with these two lines verbatim:
    - `2026-10-09 | plan | Storyline: unobservable LV/DER -> physics (Paper A) limits -> data-driven (feature types x models) limits -> hybrid identifiability-guided estimator (identified slope, transferable scale m_h incl. learned scale, ML residual) as the methodological contribution -> transfer validation -> change-detection use case. Capacity only; other targets and the daily arm dropped for now. Plan: 06 hybrid ladder, 07 transfer validation, 08 change-detection use case, 09+ freeze and draft. | Alex, 2026-10-09: a methodology contribution, not a benchmark.`
    - `2026-10-09 | 06 | Ensemble rung L5 (average; r-hat gate with out-of-fold weights) is tested and dropped from the method if it fails its pre-registered rule. | Alex, 2026-10-09.`
  - the ladder, the axes and rules 1–3 of this brief.
- Update CLAUDE.md:
  - §1: purpose, storyline, iteration plan; RQs reframed as the ladder questions;
  - §4: the four axes and the claim rule.
- Retrieve and check the references for `method_basis.md` (hard rule 11). Starting points, to verify, not to cite blindly:
  - physics-informed / hybrid modelling surveys (e.g. Willard et al., *ACM Computing Surveys*; Karniadakis et al., *Nature Reviews Physics*);
  - residual (hybrid) modelling in process and energy systems;
  - stacking (Wolpert);
  - mixtures of experts (Jacobs et al.);
  - design-temperature normalisation of heat-pump sizing (MCS / EN 12831).

  Mark anything not retrieved UNVERIFIED.

### Task 1 — L1 and L2 for the CNN, L1 on GB
- `whdd` features on GB (code exists; check the 30-min resolution settings).
- CNN option `physics_scalars: true`, joining (ŝ, P_base, T_h, N) after pooling.
- Tests: L1 inputs contain no netfit or Paper A column (sentinel).

### Task 2 — L4 scale models (`scripts/paperb/scale_model.py`)
- **L4a** (κ from the pilot) and **L4b** (regularised regression of log m_h on covariates).
- Cross-fitting on inner folds. Residual composition P̂ = ŝ / m̂_h · exp(ẑ). Invalid ŝ → 0, counted.
- Tests:
  - on a toy pool where m_h depends linearly on T_design, L4b recovers it;
  - cross-fitted m̂_h never uses its own fold;
  - ẑ = 0 reproduces ŝ / m̂_h exactly.

### Task 3 — L5 ensembles (`scripts/paperb/ensemble.py`)
- Out-of-fold inner-CV predictions for each family's L4 winner.
- L5a: the plain average.
- L5b: an r̂ gate (bin edges among {0.05, 0.1, 0.2, 0.35, 0.65} quantiles of r̂, chosen on OOF predictions; per-bin weights by non-negative least squares on OOF predictions).
- Tests: the gate and weights never see test rows; L5a equals the mean of its inputs.

### Task 4 — Queue wiring, quick config, probe
- Arms in `configs/iter06.yaml`:
  - A-GB;
  - A-CH;
  - S-GB (learning curve);
  - R-shift (×0.5, ×1.5, frozen);
  - R-rep (temporal replication).
- Persist every rung's per-seed models (A10 format) for 07.
- Quick run interactively (< ~5 min). Probe one seed per arm. Estimate the wall time at ≤ 6 workers, and print the scheduling command. Ask first if > ~3 nights.

## Part B — Runs and outputs (`results/iter06_hybrid_ladder/`)
1. **Ladder table:** rows L0–L5 × family; columns are the axes A (GB, CH), S (n = 62, n\*) and R (shift ×0.5, ×1.5, replication). Median [5–90 %], with distinct HP households and † bins.
2. **Step table** (rule 1): each step × family × axis, as better / worse / no difference.
3. **Claim table** (rule 2): inputs and outcome, with T marked "pending 07".
4. **L5 table** (rule 3).
5. **Figures:**
   - WAPE vs rung per axis;
   - learning curves L0–L4;
   - robustness bars;
   - the learned m̂_h vs true m_h (L4b), as a scatter by station.

GB rows quote the 05a D5 deltas and the 05b Arm 7 sensitivity, as in 05b.

## Out of scope
- Transfer runs (07), change detection (08).
- Other targets.
- New model families or feature sets beyond those named.
- Paper text.

## Acceptance criteria
- [ ] Task 0 committed first: DECISIONS, CLAUDE.md §1 and §4, `method_basis.md` references checked or UNVERIFIED.
- [ ] Tasks 1–4 done with tests, and `pytest` passes. Quick run, probe and scheduling command reported.
- [ ] All arms complete (`STATUS.md` 0 remaining), or failures listed. Models persisted and reload-checked.
- [ ] `data/` (outside `_paperb/`) and `models/` untouched. Push only on Alex's request.
- [ ] REVIEW.md (§9) decisions cover:
  1. the ladder steps (what each ingredient buys);
  2. the hybrid claim so far (A, S, R) and what 07 must show;
  3. L5 kept or dropped;
  4. which L4 variant (a or b) is the method's default for 07.

## Amendments (recorded before the run; DECISIONS.md 2026-10-12)
- **[A1] Axis S, configuration set.** S-GB runs on anchor `size` and one feature set per rung: L1 `whdd` (CNN `raw`), L2 `netfit` (CNN `rawphys`), L3 and L4 on the L2 inputs (L4: `l4a` and `l4b`). The n = all point is A-GB restricted to the same configurations. Axis A, the R arms and the persisted models keep the full grid. Reason: "the same designs as 05b Arm 1", which ran netfit × size (05b A4); about −92 job-h.
- **[A2] TabPFN train-set prediction.** TabPFN does not predict its train substations (`wape_train` is NaN). No table or rule of this brief uses it; about −60 job-h.
- **Open, not yet decided:** the CNN on the GB arms with the seed's 05b Arm 2 hyperparameters and one inner-CV pass per configuration (`fixed_params` in `configs/iter06.yaml`), instead of 30 evaluations per configuration.
