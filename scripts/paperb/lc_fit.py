"""Learning-curve fit and family winners (iteration 05b, Task 1a; selection rule of the pre-registered decision rule).

Per seed, WAPE(n) = a + b n^(-c) is fitted by least squares to the median over draws at each n (distinct train HP households),
with c in (0, 2] (C_BOUNDS) and a, b free; several starting values of c are tried and the lowest SSE is kept. a is the asymptote;
n* = (b / (W_phys - a))^(1/c) is the n at which the fitted curve reaches the physics WAPE W_phys (inf if it never does, i.e.
a >= W_phys or b <= 0; 0 if the curve is below W_phys everywhere). A fit is flagged when c sits at a bound or a < 0. Summaries are
median [5 %, 90 %] over seeds (`summarise`).

Family winners: `family_winners` picks, per group (seed, draw, n, family), the configuration with the lowest inner-CV WAPE
(`wape_inner`), ties broken by the configuration label. Test columns are never read for the choice.
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

C_BOUNDS = (1e-3, 2.0)
FAMILY_OF = {**dict.fromkeys(["Linear", "Ridge", "Lasso", "ElasticNet", "PLS"], "linear"),
             **dict.fromkeys(["SVR", "KernelRidge", "GP"], "kernel"),
             **dict.fromkeys(["XGBoost", "RandomForest", "ExtraTrees", "CatBoost"], "trees"),
             **dict.fromkeys(["FFNN", "TabPFN"], "neural"), "CNN": "rawseries"}
CONFIG_COLS = ["method", "anchor", "feature_set", "mode", "target_transform"]


def power_law(n, a, b, c):
    return a + b * np.power(n, -c)


def fit_curve(n, w):
    """Fit a + b n^-c to points (n, w) -> dict(a, b, c, sse, flag_c_bound, flag_a_neg)."""
    n, w = np.asarray(n, float), np.asarray(w, float)
    best = None
    for c0 in (0.25, 0.5, 1.0, 1.5):
        p0 = [w.min(), (w.max() - w.min() + 1e-6) * n.min() ** c0, c0]
        try:
            p, _ = curve_fit(power_law, n, w, p0=p0, bounds=([-np.inf, -np.inf, C_BOUNDS[0]], [np.inf, np.inf, C_BOUNDS[1]]), maxfev=20000)
        except (RuntimeError, ValueError):
            continue
        sse = float(np.sum((power_law(n, *p) - w) ** 2))
        if best is None or sse < best[1]:
            best = (p, sse)
    if best is None:
        return {"a": np.nan, "b": np.nan, "c": np.nan, "sse": np.nan, "flag_c_bound": True, "flag_a_neg": False}
    (a, b, c), sse = best
    return {"a": a, "b": b, "c": c, "sse": sse, "flag_c_bound": bool(c <= C_BOUNDS[0] * 1.01 or c >= C_BOUNDS[1] * 0.999),
            "flag_a_neg": bool(a < 0)}


def n_star(a, b, c, w_phys):
    """n at which a + b n^-c = w_phys (see module doc)."""
    if not np.all(np.isfinite([a, b, c, w_phys])):
        return np.nan
    if a >= w_phys or b <= 0:
        return np.inf if a >= w_phys else 0.0
    return float((b / (w_phys - a)) ** (1.0 / c))


def seed_fits(lc, w_phys):
    """lc: rows (split_seed, n_train_hp, lc_draw, wape) of one family winner; w_phys: {seed: best physics WAPE at n = all}.
    -> one row per seed with a, b, c, flags, n*, asymptote below physics."""
    rows = []
    for seed, g in lc.groupby("split_seed"):
        m = g.groupby("n_train_hp")["wape"].median()
        f = fit_curve(m.index.to_numpy(), m.to_numpy())
        wp = w_phys.get(seed, np.nan)
        rows.append({"split_seed": seed, **f, "n_points": len(m), "w_phys": wp, "n_star": n_star(f["a"], f["b"], f["c"], wp),
                     "a_below_phys": bool(f["a"] < wp)})
    return pd.DataFrame(rows)


def summarise(v, q=(0.05, 0.90)):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    return {"median": float(np.median(v)) if len(v) else np.nan, "q05": float(np.quantile(v, q[0])) if len(v) else np.nan,
            "q90": float(np.quantile(v, q[1])) if len(v) else np.nan, "n": int(len(v))}


def family_winners(cand, group_cols):
    """cand: one row per configuration with CONFIG_COLS, `wape_inner` and any test columns; returns the inner-CV winner of
    every group (group_cols + 'family'). Test columns are carried along, never used."""
    c = cand.assign(family=cand["method"].map(FAMILY_OF), _label=cand[CONFIG_COLS].astype(str).agg("|".join, axis=1))
    c = c[c["family"].notna() & np.isfinite(c["wape_inner"].astype(float))]
    c = c.sort_values([*group_cols, "family", "wape_inner", "_label"], kind="mergesort")
    return c.groupby([*group_cols, "family"], sort=True).head(1).drop(columns="_label").reset_index(drop=True)
