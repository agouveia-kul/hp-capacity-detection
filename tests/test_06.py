"""Iteration 06, the hybrid ladder (iterations/06-hybrid-ladder.md): L1 / L2 inputs (Task 1), L4 scale models (Task 2), L5
ensembles (Task 3) and the queue wiring (Task 4). Toy data only; no pool cache is needed."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from paperb import load_config  # noqa: E402
from paperb import ensemble as EN  # noqa: E402
from paperb import run_benchmark as RB  # noqa: E402
from paperb import run_queue as RQ  # noqa: E402
from paperb import scale_model as SM  # noqa: E402
from paperb import train as T  # noqa: E402
from paperb.models_rawseries import PHYS_PREFIX, raw_columns  # noqa: E402
from paperb.persist import load_model, reload_check  # noqa: E402
from paperb.residual import compose  # noqa: E402
from test_05b import NEW, toy_cfg, toy_pa, toy_tab, toy_xy  # noqa: E402  (toy fixtures of 05b)

QUEUE = yaml.safe_load(open(ROOT / "configs" / "iter06.yaml"))
LADDER = {**load_config("configs/iter06_a_gb.yaml"), "physics_baselines": [], "anchor_only_baselines": {"models": [], "features": []},
          "paperA": {"estimators": []}}
SENTINEL = 987654.321


# ------------------------------------------------------------------ Task 1: the rungs' inputs
def ladder_tab():
    """toy_tab plus whdd-like and raw columns, with a sentinel in every netfit column and every physics / Paper A / label column."""
    tab, F = toy_tab()
    rng = np.random.default_rng(1)
    F = pd.concat([F, pd.DataFrame(rng.normal(size=(len(F), 3)), index=F.index, columns=["Feature a_norm_peak", "Feature ratio_b", "Feature normdelta_c"]),
                   pd.DataFrame(rng.normal(size=(len(F), 20)), index=F.index, columns=raw_columns(10))], axis=1)
    return tab, F


def test_l1_inputs_have_no_netfit_or_paperA_column():
    tab, F = ladder_tab()
    F[[c for c in F.columns if c.startswith("nf_")]] = SENTINEL
    phys = ["s_h_net", "P_base_net", "T_h_net", "delta_net", "hdh_slope_net", "s_h", "T_h_hp", "P_base_nonhp", "r", "HP_Peak", "HP_Count"]
    tab[phys] = SENTINEL
    for fs in ("whdd", "raw"):                                                  # L1: generic features and scale anchors only
        for anchor in ("size", "size_peak"):
            X = T.feature_matrix(F, tab, anchor, fs)
            assert not (X.to_numpy() == SENTINEL).any() and not any(c.startswith(("nf_", PHYS_PREFIX)) for c in X.columns)
            assert [c for c in X.columns if c.startswith("Feature Scale_")] == [f"Feature Scale_{a}" for a in T.ANCHOR_COLS[anchor]]
    for fs in ("netfit", "both", "rawphys"):                                    # L2: the physics-derived columns are there
        assert (T.feature_matrix(F, tab, "size", fs).to_numpy() == SENTINEL).any()
    assert [c for c in T.feature_matrix(F, tab, "size", "rawphys").columns if c.startswith(PHYS_PREFIX)] == [f"{PHYS_PREFIX}{k}" for k in ("s_h", "P_base", "T_h")]


@pytest.mark.parametrize("models,want", [(["Lasso"], {"L1": 2, "L2": 4, "L3": 4, "L4": 8}), (["CNN"], {"L1": 2, "L2": 2, "L3": 2, "L4": 4})])
def test_ladder_grid_is_the_preregistered_one(models, want):
    specs = [s for s in RB.specs({**LADDER, "models": models, "residual_models": models}) if s[0] in models]   # without the paperA_sh_mh row
    by = {r: [s for s in specs if SM.rung(s) == r] for r in want}
    assert {r: len(v) for r, v in by.items()} == want and len(specs) == sum(want.values())
    tab = models == ["Lasso"]
    assert {s[2] for s in by["L1"]} == ({"whdd"} if tab else {"raw"}) and {s[3] for s in by["L1"]} == {"direct"}
    l2 = {"netfit", "both"} if tab else {"rawphys"}
    assert {s[2] for s in by["L2"]} == l2 and {s[3] for s in by["L2"]} == {"direct"}
    assert {s[2] for s in by["L3"]} == l2 and {s[3] for s in by["L3"]} == {"residual"}
    assert {s[2] for s in by["L4"]} == l2 and {s[3] for s in by["L4"]} == {"l4a", "l4b"}
    assert {s[1] for s in specs} == {"size", "size_peak"} and {s[4] for s in specs} == {"log"}


def test_feature_cache_key_is_the_computed_sets():
    assert RB.computed_sets(LADDER) == ["both", "netfit", "raw"] == RB.computed_sets({"feature_sets": ["netfit", "both", "raw"]})   # 05b Arm 2's caches
    assert RB.computed_sets({}) == ["whdd"] and RB.computed_sets({"feature_sets": ["netfit", "raw"]}) == ["netfit", "raw"]
    assert RB.computed_sets({"feature_sets": ["whdd", "rawphys"]}) == ["raw", "whdd"]


def test_whdd_on_30min_series_equals_the_series_repeated_at_15min():
    """GB-EoH is 30-min and whdd keeps `resolution: 15`: each half-hour is repeated, which leaves the features of the 30-min series
    (equal on the median feature; a few differences of quantiles move by a few percent)."""
    from hp_capacity import extract_windowed_hdd_features_from_series as ex
    from hp_capacity import select_scale_free_columns
    kw, rng = LADDER["features"]["kwargs"], np.random.default_rng(0)
    assert kw["resolution"] == 15
    idx = pd.date_range("2021-11-01", "2022-10-31 23:30", freq="30min", tz="UTC")
    T_ = pd.Series(10 + 8 * np.sin(2 * np.pi * (np.arange(len(idx)) // 48 - 200) / 365) + rng.normal(0, 1.5, len(idx)), index=idx)
    y = pd.Series(5 + 0.4 * np.maximum(0, 15 - T_) + rng.gamma(2, 0.5, len(idx)), index=idx)
    f15 = pd.Series(ex(y, T_, T_base=12.0, **kw))
    cols = select_scale_free_columns(pd.DataFrame([f15]))
    rep = pd.Series(ex(y.resample("15min").ffill(), T_.resample("15min").ffill(), T_base=12.0, **kw))
    f30 = pd.Series(ex(y, T_, T_base=12.0, **{**kw, "resolution": 30}))
    assert len(cols) > 100 and f15[cols].notna().all() and (f15[cols] - rep[cols]).abs().max() == 0
    rel = (f15[cols] - f30[cols]).abs() / f30[cols].abs().clip(lower=1e-9)
    assert rel.median() < 1e-12 and rel.max() < 0.05


def test_cnn_joins_the_physics_scalars_after_pooling():
    T.configure(xgb_n_jobs=2)
    X, y = toy_xy(cnn=True)
    size = X["Feature Scale_size"].to_numpy()
    Xp = X.assign(**{f"{PHYS_PREFIX}s_h": y / 20, f"{PHYS_PREFIX}P_base": 0.4 * size, f"{PHYS_PREFIX}T_h": 15.0})
    Xp.iloc[5, -3] = np.nan                                                      # a failed net-load fit: imputed inside the model
    fit = lambda X_: (m := T.Model("CNN", NEW["CNN"], 0, {"target_transform": "log"}), m.fit(X_.iloc[:120], y[:120], n_iter=5))[0]   # noqa: E731
    m, m_raw = fit(Xp), fit(X)
    p = m.predict(Xp.iloc[120:])
    assert m.m.net.head[0].in_features == m_raw.m.net.head[0].in_features + 3 and np.isfinite(p).all()
    assert not np.allclose(p, m.predict(Xp.iloc[120:].assign(**{f"{PHYS_PREFIX}s_h": Xp[f"{PHYS_PREFIX}s_h"].iloc[120:] * 3})))   # the scalars are read
    np.testing.assert_array_equal(p, fit(Xp).predict(Xp.iloc[120:]))                # deterministic
    np.testing.assert_array_equal(m.m.p_med, np.nanmedian(Xp.iloc[:120, -3:].to_numpy() / np.c_[size[:120], size[:120], np.ones(120)], axis=0))


# ------------------------------------------------------------------ Task 2: L4 scale models
def scale_pool(seed=0, n_st=8, noise=0.0):
    """Toy substations on `n_st` stations whose m_h depends linearly on the station's design temperature."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_st):
        td = -10 + 10 * s / (n_st - 1)
        for split, fold, n in [("train", -1, 30), *[("inner", k, 10) for k in range(4)], ("test", -1, 10)]:
            for i in range(n):
                pool_hh = [f"st{s}_h{j}" for j in range(40) if (j % 4 == fold if split == "inner" else (j >= 30) == (split == "test"))]
                hh = sorted(rng.choice(pool_hh, 3, replace=False))
                size, cap = int(rng.choice([10, 20, 40])), float(rng.uniform(10, 30))
                m = (0.02 + 0.0008 * (td + 10)) * float(np.exp(rng.normal(0, noise)))
                rows.append({"sub_id": f"{s}|{split}{fold}|{i}", "split": split, "fold": fold, "station": f"st{s}", "size": size, "T_design": td,
                             "HP_Peak": cap, "s_h": m * cap, "s_h_net": m * cap + size * 0.005, "P_base_net": 0.5 * size,
                             "T_h_net": 15 + rng.normal(0, 0.5), "hp_members": hh, "m": m})
    tab = pd.DataFrame(rows).set_index("sub_id")
    clim = pd.DataFrame({"T_mean": rng.uniform(8, 11, n_st), "T_q05": rng.uniform(-3, 1, n_st)}, index=[f"st{s}" for s in range(n_st)])
    return tab, SM.covariates(tab, 0.005, clim, tab["T_design"].to_numpy())


