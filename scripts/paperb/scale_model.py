"""The hybrid ladder's rungs and the L4 scale models (iteration 06, Task 2; iterations/06-hybrid-ladder.md).

L4 (the proposed hybrid): P_hat = s_hat / m_hat_h * exp(f_theta(x)).
  s_hat = max(s_h(net) - N s0, 0): the net-load slope after Paper A's non-TCL correction (s0 per dwelling from the TRAIN fillers).
  m_hat_h, the slope per unit of capacity, in two variants (spec mode `l4a` / `l4b`):
    l4a  design-temperature normalisation: m_hat_h = kappa / (T_hat_h - T_design), with one parameter from the pilot,
         kappa = m_h(pilot) * (T_h(pilot) - T_design); T_hat_h is the substation's own net-load hinge.
    l4b  m_hat_h = exp(g(covariates)): Ridge regression of log m_h on the standardised, label-free aggregate covariates COVARS
         (T_hat_h, T_design, r_hat = s_hat / P_base(net), mean and 5th percentile of the station's daily temperature), fitted on
         the train aggregates with the label m_h = s_h(HP aggregate) / HP_Peak. alpha: lowest leave-one-fold-out MSE of log m_h
         over the inner substations (household-disjoint folds), from ALPHAS (0.01 to 1e5). T_design is one value per pool, so its coefficient
         is 0 within a pool; it is kept for pooled fits (07).
  f_theta is a residual model on the L2 inputs, fitted like L3's (residual.py) on z = log y - log(s_hat / m_hat_h).
Zero residual: `paperA_l4a` / `paperA_l4b` (rows s_hat / m_hat_h, reported with the physics rows). Invalid s_hat (<= 0 or NaN)
-> P_hat = 0, counted (as `physics.paperA_estimate`).
Cross-fitting (as 03b Task 3): the residual's training targets use an m_hat_h fitted without the row's households. l4a: kappa
from the cross-fitted pilot (`physics.crossfit_pilot_m`: inner row of fold k = pilot without fold k; train row = pilot without
its own HP members). l4b: inner row of fold k = g fitted on the inner rows of the other folds; train row = g fitted on the
train rows that share no HP household with it (other stations, and disjoint substations of its own station; with fewer than
MIN_ROWS such rows the all-train g is used and the row is counted in `n_cf_fallback`). Test rows: the full pilot / the g of all
train rows.
The own-load term of `paperA_corr_own` (m_h' instead of m_h) is a constant factor on m_hat_h, which the residual's intercept
absorbs; it is not a separate L4 component (`paperA_corr_own` stays an L0 row).
"""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from paperb.physics import paperA_estimate

BASE = {"residual": "paperA_sh_mh", "l4a": "paperA_l4a", "l4b": "paperA_l4b"}     # residual-type mode -> its physics estimate
COVARS = ["T_h", "T_design", "r_hat", "T_mean", "T_q05"]
ALPHAS, MIN_ROWS = tuple(10.0 ** k for k in range(-2, 6)), 10      # up to 1e5: with ~2000 standardised rows that is close to a constant m_h


def rung(spec):
    """Ladder rung (L1-L4) of an ML spec (method, anchor, feature_set, mode, target_transform)."""
    return {"residual": "L3", "l4a": "L4", "l4b": "L4"}.get(spec[3], "L1" if spec[2] in ("whdd", "raw") else "L2")


def covariates(tab, s0, clim, t_design):
    """Label-free aggregate quantities of the substations of `tab`: s_hat and the covariates of l4b. `clim`: per-station
    climate statistics (`climate`); `s0`: per-dwelling non-TCL slope of each row; `t_design`: one value, or one per row."""
    s_hat = np.maximum(tab["s_h_net"].to_numpy(float) - tab["size"].to_numpy(float) * np.asarray(s0, float), 0.0)
    C = pd.DataFrame({"s_hat": s_hat, "T_h": tab["T_h_net"].to_numpy(float), "T_design": np.broadcast_to(np.asarray(t_design, float), s_hat.shape),
                      "r_hat": s_hat / tab["P_base_net"].where(tab["P_base_net"] > 0).to_numpy(float)}, index=tab.index)
    return pd.concat([C, clim.reindex(tab["station"]).set_axis(tab.index)], axis=1)


def climate(temp):
    """Per station: mean and 5th percentile of the daily mean temperature (frame indexed by station)."""
    d = temp.resample("D").mean()
    return pd.DataFrame({"T_mean": d.mean(), "T_q05": d.quantile(0.05)})


def estimate(C, m_hat):
    """(P_hat, valid) = s_hat / m_hat_h; invalid (s_hat <= 0 or NaN, m_hat <= 0 or NaN) -> 0."""
    return paperA_estimate(C["s_hat"].where(C["s_hat"] > 0), m_hat)


