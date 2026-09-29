"""Uncertainty (Task 7): household-cluster bootstrap within a split, and the summary across split seeds.

Approximation in `cluster_bootstrap`: each replicate draws the test HP households with replacement and
recomputes the metric on the substations whose HP members were ALL drawn (each kept once, unweighted).
Duplicated households are not up-weighted, fill households are not resampled, and a substation with n_hp
members survives with probability ~0.632**n_hp, so large-n_hp substations are under-represented in the
replicates. The mean share of substations kept is returned so the approximation can be judged.
"""
import numpy as np
import pandas as pd


def cluster_bootstrap(metric_fn, df, cluster="hp_household", B=2000, seed=0, members_col="hp_members", ci=0.95):
    """metric_fn(df_subset) -> float. Returns dict(lo, hi, sd, n_valid, mean_kept)."""
    assert cluster == "hp_household", "only HP-household clusters are implemented"
    hh = sorted(set().union(*df[members_col]))
    pos = {h: i for i, h in enumerate(hh)}
    M = np.zeros((len(df), len(hh)), bool)
    for r, mem in enumerate(df[members_col]):
        M[r, [pos[h] for h in mem]] = True
    rng = np.random.default_rng(seed)
    vals, kept = [], []
    for _ in range(B):
        drawn = np.zeros(len(hh), bool)
        drawn[rng.integers(len(hh), size=len(hh))] = True
        keep = ~(M & ~drawn).any(axis=1)
        kept.append(keep.mean())
        vals.append(metric_fn(df[keep]) if keep.sum() >= 2 else np.nan)
    v = np.asarray(vals, float)
    a = (1 - ci) / 2
    return {"lo": float(np.nanquantile(v, a)), "hi": float(np.nanquantile(v, 1 - a)), "sd": float(np.nanstd(v)),
            "n_valid": int(np.isfinite(v).sum()), "mean_kept": float(np.mean(kept))}


def across_split_summary(metrics):
    """Long metrics (metrics.csv format) -> mean, sd and 5-95 % range of `value` over split seeds."""
    keys = [c for c in ("dataset", "target", "method", "anchor", "metric") if c in metrics]
    g = metrics.groupby(keys)["value"]
    return pd.DataFrame({"mean": g.mean(), "sd": g.std(ddof=1), "q05": g.quantile(0.05), "q95": g.quantile(0.95),
                         "n_seeds": metrics.groupby(keys)["split_seed"].nunique()}).reset_index()
