"""Resumable overnight job queue (iteration 05a, Task 4b).

A queue config lists `arms` in priority order. Each arm names a run_benchmark config (`config`) and the job dimensions
seeds / draws / n / families; `families` maps a family to the models it runs (`models`, `residual_models`, extra dotted
overrides in `set`). A job is one (arm, seed, draw, n, family); jobs run in the order arm (priority) -> family (in the
arm's order, physics first, so each seed's substation features are evaluated once and cached before the model families
reuse them) -> seed -> n -> draw. A job calls the arm's runner (default `run_benchmark.run_seed`) on the arm config
restricted to the family and keeps only the family's rows (`physics`: every non-ML row). Its frames are written to a
local staging directory, then moved one by one to <out_dir>/jobs/<job_id>.<frame>.parquet, and a <job_id>.done marker
(json: seconds, start, end) is written last. A relaunch skips jobs with a marker, so a crash, reboot or morning stop
loses at most the running jobs. A failing job writes <job_id>.failed (traceback) and is never retried in a loop;
`--retry-failed` reruns only the failed jobs. A family's `max_concurrent` caps how many of its jobs run at once (the next job
of another family starts instead). `--stop-at HH:MM` starts no job after the next such time (running jobs
finish). While the queue runs, SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) keeps Windows awake (no
admin rights, no power-setting change); it is reset at exit. progress.json is rewritten after every job and STATUS.md at
exit; once no job remains, every arm's job frames are merged into <out_dir>/<arm>/<frame>.csv (metrics.csv as
run_benchmark.py writes it). 05b: a job with n != all runs one learning-curve design (n, draw) of the arm (`lc_only`: only the test
substations of the full design are evaluated, every spec of the family is scored into metrics_lc.csv); n = all has one draw.

    python scripts/paperb/run_queue.py --config configs/iter05a_overnight.yaml [--workers 4] [--stop-at 07:30] [--retry-failed] [--arms name,name] [--shard I/N]

05b: `--shard I/N` runs only the jobs whose position in the job list is I modulo N, so N machines can share one queue with
disjoint jobs (same commit, environment and data/_paperb caches on each). Status and the merge still cover every job: after
copying the other machines' jobs/ files into this out_dir, a relaunch finds nothing to do and merges. Each .done marker
records the host that ran the job.
"""
import os
import platform

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):    # BLAS 1 thread (determinism), before numpy
    os.environ.setdefault(_v, "1")
try:                                                                  # 05b: torch before pandas / pyarrow (pyarrow 15 bundles an old
    import torch  # noqa: F401                                        # msvcp140.dll that breaks torch's c10.dll if it is loaded first)
except ImportError:
    pass
import argparse  # noqa: E402
import concurrent.futures as cf  # noqa: E402
import importlib  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from paperb import ROOT, git_hash, load_config, set_dotted  # noqa: E402

FRAMES = ("metrics", "timing", "preds", "pilots", "dropped", "diag", "lc", "lc_dropped")
CSV = {"preds": "predictions", "dropped": "dropped_cells", "diag": "physics_diagnostics", "lc": "metrics_lc", "lc_dropped": "dropped_cells_lc"}
ML_OFF = ["models=[]", "residual_models=[]", "modes=[direct]"]


def jobs(q):
    """All jobs of queue config `q` in priority order: dicts with arm, seed, draw, n, family, id."""
    out = []
    for arm in q["arms"]:
        for fam in arm["families"]:
            for seed in arm["seeds"]:
                for n in arm.get("n", ["all"]):
                    for draw in ([0] if n == "all" else arm.get("draws", [0])):
                        out.append({"arm": arm["name"], "seed": seed, "draw": draw, "n": n, "family": fam,
                                    "id": f"{arm['name']}__s{seed}__d{draw}__n{n}__{fam}"})
    return out


def job_config(q, arm, job, threads):
    """Arm config restricted to the job's family (and n, draw)."""
    fam = q["families"][job["family"]]
    over = ML_OFF if job["family"] == "physics" else [
        f"models={fam.get('models', [])}", f"residual_models={fam.get('residual_models', [])}", "physics_baselines=[]",
        "anchor_only_baselines.models=[]", "paperA.estimators=[]"]
    cfg = set_dotted(load_config(arm["config"]), over + list(fam.get("set", [])) + list(arm.get("set", [])))
    if job["n"] != "all":                                             # 05b: one learning-curve design, test substations shared with n = all
        cfg.update(lc_only=True, learning_curve={"n": [int(job["n"])], "draws": int(job["draw"]) + 1, "draw_ids": [int(job["draw"])],
                                                 "specs": "all", "feature_sets": cfg.get("feature_sets", ["whdd"])})
    cfg.setdefault("parallel", {})["threads"] = threads
    return cfg, set(fam.get("models", [])) | set(fam.get("residual_models", []))


