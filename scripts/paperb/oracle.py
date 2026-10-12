"""Oracle diagnostics and the filler-response scaling (iteration 05b, Task 1c, amendment A7, Arm 7).

Oracles use label-side information a DSO does not have: DIAGNOSTICS ONLY. Their rows carry methods `oracle_*` and never enter
the headline tables or the choice of the best physics row.
  O1 (perfect disaggregation): P_hat = s_h(HP aggregate) / m_h(pilot)  -> `oracle_O1` (the column `s_h` of the substation
     table is the hockey-stick slope of the HP aggregate). ML on O1: run the arm with `pool.oracle: O1` (substations.py).
  O2 (perfect scale): P_hat = s_h(HP aggregate) / m_h(true), m_h(true) = Paper A pilot fit on the substation's own HP members
     (`physics.pool_pilot`)  -> `oracle_O2`.
  Dispersion floor (`oracle_floor` rows): household CV of HP_Peak_i / s_h,i (s_h,i = Paper A fit of the household's own HP
     series) and, per n_hp, the CV of HP_Peak / s_h(HP aggregate) over the test substations.
Temperature-response scaling (`pool.response_scale: {fill: f, own: f}`): on every day d below its own T_h, a scaled household's
load is multiplied by (P_base + f (y_d - P_base)) / y_d, y_d its daily mean and (P_base, T_h) its own Paper A fit to daily means
(`physics.fit_daily`), so the day's deviation from P_base is scaled by f (noise included) and the intraday profile shape is kept;
days above T_h are unchanged. The fitted slope then scales by f (Arm 7: fillers x0.5 / x1.5; A7: f = 0 sets every day below T_h
to P_base on average, i.e. removes the response: O1a = fillers, O1b = the HP homes' own non-HP load on B*). A scaling of the
fitted hinge term alone was tried first and rejected before any run: on real LCL fillers it left the response the hinge does not
capture unscaled (x0.5 gave x0.476, tests/test_05b.py). Fillers
respond to `paperA.fill_station` on B* and to the LCL day temperature on GB-EoH; own load to its home's station. Households
whose fit fails are left unchanged (counted in `pool.response_info`). The scaled LCL array is cached in data/_paperb/pools/.
"""
import json
import os

import numpy as np
import pandas as pd

from paperb import ROOT
from paperb.physics import fit_daily, paperA_estimate, pool_pilot

EPS_KW = 1e-3


def scale_days(L, T_d, factor):
    """L [days, slots] (kW) and its daily temperature -> (scaled copy, fit dict or None if the fit failed)."""
    L = np.asarray(L, np.float64)
    y_d, ok = L.mean(axis=1), np.isfinite(T_d) & np.isfinite(L).all(axis=1)
    try:
        f = fit_daily(np.asarray(T_d)[ok], y_d[ok])
    except (RuntimeError, ValueError):
        return L.copy(), None
    below = np.asarray(T_d, float) < f["T_h"]
    ratio = np.maximum(f["P_base"] + factor * (y_d - f["P_base"]), EPS_KW) / np.maximum(y_d, EPS_KW)
    return L * np.where(below & np.isfinite(ratio), ratio, 1.0)[:, None], f


def _scale_frame(df, T_by_col, factor):
    """15-min frame (UTC days) -> scaled frame, number of failed fits."""
    days = df.index.normalize()
    n_d, out, failed = len(days.unique()), {}, 0
    for c in df.columns:
        T_d = T_by_col[c].groupby(days).mean().to_numpy()
        X, f = scale_days(df[c].to_numpy(np.float64).reshape(n_d, -1), T_d, factor)
        out[c], failed = X.ravel().astype(np.float32), failed + (f is None)
    return pd.DataFrame(out, index=df.index), failed


def apply_response_scale(pool, cfg):
    """Scale the temperature response of the pool's fillers and / or HP homes' own load in place (see module doc)."""
    rs = cfg["pool"].get("response_scale") or {}
    pool.response_info = {}
    if pool.analog is not None:                                       # GB-EoH: LCL fillers on their source days
        if set(rs) - {"fill"}:
            raise ValueError("GB-EoH has no own non-HP load to scale (each HP dwelling's own load is a random filler)")
        if "fill" in rs:
            pool.analog_unscaled = pool.analog.S
            pool.analog.S, pool.response_info["fill_failed"] = _scaled_lcl(pool.analog.S, pool.analog.S_T, rs["fill"], cfg)
        return pool
    st = cfg["paperA"].get("fill_station") or "KLO"
    if "fill" in rs:
        pool.fill_unscaled = pool.fill
        pool.fill, pool.response_info["fill_failed"] = _scale_frame(pool.fill, {c: pool.temp[st] for c in pool.fill.columns}, rs["fill"])
    if "own" in rs:
        T_own = {c: pool.temp[pool.meta.at[c, "station"]] for c in pool.own.columns}
        pool.own, pool.response_info["own_failed"] = _scale_frame(pool.own, T_own, rs["own"])
    return pool


