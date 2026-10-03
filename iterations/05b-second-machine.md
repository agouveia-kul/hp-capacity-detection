# 05b Stage 1 on a second machine (setup brief for a local agent)

You are setting up a second machine (machine B, RTX 5060 Ti 16 GB) to share the 05b Stage 1 queue of the repository `agouveia-kul/hp-capacity-detection`. **Plan of 2026-10-03:** machine B runs the two GPU families, the raw-series CNN and TabPFN (`configs/iter05b_stage1_gpu.yaml --families rawseries,tabpfn`); machine A (Alex's main PC) runs the CPU families (`configs/iter05b_stage1.yaml --families physics,linear,trees,kernel,neural`). Both configs give the same job list, so both machines must run the **same commit**. (`--shard I/N` remains available if the plan changes.)

Read `CLAUDE.md` first. Its hard rules apply here, in particular: never modify anything in `data/` other than placing the copied cache; never register a scheduled task yourself (print the command, Alex runs it); never print or commit a token; do not commit or push from this machine.

## 1. Code and environment
1. Clone the repo and check out branch `iter/05b-data-limit`. Run `git rev-parse HEAD` and confirm with Alex that it equals machine A's commit (at least `039b850`). Stop if it differs.
2. Create a Python 3.12 virtual environment in `.venv` and install `requirements.txt` exactly (pinned versions). Report the install size and any package that fails. Do not upgrade or substitute packages.
   **Exception, torch:** replace the CPU wheel by the CUDA build of the **same version** (`torch==2.14.1`). The RTX 5060 Ti (Blackwell) needs a CUDA 12.8 or newer build; take the install command from the selector on pytorch.org for that version, e.g. `pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cu128`. Check `python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"`.
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
3. The GPU smoke test passes (not skipped): `.venv\Scripts\python -m pytest tests/test_05b.py -k cuda -rs`. It checks that the CNN is deterministic on CUDA and close to its CPU result, and that TabPFN fits on CUDA.
4. Hardware: report CPU cores, RAM, `nvidia-smi` (driver, CUDA version, VRAM).

## 4. Schedule (Alex runs it)
Start with 4 workers (at most 4 CNN and 2 TabPFN jobs at once, set in the GPU config). Print this command for Alex, with `-StartAt` a few minutes ahead (a time that has passed means tomorrow):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter05b_stage1_gpu.yaml -StartAt HH:MM -Continuous -Workers 4 -Families rawseries,tabpfn
```

Watch `nvidia-smi` and the Task Manager after the first jobs. If the GPU is far from busy and RAM is below about 70 %, relaunch with more workers. If RAM exceeds about 85 %, relaunch with fewer.

After the first jobs finish, check `results\iter05b_data_limit\stage1\progress.json` and the Task Manager: CPU should be near 100 % and RAM below about 85 %. If RAM is higher, stop the queue (`Stop-ScheduledTask -TaskName paperb-iter05b_stage1`, then end the `.venv` Python processes) and relaunch with fewer workers. The queue resumes; only the running jobs are redone.

`progress.json` on this machine counts machine A's jobs as remaining. Count only the `rawseries` and `tabpfn` jobs (`jobs\*__rawseries.done`, `jobs\*__tabpfn.done`).

## 5. Hand-back
**Decision A9 (2026-10-03):** the CNN and TabPFN families run entirely on this GPU, so this machine runs **all** their jobs, including the ones machine A already ran on CPU. Before merging, Alex moves machine A's CPU outputs of these two families out of its `jobs` folder:
```powershell
New-Item -ItemType Directory -Force results\iter05b_data_limit\stage1\jobs_cpu_archive | Out-Null
Move-Item results\iter05b_data_limit\stage1\jobs\*__rawseries.* results\iter05b_data_limit\stage1\jobs_cpu_archive\
Move-Item results\iter05b_data_limit\stage1\jobs\*__tabpfn.* results\iter05b_data_limit\stage1\jobs_cpu_archive\
```
When this machine has no job left, Alex copies this machine's `results\iter05b_data_limit\stage1\jobs\` files (`*.parquet`, `*.done`, `*.failed`) into machine A's `jobs` folder, for example:
`robocopy <this repo>\results\iter05b_data_limit\stage1\jobs <machine A repo>\results\iter05b_data_limit\stage1\jobs *.parquet *.done *.failed /XO`
Machine A then runs the queue once more, finds nothing left and writes the merged CSVs. Each `.done` file records the host that ran the job.

Report back to Alex: commit, environment problems, the checks above, workers chosen, the scheduling command, and any failed job with its traceback (`STATUS.md`).