def test_l4b_recovers_a_scale_that_depends_linearly_on_T_design():
    tab, C = scale_pool(noise=0.01)
    m_cf, full, info = SM.crossfit_m(C, tab["m"].to_numpy(), tab, tab[["hp_members"]])
    te = (tab["split"] == "test").to_numpy()
    np.testing.assert_allclose(m_cf[te], tab["m"].to_numpy()[te], rtol=0.03)           # test rows: the g of all train rows
    np.testing.assert_allclose(m_cf[~te], tab["m"].to_numpy()[~te], rtol=0.05)         # cross-fitted rows
    coef = dict(zip(SM.COVARS, full.g[-1].coef_))
    assert coef["T_design"] > 0 and max(coef, key=lambda k: abs(coef[k])) == "T_design" and info["n_cf_fallback"] == 0
    np.testing.assert_allclose(C["s_hat"], tab["m"] * tab["HP_Peak"], rtol=1e-9)        # s_hat = s_h(net) - N s0


def test_crossfitted_scale_never_uses_its_own_fold_or_households(monkeypatch):
    tab, C = scale_pool()
    m, calls, real_fit, real_hat = tab["m"].to_numpy(), [], SM.Scale.fit, SM.Scale.m_hat
    monkeypatch.setattr(SM.Scale, "fit", lambda self, C_, m_: (setattr(self, "rows", set(C_.index)), real_fit(self, C_, m_))[1])
    monkeypatch.setattr(SM.Scale, "m_hat", lambda self, C_: (calls.append((self.rows, list(C_.index))), real_hat(self, C_))[1])
    out, full, info = SM.crossfit_m(C, m, tab, tab[["hp_members"]], alphas=(1.0,))
    split, fold, hh = tab["split"], tab["fold"], tab["hp_members"]
    seen = set()
    for fit_rows, pred in calls:
        if len(pred) == 1 and split[pred[0]] == "train":                          # a train row: no fitted row shares a household with it
            assert all(split[r] == "train" and not set(hh[r]) & set(hh[pred[0]]) for r in fit_rows) and pred[0] not in fit_rows
            seen.add(pred[0])
        elif all(split[r] == "inner" for r in pred):                               # an inner fold: fitted on the other folds only
            k = {fold[r] for r in pred}
            assert len(k) == 1 and all(split[r] == "inner" and fold[r] not in k for r in fit_rows)
            seen |= set(pred)
    assert seen == set(tab.index[split != "test"]) and info["n_cf_fallback"] == 0
    assert full.rows == set(tab.index[split == "train"])                          # test rows: the model of all train rows
    for j in (int(np.flatnonzero(split == "train")[7]), int(np.flatnonzero(split == "inner")[3])):   # a row's own label never reaches its m_hat
        m2 = m.copy()
        m2[j] *= 100
        assert SM.crossfit_m(C, m2, tab, tab[["hp_members"]], alphas=(1.0,))[0][j] == out[j]


def toy_l4(tab, s0=0.004, m_pilot=0.02, t_design=-8.0):
    """toy_pa plus the L4 bases of scale_model.l4_bases (one station "A"; every substation has its own HP households)."""
    members = pd.DataFrame({"hp_members": [[f"{i}_a", f"{i}_b"] for i in tab.index]}, index=tab.index)
    idx = pd.date_range("2023-01-01", "2023-12-31 23:00", freq="h")
    temp = pd.DataFrame({"A": 9 + 9 * np.sin(2 * np.pi * (np.arange(len(idx)) / 8760 - 0.3))}, index=idx)
    num = {"s0": {"paperA_corr": np.full(len(tab), s0)}, "full": {"m": m_pilot, "T_h": 15.0},
           "m_cf": np.where(tab["split"] == "test", m_pilot, m_pilot * 1.05).tolist(), "T_cf": np.full(len(tab), 15.0).tolist()}
    rows, cf, scales, cov, info = SM.l4_bases(tab, members, num, temp, t_design)
    pa = toy_pa(tab, m_pilot)
    pa.update(rows)
    pa["cf"].update(cf)
    return {**pa, "scale": scales, "l4cov": cov}, info


