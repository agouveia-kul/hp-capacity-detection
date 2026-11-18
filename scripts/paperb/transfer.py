"""Transfer evaluator (iteration 07, Task 2; iterations/07-transfer-validation.md, CLAUDE.md s4 transfer protocol).

Source seed s -> target seed s (`transfer: {source, target}` = 06 arm names a_ch / a_gb). Nothing is fitted on the target:
- target inputs: the target's 06 A-arm test substations (memberships rebuilt as run_benchmark.run_seed builds them), evaluated
  with the 06 feature pipeline (identical kwargs in both pools; holiday calendar = the target pool's). GB->CH: the CH pool's
  series are averaged to 30 min first (`at_30min`, pool name bstar30, its own feature cache). The CNN's daily series are
  reordered to the source's calendar by (month, day) (`doy_perm`; both windows have 365 days and no 29 February).
- ML rungs L1-L3: the persisted 06 rung winners (persist.load_model, unchanged). L4: L4a only, from the 07 refit directory
  (Task 3; `transfer.models_dir`) where 06 kept L4b, else the 06 winner (must be l4a; a round trip also takes an l4b winner through its scale.joblib).
- source quantities, from the source seed's 06 pilots.csv / metrics.csv (computed on the source train set in 06): pilot m_h,
  kappa (L4a), m_h' (paperA_corr_own, CH only), s0 per station (GB) or one s0 (CH; KLO fillers), cal_b of paperA_cal /
  paperA_corr_cal. s0 of a target row: the source's s0 of that station, else the source's median s0 (`s0:paperA_corr`).
  The four physics_baselines maps are refit on the source train substations (native label), as 06 did.
- bases on the target: L3 / paperA_sh_mh = s_h(net) / m_h; L4a / paperA_l4a = max(s_h(net) - N s0, 0) / (kappa / (T_h(net) - T_design)),
  T_design = the TARGET pool's (site metadata).
- labels: HL and the target's native label (labels_hl.py); c_src = median over the source seed's train substations of HL / native.
- secondary rows (label-free domain adaptation, outside the rules): `paperA_corr@tgt_s0` (s0 from the target's train fillers,
  the target's 06 pilots.csv); `paperA_corr_own` CH->GB only (GB has no whole-house meters: listed as n/a in `diag`).
Output: `preds` in the 06 format plus `direction` and `label_def` (HL: pred = c_src * y_hat, y = HL; HL_uncorrected: y_hat vs HL;
native: y_hat vs the target's native label) and `diag` (validity counts only: NaN predictions, invalid bases, load errors).
No error metric is computed here. `transfer.roundtrip: true` (test c) scores a pool's models on its own 06 test set: c = 1,
label_def native, the 15-min CH pool.

Queue runner: `runner: paperb.transfer:run_seed`; the job's family selects the rungs (cfg models / residual_models -> families,
cfg modes -> rungs: direct L1 + L2, residual L3, l4a L4); the physics family (physics_baselines non-empty) gives the L0 rows.
"""
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from paperb import ROOT, load_config
from paperb.labels_hl import household_caps, substation_labels
from paperb.lc_fit import FAMILY_OF
from paperb.models_rawseries import RAW_DAYS, RAW_PREFIX
from paperb.persist import load_model
from paperb.physics import make_baseline, paperA_corrected, paperA_estimate
from paperb.pools import Pool, build_pool
from paperb.residual import compose
from paperb.run_benchmark import NA, PHYSICS, cached_eval
from paperb.scale_model import Scale, climate, covariates, estimate, rung
from paperb.splits import grouped_inner_folds, household_splits
from paperb.substations import build_substations
from paperb.train import configure, feature_matrix

DIR06 = ROOT / "results" / "iter06_hybrid_ladder"
DIR07_MODELS = ROOT / "results" / "iter07_transfer" / "models"
POOL_OF = {"a_ch": "CH", "a_gb": "GB"}
RUNGS_OF_MODE = {"direct": ("L1", "L2"), "residual": ("L3",), "l4a": ("L4",)}


def arm_cfg(arm):
    return load_config(f"configs/iter06_{arm}.yaml")


