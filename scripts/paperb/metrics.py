"""Metrics of the protocol-v1 runner (03a): WAPE first (primary metric), then hp_capacity.compute_metrics.

WAPE = sum|y_hat - y| / sum y * 100 (%), as Paper A's `outputs._wape`. hp_capacity.compute_metrics itself is left
unchanged (its API is shared with the legacy scripts).
"""
import numpy as np

import hp_capacity

METRIC_ORDER = ["wape", "mape", "r2", "rmse", "mae"]


def compute_metrics(y_true, y_pred):
    """{wape, rmse, mae, mape, r2}; WAPE is NaN when sum(y) <= 0."""
    y, p = np.asarray(y_true, float), np.asarray(y_pred, float)
    return {"wape": float(np.abs(p - y).sum() / y.sum() * 100) if y.sum() > 0 else np.nan,
            **hp_capacity.compute_metrics(y, p)}
