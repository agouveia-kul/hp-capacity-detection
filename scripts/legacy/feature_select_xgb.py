"""Feature-selection pipeline for the XGBoost HP-capacity model.

Goal: find the feature subset that minimises error on UNSEEN substations. The
selection is driven entirely by cross-validation on the household-disjoint TRAIN
split -- the held-out test split is never used to choose features (that would
leak). Only after a subset is fixed by CV is it scored on the test split, the
synthetic-WPUQ transfer set, and the real WPUQ feeder.

Pipeline
--------
1. Tune an XGBoost on ALL features (CV on train) -> baseline + a base config.
2. Rank features by CV-averaged gain importance (importance measured on each
   fold's own training data).
3. For a grid of k, score "top-k features" by 5-fold CV RMSE on train (unseen
   fold = unseen substations). Pick k* = the parsimonious choice: the smallest k
   whose CV RMSE is within 1 SE of the best (1-SE rule), so we do not chase noise.
4. Re-tune XGBoost on the k* selected features and report the honest test /
   WPUQ / real-feeder numbers vs the all-features baseline.

Outputs: models/xgb_selected_features.json, data/xgb_feature_selection_cv.csv,
paper/figures/fig_xgb_feature_selection.png.
"""
import json
import os

import numpy as np
import pandas as pd

import hp_capacity as hc
import benchmark_capacity_models as B
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
import xgboost as xgb

SEED = 42
CV = KFold(n_splits=5, shuffle=True, random_state=SEED)
os.makedirs("models", exist_ok=True)


def make_xgb(meta, importance_type=None):
    """Build an XGBRegressor from a tune_xgb_cv meta dict (fixed n_estimators)."""
    kw = dict(
        learning_rate=meta["eta"], n_estimators=int(meta["n_estimators_final"]),
        max_depth=int(meta["max_depth"]), gamma=meta["gamma"],
        subsample=meta["subsample"], reg_alpha=meta["reg_alpha"],
        reg_lambda=meta["reg_lambda"], min_child_weight=int(meta["min_child_weight"]),
        colsample_bytree=meta["colsample_bytree"], tree_method="hist", n_jobs=-1)
    if importance_type:
        kw["importance_type"] = importance_type
    return xgb.XGBRegressor(**kw)


def cv_rmse(Xtr_f, ytr, cols, meta):
    """5-fold CV RMSE on train using only `cols` (unseen fold = unseen subs)."""
    X = Xtr_f[cols].to_numpy()
    y = ytr.to_numpy()
    errs = []
    for tri, vai in CV.split(X):
        m = make_xgb(meta)
        m.fit(X[tri], y[tri])
        errs.append(np.sqrt(mean_squared_error(y[vai], np.maximum(m.predict(X[vai]), 0))))
    return float(np.mean(errs)), float(np.std(errs))


def evaluate(model, med, X, y, tr, te, Xw, yw, Xr, yr, cols):
    """Honest metrics on test / WPUQ / real feeder for a fitted model on `cols`."""
    fill = lambda D: D[cols].fillna(med[cols])
    te_m = hc.compute_metrics(y.loc[te].to_numpy(),
                              hc.clip_non_negative(model.predict(fill(X.loc[te]))))
    wp_m = hc.compute_metrics(yw.to_numpy(),
                              hc.clip_non_negative(model.predict(fill(Xw))))
    real = float(hc.clip_non_negative(model.predict(fill(Xr)))[0])
    return te_m, wp_m, real


