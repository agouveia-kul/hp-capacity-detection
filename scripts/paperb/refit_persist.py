"""05b A10 (DECISIONS.md 2026-10-05): refit and persist each family's Arm 2 inner-CV winner per seed, reload check, carry-forward rule.

    plan   winners = lowest inner-CV WAPE per (seed, family) in stage1/arm2/metrics.csv (lc_fit.family_winners, as the report);
           their hyperparameters and best iteration are read from the queue logs (`HP_Peak <spec>: ... best_iter B, ... params {...}`)
           and matched to the Arm 2 job by its timing row (cv_wape and train_wape to 0.1, as logged) -> refit/refit_plan.csv
    refit  per seed, the winners of the chosen queue families are refit with those values on the same train substations, seed and
           code path (run_benchmark.run_seed with cfg.refit; no hyperopt, no inner CV) and saved by persist.save_model
           -> stage1/models/s<seed>/<family>/ (git-ignored). CNN / TabPFN run on machine B's GPU (A9): --families rawseries,tabpfn
           --set device=cuda there.
    check  in a fresh process, reload every saved model, predict its test design, compare with the test predictions the queue
           logged (jobs/*.preds.parquet): pass = max relative difference <= 1e-6 (CPU models), |dWAPE| <= 0.1 pp (CNN, TabPFN on GPU)
           -> refit/reload_check.csv (rows of other machines' runs are kept)
    carry  rank the families by the median over seeds of the winner's inner-CV WAPE (never test); carry the top 2 plus any family
           within 1 pp of the best, linear always; models failing the reload check are not carried -> refit/carry_forward.csv|md

    python scripts/paperb/refit_persist.py plan  [--log results/iter05b_data_limit/stage1/logCUDA.txt ...]
    python scripts/paperb/refit_persist.py refit [--families physics,linear,trees,kernel,neural] [--workers 6] [--set device=cuda]
    python scripts/paperb/refit_persist.py check [--families ...]
    python scripts/paperb/refit_persist.py carry
"""
try:                                                                  # torch before pandas / pyarrow (WinError 1114 on Windows)
    import torch  # noqa: F401
except ImportError:
    pass
import argparse  # noqa: E402
import ast
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from paperb import ROOT, load_config, set_dotted  # noqa: E402
from paperb.lc_fit import CONFIG_COLS, FAMILY_OF, family_winners  # noqa: E402

STAGE1 = ROOT / "results" / "iter05b_data_limit" / "stage1"
QUEUE = ROOT / "configs" / "iter05b_stage1.yaml"
KEYS = ["split_seed", "lc_draw", "n"]
GPU_MODELS = {"CNN", "TabPFN"}                                         # A9: these run on machine B's GPU
TOL_REL, TOL_WAPE_PP, TOP_K, NEAR_PP, ALWAYS = 1e-6, 0.1, 2, 1.0, "linear"
LINE = re.compile(r"^\[s(\d+)\s+[\d.]+s\]\s+HP_Peak (\S+): cv_mse \S+, cv_wape (\S+), train_wape (\S+), best_iter (\S+), \d+ evals, [\d.]+s, params (\{.*\})\s*$")


def queue_family(q):
    """model -> queue family (jobs/<id>__<queue family>.*)."""
    return {m: f for f, v in q["families"].items() for m in v.get("models", []) + v.get("residual_models", [])}


def winners(stage1=STAGE1):
    """Arm 2 family winners by inner-CV WAPE (the report's rule), one row per (seed, family) with its wape_inner."""
    m = pd.read_csv(stage1 / "arm2" / "metrics.csv")
    m = m[(m["target"] == "HP_Peak") & (m["cell"] == "all") & (m["metric"] == "wape_inner") & m["method"].isin(FAMILY_OF)]
    A = m.rename(columns={"value": "wape_inner"}).assign(lc_draw=0, n=-1)[KEYS + CONFIG_COLS + ["wape_inner"]]
    return family_winners(A, KEYS)


def log_params(logs):
    """(seed, spec 'm/a/f/mode/tt') -> list of logged fits {cv_wape, train_wape, best_iter, params}."""
    out = {}
    for f in logs:
        for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
            if (g := LINE.match(line)):
                bi = None if g[5] == "None" else int(g[5])
                out.setdefault((int(g[1]), g[2]), []).append({"cv_wape": float(g[3]), "train_wape": float(g[4]), "best_iter": bi,
                                                              "params": ast.literal_eval(g[6])})
    return out


