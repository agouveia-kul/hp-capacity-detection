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

Paper A capacity estimator (iteration 03a): P_hat = s_h / m_h (draft eq. `capacity`). s_h is the substation's
net-load slope (`s_h_net`); m_h is the SF slope of a submetered pilot (`pilot_fit`, a verbatim port of Paper A
`outputs._pilot_fit`, checked against Paper A's committed Kloten pilots in tests/test_fair_test.py). The pilot is
the aggregate of the seed's TRAIN HP households (`paperA_sh_mh`), or of the train HP households of the
substation's own station when it has >= `min_station_pilot` of them (`paperA_sh_mh_station`, else the full pilot,
counted as a fallback). Invalid estimates (s_h <= 0 or NaN, m_h <= 0 or NaN) are predicted as 0 and counted.

Iteration 03b: `household_sensitivity` (per-dwelling non-TCL slope s0 from TRAIN fill households, optionally plus the
train HP households' own load), `paperA_corrected` (P_hat = max(s_h - N s0, 0) / m_h) and `crossfit_pilot_m` (m_h that
is out of sample on the pilot side, for the residual targets and the bias calibration).
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


# ---------------------------------------------------------------- Paper A estimator s_h / m_h (03a, Task 1)
def household_caps(pool, cap_def="hp_peak"):
    """Per-HP-household capacity P_n^max (kW). `hp_peak`: the HP_Peak definition (99.9th percentile of the RAW
    valid 15-min samples); `paperA`: Paper A's `robust_series_peak` of the gap-filled 15-min series (eq. pk)."""
    if cap_def == "hp_peak":
        return pool.meta.loc[pool.hp.columns, "hp_peak"].astype(float)
    return pool.hp.astype(np.float64).quantile(0.999)


def pilot_fit(T, hp, own, cap):
    """Verbatim port of Paper A `outputs._pilot_fit` on daily arrays of the pilot aggregate: T_h from the pilot's
    own net-load fit (hp + own), then the SF arm of clip(hp / cap, 0, 1) anchored at T_h -> (b_h, m_h, T_h)."""
    _, _, th, _ = fit_hockey_stick(T, hp + own, T_BALANCE_BOUNDS)
    b, m, _, _ = sf_arm(T, np.clip(hp / cap, 0, 1), th, "h")
    return b, m, th


def pool_pilot(pool, hh, caps):
    """Pilot of HP households `hh`: daily means of their summed HP and own load against the capacity-weighted mean
    of their stations' temperatures (one station: that station's T) -> dict(b, m, T_h, cap, n_hh)."""
    hh = sorted(hh)
    w, st = caps[hh] / caps[hh].sum(), pool.meta.loc[hh, "station"]
    T = sum(pool.temp[s].astype(np.float64) * w[st.index[st == s]].sum() for s in sorted(st.unique()))
    d = pd.DataFrame({"T": T, "hp": pool.hp[hh].astype(np.float64).sum(axis=1),
                      "own": pool.own[hh].astype(np.float64).sum(axis=1)}).resample("D").mean()
    d = d[np.isfinite(d).all(axis=1)]
    try:
        b, m, th = pilot_fit(d["T"].to_numpy(), d["hp"].to_numpy(), d["own"].to_numpy(), float(caps[hh].sum()))
    except (RuntimeError, ValueError):
        b = m = th = np.nan
    return {"b": b, "m": m, "T_h": th, "cap": float(caps[hh].sum()), "n_hh": len(hh)}


def paperA_pilots(pool, train_hp, caps, min_station=10):
    """(full pilot, {station: station pilot}) of one split seed; station pilots only with >= min_station HPs."""
    st = pool.meta.loc[list(train_hp), "station"]
    return pool_pilot(pool, train_hp, caps), {s: pool_pilot(pool, g.index, caps)
                                              for s, g in st.groupby(st) if len(g) >= min_station}


def paperA_estimate(s_h, m_h):
    """P_hat = s_h / m_h and the validity mask; invalid (s_h <= 0 or NaN, m_h <= 0 or NaN) -> P_hat = 0."""
    s_h, m_h = np.asarray(s_h, float), np.broadcast_to(np.asarray(m_h, float), np.shape(s_h))
    valid = np.isfinite(s_h) & (s_h > 0) & np.isfinite(m_h) & (m_h > 0)
    return np.where(valid, s_h / np.where(valid, m_h, 1.0), 0.0), valid


