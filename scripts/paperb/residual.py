"""Residual learning on top of Paper A's estimator (iteration 03a, Task 4).

Target z = log(y) - log(P_hat_A), with P_hat_A = `paperA_sh_mh` (s_h / m_h, the seed's full train pilot). A model
predicts z_hat and the prediction is y_hat = P_hat_A * exp(z_hat); z_hat = 0 reproduces P_hat_A exactly (the
zero-residual model, always reported as `paperA_sh_mh`). Residual models are Ridge, Lasso and ElasticNet (their
regularisation can reach the all-zero model) and a shallow, strongly regularised XGBoost (`train.RESIDUAL_SPACES`),
tuned with the same household-grouped inner CV on the z scale. Substations with an invalid P_hat_A
(`physics.paperA_estimate`) are excluded from residual tuning and fitting (counted) and scored with the fallback
rule of Task 1.5 (predict 0, counted as `n_invalid`).
"""
import numpy as np

from paperb.train import RESIDUAL_SPACES

RESIDUAL_MODELS = tuple(RESIDUAL_SPACES)


def log_ratio(y, p_hat, valid):
    """z = log(y) - log(P_hat) where P_hat is valid and y > 0, else NaN."""
    y, p_hat = np.asarray(y, float), np.asarray(p_hat, float)
    ok = np.asarray(valid, bool) & (y > 0)
    z = np.full(len(y), np.nan)
    z[ok] = np.log(y[ok]) - np.log(p_hat[ok])
    return z


def compose(p_hat, z_hat, valid, fallback=0.0):
    """y_hat = P_hat * exp(z_hat) where P_hat is valid, else the fallback rule (0)."""
    valid = np.asarray(valid, bool)
    return np.where(valid, np.asarray(p_hat, float) * np.exp(np.where(valid, z_hat, 0.0)), fallback)


def residual_predict(tuned, name, X, y, p_hat, valid, fit_in, fit_tr, te):
    """Tune on inner, refit on train (valid P_hat only) and predict test.

    `tuned(name, X, yv, mask_in, mask_tr, opts, space) -> test prediction of yv` is the runner's tuner (it logs
    and times the fit). Returns (y_hat on test, counts)."""
    z = log_ratio(y, p_hat, valid)
    ok = np.isfinite(z)
    z_hat = tuned(name, X, z, fit_in & ok, fit_tr & ok, {"clip": False}, RESIDUAL_SPACES[name])
    counts = {"n_resid_excluded_train": int((fit_tr & ~ok).sum()), "n_resid_excluded_inner": int((fit_in & ~ok).sum())}
    return compose(p_hat[te], z_hat, valid[te]), counts
