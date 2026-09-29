# Iteration 03b — Fair test of ML against the physics estimator: runs and results

**Branch:** `iter/03b-fair-test-runs`, from `main` after 03a is merged.
**Type:** a few small code additions (≤ ~250 logic lines, Tasks 1–4), then runs and results. REVIEW.md reports numbers; the paper narrative is decided in review.

## Decisions carried into this iteration (Alex, 2026-09-29, 03a review)
1. **Pilot:** all train HP households (multi-station, capacity-weighted temperature) is the headline. The station-matched pilot is a sensitivity row.
2. **Invalid P̂_A:** predict 0 and count it. Score against `HP_Peak`, and footnote Paper A's capacity definition (they differ by 0.03 pp WAPE).
3. **Budget:** the ≈ 7.7 h plan. `XGBoost_mono` runs only with the `size_peak` anchor; the learning curve uses 10 seeds × 3 draws.
4. **Residual intercept:** kept. The bias-calibrated P̂_A row (Task 2) is reported next to it.

Record all four in DECISIONS.md.

## Why the additions
A residual model must not get credit for corrections that are really physics or a constant scale factor. Three physics-side baselines and one protocol fix make the comparison fair.

## Task 1 — Paper A with non-TCL correction (`paperA_corr`)
This is the correction Paper A lists as future work.
- Estimate a per-household non-TCL heating sensitivity s₀ from the **train fill households** of each seed: fit Paper A's net-load hockey stick to their aggregate, then s₀ = s_h(fill aggregate) / N_fill.
- Corrected estimate: P̂ = max(s_h − N · s₀, 0) / m_h. N is the substation's dwelling count, which a DSO knows. Count zeros the same way as invalid P̂_A.
- Sensitivity variant `paperA_corr_all`: estimate s₀ from the fill households **plus** the HP households' own non-HP load. Some of that load contains electric water heaters (M9); report how much s₀ moves.

## Task 2 — Bias-calibrated Paper A (`paperA_cal`)
- P̂ = P̂_A · exp(b), where b is the mean of the **cross-fitted** train residual targets z (Task 3). This is a one-parameter calibration and the equivalent of the residual intercept alone.
- Also report `paperA_corr_cal`, the same calibration applied to `paperA_corr`.

## Task 3 — Cross-fitted pilot for residual targets
- For each inner fold k (the existing K = 4 household-disjoint folds), compute m_h from the train HP households **not** in fold k. Use it for z on the fold-k inner and train substations. Residual training targets are then out-of-sample on the pilot side.
- Test predictions keep the pilot of all train HP households.
- The cross-fitted pilots use about 3/4 of the households. Report the spread of the fold m_h values against the full-pilot m_h.
- Applies to every residual model and to `paperA_cal`.

## Task 4 — Small fixes
- Add Berchtoldstag (2 January) to the ZH holiday calendar, and extend the test.
- Report WAPE in **Paper A's penetration bins** as well: ≤ 15 %, 15–35 %, 35–65 %, > 65 %, and overall. This makes the numbers comparable with Paper A's Table "baselines" (19.3 % overall).

## Task 5 — Runs
Run `configs/iter03b_quick.yaml` first, then the full arms. Report the actual wall time.

| Arm | Pool / seeds | What |
|---|---|---|
| Main | B\* / 20 | anchors {none, size, size_peak} × feature sets {whdd, netfit, both} × {direct, direct-log, residual} × 7 models, plus `XGBoost_mono` (size_peak only) |
| Physics | B\* / 20 | `paperA_sh_mh`, `paperA_sh_mh_station`, `paperA_cal`, `paperA_corr`, `paperA_corr_all`, `paperA_corr_cal`, slope-only, slope + base, calibrated delta, anchor-only baselines |
| Learning curve | B\* / 10 × 3 draws | n_train_hp ∈ {16, 32, 48, all}: all physics rows above, plus the best direct and best residual model of each family (chosen by **inner-CV** WAPE, never by test) |
| Sensitivity | B / 10 | the main arm restricted to anchor `size_peak`, feature set `both`, direct-log + residual, all models, plus all physics rows |

## Task 6 — Pre-registered comparison criterion
The criterion is fixed now, before any results are seen. For each ML configuration, compute the paired per-seed ΔWAPE against the **best physics row**. The best physics row is chosen by median WAPE over seeds among the physics rows in Task 5, excluding anchor-only.

ML **beats physics** only if both hold:
1. ΔWAPE < 0 in ≥ 16 of 20 seeds;
2. the median ΔWAPE ≤ −1 pp.

Otherwise the result is "no better than physics" (report it, whichever way it goes). Apply the same criterion per penetration bin.

## Task 7 — Tables and figures (`results/iter03b_fair_test/`)
1. **Headline table (B\*):**
   - rows: all physics rows, the best anchor-only, the best direct ML per feature set, the best residual ML;
   - columns: WAPE overall and per Paper A bin, then MAPE and R², as median [5 %–90 %].
2. **Ablation table:** feature set × {direct, direct-log, residual} × model, WAPE median [5–90]. Mark the best cell per row.
3. **Comparison table:** the Task 6 criterion outcome for each ML configuration against the best physics row (overall and per bin), with the win count out of 20 and the median ΔWAPE.
4. **Learning-curve figure:** WAPE vs n_train_hp for the physics rows and the selected models, with bands across seeds × draws.
5. **Figure:** WAPE by penetration bin for the best physics row, the best direct ML and the best residual ML.
6. **Diagnostic:** the median P̂/y by penetration for `paperA_sh_mh` vs `paperA_corr`, which shows whether the correction removes the low-p bias (1.75 at p = 0.05 in the 03a probe).

## Out of scope
- Other targets and the daily arm (04).
- Transfer (05).
- Feature-set changes beyond Task 4.
- Notebook edits.

## Acceptance criteria
- [ ] Tasks 1–4 are implemented with tests (s₀ estimated from train households only; cross-fitted pilots are household-disjoint from their fold; Berchtoldstag present), and `pytest` passes.
- [ ] All four arms have completed, or a failure is listed with its reason. The actual wall time is reported.
- [ ] `metrics.csv`, `summary.csv`, the tables and the figures are in `results/iter03b_fair_test/`.
- [ ] `data/` (outside `data/_paperb/`) and `models/` are unmodified.
- [ ] REVIEW.md follows the §9 template. The decisions must cover at least:
  1. **The paper's lead:** does any ML configuration meet the Task 6 criterion against the best physics row (overall or in any bin)?
  2. whether `paperA_corr` becomes the physics reference for 04/05;
  3. which feature set and model family carry forward to 04 (targets) and 05 (transfer).
