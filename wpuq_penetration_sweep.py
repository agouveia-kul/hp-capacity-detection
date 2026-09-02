"""Real WPUQ feeder at varying HP penetration, by OMITTING heat-pump loads.

The feeder always contains all 37 real WPUQ smart meters (their household/base
load is always present). Penetration is varied by including the submetered heat
pump for only a fraction of the houses; the rest keep only their base load. So
the feeder stays the SAME 37 real consumers -- only how many of them run a heat
pump changes. True installed capacity at penetration p = sum of the robust HP
peaks over the included HP houses.

At each penetration level several random house-subsets are drawn to get a spread.
Swiss-trained XGBoost (60 selected features) and the hockey-stick slope->capacity
map are applied; we report MAPE vs penetration with a spread across realisations
and XGBoost's 90% quantile prediction interval. National HDD bases 12/15.
"""
import json
import numpy as np
import pandas as pd

import hp_capacity as hc
import hp_pools as hpp
import benchmark_capacity_models as B
from hp_common import fit_hockey_stick, daily_min_max_heating_season
import xgboost as xgb

SEED = 42
rng = np.random.default_rng(SEED)
T_BASE_CH, T_BASE_DE = 12.0, 15.0
N_REALISATIONS = 30
CAP_KW = B.CAP_FEATURE_KWARGS


def hs_sensitivity(load, temp, t_base):
    try:
        x, y = daily_min_max_heating_season(temp, load, heating_season_thresh=t_base)
        if len(x) < 20:
            return np.nan
        _, slope, _, _ = fit_hockey_stick(x, y)
        return float(slope)
    except Exception:
        return np.nan


def ols_fit(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x); xbar = x.mean(); Sxx = np.sum((x - xbar) ** 2)
    b = np.sum((x - xbar) * (y - y.mean())) / Sxx
    a = y.mean() - b * xbar
    s = np.sqrt(np.sum((y - (a + b * x)) ** 2) / (n - 2))
    return dict(a=a, b=b, s=s, n=n, xbar=xbar, Sxx=Sxx)


def ols_predict(fit, x0, alpha=0.10):
    from scipy.stats import t as tdist
    x0 = np.asarray(x0, float)
    pred = fit["a"] + fit["b"] * x0
    tval = tdist.ppf(1 - alpha / 2, fit["n"] - 2)
    se = fit["s"] * np.sqrt(1 + 1 / fit["n"] + (x0 - fit["xbar"]) ** 2 / fit["Sxx"])
    return pred, pred - tval * se, pred + tval * se