def plan(logs, stage1=STAGE1):
    q = yaml.safe_load(QUEUE.read_text())
    qf, L, rows = queue_family(q), log_params(logs), []
    for r in winners(stage1).to_dict("records"):
        spec = [r[c] for c in CONFIG_COLS]
        job = f"arm2__s{r['split_seed']}__d0__nall__{qf[r['method']]}"
        t = pd.read_parquet(stage1 / "jobs" / f"{job}.timing.parquet")
        t = t[(t[CONFIG_COLS].astype(str).to_numpy() == np.array(spec, dtype=str)).all(axis=1)]
        cand = [c for c in L.get((int(r["split_seed"]), "/".join(spec)), []) if len(t)
                and abs(c["cv_wape"] - float(t["cv_wape"].iloc[0])) <= 0.051 and abs(c["train_wape"] - float(t["train_wape"].iloc[0])) <= 0.051]
        distinct = {json.dumps([c["params"], c["best_iter"]], sort_keys=True, default=str) for c in cand}
        status = "ok" if len(distinct) == 1 else "ambiguous" if distinct else "no log line"
        if not distinct and r["method"] == "TabPFN":                    # no search space: nothing to look up
            distinct, status = {json.dumps([{}, None])}, "ok (no hyperparameters)"
        p, bi = json.loads(next(iter(distinct))) if len(distinct) == 1 else (None, None)
        rows.append({"split_seed": int(r["split_seed"]), "family": r["family"], "queue_family": qf[r["method"]], "spec": "|".join(spec),
                     "wape_inner": r["wape_inner"], "params": json.dumps(p), "best_iter": bi, "device": "cuda" if r["method"] in GPU_MODELS else "cpu",
                     "n_log_matches": len(cand), "status": status})
    P = pd.DataFrame(rows).sort_values(["split_seed", "family"])
    (stage1 / "refit").mkdir(exist_ok=True)
    P.to_csv(stage1 / "refit" / "refit_plan.csv", index=False)
    print(P.groupby(["family", "status"]).size().to_string())
    return P


def refit_seed(cfg, seed):
    from paperb.run_benchmark import run_seed
    res = run_seed(cfg, seed)
    return seed, res["log"]


