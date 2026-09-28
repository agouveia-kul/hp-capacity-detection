"""Benchmark regressors for HP installed-capacity estimation on the Swiss
windowed-HDD features (scale-free shape features + 2 size anchors).

Every model is hyperparameter-tuned by 5-fold CV on the household-disjoint
TRAIN split, refit on the full train split, then scored on:
  * the held-out TEST split  (unseen Swiss households -- the honest metric)
  * the Swiss -> WPUQ transfer (external HP-rich German population)

Models: Linear Regression, Lasso, Ridge, Elastic Net, SVR (RBF), XGBoost, FFNN.
FeederBW is intentionally excluded (HP penetration too low for estimation).
Target = robust 99.9th-pct HP peak summed over the substation. HDD bases 12/15.
"""
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")   # quiet TF before import
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")  # reproducible float order
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")   # reproducible NN training
import pickle
import time
import warnings

import numpy as np
import pandas as pd

import hp_capacity as hc
import hp_pools as hpp
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor
from sklearn.model_selection import KFold, GridSearchCV, RandomizedSearchCV
from sklearn.linear_model import LinearRegression, Lasso, Ridge, ElasticNet
from sklearn.svm import SVR
from sklearn.metrics import r2_score
from scipy.stats import loguniform

warnings.filterwarnings("ignore")
SEED = 42
CV = KFold(n_splits=5, shuffle=True, random_state=SEED)
WPUQ_FEAT_CACHE = "data/_X_wpuq_bench.pkl"
WPUQ_REAL_CACHE = "data/_X_wpuq_real.pkl"

CAP_FEATURE_KWARGS = dict(
    resolution=15, mild_thresh=10.0, cold_thresh=25.0, weekday_only=True,
    include_shape=False, include_minmax=True, include_quantiles=True,
    include_n_days=False, include_corr_features=False,
    include_climate_context=False, normalize_by_peak=True)
T_BASE_DE = 15.0


# --------------------------------------------------------------------------
# data: Swiss train/test + WPUQ transfer set (same feature construction)
# --------------------------------------------------------------------------
def load_data():
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    Xraw = pickle.load(open("data/_X_swiss_pooled.pkl", "rb"))
    sf = hc.select_scale_free_columns(Xraw)
    X = hc.capacity_feature_matrix(
        Xraw, sf, size=sub["size"], peak=sub["Total_Load"].apply(hc.series_peak))
    X = X.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    y = sub["HP_Peak"].astype(float)
    tr = sub.index[sub["split"] == "train"]
    te = sub.index[sub["split"] == "test"]
    cols = list(X.columns)

    if os.path.exists(WPUQ_FEAT_CACHE):
        Xw, yw = pickle.load(open(WPUQ_FEAT_CACHE, "rb"))
    else:
        print("Building WPUQ transfer set ...", flush=True)
        pool = hpp.build_pool_wpuq(verbose=False)
        wp = hc.build_wpuq_substations(pool, n=400, size_range=(10, 37),
                                       pen_max=0.5, seed=7)
        Xw_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
            wp, T_base=T_BASE_DE, use_entity_index=True, show_progress=False,
            **CAP_FEATURE_KWARGS)
        Xw = hc.capacity_feature_matrix(
            Xw_raw, sf, size=wp["size"],
            peak=wp["Total_Load"].apply(hc.series_peak))[cols]
        Xw = Xw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        yw = wp["HP_Peak"].astype(float)
        pickle.dump((Xw, yw), open(WPUQ_FEAT_CACHE, "wb"))

    # the single REAL WPUQ feeder (true aggregate of all 37 houses)
    if os.path.exists(WPUQ_REAL_CACHE):
        Xr, yr = pickle.load(open(WPUQ_REAL_CACHE, "rb"))
    else:
        print("Building REAL WPUQ feeder ...", flush=True)
        pool = hpp.build_pool_wpuq(verbose=False)
        rf = hc.build_wpuq_real_feeder(pool)
        Xr_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
            rf, T_base=T_BASE_DE, use_entity_index=True, show_progress=False,
            **CAP_FEATURE_KWARGS)
        Xr = hc.capacity_feature_matrix(
            Xr_raw, sf, size=rf["size"],
            peak=rf["Total_Load"].apply(hc.series_peak))[cols]
        Xr = Xr.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        yr = float(rf["HP_Peak"].iloc[0])
        pickle.dump((Xr, yr), open(WPUQ_REAL_CACHE, "wb"))
    return X, y, tr, te, Xw, yw, Xr, yr