def test_l4_zero_residual_is_s_hat_over_m_hat_and_invalid_is_zero():
    tab, F = toy_tab()
    tab.loc[tab.index[[200, 201]], "s_h_net"] = [0.001, np.nan]                    # corrected slope <= 0 / failed fit: invalid test rows
    pa, info = toy_l4(tab)
    te, C = (tab["split"] == "test").to_numpy(), pa["l4cov"]
    assert info["l4a_kappa"] == pytest.approx(0.02 * (15.0 + 8.0))
    for mode, col in (("l4a", "m_l4a"), ("l4b", "m_l4b")):
        p, valid, _ = pa[SM.BASE[mode]]
        assert (~valid[te]).sum() == 2 and (p[~valid] == 0).all()
        np.testing.assert_array_equal(compose(p, np.zeros(len(p)), valid)[valid], (C["s_hat"] / C[col]).to_numpy()[valid])   # z = 0 -> s_hat / m_hat
        np.testing.assert_array_equal(pa["cf"][SM.BASE[mode]][0][te], p[te])            # test rows: the full model
    np.testing.assert_allclose(C["m_l4a"], 0.02, rtol=1e-12)                        # T_h = pilot T_h -> kappa / (T_h - T_design) = pilot m_h
    np.testing.assert_allclose(C["m_l4a_cf"][~te], 0.021, rtol=1e-12)               # train / inner rows: the cross-fitted pilot
    np.testing.assert_allclose(C["m_l4b"], 0.02, rtol=1e-9)                         # the toy's m_h = s_h / HP_Peak is 0.02 everywhere
    tab2 = tab.copy()                                                               # labels = the cross-fitted base: the residual target is 0
    tab2["HP_Peak"] = np.where(pa["cf"]["paperA_l4a"][1], pa["cf"]["paperA_l4a"][0], tab["HP_Peak"])
    spec = ("Linear", "size", "netfit", "l4a", "log")
    cfg = {**toy_cfg(), "modes": ["l4a"], "residual_models": ["Linear"]}
    out, extra = RB.predictions(cfg, tab2, F, tab2["HP_Peak"], 0, [], lambda m: None, pa, [spec])
    np.testing.assert_allclose(out[spec], pa["paperA_l4a"][0][te], rtol=1e-9)
    assert extra[spec]["n_invalid"] == 2 and (out[spec][~pa["paperA_l4a"][1][te]] == 0).all()


def ladder_run(tmp_path, tab, F, pa, **refit):
    cfg = {**toy_cfg(), "models": ["Lasso", "Ridge"], "residual_models": ["Lasso", "Ridge"], "feature_sets": ["whdd", "netfit"],
           "modes": ["direct", "residual", "l4a", "l4b"], "physics_baselines": [],     # the anchor-only baseline of toy_cfg is never persisted
           "mode_feature_sets": {m: ["netfit"] for m in ("residual", "l4a", "l4b")}, "refit": refit}
    spl = [tuple(s.split("|")) for s in refit["fixed"]] if "fixed" in refit else None
    return RB.predictions(cfg, tab, F, tab["HP_Peak"], 0, [], lambda m: None, pa, spl)


def test_rung_winners_are_persisted_by_inner_cv_and_the_frozen_l4_keeps_its_scale(tmp_path):
    T.configure(xgb_n_jobs=2)
    tab, F = ladder_tab()
    pa, _ = toy_l4(tab)
    te, inn = (tab["split"] == "test").to_numpy(), (tab["split"] == "inner").to_numpy()
    out, extra = ladder_run(tmp_path, tab, F, pa, dir=str(tmp_path), by_rung=True)
    fixed = {}
    assert ("anchor_only_Linear", "size", "-", "direct", "none") in out and sorted(p.name for p in tmp_path.iterdir()) == ["L1", "L2", "L3", "L4"]
    for r in ("L1", "L2", "L3", "L4"):
        d = tmp_path / r / "s0" / "linear"
        m, man = load_model(d)
        spec = tuple(man["spec"].split("|"))
        cv = {s: e["wape_inner"] for s, e in extra.items() if s[0] in ("Lasso", "Ridge") and SM.rung(s) == r}
        assert SM.rung(spec) == r and len(cv) == (4 if r == "L4" else 2) and man["cv_wape"] == min(cv.values()) == cv[spec]   # inner CV, never test
        np.testing.assert_array_equal(pd.read_parquet(d / "pred_refit.parquet")["pred"], out[spec])
        oof = pd.read_parquet(d / "oof_inner.parquet")
        assert set(oof.index) <= set(tab.index[inn]) and (oof["fold"] == tab.loc[oof.index, "fold"]).all()
        assert 100 * (oof["oof"] - oof["y"]).abs().sum() / tab.loc[inn, "HP_Peak"].sum() == pytest.approx(man["cv_wape"])   # the winner's out-of-fold predictions
        assert (d / "scale.joblib").exists() == (r == "L4")
        fixed[man["spec"]] = {"params": man["params"], "best_iter": man["best_iter"]}
    chk = reload_check(tmp_path)                                                 # every persisted winner reloads to its own predictions
    assert len(chk) == 4 and chk["max_rel_diff"].max() < 1e-9 and "error" not in chk
    l4 = next(tuple(s.split("|")) for s in fixed if SM.rung(tuple(s.split("|"))) == "L4")
    tab2, F2 = tab.copy(), F.copy()                                              # "scaled fillers": other slopes; the new pilot has another s0
    tab2["s_h_net"] = tab["s_h_net"] + tab["size"] * 0.003
    F2["nf_all_s_h"] = tab2["s_h_net"]
    pa2, _ = toy_l4(tab2, s0=0.007)
    out2, _ = ladder_run(tmp_path, tab2, F2, pa2, fixed=fixed, frozen_dir=str(tmp_path), by_rung=True)
    d = tmp_path / "L4" / "s0" / "linear"
    scale, (m, man) = joblib.load(d / "scale.joblib"), load_model(d)
    p, valid = scale.base(tab2[te])                                              # the x1.0 scale model and s0 on the scaled test substations
    np.testing.assert_allclose(p[valid], ((tab2["s_h_net"] - tab2["size"] * 0.004)[te] / scale.m_hat(SM.covariates(tab2[te], 0.004, scale.clim, -8.0)))[valid])
    want = compose(p, m.predict(T.feature_matrix(F2, tab2, l4[1], l4[2])[te]), valid)
    np.testing.assert_allclose(out2[(f"{l4[0]}@frozen", *l4[1:])], want, rtol=1e-12)
    assert not np.allclose(want, out2[l4]) and not np.allclose(p, pa2[SM.BASE[l4[3]]][0][te])    # not the refit, not the new base
    kinds = sorted((s[0].split("@")[1] if "@" in s[0] else "refit", SM.rung(s)) for s in out2)
    assert kinds == sorted([(k, r) for k in ("refit", "frozen") for r in ("L1", "L2", "L3", "L4")] + [("update", "L4")])   # the fixed specs; update: L4 only
    # R(i) update row (C7): the frozen residual and the frozen scale model, only s0 replaced by the new arm's (label-free) s0
    z = m.predict(T.feature_matrix(F2, tab2, l4[1], l4[2])[te])
    C_new = SM.covariates(tab2[te], 0.007, scale.clim, -8.0)
    p_new, v_new = SM.estimate(C_new, scale.m_hat(C_new))
    upd = out2[(f"{l4[0]}@update", *l4[1:])]
    np.testing.assert_allclose(upd, compose(p_new, z, v_new), rtol=1e-12)
    assert not np.allclose(upd, want) and not np.allclose(upd, out2[l4])           # neither the fully frozen row nor the refit
    np.testing.assert_array_equal(joblib.load(d / "scale.joblib").s0, scale.s0)      # the saved scale model is not modified
    out3, _ = ladder_run(tmp_path, tab, F, pa, fixed=fixed, frozen_dir=str(tmp_path), by_rung=True)
    for s in map(lambda x: tuple(x.split("|")), fixed):                          # same data: every frozen row is the persisted model's prediction
        np.testing.assert_allclose(out3[(f"{s[0]}@frozen", *s[1:])], out[s], rtol=1e-12)
    np.testing.assert_array_equal(out3[(f"{l4[0]}@update", *l4[1:])], out3[(f"{l4[0]}@frozen", *l4[1:])])   # same s0: update = frozen


