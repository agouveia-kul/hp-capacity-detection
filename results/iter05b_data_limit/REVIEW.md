# Iteration 05b — Is training data what holds ML back? (final: Stage 2, Arms 3–7)
**Goal:** test whether the Stage 1 result (ML ahead of physics on GB-EoH above n\* ≈ 40–75 HP households) survives another year (Arm 6), a ±50 % shift of the fillers' temperature response (Arm 7) and B\* under v1.1 (Arm 5), read the S test (Arm 3) and the error decomposition (Arm 4), and apply A12.
**Branch / commit:** iter/05b-data-limit @ 255f1d8 (Stage 2 code), ba970c4 (probe + estimate), dba621f (A12), a44fa60 (report script, before any Stage 2 result was read), results + this REVIEW in the commit that adds this file.
**Changed:** logic ≈ 472 lines (over the ~300 budget: 342 are the report script the handover asked for): `iter05b_report2.py` (new, 342), `runtime_estimate.py` (+50, `--stage2`), `run_queue.py` (+34: frozen specs per seed, `frozen_model`, `spc_train`), `persist.py` (+27: `frozen_predict`), `run_benchmark.py` (+23: `@frozen` row, cache-read retry), `oracle.py` (+10: cache-name fix); tests +124 (`tests/test_05b.py`: 6 new tests, 10 cases). Configs: `iter05b_arm{3,4,5,6,7}`, `iter05b_stage2`, `iter05b_probe_stage2`, `iter05b_quick_stage2`. Brief + DECISIONS: A12 and three Stage 2 decisions. Results: `stage2/<arm>/*`, `stage2/report/*` (generated, script unchanged after its commit), `stage2/wall_times.csv`, `runtime_estimate_stage2.md`, `jobs/*.done`, `quick_stage2/*`. Not committed: `jobs/*.parquet` (41 MB), `predictions.csv`.

