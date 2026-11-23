You are closing out iteration 06 (the hybrid ladder) of Paper B in `agouveia-kul/hp-capacity-detection`, on branch `iter/06-hybrid-ladder` (REVIEW at `a5eb154`). Read CLAUDE.md and the tail of DECISIONS.md first.

Alex has accepted the orchestrator's review of `results/iter06_hybrid_ladder/REVIEW.md` (2026-11-13). On 2026-11-16 he added one metric change. Everything below is bookkeeping, post-review analysis of saved outputs, and one small metric function.

## Rules for this session
- **No reruns and no new model fits.** Use only the saved outputs: `predictions.csv`, `l4.csv`, `metrics*.csv`, `timing.csv` and the logs.
- `scripts/paperb/iter06_report.py` is frozen (committed before the results were read). Do not edit it. Put every addition in the new script `scripts/paperb/iter06_postreview.py`, with outputs in `results/iter06_hybrid_ladder/report/postreview/`. Label everything there **post-review, not of record**.
- `data/` (outside `data/_paperb/`) and `models/` are untouched. Never print or commit tokens.
- Commit on `iter/06-hybrid-ladder` and push the branch. **Merge into `main` only when Alex says so in this conversation** (hard rule 6).
- **CLAUDE.md:** apply exactly the edits below. Leave the rest unchanged.

## Task 1 — DECISIONS.md (append verbatim, in this order)
```
2026-11-13 | 06 | Outcome as pre-registered: rule 2 fails (hybrid = TabPFN L4, A-GB 19.4 % vs best pure data-driven TabPFN L2 16.4 %, gap +3.0 pp > 1 pp; S worse, R no difference; not CNN-dependent; T cannot rescue it). Rule 1: L2 vs L1 better for linear and TabPFN, no difference for the CNN (CNN-dependent across families); L3 vs L2 better for linear, no difference for TabPFN; L4 vs L3 worse in all families on A-GB and S-GB, the loss in the <=15 % bin. Rule 3: L5 dropped on the registered reading (pooled filler-variability-limited bins); taken one bin at a time, both forms would pass in 15-35 % only, which is reported but not used (not the registered reading). | Final REVIEW, rules applied as fixed in the iter06_report.py docstring (7b723e5).
2026-11-13 | 06 | Decision 1: the paper's method becomes identifiability-guided hybridisation through the inputs and the target (L2 physics-derived features; L3 residual on the Paper A estimate), labelled post hoc in the paper; the learned transferable scale (L4) is reported as a pre-registered negative result (scale not identifiable within a pool; corrected base unidentified at <=15 % penetration). No revised L4 now; a revision is allowed only as a new rung pre-registered after 07 and tested on unseen data. | Alex, 2026-11-13.
2026-11-13 | 07 | The confirmatory test of the post hoc method is fixed in the 07 brief before any 07 run: L2 and L3 (per family) against L1 and L0 on transfer data under the 03b-style criterion, so the 06 choice is confirmed or refuted on data it has not seen. | Alex, 2026-11-13; converts a post hoc selection into a confirmatory test.
2026-11-13 | 06 | Decision 2: L5 is dropped (rule 3) and the R(i) label-free update row is not a deployment mode: at x0.5 the frozen residual inflates a correct re-estimated base (exp(f) of about 25 at p = 0.05), so a multiplicative residual is not separable from the base it was trained on; reported as a robustness finding, alongside physics' label-free update gain (-7.6 pp at x0.5). The REVIEW adds the median exp(f) per bin at x1.0 and x0.5. | Alex, 2026-11-13.
2026-11-13 | 07 | Decision 3: 07 carries every rung with L4a as the only L4 variant; L4b is not carried (T_design is one value per training pool, so L4b cannot learn its effect). The 07 runtime estimate includes a CNN epoch cap and a timeout that fires on time; the own-load term and label harmonisation follow iterations/07-transfer-notes.md. | Alex, 2026-11-13.
2026-11-13 | 06 | S-GB n = 32 is reported as registered (flagged: usable designs differ by job type, 7-15 of 20) and on the designs feasible for every job type; n* is reported both ways; the cause is traced before any sample-efficiency figure enters the paper. n = 62 (the primary S point, 20/20 everywhere) is unaffected. No rerun. | Final REVIEW problem 3.
2026-11-13 | 06 | Recorded deviations: B1's final-fit initialisation is chosen on inner substations that share households with train (no household-disjoint set exists for a full-train fit; screens out collapsed initialisations, not an unbiased loss; decided before results, PART_A.md); after the results, the robustness figure's panels got separate y-axes (display only, no number or rule changed). | Final REVIEW.
2026-11-16 | metric | Primary metric from iteration 07 on and in the paper's tables: nMAE = mean|y_hat - y| / max(y) x 100 %, computed per evaluation set (one seed x dataset x arm cell; per Paper A bin, over that bin's substations with the bin's own maximum); the normaliser max(y) in kW is reported beside each cell. WAPE stays as the secondary metric (continuity with Paper A). Inner-CV model selection stays on WAPE unless an iteration brief says otherwise. | Alex, 2026-11-16.
2026-11-16 | metric | Decisions already taken stand as recorded (03b, 05b and 06 rules were applied on WAPE). On a fixed evaluation set nMAE = WAPE x mean(y)/max(y), so per-seed signs and seed counts are unchanged and only the size of differences shrinks (06 test sets: mean/max 0.21 on GB, 0.32 on CH; per seed 0.20-0.22 and 0.30-0.35), so a 1 pp threshold cannot be carried over. From 07 on, "better" = paired per-seed difference < 0 in >= 8 of 10 seeds and median per-seed relative difference <= -5 %, which gives the same verdict in nMAE and WAPE on the same set. 06 tables are recomputed in nMAE from saved predictions (no rerun), and the 06 rules are re-applied in this form as a sensitivity, not of record. | Orchestrator, 2026-11-16, before any 07 run.
```

