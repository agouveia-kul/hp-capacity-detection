# Handover: iteration 05b, end of Stage 1 (2026-10-05)

You take over iteration 05b ("Is training data what holds ML back?") on **machine A** (Alex's main PC, Windows, the data and the queue live here). Your task: finish Stage 1, produce the Stage 1 report and write `results/iter05b_data_limit/REVIEW_stage1.md`, then **stop and wait for Alex's go** before Stage 2.

Read first, in this order: `CLAUDE.md` (the contract; hard rules apply), `iterations/05b-data-limit-test.md` (the brief, amendments A1–A7 inside), `DECISIONS.md` (A8 and A9 at the end), this file.

## 1. Where things stand

- **Branch:** `iter/05b-data-limit`. Commit and push only there; never merge. The paper is drafted by a separate agent on `paper/draft`; do not touch it.
- **Stage 1** = Arm 1 (learning curve, 700 jobs) + Arm 2 (headline, 140 jobs) = 840 queue jobs, one per (arm, seed, n, draw, family). Outputs in `results/iter05b_data_limit/stage1/` (`jobs/` holds one `.done` marker + parquet frames per job).
- **Families and devices (A8, A9):**
  - CatBoost and GP are not run (A8).
  - The raw-series CNN and TabPFN ran **entirely on the GPU of machine B** (RTX 5060 Ti, host `DESKTOP-MU8L2HT`): all 240 jobs done, copied into machine A's `jobs/`, checked OK.
  - Their earlier CPU outputs are in `stage1/jobs_cpu_archive/`: kept, **never reported**.
  - All other families run on machine A's CPU.
- **On 2026-10-05 the queue on machine A was still running** the last CPU jobs of Arm 2: trees 13/20, kernel 1/20, neural 1/20 done (45 left, estimate 12–17 h). It runs as the scheduled task `paperb-iter05b_stage1` (6 workers, `--families physics,linear,trees,kernel,neural`, `-Continuous`). Do not restart it while jobs run: a restart loses the running jobs.
- **Expected, not a problem:** in Arm 1, 33 learning-curve designs (n = 16 / 32) have no ML results in every ML family, because grouped inner CV is infeasible there (too few HP households for 4 folds). The physics job of each design records the reason. The same happened in 03b. Report it.
- **Device and host** are recorded in each `.done` from commit `a64e65f` on; earlier CPU jobs show `cpu (not recorded)` and host `?`.

## 2. Steps

1. **Wait for the queue to finish.** Check with
   `.venv\Scripts\python scripts\paperb\check_jobs.py --config configs\iter05b_stage1.yaml --families physics,linear,trees,kernel,neural`
   and
   `.venv\Scripts\python scripts\paperb\check_jobs.py --config configs\iter05b_stage1_gpu.yaml --families rawseries,tabpfn --expect-device rawseries=cuda,tabpfn=cuda`.
   Both must end with `OK:`.
   - If jobs failed: read `stage1\STATUS.md`. If a worker died, rerun the failed jobs with `.venv\Scripts\python scripts\paperb\run_queue.py --config configs\iter05b_stage1.yaml --families physics,linear,trees,kernel,neural --retry-failed --workers 6`.
   - Failed CNN / TabPFN jobs must be rerun on machine B with the GPU config, never on this CPU.
2. **Merge:** `.venv\Scripts\python scripts\paperb\run_queue.py --config configs\iter05b_stage1.yaml`. It finds nothing to run and writes `stage1\arm1\metrics_lc.csv`, `stage1\arm2\metrics.csv` and the other merged CSVs.
3. **Report:** `.venv\Scripts\python scripts\paperb\iter05b_report.py`.
   - It writes `stage1\report\stage1_report.md`, `verdict.csv`, `lc_paired.csv` and `fig_learning_curve.png/pdf`.
   - The script was committed before any result was read. Its open choices are fixed in its docstring and **approved by Alex (2026-10-05)**. Do not change the rule or these choices after seeing results (hard rule 12).
   - If the script fails on the real data, fix only the mechanics, and list the fix in the REVIEW.
4. **Wall times:** compute the actual wall time per arm from the `.done` markers (`start`, `end`, `seconds`, `host`, `device`), per machine.
5. **Write `results/iter05b_data_limit/REVIEW_stage1.md`.** It is one page, in the CLAUDE.md §9 template. It must contain:
   - the D verdict per family and overall, and F if it applies (pre-registered rule; per Paper A bin too);
   - the learning-curve figure;
   - the headline criterion table, with the filler-variability-limited bins (≤ 15, 15–35, 35–65 %) marked.

   **Cautions to state:**
   - multiplicity (5 families tested, configurations selected by inner CV);
   - GB labels are 30-min, so compare gaps to physics across datasets, not levels;
   - the fillers are analog-mapped LCL households (quote the 05a D5 swap-test deltas next to the headline numbers, which the report prints);
   - the 33 skipped designs and the thinner n = 16 / 32 points;
   - A8 (CatBoost and GP dropped);
   - A9 (CNN and TabPFN on GPU, machine split, CPU runs archived);
   - the actual wall times, and the queue crash of 2026-10-03 (a worker died of memory pressure; nothing finished was lost).

   **Decisions for Alex (2–3, each with a recommended option):** at least the verdict, and whether to start Stage 2 and with which runtime reduction (see §3).
6. **Commit and push** to `iter/05b-data-limit`:
   - include the merged CSVs, `stage1\report\`, `REVIEW_stage1.md`, `STATUS.md`, `progress.json` and the `jobs\*.done` / `*.failed` markers;
   - leave out `jobs\*.parquet` and `jobs_cpu_archive\` if they are large (state their size in the REVIEW).

   Then **stop**.

## 3. Stage 2 (only after Alex's go; prepare nothing heavy before)

- Arms 3–7 in the order Arm 7 → 4 → 3 → 5 → 6 (brief, Task 2).
- At current settings, Stage 2 is far beyond ~3 nights. Propose a reduction **for Alex to decide** before scheduling. The leading option is to run only each family's Arm 2 inner-CV winner (per seed) in Arms 3, 4, 6 and 7. Size it from the real job times in the `.done` markers and the `*.timing.parquet` frames.
- The CNN and TabPFN should again run on machine B's GPU (A9: one device per family).

## 4. Practical notes (machine A)

- **Memory:** 10 workers caused paging (RAM 93 %, CPU 40 %) and a dead worker. Use at most 6 workers here and keep RAM below about 85 %.
- **Measured job times on this CPU:**
  - Arm 2 tree jobs: 8.5–11 h;
  - CNN on CPU: 11–16 h (this is why the CNN and TabPFN moved to the GPU).
- **Windows DLL order:** torch must be imported before pandas / pyarrow (WinError 1114 otherwise). `run_queue.py` does this; scripts that import it must import it first, as `check_jobs.py` does.
- **Scheduling:** never register a scheduled task yourself. Print the `scripts\schedule_overnight.ps1` command and Alex runs it (`-Continuous`, `-Workers`, `-Families`, `-Shard` are available).
- **Secrets:** never print or commit a token. TabPFN weights are local (`TABPFN_MODEL_CACHE_DIR`).
- **Tools:**
  - `scripts/paperb/check_jobs.py` (merge readiness);
  - `scripts/paperb/iter05b_report.py` (Stage 1 verdict and tables);
  - `scripts/paperb/run_queue.py` (`--families`, `--shard`, `--retry-failed`, `--arms`);
  - `scripts/paperb/runtime_estimate.py --probe05b`.