**Results** (WAPE %, median over seeds; † = filler-variability-limited bin; HP households used: GB-EoH main **274 train / 81 test**, replication 226 / 61, B\* 62 / 20. Stage 1's REVIEW wrote 292 / 81: 292 is the train split, 274 the households inside substations.)

| | best physics row | linear | neural (TabPFN) | raw-series (CNN) |
|---|---|---|---|---|
| Arm 2, GB-EoH main, 20 seeds (Stage 1, of record) | 25.8 `paperA_corr` | 21.2, −5.8 pp, 20/20 ✔ | 16.8, −9.8 pp, 20/20 ✔ | 16.2, −9.1 pp, 20/20 ✔ |
| 05a D5 swap Δ (fusion bound, pp) | – | −0.33 | −0.42 | n/a |
| **Arm 6**, replication Oct 2022 – Sep 2023, 10 seeds | 24.9 `paperA_corr_own` | 20.9, −3.8 pp, 9/10 ✔ | 16.9, −8.4 pp, 10/10 ✔ | 17.9, −7.3 pp, 10/10 ✔ |
| Arm 6 per bin (criterion met) | | ≤15 † only | ≤15 †, 35–65 † | ≤15 † only |
| **Arm 7**, model refit on scaled data, Δ vs ×1.0 at ×0.5 / ×1.5 | −7.6 / +8.1 | −5.3 / +3.7 | −4.1 / +3.1 | −3.0 / +3.1 |
| Arm 7, frozen Stage 1 model, Δ vs ×1.0 at ×0.5 / ×1.5 | | +2.5 / +7.0 | +1.9 / +8.5 | −0.4 / +4.0 |
| Arm 7, frozen model beats best physics, seeds at ×0.5 / ×1.5 | 18.1 / 33.8 | 0/10 / 10/10 | 5/10 / 10/10 | 10/10 / 10/10 |
| **Arm 5**, B\* v1.1, 20 seeds, tuned (03b, v1: best physics `slope_base` 21.1, 4/166 configs) | 19.3 `paperA_corr_own` (`slope_base` 21.2) | 20.0, −0.9 pp, 12/20 ✘ | 17.6, −2.0 pp, 14/20 ✘ (FFNN alone 20.1, 7/20 ✘) | 22.4, +0.2 pp, 9/20 ✘ |
| **Arm 3**, drop 10 → 40 substations per cell at n = all (n = 62) | 25.6 → 25.6 (25.4 → 25.1) | 0.3 pp, 8/10 (−0.3) | 0.3 pp, 7/10 (−1.7) | **1.2 pp, 8/10 → S** (1.4 pp, 7/10) |
| **Arm 4**, ML on O1 (perfect disaggregation), by anchor size / size_peak | 13.0 `oracle_O1` | 7.0 / 7.8 | 7.1 / 5.9 | 10.0 / 7.5 |

**A12 inputs** (applied as written; `stage2/report/a12.csv`, `a12_b_inputs.csv`). (a) = 03b criterion overall in Arm 2 and in Arm 6. (b) = seeds in which the frozen model beats the best physics row of the same scaled arm, ×0.5 / ×1.5, need ≥ 8/10 at both.

| family | (a) Arm 2 | (a) Arm 6 | (a) | (b) all | ≤15 † | 15–35 † | 35–65 † | >65 | (b) overall | (b) every bin > 15 % | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| linear | 20/20, −5.8 | 9/10, −3.8 | ✔ | 0 / 10 | 4 / 9 | 0 / 7 | 1 / 6 | 3 / 4 | ✘ | ✘ | other combination |
| neural | 20/20, −9.8 | 10/10, −8.4 | ✔ | 5 / 10 | 9 / 10 | 0 / 2 | 7 / 7 | 9 / 10 | ✘ | ✘ | other combination |
| raw-series | 20/20, −9.1 | 10/10, −7.3 | ✔ | 10 / 10 | 9 / 10 | 8 / 7 | 8 / 9 | 8 / 9 | ✔ | ✘ | lead changes |

**A12 outcome: the families differ, so it is "any other combination → reported, and Alex decides".** Dropping `paperA_corr_s0unscaled` from the physics candidates changes no outcome. Error decomposition of `paperA_sh_mh` (Arm 4, `fig_error_decomposition.png`): GB-EoH overall 87.3, of which fill contamination 75.4 and scale dispersion 13.0 (>65 %: 5.3 and 10.3); B\* 42.8, with 30.8 and 16.8 (medians over seeds, so not exactly additive); on B\* the fillers' response costs `paperA_sh_mh` 21.9 pp and the HP homes' own non-HP response 10.0 pp, `paperA_corr` 2.1 and 2.2 pp. `paperA_corr_own` on B\*: 19.3 vs `paperA_corr` 23.7 (−3.0 pp, 13/20 seeds) and vs the best label-calibrated row `slope_base` 21.2 (−0.9 pp, 13/20); per bin −0.6 †, +1.4 † (15–35 %, 2/20), −0.8 †, −2.5. **Wall time:** 439 job-h, 76 h busy (probe 5 h + run 71 h; estimate 23–35 h): Arm 5 179 job-h, Arm 3 121, Arm 4 55, Arm 7 45, Arm 2 CPU reference 22, Arm 6 17. 580/580 jobs, 0 failed (`check_jobs.py` OK). pytest after the runs: 133 passed, 1 skipped (CUDA), 1 xfailed (the CNN CPU-vs-GPU case, documented).

**Assumptions & deviations:**
- A10: frozen Arm 2 specs replace inner-CV selection in Arms 3, 4, 6, 7; kernel and trees are not run in Stage 2 (Arm 5 runs the three carried families + FFNN, tuned). Arm 3's specs were tuned at n = all with 10 per cell, which favours that design.
- A11 deviation from A9, and beyond it: the CNN retrained on the CPU is not the GPU model (below). Stage 2 CNN deltas are paired with the new arm `arm2_cpu` (decision 2026-10-07); Arm 2 stays the result of record.
- ML on O1 uses the frozen spec as is, not the brief's netfit × size (decision 2026-10-07); with `size_peak` the anchor is the HP aggregate's coincident peak.
- A12 readings fixed in the report script before the results: `paperA_corr_s0unscaled` is a physics candidate (hardest for ML); the outcome is read per family and jointly only if the families agree.
- The Stage 2 run was started by the agent as a detached process on Alex's request (no scheduled task was registered). The quick run took 27 min, not ~5.
- Multiplicity: 3 families × 5 scopes × 2 factors in A12 (b); 3 families × 2 n in S. GB labels are 30-min, B\*'s 15-min: compare gaps, not levels.

**Problems found:**
- **`oracle_O2` is an identity:** m_h(true) is fitted on the same HP aggregate whose slope it divides, so P̂ = HP_Peak and "fit noise" is 0.0 (B\* 0.5) by construction. The decomposition has two informative terms.
- **The CNN is fragile to retraining.** Same spec, hyperparameters and epochs, CPU instead of GPU: per-seed ΔWAPE std 3.2 pp over 20 seeds, median +0.3, seeds 8 and 9 at +8.7 and +10.8 pp (27 % WAPE). On the CPU it is deterministic (Arm 3 at 10 per cell reproduces `arm2_cpu` exactly). The S result rests on it: of the 8 improving seeds, 2 are those collapses repaired at 40 per cell, and the median drop lies between 0.6 and 1.9 pp.
- Frozen linear and TabPFN models do not transfer to a halved filler response (0/10 and 5/10 against physics, which itself improves by 7.6 pp); refit on the scaled data their median WAPE stays below physics (15.6 and 12.8 against 18.1 at ×0.5).
- Runtime: jobs ran 1.5–13 × slower than in the probe (6 workers × 4 threads on 20 cores); one CNN job took 13.1 h, the probe's 4.2 h against 471 s alone. The queue has no per-job timeout.
- Fixed before any Stage 2 run: the ×0.5 filler cache was named `rscale0.npy` (shared with factor 0); cache reads raced with a concurrent replace (one quick-run job failed, rerun).

**Decisions for Alex:**
1. **Verdict.** Stage 1's D (linear, CNN) + F stands. S holds by the rule for the CNN at n = all only (1.2 pp, 8/10; per bin: 15–35 † at n = all, ≤15 † at n = 62) and for no other family. *Recommended:* record "D + F; S formally met for the raw-series family, not robust (CNN retraining noise)".
2. **Dominant error and the paper lead (A12).** Fill contamination dominates s_h / m_h (75 of 87 pp on GB-EoH); once corrected, scale dispersion (13–17 pp) is the floor, and ML also goes below it on O1. A12 gives "Alex decides": the gain replicates in a second year for all three families, but only the CNN's frozen model stays ahead of physics at both filler factors, and above 15 % no family passes every bin. Options: (i) keep the identifiability-bounded lead and report the ML gain as replicated but conditional on the non-HP temperature response it was trained on; (ii) the A12 lead restricted to the raw-series model; (iii) the full A12 lead. *Recommended:* (i).
3. **GB-EoH as headline pool for 06 / 07?** *Recommended:* it stays the second pool. B\* (Arm 5, v1.1) confirms 03b: no family and 0 of 60 configurations beat the best physics row overall; the GB-EoH gain sits mostly in the ≤15 % † bin and moves by up to 8.5 pp with the fillers' response.
4. **Simulator.** The rule allows it (verdict D). *Recommended:* no-go for now: the households that helped are real ones, hplib misses EoH electricity by 20 %, and 07 can first test whether the saved GB-EoH models help B\*.
5. **`paperA_corr_own`.** It closes the gap on B\* overall and in 4 of 5 scopes (not 15–35 % †) and is B\*'s best physics row. *Recommended:* add it to the physics reference set.
