"""Change evaluator (iteration 08, Task 2; iterations/08-change-detection.md, DECISIONS.md 2026-11-18).

One seed: the paired feeders of change_feeders.py, both years evaluated with the 06 feature pipeline (`cached_eval`; year 1 =
the 06 A-GB arm config, pool 2122r3; year 2 = the 06 R(ii) arm config, pool 2223r3; each pool on its own analog map of seed
s), and the estimators applied to both years with the same model (nothing is fitted):
- E1 / E4: the persisted 06 A-GB TabPFN rung winners of seed s, L2 / L1 (persist.load_model, unchanged; direct-log);
- E2: paperA_corr = max(s_h(net) - N s0, 0) / m_h, s0 = the local s0 of that year: per weather group, the seed's train fillers
  under the group's analog map of that year (AnalogFill.s0; label-free); m_h = the year-1 train pilot of 06 (pilots.csv 'all');
- E3: paperA_sh_mh = s_h(net) / m_h, same m_h, no s0 correction.
Invalid Paper A bases give P_hat = 0 (Paper A's convention, counted in diag). dhat = P_hat2 - P_hat1 (kW).
`run_seed` (queue runner) returns predictions and labels per feeder and estimator, the feeder memberships, dropped cells, the
local s0 per year and validity counts. It computes no detection or error metric: `thresholds` / `flags` (two-fold
cross-calibration) are used by the report script and the tests only. Family physics -> E2, E3 (cfg models empty);
a family with models [E1, E4] -> those (TabPFN).
"""
import time

import numpy as np
import pandas as pd

from paperb import ROOT, load_config
from paperb.change_feeders import build_feeders, year_members
from paperb.persist import load_model
from paperb.physics import paperA_corrected, paperA_estimate
from paperb.pools import build_pool
from paperb.run_benchmark import cached_eval
from paperb.train import configure, feature_matrix
from paperb.transfer import source_numbers

DIR06_MODELS = ROOT / "results" / "iter06_hybrid_ladder" / "models" / "a_gb"
ML = {"E1": "L2", "E4": "L1"}                       # frozen 06 A-GB TabPFN rung winners (family folder `neural`)
PHYS = ("E2", "E3")
KEY = ["split_seed", "estimator", "N"]


def year_pool(path, seed):
    cfg = load_config(path)
    pool = build_pool(cfg["pool"]["option"], cfg, verbose=False)
    pool.analog.set_seed(seed)
    return pool, cfg


def local_s0(pool, train_fill, stations):
    """{weather group: per-dwelling s0} of the train fillers under each group's analog map of this pool (year)."""
    return {st: v["s0"] for st, v in pool.analog.s0(train_fill, pool.index, pool.temp, sorted(stations)).items()}


def physics_estimates(tab, s0, m):
    """{E2, E3: (P_hat, valid)} on the rows of `tab` (one year)."""
    s0_row = tab["station"].map(s0).to_numpy(float)
    return {"E2": paperA_corrected(tab["s_h_net"], tab["size"], s0_row, m), "E3": paperA_estimate(tab["s_h_net"], m)}


def ml_estimates(tab, F, seed, names, models_dir=DIR06_MODELS, device="cpu"):
    """{name: (P_hat, valid)} of the frozen models; -> also {name: spec} for the log."""
    out, specs = {}, {}
    for name in names:
        m, man = load_model(models_dir / ML[name] / f"s{seed}" / "neural", device)
        spec = man["spec"].split("|")
        if man["residual"] or spec[3] != "direct" or spec[0] != "TabPFN":
            raise ValueError(f"{name} seed {seed}: expected a direct TabPFN winner, got {man['spec']}")
        p = np.asarray(m.predict(feature_matrix(F, tab, spec[1], spec[2])[man["feature_columns"]]), float)
        out[name], specs[name] = (p, np.isfinite(p)), man["spec"]
    return out, specs


