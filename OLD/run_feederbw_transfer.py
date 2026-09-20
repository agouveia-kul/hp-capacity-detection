"""Corrected HP installed-capacity transfer: Swiss (HEAPO) -> FeederBW.

Implements the approved fixes for the windowed-HDD feature models:

* B1/B3 -- canonical household-disjoint split from the regenerated substations
  (the ``split`` column); the internal test is genuinely unseen households.
* A1    -- capacity target is the robust (99.9th-pct) HP peak, summed.
* A4    -- peak-normalised (scale-free) shape features PLUS explicit size
  anchors (household / housing-unit count and observed peak load), so an
  absolute-kW target transfers across feeders of very different size.
* A2    -- FeederBW is scored on three targets: HP-only capacity, total
  electric-heating capacity (the quantity the temperature response really
  reflects), and an HP-dominant feeder subset.
* B4    -- feeders with zero registered HP capacity are dropped from the
  HP-estimation metric (they are a detection, not an estimation, case).
* C3    -- XGBoost tuned by cross-validation (hp_capacity.tune_xgb_cv).

T_base is per national HDD convention: 12 degC Switzerland, 15 degC Germany.
"""
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

import hp_capacity as hc
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV

# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------
T_BASE_CH, T_BASE_DE = 12.0, 15.0
MILD, COLD = 10.0, 25.0
RES = 15
FEATURE_KWARGS = dict(
    resolution=RES, mild_thresh=MILD, cold_thresh=COLD, weekday_only=True,
    include_shape=False, include_minmax=True, include_quantiles=True,
    include_n_days=False, include_corr_features=False,
    include_climate_context=False, normalize_by_peak=True,
)
POOLED = "data/substations_data_pooled.pkl"
SWISS_FEAT_CACHE = "data/_X_swiss_pooled.pkl"


def select_scale_free(X):
    """Keep only dimensionless features (peak-normalised magnitudes + ratios)."""
    keep = [c for c in X.columns
            if c.endswith("_norm_peak") or "ratio_" in c or "normdelta_" in c]
    return X[keep].copy()


def peak_of(series):
    return float(pd.Series(series).dropna().max())


# --------------------------------------------------------------------------
# 1) Swiss training data (regenerated, household-disjoint split)
# --------------------------------------------------------------------------
print("Loading pooled substations ...", flush=True)
sub = pickle.load(open(POOLED, "rb"))
assert "split" in sub.columns, "regenerate substations first (needs 'split')"
print(f"  {len(sub)} substations | split {sub['split'].value_counts().to_dict()}")

if os.path.exists(SWISS_FEAT_CACHE):
    X_swiss_raw = pickle.load(open(SWISS_FEAT_CACHE, "rb"))
else:
    print("Extracting Swiss windowed-HDD features @T_base=12 ...", flush=True)
    X_swiss_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
        sub, load_col="Total_Load", temp_col="Temperature",
        T_base=T_BASE_CH, use_entity_index=True, **FEATURE_KWARGS)
    pickle.dump(X_swiss_raw, open(SWISS_FEAT_CACHE, "wb"))

X_swiss = select_scale_free(X_swiss_raw)
# A4 scale anchors
X_swiss = hc.add_scale_features(X_swiss, sub["size"], name="Feature Scale_size")
X_swiss = hc.add_scale_features(
    X_swiss, sub["Total_Load"].apply(peak_of), name="Feature Scale_peak")
X_swiss = X_swiss.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)

y_swiss = sub["HP_Peak"].astype(float)
tr = sub.index[sub["split"] == "train"]
te = sub.index[sub["split"] == "test"]

print(f"  feature matrix: {X_swiss.shape} | scale-free + 2 anchors")
print(f"  Swiss HP_Peak (kW): median {y_swiss.median():.1f} range [{y_swiss.min():.0f}, {y_swiss.max():.0f}]")

# --------------------------------------------------------------------------
# 2) Train models on the train split, honest test on the test split
# --------------------------------------------------------------------------
def make_ridge():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("ridge", RidgeCV(alphas=np.logspace(-3, 4, 30), cv=5)),
    ])

print("\nTraining Ridge (RidgeCV) ...", flush=True)
ridge = make_ridge().fit(X_swiss.loc[tr], y_swiss.loc[tr])

print("Tuning + training XGBoost (CV) ...", flush=True)
xgb_model, xgb_meta = hc.tune_xgb_cv(
    X_swiss.loc[tr].fillna(X_swiss.loc[tr].median()), y_swiss.loc[tr],
    max_evals=60, n_splits=4, verbose=True)

for name, model, needs_fill in [("Ridge", ridge, False), ("XGBoost", xgb_model, True)]:
    Xte = X_swiss.loc[te]
    if needs_fill:
        Xte = Xte.fillna(X_swiss.loc[tr].median())
    pred = hc.clip_non_negative(model.predict(Xte))
    m = hc.compute_metrics(y_swiss.loc[te].to_numpy(), pred)
    print(f"  [internal test / unseen households] {name}: "
          f"RMSE {m['rmse']:.1f} kW | MAE {m['mae']:.1f} | MAPE {m['mape']:.0f}% | R2 {m['r2']:.3f}")

