"""Error per model per HP-penetration level on the UNSEEN Swiss test substations,
then a penetration-gated XGBoost/hockey-stick ensemble.

Part 1 mirrors the real-WPUQ penetration sweep but on the household-disjoint
Swiss TEST split (each substation carries its true HP_ratio). Part 2 builds an
ensemble that must decide, per feeder, which estimator to trust WITHOUT knowing
the true penetration -- it gates on an OBSERVABLE proxy (the hockey-stick fit
quality r2, which is high only when the heating response is clean, i.e. high
penetration). Trained only on Swiss train; evaluated on Swiss test and the real
WPUQ penetration variants.
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

T_BASE_CH, T_BASE_DE = 12.0, 15.0


def hs_fit(load, temp, t_base):
    """Return (slope, r2) of the peak-tied hockey stick, or (nan, nan)."""
    try:
        x, y = daily_min_max_heating_season(temp, load, heating_season_thresh=t_base)
        if len(x) < 20:
            return np.nan, np.nan
        _, slope, _, r2 = fit_hockey_stick(x, y)
        return float(slope), float(r2)
    except Exception:
        return np.nan, np.nan


def ols_fit(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x); xbar = x.mean(); Sxx = np.sum((x - xbar) ** 2)
    b = np.sum((x - xbar) * (y - y.mean())) / Sxx
    a = y.mean() - b * xbar
    s = np.sqrt(np.sum((y - (a + b * x)) ** 2) / (n - 2))
    return dict(a=a, b=b, s=s, n=n, xbar=xbar, Sxx=Sxx)


def ols_pred(fit, x0):
    return fit["a"] + fit["b"] * np.asarray(x0, float)


def mape(t, p):
    t = np.asarray(t, float); p = np.asarray(p, float)
    m = t != 0
    return float(np.mean(np.abs((t[m] - p[m]) / t[m])) * 100)


def main():
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()
    sub = pickle.load(open("data/substations_data_pooled.pkl", "rb"))
    meta = json.load(open("models/xgb_selected_features.json"))
    sel, sm = meta["selected_features"], meta["sel_meta"]

    Xtr = X.loc[tr, sel]; ytr = y.loc[tr].to_numpy(); med = Xtr.median()
    xgbm = xgb.XGBRegressor(
        learning_rate=sm["eta"], n_estimators=int(sm["n_estimators_final"]),
        max_depth=int(sm["max_depth"]), gamma=sm["gamma"], subsample=sm["subsample"],
        reg_alpha=sm["reg_alpha"], reg_lambda=sm["reg_lambda"],
        min_child_weight=int(sm["min_child_weight"]),
        colsample_bytree=sm["colsample_bytree"], tree_method="hist", n_jobs=-1
    ).fit(Xtr.fillna(med), ytr)

    # hockey-stick slope -> HP_Peak, fitted on train
    sr = np.array([hs_fit(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_BASE_CH)
                   for i in tr])
    s_tr, r2_tr = sr[:, 0], sr[:, 1]
    ok = np.isfinite(s_tr)
    hs = ols_fit(s_tr[ok], ytr[ok])

    # ---- per-substation predictions on the Swiss test split ----------------
    te_df = pd.DataFrame(index=te)
    te_df["pen"] = sub.loc[te, "HP_ratio"].round(2)
    te_df["true"] = y.loc[te]
    te_df["xgb"] = hc.clip_non_negative(xgbm.predict(X.loc[te, sel].fillna(med)))
    sr_te = np.array([hs_fit(sub.loc[i, "Total_Load"], sub.loc[i, "Temperature"], T_BASE_CH)
                      for i in te])
    te_df["slope"], te_df["hs_r2"] = sr_te[:, 0], sr_te[:, 1]
    te_df["hockey"] = np.maximum(ols_pred(hs, te_df["slope"].to_numpy()), 0)

    print("=" * 78)
    print("UNSEEN Swiss test substations -- MAPE per model per HP penetration")
    print("=" * 78)
    print(f"{'pen':>5s} {'n':>5s} {'true kW':>9s} {'XGB MAPE%':>10s} "
          f"{'hockey MAPE%':>13s} {'hockey r2':>10s}")
    print("-" * 78)
    rows = []
    for p, g in te_df.groupby("pen"):
        xm = mape(g["true"], g["xgb"]); hm = mape(g["true"], g["hockey"])
        rows.append(dict(penetration=p, n=len(g), true_mean=g["true"].mean(),
                         xgb_mape=xm, hockey_mape=hm, hockey_r2=g["hs_r2"].median()))
        print(f"{p:5.2f} {len(g):5d} {g['true'].mean():9.1f} {xm:10.1f} "
              f"{hm:13.1f} {g['hs_r2'].median():10.2f}")
    print("=" * 78)
    pd.DataFrame(rows).to_csv("data/swiss_penetration_error.csv", index=False)

    # ---- Part 2: penetration-gated ensemble --------------------------------
    # We cannot use true penetration at inference. Gate on the hockey-stick fit
    # quality r2 (observable): pick the threshold on TRAIN that minimises MAPE,
    # then apply the frozen rule to test / WPUQ. Above the r2 threshold trust the
    # hockey-stick estimate, below it trust XGBoost.
    xgb_tr = hc.clip_non_negative(xgbm.predict(Xtr.fillna(med)))
    hk_tr = np.maximum(ols_pred(hs, np.where(np.isfinite(s_tr), s_tr, np.nan)), 0)
    valid_tr = np.isfinite(r2_tr) & np.isfinite(hk_tr)
    best = None
    for thr in np.linspace(0.3, 0.98, 35):
        use_h = valid_tr & (r2_tr >= thr)
        blend = np.where(use_h, hk_tr, xgb_tr)
        m = mape(ytr, blend)
        if best is None or m < best["mape"]:
            best = dict(thr=float(thr), mape=m, frac_hockey=float(np.mean(use_h)))
    thr_opt = best["thr"]
    thr_beyond = float(np.nanmax(r2_tr[ok]))   # cleaner heating response than ANY train feeder
    print(f"\ngate A (train-MAPE-optimal): hockey if fit r2 >= {thr_opt:.2f} "
          f"(fires on {best['frac_hockey']*100:.0f}% of train)")
    print(f"gate B (beyond-training):    hockey if fit r2 >  {thr_beyond:.2f} "
          f"(= max train hockey r2; fires only for feeders with a cleaner response than training)")

    def gate(df, thr, strict=False):
        r = df["hs_r2"].to_numpy(); h = df["hockey"].to_numpy(); x = df["xgb"].to_numpy()
        use_h = np.isfinite(r) & np.isfinite(h) & ((r > thr) if strict else (r >= thr))
        return np.where(use_h, h, x), use_h

    def oracle(df):   # ceiling: pick the better method per feeder (uses truth)
        t = df["true" if "true" in df else "HP_Peak"].to_numpy()
        h = df["hockey"].to_numpy(); x = df["xgb"].to_numpy()
        return np.where(np.abs(h - t) < np.abs(x - t), h, x)

    def report(df, tag):
        t = df["true" if "true" in df else "HP_Peak"]
        eA, uA = gate(df, thr_opt); eB, uB = gate(df, thr_beyond, strict=True)
        print(f"\n--- {tag}: overall MAPE ---")
        print(f"  XGBoost            {mape(t, df['xgb']):6.1f}%")
        print(f"  hockey-stick       {mape(t, df['hockey']):6.1f}%")
        print(f"  gate A (opt)       {mape(t, eA):6.1f}%  (hockey on {uA.mean()*100:.0f}%)")
        print(f"  gate B (beyond)    {mape(t, eB):6.1f}%  (hockey on {uB.mean()*100:.0f}%)")
        print(f"  ORACLE (ceiling)   {mape(t, oracle(df)):6.1f}%")
        return eB

    report(te_df, "Swiss test")

    # real WPUQ penetration variants (reuse the saved variants + recompute preds)
    pool = hpp.build_pool_wpuq(verbose=False)
    idx = pool["index"]; hp_mat, other_mat = pool["hp_mat"], pool["other_mat"]
    nh_all = hp_mat.shape[0]
    robust = np.array([hc.robust_series_peak(hp_mat[i], 0.999) for i in range(nh_all)])
    base_total = other_mat.sum(axis=0); temp = pd.Series(pool["temperature"]["WPUQ"], index=idx)
    rng = np.random.default_rng(42)
    vr = {}
    kk = 0
    for nh in [4, 7, 11, 15, 19, 22, 26, 30, 33, 37]:
        seen = set(); reps = 1 if nh == nh_all else 30
        while len([r for r in vr.values() if r["n_hp"] == nh]) < reps:
            hh = tuple(sorted(rng.choice(nh_all, nh, replace=False)))
            if hh in seen:
                continue
            seen.add(hh)
            load = base_total + hp_mat[list(hh)].sum(axis=0)
            vr[kk] = {"Total_Load": pd.Series(load, index=idx), "Temperature": temp,
                      "size": nh_all, "n_hp": nh, "penetration": nh / nh_all,
                      "HP_Peak": float(robust[list(hh)].sum())}
            kk += 1
    V = pd.DataFrame.from_dict(vr, orient="index")
    Xv_raw = hc.extract_windowed_hdd_features_from_entity_dataframe(
        V, T_base=T_BASE_DE, use_entity_index=True, show_progress=False, **B.CAP_FEATURE_KWARGS)
    Xv = hc.capacity_feature_matrix(Xv_raw, hc.select_scale_free_columns(Xv_raw),
                                    size=V["size"], peak=V["Total_Load"].apply(hc.series_peak))
    Xv = Xv.reindex(columns=X.columns)[sel].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    V["xgb"] = hc.clip_non_negative(xgbm.predict(Xv.fillna(med)))
    srv = np.array([hs_fit(V.loc[i, "Total_Load"], V.loc[i, "Temperature"], T_BASE_DE)
                    for i in V.index])
    V["slope"], V["hs_r2"] = srv[:, 0], srv[:, 1]
    V["hockey"] = np.maximum(ols_pred(hs, V["slope"].to_numpy()), 0)
    V["ensemble"], useh_v = gate(V, thr_beyond, strict=True)   # deployable gate B

    report(V, "Real WPUQ penetration variants")

    print("\n--- WPUQ variants: MAPE by penetration (gate B = beyond-training) ---")
    print(f"{'pen':>5s} {'hockey r2':>10s} {'XGB':>7s} {'hockey':>7s} "
          f"{'gateB':>7s} {'oracle':>7s} {'pick':>8s}")
    erows = []
    for p, g in V.groupby("penetration"):
        loc = [V.index.get_loc(i) for i in g.index]
        picks = "hockey" if useh_v[loc].mean() > 0.5 else "xgb"
        xm = mape(g["HP_Peak"], g["xgb"]); hm = mape(g["HP_Peak"], g["hockey"])
        em = mape(g["HP_Peak"], g["ensemble"]); om = mape(g["HP_Peak"], oracle(g))
        print(f"{p:5.2f} {g['hs_r2'].median():10.2f} {xm:7.1f} {hm:7.1f} "
              f"{em:7.1f} {om:7.1f} {picks:>8s}")
        erows.append(dict(penetration=p, hockey_r2=g["hs_r2"].median(), xgb_mape=xm,
                          hockey_mape=hm, ensemble_mape=em, oracle_mape=om))
    pd.DataFrame(erows).to_csv("data/wpuq_ensemble_by_pen.csv", index=False)
    json.dump({"gate_A_train_optimal": thr_opt, "gate_B_beyond_training": thr_beyond,
               "train": best}, open("models/ensemble_gate.json", "w"), indent=2)
    print("\nSaved -> data/swiss_penetration_error.csv, data/wpuq_ensemble_by_pen.csv, "
          "models/ensemble_gate.json")


if __name__ == "__main__":
    main()
