"""Model training utilities (Task 6; fixes F13, supports F1).

`tune_grouped_cv` scores every hyperopt candidate by leave-one-fold-out CV over household-disjoint inner
folds (`groups` = inner fold id of each inner substation). Iterative models (XGBoost trees, FFNN epochs)
early-stop on the NEXT training fold, which is household-disjoint from both the fit folds and the scored
fold -- never on the scored fold (legacy `tune_xgb_cv` stopped on the fold it scored, F13). The final model
is refit on all train substations at the best parameters and the median early-stopped iteration count.
Hyperopt is seeded through `rstate`; every model takes the same seed.
"""
import warnings

import numpy as np
import pandas as pd
from hyperopt import STATUS_OK, Trials, fmin, hp, space_eval, tpe
from sklearn.cross_decomposition import PLSRegression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from hp_capacity import select_scale_free_columns

ANCHOR_COLS = {"none": [], "size": ["size"], "size_peak": ["size", "peak"]}
MAX_EPOCHS, PATIENCE, XGB_ES_ROUNDS = 500, 40, 25
SETTINGS = {"xgb_n_jobs": -1, "patience": PATIENCE}          # per-process; set by configure() (02b runner)


def configure(xgb_n_jobs=-1, patience=PATIENCE):
    """XGBoost thread cap per worker and FFNN early-stopping patience (protocol default 40)."""
    SETTINGS.update(xgb_n_jobs=int(xgb_n_jobs), patience=int(patience))

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
    "FFNN": {"arch": hp.choice("arch", [(64,), (128,), (128, 64), (256, 128)]), "lr": hp.choice("lr", [1e-3, 5e-4]),
             "l2": hp.choice("l2", [0.0, 1e-4])},
    "Linear": {},
}


def feature_matrix(features, tab, anchor):
    """Scale-free windowed-HDD features plus the anchor columns of `anchor` in {none, size, size_peak}."""
    X = features[select_scale_free_columns(features)].copy()
    for c in ANCHOR_COLS[anchor]:
        X[f"Feature Scale_{c}"] = tab.loc[X.index, c].astype(float)
    return X.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)


class Model:
    """One API for every model: fit(X, y, n_iter=None, X_es=None, y_es=None) -> best iteration or None."""

    def __init__(self, name, params, seed):
        self.name, self.params, self.seed = name, dict(params), seed

    def _prep(self, X, y):
        self.imp = SimpleImputer(strategy="median", keep_empty_features=True).fit(X)
        self.xs = StandardScaler().fit(self.imp.transform(X))
        self.ym, self.ysd = 0.0, 1.0
        if self.name in ("SVR", "FFNN"):                         # legacy standardised y for these two only
            self.ym, self.ysd = float(np.mean(y)), float(np.std(y)) or 1.0
        return self._x(X), (np.asarray(y, float) - self.ym) / self.ysd

    def _x(self, X):
        return self.xs.transform(self.imp.transform(X))

    def fit(self, X, y, n_iter=None, X_es=None, y_es=None):
        Xs, ys = self._prep(X, y)
        es = None if X_es is None else (self._x(X_es), (np.asarray(y_es, float) - self.ym) / self.ysd)
        p, n = self.params, self.name
        if n == "XGBoost":
            import xgboost as xgb
            kw = dict(learning_rate=p["eta"], max_depth=int(p["max_depth"]), gamma=p["gamma"], subsample=p["subsample"],
                      reg_alpha=p["reg_alpha"], reg_lambda=p["reg_lambda"], colsample_bytree=p["colsample_bytree"],
                      min_child_weight=int(p["min_child_weight"]), tree_method="hist", random_state=self.seed, n_jobs=SETTINGS["xgb_n_jobs"])
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
        est = {"Ridge": lambda: Ridge(alpha=p["alpha"]),
               "ElasticNet": lambda: ElasticNet(alpha=p["alpha"], l1_ratio=p["l1_ratio"], max_iter=20000),
               "SVR": lambda: SVR(kernel="rbf", C=p["C"], gamma=p["gamma"], epsilon=p["epsilon"]),
               "PLS": lambda: PLSRegression(n_components=int(min(p["n_components"], Xs.shape[1], len(ys) - 1))),
               "Linear": LinearRegression}[n]()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.m = est.fit(Xs, ys)
        return None

    def predict(self, X):
        return np.maximum(np.ravel(self.m.predict(self._x(X))) * self.ysd + self.ym, 0.0)


def tune_grouped_cv(model_name, X, y, groups, seed, max_evals=50, X_final=None, y_final=None):
    """Seeded hyperopt over household-grouped CV; returns (final model, meta dict, Trials).

    X, y, groups: inner substations and their fold ids. The final model is refit on (X_final, y_final)
    -- all train substations -- or on (X, y) when those are not given.
    """
    X, y, groups = pd.DataFrame(X), np.asarray(y, float), np.asarray(groups)
    folds = sorted(set(groups))
    iterative = model_name in ("XGBoost", "FFNN")

    def objective(params):
        losses, iters = [], []
        for i, f in enumerate(folds):
            va = groups == f
            es = groups == folds[(i + 1) % len(folds)] if iterative else np.zeros(len(y), bool)
            tr = ~va & ~es
            m = Model(model_name, params, seed)
            iters.append(m.fit(X[tr], y[tr], X_es=X[es] if iterative else None, y_es=y[es] if iterative else None))
            losses.append(float(np.mean((m.predict(X[va]) - y[va]) ** 2)))
        return {"loss": float(np.mean(losses)), "status": STATUS_OK, "fold_losses": losses,
                "best_iter": int(np.median(iters)) if iterative else None}

    trials = Trials()
    space = SPACES[model_name]
    if space:
        best = fmin(objective, space, algo=tpe.suggest, max_evals=max_evals, trials=trials,
                    rstate=np.random.default_rng(seed), show_progressbar=False)
        params, res = space_eval(space, best), trials.best_trial["result"]
    else:
        params, res = {}, objective({})
    final = Model(model_name, params, seed)
    final.fit(X if X_final is None else pd.DataFrame(X_final), y if y_final is None else y_final, n_iter=res["best_iter"])
    return final, {"params": params, "cv_mse": res["loss"], "best_iter": res["best_iter"], "n_evals": len(trials.trials)}, trials
