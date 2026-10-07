# Handover: iteration 05b, Stage 2 (written 2026-10-07)

You take over iteration 05b ("Is training data what holds ML back?") on **machine A** (Alex's main PC, Windows; data, caches,
Stage 1 outputs and the saved models are here). **Start only after Alex has given the go for Stage 2 in the conversation.**
Your job: build and smoke-test Stage 2 (Arms 3-7), size it, hand Alex the scheduling command, and after the runs write the
final `results/iter05b_data_limit/REVIEW.md`. Then stop.

Read first, in this order: `CLAUDE.md` (contract; hard rules apply, rule 6 amended 2026-10-06), `iterations/05b-data-limit-test.md`
(brief: Arms 3-7 table, amendments A1-A11), `DECISIONS.md` (from 2026-10-01 on), `results/iter05b_data_limit/REVIEW_stage1.md`,
`results/iter05b_data_limit/HANDOVER_stage1.md` (practical history), this file.

## 1. Where things stand

- **Branch** `iter/05b-data-limit` @ `6b18100` (pushed). `main` = 05a merge (`2e6f229`); 05b is not merged.
- **Stage 1 is done.** Arms 1 + 2 merged in `stage1/arm{1,2}/` (big long files gzipped: gunzip before `iter05b_report.py`);
  report in `stage1/report/`; verdict **D (linear, CNN) + F** overall. ML family winners beat the best physics row
  (`paperA_corr`, 25.8 %) by 5.8-9.8 pp at n = all; at n = 62 they are within ~2 pp of physics.
- **REVIEW_stage1 decision 1 resolved (2026-10-07):** D + F accepted; the paper-lead change is deferred until Arms 7 and 6, so the final REVIEW must say whether they support it.
- **A10 (refit, persist, carry-forward)** - done:
  - 100 Arm 2 winners (20 seeds x 5 families) refit with their logged hyperparameters and saved in
    `stage1/models/s<seed>/<family>/` (git-ignored, 767 MB; manifest + SHA-256 each); reload check 100/100
    (`stage1/refit/reload_check.csv`).
  - **Carried families: linear, neural (= TabPFN, the winner in 20/20 seeds), raw-series (CNN)**; kernel and trees are not carried
    (`stage1/refit/carry_forward.md`, `carry_forward_models.csv`). Physics rows are always run.
  - Each seed's frozen configuration (spec `method|anchor|feature_set|mode|transform`, params, best_iter) is in
    `stage1/refit/refit_plan.csv`.
- **A11 (TabPFN and CNN on CPU)** - done: machine B (the only GPU) is away ~4 months; the CPU gate passed 40/40 (max |dWAPE|
  0.020 pp, `stage1/refit/reload_check_cpu.csv`). So **every Stage 2 job runs on machine A's CPU**; state it as the A11 deviation
  from A9 in the REVIEW.

## 2. What Stage 2 is (brief, Task 2 table, with A4 / A7 / A10 / A11)

Order: **Arm 7 -> Arm 4 -> Arm 3 -> Arm 5 -> Arm 6.** In Arms 3, 4, 6, 7 the carried families run with **each seed's frozen
Arm 2 configuration and hyperparameters, refit on the arm's own data (no hyperopt)** (A10); all physics rows (incl.
`paperA_corr_own`, A7) as in Stage 1.

