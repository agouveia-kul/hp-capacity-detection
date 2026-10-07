"""Model training utilities (Task 6; fixes F13, supports F1).

`tune_grouped_cv` scores every hyperopt candidate by leave-one-fold-out CV over household-disjoint inner
folds (`groups` = inner fold id of each inner substation). Iterative models (XGBoost trees, FFNN epochs)
early-stop on the NEXT training fold, which is household-disjoint from both the fit folds and the scored
fold -- never on the scored fold (legacy `tune_xgb_cv` stopped on the fold it scored, F13). The final model
is refit on all train substations at the best parameters and the median early-stopped iteration count.
Hyperopt is seeded through `rstate`; every model takes the same seed.

03a: registry Linear, Ridge, Lasso, ElasticNet, SVR, PLS, XGBoost (+ FFNN, off by default) and the alias
`XGBoost_mono` (= XGBoost with `monotone_sh`: a +1 monotone constraint on every nf_*_s_h and nf_*_cold_resp column,
0 elsewhere). Every model is a pipeline median imputer -> standard scaler -> estimator, and the imputer and scaler
are fitted on the rows passed to `fit` only (inside each CV fold). Options (`opts`):
  target_transform: none | log. `log` fits log(y) and predicts exp(.) WITHOUT a smearing correction, so it
      predicts roughly the conditional median, not the mean;
  clip: predictions clipped at 0 (default True; residual models predict z = log ratios and set False).
The CV loss is the MSE of the model's output: kW for direct models (also under `log`), z for residual models.
`RESIDUAL_SPACES` (Task 4) let the regularisation reach an all-zero model and keep XGBoost shallow.
"""
import os
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from hyperopt import STATUS_OK, Trials, fmin, hp, space_eval, tpe
from sklearn.cross_decomposition import PLSRegression
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.impute import SimpleImputer
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from hp_capacity import select_scale_free_columns
from paperb.models_rawseries import CNN_SPACE, RAW_PREFIX

ANCHOR_COLS = {"none": [], "size": ["size"], "size_peak": ["size", "peak"]}
MAX_EPOCHS, PATIENCE, XGB_ES_ROUNDS = 500, 40, 25
SETTINGS = {"xgb_n_jobs": -1, "patience": PATIENCE, "device": "cpu"}   # per-process; set by configure() (02b runner)


def configure(xgb_n_jobs=-1, patience=PATIENCE, device="cpu"):
    """XGBoost thread cap per worker, FFNN early-stopping patience (protocol default 40) and the torch device of the CNN and
    TabPFN ("cpu" or "cuda"; 05b: one device per family for a whole stage, recorded in each job's .done marker)."""
    SETTINGS.update(xgb_n_jobs=int(xgb_n_jobs), patience=int(patience), device=str(device))