def at_30min(pool):
    """The pool with every series averaged to 30 min (mean of the two 15-min values); labels stay in meta (native)."""
    r = lambda d: d.astype(np.float64).resample("30min").mean()      # noqa: E731  float64: daily means equal the 15-min ones
    return Pool(f"{pool.name}30", r(pool.hp), r(pool.own), r(pool.fill), r(pool.temp), pool.meta)


def side(arm, seed, at30=False, test_only=False, log=print):
    """One pool and seed: pool, cfg, memberships, tab and features (06 caches), household HL caps."""
    cfg = arm_cfg(arm)
    pool = build_pool(cfg["pool"]["option"], cfg, verbose=False)
    if pool.analog is not None:                                         # GB: the seed's analog-day map (part of the cache key)
        pool.analog.set_seed(seed)
    caps = household_caps(pool, cfg)
    if at30:
        pool, cfg = at_30min(pool), {**cfg, "pool": {**cfg["pool"], "resample_min": 30}}     # own cache key
    sp = household_splits(pool.meta, [seed], cfg["split"]["test_frac"], cfg["split"]["stratify"], cfg["pool"].get("shared_fill", False))[seed]
    mem = build_substations(pool.meta, sp, seed, cfg, grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], seed))[0]
    tab, F, _ = cached_eval(pool, mem[mem["split"] == "test"] if test_only else mem, cfg, seed, log)
    return {"arm": arm, "pool": pool, "cfg": cfg, "members": mem, "tab": tab, "F": F, "caps": caps}


def source_numbers(arm, seed):
    """The source seed's 06 pilot quantities (pilots.csv, physics job) and calibration constants (metrics.csv)."""
    P = pd.read_csv(DIR06 / arm / "pilots.csv")
    P = P[(P["split_seed"] == seed) & (P["n"].astype(str) == "main") & (P["cap_def"] == "hp_peak") & (P["family"] == "physics")].set_index("pilot")
    M = pd.read_csv(DIR06 / arm / "metrics.csv", usecols=["split_seed", "method", "cell", "metric", "value"])
    M = M[(M["split_seed"] == seed) & (M["metric"] == "cal_b") & (M["cell"] == "all")].groupby("method")["value"].first()
    s0map = {k.split(":", 1)[1]: v for k, v in P["s0"].items() if k.startswith("s0map:")}
    return {"m": float(P.at["all", "m"]), "m_own": float(P.at["own", "m"]) if "own" in P.index else np.nan,
            "kappa": float(P.at["l4", "l4a_kappa"]), "s0_med": float(P.at["s0:paperA_corr", "s0"]), "s0_map": s0map,
            "cal_b": M.to_dict()}


def s0_rows(tab, nums):
    return tab["station"].map(nums["s0_map"]).fillna(nums["s0_med"]).to_numpy(float)


def doy_perm(src_start, tgt_start, n=RAW_DAYS):
    """perm[i] = the target day index with the (month, day) of the source's day i."""
    md = lambda s: [(d.month, d.day) for d in pd.date_range(pd.Timestamp(s).normalize(), periods=n, freq="D")]   # noqa: E731
    pos = {k: j for j, k in enumerate(md(tgt_start))}
    return np.array([pos[k] for k in md(src_start)])


def align_days(X, perm):
    """Reorder the CNN's daily columns rs_y_* / rs_T_* by `perm` (identity when the calendars agree)."""
    X = X.copy()
    for ch in ("y", "T"):
        cols = [f"{RAW_PREFIX}{ch}_{i:03d}" for i in range(len(perm))]
        if cols[0] in X:
            X[cols] = X[cols].to_numpy()[:, perm]
    return X


def bases(tab, nums, t_design, temp):
    """Paper A base (L3) and L4a base on target rows with the source's numbers -> {name: (P_hat, valid)}."""
    C = covariates(tab, s0_rows(tab, nums), climate(temp), t_design)
    return {"paperA_sh_mh": paperA_estimate(tab["s_h_net"], nums["m"]), "paperA_l4a": estimate(C, Scale("l4a", nums["kappa"]).m_hat(C))}


def model_dir(src_arm, rung_, seed, fam, root07=DIR07_MODELS):
    d07 = Path(root07) / src_arm / rung_ / f"s{seed}" / fam
    return d07 if (d07 / "manifest.json").exists() else DIR06 / "models" / src_arm / rung_ / f"s{seed}" / fam