def main():
    import pickle
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    meta = json.load(open("models/xgb_selected_features.json"))
    sel, sel_meta = meta["selected_features"], meta["sel_meta"]

    # --- train the two Swiss estimators -------------------------------------
    Xtr = X.loc[tr, sel]; ytr = y.loc[tr].to_numpy(); med = Xtr.median()

    def xgb_base(**kw):
        return xgb.XGBRegressor(
            learning_rate=sel_meta["eta"], n_estimators=int(sel_meta["n_estimators_final"]),
            max_depth=int(sel_meta["max_depth"]), gamma=sel_meta["gamma"],
            subsample=sel_meta["subsample"], reg_alpha=sel_meta["reg_alpha"],
            reg_lambda=sel_meta["reg_lambda"], min_child_weight=int(sel_meta["min_child_weight"]),
            colsample_bytree=sel_meta["colsample_bytree"], tree_method="hist", n_jobs=-1, **kw)

    xgb_pt = xgb_base().fit(Xtr.fillna(med), ytr)
    xgb_lo = xgb_base(objective="reg:quantileerror", quantile_alpha=0.05).fit(Xtr.fillna(med), ytr)
    xgb_hi = xgb_base(objective="reg:quantileerror", quantile_alpha=0.95).fit(Xtr.fillna(med), ytr)

    s_tr = np.array([hs_sensitivity(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_BASE_CH)
                     for i in tr])
    ok = np.isfinite(s_tr)
    hs = ols_fit(s_tr[ok], ytr[ok])

    # --- build the WPUQ penetration variants (real feeder, HP omitted) ------
    pool = hpp.build_pool_wpuq(verbose=False)
    idx = pool["index"]; hp_mat, other_mat = pool["hp_mat"], pool["other_mat"]
    n_house = hp_mat.shape[0]
    robust_hp = np.array([hc.robust_series_peak(hp_mat[i], 0.999) for i in range(n_house)])
    base_total = other_mat.sum(axis=0)               # all 37 base loads, always present
    temp = pd.Series(pool["temperature"]["WPUQ"], index=idx)

    n_hps = [4, 7, 11, 15, 19, 22, 26, 30, 33, 37]   # penetration ~0.11 .. 1.00
    rows = {}
    k = 0
    for nh in n_hps:
        seen = set()
        reps = 1 if nh == n_house else N_REALISATIONS
        while len([r for r in rows.values() if r["n_hp"] == nh]) < reps:
            hp_houses = tuple(sorted(rng.choice(n_house, nh, replace=False)))
            if hp_houses in seen:
                continue
            seen.add(hp_houses)
            load = base_total + hp_mat[list(hp_houses)].sum(axis=0)
            rows[k] = {"Total_Load": pd.Series(load, index=idx), "Temperature": temp,
                       "size": n_house, "n_hp": nh, "penetration": nh / n_house,
                       "HP_Peak": float(robust_hp[list(hp_houses)].sum())}
            k += 1
    variants = pd.DataFrame.from_dict(rows, orient="index")
    print(f"{len(variants)} feeder variants across {len(n_hps)} penetration levels "
          f"(size fixed at {n_house} real meters)\n", flush=True)

    # --- features + predictions ---------------------------------------------
    Xv_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
        variants, T_base=T_BASE_DE, use_entity_index=True, show_progress=False, **CAP_KW)
    Xv = hc.capacity_feature_matrix(
        Xv_raw, hc.select_scale_free_columns(Xv_raw), size=variants["size"],
        peak=variants["Total_Load"].apply(hc.series_peak))
    # align to the training feature columns, then take the selected subset
    Xv = Xv.reindex(columns=X.columns)[sel].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    Xv_f = Xv.fillna(med)

    variants["xgb"] = hc.clip_non_negative(xgb_pt.predict(Xv_f))
    variants["xgb_lo"] = hc.clip_non_negative(xgb_lo.predict(Xv_f))
    variants["xgb_hi"] = np.maximum(hc.clip_non_negative(xgb_hi.predict(Xv_f)), variants["xgb_lo"])
    s_v = np.array([hs_sensitivity(variants.loc[i, "Total_Load"],
                                   variants.loc[i, "Temperature"], T_BASE_DE)
                    for i in variants.index])
    hp_, hlo_, hhi_ = ols_predict(hs, s_v)
    variants["hockey"] = np.maximum(hp_, 0)
    variants["hockey_lo"] = np.maximum(hlo_, 0)
    variants["hockey_hi"] = np.maximum(hhi_, 0)

    # --- summarise by penetration level -------------------------------------
    def mape(a, b):
        return float(np.mean(np.abs((a - b) / a)) * 100)

    print("=" * 92)
    print(f"{'pen':>5s} {'n_hp':>4s} {'reps':>4s} {'true kW (mean)':>15s} "
          f"{'XGB MAPE%':>10s} {'XGB cov':>8s} {'hockey MAPE%':>13s} {'hockey cov':>11s}")
    print("-" * 92)
    summ = []
    for nh in n_hps:
        g = variants[variants["n_hp"] == nh]
        t = g["HP_Peak"].to_numpy()
        xm = mape(t, g["xgb"].to_numpy()); hm = mape(t, g["hockey"].to_numpy())
        xcov = float(((t >= g["xgb_lo"]) & (t <= g["xgb_hi"])).mean())
        hcov = float(((t >= g["hockey_lo"]) & (t <= g["hockey_hi"])).mean())
        print(f"{nh / n_house:5.2f} {nh:4d} {len(g):4d} {t.mean():15.1f} "
              f"{xm:10.1f} {xcov * 100:7.0f}% {hm:13.1f} {hcov * 100:10.0f}%")
        summ.append(dict(penetration=nh / n_house, n_hp=nh, reps=len(g),
                         true_mean=t.mean(), xgb_mape=xm, xgb_cov=xcov,
                         hockey_mape=hm, hockey_cov=hcov,
                         xgb_pred_mean=g["xgb"].mean(), hockey_pred_mean=g["hockey"].mean()))
    print("=" * 92)
    pd.DataFrame(summ).to_csv("data/wpuq_penetration_sweep.csv", index=False)
    variants.drop(columns=["Total_Load", "Temperature"]).to_csv(
        "data/wpuq_penetration_variants.csv", index=False)
    print("Saved -> data/wpuq_penetration_sweep.csv, data/wpuq_penetration_variants.csv")

    # --- figure --------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sdf = pd.DataFrame(summ)
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8))
    # (a) predicted vs true capacity
    ax[0].plot([0, variants["HP_Peak"].max()], [0, variants["HP_Peak"].max()],
               "k--", lw=1, label="ideal")
    ax[0].scatter(variants["HP_Peak"], variants["xgb"], s=14, alpha=0.5,
                  color="#238b45", label="XGBoost")
    ax[0].scatter(variants["HP_Peak"], variants["hockey"], s=14, alpha=0.5,
                  color="#d95f0e", label="hockey-stick")
    ax[0].set_xlabel("true installed HP capacity (kW)")
    ax[0].set_ylabel("predicted (kW)")
    ax[0].set_title("Real WPUQ feeder, HP omitted to vary penetration")
    ax[0].legend(); ax[0].grid(alpha=0.3)
    # (b) MAPE vs penetration
    ax[1].plot(sdf["penetration"] * 100, sdf["xgb_mape"], "o-", color="#238b45", label="XGBoost")
    ax[1].plot(sdf["penetration"] * 100, sdf["hockey_mape"], "s-", color="#d95f0e", label="hockey-stick")
    ax[1].set_xlabel("HP penetration (%)"); ax[1].set_ylabel("MAPE (%)")
    ax[1].set_title("Error vs penetration"); ax[1].legend(); ax[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("paper/figures/fig_wpuq_penetration_sweep.png", dpi=150)
    print("Saved -> paper/figures/fig_wpuq_penetration_sweep.png")


if __name__ == "__main__":
    main()