def keep_family(frames, family, fam_models, ml_models):
    """Rows of the family: its models (family jobs), or every non-ML row (physics)."""
    out = {}
    for k, d in frames.items():
        if isinstance(d, pd.DataFrame) and len(d) and "method" in d:
            d = d[~d["method"].isin(ml_models)] if family == "physics" else d[d["method"].isin(fam_models)]
        elif family != "physics":
            d = pd.DataFrame()
        out[k] = d
    return out


def run_job(q, job, threads, stage):
    """Worker: run one job and stage its frames -> (job, staged files, seconds)."""
    for p in q.get("sys_path", []):
        sys.path.insert(0, str(ROOT / p))
    t0, start = time.time(), datetime.now().isoformat(timespec="seconds")
    arm = next(a for a in q["arms"] if a["name"] == job["arm"])
    cfg, fam_models = job_config(q, arm, job, threads)
    mod, fn = arm.get("runner", "paperb.run_benchmark:run_seed").split(":")
    res = getattr(importlib.import_module(mod), fn)(cfg, job["seed"])
    ml = set().union(*(set(f.get("models", [])) | set(f.get("residual_models", [])) for f in q["families"].values()))
    files = []
    for k, d in keep_family({k: res.get(k) for k in FRAMES}, job["family"], fam_models, ml).items():
        if isinstance(d, pd.DataFrame) and len(d):
            f = stage / f"{job['id']}.{k}.parquet"
            d.assign(arm=job["arm"], family=job["family"]).astype({c: str for c in d.columns if d[c].dtype == object}).to_parquet(f)
            files.append(f)
    return job, files, {"seconds": time.time() - t0, "start": start, "end": datetime.now().isoformat(timespec="seconds"), "host": platform.node()}


def shard(all_jobs, spec):
    """Jobs of shard `spec` = "I/N" (positions I mod N of the fixed job list); every job if spec is None."""
    if not spec:
        return list(all_jobs)
    i, n = (int(x) for x in spec.split("/"))
    if not 0 <= i < n:
        raise ValueError(f"--shard {spec}: need 0 <= I < N")
    return [j for k, j in enumerate(all_jobs) if k % n == i]


def keep_awake(on):
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | (0x00000001 if on else 0))   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED


def stop_time(hhmm):
    if not hhmm:
        return None
    now = datetime.now()
    t = now.replace(hour=int(hhmm[:2]), minute=int(hhmm[3:5]), second=0, microsecond=0)
    return t if t > now else t + timedelta(days=1)