def ml_predictions(src_arm, seed, fams, modes, tgt_tab, F, base, perm, device, roundtrip, log, models=(), root07=DIR07_MODELS):
    out, diag = {}, []
    for fam in fams:
        for rg in [r for m in modes for r in RUNGS_OF_MODE.get(m, ())]:
            d = model_dir(src_arm, rg, seed, fam, root07)
            try:                                                        # the method names the row for the queue's family filter
                meth = json.loads((d / "manifest.json").read_text(encoding="utf-8"))["spec"].split("|")[0]
            except (OSError, ValueError, KeyError):
                meth = next((m for m in models if FAMILY_OF[m] == fam), fam)
            row = {"method": meth, "rung": rg, "family": fam, "dir": str(d.relative_to(ROOT))}
            try:
                t0 = time.time()
                m, man = load_model(d, device)
                spec = tuple(man["spec"].split("|"))
                X = align_days(feature_matrix(F, tgt_tab, spec[1], spec[2]), perm)[man["feature_columns"]]
                z = np.asarray(m.predict(X), float)
                if spec[3] == "residual":
                    p, v = base["paperA_sh_mh"]
                elif spec[3] == "l4a":
                    p, v = base["paperA_l4a"]
                elif spec[3] == "l4b" and roundtrip:
                    p, v = joblib.load(d / "scale.joblib").base(tgt_tab)
                elif spec[3] == "l4b":
                    raise ValueError(f"{d}: L4b winner without an L4a refit (Task 3)")
                pred = compose(p, z, v) if man["residual"] else z
                out[spec] = pred
                row.update(spec=man["spec"], n_pred_nan=int((~np.isfinite(pred)).sum()), seconds=time.time() - t0,
                           n_invalid_base=int((~np.asarray(v, bool)).sum()) if man["residual"] else 0)
                log(f"  {rg} {fam} {man['spec']}: predicted {len(pred)} target substations in {time.time() - t0:.1f}s")
            except Exception as e:  # noqa: BLE001 - listed in diag, never silently dropped
                row["load_error"] = repr(e)[:300]
                log(f"  {rg} {fam} FAILED: {e!r}")
            diag.append(row)
    return out, diag


def physics_predictions(src, nums, tgt_tab, base, nums_tgt, src_pool_name, roundtrip):
    tr = (src["tab"]["split"] == "train") & src["tab"]["HP_Peak"].notna()
    out = {(b, "none", NA, NA, NA): make_baseline(b).fit(src["tab"][tr], src["tab"].loc[tr, "HP_Peak"]).predict(tgt_tab)
           for b in src["cfg"]["physics_baselines"] if b in PHYSICS}
    corr = paperA_corrected(tgt_tab["s_h_net"], tgt_tab["size"], s0_rows(tgt_tab, nums), nums["m"])
    rows = {"paperA_sh_mh": base["paperA_sh_mh"], "paperA_l4a": base["paperA_l4a"], "paperA_corr": corr}
    rows["paperA_cal"] = (np.where(base["paperA_sh_mh"][1], base["paperA_sh_mh"][0] * np.exp(nums["cal_b"]["paperA_cal"]), 0.0), base["paperA_sh_mh"][1])
    rows["paperA_corr_cal"] = (np.where(corr[1], corr[0] * np.exp(nums["cal_b"]["paperA_corr_cal"]), 0.0), corr[1])
    if src_pool_name == "bstar":                                         # whole-house pilot: CH only
        rows["paperA_corr_own"] = paperA_corrected(tgt_tab["s_h_net"], tgt_tab["size"], s0_rows(tgt_tab, nums), nums["m_own"])
    if not roundtrip:
        rows["paperA_corr@tgt_s0"] = paperA_corrected(tgt_tab["s_h_net"], tgt_tab["size"], s0_rows(tgt_tab, nums_tgt), nums["m"])
    out.update({(k, "none", NA, NA, NA): v[0] for k, v in rows.items()})
    diag = [{"method": k, "rung": "L0", "family": "physics", "n_invalid_base": int((~np.asarray(v[1], bool)).sum()),
             "n_pred_nan": int((~np.isfinite(v[0])).sum())} for k, v in rows.items()]
    if src_pool_name != "bstar":
        diag.append({"method": "paperA_corr_own", "rung": "L0", "family": "physics", "load_error": "n/a: no whole-house meters in GB"})
    return out, diag


