"""Intensive (per-dwelling) capacity target -- scale-invariant transfer test.

Reuses the cached Swiss windowed-HDD features. The target is capacity DENSITY
(kW per dwelling): Swiss HP_Peak / size, FeederBW heat_pumps_kW / housing_units.
Density is comparable across feeders of any size, so it sidesteps the
train/deploy scale-distribution gap that sinks the absolute-kW target. Absolute
capacity at deployment is then density * housing_units.
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

import hp_capacity as hc
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV
import xgboost as xgb

T_BASE_CH, T_BASE_DE = 12.0, 15.0
FEATURE_KWARGS = dict(
    resolution=15, mild_thresh=10.0, cold_thresh=25.0, weekday_only=True,
    include_shape=False, include_minmax=True, include_quantiles=True,
    include_n_days=False, include_corr_features=False,
    include_climate_context=False, normalize_by_peak=True,
)


def select_scale_free(X):
    keep = [c for c in X.columns
            if c.endswith("_norm_peak") or "ratio_" in c or "normdelta_" in c]
    return X[keep].copy()


def clean(X):
    return X.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)


# --- Swiss: intensive target = HP_Peak / size -----------------------------
sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
X_swiss_raw = pickle.load(open("data/_X_swiss_pooled.pkl", "rb"))
X = clean(select_scale_free(X_swiss_raw))            # scale-free only, NO size anchor
y = (sub["HP_Peak"] / sub["size"]).astype(float)     # kW per dwelling
tr = sub.index[sub["split"] == "train"]
te = sub.index[sub["split"] == "test"]
print(f"Swiss density target (kW/dwelling): median {y.median():.3f} range [{y.min():.2f}, {y.max():.2f}]")

ridge = Pipeline([("imp", SimpleImputer(strategy="median")),
                  ("sc", StandardScaler()),
                  ("r", RidgeCV(alphas=np.logspace(-3, 4, 30), cv=5))]).fit(X.loc[tr], y.loc[tr])
xmodel = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                          subsample=0.8, colsample_bytree=0.7, reg_lambda=2.0,
                          tree_method="hist", n_jobs=-1)
xmodel.fit(X.loc[tr].fillna(X.loc[tr].median()), y.loc[tr])

print("\n=== internal test (unseen households), DENSITY target ===")
for nm, mdl, fill in [("Ridge", ridge, False), ("XGB", xmodel, True)]:
    Xte = X.loc[te].fillna(X.loc[tr].median()) if fill else X.loc[te]
    pred = hc.clip_non_negative(mdl.predict(Xte))
    m = hc.compute_metrics(y.loc[te].to_numpy(), pred)
    print(f"  {nm:5s} density: RMSE {m['rmse']:.3f} kW/dw | MAPE {m['mape']:.0f}% | R2 {m['r2']:.3f}")

# --- FeederBW: density target = heat_pumps_kW / housing_units --------------
fbw_dir = Path("data/FeederBW")
meas_dir = fbw_dir / "feeder_measurement_data_001-040" / "feeder_measurement_data_001-040"
meta = pd.read_csv(fbw_dir / "feeder_metadata.csv"); meta["date"] = pd.to_datetime(meta["date"])
wx = pd.read_parquet(fbw_dir / "weather_data.parquet")
meas = {int(fp.stem.split("_")[-1]): pd.read_parquet(fp) for fp in sorted(meas_dir.rglob("feeder_*.parquet"))}
m24 = meta[(meta["date"] >= "2024-01-01") & (meta["date"] < "2025-01-01")]
m24 = m24[m24["feeder"].isin(meas.keys())]
start = m24.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder")
end = m24.sort_values("date").drop_duplicates("feeder", keep="last").set_index("feeder")
static = start.combine_first(meta.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder"))

rows = {}
for fid, fdf in meas.items():
    fdf = fdf.copy(); fdf["timestamp_UTC"] = pd.to_datetime(fdf["timestamp_UTC"], utc=True)
    fdf = fdf[(fdf["timestamp_UTC"] >= pd.Timestamp("2024-01-01", tz="UTC")) &
              (fdf["timestamp_UTC"] < pd.Timestamp("2025-01-01", tz="UTC"))].sort_values("timestamp_UTC").set_index("timestamp_UTC")
    w = wx[wx["feeder"] == fid].copy(); w["timestamp_UTC"] = pd.to_datetime(w["timestamp_UTC"], utc=True)
    w = w.sort_values("timestamp_UTC").set_index("timestamp_UTC")
    load = fdf["active_power_kW"].resample("15min").mean().rename("Total_Load")
    temp = w["air_temperature_C"].resample("15min").interpolate("time").ffill().bfill().rename("Temperature")
    a = pd.concat([load, temp], axis=1, join="inner").dropna()
    if not a.empty and fid in static.index:
        rows[fid] = {"Total_Load": a["Total_Load"], "Temperature": a["Temperature"]}
fbw = pd.DataFrame.from_dict(rows, orient="index"); fbw.index.name = "Feeder_ID"
hp_change = (end["heat_pumps_kW"] - start["heat_pumps_kW"]).reindex(fbw.index)
fbw = fbw[hp_change.fillna(0) == 0]

X_fbw = clean(select_scale_free(
    hc.extract_windowed_hdd_features_from_entity_dataframe(
        fbw, T_base=T_BASE_DE, use_entity_index=True, show_progress=False, **FEATURE_KWARGS)
).reindex(columns=select_scale_free(X_swiss_raw).columns))
X_fbw = X_fbw[X.columns]

hu = static.loc[fbw.index, "housing_units_count"]
tgt = hc.feederbw_targets(static.loc[fbw.index])
valid = (hu > 0)                      # density undefined without dwelling count
dens_true = (tgt["HP_kW"] / hu)[valid]

print("\n=== FeederBW transfer, DENSITY target (kW/dwelling), HP-only ===")
for nm, mdl, fill in [("Ridge", ridge, False), ("XGB", xmodel, True)]:
    Xf = X_fbw.loc[valid].fillna(X.loc[tr].median()) if fill else X_fbw.loc[valid]
    dens_pred = pd.Series(hc.clip_non_negative(mdl.predict(Xf)), index=Xf.index)
    md = hc.compute_metrics(dens_true.to_numpy(), dens_pred.to_numpy())
    # back to absolute kW = density * housing_units, vs registered HP kW
    abs_pred = dens_pred * hu.loc[valid]
    abs_true = tgt.loc[valid, "HP_kW"]
    ma = hc.compute_metrics(abs_true[abs_true > 0].to_numpy(),
                            abs_pred[abs_true > 0].to_numpy())
    print(f"  {nm:5s} density : RMSE {md['rmse']:.3f} kW/dw | MAPE {md['mape']:.0f}% | R2 {md['r2']:.3f}")
    print(f"  {nm:5s} absolute: RMSE {ma['rmse']:.1f} kW    | MAPE {ma['mape']:.0f}% | R2 {ma['r2']:.3f}  (n={int((abs_true>0).sum())})")

print("\nDone.")