# --------------------------------------------------------------------------
# model zoo -- each returns a searcher already configured for CV tuning
# (linear/SVR/FFNN standardise X; SVR & FFNN also standardise y)
# --------------------------------------------------------------------------
def pre():
    return [("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]


def wrap_y(est):
    return TransformedTargetRegressor(regressor=est, transformer=StandardScaler())


def build_searchers():
    S = {}

    # 1) Linear Regression -- nothing to tune (baseline)
    S["LinearReg"] = ("fixed", Pipeline(pre() + [("m", LinearRegression())]))

    # 2) Lasso
    S["Lasso"] = ("grid", Pipeline(pre() + [("m", Lasso(max_iter=20000))]),
                  {"m__alpha": np.logspace(-3, 2, 20)})

    # 3) Ridge
    S["Ridge"] = ("grid", Pipeline(pre() + [("m", Ridge())]),
                  {"m__alpha": np.logspace(-3, 4, 25)})

    # 4) Elastic Net
    S["ElasticNet"] = ("grid", Pipeline(pre() + [("m", ElasticNet(max_iter=20000))]),
                       {"m__alpha": np.logspace(-3, 2, 12),
                        "m__l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9]})

    # 5) SVR (RBF) -- standardise target too
    svr_pipe = Pipeline(pre() + [("m", wrap_y(SVR(kernel="rbf")))])
    S["SVR"] = ("rand", svr_pipe,
                {"m__regressor__C": loguniform(1e0, 1e3),
                 "m__regressor__gamma": loguniform(1e-4, 1e-1),
                 "m__regressor__epsilon": [0.01, 0.05, 0.1, 0.2]}, 40)

    # (FFNN is a TensorFlow/Keras model, tuned separately in tune_keras_ffnn)
    return S


def fit_searcher(spec, Xtr, ytr):
    kind = spec[0]
    if kind == "fixed":
        return spec[1].fit(Xtr, ytr), {}
    if kind == "grid":
        gs = GridSearchCV(spec[1], spec[2], scoring="r2", cv=CV, n_jobs=-1)
        gs.fit(Xtr, ytr)
        return gs.best_estimator_, gs.best_params_
    if kind == "rand":
        rs = RandomizedSearchCV(spec[1], spec[2], n_iter=spec[3], scoring="r2",
                                cv=CV, n_jobs=-1, random_state=SEED)
        rs.fit(Xtr, ytr)
        return rs.best_estimator_, rs.best_params_


# --------------------------------------------------------------------------
# FFNN -- TensorFlow/Keras, tuned by random search over 3-fold CV on train
# (X imputed+standardised, y standardised; predictions clipped >=0 in kW space)
# --------------------------------------------------------------------------
def tune_keras_ffnn(Xtr, ytr, Xte, yte, Xw, yw, seed=SEED, n_seeds=3, Xextra=None):
    """FFNN (TensorFlow/Keras), hyperparameter-tuned like the other models.

    Architecture / learning-rate / L2 are selected by the same KFold CV on the
    train split used for the sklearn models (op-determinism on, so each fit is
    reproducible). The best config is then refit over ``n_seeds`` seeds and the
    reported metrics are the PER-SEED MEAN (with the test-R2 spread), since the
    net is more seed-sensitive than the deterministic tree/kernel models."""
    import tensorflow as tf
    from tensorflow import keras
    try:
        tf.config.experimental.enable_op_determinism()   # reproducible NN training
    except Exception:
        pass

    med = Xtr.median()
    xsc = StandardScaler().fit(Xtr.fillna(med).to_numpy())
    ysc = StandardScaler().fit(ytr.to_numpy().reshape(-1, 1))
    prep = lambda X: xsc.transform(X.fillna(med).to_numpy()).astype("float32")
    Xtr_a, Xte_a, Xw_a = prep(Xtr), prep(Xte), prep(Xw)
    ytr_a = ysc.transform(ytr.to_numpy().reshape(-1, 1)).astype("float32")
    ytr_np = ytr.to_numpy()
    n_in = Xtr_a.shape[1]
    inv = lambda A: np.maximum(ysc.inverse_transform(A).ravel(), 0.0)

    def build(cfg):
        reg = keras.regularizers.l2(cfg["l2"]) if cfg["l2"] > 0 else None
        m = keras.Sequential([keras.layers.Input(shape=(n_in,))])
        for u in cfg["arch"]:
            m.add(keras.layers.Dense(u, activation="relu", kernel_regularizer=reg))
        m.add(keras.layers.Dense(1))
        m.compile(optimizer=keras.optimizers.Adam(cfg["lr"]), loss="mse")
        return m

    es = keras.callbacks.EarlyStopping(patience=40, restore_best_weights=True)

    # --- hyperparameter search: KFold CV on train (same CV as sklearn models) --
    grid = [dict(arch=a, lr=lr, l2=l2)
            for a in [(64,), (128,), (128, 64), (256, 128)]
            for lr in (1e-3, 5e-4) for l2 in (0.0, 1e-4)]
    best = None
    for cfg in grid:
        sc = []
        for tri, vai in CV.split(Xtr_a):
            keras.utils.set_random_seed(seed)
            m = build(cfg)
            m.fit(Xtr_a[tri], ytr_a[tri], validation_data=(Xtr_a[vai], ytr_a[vai]),
                  epochs=500, batch_size=32, verbose=0, callbacks=[es])
            sc.append(r2_score(ytr_np[vai], inv(m.predict(Xtr_a[vai], verbose=0))))
        s = float(np.mean(sc))
        if best is None or s > best["cv"]:
            best = {"cv": s, "cfg": cfg}
    cfg = best["cfg"]

    # --- refit best config over seeds, report per-seed-mean metrics -----------
    yte_np, yw_np = np.array(yte, dtype=float), np.array(yw, dtype=float)
    Xr_a = prep(Xextra) if Xextra is not None else None
    te_ms, wp_ms, te_r2s, extra_preds = [], [], [], []
    for s in range(n_seeds):
        keras.utils.set_random_seed(seed + s)
        m = build(cfg)
        m.fit(Xtr_a, ytr_a, validation_split=0.15, epochs=500, batch_size=32,
              verbose=0, callbacks=[es])
        te_ms.append(hc.compute_metrics(yte_np, inv(m.predict(Xte_a, verbose=0))))
        wp_ms.append(hc.compute_metrics(yw_np, inv(m.predict(Xw_a, verbose=0))))
        te_r2s.append(te_ms[-1]["r2"])
        if Xr_a is not None:
            extra_preds.append(inv(m.predict(Xr_a, verbose=0)))
    te_m = {k: float(np.mean([d[k] for d in te_ms])) for k in te_ms[0]}
    wp_m = {k: float(np.mean([d[k] for d in wp_ms])) for k in wp_ms[0]}
    cfg_out = {**cfg, "cv_r2": round(best["cv"], 3), "n_seeds": n_seeds,
               "test_r2_std": round(float(np.std(te_r2s)), 3)}
    extra_pred = (np.mean(extra_preds, axis=0) if extra_preds else None)
    return te_m, wp_m, cfg_out, extra_pred


# --------------------------------------------------------------------------
def main():
    X, y, tr, te, Xw, yw, Xr, yr = load_data()
    size_real = float(Xr["Feature Scale_size"].iloc[0])
    print(f"Swiss: train {len(tr)} / test {len(te)} | {X.shape[1]} features | "
          f"WPUQ transfer: {len(Xw)} substations", flush=True)
    print(f"REAL WPUQ feeder: {int(size_real)} houses | TRUE installed HP "
          f"capacity {yr:.1f} kW\n", flush=True)

    Xtr, ytr = X.loc[tr], y.loc[tr]
    rows = []
    real = {}   # model -> predicted kW on the real feeder
    for name, spec in build_searchers().items():
        t0 = time.time()
        if name == "XGBoost":
            continue  # handled separately below
        best, params = fit_searcher(spec, Xtr, ytr)
        te_m = hc.compute_metrics(y.loc[te].to_numpy(),
                                  hc.clip_non_negative(best.predict(X.loc[te])))
        wp_m = hc.compute_metrics(yw.to_numpy(),
                                  hc.clip_non_negative(best.predict(Xw)))
        real[name] = float(hc.clip_non_negative(best.predict(Xr))[0])
        rows.append((name, te_m, wp_m))
        pstr = {k.split("__")[-1]: (round(v, 4) if isinstance(v, float) else v)
                for k, v in params.items()}
        print(f"[{name:10s}] {time.time()-t0:5.1f}s  test R2={te_m['r2']:.3f}  "
              f"WPUQ R2={wp_m['r2']:.3f}  real={real[name]:6.1f} kW  best={pstr}",
              flush=True)

    # 6) XGBoost via the project's hyperopt tuner (fill NaNs with train median)
    t0 = time.time()
    med = Xtr.median()
    xgb_model, xgb_meta = hc.tune_xgb_cv(Xtr.fillna(med), ytr, max_evals=60,
                                         n_splits=5, verbose=False)
    te_m = hc.compute_metrics(y.loc[te].to_numpy(),
                              hc.clip_non_negative(xgb_model.predict(X.loc[te].fillna(med))))
    wp_m = hc.compute_metrics(yw.to_numpy(),
                              hc.clip_non_negative(xgb_model.predict(Xw.fillna(med))))
    real["XGBoost"] = float(hc.clip_non_negative(xgb_model.predict(Xr.fillna(med)))[0])
    rows.append(("XGBoost", te_m, wp_m))
    xgb_p = {k: (round(v, 4) if isinstance(v, float) else v)
             for k, v in xgb_meta.items()}
    print(f"[{'XGBoost':10s}] {time.time()-t0:5.1f}s  test R2={te_m['r2']:.3f}  "
          f"WPUQ R2={wp_m['r2']:.3f}  real={real['XGBoost']:6.1f} kW  best={xgb_p}",
          flush=True)

    # FFNN via TensorFlow/Keras (also predicts the real feeder, seed-averaged)
    t0 = time.time()
    te_m, wp_m, ff_cfg, ff_real = tune_keras_ffnn(
        Xtr, ytr, X.loc[te], y.loc[te], Xw, yw, Xextra=Xr)
    real["FFNN"] = float(ff_real[0])
    rows.append(("FFNN", te_m, wp_m))
    print(f"[{'FFNN':10s}] {time.time()-t0:5.1f}s  test R2={te_m['r2']:.3f}  "
          f"WPUQ R2={wp_m['r2']:.3f}  real={real['FFNN']:6.1f} kW  best={ff_cfg}",
          flush=True)

    # non-model baselines for the real feeder
    base_med = float(ytr.median())
    base_den = float((ytr / X.loc[tr, "Feature Scale_size"]).median()) * size_real

    # --- summary table, sorted by held-out test R2 -------------------------
    rows.sort(key=lambda r: r[1]["r2"], reverse=True)
    print("\n" + "=" * 78)
    print("HP capacity estimation -- model benchmark (target: robust HP peak, kW)")
    print("=" * 78)
    hdr = f"{'model':11s} | {'TEST (unseen HH)':^30s} | {'WPUQ transfer':^24s}"
    print(hdr); print("-" * len(hdr))
    print(f"{'':11s} | {'R2':>6s} {'RMSE':>7s} {'MAE':>6s} {'MAPE':>6s} | "
          f"{'R2':>6s} {'RMSE':>7s} {'MAPE':>6s}")
    for name, t, w in rows:
        print(f"{name:11s} | {t['r2']:6.3f} {t['rmse']:7.1f} {t['mae']:6.1f} "
              f"{t['mape']:5.0f}% | {w['r2']:6.3f} {w['rmse']:7.1f} {w['mape']:5.0f}%")

    out = pd.DataFrame([{"model": n, **{f"test_{k}": v for k, v in t.items()},
                         **{f"wpuq_{k}": v for k, v in w.items()}}
                        for n, t, w in rows])
    out.to_csv("data/capacity_model_benchmark.csv", index=False)
    print("\nSaved -> data/capacity_model_benchmark.csv")

    # --- REAL WPUQ feeder: Swiss-trained models applied to the true aggregate
    print("\n" + "=" * 60)
    print(f"REAL WPUQ feeder -- deploy Swiss-trained models (TRUE {yr:.1f} kW)")
    print("=" * 60)
    print(f"{'method':16s} {'pred kW':>9s} {'err kW':>8s} {'abs %err':>9s}")
    print("-" * 46)
    real_rows = ([(n, real[n]) for n, _, _ in rows]
                 + [("baseline:median", base_med),
                    ("baseline:density", base_den)])
    real_rows.sort(key=lambda r: abs(r[1] - yr))
    for name, pred in real_rows:
        err = pred - yr
        print(f"{name:16s} {pred:9.1f} {err:8.1f} {abs(err)/yr*100:8.0f}%")
    rf = pd.DataFrame([{"method": n, "pred_kW": p, "true_kW": yr,
                        "err_kW": p - yr, "abs_pct_err": abs(p - yr) / yr * 100}
                       for n, p in real_rows])
    rf.to_csv("data/capacity_wpuq_real_feeder.csv", index=False)
    print("\nSaved -> data/capacity_wpuq_real_feeder.csv")


if __name__ == "__main__":
    main()
