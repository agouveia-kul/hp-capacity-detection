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

03a: every prediction is a spec (method, anchor, feature_set, mode, target_transform) -- see `specs`; defaults
(feature_sets [whdd], modes [direct], target_transforms [none]) reproduce the 02b grid. `paperA.estimators` adds
Paper A's s_h / m_h (pilot = the seed's train HP households; pilots.csv, caps.csv); mode `residual` fits
z = log(y / P_hat_A) (residual.py); `paperA.cap_def_check` also scores the estimator against Paper A's capacity
definition (target HP_Peak_A); a `learning_curve` block adds metrics_lc.csv (learning_curve.py). Metrics: WAPE first.

03b: more physics rows: `paperA_corr` / `paperA_corr_all` (non-TCL-corrected s_h / m_h, s0 from TRAIN fill households
[+ the train HP households' own load]), `paperA_cal` / `paperA_corr_cal` (times exp(b), b = mean cross-fitted train
log-residual). With `paperA.crossfit` the residual targets z (and b) use pilots that are household-disjoint from the
substation (inner substation of fold k: pilot without fold k; train substation: pilot without its own HP members;
test: the full pilot). Extra cells per test substation set: Paper A's penetration bins (`pbin...`). `model_anchors`
restricts a model to given anchors. The timing table carries the inner-CV WAPE (`cv_wape`) of every tuned model.

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

from paperb import ROOT, git_hash, load_config, set_dotted  # noqa: E402
from paperb.learning_curve import lc_designs  # noqa: E402
from paperb.metrics import compute_metrics  # noqa: E402
from paperb.features_netfit import FEATURE_VERSION  # noqa: E402
from paperb.physics import (crossfit_pilot_m, household_caps, household_sensitivity, make_baseline,  # noqa: E402
                            paperA_pilots, paperA_predictions)
from paperb.pools import build_pool  # noqa: E402
from paperb.residual import log_ratio, residual_predict  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import build_substations, evaluate_members  # noqa: E402
from paperb.train import configure, feature_matrix, tune_grouped_cv  # noqa: E402
from paperb.uncertainty import cluster_bootstrap  # noqa: E402

PHYSICS_FIT = ("slope_only", "slope_base", "calibrated_delta")     # HDH uses the fixed 12 degC base: no T_h fit
PHYSICS = PHYSICS_FIT + ("hdh",)
SPEC_COLS = ["method", "anchor", "feature_set", "mode", "target_transform"]
NA = "-"
PBINS = [("pbin<=15", 0.0, 0.15), ("pbin15-35", 0.15, 0.35), ("pbin35-65", 0.35, 0.65), ("pbin>65", 0.65, np.inf)]   # Paper A (actual p)
CAL = {"paperA_cal": "paperA_sh_mh", "paperA_corr_cal": "paperA_corr"}     # calibrated estimator -> its base estimator


def paperA_estimators(cfg):
    """Paper A estimators to report; `paperA_sh_mh` (the zero-residual model) always runs with mode residual."""
    est = list(cfg.get("paperA", {}).get("estimators", []))
    return (["paperA_sh_mh"] if "residual" in cfg.get("modes", []) and "paperA_sh_mh" not in est else []) + est


def specs(cfg):
    """Every prediction of one target as (method, anchor, feature_set, mode, target_transform)."""
    out = [(b, "none", NA, NA, NA) for b in cfg["physics_baselines"]] + [(e, "none", NA, NA, NA) for e in paperA_estimators(cfg)]
    models = [m for m in cfg["models"] if m != "FFNN" or cfg.get("ffnn", {}).get("enabled", False)]
    for anchor in cfg["anchors"]:
        for fs in cfg.get("feature_sets", ["whdd"]):
            for mode in cfg.get("modes", ["direct"]):
                out += ([(m, anchor, fs, "direct", t) for t in cfg.get("target_transforms", ["none"]) for m in models
                         if not (m == "XGBoost_mono" and fs == "whdd")                   # no nf_* column: = XGBoost
                         and anchor in cfg.get("model_anchors", {}).get(m, [anchor])]
                        if mode == "direct" else [(m, anchor, fs, "residual", "log") for m in cfg["residual_models"]])
    ao = cfg["anchor_only_baselines"]
    return out + [(f"anchor_only_{m}", "+".join(c), NA, "direct", "none") for m in ao["models"] for c in ao["features"]]


def cached_eval(pool, members, cfg, seed, log):
    key = hashlib.md5(json.dumps([FEATURE_VERSION, pool.name, cfg["pool"], cfg["target_defs"], cfg["features"], sorted(cfg.get("feature_sets", ["whdd"])),
                                  list(members.index), members["hp_members"].tolist(), members["fill_members"].tolist()],
                                 sort_keys=True, default=str).encode()).hexdigest()[:12]     # 03a: memberships in the key
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


def predictions(cfg, tab, F, y, seed, timing, log, pa=None, spec_list=None):
    """spec -> test predictions for one target, plus spec -> extra count metrics. `pa`: Paper A estimates over `tab`."""
    tr, te, inn = ((tab["split"] == s).to_numpy() for s in ("train", "test", "inner"))
    fit_tr, fit_in = tr & y.notna().to_numpy(), inn & y.notna().to_numpy()
    if (~y[tr | inn].notna()).any():
        log(f"  {y.name}: {int((~y[tr | inn].notna()).sum())} train/inner substations without a target (failed fit), not used for fitting")
    ev_all, ev_by = cfg["cv"]["hyperopt"]["max_evals"], cfg["cv"]["hyperopt"].get("max_evals_by_model", {})
    pa_target = cfg.get("paperA", {}).get("target", "HP_Peak")
    yv, out, extra, Xc = y.to_numpy(float), {}, {}, {}

    def tuned(spec, name, X, yt, m_in, m_tr, opts=None, space=None, eval_on=None):
        t0, ev = time.time(), ev_by.get(name, ev_all)
        y_kw, p_base = eval_on if eval_on is not None else (yv, None)              # direct models: yt is y itself
        m, meta, _ = tune_grouped_cv(name, X[m_in], yt[m_in], tab.loc[m_in, "fold"], seed, ev, X[m_tr], yt[m_tr], opts, space,
                                     (y_kw[m_in], None if p_base is None else p_base[m_in]))
        timing.append({"split_seed": seed, "target": y.name, **dict(zip(SPEC_COLS, spec)), "n_evals": meta["n_evals"],
                       "seconds": time.time() - t0, "n_inner": int(m_in.sum()), "n_train": int(m_tr.sum()),
                       "cv_wape": meta["cv_wape"]})
        log(f"  {y.name} {'/'.join(spec)}: cv_mse {meta['cv_mse']:.4g}, cv_wape {meta['cv_wape']:.1f}, best_iter {meta['best_iter']}, "
            f"{meta['n_evals']} evals, {time.time() - t0:.1f}s, params {meta['params']}")
        return m.predict(X[te])

    for spec in spec_list or specs(cfg):
        method, anchor, fs, mode, tt = spec
        if (method.startswith("paperA_") or mode == "residual") and y.name != pa_target:
            continue                                                    # s_h / m_h estimates HP_Peak only
        if method in PHYSICS:
            out[spec] = make_baseline(method).fit(tab[fit_tr], y[fit_tr]).predict(tab[te])
        elif method in CAL:                                              # P_hat * exp(b), b = mean cross-fitted train z
            p, valid, _ = pa[CAL[method]]
            p_cf, v_cf = pa.get("cf", {}).get(CAL[method], (p, valid))
            z = log_ratio(yv, p_cf, v_cf)
            use = fit_tr & np.isfinite(z)
            b = float(z[use].mean())
            out[spec] = np.where(valid[te], p[te] * np.exp(b), 0.0)
            extra[spec] = {"n_invalid": int((~valid[te]).sum()), "cal_b": b, "n_cal_train": int(use.sum())}
        elif method.startswith("paperA_"):
            p, valid, fb = pa[method]
            out[spec], extra[spec] = p[te], {"n_invalid": int((~valid[te]).sum()), "n_station_fallback": int(fb[te].sum())}
        elif method.startswith("anchor_only_"):
            out[spec] = tuned(spec, method[12:], tab[anchor.split("+")].astype(float), yv, fit_in, fit_tr)
        else:
            if (anchor, fs) not in Xc:
                Xc[anchor, fs] = feature_matrix(F, tab, anchor, fs)
            X = Xc[anchor, fs]
            if mode == "direct":
                out[spec] = tuned(spec, method, X, yv, fit_in, fit_tr, {"target_transform": tt})
            else:
                p, valid = pa.get("cf", {}).get("paperA_sh_mh", pa["paperA_sh_mh"][:2])      # cross-fitted (03b Task 3)
                out[spec], c = residual_predict(lambda *a, **k: tuned(spec, *a, **k), method, X, yv, p, valid, fit_in, fit_tr, te)
                extra[spec] = {"n_invalid": int((~valid[te]).sum()), **c}
    return out, extra


def metric_rows(cfg, seed, target, te, p, members, extra=None):
    """Long metric rows for one (method, anchor): overall (cell 'all') and per (penetration x size) cell."""
    y = te[target].to_numpy(float)
    ok = np.isfinite(y) & np.isfinite(p)
    pen = (te["HP_Count"] / te["size"]).to_numpy(float)               # actual penetration (n_hp is rounded), Paper A's bins
    cells = ([("all", np.ones(len(te), bool))] + [(c, (pen > lo) & (pen <= hi) if lo > 0 else pen <= hi) for c, lo, hi in PBINS]
             + [(f"p{pp}|n{ss}", ((te["p"] == pp) & (te["size"] == ss)).to_numpy()) for pp, ss in sorted(set(zip(te["p"], te["size"])))])
    rows = []
    for cell, m in cells:
        mo = ok & m
        if not mo.any():
            continue
        vals = compute_metrics(y[mo], p[mo])
        vals.update(n_pred_nan=int((m & ~np.isfinite(p)).sum()), mape_n_excluded=int((y[mo] == 0).sum()))       # F9
        if cell == "all":
            vals.update(extra or {})
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


def at_bound_rows(seed, target, tab, spec, n_hp):
    """Share of net-load hockey-stick fits whose T_h sits at a bound of (8, 20) degC, on train and on test."""
    return [{"split_seed": seed, "target": target, "cell": "all", "metric": f"at_bound_share_{s}", **dict(zip(SPEC_COLS, spec)),
             "value": float(tab.loc[tab["split"] == s, "at_bound_net"].mean()),
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
    rows, preds, pilots, lc_rows, lc_dropped = [], [], [], [], []
    pac, pa = cfg.get("paperA", {}), None
    min_st = pac.get("min_station_pilot", 10)

    def pilot_estimates(t, train_hp, caps, mem, fold_of, **tag):
        """Paper A estimates for the substations of `t` (memberships `mem`, household folds `fold_of`): pilot of
        `train_hp`, per-dwelling non-TCL slopes s0 (train fill [+ own load of train_hp]) and cross-fitted m_h."""
        full, by_st = paperA_pilots(pool, train_hp, caps, min_st)
        pilots.extend({"split_seed": seed, **tag, "pilot": k, **v} for k, v in [("all", full), *sorted(by_st.items())])
        s0 = {k: household_sensitivity(pool, sp["train"]["fill"], own, pac.get("fill_station", "KLO"))
              for k, own in (("paperA_corr", ()), ("paperA_corr_all", train_hp))}
        pilots.extend({"split_seed": seed, **tag, "pilot": f"s0:{k}", "s0": v["s0"], "s_h": v["s_h"], "T_h": v["T_h"],
                       "n_hh": v["N"]} for k, v in s0.items())
        m_cf = None
        if pac.get("crossfit", False):
            m_ser, fold_m = crossfit_pilot_m(pool, train_hp, caps, fold_of, mem.loc[t.index], full["m"])
            m_cf = m_ser.to_numpy()
            pilots.extend({"split_seed": seed, **tag, "pilot": f"cf:fold{k}", "m": v, "n_hh": len([h for h in train_hp if fold_of[h] != k])}
                           for k, v in fold_m.items())
        return paperA_predictions(t, full, by_st, {k: v["s0"] for k, v in s0.items()}, m_cf)

    if paperA_estimators(cfg) or cfg.get("learning_curve"):
        caps = household_caps(pool, pac.get("cap_def", "hp_peak"))
        pa = pilot_estimates(tab, sp["train"]["hp"], caps, members, folds, cap_def=pac.get("cap_def", "hp_peak"), n="main", lc_draw=-1)
        log(f"Paper A pilot m_h {pilots[0]['m']:.5f} ({pilots[0]['n_hh']} train HP households); station pilots "
            f"{ {r['pilot']: round(r['m'], 5) for r in pilots[1:] if r['pilot'] in pool.temp.columns} }; s0 "
            f"{ {r['pilot'][3:]: round(r['s0'], 5) for r in pilots if r['pilot'].startswith('s0:')} }; cross-fit fold m_h "
            f"{ [round(r['m'], 5) for r in pilots if r['pilot'].startswith('cf:')] }")

    def score(target, t, pr_all, mem, extra_rows=None, **tag):
        for spec, pr in pr_all[0].items():
            out = [{**r, **dict(zip(SPEC_COLS, spec)), **tag} for r in metric_rows(cfg, seed, target, t.loc[te], pr, mem, pr_all[1].get(spec))]
            (lc_rows if tag else rows).extend(out)
            if extra_rows is not None:
                extra_rows(spec, pr)

    for target in cfg["targets"]:
        def keep(spec, pr, target=target):
            if spec[0] in PHYSICS_FIT:
                rows.extend(at_bound_rows(seed, target, tab, spec, n_hp))
            preds.append(pd.DataFrame({"sub_id": te, "target": target, **dict(zip(SPEC_COLS, spec)),
                                       "y": tab.loc[te, target].to_numpy(), "pred": pr, "split_seed": seed,
                                       "size": tab.loc[te, "size"].to_numpy(), "p": tab.loc[te, "p"].to_numpy()}))
        score(target, tab, predictions(cfg, tab, F, tab[target], seed, timing, log, pa), members, keep)
    if pac.get("cap_def_check"):                                        # Paper A's own capacity definition (eq. pk)
        caps_a = household_caps(pool, "paperA")
        tab["HP_Peak_A"] = members.loc[tab.index, "hp_members"].map(lambda h: float(caps_a[list(h)].sum()))
        pa_a = pilot_estimates(tab, sp["train"]["hp"], caps_a, members, folds, cap_def="paperA", n="main", lc_draw=-1)
        spl = [(e, "none", NA, NA, NA) for e in paperA_estimators(cfg) if e in ("paperA_sh_mh", "paperA_sh_mh_station")]
        score("HP_Peak_A", tab, predictions({**cfg, "paperA": {**pac, "target": "HP_Peak_A"}}, tab, F, tab["HP_Peak_A"],
                                            seed, timing, log, pa_a, spl), members)
    if cfg.get("learning_curve"):
        spl = [tuple(x.split("|")) for x in cfg["learning_curve"]["specs"]]
        for n, draw, sub, mem, dr in lc_designs(cfg, pool.meta, sp, seed, members.loc[te]):
            lc_dropped += dr
            if mem is None:
                log(f"learning curve n={n} draw={draw}: skipped ({dr[0]['reason']})")
                continue
            k = len(timing)
            cfg_l = {**cfg, "feature_sets": cfg["learning_curve"].get("feature_sets", cfg.get("feature_sets", ["whdd"]))}
            t_l, F_l, dt_l = cached_eval(pool, mem[mem["split"] != "test"], cfg_l, seed, log)
            timing.append({"split_seed": seed, "method": "evaluate_members", "seconds": dt_l, "n_substations": len(t_l)})
            t_l, F_l = pd.concat([t_l, tab.loc[te, t_l.columns]]), pd.concat([F_l, F.loc[te, F_l.columns]])
            fold_l = grouped_inner_folds({"hp": sub, "fill": sp["train"]["fill"]}, pool.meta, cfg["cv"]["k"], seed)
            pa_l = pilot_estimates(t_l, sub, caps, mem, fold_l, cap_def=pac.get("cap_def", "hp_peak"), n=len(sub), lc_draw=draw)
            log(f"learning curve n={n} draw={draw}: {len(sub)} train HP households, {len(dr)} dropped cells")
            for target in cfg["targets"]:
                score(target, t_l, predictions(cfg, t_l, F_l, t_l[target], seed, timing, log, pa_l, spl), mem,
                      n_train_hp=len(sub), lc_draw=draw)
            for r in timing[k:]:
                r.update(n_train_hp=len(sub), lc_draw=draw)
    log(f"done in {time.time() - t0:.1f}s")
    return {"metrics": pd.DataFrame(rows).assign(exp_id=cfg["exp_id"], dataset=ds), "dropped": dropped,
            "diag": pd.DataFrame([diag]), "timing": pd.DataFrame(timing), "preds": pd.concat(preds), "log": lines,
            "pilots": pd.DataFrame(pilots), "lc": pd.DataFrame(lc_rows).assign(exp_id=cfg["exp_id"], dataset=ds),
            "lc_dropped": pd.DataFrame(lc_dropped)}


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
            for k in ("metrics", "dropped", "diag", "timing", "preds", "pilots", "lc", "lc_dropped"):
                if len(res[k]):
                    res[k].to_csv(out / "seeds" / f"seed{sd}_{k}.csv", index=False)
            lines += res["log"]
            log(f"seed {sd} finished ({len(res['metrics'])} metric rows)")
    have = [sd for sd in cfg["split"]["seeds"] if (out / "seeds" / f"seed{sd}_metrics.csv").exists()]

    def merged(k):
        fs = [out / "seeds" / f"seed{sd}_{k}.csv" for sd in have if (out / "seeds" / f"seed{sd}_{k}.csv").exists()]
        return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()

    cols = ["exp_id", "split_seed", "dataset", "target", *SPEC_COLS, "cell", "metric", "value", "n_substations", "n_hp_households"]
    merged("metrics")[cols].to_csv(out / "metrics.csv", index=False)
    for k, name in (("dropped", "dropped_cells"), ("diag", "physics_diagnostics"), ("timing", "timing"), ("preds", "predictions"),
                    ("pilots", "pilots"), ("lc_dropped", "dropped_cells_lc")):
        if len(m := merged(k)):
            m.to_csv(out / f"{name}.csv", index=False)
    if len(m := merged("lc")):
        m[cols[:4] + ["n_train_hp", "lc_draw"] + cols[4:]].to_csv(out / "metrics_lc.csv", index=False)
    if paperA_estimators(cfg):
        pool = build_pool(cfg["pool"]["option"], cfg, verbose=False)
        caps = pd.DataFrame({"station": pool.meta.loc[pool.hp.columns, "station"], "hp_peak": household_caps(pool, "hp_peak"),
                             "cap_paperA": household_caps(pool, "paperA")}).rename_axis("hh")
        caps.assign(rel_diff=caps["cap_paperA"] / caps["hp_peak"] - 1).to_csv(out / "caps.csv")
    if cfg.get("pred_figures", True):
        pr = merged("preds")
        for (target, method, anchor, fs, mode, tt), g in pr.groupby(["target", *SPEC_COLS]):
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.scatter(g["y"], g["pred"], s=10, alpha=0.6)
            lim = [0, float(np.nanmax([g["y"].max(), g["pred"].max()]))]
            ax.plot(lim, lim, "k--", lw=0.8)
            ax.set(xlabel=f"true {target}", ylabel="predicted", title=f"{method} [{anchor}] {fs}/{mode}/{tt} (test, not interpreted)")
            fig.tight_layout()
            for ext in ("png", "pdf"):
                fig.savefig(out / "figures" / f"pred_{target}_{method}_{anchor}_{fs}_{mode}_{tt}.{ext}".replace("_-", ""), dpi=120)
            plt.close(fig)
    if failed:
        log(f"FAILED seeds (no metrics): {sorted(failed)}")
    log(f"done in {time.time() - t_start:.1f}s ({len(have)} of {len(cfg['split']['seeds'])} seeds)")
    (out / "log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
