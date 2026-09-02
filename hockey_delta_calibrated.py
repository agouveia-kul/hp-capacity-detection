"""Calibrate the physical hockey-stick delta to installed capacity and compare
transfer against the fitted slope map and XGBoost.

Physical delta = slope * (T_balance - T_min): the hockey stick's coincident
(simultaneous) coldest-day HP load. It targets the SIMULTANEOUS peak, whereas
HP_Peak is the NON-SIMULTANEOUS installed sum, so the delta is biased low by the
diversity/coincidence factor. We calibrate delta -> HP_Peak with linear
regression on Swiss train, both with an intercept and THROUGH THE ORIGIN
(HP_Peak = b*delta, a pure diversity factor), and evaluate transfer to Swiss
test, the synthetic WPUQ substations, and the real WPUQ feeder.
"""
import json
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

T_CH, T_DE = 12.0, 15.0
# mean/mean (daily mean temp / mean load) gives a cleaner, less noisy slope and
# transfers better than min/max here -- it is the recommended reduction.
REDUCE = daily_mean_mean_heating_season


def hs_delta(load, temp, t_base, reduce_fn=REDUCE):
    """Physical delta = slope * (T_balance - T_min), T_min = coldest daily point."""
    try:
        x, y = reduce_fn(temp, load, heating_season_thresh=t_base)
        if len(x) < 20:
            return (np.nan, np.nan)
        _, slope, tbal, _ = fit_hockey_stick(x, y)
        return (float(slope), float(slope * (tbal - np.min(x))))
    except Exception:
        return (np.nan, np.nan)


def feats(ent, lc, tc, tb):
    return np.array([hs_delta(ent.loc[i, lc], ent.loc[i, tc], tb) for i in ent.index])


def mape(t, p):
    t = np.asarray(t, float); p = np.asarray(p, float); m = t != 0
    return float(np.mean(np.abs((t[m] - p[m]) / t[m])) * 100)


def main():
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    pool = hpp.build_pool_wpuq(verbose=False)
    wp = hc.build_wpuq_substations(pool, n=400, size_range=(10, 37), pen_max=0.5, seed=7)
    rf = hc.build_wpuq_real_feeder(pool)

    Ftr = feats(sub.loc[tr], "Total_Load", "Temperature", T_CH)
    ytr = y.loc[tr].to_numpy(); ok = np.isfinite(Ftr).all(1)
    slope_map = LinearRegression().fit(Ftr[ok, :1], ytr[ok])                    # HP_Peak ~ slope
    cal_int = LinearRegression().fit(Ftr[ok, 1:2], ytr[ok])                     # HP_Peak ~ a + b*delta
    cal_org = LinearRegression(fit_intercept=False).fit(Ftr[ok, 1:2], ytr[ok])  # HP_Peak = b*delta
    print(f"fitted slope-only:      HP_Peak = {slope_map.intercept_:.1f} + {slope_map.coef_[0]:.1f}*slope")
    print(f"delta calib (intercept):HP_Peak = {cal_int.intercept_:.1f} + {cal_int.coef_[0]:.2f}*delta")
    print(f"delta calib (origin):   HP_Peak = {cal_org.coef_[0]:.2f}*delta   (diversity factor)\n")

    sets = {"Swiss test": (feats(sub.loc[te], "Total_Load", "Temperature", T_CH), y.loc[te].to_numpy()),
            "synthetic WPUQ": (feats(wp, "Total_Load", "Temperature", T_DE), wp["HP_Peak"].to_numpy()),
            "real WPUQ feeder": (feats(rf, "Total_Load", "Temperature", T_DE), np.array([yr]))}

    methods = [("raw delta", lambda F: np.maximum(F[:, 1], 0)),
               ("delta calib (intercept)", lambda F: np.maximum(cal_int.predict(F[:, 1:2]), 0)),
               ("delta calib (origin)", lambda F: np.maximum(cal_org.predict(F[:, 1:2]), 0)),
               ("fitted slope-only", lambda F: np.maximum(slope_map.predict(F[:, :1]), 0))]

    rows = []
    print(f"{'set':18s} {'method':24s} {'n':>4s} {'MAPE%':>7s} {'R2':>7s} {'real kW':>8s}")
    print("-" * 74)
    for name, (F, t) in sets.items():
        g = np.isfinite(F).all(1); tg = t[g]
        for mm, fn in methods:
            p = fn(F[g])
            r2 = r2_score(tg, p) if g.sum() > 1 else np.nan
            r2s = f"{r2:7.3f}" if np.isfinite(r2) else f"{'--':>7s}"
            pr = f"{p[0]:.0f}" if name == "real WPUQ feeder" else ""
            print(f"{name:18s} {mm:24s} {g.sum():4d} {mape(tg, p):7.1f} {r2s} {pr:>8s}")
            rows.append(dict(set=name, method=mm, n=int(g.sum()), mape=mape(tg, p),
                             r2=r2, pred=float(p[0]) if name == "real WPUQ feeder" else np.nan))
        print()
    pd.DataFrame(rows).to_csv("data/hockey_delta_calibrated.csv", index=False)
    json.dump({"diversity_factor": float(cal_org.coef_[0]),
               "intercept_form": [float(cal_int.intercept_), float(cal_int.coef_[0])]},
              open("models/hockey_delta_calibration.json", "w"), indent=2)
    print("Saved -> data/hockey_delta_calibrated.csv, models/hockey_delta_calibration.json")


if __name__ == "__main__":
    main()
