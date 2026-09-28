"""Train and SAVE the Swiss HP installed-capacity models (Ridge + tuned XGB).

Saved once to models/capacity_swiss.pkl so the WPUQ / FeederBW transfer and the
notebook reuse the same fitted models without re-tuning. Target is the robust
99.9th-pct HP peak summed over the substation; features are the scale-free
windowed-HDD set plus two explicit size anchors (household count, peak load).
"""
import os
import pickle

import numpy as np
import pandas as pd

import hp_capacity as hc
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV

OUT = "models/capacity_swiss.pkl"


def main():
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    Xs_raw = pickle.load(open("data/_X_swiss_pooled.pkl", "rb"))

    scalefree_cols = hc.select_scale_free_columns(Xs_raw)
    X = hc.capacity_feature_matrix(
        Xs_raw, scalefree_cols,
        size=sub["size"], peak=sub["Total_Load"].apply(hc.series_peak))
    y = sub["HP_Peak"].astype(float)
    tr = sub.index[sub["split"] == "train"]
    te = sub.index[sub["split"] == "test"]

    print(f"train {len(tr)} / test {len(te)} substations | {X.shape[1]} features")

    ridge = Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc", StandardScaler()),
                      ("r", RidgeCV(alphas=np.logspace(-3, 4, 30), cv=5))]).fit(X.loc[tr], y.loc[tr])

    train_median = X.loc[tr].median()
    xgb_model, xgb_meta = hc.tune_xgb_cv(
        X.loc[tr].fillna(train_median), y.loc[tr], max_evals=60, n_splits=4, verbose=True)

    print("\n=== internal test (unseen households) ===")
    for nm, mdl, fill in [("Ridge", ridge, False), ("XGB", xgb_model, True)]:
        Xte = X.loc[te].fillna(train_median) if fill else X.loc[te]
        pred = hc.clip_non_negative(mdl.predict(Xte))
        m = hc.compute_metrics(y.loc[te].to_numpy(), pred)
        print(f"  {nm:5s}: RMSE {m['rmse']:.1f} kW | MAE {m['mae']:.1f} | "
              f"MAPE {m['mape']:.0f}% | R2 {m['r2']:.3f}")

    os.makedirs("models", exist_ok=True)
    pickle.dump(dict(ridge=ridge, xgb=xgb_model, feature_cols=list(X.columns),
                     scalefree_cols=list(scalefree_cols), train_median=train_median,
                     xgb_meta=xgb_meta), open(OUT, "wb"))
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()
