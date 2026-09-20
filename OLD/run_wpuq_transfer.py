"""Swiss -> WPUQ transferability, using the saved TUNED Swiss capacity model.

WPUQ (37 HP-equipped houses) is the fair transfer target: HP-rich like the
Swiss synthetics, so it isolates transfer from the low-penetration /
storage-heater confound that sinks FeederBW. Many synthetic WPUQ substations
are built over the range the Swiss model was trained on, and predicted with the
tuned XGB (and Ridge) from models/capacity_swiss.pkl. National HDD bases 12/15.
"""
import pickle

import numpy as np
import pandas as pd

import hp_capacity as hc
import hp_pools as hpp

T_BASE_DE = 15.0
FEATURE_KWARGS = dict(
    resolution=15, mild_thresh=10.0, cold_thresh=25.0, weekday_only=True,
    include_shape=False, include_minmax=True, include_quantiles=True,
    include_n_days=False, include_corr_features=False,
    include_climate_context=False, normalize_by_peak=True,
)

M = pickle.load(open("models/capacity_swiss.pkl", "rb"))
ridge, xgb_model = M["ridge"], M["xgb"]
scalefree_cols, feature_cols, train_median = M["scalefree_cols"], M["feature_cols"], M["train_median"]

# --- build synthetic WPUQ substations, extract features @15, predict --------
pool = hpp.build_pool_wpuq(verbose=False)
wp = hc.build_wpuq_substations(pool, n=400, size_range=(10, 37), pen_max=0.5, seed=7)
print(f"{len(wp)} WPUQ substations | HP_Peak median {wp['HP_Peak'].median():.1f} kW "
      f"range [{wp['HP_Peak'].min():.0f}, {wp['HP_Peak'].max():.0f}]")

Xw_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
    wp, T_base=T_BASE_DE, use_entity_index=True, show_progress=True, **FEATURE_KWARGS)
Xw = hc.capacity_feature_matrix(
    Xw_raw, scalefree_cols, size=wp["size"], peak=wp["Total_Load"].apply(hc.series_peak))
Xw = Xw[feature_cols]
yw = wp["HP_Peak"].to_numpy()

print("\n=== Swiss -> WPUQ transfer (tuned model) ===")
for nm, mdl, fill in [("Ridge", ridge, False), ("XGB (tuned)", xgb_model, True)]:
    pred = hc.clip_non_negative(mdl.predict(Xw.fillna(train_median) if fill else Xw))
    m = hc.compute_metrics(yw, pred)
    print(f"  {nm:12s}: RMSE {m['rmse']:.1f} kW | MAE {m['mae']:.1f} | "
          f"MAPE {m['mape']:.0f}% | R2 {m['r2']:.3f}")
print("\nDone.")
