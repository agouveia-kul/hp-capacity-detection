"""Extract the windowed-HDD features for the (regenerated) Swiss substations.

Rebuilds data/_X_swiss_pooled.pkl to match data/substations_data_pooled.pkl,
using the same feature configuration and national HDD base (12 degC) as the
capacity pipeline. Run after regenerate_substations_pooled.py.
"""
import pickle
import hp_capacity as hc

T_BASE_CH = 12.0
FEATURE_KWARGS = dict(
    resolution=15, mild_thresh=10.0, cold_thresh=25.0, weekday_only=True,
    include_shape=False, include_minmax=True, include_quantiles=True,
    include_n_days=False, include_corr_features=False,
    include_climate_context=False, normalize_by_peak=True)

sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
print(f"{len(sub)} substations | penetration (HP_ratio) "
      f"min {sub['HP_ratio'].min():.2f} median {sub['HP_ratio'].median():.2f} "
      f"max {sub['HP_ratio'].max():.2f}", flush=True)
print(f"HP_Peak target (kW): min {sub['HP_Peak'].min():.1f} "
      f"median {sub['HP_Peak'].median():.1f} max {sub['HP_Peak'].max():.1f}", flush=True)

X = hc.extract_windowed_hdd_features_from_entity_dataframe(
    sub, load_col="Total_Load", temp_col="Temperature",
    T_base=T_BASE_CH, use_entity_index=True, show_progress=True, **FEATURE_KWARGS)
pickle.dump(X, open("data/_X_swiss_pooled.pkl", "wb"))
print(f"Saved features {X.shape} -> data/_X_swiss_pooled.pkl")
