"""Penetration sweep on the Swiss data: MAPE per HP-penetration level on the
unseen Swiss TEST substations, for the three estimators (XGBoost, calibrated
delta, fitted slope-only). The Swiss counterpart of the real-WPUQ sweep -- here
penetration is the substations' own HP_ratio (balanced grid, 108 test subs per
level).
"""
import json, pickle
import numpy as np, pandas as pd

import hp_capacity as hc, benchmark_capacity_models as B
from hp_common import (fit_hockey_stick, daily_min_max_heating_season,
                       daily_mean_mean_heating_season)
from sklearn.linear_model import LinearRegression
import xgboost as xgb

T_CH = 12.0


def hs(load, temp, tb, reduce_fn):
    try:
        x, y = reduce_fn(temp, load, heating_season_thresh=tb)
        if len(x) < 20:
            return (np.nan, np.nan)
        _, slope, tbal, _ = fit_hockey_stick(x, y)
        return (float(slope), float(slope * (tbal - np.min(x))))
    except Exception:
        return (np.nan, np.nan)


def mape(t, p):
    t = np.asarray(t, float); p = np.asarray(p, float); m = t != 0
    return float(np.mean(np.abs((t[m] - p[m]) / t[m])) * 100)


def main():
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    meta = json.load(open("models/xgb_selected_features.json"))
    sel, sm = meta["selected_features"], meta["sel_meta"]

    Xtr = X.loc[tr, sel]; ytr = y.loc[tr].to_numpy(); med = Xtr.median()
    xgbm = xgb.XGBRegressor(
        learning_rate=sm["eta"], n_estimators=int(sm["n_estimators_final"]),
        max_depth=int(sm["max_depth"]), gamma=sm["gamma"], subsample=sm["subsample"],
        reg_alpha=sm["reg_alpha"], reg_lambda=sm["reg_lambda"],
        min_child_weight=int(sm["min_child_weight"]), colsample_bytree=sm["colsample_bytree"],
        tree_method="hist", n_jobs=-1).fit(Xtr.fillna(med), ytr)

    mm = np.array([hs(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_CH,
                      daily_mean_mean_heating_season) for i in tr])
    xm = np.array([hs(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_CH,
                      daily_min_max_heating_season) for i in tr])
    okm = np.isfinite(mm[:, 1]); okx = np.isfinite(xm[:, 0])
    cal = LinearRegression(fit_intercept=False).fit(mm[okm, 1:2], ytr[okm])
    smap = LinearRegression().fit(xm[okx, :1], ytr[okx])
    print(f"calibrated delta: HP_Peak = {cal.coef_[0]:.2f}*delta (mean/mean)")
    print(f"fitted slope-only: HP_Peak = {smap.intercept_:.1f} + {smap.coef_[0]:.1f}*slope (min/max)\n")

    d = pd.DataFrame(index=te)
    d["pen"] = sub.loc[te, "HP_ratio"].round(2)
    d["true"] = y.loc[te]
    d["xgb"] = hc.clip_non_negative(xgbm.predict(X.loc[te, sel].fillna(med)))
    mte = np.array([hs(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_CH,
                       daily_mean_mean_heating_season) for i in te])
    xte = np.array([hs(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_CH,
                       daily_min_max_heating_season) for i in te])
    d["cal_delta"] = np.maximum(cal.predict(mte[:, 1:2]), 0)
    d["slope_map"] = np.maximum(smap.predict(xte[:, :1]), 0)

    print(f"{'pen':>5s} {'n':>4s} {'true kW':>8s} {'XGB':>7s} {'calDelta':>9s} {'slopeMap':>9s}   best")
    print("-" * 60)
    out = []
    for p, g in d.groupby("pen"):
        e = {"XGB": mape(g["true"], g["xgb"]), "calDelta": mape(g["true"], g["cal_delta"]),
             "slopeMap": mape(g["true"], g["slope_map"])}
        best = min(e, key=e.get)
        print(f"{p:5.2f} {len(g):4d} {g['true'].mean():8.1f} {e['XGB']:7.1f} "
              f"{e['calDelta']:9.1f} {e['slopeMap']:9.1f}   {best}")
        out.append(dict(penetration=p, n=len(g), true_mean=g["true"].mean(),
                        **{f"{m}_mape": v for m, v in e.items()}))
    print("-" * 60)
    print(f"{'ALL':>5s} {len(d):4d} {d['true'].mean():8.1f} {mape(d['true'],d['xgb']):7.1f} "
          f"{mape(d['true'],d['cal_delta']):9.1f} {mape(d['true'],d['slope_map']):9.1f}")
    pd.DataFrame(out).to_csv("data/swiss_penetration_sweep.csv", index=False)

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    s = pd.DataFrame(out)
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(s["penetration"]*100, s["XGB_mape"], "o-", color="#2c7fb8", label="XGBoost")
    ax.plot(s["penetration"]*100, s["calDelta_mape"], "^-", color="#8856a7", label="calibrated delta (mean/mean)")
    ax.plot(s["penetration"]*100, s["slopeMap_mape"], "s-", color="#238b45", label="fitted slope-only")
    ax.set_xlabel("HP penetration (%)"); ax.set_ylabel("MAPE (%)"); ax.set_ylim(0, 70)
    ax.set_title("Swiss test penetration sweep (108 unseen subs per level)")
    ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
    plt.savefig("paper/figures/fig_swiss_penetration_sweep.png", dpi=150)
    print("\nSaved -> data/swiss_penetration_sweep.csv, paper/figures/fig_swiss_penetration_sweep.png")


if __name__ == "__main__":
    main()