def run_seed(cfg, seed):
    """One (seed, family) queue job -> {preds, feeders, dropped, pilots, diag, timing, log}."""
    configure(cfg["parallel"]["threads"], device=cfg.get("device", "cpu"))
    cc, lines, t0 = cfg["change"], [], time.time()

    def log(msg):
        lines.append(f"[s{seed} {time.time() - t0:7.1f}s] {msg}")
        print(lines[-1], flush=True)

    (p1, c1), (p2, c2) = year_pool(cc["year1"], seed), year_pool(cc["year2"], seed)
    for c in (c1, c2):                                                  # tests: a fresh feature cache
        c.update({"feature_cache_dir": cc["feature_cache_dir"]} if cc.get("feature_cache_dir") else {})
    F, dropped, info = build_feeders(p1.meta, p2.meta, seed, cc, c1["split"])
    log(f"{len(F)} feeders, {len(dropped)} dropped cells; {info['n_test_hp_both_years']} of {info['n_test_hp_06']} test HP homes in both years")
    names = list(cfg.get("models") or PHYS)
    m_h = source_numbers("a_gb", seed)["m"]
    est, pil, timing, diag = {}, [], [], []
    for y, pool, c in ((1, p1, c1), (2, p2, c2)):
        mem = year_members(F, y)
        t1 = time.time()
        tab, X, dt = cached_eval(pool, mem, c, seed, log)
        tab.index = F.index
        X.index = F.index
        timing += [{"split_seed": seed, "method": k, "step": f"evaluate_y{y}", "seconds": dt, "n_substations": len(tab)} for k in names]
        if set(names) & set(PHYS):
            s0 = local_s0(pool, info["train_fill"], set(tab["station"]))
            pil += [{"split_seed": seed, "year": y, "station": st, "s0": v, "m_h": m_h} for st, v in s0.items()]
            est[y] = physics_estimates(tab, s0, m_h)
        else:
            est[y], specs = ml_estimates(tab, X, seed, names, ROOT / cc.get("models_dir", DIR06_MODELS), cfg.get("device", "cpu"))
            log(f"year {y}: {specs}")
        timing += [{"split_seed": seed, "method": k, "step": f"estimate_y{y}", "seconds": time.time() - t1, "n_substations": len(tab)} for k in names]
        for k in names:                                                 # `method` = estimator: the queue keeps a family's own rows
            diag.append({"split_seed": seed, "year": y, "method": k, "estimator": k, "n_feeders": len(tab), "n_invalid": int((~est[y][k][1]).sum()),
                         "n_pred_nan": int((~np.isfinite(est[y][k][0])).sum()), "n_net_fit_failed": int(tab["s_h_net"].isna().sum())})
    lab = F[["split_seed", "half", "station", "station2", "N", "p1", "dp", "k1", "dk", "rep", "C1", "C2", "dC_added", "dC_total"]]
    preds = pd.concat([lab.assign(method=k, estimator=k, P1=est[1][k][0], P2=est[2][k][0], valid1=est[1][k][1], valid2=est[2][k][1])
                       for k in names]).rename_axis("feeder_id").reset_index()
    preds["dhat"] = preds["P2"] - preds["P1"]
    feeders = F.assign(**{c: F[c].map(";".join) for c in ("hp1", "hp_new", "fill")}).rename_axis("feeder_id").reset_index()
    info = {k: v for k, v in info.items() if k not in ("train_fill", "half")}
    log(f"done: {len(preds)} prediction rows ({names})")
    return {"preds": preds, "feeders": feeders, "dropped": dropped, "pilots": pd.DataFrame(pil),
            "diag": pd.DataFrame(diag).assign(**info), "timing": pd.DataFrame(timing), "log": lines}


def thresholds(preds, q=0.95):
    """tau per (seed, estimator, N, calibration half) = the q-quantile (numpy linear interpolation) of dhat on that half's null
    feeders (dp = 0). Report script and tests only."""
    null = preds[preds["dp"] == 0]
    return null.groupby(KEY + ["half"])["dhat"].quantile(q).rename("tau").reset_index().rename(columns={"half": "calib_half"})


def flags(preds, tau):
    """Each feeder of evaluation half h is flagged with the tau of calibration half 1 - h (same seed, estimator, N): an
    evaluation half never contributes to its own threshold. Feeders whose (seed, estimator, N) has no tau get NaN."""
    out = preds.assign(calib_half=1 - preds["half"]).merge(tau, on=KEY + ["calib_half"], how="left")
    out["flag"] = np.where(out["tau"].notna(), out["dhat"] > out["tau"], np.nan)
    return out