def test_oof_predictions_are_out_of_fold():
    rng = np.random.default_rng(0)
    n, g = 80, np.arange(80) % 4
    X = pd.DataFrame(rng.normal(size=(n, 2)), columns=["a", "b"])
    z, p_hat = 0.3 * X["a"].to_numpy() + rng.normal(scale=0.05, size=n), rng.uniform(5, 50, n)
    y = p_hat * np.exp(z)
    _, meta, _ = T.tune_grouped_cv("Ridge", X, z, g, 0, 3, opts={"clip": False}, eval_on=(y, p_hat))
    for f in range(4):
        m = T.Model("Ridge", meta["params"], 0, {"clip": False})
        m.fit(X[g != f], z[g != f])
        np.testing.assert_allclose(meta["oof"][g == f], p_hat[g == f] * np.exp(m.predict(X[g == f])), rtol=1e-10)   # kW, the best trial's folds
    assert 100 * np.abs(meta["oof"] - y).sum() / y.sum() == pytest.approx(meta["cv_wape"])


# ------------------------------------------------------------------ Task 3: L5 ensembles
def gate_data(n=400, seed=0):
    """Two experts: A is right below the 35 % quantile of r_hat and noisy (sd 0.3, 30 % high) above it; B the other way round."""
    rng = np.random.default_rng(seed)
    r, y = rng.uniform(0.01, 0.2, n), rng.uniform(10, 100, n)
    low = r < np.quantile(r, 0.35)
    good, bad = y[:, None] * np.exp(rng.normal(0, 0.01, (n, 2))), y[:, None] * np.exp(rng.normal(0, 0.3, (n, 2))) * [1.3, 0.7]
    return np.where(np.c_[low, ~low], good, bad), y, r, np.arange(n) % 4, low


def test_l5a_is_the_mean_of_its_inputs():
    P = gate_data()[0]
    np.testing.assert_array_equal(EN.average(P), (P[:, 0] + P[:, 1]) / 2)
    np.testing.assert_array_equal(EN.average(pd.DataFrame(P)), P.mean(axis=1))


def test_l5b_gate_finds_the_edge_and_the_weights():
    P, y, r, folds, low = gate_data()
    g = EN.Gate().fit(P, y, r, folds)
    assert len(g.edges) == 1 and g.edges[0] == pytest.approx(np.quantile(r, 0.35))
    np.testing.assert_allclose(g.W[:2], [[1, 0], [0, 1]], atol=0.05)              # per bin: the expert that is right there
    wape = lambda p: 100 * np.abs(p - y).sum() / y.sum()                          # noqa: E731
    assert wape(g.predict(P, r)) < 2 < wape(EN.average(P)) and g.cv_wape < 2
    r_nan = np.where(np.arange(len(r)) < 5, np.nan, r)                             # no r_hat: the weights of all rows
    np.testing.assert_allclose(g.predict(P, r_nan)[:5], P[:5] @ g.W[-1])
    flat = EN.Gate().fit(np.c_[y, 0.7 * y], y, r, folds)                           # nothing to gain from a gate: no edge
    assert len(flat.edges) == 0 and flat.W.shape == (2, 2) and flat.W @ [1, 0.7] == pytest.approx([1, 1])   # proportional experts: NNLS fallback


def test_l5_gate_and_weights_never_see_test_rows(tmp_path):
    P, y, r, folds, _ = gate_data()
    inner, test = [f"i{k}" for k in range(300)], [f"t{k}" for k in range(300, 400)]
    r_hat = pd.Series(r, index=inner + test)

    def write(root, P_test):
        for j, fam in enumerate(("linear", "neural")):
            d = root / fam
            d.mkdir(parents=True)
            pd.DataFrame({"oof": P[:300, j], "y": y[:300], "fold": folds[:300]}, index=inner).to_parquet(d / "oof_inner.parquet")
            pd.DataFrame({"pred": P_test[:, j]}, index=test).to_parquet(d / "pred_refit.parquet")
    write(tmp_path / "a", P[300:])
    write(tmp_path / "b", P[300:] * 5 + 3)                                         # other test predictions
    (Ta, ga, fams), (Tb, gb, _) = EN.l5_seed(tmp_path / "a", r_hat), EN.l5_seed(tmp_path / "b", r_hat.where(r_hat.index.isin(inner), 0.5))
    assert fams == ["linear", "neural"]
    np.testing.assert_array_equal(ga.edges, gb.edges)                              # the gate depends on the inner rows only
    np.testing.assert_array_equal(ga.W, gb.W)
    np.testing.assert_array_equal(Ta["L5a"], P[300:].mean(axis=1))
    np.testing.assert_array_equal(Ta["L5b"], ga.predict(P[300:], r[300:]))
    assert list(Ta.index) == test and EN.Gate.fit.__code__.co_varnames[:5] == ("self", "P", "y", "r", "folds")


# ------------------------------------------------------------------ Task 4: queue wiring
def test_queue_arms_seeds_and_core_budget():
    js = RQ.jobs(QUEUE)
    arms = list(dict.fromkeys(j["arm"] for j in js))
    assert arms == ["a_gb", "a_ch", "s_gb", "r_x05", "r_x15", "r_rep"]
    assert all(sorted({j["seed"] for j in js if j["arm"] == a}) == list(range(10)) for a in arms)
    n = {a: sum(j["arm"] == a for j in js) for a in arms}
    assert n == {"a_gb": 80, "a_ch": 80, "s_gb": 480, "r_x05": 80, "r_x15": 80, "r_rep": 80}
    assert {(j["n"], j["draw"]) for j in js if j["arm"] == "s_gb"} == {(n_, d) for n_ in (32, 62, 100) for d in (0, 1)}
    assert QUEUE["workers"] * QUEUE["threads"] <= 20                              # machine A: 20 physical cores (05b lesson)
    assert {a["name"]: a.get("after") for a in QUEUE["arms"]} == {"a_gb": None, "a_ch": None, "s_gb": None, "r_x05": "a_gb", "r_x15": "a_gb", "r_rep": "a_gb"}
    fams = QUEUE["families"]
    assert {f for f, v in fams.items() if v.get("group") == "tabpfn"} == {"tabpfn_d", "tabpfn_r", "tabpfn_h"}
    for arm in QUEUE["arms"]:                                                     # every arm: the same ladder grid; only a_gb / a_ch persist
        job = next(j for j in js if j["arm"] == arm["name"] and j["family"] == "physics")
        cfg, _ = RQ.job_config(QUEUE, arm, job, 3)
        assert cfg["l4"] and {"paperA_l4a", "paperA_l4b", "paperA_corr_own"} <= set(cfg["paperA"]["estimators"]) and cfg["parallel"]["threads"] == 3
        assert cfg["no_train_wape"] == ["TabPFN"] and cfg["cnn_inits"] == 3
        if arm["name"] == "s_gb":                                               # decision 2026-10-12: anchor size, one feature set per rung
            assert RB.computed_sets(cfg) == ["netfit", "raw", "whdd"] and cfg["anchors"] == ["size"]
        else:
            assert RB.computed_sets(cfg) == ["both", "netfit", "raw"] and cfg["anchors"] == ["size", "size_peak"]
    for name, by in (("a_gb", True), ("a_ch", True), ("s_gb", False)):
        arm = next(a for a in QUEUE["arms"] if a["name"] == name)
        cfg, keep = RQ.job_config(QUEUE, arm, next(j for j in js if j["arm"] == name and j["family"] == "cnn_h"), 3)
        assert bool(cfg.get("refit")) == by and cfg["modes"] == ["l4a", "l4b"] and keep == {"CNN"} and cfg["paperA"]["estimators"] == []
        assert {SM.rung(s) for s in RB.specs(cfg)} == {"L4"} and len(RB.specs(cfg)) == (4 if by else 2)
        if by:
            assert cfg["refit"] == {"dir": f"results/iter06_hybrid_ladder/models/{name}", "by_rung": True}


