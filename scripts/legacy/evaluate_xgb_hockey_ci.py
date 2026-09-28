"""XGBoost vs hockey-stick capacity estimation, with MAPE and confidence
intervals, on the Swiss test split and the synthetic WPUQ substations.

Two estimators only, as requested:
* XGBoost  -- feature model on the 60 CV-selected features; per-estimate 90%
  prediction intervals via quantile regression (q05/q95), point = tuned model.
* Hockey-stick -- fit a 3-parameter load-vs-temperature hockey stick per
  substation (daily min-temp / max-load, heating season), take the slope
  (HP_Sensitivity), and map slope -> HP_Peak with a linear regression fitted on
  the TRAIN split; per-estimate 90% prediction interval from the OLS formula.

Reported per evaluation set: MAPE (with a bootstrap 95% CI), RMSE, R2, and the
prediction-interval coverage + mean width. National HDD bases 12 (CH) / 15 (DE).
"""
import json
import pickle

import numpy as np
import pandas as pd

import hp_capacity as hc
import hp_pools as hpp
import benchmark_capacity_models as B
from hp_common import fit_hockey_stick, daily_min_max_heating_season
import xgboost as xgb

SEED = 42
rng = np.random.default_rng(SEED)
T_BASE_CH, T_BASE_DE = 12.0, 15.0


# ---------------------------------------------------------------- metrics ----
def mape(y, p):
    m = y != 0
    return float(np.mean(np.abs((y[m] - p[m]) / y[m])) * 100)


def point_metrics(y, p):
    return dict(mape=mape(y, p), **{k: hc.compute_metrics(y, p)[k]
                                    for k in ("rmse", "r2")})


def boot_mape_ci(y, p, n=2000):
    idx = np.arange(len(y))
    vals = [mape(y[b], p[b]) for b in (rng.choice(idx, len(idx), replace=True)
                                       for _ in range(n))]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def pi_coverage(y, lo, hi):
    inside = (y >= lo) & (y <= hi)
    return float(inside.mean()), float(np.mean(hi - lo))


# ------------------------------------------------------- hockey-stick model --
def hs_sensitivity(load, temp, t_base):
    """Slope (kW/degC) of the peak-tied hockey stick, or NaN if the fit fails."""
    try:
        x, y = daily_min_max_heating_season(temp, load, heating_season_thresh=t_base)
        if len(x) < 20:
            return np.nan
        _, slope, _, _ = fit_hockey_stick(x, y)
        return float(slope)
    except Exception:
        return np.nan