def paperA_corrected(s_h, size, s0, m_h):
    """03b Task 1: P_hat = max(s_h - N s0, 0) / m_h with N the dwelling count (`size`), s0 the per-dwelling non-TCL
    heating slope. Valid iff the corrected slope and m_h are positive; invalid -> 0 (counted), as `paperA_estimate`."""
    net = np.asarray(s_h, float) - np.asarray(size, float) * s0
    return paperA_estimate(np.where(np.isfinite(net) & (net > 0), net, np.nan), m_h)


def household_sensitivity(pool, fill_hh, own_hh=(), fill_station="KLO"):
    """03b Task 1: per-dwelling non-TCL heating sensitivity s0 = s_h(aggregate of `fill_hh` and the own non-HP load
    of `own_hh`) / N, by Paper A's net-load fit (`fit_daily`). Temperature = mean over the N dwellings of their
    station's temperature (fill dwellings: `fill_station`). Callers pass TRAIN households only."""
    own_hh, fill_hh = sorted(own_hh), sorted(fill_hh)
    st = pd.Series([fill_station] * len(fill_hh) + list(pool.meta.loc[own_hh, "station"]))
    N = len(st)
    T = sum(pool.temp[s].astype(np.float64) * (n / N) for s, n in st.value_counts().items())
    load = pool.fill[fill_hh].astype(np.float64).sum(axis=1) + (pool.own[own_hh].astype(np.float64).sum(axis=1) if own_hh else 0.0)
    f = fit_daily(*daily_means(T, load))
    return {"s0": f["s_h"] / N, "s_h": f["s_h"], "T_h": f["T_h"], "P_base": f["P_base"], "N": N}


def crossfit_pilot_m(pool, train_hp, caps, folds, members, m_full):
    """03b Task 3: pilot slope m_h that is out of sample on the pilot side, per substation of `members` (Series).
    Inner substation of fold k: pilot of the train HP households NOT in fold k (`folds`: hh -> fold). Train substation
    (no single fold): pilot of the train HP households not among its own HP members. Test: `m_full`.
    Returns (m Series over `members`, {fold k: m_h})."""
    train_hp = set(map(str, train_hp))
    fold_m, out = {}, pd.Series(m_full, index=members.index, dtype=float)
    for k in sorted(members.loc[members["split"] == "inner", "fold"].unique()):
        keep = sorted(h for h in train_hp if folds[h] != k)
        fold_m[int(k)] = pool_pilot(pool, keep, caps)["m"]
        out[(members["split"] == "inner") & (members["fold"] == k)] = fold_m[int(k)]
    for sid in members.index[members["split"] == "train"]:
        out[sid] = pool_pilot(pool, sorted(train_hp - set(members.at[sid, "hp_members"])), caps)["m"]
    return out, fold_m


def paperA_predictions(tab, full, by_station, s0=None, m_cf=None):
    """All estimators for every substation of `tab` -> {name: (P_hat, valid, fallback-to-full-pilot mask)}.
    `s0` {name: per-dwelling slope} adds the non-TCL-corrected estimators; `m_cf` (array over tab, cross-fitted m_h,
    equal to the full m_h on test rows) adds out-of-sample versions under key "cf" (name -> (P_hat, valid))."""
    m_st = tab["station"].map({s: p["m"] for s, p in by_station.items()})
    fallback = m_st.isna().to_numpy()
    no_fb = np.zeros(len(tab), bool)
    out = {"paperA_sh_mh": (*paperA_estimate(tab["s_h_net"], full["m"]), no_fb),
           "paperA_sh_mh_station": (*paperA_estimate(tab["s_h_net"], m_st.fillna(full["m"])), fallback)}
    for name, s in (s0 or {}).items():
        out[name] = (*paperA_corrected(tab["s_h_net"], tab["size"], s, full["m"]), no_fb)
    if m_cf is not None:
        out["cf"] = {"paperA_sh_mh": paperA_estimate(tab["s_h_net"], m_cf)}
        if s0:
            out["cf"]["paperA_corr"] = paperA_corrected(tab["s_h_net"], tab["size"], s0["paperA_corr"], m_cf)
    return out
