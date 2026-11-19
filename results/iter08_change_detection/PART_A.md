# Iteration 08, Part A — code, quick run, probe, runtime (2026-11-18)

Not the iteration's REVIEW (that follows Part B). **No detection or error metric of 08 was computed or opened in Part A**: the
quick run and the probe were read for runtime and validity counts only (`diag`, `timing`, job markers). The probe's
`preds` frames are on disk and were not opened.

## State
- Branch `iter/08-change-detection` from `main` cd42638 (the 07 close-out is in `main`; 07b-i finished on its own branch and
  no other agent was running). Task 0 `f35464a` (brief, DECISIONS pre-registration: six lines, CLAUDE.md §4 paragraph,
  `method_basis.md`); Tasks 1–3 in the commit that adds this file.
- Logic added: `change_feeders.py` (new, 77 lines), `change_eval.py` (new, 83), `run_queue.py` (1: frame `feeders`).
  Tests `tests/test_08.py` (10 tests). Configs `iter08{,_change,_quick,_probe}.yaml`.
- pytest (`pytest.log`): 183 passed, 5 skipped (the 2 slow 08 tests, CUDA, others), 1 xfailed (the documented CNN case).
  Slow 08 tests with `PAPERB_SLOW=1` (`pytest_slow.log`, 38 min): 2 passed. E1 on the 06 test substations reproduces the 06
  predictions within 0.001 pp of WAPE (seeds 0 and 3, anchors size and size_peak); permuting the households' `HP_Peak` in both
  pool tables leaves P̂₁ and Δ̂ bit-identical for E1, E4 (and, in the default suite, E2, E3).

## Envelope (Task 1; memberships only, no estimator)
- **Households** (`envelope/households.csv`): of the 92 test HP homes per seed, **58–72** are eligible in both years (seed 0: 63);
  halves of 28–38 HP homes and 400 test fillers each. Train fillers for s₀: 2,399.
- **Only 3 weather groups per half reach H ≥ 3**, with half pools of 3–14 homes (seed 0: 4/5/13 and 4/6/12); every other group
  is dropped (`station pool < min_station_pool`, 900 cells in seed 0). The binding rule is k₁ + Δk ≤ 0.75 H (281 cells in seed 0).
- **Feeders:** 350–480 per seed (4,130 over 10 seeds; `envelope/feeders_per_cell.csv`). Feasible cells (min–max feeders over
  seeds, both halves):

  | N | p₁ | Δp = 0 | 0.05 | 0.1 | 0.2 |
  |---|---|---|---|---|---|
  | 20 | 0.05 | 30 | 30 | 20–30 | 10–20 |
  | 20 | 0.1 | 30 | 20–30 | 10–20 | 10–20 |
  | 20 | 0.2 | 10–20 | 10–20 | 10–20 | 0–10 |
  | 20 | 0.3 | 10–20 | 10 | 0–10 | 0–5 |
  | 20 | 0.5 | 0–5 | — | — | — |
  | 40 | 0.05 | 30 | 10–20 | 10–20 | 0–5 |
  | 40 | 0.1 | 10–20 | 10–20 | 0–10 | — |
  | 40 | 0.2 | 0–10 | 0–5 | — | — |
  | 80 | 0.05 | 10–20 | 0–10 | — | — |
  | 80 | 0.1 | 0–10 | — | — | — |

  - Rule D (Δp = 0.1) pools **4–6 feasible (N, p₁) cells per seed**: (20; 0.05, 0.1, 0.2) in every seed, (20, 0.3) in 9,
    (40, 0.05) in 10, (40, 0.1) in 9. **N = 80 has no Δp = 0.1 cell; p₁ = 0.5 (Paper A bin 35–65 %) has no uptake cell.**
    Only the ≤ 15 % and 15–35 % bins of p₁ are populated.
  - Null feeders for τ (both halves; a half has about half): N = 20 80–100, N = 40 50–60, N = 80 20–30. With 10–15 null
    feeders per half at N = 80, the 95th percentile is close to the half's maximum.