def ols_fit(x, y):
    """Simple linear regression y = a + b x; returns coeffs + PI ingredients."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x); xbar = x.mean()
    Sxx = np.sum((x - xbar) ** 2)
    b = np.sum((x - xbar) * (y - y.mean())) / Sxx
    a = y.mean() - b * xbar
    resid = y - (a + b * x)
    s = np.sqrt(np.sum(resid ** 2) / (n - 2))
    return dict(a=a, b=b, s=s, n=n, xbar=xbar, Sxx=Sxx)


def ols_predict(fit, x0, alpha=0.10):
    from scipy.stats import t as tdist
    x0 = np.asarray(x0, float)
    pred = fit["a"] + fit["b"] * x0
    tval = tdist.ppf(1 - alpha / 2, fit["n"] - 2)
    se = fit["s"] * np.sqrt(1 + 1 / fit["n"] + (x0 - fit["xbar"]) ** 2 / fit["Sxx"])
    return pred, pred - tval * se, pred + tval * se


# ------------------------------------------------------------------- main ----
def main():
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    sel = json.load(open("models/xgb_selected_features.json"))["selected_features"]
    sel_meta = json.load(open("models/xgb_selected_features.json"))["sel_meta"]

    # rebuild the synthetic WPUQ substations (same params as the benchmark set)
    pool = hpp.build_pool_wpuq(verbose=False)
    wp = hc.build_wpuq_substations(pool, n=400, size_range=(10, 37),
                                   pen_max=0.5, seed=7)
    assert len(wp) == len(yw), "WPUQ rebuild does not match cached targets"

    Xtr = X.loc[tr, sel]; ytr = y.loc[tr].to_numpy()
    med = Xtr.median()

    # ---- XGBoost: point (tuned) + quantile prediction interval -------------
    def xgb_base(**kw):
        return xgb.XGBRegressor(
            learning_rate=sel_meta["eta"], n_estimators=int(sel_meta["n_estimators_final"]),
            max_depth=int(sel_meta["max_depth"]), gamma=sel_meta["gamma"],
            subsample=sel_meta["subsample"], reg_alpha=sel_meta["reg_alpha"],
            reg_lambda=sel_meta["reg_lambda"], min_child_weight=int(sel_meta["min_child_weight"]),
            colsample_bytree=sel_meta["colsample_bytree"], tree_method="hist",
            n_jobs=-1, **kw)

    xgb_pt = xgb_base().fit(Xtr.fillna(med), ytr)
    xgb_lo = xgb_base(objective="reg:quantileerror", quantile_alpha=0.05).fit(Xtr.fillna(med), ytr)
    xgb_hi = xgb_base(objective="reg:quantileerror", quantile_alpha=0.95).fit(Xtr.fillna(med), ytr)

    # ---- hockey-stick: slope per substation, then slope -> HP_Peak (train) --
    def slopes(entities, load_col, temp_col, t_base):
        return np.array([hs_sensitivity(entities.loc[i, load_col],
                                        entities.loc[i, temp_col], t_base)
                         for i in entities.index])

    s_tr = slopes(sub.loc[tr], "Total_Load", "Temperature", T_BASE_CH)
    ok = np.isfinite(s_tr)
    hs = ols_fit(s_tr[ok], ytr[ok])
    print(f"hockey-stick slope->HP_Peak (train, n={ok.sum()}): "
          f"HP_Peak = {hs['a']:.1f} + {hs['b']:.1f} * slope\n", flush=True)

    # ---- evaluation on the two sets ----------------------------------------
    sets = {
        "Swiss test (unseen subs)": dict(
            Xf=X.loc[te, sel], yy=y.loc[te].to_numpy(),
            ent=sub.loc[te], lc="Total_Load", tc="Temperature", tb=T_BASE_CH),
        "synthetic WPUQ substations": dict(
            Xf=Xw[sel], yy=yw.to_numpy(),
            ent=wp, lc="Total_Load", tc="Temperature", tb=T_BASE_DE),
    }

    print("=" * 92)
    hdr = (f"{'set':28s} {'method':13s} {'n':>4s} {'MAPE %':>7s} "
           f"{'MAPE 95% CI':>16s} {'RMSE':>7s} {'R2':>7s} {'PI cov':>7s} {'PI wid':>7s}")
    print(hdr); print("-" * len(hdr))
    out = []
    for name, d in sets.items():
        yy = d["yy"]; m = yy != 0
        Xf = d["Xf"].fillna(med)

        # XGBoost
        p = hc.clip_non_negative(xgb_pt.predict(Xf))
        lo = hc.clip_non_negative(xgb_lo.predict(Xf))
        hi = hc.clip_non_negative(xgb_hi.predict(Xf))
        hi = np.maximum(hi, lo)
        pm = point_metrics(yy[m], p[m]); ci = boot_mape_ci(yy[m], p[m])
        cov, wid = pi_coverage(yy[m], lo[m], hi[m])
        print(f"{name:28s} {'XGBoost':13s} {m.sum():4d} {pm['mape']:7.1f} "
              f"[{ci[0]:6.1f},{ci[1]:6.1f}] {pm['rmse']:7.1f} {pm['r2']:7.3f} "
              f"{cov*100:6.0f}% {wid:7.1f}")
        out.append(dict(set=name, method="XGBoost", n=int(m.sum()), **pm,
                        mape_lo=ci[0], mape_hi=ci[1], pi_cov=cov, pi_width=wid))

        # hockey-stick
        s = slopes(d["ent"], d["lc"], d["tc"], d["tb"])
        good = np.isfinite(s) & m
        pp, plo, phi = ols_predict(hs, s[good])
        pp = np.maximum(pp, 0); plo = np.maximum(plo, 0); phi = np.maximum(phi, 0)
        yg = yy[good]
        pm = point_metrics(yg, pp); ci = boot_mape_ci(yg, pp)
        cov, wid = pi_coverage(yg, plo, phi)
        print(f"{'':28s} {'hockey-stick':13s} {good.sum():4d} {pm['mape']:7.1f} "
              f"[{ci[0]:6.1f},{ci[1]:6.1f}] {pm['rmse']:7.1f} {pm['r2']:7.3f} "
              f"{cov*100:6.0f}% {wid:7.1f}")
        out.append(dict(set=name, method="hockey-stick", n=int(good.sum()), **pm,
                        mape_lo=ci[0], mape_hi=ci[1], pi_cov=cov, pi_width=wid))
    print("=" * 92)
    print("PI = 90% prediction interval (XGBoost q05-q95 / hockey-stick OLS); "
          "cov = fraction of true inside, wid = mean width (kW).")

    # --- real WPUQ feeder (n=1): point estimate + 90% PI (no bootstrap) ------
    rf = hc.build_wpuq_real_feeder(pool)
    Xr_f = Xr[sel].fillna(med)
    xp = float(hc.clip_non_negative(xgb_pt.predict(Xr_f))[0])
    xlo = float(hc.clip_non_negative(xgb_lo.predict(Xr_f))[0])
    xhi = max(float(hc.clip_non_negative(xgb_hi.predict(Xr_f))[0]), xlo)
    s0 = hs_sensitivity(rf.loc["WPUQ_real", "Total_Load"],
                        rf.loc["WPUQ_real", "Temperature"], T_BASE_DE)
    hp_, hlo_, hhi_ = ols_predict(hs, np.array([s0]))
    hp0 = max(float(hp_[0]), 0); hlo = max(float(hlo_[0]), 0); hhi = max(float(hhi_[0]), 0)

    print("\n" + "=" * 92)
    print(f"REAL WPUQ feeder (n=1) -- TRUE installed HP capacity {yr:.1f} kW")
    print("-" * 92)
    for meth, p, lo, hi in [("XGBoost", xp, xlo, xhi),
                            ("hockey-stick", hp0, hlo, hhi)]:
        inside = lo <= yr <= hi
        print(f"  {meth:13s}: point {p:6.1f} kW  ({(p - yr) / yr * 100:+4.0f} %, "
              f"|err| {abs(p - yr) / yr * 100:3.0f} %)   90% PI [{lo:5.0f}, {hi:5.0f}] kW"
              f"  -> true {yr:.0f} is {'INSIDE' if inside else 'OUTSIDE'}")
        out.append(dict(set="real WPUQ feeder", method=meth, n=1,
                        mape=abs(p - yr) / yr * 100, rmse=abs(p - yr), r2=np.nan,
                        mape_lo=np.nan, mape_hi=np.nan,
                        pi_cov=float(lo <= yr <= hi), pi_width=hi - lo,
                        pred=p, pi_lo=lo, pi_hi=hi, true=yr))

    pd.DataFrame(out).to_csv("data/xgb_hockey_ci_metrics.csv", index=False)
    print("\nSaved -> data/xgb_hockey_ci_metrics.csv")


if __name__ == "__main__":
    main()
