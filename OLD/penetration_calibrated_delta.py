"""Compare the calibrated physical delta against XGBoost and the fitted
slope-only map on the real-WPUQ penetration sweep (HP omitted to vary
penetration on the same 37 real meters).

Estimators (all trained only on Swiss train):
  * XGBoost            -- 60 selected features
  * calibrated delta   -- HP_Peak = b * slope*(T_balance - T_min), mean/mean
                          reduction, fit through the origin
  * fitted slope-only  -- HP_Peak = a + c*slope, min/max reduction
"""
import json, pickle
import numpy as np, pandas as pd

import hp_capacity as hc, hp_pools as hpp, benchmark_capacity_models as B
from hp_common import (fit_hockey_stick, daily_min_max_heating_season,
                       daily_mean_mean_heating_season)
from sklearn.linear_model import LinearRegression
import xgboost as xgb

T_CH, T_DE = 12.0, 15.0


def hs(load, temp, tb, reduce_fn):
    try:
        x, y = reduce_fn(temp, load, heating_season_thresh=tb)
        if len(x) < 20:
            return (np.nan, np.nan)
        _, slope, tbal, _ = fit_hockey_stick(x, y)
        return (float(slope), float(slope * (tbal - np.min(x))))  # slope, delta
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

    # --- train the three estimators on Swiss train --------------------------
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
    delta_cal = LinearRegression(fit_intercept=False).fit(mm[okm, 1:2], ytr[okm])   # b*delta
    slope_map = LinearRegression().fit(xm[okx, :1], ytr[okx])                       # a + c*slope
    print(f"calibrated delta:  HP_Peak = {delta_cal.coef_[0]:.2f}*delta (mean/mean)")
    print(f"fitted slope-only: HP_Peak = {slope_map.intercept_:.1f} + {slope_map.coef_[0]:.1f}*slope (min/max)\n")

    # --- build the real-feeder penetration variants -------------------------
    pool = hpp.build_pool_wpuq(verbose=False)
    idx = pool["index"]; hp_mat, other_mat = pool["hp_mat"], pool["other_mat"]
    nH = hp_mat.shape[0]
    robust = np.array([hc.robust_series_peak(hp_mat[i], 0.999) for i in range(nH)])
    base_total = other_mat.sum(axis=0); temp = pd.Series(pool["temperature"]["WPUQ"], index=idx)
    rng = np.random.default_rng(42)
    rows = {}; k = 0
    for nh in [4, 7, 11, 15, 19, 22, 26, 30, 33, 37]:
        seen = set(); reps = 1 if nh == nH else 30
        while len([r for r in rows.values() if r["n_hp"] == nh]) < reps:
            hh = tuple(sorted(rng.choice(nH, nh, replace=False)))
            if hh in seen:
                continue
            seen.add(hh)
            load = base_total + hp_mat[list(hh)].sum(axis=0)
            rows[k] = {"Total_Load": pd.Series(load, index=idx), "Temperature": temp,
                       "size": nH, "n_hp": nh, "penetration": nh / nH,
                       "HP_Peak": float(robust[list(hh)].sum())}
            k += 1
    V = pd.DataFrame.from_dict(rows, orient="index")

    # XGBoost features
    Xv_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
        V, T_base=T_DE, use_entity_index=True, show_progress=False, **B.CAP_FEATURE_KWARGS)
    Xv = hc.capacity_feature_matrix(Xv_raw, hc.select_scale_free_columns(Xv_raw),
                                    size=V["size"], peak=V["Total_Load"].apply(hc.series_peak))
    Xv = Xv.reindex(columns=X.columns)[sel].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    V["xgb"] = hc.clip_non_negative(xgbm.predict(Xv.fillna(med)))
    dmm = np.array([hs(V.loc[i, "Total_Load"], V.loc[i, "Temperature"], T_DE,
                       daily_mean_mean_heating_season) for i in V.index])
    dxm = np.array([hs(V.loc[i, "Total_Load"], V.loc[i, "Temperature"], T_DE,
                       daily_min_max_heating_season) for i in V.index])
    V["cal_delta"] = np.maximum(delta_cal.predict(dmm[:, 1:2]), 0)
    V["slope_map"] = np.maximum(slope_map.predict(dxm[:, :1]), 0)

    print(f"{'pen':>5s} {'true kW':>8s} {'XGB':>7s} {'calDelta':>9s} {'slopeMap':>9s}   best")
    print("-" * 56)
    out = []
    for p, g in V.groupby("penetration"):
        t = g["HP_Peak"].to_numpy()
        e = {"XGB": mape(t, g["xgb"]), "calDelta": mape(t, g["cal_delta"]),
             "slopeMap": mape(t, g["slope_map"])}
        best = min(e, key=e.get)
        print(f"{p:5.2f} {t.mean():8.1f} {e['XGB']:7.1f} {e['calDelta']:9.1f} "
              f"{e['slopeMap']:9.1f}   {best}")
        out.append(dict(penetration=p, true_mean=t.mean(), **{f"{m}_mape": v for m, v in e.items()}))
    tt = V["HP_Peak"].to_numpy()
    print("-" * 56)
    print(f"{'ALL':>5s} {tt.mean():8.1f} {mape(tt, V['xgb']):7.1f} "
          f"{mape(tt, V['cal_delta']):9.1f} {mape(tt, V['slope_map']):9.1f}")
    pd.DataFrame(out).to_csv("data/penetration_calibrated_delta.csv", index=False)

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    s = pd.DataFrame(out)
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(s["penetration"]*100, s["XGB_mape"], "o-", color="#2c7fb8", label="XGBoost")
    ax.plot(s["penetration"]*100, s["calDelta_mape"], "^-", color="#8856a7", label="calibrated delta (2.70*delta)")
    ax.plot(s["penetration"]*100, s["slopeMap_mape"], "s-", color="#238b45", label="fitted slope-only")
    ax.set_xlabel("HP penetration (%)"); ax.set_ylabel("MAPE (%)"); ax.set_ylim(0, 60)
    ax.set_title("Real WPUQ penetration sweep: calibrated delta vs XGBoost vs fitted map")
    ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
    plt.savefig("paper/figures/fig_penetration_calibrated_delta.png", dpi=150)
    print("\nSaved -> data/penetration_calibrated_delta.csv, "
          "paper/figures/fig_penetration_calibrated_delta.png")


if __name__ == "__main__":
    main()