- Validity (probe, seed 0, 395 feeders): no NaN prediction, no failed net-load fit in either year. **E2's corrected base is invalid
  (ŝ − N s₀ ≤ 0, P̂ = 0) in 51 year-1 and 21 year-2 feeders** (12.9 % vs 5.3 %; `diag` gives counts per year, not per cell;
  in the quick run, whose cells are all N = 20 with p₁ ≤ 0.1, 9 and 2 of 42).
  E1, E3, E4: 0 invalid. Local s₀ (kW/K per dwelling): year 1 G001 0.01264, G002 0.01278, G009 0.01305 (= 06's `s0map`);
  year 2 G001 0.01233, G002 0.01236, G003 0.01271.

## Rules written in Part A (not in the brief; for Alex to confirm or change before the run)
1. **New HP homes come from the feeder's own weather group** (same half, not already in the feeder). The brief says "drawn
   from the same half"; the 06 generator rule says all HP members of a substation are from one station, whose temperature is
   the feeder's T. Both are applied. A new home from another group would respond to a temperature the feeder is not fitted on.
2. **The 06 rules apply to the year-2 feeder** (the larger one): the group's half pool H ≥ 3 (`min_station_pool`),
   k₁ + Δk ≤ 0.75 H (`max_overlap`), N ≤ the half's fillers. `feeders_per_cell` = 5, the 06 test value. Cells are independent:
   the null cell (Δp = 0) and each uptake cell of the same (group, N, p₁) are separate draws.
3. **Eligible in both years** = in both pool tables (2122r3 and 2223r3): ≥ 90 % valid 30-min bins in each window, and not
   excluded by the silent-electricity rule. The 06 test HP households are the split's test homes (92 per seed), not only the
   81 that sat in 06 test substations.
4. **Halves:** HP homes alternate within their main-year weather group from a random start (as `grouped_inner_folds`, k = 2);
   fillers alternate over a random permutation (stream [s, 7]); feeders stream [s, 8, half, crc32(cell)].
5. **Year-2 weather group:** the main-year group's homes map one-to-one onto one year-2 group (asserted per feeder). The group
   labels differ between the two pool tables (they are numbered per build), so the mapping goes through the homes.
6. **Local s₀ of E2:** per weather group and year, `AnalogFill.s0` of the seed's 2,399 train fillers under that year's analog
   map (the 06 machinery). Year 1 reproduces 06's `s0map` exactly (test). The pilot m_h is 06's year-1 train pilot (pilots.csv,
   pilot `all`) for both years.
7. **Invalid Paper A bases** (ŝ ≤ 0 after the s₀ correction, or a failed net-load fit) give P̂ = 0, Paper A's convention, so
   Δ̂ = P̂₂ − P̂₁ is defined for every feeder; the counts per year are in `diag`.
8. **τ** = the 0.95 quantile of Δ̂ (numpy linear interpolation) over the calibration half's null feeders of the same seed,
   estimator and N, pooled over weather groups and p₁. A feeder of evaluation half h is flagged against the τ of half 1 − h.

## Quick run, probe, runtime (Task 3)
- **Quick** (`configs/iter08_quick.yaml`: seed 0, N 20, p₁ {0.05, 0.1}, Δp {0, 0.1}, 2 feeders per cell; `quick_log.txt`):
  2/2 jobs, 0 failed; 42 feeders; physics 15 s, TabPFN 651 s. The quick run takes 11 min, over the ~5 min of hard rule 7:
  each TabPFN load refits its 2,080-row context (four loads per job, ~160 s each), whatever the number of feeders.
- **Probe** (`configs/iter08_probe.yaml`: the run's seed-0 jobs, same job ids, 2 workers × 4 threads; `probe_log.txt`):
  2/2 jobs, 0 failed; physics 84 s (feature evaluation 0.09–0.11 s per feeder-year), TabPFN 720 s. The run skips both jobs.
  The merged seed-0 tables in `change/` were opened for `physics_diagnostics.csv`, `pilots.csv` and `dropped_cells.csv` only;
  `predictions.csv` was not opened.
- **Estimate:** 18 jobs remain (9 seeds × 2 families): physics ≈ 9 × 85 s, TabPFN ≈ 9 × 720 s, one TabPFN job at a time
  (a TabPFN process peaked at ~6 GB in 06; 11.5 GB were free here with nothing running) → **about 2 h wall** at 2 workers × 4
  threads (`configs/iter08.yaml`). Timeouts = max(3 × probe job, 1,800 s): physics 1,800 s, TabPFN 2,160 s, hard watchdog on.
- **Command** (continuous, below-normal priority; Alex runs it; no task was registered):
  `powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter08.yaml -StartAt 22:00 -Continuous -Workers 2`
  Or, on Alex's request, detached now: `results\iter08_change_detection\launch_detached.cmd configs\iter08.yaml` (log `log.txt`).
- **Part B, after the run:** `check_jobs.py --config configs/iter08.yaml`; write and commit `scripts/paperb/iter08_report.py`
  (it uses `change_eval.thresholds` / `flags`) **before** any prediction is read; then the tables, figures and REVIEW.md.

## Decisions for Alex before the run
1. **Envelope and feeders per cell.** The design runs, but its envelope is narrow (above): N = 80 and p₁ = 0.5 carry no uptake
   cell, rule D pools 4–6 cells at N ≤ 40, and τ at N = 80 rests on 10–15 null feeders per half. Options: (a) run as is and
   report the envelope; (b) 20 feeders per cell instead of 5 (06's test value), which steadies τ and the power estimates but
   adds no household (the draws of a cell reuse its group's 3–14 homes; seeds stay the independent replication); (c) relax
   `max_overlap` to 1.0 for 08, which opens p₁ 0.3–0.5 at N = 20 with feeders that share nearly all their HP homes.
   *Recommended:* (b), with `max_overlap` unchanged; the probe is rerun (≈ 15 min) before the run.
2. **New HP homes from the feeder's own weather group** (Part A rule 1). *Recommended:* confirm; the alternative (any group of
   the half) mixes temperature series within one feeder, which no 06 substation does.
3. **E2's invalid bases differ between years** (12.9 % year 1, 5.3 % year 2 in the probe). Under the pre-registered
   convention (P̂ = 0) such a feeder's Δ̂ is P̂₂ − 0 or 0 − P̂₁. *Recommended:* keep the convention for rules D and Q, report
   the invalid share per cell and year, and add now, before any result, one secondary row outside the rules: E2 on the
   feeders whose base is valid in both years.

- **OneDrive:** pause the sync for the run and resume it only after the run and the Part B merge are finished. Never delete and
  recreate a results folder under OneDrive in one step (06 incident). A reboot resumes the sync: re-pause it.
