"""Protocol v1 benchmark runner. Writes results/<exp_id>/ in the CLAUDE.md s.8 format.

Per split seed: household split -> inner folds -> memberships (train, test, inner) -> targets, physics and
windowed features (cached in data/_paperb/features/) -> physics baselines, anchor-only baselines and ML
models (grouped-CV tuning on inner substations, refit on train) -> test metrics with household-cluster
bootstrap CIs.

    python scripts/paperb/run_benchmark.py --config configs/protocol_v1_quick.yaml
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from hp_capacity import compute_metrics  # noqa: E402
from paperb import ROOT, git_hash, load_config  # noqa: E402
from paperb.physics import make_baseline  # noqa: E402
from paperb.pools import build_pool  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import build_substations, evaluate_members  # noqa: E402
from paperb.train import feature_matrix, tune_grouped_cv  # noqa: E402
from paperb.uncertainty import cluster_bootstrap  # noqa: E402


def cached_eval(pool, members, cfg, seed, log):
    key = hashlib.md5(json.dumps([pool.name, cfg["pool"], cfg["target_defs"], cfg["features"], list(members.index)],
                                 sort_keys=True, default=str).encode()).hexdigest()[:12]
    d = ROOT / cfg["cache_dir"] / "features"
    f_tab, f_x = d / f"{pool.name}_s{seed}_{key}_tab.parquet", d / f"{pool.name}_s{seed}_{key}_X.parquet"
    if f_tab.exists() and f_x.exists():
        log(f"seed {seed}: features from cache {f_tab.name}")
        return pd.read_parquet(f_tab), pd.read_parquet(f_x), 0.0
    t0 = time.time()
    tab, X = evaluate_members(pool, members, cfg)
    dt = time.time() - t0
    d.mkdir(parents=True, exist_ok=True)
    tab.astype({c: float for c in tab.columns if c.startswith(("hinge_inside", "at_bound"))}).to_parquet(f_tab)
    X.to_parquet(f_x)
    log(f"seed {seed}: evaluated {len(tab)} substations in {dt:.1f}s ({dt / len(tab):.3f} s each)")
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
    ev = cfg["cv"]["hyperopt"]["max_evals"]

    def tuned(name, X, anchor, method):
        t0 = time.time()
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


def metric_rows(cfg, exp_id, dataset, seed, target, y, p, members, B):
    ok = np.isfinite(y) & np.isfinite(p)
    sub = pd.DataFrame({"y": y[ok], "p": p[ok], "hp_members": members.loc[y.index[ok], "hp_members"]})
    base = {"exp_id": exp_id, "split_seed": seed, "dataset": dataset, "target": target,
            "n_substations": int(ok.sum()), "n_hp_households": len(set().union(*sub["hp_members"]))}
    vals = compute_metrics(sub["y"], sub["p"])
    vals.update(n_pred_nan=int((~np.isfinite(p)).sum()), mape_n_excluded=int((sub["y"] == 0).sum()))  # F9
    for m in ("rmse", "r2"):
        fn = {"rmse": lambda d: float(np.sqrt(np.mean((d["y"] - d["p"]) ** 2))),
              "r2": lambda d: compute_metrics(d["y"], d["p"])["r2"]}[m]
        bs = cluster_bootstrap(fn, sub, B=B, seed=seed)
        vals.update({f"{m}_ci_lo": bs["lo"], f"{m}_ci_hi": bs["hi"], f"{m}_boot_sd": bs["sd"]})
    vals["boot_mean_kept"] = bs["mean_kept"]
    return [{**base, "metric": k, "value": v} for k, v in vals.items()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = load_config(ap.parse_args().config)
    out = ROOT / cfg["out_dir"]
    (out / "figures").mkdir(parents=True, exist_ok=True)
    lines, t_start = [], time.time()

    def log(msg):
        print(msg, flush=True)
        lines.append(f"[{time.time() - t_start:7.1f}s] {msg}")

    cfg["git_commit"] = git_hash()
    (out / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    pool = build_pool(cfg["pool"]["option"], cfg)
    ds = f"{pool.name}_{cfg['pool']['year']}"
    log(f"pool {ds}: {pool.meta['role'].value_counts().to_dict()} (load {time.time() - t_start:.1f}s)")
    splits = household_splits(pool.meta, cfg["split"]["seeds"], cfg["split"]["test_frac"], cfg["split"]["stratify"])
    rows, dropped_all, diag, timing, preds_all = [], [], [], [], []
    for seed in cfg["split"]["seeds"]:
        sp = splits[seed]
        folds = grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], seed)
        members, dropped = build_substations(pool.meta, sp, seed, cfg, folds)
        dropped_all.append(dropped)
        log(f"seed {seed}: HP train/test {len(sp['train']['hp'])}/{len(sp['test']['hp'])}, fill {len(sp['train']['fill'])}/"
            f"{len(sp['test']['fill'])}; substations {members['split'].value_counts().to_dict()}; dropped cells {len(dropped)}")
        tab, F, dt = cached_eval(pool, members, cfg, seed, log)
        timing.append({"split_seed": seed, "method": "evaluate_members", "seconds": dt, "n_substations": len(tab)})
        viol = tab["HP_CoincPeak"] > tab["HP_Peak"] + 1e-9
        diag.append({"split_seed": seed, "n_substations": len(tab), "hinge_inside_net": tab["hinge_inside_net"].mean(),
                     "hinge_inside_hp": tab["hinge_inside_hp"].mean(), "at_bound_net": tab["at_bound_net"].mean(),
                     "coincpeak_gt_peak": int(viol.sum()), "failed_net_fit": int(tab["s_h_net"].isna().sum()),
                     "failed_hp_fit": int(tab["s_h"].isna().sum())})
        if viol.any():
            log(f"seed {seed}: FLAG HP_CoincPeak > HP_Peak in {int(viol.sum())} substations (robust 99.9 % peaks)")
        te = tab.index[tab["split"] == "test"]
        for target in cfg["targets"]:
            for (method, anchor), p in predictions(cfg, tab, F, tab[target], seed, timing, log).items():
                for r in metric_rows(cfg, cfg["exp_id"], ds, seed, target, tab.loc[te, target], p, members, cfg["bootstrap"]["B"]):
                    rows.append({**r, "method": method, "anchor": anchor})
                preds_all.append(pd.DataFrame({"sub_id": te, "target": target, "method": method, "anchor": anchor,
                                               "y": tab.loc[te, target].to_numpy(), "pred": p, "split_seed": seed}))
    cols = ["exp_id", "split_seed", "dataset", "target", "method", "anchor", "metric", "value", "n_substations", "n_hp_households"]
    pd.DataFrame(rows)[cols].to_csv(out / "metrics.csv", index=False)
    pd.concat(dropped_all).to_csv(out / "dropped_cells.csv", index=False)
    pd.DataFrame(diag).to_csv(out / "physics_diagnostics.csv", index=False)
    pd.DataFrame(timing).to_csv(out / "timing.csv", index=False)
    pr = pd.concat(preds_all)
    pr.to_csv(out / "predictions.csv", index=False)
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
    log(f"done in {time.time() - t_start:.1f}s")
    (out / "log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
