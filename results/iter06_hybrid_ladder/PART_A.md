# Iteration 06, Part A — code, quick run, probe, runtime (2026-10-12)

Not the iteration's REVIEW (that follows Part B). This note records what Part A did, what it assumed and what the final REVIEW
must carry. **No full-size test metric was read in Part A**: only timings, inner-CV WAPE (the selection statistic) and
diagnostics on train and inner substations.

## State
- Branch `iter/06-hybrid-ladder`, not pushed. Task 0 `c68dfbc`; code (Tasks 1–4) `66d6639`; probe, quick run and this note in the
  commit that adds this file.
- Logic added or changed: 334 lines (budget ~400): `scale_model.py` (new, 86), `ensemble.py` (new, 71),
  `run_benchmark.py` (48), `run_queue.py` (34), `runtime_estimate.py` (31), `persist.py` (21), `train.py` (17),
  `models_rawseries.py` (9), `physics.py` (8), `check_jobs.py` (8), `substations.py` (1). Tests: `tests/test_06.py`
  (20 tests). Configs: `iter06.yaml`, `iter06_probe.yaml`, `iter06_quick.yaml`, `iter06_{a_gb,a_ch,r_shift,r_rep}.yaml`.
- pytest on the final code (`pytest.log`): 153 passed, 1 skipped (CUDA), 1 xfailed (the documented CNN CPU-vs-GPU case).
- Quick run (`configs/iter06_quick.yaml`, every arm, seed 0, tiny grid): 28/28 jobs, 0 failed, 5.5 min. The first quick run
  found one bug (the anchor-only baselines reached the model persistence), fixed and tested.
- Probe (`configs/iter06_probe.yaml`: seed 0 of every arm, draw 0, full size, 6 workers × 3 threads; 40 of its jobs remain
  on disk after cut 2 removed the 24 S-GB ones): 64/64 jobs, 0 failed,
  30.1 job-h in 6.2 h. The job ids are those of the run, which skips them. The merged seed-0 tables (`<arm>/metrics.csv`
  and the like) are on disk but not committed and were not opened; the run rewrites them.
- Reload check of the persisted seed-0 rung winners (`check_jobs.py --reload-models`; `models/` is git-ignored): 24 of 24
  models (2 arms × 4 rungs × 3 families) reproduce their own test predictions in a fresh process: linear and CNN exactly,
  TabPFN within 1.6e-5 relative (0.00015 pp of WAPE). Models of seed 0: 52 MB (about 0.5 GB for the run).
- L5 step on A-GB seed 0 (`ensemble.py`): runs; the gate keeps no edge (weights linear 0.08, TabPFN 0.71, CNN 0.25 on the
  out-of-fold predictions).

## Review decisions of 2026-10-12 (DECISIONS.md, brief amendments A3-A8 and B1-B4; commit `7b723e5`, then the commit adding this section)
- **B1, CNN best of 3 initialisations** (seeds seed + k * 7919; k = 0 is the split seed). In every fold fit of a fixed-params pass
  the kept one has the lowest loss on the early-stopping fold (household-disjoint from the fitted and the scored fold). In every
  final fit it has the lowest loss on the inner substations. **Deviation from the wording of B1:** a final fit uses every train
  household, so no household-disjoint substation exists for it outside test; the inner substations are never fitted by the final
  model and never test, but share households with the train substations. The choice screens out a collapsed initialisation; it
  is not an unbiased loss. A B\* search evaluation trains one initialisation. Validation losses and per-initialisation test WAPE
  are metrics `init<k>_val_loss` / `init<k>_test_wape` (diagnostics; the report lists their spread). In the re-probe (24 final
  fits) the chosen initialisation was 0, 1, 2 in 8 fits each; worst / best validation loss: median 1.09, max 1.52.
- **B2.** `timeout_s` per family = 3 x its longest probe job: physics 1,758 s, linear 13,968, tabpfn_d 32,961, tabpfn_r 19,455,
  tabpfn_h 36,666, cnn_d 27,399, cnn_r 13,524, cnn_h 26,343. The job's main thread is interrupted at its next Python instruction,
  the job is failed with `reason: timeout` and rerun by `--retry-failed`; other jobs are not touched. Limit: a job blocked inside
  one native call is interrupted only when that call returns. The queue refuses to start above the physical cores. A read-only
  check found the 05b feature caches for all ten seeds of a_gb, a_ch, r_x05, r_x15 and r_rep, so no physics job starts cold there.
- **C7.** In r_x05 / r_x15 every L4 model also gets `<model>@update` (frozen residual and scale model, s0 from the scaled train
  fillers). `paperA_corr` (scaled s0) and `paperA_corr_s0unscaled` were already both in the R-shift physics job.
