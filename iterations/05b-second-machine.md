# 05b Stage 1 on a second machine (setup brief for a local agent)

You are setting up a second machine to share the 05b Stage 1 queue of the repository `agouveia-kul/hp-capacity-detection`. Machine A (Alex's main PC) runs shard `0/2`; this machine runs shard `1/2`. The two shards are disjoint halves of the same job list (`scripts/paperb/run_queue.py --shard`), so both machines must run the **same commit and the same config**.

Read `CLAUDE.md` first. Its hard rules apply here, in particular: never modify anything in `data/` other than placing the copied cache; never register a scheduled task yourself (print the command, Alex runs it); never print or commit a token; do not commit or push from this machine.

## 1. Code and environment
1. Clone the repo and check out branch `iter/05b-data-limit`. Run `git rev-parse HEAD` and confirm with Alex that it equals machine A's commit (at least `039b850`). Stop if it differs.
2. Create a Python 3.12 virtual environment in `.venv` and install `requirements.txt` exactly (pinned versions). Report the install size and any package that fails. Do not upgrade or substitute packages.
3. TabPFN: Alex copies the checkpoint `tabpfn-v3.5-20260909.safetensors` to a local folder and you set the environment variable `TABPFN_MODEL_CACHE_DIR` to that folder (user scope). Never download weights yourself and never use a token.

## 2. Data
Alex copies the cache folder `data/_paperb/` from machine A (not the whole `data/` folder). On machine A, `data/` is a junction to a OneDrive folder; here `data/_paperb/` can be a plain folder inside the repo. Check that these files exist:
- `data/_paperb/pools/gb_eoh_2122r3.parquet` and `gb_eoh_2122r3_meta.parquet` (GB dataset, main window);
- `data/_paperb/pools/lcl_std_20120701_20140228_heathrow.npy`, `..._days.parquet`, `..._meta.parquet`, `..._audit.json` (LCL fillers);
- optionally `data/_paperb/features/` and `data/_paperb/pilots/` (caches that save time; they are rebuilt deterministically if missing).

If the pool or LCL cache is missing, **stop**: the code would try to rebuild it from raw EoH / LCL files that are not on this machine. The EoH (UKDS SN 9050) and LCL (UKDS SN 7857) data are licensed; do not copy them anywhere else.

## 3. Checks before anything runs
1. `.venv\Scripts\python -m pytest -q` passes (tests that need the B* cache or the TabPFN checkpoint may skip; list the skips).
2. The GB dataset loads from the cache without a rebuild:
   `.venv\Scripts\python -c "import sys; sys.path.insert(0,'scripts'); from paperb import load_config; from paperb.pools import build_pool; c=load_config('configs/iter05b_arm2.yaml'); p=build_pool('gb_eoh', c, verbose=False); print(p.meta['role'].value_counts())"`
   Expected: 384 `hp` and 3,199 `fill`.
3. The shard is what machine A expects: `.venv\Scripts\python -c "import sys,yaml; sys.path.insert(0,'scripts'); from paperb import run_queue as RQ; q=yaml.safe_load(open('configs/iter05b_stage1.yaml')); j=RQ.jobs(q); print(len(j), len(RQ.shard(j,'1/2')))"` gives `840 420`.
4. Hardware: report CPU cores, RAM and whether an NVIDIA GPU is present (`nvidia-smi`; model and VRAM). **If there is an NVIDIA GPU, stop and report it before scheduling**: Alex may move the CNN and TabPFN jobs to it, which changes how the jobs are split.

## 4. Schedule (Alex runs it)
Choose the number of workers from RAM: start with `min(physical cores / 2, RAM in GB / 5)`, rounded down. Machine A paged at 10 workers. Print this command for Alex, with `-StartAt` a few minutes ahead (a time that has passed means tomorrow):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter05b_stage1.yaml -StartAt HH:MM -Continuous -Workers N -Shard 1/2
```

After the first jobs finish, check `results\iter05b_data_limit\stage1\progress.json` and the Task Manager: CPU should be near 100 % and RAM below about 85 %. If RAM is higher, stop the queue (`Stop-ScheduledTask -TaskName paperb-iter05b_stage1`, then end the `.venv` Python processes) and relaunch with fewer workers. The queue resumes; only the running jobs are redone.

`progress.json` on this machine counts machine A's jobs as remaining. Count only this shard: 420 jobs.

## 5. Hand-back
When this shard has no job left, Alex copies this machine's `results\iter05b_data_limit\stage1\jobs\` files (`*.parquet`, `*.done`, `*.failed`) into machine A's `jobs` folder, for example:
`robocopy <this repo>\results\iter05b_data_limit\stage1\jobs <machine A repo>\results\iter05b_data_limit\stage1\jobs *.parquet *.done *.failed /XO`
Machine A then runs the queue once more, finds nothing left and writes the merged CSVs. Each `.done` file records the host that ran the job.

Report back to Alex: commit, environment problems, the checks above, workers chosen, the scheduling command, and any failed job with its traceback (`STATUS.md`).