| Arm | Pool / seeds | Content | Existing code path (smoke-tested in `configs/iter05b_quick.yaml`) |
|---|---|---|---|
| 7 filler uncertainty | GB main / 10 seeds (0-9), n = all | fillers' response x0.5 and x1.5; physics incl. `paperA_corr` (s0 from the scaled fillers) and `paperA_corr_s0unscaled`; carried families frozen; **plus a frozen-model row**: the saved step-1 model (trained at x1.0) applied to the scaled test substations. Report dWAPE vs x1.0 (= Arm 2, seeds 0-9) per bin | `pool.response_scale={fill: f}` (q_scale). The frozen-model row is **new code** |
| 4 oracles | GB main / 20 seeds; **B\* / 20 seeds physics only** | O1, O2, decomposition (fill contamination / scale dispersion / fit noise), dispersion floor; ML-on-O1 (carried families); B\*: O1a (fillers' response removed) and O1b (HP homes' own non-HP response removed), reported per bin | `oracle_rows=true`, `pool.oracle=O1` (q_oracle), `pool.response_scale={own: 0}` / `{fill: 0}` on `configs/pool_bstar.yaml` (q_bstar_o1b) |
| 3 households vs substations | GB main / 10 seeds x 1 draw | n in {62, all} x `substations_per_cell` train in {10, 40}; carried families frozen + physics; the S test (pre-registered: >= 1 pp median drop 10 -> 40, >= 80 % of seeds) | `grid.substations_per_cell`, learning-curve designs (`lc_only`, `learning_curve.specs` accepts `m|a|f|mode|tt` strings) |
| 5 B\* under v1.1 | B\* / 20 seeds | physics + carried families **with per-arm tuning** (A10); p = 0.8 in the grid; the neural family here means FFNN (full budget: 50 evals, patience 20) **and** TabPFN (the brief's FFNN fair test) | `configs/pool_bstar.yaml` + v1.1 grid |
| 6 temporal replication | GB Oct 2022 - 28 Sep 2023 (`configs/pool_gb_eoh_2223.yaml`, 319 homes) / 10 seeds, n = all | physics + carried families frozen | pool config exists |

**Frozen-configuration mechanism (exists, needs queue wiring):** `run_benchmark` accepts `cfg.refit = {fixed: {"<spec>": {params,
best_iter}}}` (no `dir`, so nothing is persisted): `tune_grouped_cv(fixed=...)` skips the search and inner CV and refits on the
arm's train substations; the main-target loop then runs only those specs (physics stays in the separate `physics` queue job).
**Missing:** `run_queue.job_config` must inject each job's per-seed `refit.fixed` from `refit_plan.csv` for the carried families
(and set `learning_curve.specs` to the frozen spec for the Arm 3 n = 62 designs). Rows have no `wape_inner` in frozen mode; that
is expected (no selection happens in Stage 2).

**Decisions to raise with Alex before coding (do not decide alone):**
1. **ML-on-O1 (Arm 4).** The brief says "netfit features of the HP aggregate + size"; the frozen Arm 2 winners mostly use
   `both` features and/or `size_peak`, and the CNN uses `raw`. Options: (a) frozen spec as is, on the O1 pool (recommended:
   it is what A10 says; feature computation on the O1 series works for every set); (b) the brief's netfit x size, which needs
   tuning (no frozen params exist for it).
2. **Seeds 10-19 in Arms 4 / 5:** frozen configs exist for all 20 Arm 2 seeds, so no gap; confirm Arm 7 / 3 / 6 use seeds 0-9.

## 3. Steps

1. Wire the frozen configs into the queue (above), new configs `configs/iter05b_arm{3,4,5,6,7}.yaml` and a queue config
   `configs/iter05b_stage2.yaml` (families: physics, linear, neural = TabPFN only in frozen arms, rawseries; device cpu).
   Add the Arm 7 frozen-model row. Tests: frozen spec reproduces Stage 1 predictions on Arm 2 data (seed 0, one model per carried
   family, within the A10 tolerances); queue injects the right spec per seed; frozen-model row uses the saved model unchanged.
   Keep the logic diff near ~300 lines; if bigger, stop and propose a split (rule 5). Commit; ask Alex before pushing (rule 6).
2. Add the Stage 2 arms to `configs/iter05b_quick.yaml` (or a `iter05b_quick_stage2.yaml`) and run quick interactively (< ~5 min).
3. **Probe:** one seed per arm at full size through the queue; measure job hours from the `.done` markers
   (`scripts/paperb/wall_times.py --config ...`) and the `*.timing.parquet` frames; estimate the full Stage 2 wall time at
   <= 6 workers. If > ~3 nights, report and propose a reduction; Alex decides (rule 7).
4. Print the scheduling command for Alex (`scripts\schedule_overnight.ps1 -Config configs\iter05b_stage2.yaml -Continuous
   -Workers 6`); never register a task yourself.
5. After the runs: `check_jobs.py` OK, merge with one `run_queue.py` call, extend the report (Task 3 tables 5-8: Arm 3 table,
   error-decomposition figure, headline tables, verdict table incl. S), and write the final `REVIEW.md` (CLAUDE.md s.9). Its
   decisions must cover the brief's four (verdict incl. S; dominant error component and the paper lead; GB-EoH as headline pool
   for 06/07 or not; simulator go/no-go) plus: does `paperA_corr_own` close the gap to the label-calibrated rows on B\*? Quote
   Arm 7's sensitivity and the 05a D5 deltas next to GB-EoH headline numbers; mark the filler-variability-limited bins (†).

## 4. Practical notes (machine A)

- **Workers:** at most 6; RAM stays below ~85 %. With 6 workers, Arm 2 tree jobs took 11-12 h and FFNN jobs 2.5-3.8 h
  (probe: 3.9 / 1.1 h). The 2026-10-05 19:08 stop was the queue's console closing during a desktop hang.
- **Detached runs:** a long job started from the agent's shell must be launched via WMI (`Invoke-CimMethod Win32_Process
  Create` with `Win32_ProcessStartup` PriorityClass 16384 = below normal); `Start-Process` children and `cmd start /b` did not
  survive or hung. Prefer Alex's scheduled task for long runs.
- **OneDrive:** files synced from another machine can be cloud-only placeholders (attribute 0x400000); reads then fail with
  OSError 22 / "cloud operation timed out". Check before merging; Alex sets the folder to "Always keep on this device".
  `importlib.metadata` can fail the same way (persist.py uses `__version__`). On 2026-10-06 Windows TLS hung (OneDrive, browser,
  git push); a reboot fixed it.
- **Windows DLL order:** import torch before pandas / pyarrow in any new entry point (WinError 1114 otherwise).
- **TabPFN on CPU:** set threads (`configure(xgb_n_jobs=...)`); with 1 thread it is very slow. Checkpoint via
  `TABPFN_MODEL_CACHE_DIR`; never print or commit tokens; never download weights.
- **Git:** push only when Alex asks (rule 6), via `git push https://github.com/agouveia-kul/hp-capacity-detection.git
  iter/05b-data-limit` (SSH fails). The working tree has older uncommitted changes under `results/iter05a_pool/overnight/` and
  `results/iter05b_data_limit/quick/` and an untracked `AGENTS.md`: not yours, leave them out of commits. `jobs_cpu_archive/Get-Date`
  is a stray probe marker; leave it.
- **Tools:** `run_queue.py` (`--families`, `--shard`, `--retry-failed`, `--arms`), `check_jobs.py`, `wall_times.py`,
  `refit_persist.py` (`plan | refit | check [--device --out --resume] | carry`), `iter05b_report.py`, `runtime_estimate.py`.
- **Tests:** `.venv\Scripts\python -m pytest` (all pass on 2026-10-06/07; the CUDA test is skipped on machine A; ~10 min).
