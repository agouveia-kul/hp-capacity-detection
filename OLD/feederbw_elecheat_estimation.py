"""In-FeederBW estimation of TOTAL electric-heating capacity (ElecHeat_kW), the
quantity the aggregate temperature response actually reflects. Trained and
cross-validated WITHIN FeederBW (substation-grouped CV) so target definition and
population match -- this isolates genuine model skill from the Swiss-transfer /
HP-definition problems seen when predicting registry HP capacity.

Three estimators: calibrated delta (b*delta, mean/mean), fitted slope-only
(a + c*slope, min/max), and a windowed-HDD feature model (top-k + gradient
boosting). Reported for the ElecHeat target and, for contrast, HP-only.
"""
import numpy as np, pandas as pd

import hp_capacity as hc, benchmark_capacity_models as B
from hp_common import (fit_hockey_stick, daily_min_max_heating_season,
                       daily_mean_mean_heating_season)
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import LinearRegression
import xgboost as xgb

T_DE = 15.0
HEAT = list(hc._FBW_HEAT_COLS)


def hs(load, temp, rf):
    try:
        x, y = rf(temp, load, heating_season_thresh=T_DE)
        if len(x) < 20:
            return (np.nan, np.nan)
        _, slope, tbal, _ = fit_hockey_stick(x, y)
        return (float(slope), float(slope * (tbal - np.min(x))))
    except Exception:
        return (np.nan, np.nan)


def metrics(t, p):
    t = np.asarray(t, float); p = np.asarray(p, float); m = t != 0
    ss = np.sum((t - t.mean()) ** 2)
    r2 = 1 - np.sum((t - p) ** 2) / ss if ss > 0 else np.nan
    return float(np.mean(np.abs((t[m] - p[m]) / t[m])) * 100), float(r2)


def grouped_delta(delta, y, groups, gkf, fit_intercept):
    """cross_val_predict for a 1-feature OLS (delta) with GroupKFold."""
    pred = np.zeros(len(y))
    D = delta.reshape(-1, 1)
    for tri, tei in gkf.split(D, y, groups):
        m = LinearRegression(fit_intercept=fit_intercept).fit(D[tri], y[tri])
        pred[tei] = np.maximum(m.predict(D[tei]), 0)
    return pred


def main():
    print("Loading FeederBW (all feeders) ...", flush=True)
    fbw, static, end = hc.load_feederbw(year=2024)
    static[HEAT] = static.reindex(fbw.index)[HEAT].fillna(0)
    tgt = pd.DataFrame(index=fbw.index)
    tgt["ElecHeat"] = static.loc[fbw.index, HEAT].sum(axis=1)
    tgt["HP"] = static.loc[fbw.index, "heat_pumps_kW"].fillna(0)
    tgt["housing"] = static.loc[fbw.index, "housing_units_count"]
    tgt["substation"] = static.loc[fbw.index, "substation"]
    eh_end = end.reindex(fbw.index)[HEAT].fillna(0).sum(axis=1)
    stable = (eh_end - tgt["ElecHeat"]).abs().fillna(1e9) == 0
    usable = tgt[(tgt.ElecHeat > 0) & stable & (tgt.housing > 0)].index
    print(f"usable feeders: {len(usable)} across {tgt.loc[usable,'substation'].nunique()} substations | "
          f"ElecHeat median {tgt.loc[usable,'ElecHeat'].median():.1f} kW\n", flush=True)

    fu = fbw.loc[usable]
    dmm = np.array([hs(fu.loc[i, "Total_Load"], fu.loc[i, "Temperature"], daily_mean_mean_heating_season) for i in usable])
    dxm = np.array([hs(fu.loc[i, "Total_Load"], fu.loc[i, "Temperature"], daily_min_max_heating_season) for i in usable])
    Xf_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
        fu, T_base=T_DE, use_entity_index=True, show_progress=False, **B.CAP_FEATURE_KWARGS)
    Xf = Xf_raw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    Xf["Feature Scale_peak"] = fu["Total_Load"].apply(hc.series_peak)
    Xf["Feature Scale_size"] = tgt.loc[usable, "housing"].values

    groups = tgt.loc[usable, "substation"].astype(int).to_numpy()
    gkf = GroupKFold(n_splits=min(5, len(np.unique(groups))))
    okm = np.isfinite(dmm[:, 1]); okx = np.isfinite(dxm[:, 0])

    feat_pipe = Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler()),
                          ("sel", SelectKBest(f_regression, k=8)),
                          ("gb", xgb.XGBRegressor(n_estimators=150, max_depth=3,
                                                  learning_rate=0.05, subsample=0.8,
                                                  reg_lambda=2.0, tree_method="hist", n_jobs=-1))])

    for tname, tcol in [("TOTAL electric heating (ElecHeat_kW)", "ElecHeat"),
                        ("HP-only (heat_pumps_kW)", "HP")]:
        y = tgt.loc[usable, tcol].to_numpy(float)
        print(f"=== target: {tname} ===")
        # feature model (grouped CV)
        pf = np.maximum(cross_val_predict(feat_pipe, Xf, y, cv=gkf, groups=groups), 0)
        mp, r2 = metrics(y, pf)
        print(f"  windowed-HDD + XGB (k=8, grouped CV) : MAPE {mp:5.1f}%   R2 {r2:6.3f}")
        # calibrated delta (grouped CV, through origin)
        pd_ = np.full(len(y), np.nan)
        pd_[okm] = grouped_delta(dmm[okm, 1], y[okm], groups[okm], gkf, fit_intercept=False)
        mp, r2 = metrics(y[okm], pd_[okm])
        print(f"  calibrated delta (b*delta, grouped)  : MAPE {mp:5.1f}%   R2 {r2:6.3f}  (n={okm.sum()})")
        # fitted slope-only (grouped CV, with intercept)
        ps = np.full(len(y), np.nan)
        ps[okx] = grouped_delta(dxm[okx, 0], y[okx], groups[okx], gkf, fit_intercept=True)
        mp, r2 = metrics(y[okx], ps[okx])
        print(f"  fitted slope-only (a+c*slope, grouped): MAPE {mp:5.1f}%   R2 {r2:6.3f}  (n={okx.sum()})\n")

    pd.DataFrame({"ElecHeat": tgt.loc[usable, "ElecHeat"], "HP": tgt.loc[usable, "HP"],
                  "delta_mm": dmm[:, 1], "slope_xm": dxm[:, 0],
                  "substation": tgt.loc[usable, "substation"]}).to_csv(
        "data/feederbw_elecheat_estimation.csv")
    print("Saved -> data/feederbw_elecheat_estimation.csv")


if __name__ == "__main__":
    main()