## Task 2 — CLAUDE.md edits (exact)
1. **§1 Purpose:** after the sentence ending "…learns only the part it does not (the scale m_h and a residual).*", insert:
   > **After 06 (decision 2026-11-13):** the method is identifiability-guided hybridisation through the **inputs** (physics-derived features, L2) and the **target** (a residual on the Paper A estimate, L3). It is labelled post hoc and tested confirmatorily on transfer in 07. The learned transferable scale (L4) and the ensemble (L5) are pre-registered negative results.
2. **§1 Iteration plan:**
   - change the 06 line to "06 — the hybrid ladder (L0–L5; axes A, S, R), both pools; done (rule 2 failed; L5 dropped)";
   - change the 07 line to "07 — transfer validation: confirmatory test of L2/L3 (rules T1–T3), axis T for the 06 record, CH ↔ GB under the harmonised label `HL`".
3. **§4:** replace the bullet that begins "**Primary metric = WAPE**" with:
   > - **Primary metric = nMAE** (from 07; decision 2026-11-16): mean|ŷ − y| / max(y) × 100 %, per evaluation set (seed × dataset × arm; per Paper A bin over that bin's substations, with the bin's own maximum). Report the normaliser max(y) (kW) beside each cell. It comes first in `summary.csv` and in every table. **WAPE** (Σ|ŷ − y| / Σy, as in Paper A) is secondary; MAPE and R² follow. On one set nMAE = WAPE · mean(y)/max(y). Results up to 06 were decided on WAPE and stand as recorded.
4. **§4, after the line "On R the degradation is compared, not the level.":** add
   > *(06 rules, applied on WAPE, of record.)* From 07 on, "better" = paired per-seed difference < 0 in ≥ 8 of 10 seeds **and** median per-seed relative difference ≤ −5 % (the same verdict in nMAE and WAPE).

## Task 3 — The metric (`scripts/paperb/metrics.py`)
- Add `nmae` = mean|ŷ − y| / max(y) × 100, NaN when max(y) ≤ 0. Put it first in `METRIC_ORDER`.
- Check that the per-bin (`pbin…`) cells call `compute_metrics` on the bin's subset, so that each bin uses its own maximum. Do not change how WAPE is computed.
- Tests:
  - nMAE = WAPE · mean(y)/max(y) on random data;
  - each bin uses its own maximum;
  - NaN behaviour.
- `pytest` passes.

## Task 4 — 06 in nMAE (`iter06_postreview.py`, saved outputs only)
- For A-GB, A-CH, R ×0.5 / ×1.5 / rep and L5, recompute from `predictions.csv` (and `l5_predictions.csv`):
  - the ladder table;
  - the step table;
  - the claim table;
  - hybrid vs L0;
  - the L5 table.

  Use nMAE, with the normaliser reported.
- **S-GB** saved no `predictions.csv`. Use the MAE in `metrics_lc.csv` and the test-set maximum, **only if** you verify that each S design's test set is the seed's A-GB test set. Otherwise mark S as WAPE-only and say why.
- Re-apply rules 1–3 in the 2026-11-16 form (≥ 8/10 seeds, median relative ≤ −5 %). List every outcome that differs from the record. It is a sensitivity, not of record.

## Task 5 — exp(f) table (Decision 2)
Report the following for the L4 rows, per family and Paper A bin, at ×1.0 (frozen) and ×0.5 (update row):
- the median exp(ẑ) [5–90 %];
- the median y / base.

Take them from the saved `l4.csv` / predictions.

## Task 6 — S-GB n = 32 (no rerun, no code fix)
- Trace from the code and logs why the usable n = 32 designs differ by job type (residual and linear 7, CNN direct/L4 11, TabPFN direct/L4 15 of 20). Name the function and the condition.
- Report n = 32 and n\* in two forms: as registered, and on the designs feasible for every job type.

## Task 7 — REVIEW addendum
Append a section "**Post-review (2026-11-16)**" to `REVIEW.md` (at most ~25 lines):
- the decisions taken (quote the DECISIONS dates);
- the nMAE headline table: A-GB and A-CH per rung × family, nMAE median [5–90 %], with the normaliser;
- any rule outcome that differs in the relative form;
- the exp(f) table (or a pointer to it);
- the n = 32 cause, and the two readings.

Commit, push the branch, report the commit hash, and stop.
