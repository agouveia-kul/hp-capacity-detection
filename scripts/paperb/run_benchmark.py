"""Protocol v1 benchmark runner. Writes results/<exp_id>/ in the CLAUDE.md s.8 format.

Per split seed: household split -> inner folds -> memberships (train, test, inner) -> targets, physics and
windowed features (cached in data/_paperb/features/) -> physics baselines, anchor-only baselines and ML
models (grouped-CV tuning on inner substations, refit on train) -> test metrics overall and per
(penetration x size) cell (household-cluster bootstrap CIs only if `uncertainty.bootstrap`).

Split seeds run in `parallel.workers` spawned processes (always, also for 1 worker, so the code path is the
same). Each worker gets XGBoost n_jobs = floor(cores / workers) (`train.configure`); OMP / MKL / OPENBLAS_NUM_THREADS
are set to `parallel.blas_threads` (1) in the environment the workers inherit, before their numpy import. BLAS
is pinned to one thread because the matrices are tiny and the summation order of a threaded BLAS changes Ridge
at the 1e-14 level, which would make metrics.csv depend on the worker count. Each finished seed is written to <out_dir>/seeds/ (`--resume` skips finished seeds);
metrics.csv is merged in seed order, so it does not depend on completion order.

    python scripts/paperb/run_benchmark.py --config configs/protocol_v1_quick.yaml [--set parallel.workers=4] [--resume]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from hp_capacity import compute_metrics  # noqa: E402
from paperb import ROOT, git_hash, load_config, set_dotted  # noqa: E402
from paperb.physics import make_baseline  # noqa: E402
from paperb.pools import build_pool  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import build_substations, evaluate_members  # noqa: E402
from paperb.train import configure, feature_matrix, tune_grouped_cv  # noqa: E402
from paperb.uncertainty import cluster_bootstrap  # noqa: E402

PHYSICS_FIT = ("slope_only", "slope_base", "calibrated_delta")     # HDH uses the fixed 12 degC base: no T_h fit


def cached_eval(pool, members, cfg, seed, log):
    key = hashlib.md5(json.dumps([pool.name, cfg["pool"], cfg["target_defs"], cfg["features"], list(members.index)],
                                 sort_keys=True, default=str).encode()).hexdigest()[:12]
    d = ROOT / cfg.get("feature_cache_dir", Path(cfg["cache_dir"]) / "features")
    f_tab, f_x = d / f"{pool.name}_s{seed}_{key}_tab.parquet", d / f"{pool.name}_s{seed}_{key}_X.parquet"
    if f_tab.exists() and f_x.exists():
        log(f"features from cache {f_tab.name}")
        return pd.read_parquet(f_tab), pd.read_parquet(f_x), 0.0
    t0 = time.time()
    tab, X = evaluate_members(pool, members, cfg)
    dt = time.time() - t0
    d.mkdir(parents=True, exist_ok=True)
    tab.astype({c: float for c in tab.columns if c.startswith(("hinge_inside", "at_bound"))}).to_parquet(f_tab)
    X.to_parquet(f_x)
    log(f"evaluated {len(tab)} substations in {dt:.1f}s ({dt / len(tab):.3f} s each)")
    return pd.read_parquet(f_tab), X, dt


def predictions(cfg, tab, F, y, seed, timing, log):
    """(method, anchor) -> test predictions for one target."""
    tr, te, inn = (tab["split"] == s for s in ("train", "test", "inner"))
    fit_tr, fit_in = tr & y.notna(), inn & y.notna()
    if (~y[tr | inn].notna()).any():
        log(f"  {y.name}: {int((~y[tr | inn].notna()).sum())} train/inner substations without a target (failed fit), not used for fitting")
    out = {}
    for b in cfg["physics_baselines"]:
        out[(b, "none")] = make_baseline(b).fit(tab[fit_tr], y[fit_tr]).predict(tab[te])
    ev_all, ev_by = cfg["cv"]["hyperopt"]["max_evals"], cfg["cv"]["hyperopt"].get("max_evals_by_model", {})

    def tuned(name, X, anchor, method):
        t0, ev = time.time(), ev_by.get(name, ev_all)
        m, meta, _ = tune_grouped_cv(name, X[fit_in], y[fit_in], tab.loc[fit_in, "fold"], seed, ev, X[fit_tr], y[fit_tr])
        timing.append({"split_seed": seed, "target": y.name, "method": method, "anchor": anchor, "n_evals": meta["n_evals"],
                       "seconds": time.time() - t0, "n_inner": int(fit_in.sum()), "n_train": int(fit_tr.sum())})
        log(f"  {y.name} {method}[{anchor}]: cv_mse {meta['cv_mse']:.4g}, best_iter {meta['best_iter']}, "
            f"{meta['n_evals']} evals, {time.time() - t0:.1f}s, params {meta['params']}")
        return m.predict(X[te])

    for anchor in cfg["anchors"]:
        X = feature_matrix(F, tab, anchor)
        for name in cfg["models"]:
            out[(name, anchor)] = tuned(name, X, anchor, name)
    for name in cfg["anchor_only_baselines"]["models"]:
        for cols in cfg["anchor_only_baselines"]["features"]:
            a = "+".join(cols)
            out[(f"anchor_only_{name}", a)] = tuned(name, tab[cols].astype(float), a, f"anchor_only_{name}")
    return out


def metric_rows(cfg, seed, target, te, p, members):
    """Long metric rows for one (method, anchor): overall (cell 'all') and per (penetration x size) cell."""
    y = te[target].to_numpy(float)
    ok = np.isfinite(y) & np.isfinite(p)
    cells = [("all", np.ones(len(te), bool))] + [(f"p{pp}|n{ss}", ((te["p"] == pp) & (te["size"] == ss)).to_numpy())
                                                for pp, ss in sorted(set(zip(te["p"], te["size"])))]
    rows = []
    for cell, m in cells:
        mo = ok & m
        if not mo.any():
            continue
        vals = compute_metrics(y[mo], p[mo])
        vals.update(n_pred_nan=int((m & ~np.isfinite(p)).sum()), mape_n_excluded=int((y[mo] == 0).sum()))       # F9
        if cell == "all" and cfg["uncertainty"]["bootstrap"]:
            sub = pd.DataFrame({"y": y[mo], "p": p[mo], "hp_members": members.loc[te.index[mo], "hp_members"].to_numpy()})
            for mname, fn in (("rmse", lambda d: float(np.sqrt(np.mean((d["y"] - d["p"]) ** 2)))),
                              ("r2", lambda d: compute_metrics(d["y"], d["p"])["r2"])):
                bs = cluster_bootstrap(fn, sub, B=cfg["bootstrap"]["B"], seed=seed)
                vals.update({f"{mname}_ci_lo": bs["lo"], f"{mname}_ci_hi": bs["hi"], f"{mname}_boot_sd": bs["sd"]})
            vals["boot_mean_kept"] = bs["mean_kept"]
        base = {"split_seed": seed, "target": target, "cell": cell, "n_substations": int(mo.sum()),
                "n_hp_households": len(set().union(*members.loc[te.index[mo], "hp_members"]))}
        rows += [{**base, "metric": k, "value": v} for k, v in vals.items()]
    return rows


def at_bound_rows(seed, target, tab, method, n_hp):
    """Share of net-load hockey-stick fits whose T_h sits at a bound of (8, 20) degC, on train and on test."""
    return [{"split_seed": seed, "target": target, "cell": "all", "metric": f"at_bound_share_{s}", "method": method,
             "anchor": "none", "value": float(tab.loc[tab["split"] == s, "at_bound_net"].mean()),
             "n_substations": int((tab["split"] == s).sum()), "n_hp_households": n_hp[s]} for s in ("train", "test")]


def run_seed(cfg, seed):
    """One split seed end to end -> dict of frames (runs in a worker process)."""
    configure(cfg["parallel"]["threads"], cfg.get("ffnn", {}).get("patience", 40))
    lines, t0 = [], time.time()

    def log(msg):
        lines.append(f"[s{seed} {time.time() - t0:7.1f}s] {msg}")
        print(lines[-1], flush=True)

    pool = build_pool(cfg["pool"]["option"], cfg, verbose=False)
    ds = f"{pool.name}_{cfg['pool']['year']}"
    sp = household_splits(pool.meta, [seed], cfg["split"]["test_frac"], cfg["split"]["stratify"],
                          cfg["pool"].get("shared_fill", False))[seed]
    folds = grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], seed)
    members, dropped = build_substations(pool.meta, sp, seed, cfg, folds)
    log(f"HP train/test {len(sp['train']['hp'])}/{len(sp['test']['hp'])}, fill {len(sp['train']['fill'])}/"
        f"{len(sp['test']['fill'])}; substations {members['split'].value_counts().to_dict()}; dropped cells {len(dropped)}")
    tab, F, dt = cached_eval(pool, members, cfg, seed, log)
    viol = tab["HP_CoincPeak"] > tab["HP_Peak"] + 1e-9
    diag = {"split_seed": seed, "n_substations": len(tab), "hinge_inside_net": tab["hinge_inside_net"].mean(),
            "hinge_inside_hp": tab["hinge_inside_hp"].mean(), "at_bound_net": tab["at_bound_net"].mean(),
            "coincpeak_gt_peak": int(viol.sum()), "failed_net_fit": int(tab["s_h_net"].isna().sum()),
            "failed_hp_fit": int(tab["s_h"].isna().sum())}
    timing = [{"split_seed": seed, "method": "evaluate_members", "seconds": dt, "n_substations": len(tab)}]
    te = tab.index[tab["split"] == "test"]
    n_hp = {s: len(set().union(*members.loc[tab.index[tab["split"] == s], "hp_members"])) for s in ("train", "test")}
    rows, preds = [], []
    for target in cfg["targets"]:
        for (method, anchor), pr in predictions(cfg, tab, F, tab[target], seed, timing, log).items():
            rows += [{**r, "method": method, "anchor": anchor} for r in metric_rows(cfg, seed, target, tab.loc[te], pr, members)]
            if method in PHYSICS_FIT:
                rows += at_bound_rows(seed, target, tab, method, n_hp)
            preds.append(pd.DataFrame({"sub_id": te, "target": target, "method": method, "anchor": anchor,
                                       "y": tab.loc[te, target].to_numpy(), "pred": pr, "split_seed": seed,
                                       "size": tab.loc[te, "size"].to_numpy(), "p": tab.loc[te, "p"].to_numpy()}))
    log(f"done in {time.time() - t0:.1f}s")
    return {"metrics": pd.DataFrame(rows).assign(exp_id=cfg["exp_id"], dataset=ds), "dropped": dropped,
            "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--set", nargs="*", default=[], help="dotted overrides, e.g. parallel.workers=1 split.seeds=[0,1]")
    ap.add_argument("--resume", action="store_true", help="skip seeds already written to <out_dir>/seeds/")
    a = ap.parse_args()
    cfg = set_dotted(load_config(a.config), a.set)
    par = cfg.setdefault("parallel", {})
    par.setdefault("workers", 1)
    par.setdefault("cores", os.cpu_count())
    par["threads"] = max(1, par["cores"] // par["workers"])
    out = ROOT / cfg["out_dir"]
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "seeds").mkdir(exist_ok=True)
    lines, t_start = [], time.time()

    def log(msg):
        print(msg, flush=True)
        lines.append(f"[{time.time() - t_start:7.1f}s] {msg}")

    cfg["git_commit"] = git_hash()
    (out / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    pool = build_pool(cfg["pool"]["option"], cfg)                       # builds the cache once, before the workers start
    log(f"pool {pool.name}_{cfg['pool']['year']}: {pool.meta['role'].value_counts().to_dict()}; "
        f"{par['workers']} workers x {par['threads']} threads; seeds {cfg['split']['seeds']}")
    del pool
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(par.get("blas_threads", 1))               # inherited by the spawned workers
    todo = [sd for sd in cfg["split"]["seeds"] if not (a.resume and (out / "seeds" / f"seed{sd}_metrics.csv").exists())]
    failed = {}
    with cf.ProcessPoolExecutor(par["workers"], mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(run_seed, cfg, sd): sd for sd in todo}
        for fut in cf.as_completed(futs):
            sd = futs[fut]
            try:
                res = fut.result()
            except Exception:                                           # listed, never silently dropped
                failed[sd] = traceback.format_exc()
                log(f"seed {sd} FAILED:\n{failed[sd]}")
                continue
            for k in ("metrics", "dropped", "diag", "timing", "preds"):
                res[k].to_csv(out / "seeds" / f"seed{sd}_{k}.csv", index=False)
            lines += res["log"]
            log(f"seed {sd} finished ({len(res['metrics'])} metric rows)")
    have = [sd for sd in cfg["split"]["seeds"] if (out / "seeds" / f"seed{sd}_metrics.csv").exists()]

    def merged(k):
        return pd.concat([pd.read_csv(out / "seeds" / f"seed{sd}_{k}.csv") for sd in have], ignore_index=True)

    cols = ["exp_id", "split_seed", "dataset", "target", "method", "anchor", "cell", "metric", "value",
            "n_substations", "n_hp_households"]
    merged("metrics")[cols].to_csv(out / "metrics.csv", index=False)
    for k, name in (("dropped", "dropped_cells"), ("diag", "physics_diagnostics"), ("timing", "timing"), ("preds", "predictions")):
        merged(k).to_csv(out / f"{name}.csv", index=False)
    if cfg.get("pred_figures", True):
        pr = merged("preds")
        for (target, method, anchor), g in pr.groupby(["target", "method", "anchor"]):
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.scatter(g["y"], g["pred"], s=10, alpha=0.6)
            lim = [0, float(np.nanmax([g["y"].max(), g["pred"].max()]))]
            ax.plot(lim, lim, "k--", lw=0.8)
            ax.set(xlabel=f"true {target}", ylabel="predicted", title=f"{method} [{anchor}] (test, not interpreted)")
            fig.tight_layout()
            for ext in ("png", "pdf"):
                fig.savefig(out / "figures" / f"pred_{target}_{method}_{anchor}.{ext}", dpi=120)
            plt.close(fig)
    if failed:
        log(f"FAILED seeds (no metrics): {sorted(failed)}")
    log(f"done in {time.time() - t_start:.1f}s ({len(have)} of {len(cfg['split']['seeds'])} seeds)")
    (out / "log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