# --------------------------------------------------------------------------
# 3) FeederBW transfer (ported from notebook cell 146)
# --------------------------------------------------------------------------
print("\nLoading FeederBW ...", flush=True)
fbw_dir = Path("data/FeederBW")
meas_dir = fbw_dir / "feeder_measurement_data_001-040" / "feeder_measurement_data_001-040"
meta = pd.read_csv(fbw_dir / "feeder_metadata.csv")
wx = pd.read_parquet(fbw_dir / "weather_data.parquet")
meta["date"] = pd.to_datetime(meta["date"])

meas = {}
for fp in sorted(meas_dir.rglob("feeder_*.parquet")):
    meas[int(fp.stem.split("_")[-1])] = pd.read_parquet(fp)

meta_2024 = meta[(meta["date"] >= "2024-01-01") & (meta["date"] < "2025-01-01")]
meta_2024 = meta_2024[meta_2024["feeder"].isin(meas.keys())]
start_2024 = meta_2024.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder")
end_2024 = meta_2024.sort_values("date").drop_duplicates("feeder", keep="last").set_index("feeder")
static_all = meta.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder")
static = start_2024.combine_first(static_all)

rows = {}
for fid, fdf in meas.items():
    fdf = fdf.copy()
    fdf["timestamp_UTC"] = pd.to_datetime(fdf["timestamp_UTC"], utc=True)
    fdf = fdf[(fdf["timestamp_UTC"] >= pd.Timestamp("2024-01-01", tz="UTC")) &
              (fdf["timestamp_UTC"] < pd.Timestamp("2025-01-01", tz="UTC"))]
    fdf = fdf.sort_values("timestamp_UTC").set_index("timestamp_UTC")

    w = wx[wx["feeder"] == fid].copy()
    w["timestamp_UTC"] = pd.to_datetime(w["timestamp_UTC"], utc=True)
    w = w.sort_values("timestamp_UTC").set_index("timestamp_UTC")

    load = fdf["active_power_kW"].resample("15min").mean().rename("Total_Load")
    temp = (w["air_temperature_C"].resample("15min").interpolate("time")
            .ffill().bfill().rename("Temperature"))
    aligned = pd.concat([load, temp], axis=1, join="inner").dropna()
    if aligned.empty or fid not in static.index:
        continue
    rows[fid] = {"Total_Load": aligned["Total_Load"], "Temperature": aligned["Temperature"]}

fbw = pd.DataFrame.from_dict(rows, orient="index")
fbw.index.name = "Feeder_ID"

# change-free feeders only (stable HP capacity over 2024), from static metadata
hp_change = (end_2024["heat_pumps_kW"] - start_2024["heat_pumps_kW"]).reindex(fbw.index)
fbw = fbw[hp_change.fillna(0) == 0]
tgt = hc.feederbw_targets(static.loc[fbw.index])
print(f"  {len(fbw)} change-free feeders | HP>0: {(tgt['HP_kW']>0).sum()} | HP-dominant: {tgt['HP_dominant'].sum()}")

# features @T_base=15 + same scale anchors
X_fbw_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
    fbw, load_col="Total_Load", temp_col="Temperature",
    T_base=T_BASE_DE, use_entity_index=True, show_progress=False, **FEATURE_KWARGS)
X_fbw = select_scale_free(X_fbw_raw).reindex(columns=select_scale_free(X_swiss_raw).columns)
X_fbw = hc.add_scale_features(X_fbw, static.loc[fbw.index, "housing_units_count"], name="Feature Scale_size")
X_fbw = hc.add_scale_features(X_fbw, fbw["Total_Load"].apply(peak_of), name="Feature Scale_peak")
X_fbw = X_fbw[X_swiss.columns]  # exact column order
X_fbw = X_fbw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)

pred_ridge = pd.Series(hc.clip_non_negative(ridge.predict(X_fbw)), index=X_fbw.index)
pred_xgb = pd.Series(hc.clip_non_negative(
    xgb_model.predict(X_fbw.fillna(X_swiss.loc[tr].median()))), index=X_fbw.index)

print("\n=== FeederBW transfer (Swiss-trained, national HDD bases 12/15) ===")
for tname, tcol, mask in [
    ("HP-only (HP>0)", "HP_kW", tgt["HP_kW"] > 0),
    ("Total electric heating", "ElecHeat_kW", tgt["ElecHeat_kW"] > 0),
    ("HP-only, HP-dominant feeders", "HP_kW", tgt["HP_dominant"] & (tgt["HP_kW"] > 0)),
]:
    idx = tgt.index[mask]
    if len(idx) < 3:
        print(f"  {tname}: n={len(idx)} (too few)"); continue
    yt = tgt.loc[idx, tcol].to_numpy()
    for mname, pred in [("Ridge", pred_ridge), ("XGB", pred_xgb)]:
        m = hc.compute_metrics(yt, pred.loc[idx].to_numpy())
        print(f"  {tname:32s} n={len(idx):2d} {mname:5s}: "
              f"RMSE {m['rmse']:.1f} kW | MAE {m['mae']:.1f} | MAPE {m['mape']:.0f}% | R2 {m['r2']:.3f}")

print("\nDone.")
