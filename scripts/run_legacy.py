"""Run the unchanged legacy scripts in scripts/legacy/ with their writes redirected.

The legacy scripts hard-code outputs into data/, models/ and paper/figures/.
This runner executes each one in a child process with a write guard installed:

* data/*.csv          -> <out_dir>/reproduced/<name>.csv
* data/<other>        -> <cache_dir>/<name>          (new caches go to data/_paperb/)
* models/<name>       -> <out_dir>/models/<name>     (gitignored)
* paper/figures/<f>   -> <out_dir>/figures/<f> (+ a PDF copy)

Reads always come from the original path when it exists (so the downstream
scripts use the legacy models/xgb_selected_features.json, i.e. evaluation-only),
and fall back to the redirected copy otherwise. Seeds that the legacy code does
not expose (hyperopt TPE) are set through HYPEROPT_FMIN_SEED from the config.

    python scripts/run_legacy.py --config configs/iter00_quick.yaml
"""
import argparse
import builtins
import io
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "scripts" / "legacy"


def load_config(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------- write guard --
def _rel(path):
    """Repo-relative posix path of `path` if it lies in data/, models/ or paper/."""
    if not isinstance(path, (str, os.PathLike)):
        return None
    p = os.path.abspath(os.fspath(path))
    try:
        rel = Path(os.path.relpath(p, ROOT)).as_posix()
    except ValueError:          # different drive
        return None
    if rel.split("/")[0] in ("data", "models", "paper") and not rel.startswith("data/_paperb/"):
        return rel
    return None


def redirect_target(rel, out_dir, cache_dir):
    top, name = rel.split("/")[0], rel.split("/", 1)[1]
    if top == "data":
        return (out_dir / "reproduced" / name) if name.endswith(".csv") else (cache_dir / name)
    if top == "models":
        return out_dir / "models" / name
    return out_dir / "figures" / Path(name).name          # paper/figures/...


def install_guard(out_dir, cache_dir, log):
    real_open, real_exists, real_makedirs = builtins.open, os.path.exists, os.makedirs

    def target(path):
        rel = _rel(path)
        return (rel, redirect_target(rel, out_dir, cache_dir)) if rel else (None, None)

    def guarded_open(file, mode="r", *a, **kw):
        rel, tgt = target(file)
        if rel is None:
            return real_open(file, mode, *a, **kw)
        if any(c in mode for c in "wax+"):
            tgt.parent.mkdir(parents=True, exist_ok=True)
            log(f"[redirect] write {rel} -> {tgt.relative_to(ROOT).as_posix()}")
            return real_open(tgt, mode, *a, **kw)
        if not real_exists(file) and real_exists(tgt):
            log(f"[redirect] read {rel} <- {tgt.relative_to(ROOT).as_posix()}")
            return real_open(tgt, mode, *a, **kw)
        return real_open(file, mode, *a, **kw)

    def guarded_exists(path):
        rel, tgt = target(path)
        return real_exists(path) or (rel is not None and real_exists(tgt))

    def guarded_makedirs(name, *a, **kw):
        if _rel(name) is not None:
            return None          # never create folders inside data/ models/ paper/
        return real_makedirs(name, *a, **kw)

    builtins.open = io.open = guarded_open
    os.path.exists = guarded_exists
    os.makedirs = guarded_makedirs

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    real_savefig = Figure.savefig

    def guarded_savefig(self, fname, *a, **kw):
        rel, tgt = target(fname)
        tgt = tgt if rel else Path(fname)
        tgt.parent.mkdir(parents=True, exist_ok=True)
        real_savefig(self, tgt, *a, **kw)
        real_savefig(self, tgt.with_suffix(".pdf"), *[x for x in a], **{k: v for k, v in kw.items() if k != "dpi"})
        log(f"[redirect] figure {fname} -> {Path(tgt).relative_to(ROOT).as_posix()} (+pdf)")

    Figure.savefig = guarded_savefig
    plt.savefig = lambda *a, **kw: plt.gcf().savefig(*a, **kw)


def run_one(cfg, name, args):
    """Child-process entry: guard, then execute the legacy script as __main__."""
    import runpy
    import numpy as np
    out_dir = ROOT / cfg["out_dir"]
    cache_dir = ROOT / cfg["cache_dir"]
    cache_dir.mkdir(parents=True, exist_ok=True)
    install_guard(out_dir, cache_dir, lambda m: print(m, flush=True))
    np.random.seed(cfg["seeds"]["numpy_global"])
    sys.path[:0] = [str(LEGACY), str(ROOT / "scripts"), str(ROOT / "src")]
    sys.argv = [str(LEGACY / f"{name}.py"), *args]
    runpy.run_path(str(LEGACY / f"{name}.py"), run_name="__main__")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--one", help=argparse.SUPPRESS)          # internal: child mode
    ap.add_argument("--only", nargs="*", help="subset of script names to run")
    ns, rest = ap.parse_known_args()
    cfg = load_config(ns.config)
    os.chdir(ROOT)
    if ns.one:
        return run_one(cfg, ns.one, rest)

    out_dir = ROOT / cfg["out_dir"]
    (out_dir / "logs").mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "HYPEROPT_FMIN_SEED": str(cfg["seeds"]["hyperopt"]),
           "PYTHONHASHSEED": str(cfg["seeds"]["pythonhash"]), "PYTHONUNBUFFERED": "1"}
    summary = []
    for job in cfg["scripts"]:
        name, args = job["name"], [str(a) for a in job.get("args", [])]
        if ns.only and name not in ns.only:
            continue
        log_path = out_dir / "logs" / f"{name}.log"
        t0 = time.time()
        with open(log_path, "w", encoding="utf-8") as fh:
            rc = subprocess.call([sys.executable, __file__, "--config", ns.config, "--one", name, *args],
                                 stdout=fh, stderr=subprocess.STDOUT, env=env, cwd=ROOT)
        dt = time.time() - t0
        summary.append(f"{name:32s} rc={rc}  {dt / 60:6.1f} min  log={log_path.relative_to(ROOT).as_posix()}")
        print(summary[-1], flush=True)
    with open(out_dir / "log.txt", "a", encoding="utf-8") as fh:
        fh.write(f"\n# run_legacy {time.strftime('%Y-%m-%d %H:%M:%S')} config={ns.config}\n")
        fh.write("\n".join(summary) + "\n")


if __name__ == "__main__":
    main()