def _rscale_files(cfg, factor):
    """Cache files (.npy, _info.json) of the LCL fillers scaled by `factor`. Not `with_suffix`: it read the ".5" of "rscale0.5" as a
    suffix, so x0.5 and x0 shared "rscale0.npy" (x1.5 and x1 "rscale1.npy"); fixed in 05b Stage 2 before any Stage 2 run."""
    fc = cfg["pool"]["fill"]
    base = ROOT / cfg["cache_dir"] / "pools" / f"lcl_std_{fc['lcl_window'][0].replace('-', '')}_{fc['lcl_window'][1].replace('-', '')}_{fc.get('temp_source', 'heathrow')}_rscale{factor:g}"
    return base.with_name(base.name + ".npy"), base.with_name(base.name + "_info.json")


def _scaled_lcl(S, T_days, factor, cfg):
    f_npy, f_info = _rscale_files(cfg, factor)
    if not f_npy.exists():
        out, failed = np.empty(S.shape, np.float32), 0
        for j in range(S.shape[0]):
            X, f = scale_days(S[j], T_days, factor)
            out[j], failed = X.astype(np.float32), failed + (f is None)
        tmp = f_npy.with_name(f"{f_npy.stem}.{os.getpid()}.tmp.npy")
        np.save(tmp, out)
        try:
            os.replace(tmp, f_npy)
            f_info.write_text(json.dumps({"factor": factor, "failed_fits": failed, "n_households": int(S.shape[0])}))
        except PermissionError:                                       # another worker wrote the same array
            os.remove(tmp)
    return np.load(f_npy, mmap_mode="r"), json.loads(f_info.read_text())["failed_fits"] if f_info.exists() else None


def true_m(pool, members, caps):
    """m_h(true) per substation: the Paper A pilot fit on its own HP members."""
    return pd.Series({sid: pool_pilot(pool, list(h), caps)["m"] for sid, h in members["hp_members"].items()}, dtype=float)


def oracle_predictions(tab, m_pilot, m_true):
    """{method: (P_hat, valid)} of O1 (s_h(HP aggregate) / pilot m_h) and O2 (s_h(HP aggregate) / own m_h)."""
    return {"oracle_O1": paperA_estimate(tab["s_h"], m_pilot), "oracle_O2": paperA_estimate(tab["s_h"], m_true.reindex(tab.index))}


def household_floor(pool):
    """HP_Peak_i / s_h,i per HP household (Paper A fit of its own HP series against its station T)."""
    out = {}
    for h in pool.hp.columns:
        d = pd.DataFrame({"T": pool.temp[pool.meta.at[h, "station"]], "y": pool.hp[h]}).resample("D").mean().dropna()
        try:
            s = fit_daily(d["T"].to_numpy(), d["y"].to_numpy())["s_h"]
        except (RuntimeError, ValueError):
            s = np.nan
        out[h] = pool.meta.at[h, "hp_peak"] / s if s > 0 else np.nan
    return pd.Series(out, dtype=float)


def floor_rows(pool, tab_test, seed, target="HP_Peak"):
    """Dispersion-floor metric rows: household CV (all HP households of the pool) and substation CV per n_hp (test)."""
    cv = lambda v: float(np.nanstd(v) / np.nanmean(v)) if np.isfinite(v).sum() > 1 else np.nan      # noqa: E731
    hh = household_floor(pool).to_numpy()
    rows = [{"cell": "household", "value": cv(hh), "n_substations": 0, "n_hp_households": int(np.isfinite(hh).sum())}]
    ratio = (tab_test[target] / tab_test["s_h"].where(tab_test["s_h"] > 0)).to_numpy(float)
    for k, g in pd.Series(ratio, index=tab_test["HP_Count"].to_numpy()).groupby(level=0):
        rows.append({"cell": f"n_hp={int(k)}", "value": cv(g.to_numpy()), "n_substations": len(g), "n_hp_households": -1})
    return [{"split_seed": seed, "target": target, "method": "oracle_floor", "anchor": "none", "feature_set": "-", "mode": "-",
             "target_transform": "-", "metric": "cv_peak_per_sh", **r} for r in rows]
