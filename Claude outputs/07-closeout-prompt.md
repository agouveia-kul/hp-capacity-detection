You are closing out iteration 07 (transfer validation) of Paper B in `agouveia-kul/hp-capacity-detection`, on branch `iter/07-transfer` (REVIEW at `6f97acc`). Read CLAUDE.md and the tail of DECISIONS.md first.

Alex accepted the orchestrator's review of `results/iter07_transfer/REVIEW.md` and its three recommendations (2026-11-18). This session covers bookkeeping, small additions to the report from saved outputs, and CLAUDE.md text. **No reruns and no new fits.**

## Rules
- `scripts/paperb/iter07_report.py` is frozen. Put additions in `scripts/paperb/iter07_postreview.py`, writing to `results/iter07_transfer/report/postreview/`. Label them **post-review, not of record**.
- `data/` (outside `data/_paperb/`) and `models/` stay untouched. Never print or commit tokens.
- Commit on `iter/07-transfer` and push the branch. **Merge into `main` only when Alex says so in this conversation.**

## Task 1 — DECISIONS.md (append verbatim)
```
2026-11-18 | 07 | Outcome as pre-registered (191/191 jobs): T1 not confirmed (H* TabPFN L2 vs D* CNN L1: 7/10 seeds in both directions, median -6 % CH->GB, -17 % GB->CH); T2 better in both directions vs slope_base (10/10; -42 %, -27 %), but slope_base is weak under transfer (post hoc, by median: calibrated_delta, paperA_sh_mh, L1 TabPFN and the label-free target-s0 row are below H*); T3 mixed (L2 vs L1 no difference for every family and direction); 06 rule 2 stays failed. Transfer WAPE: H* 52 % CH->GB, 31 % GB->CH. | Final 07 REVIEW; orchestrator review 2026-11-18.
2026-11-18 | 07 | Run go and Part A open items (confirmed by Alex): the full run was started on Alex's request after A2; immersion = 0 for the 40 GB homes without a P_ih channel (bound -0.46 % of the GB HL total); CH T_design -8 degC, UNVERIFIED until sourced. | PART_A.md open items.
2026-11-18 | 07 | Reading of the label-free target-s0 row (secondary, outside the rules): GB->CH it beats CH's own in-pool physics (5.6 vs 7.9 nMAE), as does uncorrected paperA_sh_mh (6.4 vs 15.9), so part of its transfer score is the GB pilot scale offsetting CH's own-load bias, not transfer skill; CH->GB it ties L1 TabPFN (8.8) and stays 3.8 pp above in-pool. What holds: the physics bias changes sign with direction, tracking the filler-slope ratio (s0 CH 0.0054, GB 0.0126 kW/K). The best-transferring rows carry no net-load slope (L1 TabPFN, size_peak in 10/10 seeds; calibrated_delta, gap -1.4 pp); the slope-based inputs of L2/L3 import the s0 mismatch. | Orchestrator review 2026-11-18.
2026-11-18 | plan | Decision 1 (after 06 and 07): the paper is reframed. Contribution = a pre-registered, identifiability-guided analysis of what aggregated LV net load lets physics, data-driven and hybrid estimators learn and transfer: the hybrid ladder is reported with its negative results (L4 learned scale, L5 ensemble) and with the post hoc L2/L3 in-pool gain that is not confirmed under transfer (T1); under transfer every ML rung loses 2-4x its in-pool error; the HP-side scale (m_h, peak scaling) transfers approximately, while the non-HP temperature response s0 is site-specific and is the transfer bottleneck. A label-free estimator with a locally estimated s0 is a candidate contribution only if 07b confirms it on unseen data. Storyline steps 1-3 and 6 unchanged; step 4 becomes "identifiability-guided hybridisation, tested as a ladder"; step 5 "transfer: what is transferable and what is site-specific". | Alex, 2026-11-18.
2026-11-18 | 07b | Decision 2: before any local-s0 rung is pre-registered, a read-only audit (07b-i) finds which on-disk dataset can serve as an unseen target (HP labels, temperature, a local non-HP sample for s0, own-load observability, household-disjoint from B* and GB-EoH). No estimator, prediction or error metric is computed on any candidate in 07b-i. The 07b rung must include the HP homes' own non-HP load term. | Alex, 2026-11-18; both pools are now spent for confirmation.
2026-11-18 | 08 | Decision 3: 08 (change detection within GB-EoH, main and replication years) pre-registers two estimators with no single primary: TabPFN L2 (the frozen 06 A-GB winners) and paperA_corr with the site's own s0 (label-free); change is detected and quantified on differences between years, so a stable bias cancels. | Alex, 2026-11-18.
2026-11-18 | method | From 07b and 08 on, every CNN that trains several initialisations chooses among them on a household-disjoint validation fold, not on inner substations that share households with train (the 06 B1 deviation selected a collapsed GB seed-6 L4a refit in 07: in-pool WAPE 213.8 %). Earlier results stand. | Orchestrator review 2026-11-18.
```

## Task 2 — CLAUDE.md (exact edits)
1. **§1 Purpose.** Replace the paragraph that starts "**After 06 (decision 2026-11-13):**" with:
   > **After 06 and 07 (decisions 2026-11-13, 2026-11-18):** the paper is a pre-registered, identifiability-guided analysis of what aggregated net load lets physics, data-driven and hybrid estimators learn and transfer.
   > - The hybrid ladder is reported with its negative results (L4, L5) and with its post hoc in-pool gain (L2/L3), which is not confirmed under transfer (07 T1).
   > - Under transfer the HP-side scale transfers approximately, while the non-HP temperature response s₀ is site-specific and is the bottleneck.
   > - A label-free estimator with a locally estimated s₀ becomes a contribution only if 07b confirms it on unseen data.
2. **§1 storyline list.**
   - Item 4 becomes: "identifiability-guided hybridisation, tested as a pre-registered ladder (what pays within a pool, what does not)".
   - Item 5 becomes: "transfer: what is transferable and what is site-specific".
3. **§1 Iteration plan.** Replace the lines from 07 onwards with:
   - 07 — transfer validation CH ↔ GB; done (T1 not confirmed);
   - 07b-i — read-only audit of unseen targets for a label-free local-s₀ estimator;
   - 07b — confirmatory test of that estimator, if 07b-i finds a target;
   - 08 — change-detection use case within GB-EoH (two years);
   - 09+ — freeze and draft.

## Task 3 — Post-review additions (`iter07_postreview.py`, saved outputs only)
1. **WAPE beside nMAE.** Rebuild the REVIEW's results table with both metrics: overall, and the ≤ 15 % bin for each direction.
2. **Bias decomposition table**, per direction, from the saved predictions. Give the median signed error (% of max y) for:
   - the physics rows with source s₀ (`paperA_corr`, `slope_base`);
   - the physics row with target s₀;
   - `paperA_sh_mh`;
   - H\*;
   - L1 TabPFN.

   Split it by bin and list it next to the s₀ values in use. This supports the second 2026-11-18 reading line.
3. **Seed 6 without the collapse.** Repeat T3's L4a-vs-L3 CNN rows with seed 6 excluded, as already stated in the REVIEW. Show this as one line, not of record.

## Task 4 — REVIEW addendum
Append "**Post-review (2026-11-18)**" (at most ~20 lines):
- the WAPE table;
- the bias table, or a pointer to it;
- the decisions, quoting their DECISIONS dates;
- one sentence that the target-s₀ row's GB→CH score is partly bias cancellation.

Commit, push the branch, report the hash, and stop.