def refit(families, workers, overrides, stage1=STAGE1):
    P = pd.read_csv(stage1 / "refit" / "refit_plan.csv")
    P = P[P["queue_family"].isin(families) & P["status"].str.startswith("ok")]
    q = yaml.safe_load(QUEUE.read_text())
    arm = next(a for a in q["arms"] if a["name"] == "arm2")
    base = set_dotted(load_config(arm["config"]), overrides)
    base.setdefault("parallel", {})["threads"] = max(1, (os.cpu_count() or 1) // workers)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = "1"                                           # as the queue: BLAS order independent of the worker count
    jobs = {}
    for seed, g in P.groupby("split_seed"):
        fixed = {r["spec"]: {"params": json.loads(r["params"]), "best_iter": None if pd.isna(r["best_iter"]) else int(r["best_iter"])} for r in g.to_dict("records")}
        jobs[int(seed)] = {**base, "refit": {"dir": str(stage1 / "models"), "fixed": fixed, "device": base.get("device", "cpu")}, "pilot_cache": True}
    lines, failed = [], {}
    with cf.ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(refit_seed, c, s): s for s, c in jobs.items()}
        for fut in cf.as_completed(futs):
            try:
                _, log = fut.result()
                lines += log
            except Exception:                                           # listed, never silently dropped
                failed[futs[fut]] = traceback.format_exc()
                lines.append(f"seed {futs[fut]} FAILED:\n{failed[futs[fut]]}")
            print(f"seed {futs[fut]} {'FAILED' if futs[fut] in failed else 'done'}", flush=True)
    with open(stage1 / "refit" / "refit_log.txt", "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return failed


def check(families, stage1=STAGE1):
    from paperb.persist import load_predict
    P = pd.read_csv(stage1 / "refit" / "refit_plan.csv")
    P = P[P["queue_family"].isin(families)]
    rows = []
    for r in P.to_dict("records"):
        d = stage1 / "models" / f"s{r['split_seed']}" / r["family"]
        row = {k: r[k] for k in ("split_seed", "family", "spec", "device")}
        try:
            pr = load_predict(d)
            lg = pd.read_parquet(stage1 / "jobs" / f"arm2__s{r['split_seed']}__d0__nall__{r['queue_family']}.preds.parquet")
            lg = lg[(lg["target"] == "HP_Peak") & (lg[CONFIG_COLS].astype(str).agg("|".join, axis=1) == r["spec"])]
            lg = lg.assign(sub_id=lg["sub_id"].astype(str)).set_index("sub_id")
            pr.index = pr.index.astype(str)
            a, b, y = pr.reindex(lg.index).to_numpy(float), lg["pred"].to_numpy(float), lg["y"].to_numpy(float)
            rel = np.abs(a - b) / np.maximum(np.abs(b), 1e-9)
            w_r, w_l = (100 * np.nansum(np.abs(v - y)) / np.nansum(y) for v in (a, b))
            gpu = r["spec"].split("|")[0] in GPU_MODELS
            ok = len(lg) > 0 and not np.isnan(a).any() and (abs(w_r - w_l) <= TOL_WAPE_PP if gpu else float(np.max(rel)) <= TOL_REL)
            row.update(n_test=len(lg), max_rel_diff=float(np.max(rel)) if len(rel) else np.nan, wape_logged=w_l, wape_reload=w_r,
                       dwape_pp=w_r - w_l, rule=f"|dWAPE| <= {TOL_WAPE_PP} pp" if gpu else f"max rel <= {TOL_REL:g}", reload_pass=bool(ok),
                       model_mb=round(sum(f.stat().st_size for f in d.iterdir()) / 2**20, 2), error="")
        except Exception as e:                                          # listed, never silently dropped
            row.update(reload_pass=False, error=f"{type(e).__name__}: {e}"[:300])
        rows.append(row)
    C = pd.DataFrame(rows)
    f = stage1 / "refit" / "reload_check.csv"
    if f.exists():                                                      # keep the other machine's rows
        old = pd.read_csv(f)
        C = pd.concat([old[~old.set_index(["split_seed", "family"]).index.isin(C.set_index(["split_seed", "family"]).index)], C])
    C.sort_values(["split_seed", "family"]).to_csv(f, index=False)
    print(C.groupby("family")["reload_pass"].agg(["sum", "size"]).to_string())
    return C


def carry_rule(P, checked=None):
    """Family ranking and carry decision from the plan (inner-CV WAPE of each seed's winner) -> (family table, per-model table)."""
    med = P.groupby("family")["wape_inner"].median().sort_values()
    best = med.iloc[0]
    F = pd.DataFrame({"family": med.index, "median_inner_wape": med.to_numpy(), "rank": range(1, len(med) + 1),
                      "gap_to_best_pp": med.to_numpy() - best})
    F["carried"] = (F["rank"] <= TOP_K) | (F["gap_to_best_pp"] <= NEAR_PP) | (F["family"] == ALWAYS)
    F["reason"] = np.where(F["rank"] <= TOP_K, f"top {TOP_K}", np.where(F["gap_to_best_pp"] <= NEAR_PP, f"within {NEAR_PP:g} pp",
                                                                       np.where(F["family"] == ALWAYS, "linear always", "not carried")))
    M = P.merge(F[["family", "carried"]], on="family")
    if checked is not None and len(checked):
        M = M.merge(checked[["split_seed", "family", "reload_pass"]], on=["split_seed", "family"], how="left")
    else:
        M["reload_pass"] = np.nan
    M["carried_model"] = M["carried"] & (M["reload_pass"] == True)  # noqa: E712  (NaN = not checked yet -> not carried)
    return F, M


def md(df):
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * df.shape[1]]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])


def carry(stage1=STAGE1):
    P = pd.read_csv(stage1 / "refit" / "refit_plan.csv")
    f = stage1 / "refit" / "reload_check.csv"
    F, M = carry_rule(P, pd.read_csv(f) if f.exists() else None)
    F.to_csv(stage1 / "refit" / "carry_forward.csv", index=False)
    M.to_csv(stage1 / "refit" / "carry_forward_models.csv", index=False)
    txt = ["# A10 carry-forward (refit_persist.py carry)", "", "Families ranked by the median over seeds of the Arm 2 winner's inner-CV WAPE (never test).", "",
           md(F.round(2)), "", "Carried models per family (reload check passed):", "",
           M.groupby("family").agg(seeds=("split_seed", "size"), reload_pass=("reload_pass", lambda s: int((s == True).sum())),  # noqa: E712
                                   carried_models=("carried_model", "sum")).reset_index().pipe(md)]
    (stage1 / "refit" / "carry_forward.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))
    return F, M


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["plan", "refit", "check", "carry"])
    ap.add_argument("--log", nargs="*", default=[], help="extra queue logs (machine B: logCUDA.txt); stage1/log.txt is always read")
    ap.add_argument("--families", default="linear,trees,kernel,neural", help="queue families (GPU: rawseries,tabpfn)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--set", nargs="*", default=[], help="dotted overrides, e.g. device=cuda")
    a = ap.parse_args()
    fams = a.families.split(",")
    if a.step == "plan":
        plan([STAGE1 / "log.txt", *a.log])
    elif a.step == "refit":
        sys.exit(1 if refit(fams, a.workers, a.set) else 0)
    elif a.step == "check":
        check(fams)
    else:
        carry()