def test_frozen_specs_come_from_the_rung_winners_manifests(tmp_path):
    specs = {"L1": "TabPFN|size|whdd|direct|log", "L2": "TabPFN|size_peak|both|direct|log", "L3": "TabPFN|size|netfit|residual|log",
             "L4": "TabPFN|size|both|l4b|log"}
    for r, s in specs.items():
        for seed, fam, spec in ((3, "neural", s), (3, "linear", s.replace("TabPFN", "Ridge")), (4, "neural", s)):
            d = tmp_path / r / f"s{seed}" / fam
            d.mkdir(parents=True)
            (d / "manifest.json").write_text(json.dumps({"spec": spec, "family": fam, "params": {"k": seed}, "best_iter": None}))
    q = {**QUEUE, "frozen": {"models_dir": str(tmp_path), "by_rung": True}}
    arm = next(a for a in q["arms"] if a["name"] == "r_x05")
    job = lambda fam, seed=3: {"arm": "r_x05", "seed": seed, "draw": 0, "n": "all", "family": fam, "id": f"r_x05__s{seed}__d0__nall__{fam}"}   # noqa: E731
    for fam, rungs in (("tabpfn_d", ["L1", "L2"]), ("tabpfn_r", ["L3"]), ("tabpfn_h", ["L4"])):
        cfg, keep = RQ.job_config(q, arm, job(fam), 3)
        assert cfg["refit"] == {"fixed": {specs[r]: {"params": {"k": 3}, "best_iter": None} for r in rungs}, "by_rung": True, "frozen_dir": str(tmp_path)}
        assert keep == {"TabPFN", "TabPFN@frozen", "TabPFN@update"} and cfg["pool"]["response_scale"] == {"fill": 0.5}
        assert "paperA_corr_s0unscaled" not in cfg["paperA"]["estimators"]          # a family job has no physics row
    cfg, _ = RQ.job_config(q, arm, job("linear"), 3)
    assert set(cfg["refit"]["fixed"]) == {s.replace("TabPFN", "Ridge") for s in specs.values()}
    cfg, _ = RQ.job_config(q, arm, job("physics"), 3)
    assert "refit" not in cfg and "paperA_corr_s0unscaled" in cfg["paperA"]["estimators"]
    rep = next(a for a in q["arms"] if a["name"] == "r_rep")
    cfg, keep = RQ.job_config(q, rep, {**job("tabpfn_h"), "arm": "r_rep"}, 3)
    assert "frozen_dir" not in cfg["refit"] and keep == {"TabPFN"} and cfg["pool"]["year"] == "2223r3"
    with pytest.raises(ValueError, match="no persisted rung winner"):           # never run without the seed's models
        RQ.job_config(q, arm, job("tabpfn_d", seed=9), 3)
    with pytest.raises(ValueError, match="no persisted rung winner"):
        RQ.job_config(q, arm, job("cnn_d"), 3)


def test_after_blocks_a_family_job_until_its_models_exist(tmp_path, monkeypatch):
    """Arm b (`after: a`): b's linear job of a seed starts only when a's linear job of that seed is done; physics jobs never wait."""
    for k, v in {"TOY_LOG": tmp_path / "calls.log", "TOY_SLEEP": "0", "TOY_FAIL": tmp_path / "fail.txt"}.items():
        monkeypatch.setenv(k, str(v))
    (tmp_path / "fail.txt").write_text("1")
    arm = {"config": "tests/fixtures/toy_queue_arm.yaml", "runner": "toy_queue_runner:run_seed", "seeds": [0, 1], "families": ["physics", "linear"]}
    for workers in (1, 2):
        out = tmp_path / f"w{workers}"
        cfg = {"exp_id": f"toy06_{workers}", "out_dir": str(out), "workers": workers, "threads": 1, "sys_path": [str(ROOT / "tests")],
               "families": {"physics": {}, "linear": {"models": ["Lasso", "Ridge"]}},
               "arms": [{**arm, "name": "a"}, {**arm, "name": "b", "after": "a", "seeds": [0, 1, 2]}]}
        (tmp_path / f"q{workers}.yaml").write_text(yaml.safe_dump(cfg))
        prog = RQ.main(["--config", str(tmp_path / f"q{workers}.yaml")])
        done = {f.stem for f in (out / "jobs").glob("*.done")}
        assert "b__s0__d0__nall__linear" in done and "b__s0__d0__nall__physics" in done and "b__s2__d0__nall__physics" in done
        assert not {"b__s1__d0__nall__linear", "b__s2__d0__nall__linear"} & done    # a's seed 1 failed, a has no seed 2: left waiting
        assert prog["failed"] == 3 and prog["remaining"] == 2                       # failed: a's two seed-1 jobs and b's seed-1 physics job


def test_fixed_params_keep_one_inner_cv_pass_and_no_search():
    T.configure(xgb_n_jobs=2)
    X, y = toy_xy(n=120, cnn=True)
    g = np.arange(120) % 4
    m, meta, _ = T.tune_grouped_cv("CNN", X, y, g, 0, 30, opts={"target_transform": "log"}, eval_on=(y, None), params=NEW["CNN"])
    assert meta["params"] == NEW["CNN"] and meta["n_evals"] == 0 and meta["best_iter"] >= 1 and np.isfinite(meta["oof"]).all()
    assert meta["cv_wape"] == pytest.approx(100 * np.abs(meta["oof"] - y).sum() / y.sum())
    ref = T.Model("CNN", NEW["CNN"], 0, {"target_transform": "log"})                # the final model: those hyperparameters, the CV's epoch count
    ref.fit(X, y, n_iter=meta["best_iter"])
    np.testing.assert_array_equal(m.predict(X), ref.predict(X))