SPACES = {                                                  # legacy search ranges (benchmark_capacity_models.py)
    "XGBoost": {"eta": hp.uniform("eta", 0.01, 0.3), "max_depth": hp.quniform("max_depth", 3, 10, 1),
                "gamma": hp.uniform("gamma", 0, 10), "subsample": hp.uniform("subsample", 0.5, 1.0),
                "reg_alpha": hp.uniform("reg_alpha", 0, 1), "reg_lambda": hp.uniform("reg_lambda", 0, 10),
                "colsample_bytree": hp.uniform("colsample_bytree", 0.3, 1.0),
                "min_child_weight": hp.quniform("min_child_weight", 1, 20, 1),
                "n_estimators": hp.quniform("n_estimators", 50, 500, 10)},
    "Ridge": {"alpha": hp.loguniform("alpha", np.log(1e-3), np.log(1e4))},
    "ElasticNet": {"alpha": hp.loguniform("alpha", np.log(1e-3), np.log(1e2)), "l1_ratio": hp.uniform("l1_ratio", 0.1, 0.9)},
    "SVR": {"C": hp.loguniform("C", 0, np.log(1e3)), "gamma": hp.loguniform("gamma", np.log(1e-4), np.log(1e-1)),
            "epsilon": hp.choice("epsilon", [0.01, 0.05, 0.1, 0.2])},
    "PLS": {"n_components": hp.quniform("n_components", 1, 20, 1)},
    "Lasso": {"alpha": hp.loguniform("alpha", np.log(1e-4), np.log(1e2))},
    "FFNN": {"arch": hp.choice("arch", [(64,), (128,), (128, 64), (256, 128)]), "lr": hp.choice("lr", [1e-3, 5e-4]),
             "l2": hp.choice("l2", [0.0, 1e-4])},
    "Linear": {},
    # 05b (Task 1e)
    "KernelRidge": {"alpha": hp.loguniform("alpha", np.log(1e-3), np.log(1e2)), "gamma": hp.loguniform("gamma", np.log(1e-4), np.log(1.0)),
                    "kernel": hp.choice("kernel", ["rbf", "laplacian"])},
    "GP": {},                                                # marginal-likelihood fit (ARD RBF + white noise), no hyperopt
    "RandomForest": {"n_estimators": hp.quniform("n_estimators", 100, 500, 50), "max_features": hp.uniform("max_features", 0.2, 1.0),
                     "min_samples_leaf": hp.quniform("min_samples_leaf", 1, 20, 1), "max_depth": hp.choice("max_depth", [None, 4, 6, 8, 12, 16])},
    "CatBoost": {"depth": hp.quniform("depth", 3, 8, 1), "learning_rate": hp.loguniform("learning_rate", np.log(0.01), np.log(0.3)),
                 "l2_leaf_reg": hp.loguniform("l2_leaf_reg", np.log(1.0), np.log(30.0)), "iterations": hp.quniform("iterations", 100, 1000, 50)},
    "TabPFN": {},                                            # in-context learning, no hyperopt
    "CNN": CNN_SPACE,
}
SPACES["ExtraTrees"] = SPACES["RandomForest"]
SPACES["XGBoost_mono"] = SPACES["XGBoost"]
ITERATIVE = ("XGBoost", "XGBoost_mono", "FFNN", "CatBoost", "CNN")       # early stopping on the next training fold
STD_Y = ("SVR", "FFNN", "KernelRidge", "GP", "CNN")                       # fitted on standardised y
TABPFN_CHECKPOINT = "tabpfn-v3.5-20260909.safetensors"
RESIDUAL_SPACES = {                                          # z = log(y / P_hat_A) has sd ~ 0.3: all-zero reachable
    "Ridge": {"alpha": hp.loguniform("alpha", np.log(1e-2), np.log(1e6))},
    "Lasso": {"alpha": hp.loguniform("alpha", np.log(1e-4), np.log(10.0))},
    "ElasticNet": {"alpha": hp.loguniform("alpha", np.log(1e-4), np.log(10.0)), "l1_ratio": hp.uniform("l1_ratio", 0.1, 0.9)},
    "XGBoost": {"eta": hp.uniform("eta", 0.01, 0.1), "max_depth": hp.quniform("max_depth", 1, 3, 1),
                "gamma": hp.uniform("gamma", 0, 1), "subsample": hp.uniform("subsample", 0.5, 0.9),
                "reg_alpha": hp.loguniform("reg_alpha", np.log(1e-2), np.log(10.0)),
                "reg_lambda": hp.loguniform("reg_lambda", np.log(1.0), np.log(100.0)),
                "colsample_bytree": hp.uniform("colsample_bytree", 0.3, 0.8),
                "min_child_weight": hp.quniform("min_child_weight", 5, 40, 1),
                "n_estimators": hp.quniform("n_estimators", 20, 300, 10)},
}
MONOTONE = re.compile(r"nf_(all|wd|we)_(s_h|cold_resp)")


def feature_matrix(features, tab, anchor, feature_set="whdd"):
    """Columns of `feature_set` plus the anchor columns of `anchor` in {none, size, size_peak}. whdd: scale-free
    windowed-HDD features (unchanged); netfit: the nf_* columns (features_netfit); both: the union; raw (05b): the daily
    series rs_* of the raw-series CNN (substations.raw_daily)."""
    whdd = select_scale_free_columns(features[[c for c in features.columns if not c.startswith(("nf_", RAW_PREFIX))]])
    nf = [c for c in features.columns if c.startswith("nf_")]
    raw = [c for c in features.columns if c.startswith(RAW_PREFIX)]
    X = features[{"whdd": whdd, "netfit": nf, "both": whdd + nf, "raw": raw}[feature_set]].copy()
    for c in ANCHOR_COLS[anchor]:
        X[f"Feature Scale_{c}"] = tab.loc[X.index, c].astype(float)
    return X.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)


