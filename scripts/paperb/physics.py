"""Physics estimators aligned with Paper A (Task 5, fixes F2).

Paper A (hp-sensitivity-paper @ 56710ef, scripts/outputs.py `_daily_pools` / `_evaluate` / `_metrics_k`,
scripts/utils.py `_sf_arm`; draft hp_sensitivity_overleaf.tex Sec. II) fits the net load as
    P(T) = P_base + s_h * max(0, T_h - T)
to DAILY MEANS of load and temperature over ALL days (no heating-season filter), by least squares with the
threshold T_h latent inside T_BALANCE_BOUNDS = (8, 20) degC (`hp_common.fit_hockey_stick`, which is
byte-identical in both repositories). The legacy Paper-B fit (daily min T < 12 degC, daily max load) put
the hinge above every retained temperature in 92 % of fits (F2); keeping warm days identifies it.

`daily_means`, `fit_daily` and `sf_arm` are the ports; tests/test_protocol_v1.py checks them against
Paper A's own code (tests/fixtures/paperA_fixture.npz, scripts/paperb/make_paperA_fixture.py).
The four baselines map substation-level fit results to a target with a fit(train) / predict(X) API.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from hp_common import HDH_THRESH, T_BALANCE_BOUNDS, daily_hdh_mean_load, fit_hdh_linear, fit_hockey_stick


def daily_means(T, load):
    """Paper A reduction: calendar-day means of 15-min temperature and load, days with finite values."""
    d = pd.DataFrame({"T": T, "y": load}).resample("D").mean()
    d = d[np.isfinite(d["T"]) & np.isfinite(d["y"])]
    return d["T"].to_numpy(), d["y"].to_numpy()


def fit_daily(T, y, bounds=T_BALANCE_BOUNDS, tol=1e-3):
    """Paper A net-load fit on daily arrays -> dict (P_base, s_h, T_h, r2, hinge diagnostics)."""
    base, s_h, t_h, r2 = fit_hockey_stick(T, y, bounds)
    return {"P_base": float(base), "s_h": float(s_h), "T_h": float(t_h), "r2": float(r2),
            "T_min": float(np.min(T)), "T_max": float(np.max(T)),
            "hinge_inside": bool(np.min(T) < t_h < np.max(T)),
            "at_bound": bool(t_h <= bounds[0] + tol or t_h >= bounds[1] - tol)}


def sf_arm(T, sf, thr, side, tmin=None):
    """Verbatim port of Paper A `utils._sf_arm`: OLS SF arm anchored at `thr` -> (b, m, SF_extreme, r2)."""
    if not np.isfinite(thr):
        return (np.nan,) * 4
    m = (T < thr) if side == 'h' else (T > thr)
    if side == 'h' and tmin is not None:
        m = m & (T >= tmin)
    if m.sum() < 10:
        return (np.nan,) * 4
    x = (thr - T[m]) if side == 'h' else (T[m] - thr)
    y = sf[m]
    if np.nanstd(y) == 0:
        return (np.nan,) * 4
    mm, bb = np.polyfit(x, y, 1)
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1 - np.sum((y - (bb + mm * x)) ** 2) / ss if ss > 0 else np.nan
    if side == 'h':
        lo = max(T.min(), tmin) if tmin is not None else T.min()
        ext = thr - lo
    else:
        ext = T.max() - thr
    return float(bb), float(mm), float(np.clip(bb + mm * ext, 0, 1)), float(r2)


def net_features(T, net):
    """Physics features of one substation's net load (inputs of the four baselines); NaN on a failed fit."""
    out = dict.fromkeys(["s_h_net", "P_base_net", "T_h_net", "r2_net", "T_min_net", "delta_net",
                         "hinge_inside_net", "at_bound_net", "hdh_slope_net"], np.nan)
    try:
        f = fit_daily(*daily_means(T, net))
        out.update(s_h_net=f["s_h"], P_base_net=f["P_base"], T_h_net=f["T_h"], r2_net=f["r2"], T_min_net=f["T_min"],
                   delta_net=f["s_h"] * max(0.0, f["T_h"] - f["T_min"]),  # coldest-day coincident HP load proxy
                   hinge_inside_net=f["hinge_inside"], at_bound_net=f["at_bound"])
        out["hdh_slope_net"] = fit_hdh_linear(*daily_hdh_mean_load(T, net, HDH_THRESH))[1]
    except (RuntimeError, ValueError):
        pass
    return out


class LinearMap:
    """OLS map from physics features to a target; predictions clipped at 0, NaN where a feature is NaN."""

    def __init__(self, cols, intercept=True):
        self.cols, self.intercept = list(cols), intercept

    def fit(self, X, y):
        ok = X[self.cols].notna().all(axis=1).to_numpy() & np.isfinite(np.asarray(y, float))
        self.n_fit_dropped = int((~ok).sum())
        self.m = LinearRegression(fit_intercept=self.intercept).fit(X.loc[ok, self.cols], np.asarray(y, float)[ok])
        return self

    def predict(self, X):
        ok = X[self.cols].notna().all(axis=1).to_numpy()
        p = np.full(len(X), np.nan)
        if ok.any():
            p[ok] = np.maximum(self.m.predict(X.loc[ok, self.cols]), 0.0)
        return p


def make_baseline(name):
    return {"slope_only": lambda: LinearMap(["s_h_net"]),                         # legacy "fitted slope-only"
            "slope_base": lambda: LinearMap(["s_h_net", "P_base_net"]),
            "calibrated_delta": lambda: LinearMap(["delta_net"], intercept=False),  # legacy "delta calib (origin)"
            "hdh": lambda: LinearMap(["hdh_slope_net"])}[name]()