def test_queue_gives_the_cnn_its_05b_hyperparameters_on_the_gb_arms_only():
    P = pd.read_csv(ROOT / QUEUE["fixed_params"]["csv"])
    js = RQ.jobs(QUEUE)
    pick = lambda arm, fam, seed: (next(a for a in QUEUE["arms"] if a["name"] == arm),      # noqa: E731
                                   next(j for j in js if j["arm"] == arm and j["family"] == fam and j["seed"] == seed))
    for arm, fam, seed in (("a_gb", "cnn_d", 3), ("a_gb", "cnn_h", 7), ("s_gb", "cnn_r", 0)):
        cfg, _ = RQ.job_config(QUEUE, *pick(arm, fam, seed), 3)
        row = P[(P["split_seed"] == seed) & (P["queue_family"] == "rawseries")].iloc[0]
        assert row["carried_model"] and cfg["cv"]["fixed_params"] == {"CNN": json.loads(row["params"])}
        assert set(cfg["cv"]["fixed_params"]["CNN"]) == {"width", "kernel", "n_blocks", "dropout", "weight_decay", "lr"}
    for arm, fam in (("a_ch", "cnn_d"), ("a_gb", "tabpfn_h"), ("a_gb", "linear"), ("a_gb", "physics"), ("s_gb", "tabpfn_d")):
        assert "fixed_params" not in RQ.job_config(QUEUE, *pick(arm, fam, 2), 3)[0]["cv"]         # tuned (a_ch) or nothing to tune


def test_probe_jobs_are_jobs_of_the_run():
    probe = yaml.safe_load(open(ROOT / "configs" / "iter06_probe.yaml"))
    ids = {j["id"] for j in RQ.jobs(QUEUE)}
    pj = RQ.jobs(probe)
    assert len(pj) == 8 * (5 + 3) and {j["id"] for j in pj} <= ids and {j["seed"] for j in pj} == {0}
    assert all(probe[k] == QUEUE[k] for k in ("exp_id", "out_dir", "workers", "threads", "families", "frozen", "fixed_params"))
    strip = lambda a: {k: v for k, v in a.items() if k not in ("seeds", "draws")}               # noqa: E731
    assert [strip(a) for a in probe["arms"]] == [strip(a) for a in QUEUE["arms"]]


@pytest.mark.parametrize("models", [["Lasso"], ["TabPFN"], ["CNN"]])
def test_s_gb_runs_anchor_size_and_one_feature_set_per_rung(models):
    """Decision 2026-10-12 (as 05b Arm 1 under A4): S-GB = anchor size; whdd (L1) and netfit (L2-L4); CNN raw and rawphys."""
    cfg = {**load_config("configs/iter06_s_gb.yaml"), "physics_baselines": [], "anchor_only_baselines": {"models": [], "features": []},
           "paperA": {"estimators": []}, "models": models, "residual_models": models}
    specs = [s for s in RB.specs(cfg) if s[0] in models]
    l1, l2 = ("raw", "rawphys") if models == ["CNN"] else ("whdd", "netfit")
    assert sorted((SM.rung(s), s[1], s[2], s[3]) for s in specs) == [("L1", "size", l1, "direct"), ("L2", "size", l2, "direct"),
                                                                      ("L3", "size", l2, "residual"), ("L4", "size", l2, "l4a"), ("L4", "size", l2, "l4b")]
    full = [s for s in RB.specs({**LADDER, "models": models, "residual_models": models}) if s[0] in models]
    assert set(specs) < set(full) and not cfg.get("refit")                        # a subset of A-GB's grid (the n = all point); nothing persisted


def test_no_train_wape_skips_the_train_prediction_only(monkeypatch):
    T.configure(xgb_n_jobs=2)
    tab, F = toy_tab()
    cfg = {**toy_cfg(), "models": ["Lasso", "Ridge"], "residual_models": ["Lasso"], "physics_baselines": [], "anchor_only_baselines": {"models": [], "features": []}}
    seen, real = [], T.Model.predict
    monkeypatch.setattr(T.Model, "predict", lambda self, X: seen.append((self.name, len(X))) or real(self, X))
    ref, e_ref = RB.predictions(cfg, tab, F, tab["HP_Peak"], 0, [], lambda m: None, toy_pa(tab))
    n_ref = sum(n == 120 for name, n in seen if name == "Lasso")                 # 120 train substations
    seen.clear()
    out, extra = RB.predictions({**cfg, "no_train_wape": ["Lasso"]}, tab, F, tab["HP_Peak"], 0, [], lambda m: None, toy_pa(tab))
    assert n_ref == 2 and not any(n == 120 for name, n in seen if name == "Lasso") and sum(n == 120 for name, n in seen if name == "Ridge") == 1
    for s in out:                                                                 # predictions and the inner-CV WAPE are untouched
        np.testing.assert_array_equal(out[s], ref[s])
        if s[0] in ("Lasso", "Ridge"):
            assert extra[s]["wape_inner"] == e_ref[s]["wape_inner"] and np.isnan(extra[s]["wape_train"]) == (s[0] == "Lasso")


# ------------------------------------------------------------------ review decisions of 2026-10-12: B1, B2
def cnn_tab(seed=0):
    """A toy substation table with raw series whose target depends on the series (so that a CNN can learn it)."""
    tab, F = ladder_tab()
    s = (tab["HP_Peak"] / tab["size"]).to_numpy()
    T_ = 8 + 8 * np.sin(np.linspace(0, 2 * np.pi, 10))
    Y = tab["size"].to_numpy()[:, None] * (0.4 + 0.02 * s[:, None] * np.maximum(0, 15 - T_)[None]) + np.random.default_rng(seed).normal(0, 0.05, (len(tab), 10))
    F[raw_columns(10)] = np.c_[Y, np.tile(T_, (len(tab), 1))]
    return tab, F


def test_b1_cnn_keeps_the_best_of_three_initialisations_by_validation_loss(monkeypatch):
    spec = ("CNN", "size", "raw", "direct", "log")
    cfg = {**toy_cfg(), "models": ["CNN"], "residual_models": [], "feature_sets": ["raw"], "model_feature_sets": {"CNN": ["raw"]}, "modes": ["direct"],
           "physics_baselines": [], "anchor_only_baselines": {"models": [], "features": []}, "cv": {"hyperopt": {"max_evals": 2}, "fixed_params": {"CNN": NEW["CNN"]}}}
    tab, F = cnn_tab()
    te, inn = (tab["split"] == "test").to_numpy(), (tab["split"] == "inner").to_numpy()
    seen, real = [], T.Model.predict
    monkeypatch.setattr(T.Model, "predict", lambda self, X: seen.append(set(X.index)) or real(self, X))

    def run(F_):
        seen.clear()
        lines = []
        T.configure(xgb_n_jobs=2, cnn_inits=3)
        try:
            out, extra = RB.predictions(cfg, tab, F_, tab["HP_Peak"], 0, [], lines.append, toy_pa(tab), [spec])
        finally:
            T.configure(xgb_n_jobs=2, cnn_inits=1)
        return out[spec], extra[spec], lines, list(seen)

    p, e, lines, calls = run(F)
    losses = [e[f"init{k}_val_loss"] for k in range(3)]
    assert all(np.isfinite(losses)) and len(set(losses)) == 3 and e["init_chosen"] == int(np.argmin(losses))     # three seeds, the lowest loss kept
    assert all(np.isfinite(e[f"init{k}_test_wape"]) for k in range(3))                                         # diagnostics, written and logged
    assert any("initialisations val_loss" in ln and all(f"{v:.5f}"[:6] in ln for v in losses) for ln in lines)
    first_test = next(i for i, rows in enumerate(calls) if rows & set(tab.index[te]))
    n_val = sum(rows == set(tab.index[inn]) for rows in calls[:first_test])
    assert n_val == 3 and not any(rows & set(tab.index[te]) for rows in calls[:first_test])                    # chosen on the inner rows, before any test row is read
    F2 = F.copy()                                                                                               # sentinel: other test rows, same choice
    F2.loc[te, raw_columns(10)] = 987.0
    p2, e2, _, _ = run(F2)
    assert [e2[f"init{k}_val_loss"] for k in range(3)] == losses and e2["init_chosen"] == e["init_chosen"] and not np.allclose(p2, p)
    p3, e3, _, _ = run(F)                                                                                       # identical seeds, identical choice
    np.testing.assert_array_equal(p3, p)
    assert e3 == e