class Scale:
    """m_hat_h of one L4 variant. `base(tab)` applies the saved model to another version of the same substations (R-shift)."""

    def __init__(self, kind, kappa=None, alpha=None):
        self.kind, self.kappa, self.alpha = kind, kappa, alpha

    def fit(self, C, m):
        ok = np.isfinite(m) & (np.asarray(m, float) > 0)
        self.g = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(),
                               Ridge(alpha=self.alpha)).fit(C.loc[ok, COVARS], np.log(np.asarray(m, float)[ok]))
        return self

    def m_hat(self, C):
        if self.kind == "l4a":
            return np.asarray(self.kappa, float) / (C["T_h"] - C["T_design"]).to_numpy(float)
        return np.exp(self.g.predict(C[COVARS]))

    def base(self, tab, s0=None):
        """(P_hat, valid) on `tab` with the saved s0, or with `s0` (06 R(i) update row: only s0 changes; kappa / g stay frozen)."""
        C = covariates(tab, self.s0.reindex(tab.index) if s0 is None else s0, self.clim, self.t_design)
        return estimate(C, self.m_hat(C))


def crossfit_m(C, m, tab, members, alphas=ALPHAS, min_rows=MIN_ROWS):
    """l4b: (m_hat over the rows of `tab`, cross-fitted on inner and train rows; the Scale of all train rows; info dict)."""
    m = np.asarray(m, float)
    tr, inn, fold = (tab["split"] == "train").to_numpy(), (tab["split"] == "inner").to_numpy(), tab["fold"].to_numpy()
    fit = lambda a, rows: Scale("l4b", alpha=a).fit(C[rows], m[rows])                    # noqa: E731
    lab = np.isfinite(m) & (m > 0)

    def oof(a):
        out = np.full(len(tab), np.nan)
        for k in np.unique(fold[inn]):
            out[inn & (fold == k)] = fit(a, inn & (fold != k) & lab).m_hat(C[inn & (fold == k)])
        return out

    cv = {a: float(np.mean((np.log(oof(a)[inn & lab]) - np.log(m[inn & lab])) ** 2)) for a in alphas}
    alpha = min(cv, key=cv.get)
    full = fit(alpha, tr & lab)
    out, n_fb = np.where(inn, oof(alpha), full.m_hat(C)), 0
    hp = members.loc[tab.index, "hp_members"]
    for st in pd.unique(tab.loc[tr, "station"]):                       # HP members come from one station: other stations never overlap
        own = np.flatnonzero(tr & (tab["station"] == st).to_numpy())
        hh = sorted(set().union(*hp.iloc[own]))
        M = np.zeros((len(own), len(hh)), np.float32)
        for i, j in enumerate(own):
            M[i, [hh.index(h) for h in hp.iloc[j]]] = 1.0
        other = tr & lab & (tab["station"] != st).to_numpy()
        for i, j in enumerate(own):
            rows = other.copy()
            rows[own[(M @ M[i]) == 0]] = True
            rows &= lab
            if rows.sum() < min_rows:
                n_fb += 1
                continue
            out[j] = fit(alpha, rows).m_hat(C.iloc[[j]])[0]
    return out, full, {"l4b_alpha": alpha, "l4b_cv_mse": cv[alpha], "n_cf_fallback": n_fb}


def l4_bases(tab, members, num, temp, t_design):
    """Both L4 variants for the substations of `tab` (splits train / inner / test; `num` = the runner's pilot numbers: full pilot,
    cross-fitted m_cf and T_cf, s0). Returns (rows {paperA_l4x: (P_hat, valid, no-fallback mask)}, cross-fitted {paperA_l4x:
    (P_hat, valid)}, {mode: Scale}, frame of covariates / m_hat per substation, info)."""
    if num.get("T_cf") is None:
        raise ValueError("L4 needs the cross-fitted pilot (paperA.crossfit: true)")
    s0, clim = pd.Series(np.asarray(num["s0"]["paperA_corr"], float), index=tab.index), climate(temp)
    C = covariates(tab, s0, clim, t_design)
    te = (tab["split"] == "test").to_numpy()
    m_true = (tab["s_h"] / tab["HP_Peak"]).where(tab["s_h"] > 0).to_numpy(float)
    kappa = lambda m, T: np.asarray(m, float) * (np.asarray(T, float) - t_design)        # noqa: E731
    sa = Scale("l4a", float(kappa(num["full"]["m"], num["full"]["T_h"])))
    m_cf_b, sb, info = crossfit_m(C, m_true, tab, members)
    rows, cf, cov = {}, {}, C.assign(m_true=m_true, s0=s0, **{c: tab[c] for c in ("split", "fold", "station", "size", "p", "HP_Count", "HP_Peak", "s_h_net")})
    for s, m_cf in ((sa, Scale("l4a", kappa(num["m_cf"], num["T_cf"])).m_hat(C)), (sb, m_cf_b)):
        s.s0, s.clim, s.t_design = s0[te], clim, t_design
        m_full = s.m_hat(C)
        rows[BASE[s.kind]] = (*estimate(C, m_full), np.zeros(len(tab), bool))
        cf[BASE[s.kind]] = estimate(C, np.where(te, m_full, m_cf))
        cov[f"m_{s.kind}"], cov[f"m_{s.kind}_cf"] = m_full, np.where(te, m_full, m_cf)
    return rows, cf, {"l4a": sa, "l4b": sb}, cov, {**info, "l4a_kappa": sa.kappa}
