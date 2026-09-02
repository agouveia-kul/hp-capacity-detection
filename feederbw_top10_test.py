"""Real-world validation on the 10 FeederBW feeders with the most installed HP
capacity. Apply the Swiss-trained estimators (XGBoost, calibrated delta, fitted
slope-only) and compare predictions to the REGISTRY heat_pumps_kW (and to total
electric-heating capacity, since the temperature response reflects all electric
heating, not HP alone). National HDD base 15 degC (DE).
"""
import json, pickle
from pathlib import Path
import numpy as np, pandas as pd

import hp_capacity as hc, benchmark_capacity_models as B
from hp_common import (fit_hockey_stick, daily_min_max_heating_season,
                       daily_mean_mean_heating_season)
from sklearn.linear_model import LinearRegression
import xgboost as xgb

T_CH, T_DE = 12.0, 15.0
HEAT = ["heat_pumps_kW", "storage_heaters_kW", "electric_heaters_kW",
        "flow-type_heaters_kW", "hot_water_tanks_kW"]


def hs(load, temp, tb, rf):
    try:
        x, y = rf(temp, load, heating_season_thresh=tb)
        if len(x) < 20:
            return (np.nan, np.nan)
        _, slope, tbal, _ = fit_hockey_stick(x, y)
        return (float(slope), float(slope * (tbal - np.min(x))))
    except Exception:
        return (np.nan, np.nan)


def load_feeder_series(fid, fdir, wx, lo, hi):
    fp = next(Path(fdir).rglob(f"feeder_{fid:03d}.parquet"), None)
    if fp is None:
        return None
    fdf = pd.read_parquet(fp)
    fdf["timestamp_UTC"] = pd.to_datetime(fdf["timestamp_UTC"], utc=True)
    fdf = fdf[(fdf["timestamp_UTC"] >= lo) & (fdf["timestamp_UTC"] < hi)].sort_values(
        "timestamp_UTC").set_index("timestamp_UTC")
    w = wx[wx["feeder"] == fid].copy()
    w["timestamp_UTC"] = pd.to_datetime(w["timestamp_UTC"], utc=True)
    w = w.sort_values("timestamp_UTC").set_index("timestamp_UTC")
    load = fdf["active_power_kW"].resample("15min").mean().rename("Total_Load")
    temp = (w["air_temperature_C"].resample("15min").interpolate("time")
            .ffill().bfill().rename("Temperature"))
    a = pd.concat([load, temp], axis=1, join="inner").dropna()
    return a if not a.empty else None


def main():
    # --- train the three Swiss estimators -----------------------------------
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
    cal = LinearRegression(fit_intercept=False).fit(mm[np.isfinite(mm[:, 1]), 1:2],
                                                    ytr[np.isfinite(mm[:, 1])])
    smap = LinearRegression().fit(xm[np.isfinite(xm[:, 0]), :1],
                                  ytr[np.isfinite(xm[:, 0])])
    print(f"calibrated delta = {cal.coef_[0]:.2f}*delta | "
          f"slope-only = {smap.intercept_:.1f} + {smap.coef_[0]:.1f}*slope\n")

    # --- FeederBW metadata: top-10 by installed HP capacity -----------------
    fdir = "data/FeederBW"
    meta_csv = pd.read_csv(f"{fdir}/feeder_metadata.csv"); meta_csv["date"] = pd.to_datetime(meta_csv["date"])
    m24 = meta_csv[(meta_csv.date >= "2024-01-01") & (meta_csv.date < "2025-01-01")]
    static = m24.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder")
    static[HEAT] = static[HEAT].fillna(0)
    static["ElecHeat"] = static[HEAT].sum(axis=1)
    top = static.sort_values("heat_pumps_kW", ascending=False).head(10)
    wx = pd.read_parquet(f"{fdir}/weather_data.parquet")
    lo, hi = pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")

    rows = []
    for fid, r in top.iterrows():
        a = load_feeder_series(int(fid), fdir, wx, lo, hi)
        if a is None:
            continue
        one = pd.DataFrame.from_dict({fid: {"Total_Load": a["Total_Load"],
                                            "Temperature": a["Temperature"],
                                            "size": r["housing_units_count"]}}, orient="index")
        Xf_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
            one, T_base=T_DE, use_entity_index=True, show_progress=False, **B.CAP_FEATURE_KWARGS)
        Xf = hc.capacity_feature_matrix(Xf_raw, hc.select_scale_free_columns(Xf_raw),
                                        size=one["size"], peak=one["Total_Load"].apply(hc.series_peak))
        Xf = Xf.reindex(columns=X.columns)[sel].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        p_xgb = float(hc.clip_non_negative(xgbm.predict(Xf.fillna(med)))[0])
        s_mm = hs(a["Total_Load"], a["Temperature"], T_DE, daily_mean_mean_heating_season)
        s_xm = hs(a["Total_Load"], a["Temperature"], T_DE, daily_min_max_heating_season)
        p_del = float(max(cal.predict([[s_mm[1]]])[0], 0)) if np.isfinite(s_mm[1]) else np.nan
        p_slp = float(max(smap.predict([[s_xm[0]]])[0], 0)) if np.isfinite(s_xm[0]) else np.nan
        rows.append(dict(feeder=int(fid), HP_kW=r["heat_pumps_kW"], ElecHeat_kW=r["ElecHeat"],
                         HP_frac=r["heat_pumps_kW"]/r["ElecHeat"] if r["ElecHeat"] else 0,
                         housing=int(r["housing_units_count"]),
                         XGB=p_xgb, calDelta=p_del, slopeMap=p_slp))
    d = pd.DataFrame(rows).set_index("feeder")

    print("Top-10 FeederBW feeders by installed HP capacity -- predicted vs registry")
    print(d[["HP_kW", "ElecHeat_kW", "HP_frac", "housing", "XGB", "calDelta", "slopeMap"]]
          .to_string(float_format=lambda v: f"{v:.1f}"))

    def mape(t, p): t = np.asarray(t, float); p = np.asarray(p, float); m = t != 0; return float(np.mean(np.abs((t[m]-p[m])/t[m]))*100)
    print("\nMAPE vs registry HEAT_PUMPS_kW (HP-only ground truth):")
    for c in ["XGB", "calDelta", "slopeMap"]:
        print(f"  {c:9s}: {mape(d['HP_kW'], d[c]):6.1f}%")
    print("MAPE vs TOTAL electric-heating capacity (what the temp response reflects):")
    for c in ["XGB", "calDelta", "slopeMap"]:
        print(f"  {c:9s}: {mape(d['ElecHeat_kW'], d[c]):6.1f}%")
    # HP-dominant subset (HP_frac >= 0.6)
    hd = d[d["HP_frac"] >= 0.6]
    print(f"\nHP-dominant subset (HP_frac>=0.6, n={len(hd)}) MAPE vs HP_kW:")
    for c in ["XGB", "calDelta", "slopeMap"]:
        print(f"  {c:9s}: {mape(hd['HP_kW'], hd[c]):6.1f}%")
    d.to_csv("data/feederbw_top10_test.csv")
    print("\nSaved -> data/feederbw_top10_test.csv")


if __name__ == "__main__":
    main()