def test_b1_search_evaluations_train_one_initialisation(monkeypatch):
    X, y = toy_xy(n=120, cnn=True)
    g, made = np.arange(120) % 4, []
    real = T.Model.__init__
    monkeypatch.setattr(T.Model, "__init__", lambda self, name, params, seed, opts=None: made.append(seed) or real(self, name, params, seed, opts))
    T.configure(xgb_n_jobs=2, cnn_inits=3)
    try:
        space = {"width": T.hp.choice("width", [8]), "kernel": T.hp.choice("kernel", [3]), "n_blocks": T.hp.choice("n_blocks", [2]),
                 "dropout": T.hp.uniform("dropout", 0.0, 0.1), "weight_decay": T.hp.uniform("weight_decay", 1e-5, 1e-4), "lr": T.hp.uniform("lr", 2e-3, 3e-3)}
        _, meta, _ = T.tune_grouped_cv("CNN", X, y, g, 5, 2, opts={"target_transform": "log"}, space=space)       # a search (B*): 2 evaluations
        assert made == [5] * 8 + [5, 5 + T.INIT_STEP, 5 + 2 * T.INIT_STEP] and len(meta["inits"]) == 3              # 8 fold fits x 1, final fit x 3
        made.clear()
        T.tune_grouped_cv("CNN", X, y, g, 5, 2, opts={"target_transform": "log"}, params=NEW["CNN"])               # a fixed-params pass: 3 per fold
        assert made == [5, 5 + T.INIT_STEP, 5 + 2 * T.INIT_STEP] * 5
        made.clear()
        T.tune_grouped_cv("Ridge", X.iloc[:, -1:], y, g, 5, 2)                                                     # other models: one model per fit
        assert set(made) == {5}
    finally:
        T.configure(xgb_n_jobs=2, cnn_inits=1)


def toy_queue(tmp_path, name, **fam):
    arm = {"name": "a", "config": "tests/fixtures/toy_queue_arm.yaml", "runner": "toy_queue_runner:run_seed", "seeds": [0, 1], "families": ["physics", "linear"]}
    cfg = {"exp_id": name, "out_dir": str(tmp_path / name), "workers": 1, "threads": 1, "sys_path": [str(ROOT / "tests")],
           "families": {"physics": {}, "linear": {"models": ["Lasso", "Ridge"], **fam}}, "arms": [arm]}
    (tmp_path / f"{name}.yaml").write_text(yaml.safe_dump(cfg))
    return tmp_path / f"{name}.yaml", tmp_path / name / "jobs"


def test_b2_timed_out_job_is_failed_with_reason_and_rerun(tmp_path, monkeypatch):
    for k, v in {"TOY_LOG": tmp_path / "calls.log", "TOY_SLEEP": "3", "TOY_FAIL": tmp_path / "none.txt"}.items():
        monkeypatch.setenv(k, str(v))
    cfg, J = toy_queue(tmp_path, "toy06_timeout", timeout_s=1)
    prog = RQ.main(["--config", str(cfg)])
    assert prog == {**prog, "done": 2, "failed": 2, "remaining": 0}                 # physics has no timeout; both linear jobs ran too long
    txt = (J / "a__s0__d0__nall__linear.failed").read_text()
    assert txt.startswith("reason: timeout") and "TimeoutError: timeout: a__s0__d0__nall__linear ran longer than the 1 s" in txt
    assert RQ.main(["--config", str(cfg)])["failed"] == 2                           # never retried in a loop
    monkeypatch.setenv("TOY_SLEEP", "0")
    prog = RQ.main(["--config", str(cfg), "--retry-failed"])
    assert prog["done"] == 4 and prog["failed"] == 0 and (J / "a__s1__d0__nall__linear.done").exists()


def test_b2_queue_refuses_more_threads_than_physical_cores(tmp_path, monkeypatch):
    import psutil
    monkeypatch.setenv("TOY_LOG", str(tmp_path / "calls.log"))
    cfg, J = toy_queue(tmp_path, "toy06_cores")
    with pytest.raises(SystemExit, match="exceed the .* physical cores"):
        RQ.main(["--config", str(cfg), "--workers", "2", "--threads", str(psutil.cpu_count(logical=False))])
    assert not list(J.glob("*.done"))
    assert QUEUE["workers"] * QUEUE["threads"] <= psutil.cpu_count(logical=False)


