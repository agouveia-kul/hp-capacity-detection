"""Compare hockey-stick capacity-estimator variants and their transfer.

Two design axes, 2x2:
  * daily reduction : min-temp/max-load (peak-tied)  vs  mean-temp/mean-load
  * slope->capacity map : slope only  vs  slope + base_load + T_balance (multivariate)

Every variant fits its OLS map on the Swiss TRAIN split, then is evaluated by
transfer to: the Swiss TEST split (unseen substations), the synthetic WPUQ
substations, and the single real WPUQ feeder. Metric: MAPE (and R2 where n>1).
National HDD bases 12 (CH) / 15 (DE).
"""
import pickle
import numpy as np
import pandas as pd

import hp_capacity as hc
import hp_pools as hpp
import benchmark_capacity_models as B
from hp_common import (fit_hockey_stick, daily_min_max_heating_season,
                       daily_mean_mean_heating_season)
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

T_BASE_CH, T_BASE_DE = 12.0, 15.0
REDUCTIONS = {"min/max": daily_min_max_heating_season,
              "mean/mean": daily_mean_mean_heating_season}


def hs_features(load, temp, t_base, reduce_fn):
    """(slope, base_load, T_balance) of the hockey-stick fit, or nans."""
    try:
        x, y = reduce_fn(temp, load, heating_season_thresh=t_base)
        if len(x) < 20:
            return (np.nan, np.nan, np.nan)
        base, slope, tbal, _ = fit_hockey_stick(x, y)
        return (float(slope), float(base), float(tbal))
    except Exception:
        return (np.nan, np.nan, np.nan)


def feats_for(entities, load_col, temp_col, t_base, reduce_fn):
    return np.array([hs_features(entities.loc[i, load_col], entities.loc[i, temp_col],
                                 t_base, reduce_fn) for i in entities.index])


def mape(t, p):
    t = np.asarray(t, float); p = np.asarray(p, float); m = t != 0
    return float(np.mean(np.abs((t[m] - p[m]) / t[m])) * 100)


def main():
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    pool = hpp.build_pool_wpuq(verbose=False)
    wp = hc.build_wpuq_substations(pool, n=400, size_range=(10, 37), pen_max=0.5, seed=7)
    rf = hc.build_wpuq_real_feeder(pool)

    ytr = y.loc[tr].to_numpy(); yte = y.loc[te].to_numpy()
    ywp = wp["HP_Peak"].to_numpy()

    rows = []
    for rname, rfn in REDUCTIONS.items():
        Ftr = feats_for(sub.loc[tr], "Total_Load", "Temperature", T_BASE_CH, rfn)
        Fte = feats_for(sub.loc[te], "Total_Load", "Temperature", T_BASE_CH, rfn)
        Fwp = feats_for(wp, "Total_Load", "Temperature", T_BASE_DE, rfn)
        Frf = feats_for(rf, "Total_Load", "Temperature", T_BASE_DE, rfn)

        ok = np.isfinite(Ftr).all(axis=1)
        # slope-only, slope+base, and slope+base+T_balance maps
        uni = LinearRegression().fit(Ftr[ok, :1], ytr[ok])
        mid = LinearRegression().fit(Ftr[ok, :2], ytr[ok])
        multi = LinearRegression().fit(Ftr[ok], ytr[ok])
        print(f"[{rname:9s}] slope-only:  HP_Peak = {uni.intercept_:.1f} + "
              f"{uni.coef_[0]:.1f}*slope", flush=True)
        print(f"[{rname:9s}] slope+base:  coefs slope {mid.coef_[0]:.1f}, "
              f"base {mid.coef_[1]:.2f}, int {mid.intercept_:.1f}", flush=True)
        print(f"[{rname:9s}] multivar:    coefs slope {multi.coef_[0]:.1f}, "
              f"base {multi.coef_[1]:.2f}, Tbal {multi.coef_[2]:.2f}, int {multi.intercept_:.1f}",
              flush=True)

        for mname, mdl, ncol in [("slope-only", uni, 1), ("slope+base", mid, 2),
                                 ("slope+base+Tbal", multi, 3)]:
            for sname, F, t in [("Swiss test", Fte, yte),
                                ("synthetic WPUQ", Fwp, ywp),
                                ("real WPUQ feeder", Frf, np.array([yr]))]:
                good = np.isfinite(F).all(axis=1)
                if t[t != 0].size == 0 or good.sum() == 0:
                    continue
                p = np.maximum(mdl.predict(F[good][:, :ncol]), 0)
                tg = t[good]
                mp = mape(tg, p)
                r2 = r2_score(tg, p) if good.sum() > 1 else np.nan
                rows.append(dict(reduction=rname, map=mname, set=sname,
                                 n=int(good.sum()), mape=mp, r2=r2,
                                 pred=float(p[0]) if sname == "real WPUQ feeder" else np.nan))

    res = pd.DataFrame(rows)
    print("\n" + "=" * 84)
    print("Hockey-stick variants -- transfer comparison (MAPE %, and R2 where n>1)")
    print("=" * 84)
    for sname in ["Swiss test", "synthetic WPUQ", "real WPUQ feeder"]:
        s = res[res["set"] == sname]
        print(f"\n{sname}  (true {yr:.0f} kW)" if sname == "real WPUQ feeder" else f"\n{sname}")
        print(f"  {'reduction':10s} {'map':16s} {'MAPE%':>7s} {'R2':>7s}"
              + ("  pred kW" if sname == "real WPUQ feeder" else ""))
        for _, r in s.iterrows():
            extra = f"  {r['pred']:.0f}" if sname == "real WPUQ feeder" else ""
            r2s = f"{r['r2']:7.3f}" if np.isfinite(r["r2"]) else f"{'--':>7s}"
            print(f"  {r['reduction']:10s} {r['map']:16s} {r['mape']:7.1f} {r2s}{extra}")

    res.to_csv("data/hockey_variants_transfer.csv", index=False)
    print("\nSaved -> data/hockey_variants_transfer.csv")


if __name__ == "__main__":
    main()