- **Report script** `scripts/paperb/iter06_report.py`, committed in `7b723e5` before any result: open choices in its docstring
  (R = better on at least two of its three readings and worse on none; hybrid and best pure data-driven model chosen by the
  median inner-CV WAPE over the seeds on A-GB; L5 judged on all test substations or on the union of the † bins; S second reading
  = CH at n = all on the S configurations; n = all of S placed at the seed's number of train HP households). Tested on a
  fabricated result tree and run on the quick (toy) outputs only.
- **Probe jobs.** B1 and C7 change the content of 19 of the 40 seed-0 jobs, not only the GB CNN ones: every CNN job (a_gb, a_ch,
  r_x05, r_x15, r_rep: 15) and the L4-holding linear and tabpfn_h jobs of r_x05 and r_x15 (4). These 19 were removed; the other
  21 are unchanged. Re-probed at 6 workers x 3 threads: a_gb, a_ch and r_x05 CNN (9 jobs, 0 failed); the remaining 10 run with
  the run. 30 of 880 jobs are done.
- **Runtime after B1** (job-h per seed, re-probe): A-GB CNN 6.23 (was 2.00: cnn_d 2.54, cnn_r 1.25, cnn_h 2.44); A-CH CNN 3.66
  (unchanged: the search dominates); r_x05 CNN 0.85 (was 0.48). Estimate of what remains: A-GB 118 job-h, A-CH 50, S-GB 84
  (CNN x 3 extrapolated; about 40 is per-job overhead), R arms 49: **about 300 job-h, TabPFN about 124, wall time about 50 h
  = 2.1 continuous days** at 6 workers (below the 4-day limit). TabPFN and S-GB are extrapolated from the first probe and the
  timing check (cuts 1 and 2), not re-probed.

- **Checks on the final code:** quick run 28/28 jobs; pytest 163 passed, 1 skipped (CUDA), 1 xfailed (documented); reload check
  of the persisted seed-0 rung winners after the re-probe: 24 of 24 reproduce their own predictions (linear and CNN exactly,
  TabPFN within 1.7e-5 relative). The run was **not** started and no task was registered.
- **Command** (continuous, below-normal priority, 6 workers x 3 threads from the queue config; OneDrive sync paused for the run):
  `powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter06.yaml -Continuous -Workers 6`

## Compute decisions after the probe (Alex, 2026-10-12; DECISIONS.md, brief amendments A1 and A2; commit after `60a11b8`)
- **Cut 1:** TabPFN does not predict its train substations (`no_train_wape: [TabPFN]` in the arm configs). Timed on the
  persisted A-GB seed-0 L2 and L1 models (3 threads, idle machine): test prediction 197–202 s, train prediction 323–357 s,
  four CV folds 411–591 s, fit 2–4 s; the train prediction is 31–34 % of the total. Only `wape_train` is lost (NaN from seed 1
  on; seed 0's probe jobs still carry it). A TabPFN process peaked at 5.9–6.6 GB, so the cap of 3 jobs stays.
- **Cut 2:** S-GB on anchor `size` and one feature set per rung (`configs/iter06_s_gb.yaml`): 5 configurations per model
  (L1, L2, L3, L4 × 2) instead of 18 (CNN 10). The n = all point is A-GB restricted to the same configurations. The 24 S-GB
  probe jobs held the full grid: they were removed (markers, frames, merged tables) and the run recomputes them, so every
  S-GB job has the same content. Stated cost: on S the L2-vs-L1 step compares `netfit` with `whdd`, not the best of
  {`netfit`, `both`}.
- **Estimate after the cuts** (extrapolated from the probe and the timing check, not re-probed): about 230 job-h remaining
  (A-GB 80, A-CH 50, S-GB 64 of which about 40 is per-job overhead, R arms 38), TabPFN about 110; wall time about 39 h at
  6 workers = 1.6 continuous days or about 4 nights. The table below is the probe's estimate before the cuts.
- After the cuts: quick run 28/28 jobs, 0 failed (S-GB runs the restricted grid; TabPFN's `wape_train` is NaN, its inner-CV
  WAPE is there); pytest 157 passed, 1 skipped (CUDA), 1 xfailed (documented). The run was **not** started.
- **OneDrive incident (2026-10-12, 12:20).** Deleting the 24 S-GB probe jobs and the quick folder and rerunning the quick run
  at once made OneDrive restore the deleted files and write conflict copies (`*-P240003.*`) in `quick/jobs`, so that quick
  run merged old and new frames. Everything was deleted again, left for 5 min (nothing came back), and the quick run was
  repeated in the clean folder: no conflict copy, 40 probe jobs and the models untouched. Lesson: never delete and recreate
  a results folder in one step under OneDrive; pause the sync for the run, as `schedule_overnight.ps1` advises.
- Decided in the review of 2026-10-12: the CNN's inherited hyperparameters on the GB arms (A3), and continuous mode.

## Runtime before the cuts (`runtime_estimate.md`, from the probe)
| arm | physics | linear | TabPFN | CNN | all (job-h, 10 seeds) |
|---|---|---|---|---|---|
| a_gb | 0.2 | 12.9 | 82.5 | 20.1 | 115.7 |
| a_ch | 0.2 | 3.2 | 22.4 | 36.6 | 62.3 |
| s_gb | 3.9 | 17.8 | 118.3 | 20.9 | 160.8 |
| r_x05 + r_x15 + r_rep | 2.9 | 2.5 | 22.2 | 14.7 | 42.1 |

Whole run 381 job-h; 351 job-h remain after the probe, of which TabPFN 227. TabPFN runs at most 3 jobs at once, which sets
the wall time: **76 h = 3.1 continuous days, or 8.0 nights of 9.5 h** at 6 workers. This is above the ~3 nights of hard
rule 7, so the mode is Alex's choice. Nothing was scheduled.

```
powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter06.yaml -StartAt 22:00 -Continuous -Workers 6
```
Nights only: replace `-Continuous` by `-StopAt 07:30` (about 8 nights). Threads per worker (3) come from the queue config.

Ways to shorten it, none applied:
- TabPFN cap 4 instead of 3 (`max_concurrent` of the three TabPFN families): about 59 h, if the RAM allows it (not measured;
  6.8 GB were free during the probe with 3 TabPFN jobs).
- S-GB with one draw per n instead of two: −80 job-h, about 56 h. It changes the pre-registered axis S (10 seeds × 2 draws).
- Reusing 05b Stage 1's L2 / L3 rows for linear and TabPFN on A-GB (the brief allows it): about −35 job-h, but those rungs
  would have no persisted model or out-of-fold predictions unless refit, and it needs new code.

## Assumptions and deviations (for the REVIEW)
- **CNN hyperparameters on the GB arms (deviation; accepted by Alex on 2026-10-12, amendment A3).** `fixed_params` in `configs/iter06.yaml`: on `a_gb`
  and `s_gb` every CNN configuration takes the hyperparameters of the seed's 05b Arm 2 CNN winner (A10 carry-forward table);
  one inner-CV pass per configuration gives its inner-CV WAPE, the epoch count and the out-of-fold predictions. Reasons: A11
  puts the CNN on this CPU; one such pass plus the final fit took 11–17 min per configuration at n = all; 30 evaluations would
  cost roughly 20 times that, i.e. about 400 to 900 more job-hours for A-GB and S-GB (3 to 6 more days), assuming an
  evaluation costs what the winner's hyperparameters cost. Bias to state: the hyperparameters were tuned in 05b on the raw
  input (the ladder's L1, or its residual form), and at n = all, so they favour L1 over L2–L4 and n = all over small n.
  Removing the `fixed_params` line restores per-configuration tuning. On B\* (`a_ch`) the CNN is tuned (30 evals; 05b
  persisted no B\* CNN); it took 3.7 job-h for seed 0.
- **L1 and L2 anchors.** L1 = `whdd` × {size, size_peak} (CNN: `raw` × the same), so that L1 and L2 differ in the feature
  type only. The brief's "scale features (N, observed peak)" was read this way.
- **CNN L2 = feature set `rawphys`** (the brief's option `physics_scalars: true`): the net-load fit's s_h, P_base and T_h
  (per dwelling for the kW columns) joined after pooling next to the anchors. ŝ here is the net-load slope, not the
  corrected one, as in `netfit`. CNN L3 and L4 use `rawphys`; 05b's `raw` + residual CNN is not a ladder configuration.
- **L3** is exactly 05b's residual (cross-fitted `paperA_sh_mh`).
- **L4 scale.** L4a: κ = m_h(pilot) · (T_h(pilot) − T_design); per substation m̂_h = κ / (T̂_h(net) − T_design); cross-fitted
  through the 03b pilots (now also their T_h). L4b: Ridge of log m_h on (T̂_h, T_design, r̂, mean and 5th percentile of the
  station's daily temperature), α from 10⁻² to 10⁵ by leave-one-fold-out over the inner substations; cross-fitted (inner rows:
  the other folds; train rows: the train rows sharing no HP household). T_design is one value per pool, so it has no effect
  within a pool. The first α grid stopped at 100 and inner CV sat at that bound in seed 0 of both pools; it was widened and
  the probe restarted (`probe_log_aborted_alpha_grid.txt`), before any test metric was read.
- **Own-load term.** `paperA_corr_own`'s m_h′ is a constant factor on m̂_h, which the residual's intercept absorbs; it is not a
  separate L4 component. `paperA_corr_own` stays an L0 row.
- **Zero-residual rows** `paperA_l4a` / `paperA_l4b` (ŝ / m̂_h) are reported with the physics rows; they are not L0 candidates.
- **L5b details not in the brief:** the gate takes the fewest edges whose grouped-CV error is within 1 % (relative) of the
  best; a bin needs ≥ 20 inner rows in every fit; weights by bounded least squares (scipy's `nnls` fails on proportional
  columns). L5 is a post-processing step (`ensemble.py`) on A-GB and A-CH, not a queue arm.
- **R-shift, frozen L4:** the saved model keeps its ×1.0 scale model and s₀ (the unscaled fillers'). The frozen physics
  reference is `paperA_corr_s0unscaled`; `slope_base` has no frozen row (its map was not persisted).
- **Persistence:** per arm, rung, seed and family, the inner-CV winner (first on ties), in the A10 format plus
  `oof_inner.parquet` and, for L4, `scale.joblib`; A-GB and A-CH only (S-GB and the R arms persist nothing).
- **whdd on GB** keeps `resolution: 15` and T_base 12 °C, as in 05b's `both` (so the 05b feature caches are reused). On a
  30-min series each value is repeated; against `resolution: 30` the median feature is identical and the largest
  difference is 2.4 % (a quantile difference). The UK degree-day base (15.5 °C) is not used.
- **Queue:** TabPFN and the CNN are split into three queue families each (direct = L1 + L2, residual = L3, l4a + l4b = L4);
  `after: a_gb` holds an R job until A-GB's job of that seed and family is done; 6 workers × 3 threads (20 physical cores).
  No per-job timeout yet.
- The arm `config.yaml` files of the probe record commit `c68dfbc` (the code was committed as `66d6639` while it ran, unchanged).

## Problems found and early signals (train and inner rows, seed 0)
- **L4's residual target is noisy at low penetration.** GB, ≤ 15 % bin: z = log y − log(ŝ / m̂_h) has sd 0.82 (L3's z: 0.37),
  a right tail to +4.8, and 8.9 % of the rows have ŝ ≤ 0 (predicted 0). B\*: sd 0.70 against 0.46, 1.5 % invalid. The
  corrected slope removes L3's bias (median z ≈ 0 against −1.0) but is not identified where the fillers dominate. From 35 %
  up the two targets are alike. The method was left as pre-registered.
- **Inner-CV WAPE of the rung winners, seed 0** (selection statistic, not test). GB: linear L1 25.2, L2 22.4, L3 20.7,
  L4 27.0; TabPFN 18.9, 16.8, 17.7, 18.6; CNN 19.2, 18.8, 18.5, 22.3. B\*: linear 28.8, 26.0, 27.0, 28.9; TabPFN 27.7, 21.9,
  22.6, 22.6; CNN 25.4, 25.7, 26.5, 26.7. In inner CV, L4 does not improve on L3 in any family.
- **The learned scale does not beat the pilot constant within a pool.** Error of log m̂_h on train and inner rows
  (cross-fitted, sd): GB L4a 0.236, L4b 0.231, constant pilot 0.227; B\* 0.252, 0.271, 0.240. L4b's α lands at 10⁴–10⁵
  (close to a constant) in 7 of 8 designs. The aggregate covariates carry almost nothing about m_h inside one pool; any
  value of the learned scale would have to show in transfer (07).
- The quick grid (3 train substations per cell) makes L4 blow up (TabPFN above 300 % WAPE): a toy-size artefact of the
  heavy-tailed target, not seen at full size in inner CV.
- 05b's slow CNN was largely the thread oversubscription: tuned on B\* (30 evals) with 3 threads per worker, a residual CNN
  configuration took about 8 min here against 47 min in 05b Arm 5, a direct one 27 min against 90.

## Part B, after the run
1. `python scripts/paperb/check_jobs.py --config configs/iter06.yaml` (0 remaining, failures listed).
2. `python scripts/paperb/check_jobs.py --reload-models results/iter06_hybrid_ladder/models/a_gb` and `.../a_ch`.
3. `python scripts/paperb/ensemble.py --arm results/iter06_hybrid_ladder/a_gb --models results/iter06_hybrid_ladder/models/a_gb`
   (and `a_ch`): L5a / L5b test predictions and the gates.
4. The report script (ladder, step, claim and L5 tables; figures) is still to be written, and committed before the results
   are read. The n = all point of S-GB is A-GB. GB rows quote the 05a D5 deltas and the 05b Arm 7 sensitivity.
