"""In-distribution capacity estimation WITHIN FeederBW (train/test on feeders).

Motivation (from the metadata scan): only ~12 of 200 feeders are HP-dominant,
so HP-only estimation is data-starved. The net-load temperature response
measures TOTAL electric-heating capacity, which many feeders have. This script
estimates ElecHeat_kW (HP + storage + resistive + flow + hot-water) with
honest, feeder-disjoint cross-validation, and reports HP-only on the
HP-dominant subset as a stretch target.

Small n (~23 usable feeders in the 40 downloaded) => a compact, interpretable
model (temperature sensitivity + size), leave-one-feeder-out CV, and a
substation-grouped CV so feeders sharing a substation never split across folds.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import hp_capacity as hc
from hp_common import daily_mean_mean_heating_season, fit_hockey_stick, T_BALANCE_BOUNDS
from sklearn.linear_model import RidgeCV, LinearRegression
from sklearn.model_selection import LeaveOneOut, GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

T_BASE_DE = 15.0            # German national HDD base
HEAT_SEASON_DE = 15.0

# --------------------------------------------------------------------------
# load every downloaded feeder + metadata (all batches, via the helper)
# --------------------------------------------------------------------------
fbw, static, end = hc.load_feederbw("data/FeederBW", year=2024)
fbw.index.name = "Feeder_ID"
HEAT = list(hc._FBW_HEAT_COLS)

# targets + stability
h = static.reindex(fbw.index)[HEAT].fillna(0)
he = static.reindex(fbw.index)
tgt = pd.DataFrame(index=fbw.index)
tgt["ElecHeat_kW"] = h.sum(axis=1)
tgt["HP_kW"] = h["heat_pumps_kW"]
tgt["HP_frac"] = np.where(tgt.ElecHeat_kW > 0, tgt.HP_kW / tgt.ElecHeat_kW, 0)
tgt["housing"] = he["housing_units_count"]
tgt["substation"] = he["substation"]
eh_stable = (end.reindex(fbw.index)[HEAT].fillna(0).sum(axis=1) - tgt["ElecHeat_kW"]).abs().fillna(1e9) == 0

usable = tgt[(tgt.ElecHeat_kW > 0) & eh_stable & (tgt.housing > 0)].index
print(f"downloaded feeders: {len(fbw)} | usable for ElecHeat estimation: {len(usable)} "
      f"| across {tgt.loc[usable,'substation'].nunique()} substations")
print(f"ElecHeat_kW target: median {tgt.loc[usable,'ElecHeat_kW'].median():.1f} "
      f"range [{tgt.loc[usable,'ElecHeat_kW'].min():.1f}, {tgt.loc[usable,'ElecHeat_kW'].max():.1f}]")

# --------------------------------------------------------------------------
# features: (1) compact temperature-sensitivity + size, (2) windowed-HDD
# --------------------------------------------------------------------------
sens = {}
for fid in fbw.index:
    try:
        x, y = daily_mean_mean_heating_season(fbw.loc[fid, "Temperature"],
                                              fbw.loc[fid, "Total_Load"], HEAT_SEASON_DE)
        if len(x) >= 20:
            base, slope, tb, r2 = fit_hockey_stick(x, y, T_BALANCE_BOUNDS)
            sens[fid] = dict(HP_Sensitivity=slope, Base_Load=base, T_Balance=tb, fit_r2=r2)
    except Exception:
        pass
sens = pd.DataFrame(sens).T
peak = fbw["Total_Load"].apply(lambda s: float(pd.Series(s).dropna().max()))

Xc = pd.DataFrame(index=fbw.index)
Xc["HP_Sensitivity"] = sens["HP_Sensitivity"]
Xc["Peak_Load"] = peak
Xc["housing_units"] = tgt["housing"]
Xc = Xc.loc[usable].dropna()
idx = Xc.index
y_eh = tgt.loc[idx, "ElecHeat_kW"].astype(float)
groups = tgt.loc[idx, "substation"].astype(int)


def report(name, y_true, y_pred):
    m = hc.compute_metrics(y_true.to_numpy(), np.maximum(y_pred, 0))
    print(f"  {name:34s} RMSE {m['rmse']:5.1f} kW | MAE {m['mae']:5.1f} | MAPE {m['mape']:4.0f}% | R2 {m['r2']:.3f}")


print(f"\n=== ElecHeat_kW, compact model [sensitivity, peak, housing], n={len(idx)} ===")
# leave-one-feeder-out
ridge = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
                  ("r", RidgeCV(alphas=np.logspace(-2, 4, 25)))])
loo = cross_val_predict(ridge, Xc, y_eh, cv=LeaveOneOut())
report("Ridge, leave-one-feeder-out", y_eh, loo)
# substation-grouped CV
gkf = GroupKFold(n_splits=min(5, groups.nunique()))
gcv = cross_val_predict(ridge, Xc, y_eh, cv=gkf, groups=groups)
report("Ridge, substation-grouped CV", y_eh, gcv)
# single-feature interpretable baseline: ElecHeat ~ HP_Sensitivity
lin = LinearRegression()
loo_lin = cross_val_predict(lin, Xc[["HP_Sensitivity"]], y_eh, cv=LeaveOneOut())
report("Sensitivity-only (LOO)", y_eh, loo_lin)
r = np.corrcoef(Xc["HP_Sensitivity"], y_eh)[0, 1]
print(f"  corr(HP_Sensitivity, ElecHeat_kW) = {r:.3f}")

# windowed-HDD feature set, heavily selected (SelectKBest) for small n
from sklearn.feature_selection import SelectKBest, f_regression
Xw = hc.extract_windowed_hdd_features_from_entity_dataframe(
    fbw.loc[idx], T_base=T_BASE_DE, use_entity_index=True, show_progress=False,
    resolution=15, mild_thresh=10.0, cold_thresh=25.0, weekday_only=True,
    include_shape=False, include_minmax=True, include_quantiles=True,
    include_n_days=False, include_corr_features=False, normalize_by_peak=True)
Xw = Xw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
Xw["Peak_Load"] = peak.loc[idx]; Xw["housing_units"] = tgt.loc[idx, "housing"]
pipe_w = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
                   ("sel", SelectKBest(f_regression, k=6)),
                   ("r", RidgeCV(alphas=np.logspace(-2, 4, 25)))])
gcv_w = cross_val_predict(pipe_w, Xw, y_eh, cv=gkf, groups=groups)
report("Windowed-HDD k=6, grouped CV", y_eh, gcv_w)

# --------------------------------------------------------------------------
# HP-only on the HP-dominant subset (stretch; likely too few)
# --------------------------------------------------------------------------
hp_dom = tgt.loc[idx][(tgt.loc[idx, "HP_frac"] >= 0.5) & (tgt.loc[idx, "HP_kW"] > 0)].index
print(f"\n=== HP-only, HP-dominant subset: n={len(hp_dom)} ===")
if len(hp_dom) >= 8:
    yhp = tgt.loc[hp_dom, "HP_kW"].astype(float)
    loo_hp = cross_val_predict(ridge, Xc.loc[hp_dom], yhp, cv=LeaveOneOut())
    report("Ridge HP-only (LOO)", yhp, loo_hp)
else:
    print(f"  too few HP-dominant feeders in the 40 downloaded ({len(hp_dom)}); "
          f"download more (see priority list) before an HP-only model is meaningful.")

print("\nDone.")