def tabpfn_checkpoint():
    """Path of the local TabPFN-3.5 regressor checkpoint; raises (the queue then lists the job as failed) when it is missing."""
    d = os.environ.get("TABPFN_MODEL_CACHE_DIR")
    if not d or not (Path(d) / TABPFN_CHECKPOINT).is_file():
        raise RuntimeError(f"TabPFN checkpoint {TABPFN_CHECKPOINT} not found: TABPFN_MODEL_CACHE_DIR={d!r}. Ask Alex; no download is attempted.")
    return Path(d) / TABPFN_CHECKPOINT


def tabpfn_info():
    """Checkpoint file name, SHA-256 and package version, for config.yaml."""
    import hashlib
    from importlib.metadata import version
    h, f = hashlib.sha256(), tabpfn_checkpoint()
    with open(f, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 24), b""):
            h.update(b)
    return {"checkpoint": f.name, "sha256": h.hexdigest(), "package": version("tabpfn")}


def tabpfn_regressor(seed, n_estimators=None):
    """TabPFN-3.5 regressor from the local checkpoint, offline (no download, no hub call), seeded, on SETTINGS["device"]. The CPU
    guard of tabpfn (> 1000 rows) is a speed warning, not a pre-training limit, and is lifted by TABPFN_ALLOW_CPU_LARGE_DATASET."""
    os.environ.update(HF_HUB_OFFLINE="1", TABPFN_ALLOW_CPU_LARGE_DATASET="1")
    from tabpfn import TabPFNRegressor
    return TabPFNRegressor(model_path=str(tabpfn_checkpoint()), device=SETTINGS["device"], random_state=int(seed),
                           n_estimators="auto" if n_estimators is None else int(n_estimators), n_preprocessing_jobs=1)


