# Paper B — structure after the storyline change (agreed by Alex, 2026-10-09)

**For the paper agent.** Agreed by Alex on 2026-10-09 (open points answered at the end). Apply it to `main.tex` and `structure.tex` as headings, outline comments and planned figures/tables only. Do not draft new prose from it; drafting rules in `paper/HANDOFF.md` §6 still apply.

## Storyline (Alex, 2026-10-09)
1. The LV network and its DER are unobservable.
2. Physics-based estimation (Paper A) has limits.
3. Data-driven estimation (feature types × models) has other limits.
4. A **hybrid, identifiability-guided estimator** (the methodological contribution).
5. Validation by transfer.
6. Use case: detecting a change in capacity.

Target: capacity only ($P_{\mathrm{TCL}}^{\max}$).

## Proposed sections

| # | Section | Content | Evidence (iteration) |
|---|---|---|---|
| I | Introduction | unobservable LV/DER; Paper A; the gap; contributions: (1) the hybrid estimator, (2) the validation methodology (household-disjoint semi-synthetic aggregates, statistical-matching fusion), (3) transfer evidence, (4) the use case | – |
| II | Problem Statement | net-load decomposition, target, what net load identifies (short; cite Paper A, do not repeat it) | Paper A |
| III | Physics-Based Estimation and Its Limits | Paper A estimator; non-TCL correction incl. the own-load term; limits: filler contamination, scale (m_h) dispersion, transfer of m_h | 03b, 05b Arm 4 |
| IV | Data-Driven Estimation | features: generic, physics-derived, raw series; models: linear, kernel, trees, neural (incl. TabPFN), CNN; limits: data hunger (n\*), sensitivity to the fillers | 05b Stage 1–2 |
| V | Hybrid Identifiability-Guided Estimation | identified slope; transferable scale (pilot, design-temperature normalisation, learned); ML residual; ensemble of experts only if it passes its rule | 06 |
| VI | Data and Semi-Synthetic Aggregates | current Section IV (IV-A/B reviewed, IV-C in review) | 05a |
| VII | Results | **A Evaluation** (error metrics, seeds and splits, inner-CV selection, comparison criterion, penetration bins, the four axes: accuracy, sample efficiency, robustness, transfer; the 5 % filler-variability criterion); B physics-based; C data-driven (accuracy, learning curve, robustness); D the hybrid ladder | 03b, 05b, 06 |
| VIII | Transfer Validation | CH ↔ GB under harmonised labels; all rungs | 07 |
| IX | Use Case: Detecting a Change in Capacity | compact demonstration | 08 |
| X | Discussion | | |
| XI | Conclusion | | |
| App. | A design envelope; B hyperparameters; C filler-variability derivation | | |

## What changes vs the 2026-10-09 morning structure
- The RQ1–RQ4 results sections become a method ladder (III → IV → V), with results in VIII and transfer and the use case as their own sections.
- Other targets (RQ1) are dropped for now.
- "Learning the Transfer Parameter" moves from Estimators into the hybrid (V) as its central part.
- Anchor-only baselines stay removed. The scale features stay under Features.
- Section IV-C (aggregates) is unchanged in content; it becomes VI-C.
- The separate Evaluation Protocol section is gone: evaluation is subsection VII-A of Results.

## Answered by Alex (2026-10-09)
1. **Methods-then-results:** III–V are methods, VII holds the results, mirrored subsection by subsection.
2. **Evaluation is a subsection of Results** (VII-A), describing the error metrics and how the methods are evaluated. The aggregate-construction rules stay in VI-C.
3. **The use case stays in this paper** for now (IX); revisit once 08 shows its size.
