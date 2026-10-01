# Iteration 05a-ii — R1–R8 rebuild, D4 diagnostics, overnight queue, D5 swap test
**Goal:** Apply the 05a-i review decisions, settle the D4 flag, run D5 through the queue, and decide whether 05b can start.

**Branch / commit:** iter/05a-gb-eoh-pool @ CODEHASH (code fba77a1; results and this REVIEW in the last commit). Not pushed: the push was denied by the auto-mode classifier. Interim REVIEW: `REVIEW_05a-ii-a.md`. The ~450-line budget was exceeded (~850 logic lines in total).

**Changed:** line counts in `REVIEW_05a-ii-a.md`. Since then: `gb_eoh.py` (replication window clipped to the last full day, silent-electricity exclusion), `d4_diagnostics.py` (flag renamed), `iter05a_report.py` (`--queue-dir`, replication report), `envelopes_v11.py`, `runtime_estimate.py` (amended 05b arms, measured B\* ratio), `test_05a_ii.py`, CLAUDE.md (restored and updated), DECISIONS.md. Results: `mapping.md` (D1–D5), `d4_diagnostics.md`, `zero_runs.md`, `envelopes.md`, `runtime_estimate.md`, `eoh_selection.md`, `overnight/STATUS.md`. pytest: 74 passed before the last edits (21 min); the 15 new or changed tests pass afterwards.

**Results**

| item | 05a-i | 05a-ii (final) |
|---|---|---|
| GB-EoH main (Nov 2021 – Oct 2022): homes; HP train / test used | 295 (Oct 2021, ≥ 95 %) | **384** (≥ 90 %; EOH2291 excluded); 274 / 81 |
| temporal replication (Oct 2022 – 28 Sep 2023, 363 days) | 244 | **319** (no fallback; 272 shared with main); 226 / 61 |
| test substations per bin ≤ 15 / 15–35 / 35–65 / > 65 % | B\* 75 / 40 / 10 / 10 | main 265 / 125 / 30 / 35; replication 190 / 105 / 30 / 30 |
| D1 / D2 | pass | +5.9 % / 0.24 % of days > 1 K: not raised |
| Task A: real year-to-year Y vs D4 error E, n = 10 / 40 / 120 | D4 raised | Y 0.78 / 0.63 / 0.52 vs E 0.94 / 0.50 / 0.38: **intrinsic**; p ≤ 0.5 filler-variability-limited |
| **D5**, 10 seeds, median ΔWAPE (swap − real), overall, pp | not run | `slope_base` −0.2, `paperA_cal` +1.0, `paperA_corr_cal` −0.7, `slope_only` +1.3, `hdh` +1.7, `calibrated_delta` +1.9; kernel −0.7, linear −0.3, neural −0.4, trees −0.7 |
| D5 cells beyond 2 pp | – | `calibrated_delta` ≤ 15 % +4.1, `hdh` ≤ 15 % +3.0; `paperA_corr` −5…−8 and `paperA_sh_mh` −8…−14 in every bin; kernel 35–65 % +2.0, neural 15–35 % +2.6 and 35–65 % −2.4: **flag raised** |
| D5 median P̂/y change | – | `slope_base` ≤ 0.05, `paperA_cal` ≤ 0.03 at every p |
| wall time | – | D5 105 jobs, 0 failed, 1.5 h (estimate 2.8 h); 05b stage 1 ≈ 23 h, stage 2 ≈ 80 h |

**Assumptions & deviations:**
- D5 ran in the daytime at below-normal priority, started by me at 08:26 on your go. The 22:00 task is still registered; it would find nothing to run.
- D5 measures swap − real, and the real arm is not clean: each B\* HP home keeps its own non-HP load, which can include electric water heating. The `paperA_corr` / `paperA_sh_mh` gain under the swap is therefore not a pure matching error.
- The replication is clipped to 28 Sep (29 Sep has one bin). Weather groups are derived per loaded window, hence 384 vs 388 homes in the same window of two caches.
- The runtime estimate scales the probe; B\* measured 0.11 × GB-EoH per seed (my pre-run guess 0.3). The 05b models are assumed to double the tuning cost.
- CLAUDE.md in the working tree had been overwritten with an older copy; I restored my records on the committed version and kept only your paper-lead sentence.

**Problems found:**
- The D5 flag comes from three sources: the two Paper A rows with a contaminated reference side, the ≤ 15 % bin of two simple physics rows, and small-bin (10 test substations) family winners.
- The Task A error uses a winter-only slope, while the estimators fit a full year: the capacity-equivalent error is pessimistic.
- B\* has 10 test substations in its 35–65 % and > 65 % bins (target ≥ 20), unchanged by p = 0.8.
- The mtimes of the four EoH zips changed on 30 Sep 22:47–22:50 (probably OneDrive); all four pass `zipfile -t`. Meteostat 03772 = London Heathrow Airport is confirmed.

**Decisions for Alex** (answers of 2026-10-01 in italics):
1. **D4 verdict and 05b:** settled earlier (intrinsic; "filler-variability-limited" for p ≤ 0.5; arm 7 in 05b).
2. **D5 against its 2 pp flag.** *Chosen: diagnose `paperA_corr` / `paperA_sh_mh` first (done, `d5_paperA_diagnostic.md`).* The own non-HP load of a B\* HP home has a slope of 0.0181 kW/K (3.3 × a filler's 0.0054; 0.0137–0.0208 over seeds); neither estimator removes it, which leaves ≈ 0.7 kW per HP home (≈ 10 % of HP_Peak) in the estimate. That predicts the observed real − swap shift (actual / expected 0.8, r = 0.5 per substation). So the 7–11 pp is a property of the real arm, not matching error; the remaining flags are two simple rows in the ≤ 15 % bin and small-bin family winners. *Open:* how the flag is reported (options in the follow-up question).
3. **Pools and 05b start.** Main 384, replication 319. *Chosen: 05b starts after you push and merge; it also waits for the point above.*
4. **05b runtime.** Stage 1 ≈ 23 h wall, stage 2 ≈ 80 h (arm 3: 44 h); ≈ 6 nights if the new models do not double the tuning cost. *Chosen: raise the queue to 10 workers (throughput gain unmeasured, so these hours may shrink); run each stage continuously or overnight when you schedule it.*