class Model:
    """One API for every model: fit(X, y, n_iter=None, X_es=None, y_es=None) -> best iteration or None."""

    def __init__(self, name, params, seed, opts=None):
        self.opts = {"target_transform": "none", "clip": True, "monotone_sh": name == "XGBoost_mono", **(opts or {})}
        self.name, self.params, self.seed = "XGBoost" if name == "XGBoost_mono" else name, dict(params), seed

    def _prep(self, X, y):
        y = np.asarray(y, float)
        if self.opts["target_transform"] == "log":
            if (y <= 0).any():
                raise ValueError("log target transform needs y > 0")
            y = np.log(y)
        self.cols = list(pd.DataFrame(X).columns)
        self.ym, self.ysd = 0.0, 1.0
        if self.name in STD_Y:                                   # standardised y (SVR, FFNN as before; 05b kernel models, CNN)
            self.ym, self.ysd = float(np.mean(y)), float(np.std(y)) or 1.0
        if self.name == "CNN":                                   # imputes and scales its own channels on the rows it is fitted on
            return pd.DataFrame(X), (np.asarray(y, float) - self.ym) / self.ysd
        self.imp = SimpleImputer(strategy="median", keep_empty_features=True).fit(X)
        self.xs = StandardScaler().fit(self.imp.transform(X))
        return self._x(X), (np.asarray(y, float) - self.ym) / self.ysd

    def _x(self, X):
        return pd.DataFrame(X) if self.name == "CNN" else self.xs.transform(self.imp.transform(X))

    def fit(self, X, y, n_iter=None, X_es=None, y_es=None):
        Xs, ys = self._prep(X, y)
        if y_es is not None and self.opts["target_transform"] == "log":
            y_es = np.log(np.asarray(y_es, float))
        es = None if X_es is None else (self._x(X_es), (np.asarray(y_es, float) - self.ym) / self.ysd)
        p, n = self.params, self.name
        if np.ptp(ys) == 0 and n in ("CatBoost", "TabPFN", "GP", "CNN"):   # constant target (e.g. z = 0): these refuse it or need not learn it
            self.m = DummyRegressor(strategy="constant", constant=float(ys[0])).fit(np.zeros((len(ys), 1)), ys)
            return None
        if n == "XGBoost":
            import xgboost as xgb
            kw = dict(learning_rate=p["eta"], max_depth=int(p["max_depth"]), gamma=p["gamma"], subsample=p["subsample"],
                      reg_alpha=p["reg_alpha"], reg_lambda=p["reg_lambda"], colsample_bytree=p["colsample_bytree"],
                      min_child_weight=int(p["min_child_weight"]), tree_method="hist", random_state=self.seed, n_jobs=SETTINGS["xgb_n_jobs"])
            if self.opts["monotone_sh"] and any(self.monotone_constraints()):   # all-zero = unconstrained (and faster)
                kw["monotone_constraints"] = self.monotone_constraints()
            if n_iter is None and es is not None:
                self.m = xgb.XGBRegressor(n_estimators=int(p["n_estimators"]), early_stopping_rounds=XGB_ES_ROUNDS, **kw)
                self.m.fit(Xs, ys, eval_set=[es], verbose=False)
                return int(self.m.best_iteration) + 1
            self.m = xgb.XGBRegressor(n_estimators=int(n_iter or p["n_estimators"]), **kw).fit(Xs, ys)
            return None
        if n == "FFNN":
            self.m = MLPRegressor(hidden_layer_sizes=p["arch"], alpha=p["l2"], learning_rate_init=p["lr"],
                                  batch_size=32, random_state=self.seed)
            best, best_ep, epochs = np.inf, 1, n_iter or MAX_EPOCHS
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for ep in range(1, epochs + 1):
                    self.m.partial_fit(Xs, ys)
                    if n_iter is None and es is not None:
                        loss = float(np.mean((self.m.predict(es[0]) - es[1]) ** 2))
                        if loss < best - 1e-9:
                            best, best_ep = loss, ep
                        elif ep - best_ep >= SETTINGS["patience"]:
                            break
            if n_iter is None and es is not None:     # restore = refit to the best epoch (deterministic)
                self.fit(X, y, n_iter=best_ep)
                return best_ep
            return None
        if n == "CatBoost":
            from catboost import CatBoostRegressor
            self.m = CatBoostRegressor(iterations=int(n_iter or p["iterations"]), depth=int(p["depth"]), learning_rate=p["learning_rate"],
                                       l2_leaf_reg=p["l2_leaf_reg"], random_seed=self.seed, thread_count=SETTINGS["xgb_n_jobs"],
                                       verbose=False, allow_writing_files=False)
            if n_iter is None and es is not None:
                self.m.fit(Xs, ys, eval_set=es, early_stopping_rounds=XGB_ES_ROUNDS, use_best_model=True)
                return int(self.m.get_best_iteration()) + 1
            self.m.fit(Xs, ys)
            return None
        if n == "CNN":
            from paperb.models_rawseries import RawSeriesCNN
            self.m = RawSeriesCNN(p, self.seed, SETTINGS["xgb_n_jobs"], SETTINGS["device"])
            return self.m.fit(Xs, ys, n_iter, es)
        if n == "TabPFN":
            import torch
            torch.set_num_threads(max(1, SETTINGS["xgb_n_jobs"]))     # the queue sets OMP_NUM_THREADS = 1 (BLAS determinism)
            self.m = tabpfn_regressor(self.seed, p.get("n_estimators")).fit(Xs, ys)
            return None
        est = {"Ridge": lambda: Ridge(alpha=p["alpha"]),
               "ElasticNet": lambda: ElasticNet(alpha=p["alpha"], l1_ratio=p["l1_ratio"], max_iter=20000),
               "Lasso": lambda: Lasso(alpha=p["alpha"], max_iter=20000),
               "SVR": lambda: SVR(kernel="rbf", C=p["C"], gamma=p["gamma"], epsilon=p["epsilon"]),
               "PLS": lambda: PLSRegression(n_components=int(min(p["n_components"], Xs.shape[1], len(ys) - 1))),
               "Linear": LinearRegression,
               "KernelRidge": lambda: KernelRidge(alpha=p["alpha"], kernel=p["kernel"], gamma=p["gamma"]),
               "GP": lambda: GaussianProcessRegressor(
                   ConstantKernel(1.0, (1e-3, 1e3)) * RBF(np.ones(Xs.shape[1]), (1e-2, 1e3)) + WhiteKernel(0.1, (1e-5, 1e1)),
                   n_restarts_optimizer=3, random_state=self.seed),
               "RandomForest": lambda: RandomForestRegressor(**self._forest(p)),
               "ExtraTrees": lambda: ExtraTreesRegressor(**self._forest(p))}[n]()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.m = est.fit(Xs, ys)
        if n in ("RandomForest", "ExtraTrees"):
            self.m.n_jobs = 1                                      # threaded tree averaging is order-dependent (1e-14): predict serially
        return None

    def _forest(self, p):
        return dict(n_estimators=int(p["n_estimators"]), max_features=float(p["max_features"]), min_samples_leaf=int(p["min_samples_leaf"]),
                    max_depth=None if p["max_depth"] is None else int(p["max_depth"]), random_state=self.seed, n_jobs=SETTINGS["xgb_n_jobs"])

    def predict_interval(self, X, z=1.645):
        """GP only: (lo, hi) of the central 90 % predictive interval (mean +- z sd, white noise included) on the output scale."""
        mu, sd = self.m.predict(self._x(X), return_std=True)
        lo, hi = ((mu + s * z * sd) * self.ysd + self.ym for s in (-1, 1))
        return (np.exp(lo), np.exp(hi)) if self.opts["target_transform"] == "log" else (lo, hi)

    def monotone_constraints(self):
        """+1 on the nf_{all,wd,we}_s_h / _cold_resp columns, 0 elsewhere (the scaler keeps each column's order)."""
        return tuple(int(bool(MONOTONE.fullmatch(str(c)))) for c in self.cols)

    def predict(self, X):
        out = np.ravel(self.m.predict(self._x(X))) * self.ysd + self.ym
        out = np.exp(out) if self.opts["target_transform"] == "log" else out
        return np.maximum(out, 0.0) if self.opts["clip"] else out