def status(q, out, all_jobs, t_start, write_status=False):
    J = out / "jobs"
    done = {j["id"]: json.loads((J / f"{j['id']}.done").read_text()) for j in all_jobs if (J / f"{j['id']}.done").exists()}
    failed = [j["id"] for j in all_jobs if (J / f"{j['id']}.failed").exists() and j["id"] not in done]
    left = len(all_jobs) - len(done) - len(failed)
    med = float(np.median([d["seconds"] for d in done.values()])) if done else None
    prog = {"done": len(done), "failed": len(failed), "remaining": left, "median_job_s": med,
            "eta_h": None if med is None else round(left * med / q.get("workers", 1) / 3600, 2), "updated": datetime.now().isoformat(timespec="seconds")}
    (out / "progress.json").write_text(json.dumps(prog, indent=1))
    if write_status:
        lines = [f"# Queue status: {q['exp_id']}", "", f"Session wall time {(time.time() - t_start) / 3600:.2f} h; "
                 f"done {len(done)}, failed {len(failed)}, remaining {left} (of {len(all_jobs)}).", "",
                 "| arm | done | failed | remaining | job hours (sum) | first start | last end |", "|---|---|---|---|---|---|---|"]
        for arm in q["arms"]:
            ids = [j["id"] for j in all_jobs if j["arm"] == arm["name"]]
            d = [done[i] for i in ids if i in done]
            nf = sum(i in failed for i in ids)
            lines.append(f"| {arm['name']} | {len(d)} | {nf} | {len(ids) - len(d) - nf} | {sum(x['seconds'] for x in d) / 3600:.2f} | "
                         f"{min((x['start'] for x in d), default='-')} | {max((x['end'] for x in d), default='-')} |")
        for i in failed:
            lines += ["", f"## FAILED {i}", "```", *(J / f"{i}.failed").read_text().splitlines()[:20], "```"]
        (out / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return prog


def merge(q, out, all_jobs):
    """Concatenate every arm's job frames into <out>/<arm>/<frame>.csv."""
    from paperb.run_benchmark import SPEC_COLS
    cols = ["exp_id", "split_seed", "dataset", "target", *SPEC_COLS, "cell", "metric", "value", "n_substations", "n_hp_households"]
    for arm in q["arms"]:
        d = out / arm["name"]
        d.mkdir(parents=True, exist_ok=True)
        for k in FRAMES:
            fs = [out / "jobs" / f"{j['id']}.{k}.parquet" for j in all_jobs if j["arm"] == arm["name"]]
            parts = [pd.read_parquet(f) for f in fs if f.exists()]
            if parts:
                m = pd.concat(parts, ignore_index=True)
                lc = cols[:4] + ["n_train_hp", "lc_draw", "spc_train"] + cols[4:] + ["arm", "family"]
                {"metrics": lambda: m[cols + ["arm", "family"]], "lc": lambda: m[lc]}.get(k, lambda: m)().to_csv(d / f"{CSV.get(k, k)}.csv", index=False)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--stop-at", default=None, help="HH:MM: start no job after this time")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--arms", default=None, help="comma-separated arm names: run only these arms (e.g. the timing probe)")
    ap.add_argument("--shard", default=None, help="I/N: run only jobs at positions I mod N (several machines, disjoint jobs)")
    a = ap.parse_args(argv)
    q = yaml.safe_load(open(ROOT / a.config))
    q["workers"] = a.workers or q.get("workers", 1)
    if a.arms:
        q["arms"] = [arm for arm in q["arms"] if arm["name"] in a.arms.split(",")]
    out = ROOT / q["out_dir"]
    (out / "jobs").mkdir(parents=True, exist_ok=True)
    stage = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "paperb_queue" / q["exp_id"]
    stage.mkdir(parents=True, exist_ok=True)
    for arm in q["arms"]:                                             # full config of every arm, with the git commit
        (out / arm["name"]).mkdir(exist_ok=True)
        tab = {}
        if any("TabPFN" in q["families"][f].get("models", []) + q["families"][f].get("residual_models", []) for f in arm["families"]):
            from paperb.train import tabpfn_info
            tab = {"tabpfn": tabpfn_info()}                             # checkpoint file, SHA-256, package version (05b Task 1e)
        (out / arm["name"] / "config.yaml").write_text(yaml.safe_dump({**load_config(arm["config"]), "queue": q, "git_commit": git_hash(), **tab},
                                                                      sort_keys=False), encoding="utf-8")
    all_jobs = jobs(q)
    if a.retry_failed:
        for f in (out / "jobs").glob("*.failed"):
            f.unlink()
    todo = [j for j in shard(all_jobs, a.shard) if not (out / "jobs" / f"{j['id']}.done").exists() and not (out / "jobs" / f"{j['id']}.failed").exists()]
    threads = max(1, (os.cpu_count() or 1) // q["workers"])
    t_start, t_stop = time.time(), stop_time(a.stop_at)
    print(f"[{datetime.now():%H:%M:%S}] queue {q['exp_id']}: {len(todo)} of {len(all_jobs)} jobs to run, {q['workers']} workers x "
          f"{threads} threads, stop at {t_stop}, shard {a.shard or 'all'}", flush=True)

    def finish(job, files, info, err=None):
        J = out / "jobs"
        if err is not None:
            (J / f"{job['id']}.failed").write_text(err, encoding="utf-8")
            print(f"[{datetime.now():%H:%M:%S}] FAILED {job['id']}:\n{err}", flush=True)
        else:
            for f in files:
                shutil.move(str(f), str(J / f.name))
            (J / f"{job['id']}.done").write_text(json.dumps(info))
            print(f"[{datetime.now():%H:%M:%S}] done {job['id']} ({info['seconds']:.0f} s)", flush=True)
        status(q, out, all_jobs, t_start)

    keep_awake(True)
    try:
        if q["workers"] == 1:
            for job in todo:
                if t_stop and datetime.now() >= t_stop:
                    break
                try:
                    finish(*run_job(q, job, threads, stage))
                except Exception:                                   # logged and skipped, never retried in a loop
                    finish(job, [], None, traceback.format_exc())
        else:
            ex = cf.ProcessPoolExecutor(q["workers"], mp_context=mp.get_context("spawn"), max_tasks_per_child=1)
            running, pending = {}, list(todo)
            cap = {f: v["max_concurrent"] for f, v in q["families"].items() if v.get("max_concurrent")}   # 05b: e.g. TabPFN (RAM)
            while True:
                while len(running) < q["workers"] and not (t_stop and datetime.now() >= t_stop):
                    busy = [j["family"] for j in running.values()]
                    job = next((j for j in pending if busy.count(j["family"]) < cap.get(j["family"], q["workers"])), None)
                    if job is None:
                        break
                    pending.remove(job)
                    running[ex.submit(run_job, q, job, threads, stage)] = job
                if not running:
                    break
                fin, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
                for fut in fin:
                    job = running.pop(fut)
                    try:
                        finish(*fut.result())
                    except Exception:
                        finish(job, [], None, traceback.format_exc())
            ex.shutdown()
    finally:
        keep_awake(False)
        prog = status(q, out, all_jobs, t_start, write_status=True)
    if prog["remaining"] == 0:
        merge(q, out, all_jobs)
    print(f"[{datetime.now():%H:%M:%S}] exit: {prog}", flush=True)
    return prog


if __name__ == "__main__":
    main()