def main():
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    Xtr, ytr = X.loc[tr], y.loc[tr]
    med = Xtr.median()
    Xtr_f = Xtr.fillna(med)
    cols_all = list(X.columns)
    print(f"Swiss train {len(tr)} / test {len(te)} | {len(cols_all)} features | "
          f"real feeder true {yr:.1f} kW\n", flush=True)

    # 1) tune on ALL features -> baseline model + base config for selection
    print("Tuning XGBoost on ALL features ...", flush=True)
    base_model, base_meta = hc.tune_xgb_cv(Xtr_f, ytr, max_evals=50, n_splits=5,
                                           verbose=True)
    te0, wp0, real0 = evaluate(base_model, med, X, y, tr, te, Xw, yw, Xr, yr, cols_all)
    print(f"  ALL {len(cols_all)}: test RMSE {te0['rmse']:.2f} R2 {te0['r2']:.3f} | "
          f"WPUQ R2 {wp0['r2']:.3f} | real {real0:.1f} kW\n", flush=True)

    # 2) rank features by CV-averaged gain importance
    print("Ranking features by CV-averaged gain importance ...", flush=True)
    imp = np.zeros(len(cols_all))
    Xa, ya = Xtr_f.to_numpy(), ytr.to_numpy()
    for tri, _ in CV.split(Xa):
        m = make_xgb(base_meta, importance_type="gain")
        m.fit(Xa[tri], ya[tri])
        imp += m.feature_importances_
    order = np.argsort(imp)[::-1]
    ranked = [cols_all[i] for i in order]

    # 3) CV RMSE vs k (k = number of top-ranked features kept)
    ks = sorted(set([k for k in [5, 10, 15, 20, 30, 40, 60, 80, 120, 160, 220,
                                 len(cols_all)] if k <= len(cols_all)]))
    print("Scoring feature-count grid by 5-fold CV on train:")
    rows = []
    for k in ks:
        mu, sd = cv_rmse(Xtr_f, ytr, ranked[:k], base_meta)
        rows.append({"k": k, "cv_rmse_mean": mu, "cv_rmse_std": sd})
        print(f"  k={k:4d}: CV RMSE {mu:6.2f} +/- {sd:4.2f}", flush=True)
    curve = pd.DataFrame(rows)

    # 1-SE rule: smallest k within 1 SE of the best mean CV RMSE
    j = int(curve["cv_rmse_mean"].idxmin())
    thresh = curve.loc[j, "cv_rmse_mean"] + curve.loc[j, "cv_rmse_std"]
    k_star = int(curve[curve["cv_rmse_mean"] <= thresh]["k"].min())
    sel = ranked[:k_star]
    print(f"\nbest-CV k={curve.loc[j,'k']} (RMSE {curve.loc[j,'cv_rmse_mean']:.2f}); "
          f"1-SE parsimonious k*={k_star} ({len(sel)} features)\n", flush=True)

    # 4) re-tune XGBoost on the selected features, honest evaluation
    print(f"Re-tuning XGBoost on {k_star} selected features ...", flush=True)
    sel_model, sel_meta = hc.tune_xgb_cv(Xtr_f[sel], ytr, max_evals=50, n_splits=5,
                                         verbose=True)
    te1, wp1, real1 = evaluate(sel_model, med, X, y, tr, te, Xw, yw, Xr, yr, sel)

    print("\n" + "=" * 66)
    print("XGBoost feature selection -- honest comparison (test = unseen subs)")
    print("=" * 66)
    print(f"{'feature set':22s} {'n':>4s} {'test RMSE':>10s} {'test R2':>8s} "
          f"{'WPUQ R2':>8s} {'real kW':>8s}")
    print(f"{'all features':22s} {len(cols_all):4d} {te0['rmse']:10.2f} "
          f"{te0['r2']:8.3f} {wp0['r2']:8.3f} {real0:8.1f}")
    print(f"{'selected (1-SE)':22s} {len(sel):4d} {te1['rmse']:10.2f} "
          f"{te1['r2']:8.3f} {wp1['r2']:8.3f} {real1:8.1f}")
    d = te0["rmse"] - te1["rmse"]          # all - selected; positive = improvement
    print(f"\ntest-RMSE reduction from selection: {d:+.2f} kW "
          f"({d / te0['rmse'] * 100:+.1f} %)  [positive = selected is better]")

    # save artifacts
    json.dump({"selected_features": sel, "k_star": k_star,
               "ranking": ranked, "base_meta": {k: float(v) for k, v in base_meta.items()},
               "sel_meta": {k: float(v) for k, v in sel_meta.items()},
               "test_all": te0, "test_sel": te1,
               "wpuq_all": wp0, "wpuq_sel": wp1,
               "real_all": real0, "real_sel": real1, "real_true": yr},
              open("models/xgb_selected_features.json", "w"), indent=2)
    curve.to_csv("data/xgb_feature_selection_cv.csv", index=False)
    print("\nSaved -> models/xgb_selected_features.json, "
          "data/xgb_feature_selection_cv.csv")

    # plot CV curve
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.errorbar(curve["k"], curve["cv_rmse_mean"], yerr=curve["cv_rmse_std"],
                marker="o", capsize=3, color="#2c7fb8", label="5-fold CV RMSE (train)")
    ax.axhline(thresh, color="#de2d26", ls=":", lw=1, label="best + 1 SE")
    ax.axvline(k_star, color="#238b45", ls="--", lw=1.2, label=f"selected k*={k_star}")
    ax.set_xscale("log"); ax.set_xlabel("number of top-ranked features (k)")
    ax.set_ylabel("CV RMSE on unseen substations (kW)")
    ax.set_title("XGBoost feature selection -- CV error vs feature-set size")
    ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
    plt.savefig("paper/figures/fig_xgb_feature_selection.png", dpi=150)
    print("Saved -> paper/figures/fig_xgb_feature_selection.png")


if __name__ == "__main__":
    main()