def c_source(src):
    tr = src["members"][src["members"]["split"] == "train"]
    lab = substation_labels(tr, src["caps"])
    return float((lab["HL"] / lab["native"]).median())


def run_seed(cfg, seed):
    """One (direction, seed[, family]) job -> {preds, diag, log}. cfg: an arm config with `transfer: {source, target[, roundtrip]}`."""
    configure(cfg["parallel"]["threads"], cfg.get("ffnn", {}).get("patience", 40), cfg.get("device", "cpu"), cfg.get("cnn_inits", 1))
    tc, lines, t0 = cfg["transfer"], [], time.time()

    def log(msg):
        lines.append(f"[s{seed} {time.time() - t0:7.1f}s] {msg}")
        print(lines[-1], flush=True)

    rt = bool(tc.get("roundtrip"))
    src_arm, tgt_arm = tc["source"], (tc["source"] if rt else tc["target"])
    direction = f"{POOL_OF[src_arm]}->{POOL_OF[tgt_arm]}"
    src = side(src_arm, seed, log=log)
    tgt = src if rt else side(tgt_arm, seed, at30=(tgt_arm == "a_ch"), test_only=(tgt_arm == "a_ch"), log=log)
    te = tgt["tab"].index[tgt["tab"]["split"] == "test"]
    tt = tgt["tab"].loc[te]
    nums, nums_tgt = source_numbers(src_arm, seed), source_numbers(tgt_arm, seed)
    base = bases(tt, nums, tgt["cfg"]["target_defs"]["T_design_C"], tgt["pool"].temp)
    perm = doy_perm(src["pool"].index[0], tgt["pool"].index[0])
    log(f"{direction}: {len(te)} target test substations; source m_h {nums['m']:.5f}, kappa {nums['kappa']:.4f}, s0 median "
        f"{nums['s0_med']:.5f}; day alignment {'identity' if (perm == np.arange(len(perm))).all() else 'by (month, day)'}")
    preds, diag = {}, []
    if cfg.get("physics_baselines"):
        p, d = physics_predictions(src, nums, tt, base, nums_tgt, src["pool"].name, rt)
        preds.update(p)
        diag += d
    fams = sorted({FAMILY_OF[m] for m in list(cfg.get("models", [])) + list(cfg.get("residual_models", []))})
    if fams:
        p, d = ml_predictions(src_arm, seed, fams, cfg.get("modes", ["direct"]), tt, tgt["F"].loc[te], base, perm,
                              cfg.get("device", "cpu"), rt, log, list(cfg.get("models", [])) + list(cfg.get("residual_models", [])),
                              ROOT / tc.get("models_dir", DIR07_MODELS))
        preds.update(p)
        diag += d
    lab = substation_labels(tgt["members"].loc[te], tgt["caps"])
    c = 1.0 if rt else c_source(src)
    defs = [("native", 1.0, lab["native"])] if rt else [("HL", c, lab["HL"]), ("HL_uncorrected", 1.0, lab["HL"]), ("native", 1.0, lab["native"])]
    frames = [pd.DataFrame({"sub_id": te, "target": "HP_Peak", **dict(zip(["method", "anchor", "feature_set", "mode", "target_transform"], spec)),
                            "y": y.to_numpy(float), "pred": k * np.asarray(pr, float), "split_seed": seed, "size": tt["size"].to_numpy(),
                            "p": tt["p"].to_numpy(), "HP_Count": tt["HP_Count"].to_numpy(), "direction": direction, "label_def": ld,
                            "c_src": c, "rung": "L0" if spec[2] == NA else rung(spec)})
              for spec, pr in preds.items() for ld, k, y in defs]
    log(f"done: {len(preds)} prediction rows sets, c_src {c:.4f}")
    return {"preds": pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(),
            "diag": pd.DataFrame(diag).assign(split_seed=seed, direction=direction, c_src=c), "log": lines}
