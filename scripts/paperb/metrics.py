"""Metrics of the protocol-v1 runner: nMAE first (primary from 07, decision 2026-11-16), then WAPE, then
hp_capacity.compute_metrics.

nMAE = mean|y_hat - y| / max(y) * 100 (%), per evaluation set; `y_max` (kW) is its normaliser and is reported beside it.
A per-bin cell calls compute_metrics on that bin's subset, so each bin uses its own maximum.
WAPE = sum|y_hat - y| / sum y * 100 (%), as Paper A's `outputs._wape` (primary up to 06, secondary from 07).
On one set nMAE = WAPE * mean(y) / max(y). hp_capacity.compute_metrics itself is left unchanged (its API is shared
with the legacy scripts).
"""
import numpy as np

import hp_capacity

METRIC_ORDER = ["nmae", "y_max", "wape", "mape", "r2", "rmse", "mae"]


def nmae(y_true, y_pred):
    """mean|y_hat - y| / max(y) * 100; NaN when max(y) <= 0 or the set is empty."""
    y, p = np.asarray(y_true, float), np.asarray(y_pred, float)
    if y.size == 0 or not y.max() > 0:
        return np.nan
    return float(np.abs(p - y).mean() / y.max() * 100)


def compute_metrics(y_true, y_pred):
    """{nmae, y_max, wape, rmse, mae, mape, r2}; nMAE is NaN when max(y) <= 0, WAPE when sum(y) <= 0."""
    y, p = np.asarray(y_true, float), np.asarray(y_pred, float)
    return {"nmae": nmae(y, p), "y_max": float(y.max()) if y.size else np.nan,
            "wape": float(np.abs(p - y).sum() / y.sum() * 100) if y.sum() > 0 else np.nan,
            **hp_capacity.compute_metrics(y, p)}