# ------------------------------------------------------------------ the report script (rules 1-3 on a fabricated result tree)
def fake_results(root, seeds=range(10)):
    """A result tree with known gaps. GB: L1 30, L2 25, L3 24.6, L4 22 (linear; TabPFN -3; CNN -1), physics paperA_corr 27.
    S (n = 62): L1 40, L2 34, L3 33, L4 28. R degradation: L1 +6, L2 +5.5, L3 +5.5, L4 +1 at both factors, +2 / +2 / +2 / 0 on the
    replication year. Inner-CV WAPE = the level + 1, so the hybrid is TabPFN L4 and the best pure data-driven model TabPFN L2."""
    rng = np.random.default_rng(0)
    lvl, off = {"L1": 30.0, "L2": 25.0, "L3": 24.6, "L4": 22.0}, {"Lasso": 0.0, "TabPFN": -3.0, "CNN": -1.0}
    cfgs = {"L1": ("whdd", "direct"), "L2": ("netfit", "direct"), "L3": ("netfit", "residual"), "L4": ("netfit", "l4b")}
    raw = {"whdd": "raw", "netfit": "rawphys"}

    def rows(seed, method, fs, mode, w, inner=None, **extra):
        base = {"exp_id": "fake", "split_seed": seed, "dataset": "fake", "target": "HP_Peak", "method": method, "anchor": "none" if fs == "-" else "size",
                "feature_set": fs, "mode": mode, "target_transform": "-" if fs == "-" else "log", "n_substations": 100, "n_hp_households": 81, **extra}
        r = [{**base, "cell": c, "metric": "wape", "value": w + k} for k, c in enumerate(["all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"])]
        return r + ([{**base, "cell": "all", "metric": "wape_inner", "value": inner}] if inner is not None else [])

    def arm(shift, phys, kind="", d_rung=None, extra_phys=(), **extra):
        out = []
        for s in seeds:
            e = rng.normal(0, 0.1)
            out += rows(s, "paperA_corr", "-", "-", phys + e, **extra) + rows(s, "slope_base", "-", "-", phys + 2 + e, **extra)
            for m, ph in extra_phys:
                out += rows(s, m, "-", "-", ph + e, **extra)
            for meth, o in off.items():
                for r, (fs, mode) in cfgs.items():
                    w = lvl[r] + o + shift.get(r, 0.0) + e + rng.normal(0, 0.05)
                    f = raw[fs] if meth == "CNN" else fs
                    if kind:                                                # R(i): the refit row and the frozen row (+ L4 update)
                        out += rows(s, meth, f, mode, w - 1, **extra) + rows(s, f"{meth}@frozen", f, mode, w + (d_rung or {}).get(r, 0.0), **extra)
                        out += rows(s, f"{meth}@update", f, mode, w, **extra) if r == "L4" else []
                    else:
                        out += rows(s, meth, f, mode, w + (d_rung or {}).get(r, 0.0), None if d_rung else w + 1, **extra)
        return pd.DataFrame(out)

    for name, M in {"a_gb": arm({}, 27.0), "a_ch": arm({r: 4.0 for r in lvl}, 24.0),
                    "r_x05": arm({}, 30.0, "x", {"L1": 6, "L2": 5.5, "L3": 5.5, "L4": 1}, [("paperA_corr_s0unscaled", 33.0)]),
                    "r_x15": arm({}, 30.0, "x", {"L1": 6, "L2": 5.5, "L3": 5.5, "L4": 1}, [("paperA_corr_s0unscaled", 33.0)]),
                    "r_rep": arm({}, 28.0, "", {"L1": 2, "L2": 2, "L3": 2, "L4": 0})}.items():
        (root / name).mkdir(parents=True)
        M.to_csv(root / name / "metrics.csv", index=False)
    lc = pd.concat([arm({"L1": 10 * k, "L2": 9 * k, "L3": 8.4 * k, "L4": 6 * k}, 27.0 + 3 * k, n_train_hp=n, lc_draw=d, spc_train=-1)
                    for n, k in ((32, 1.6), (62, 1.0), (100, 0.6)) for d in (0, 1)])
    (root / "s_gb").mkdir()
    lc.to_csv(root / "s_gb" / "metrics_lc.csv", index=False)
    pd.DataFrame([{"split_seed": s, "n": "main", "pilot": p, "n_hh": 293, "l4b_alpha": 1e4, "l4b_cv_mse": 0.05, "n_cf_fallback": 0, "l4a_kappa": 0.4}
                  for s in seeds for p in ("all", "l4")]).to_csv(root / "a_gb" / "pilots.csv", index=False)


def test_report_applies_the_preregistered_rules(tmp_path):
    from paperb import iter06_report as RP
    fake_results(tmp_path)
    R = RP.main(tmp_path)
    st = R["steps"].set_index(["reading", "family", "step"])["verdict"]
    for fam in ("linear", "tabpfn", "cnn"):
        assert st["A-GB all", fam, "L2 vs L1"] == "better" and st["A-GB all", fam, "L3 vs L2"] == "no difference" and st["A-GB all", fam, "L4 vs L3"] == "better"
        assert st["S-GB n=62", fam, "L4 vs L3"] == "better" and st["R x0.5", fam, "L4 vs L3"] == "better" and st["R x0.5", fam, "L3 vs L2"] == "no difference"
        assert st["R (combined)", fam, "L4 vs L3"] == "better" and st["R (combined)", fam, "L2 vs L1"] == "no difference"     # -0.5 pp at the factors, 0 on the replication year
    n = R["steps"].set_index(["reading", "family", "step"])["n"]
    assert n["A-GB all", "linear", "L2 vs L1"] == 10 and n["S-GB n=62", "linear", "L2 vs L1"] == 20                          # units: seeds; seed x draws on S
    c = R["claim"].iloc[0]
    assert c["hybrid"] == "tabpfn L4" and c["best_pure_dd"] == "tabpfn L2" and bool(c["a_holds"]) and c["A_gap_pp"] == pytest.approx(-3, abs=0.3)
    assert c["S_n62"] == "better" and c["R"] == "better" and c["outcome"] == "holds regardless of T" and c["T"] == "pending 07"
    assert R["claim"].iloc[1]["hybrid"] == "tabpfn L4" and R["claim"].iloc[1]["families"] == "linear+tabpfn" and not R["claim"]["cnn_dependent"].any()
    assert not R["summary"]["cnn_dependent"].any()
    assert R["T"]["R x0.5"]["linear", "L4"].median() == pytest.approx(1.0, abs=0.2) and R["T"]["R x0.5 update"]["linear", "L4"].median() == pytest.approx(0.0, abs=0.2)
    assert R["Z"]["R x0.5"].name == "paperA_corr_s0unscaled" and R["Z"]["R x0.5"].median() == pytest.approx(6.0, abs=0.3)
    assert R["Z"]["A-GB all"].name == "paperA_corr" and R["T"]["S-GB n=all"]["tabpfn", "L1"].median() == pytest.approx(27.0, abs=0.3)
    assert set(R["n_star"]["rung"]) == {"L1", "L2", "L3", "L4"} and len(R["l5"]) == 0                                       # no persisted model: L5 is missing, not invented
    txt = (tmp_path / "report" / "report.md").read_text(encoding="utf-8")
    assert "inherited hyperparameters" in txt and "differs from axis A" in txt and "outside the rules" in txt and "_missing_" in txt
    assert (tmp_path / "report" / "figures" / "wape_vs_rung.png").exists() and (tmp_path / "report" / "figures" / "learning_curves.pdf").exists()
    assert RP.verdict([-2] * 8 + [1] * 2)["verdict"] == "better" and RP.verdict([-2] * 7 + [1] * 3)["verdict"] == "no difference"
    assert RP.verdict([-0.5] * 10)["verdict"] == "no difference" and RP.verdict([2] * 9 + [-1])["verdict"] == "worse"
    assert RP.combine_r(["better", "better", "no difference"]) == "better" and RP.combine_r(["better", "better", "worse"]) == "no difference"


def test_report_winner_is_chosen_by_inner_cv_never_by_test(tmp_path):
    from paperb import iter06_report as RP
    base = {"exp_id": "f", "dataset": "f", "target": "HP_Peak", "anchor": "size", "mode": "direct", "target_transform": "log", "n_substations": 9, "n_hp_households": 9, "cell": "all"}
    M = pd.DataFrame([{**base, "split_seed": 0, "method": "Lasso", "feature_set": fs, "metric": k, "value": v}
                      for fs, test, inner in (("netfit", 10.0, 30.0), ("both", 50.0, 20.0)) for k, v in (("wape", test), ("wape_inner", inner))])
    w = RP.winners(RP.wide(M, ["split_seed"]), ["split_seed"])
    assert len(w) == 1 and w["feature_set"].iloc[0] == "both" and w["all"].iloc[0] == 50.0 and w["rung"].iloc[0] == "L2"