def tune_grouped_cv(model_name, X, y, groups, seed, max_evals=50, X_final=None, y_final=None, opts=None, space=None,
                    eval_on=None, fixed=None):
    """Seeded hyperopt over household-grouped CV; returns (final model, meta dict, Trials).

    X, y, groups: inner substations and their fold ids. The final model is refit on (X_final, y_final)
    -- all train substations -- or on (X, y) when those are not given. `opts` go to Model; `space` replaces
    SPACES[model_name] (e.g. RESIDUAL_SPACES). `eval_on = (y_kw, p_hat)` (arrays aligned with X; 03b) scores the
    out-of-fold predictions as WAPE on the kW scale: y_hat = prediction (p_hat None, direct models) or
    p_hat * exp(prediction) (residual models); meta['cv_wape'] (%, pooled over the folds) is the model-selection
    statistic of the learning curve -- inner CV only, never test. 05b A10: `fixed = (params, best_iter)` skips the search and the
    inner CV and only refits the final model with those (logged) values (meta cv_* None, n_evals 0).
    """
    if fixed is not None:
        params, best_iter = dict(fixed[0]), fixed[1]
        final = Model(model_name, params, seed, opts)
        final.fit(pd.DataFrame(X if X_final is None else X_final), y if y_final is None else y_final, n_iter=best_iter)
        return final, {"params": params, "cv_mse": None, "cv_wape": None, "best_iter": best_iter, "n_evals": 0}, None
    X, y, groups = pd.DataFrame(X), np.asarray(y, float), np.asarray(groups)
    folds = sorted(set(groups))
    iterative = model_name in ITERATIVE

    def objective(params):
        losses, iters, abserr = [], [], 0.0
        for i, f in enumerate(folds):
            va = groups == f
            es = groups == folds[(i + 1) % len(folds)] if iterative else np.zeros(len(y), bool)
            tr = ~va & ~es
            m = Model(model_name, params, seed, opts)
            iters.append(m.fit(X[tr], y[tr], X_es=X[es] if iterative else None, y_es=y[es] if iterative else None))
            pred = m.predict(X[va])
            losses.append(float(np.mean((pred - y[va]) ** 2)))
            if eval_on is not None:
                y_kw, p_hat = eval_on
                abserr += float(np.abs((pred if p_hat is None else p_hat[va] * np.exp(pred)) - y_kw[va]).sum())
        wape = 100 * abserr / float(np.sum(eval_on[0])) if eval_on is not None else None
        return {"loss": float(np.mean(losses)), "status": STATUS_OK, "fold_losses": losses, "cv_wape": wape,
                "best_iter": int(np.median(iters)) if iterative else None}

    trials = Trials()
    space = SPACES[model_name] if space is None else space
    if space:
        best = fmin(objective, space, algo=tpe.suggest, max_evals=max_evals, trials=trials,
                    rstate=np.random.default_rng(seed), show_progressbar=False)
        params, res = space_eval(space, best), trials.best_trial["result"]
    else:
        params, res = {}, objective({})
    final = Model(model_name, params, seed, opts)
    final.fit(X if X_final is None else pd.DataFrame(X_final), y if y_final is None else y_final, n_iter=res["best_iter"])
    return final, {"params": params, "cv_mse": res["loss"], "cv_wape": res["cv_wape"], "best_iter": res["best_iter"], "n_evals": len(trials.trials)}, trials
