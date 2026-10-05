"""Iteration 05b (Task 1f): oracle sentinel, learning-curve fit, train / inner / test WAPE on disjoint sets, Arm 7 response
scaling, pilot cache, inner-CV-only family selection, the new models (round trip, seeds, fold-only preprocessing, residual
composition), TabPFN checkpoint and secrets, `paperA_corr_own` on a toy pool, learning-curve queue jobs. Tests that need the pool
caches or the TabPFN checkpoint are skipped without them."""
import copy
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from paperb import load_config  # noqa: E402
from paperb import lc_fit as LC  # noqa: E402
from paperb import oracle as OR  # noqa: E402
from paperb import physics as PH  # noqa: E402
from paperb import run_benchmark as RB  # noqa: E402
from paperb import run_queue as RQ  # noqa: E402
from paperb import train as T  # noqa: E402
from paperb.models_rawseries import raw_columns  # noqa: E402
from paperb.residual import compose  # noqa: E402

POOLS = ROOT / "data" / "_paperb" / "pools"
needs_bstar = pytest.mark.skipif(not (POOLS / "bstar_2023_meta.parquet").exists(), reason="B* pool cache not built")
needs_lcl = pytest.mark.skipif(not (POOLS / "lcl_std_20120701_20140228_heathrow.npy").exists(), reason="LCL cache not built")
needs_tabpfn = pytest.mark.skipif(not (Path(os.environ.get("TABPFN_MODEL_CACHE_DIR", "-")) / T.TABPFN_CHECKPOINT).is_file(),
                                  reason="TabPFN checkpoint not in TABPFN_MODEL_CACHE_DIR")
NEW = {"KernelRidge": {"alpha": 1.0, "gamma": 0.1, "kernel": "rbf"}, "GP": {},
       "RandomForest": {"n_estimators": 50, "max_features": 0.5, "min_samples_leaf": 2, "max_depth": None},
       "ExtraTrees": {"n_estimators": 50, "max_features": 0.5, "min_samples_leaf": 2, "max_depth": 6},
       "CatBoost": {"depth": 4, "learning_rate": 0.1, "l2_leaf_reg": 3.0, "iterations": 100},
       "TabPFN": {}, "CNN": {"width": 8, "kernel": 3, "n_blocks": 2, "dropout": 0.1, "weight_decay": 1e-4, "lr": 3e-3}}


def toy_xy(n=160, seed=0, cnn=False):
    rng = np.random.default_rng(seed)
    size = rng.choice([10, 20, 40], n).astype(float)
    if cnn:
        T_ = 8 + 8 * np.sin(np.linspace(0, 2 * np.pi, 30))
        s = rng.uniform(0.01, 0.1, n)
        Y = size[:, None] * (0.4 + s[:, None] * np.maximum(0, 15 - T_)[None]) + rng.normal(0, 0.1, (n, 30))
        X = pd.DataFrame(np.c_[Y, np.tile(T_, (n, 1))], columns=raw_columns(30)).assign(**{"Feature Scale_size": size})
        y = size * s * 20
    else:
        X = pd.DataFrame(rng.normal(size=(n, 6)), columns=[f"nf_{i}" for i in range(6)]).assign(**{"Feature Scale_size": size})
        y = size * np.exp(0.3 * X["nf_0"] + 0.1 * np.sin(X["nf_1"]))
    X.iloc[3, 0] = np.nan                                                    # one missing value: imputation inside the model
    return X, np.asarray(y, float)


def skip_tabpfn(name):
    if name == "TabPFN" and not (Path(os.environ.get("TABPFN_MODEL_CACHE_DIR", "-")) / T.TABPFN_CHECKPOINT).is_file():
        pytest.skip("TabPFN checkpoint missing")


# ------------------------------------------------------------------ new models (Task 1e)
@pytest.mark.parametrize("name", list(NEW))
def test_new_model_round_trip_seeds_and_fold_only_preprocessing(name):
    skip_tabpfn(name)
    T.configure(xgb_n_jobs=2)
    X, y = toy_xy(cnn=name == "CNN")
    tr, te = np.arange(120), np.arange(120, 160)
    fit = lambda seed: T.Model(name, NEW[name], seed, {"target_transform": "log"})   # noqa: E731
    m1, m2 = fit(0), fit(0)
    m1.fit(X.iloc[tr], y[tr])
    m2.fit(X.iloc[tr], y[tr])
    p1 = m1.predict(X.iloc[te])
    np.testing.assert_array_equal(p1, m2.predict(X.iloc[te]))                     # identical seeds -> identical output
    assert p1.shape == (40,) and np.isfinite(p1).all() and (p1 > 0).all()
    Xs = X.iloc[te].copy()
    Xs.iloc[1:] = 1e6                                                              # leakage sentinel: other test rows are wild
    assert m1.predict(Xs)[0] == pytest.approx(p1[0], rel=1e-6)                     # a test row's prediction ignores other test rows
    if name == "CNN":                                                              # preprocessing statistics = training rows only
        S = np.stack([X.iloc[tr].filter(like="rs_y_").to_numpy() / X.iloc[tr][["Feature Scale_size"]].to_numpy(),
                      X.iloc[tr].filter(like="rs_T_").to_numpy()], axis=1)
        np.testing.assert_allclose(m1.m.med, np.nanmedian(S, axis=0))
    else:
        np.testing.assert_allclose(m1.imp.statistics_, np.nanmedian(X.iloc[tr].to_numpy(), axis=0))
        np.testing.assert_allclose(m1.xs.mean_, m1.imp.transform(X.iloc[tr]).mean(axis=0))


@pytest.mark.parametrize("name", list(NEW))
def test_new_model_zero_residual_reproduces_paperA(name):
    skip_tabpfn(name)
    X, _ = toy_xy(cnn=name == "CNN")
    m = T.Model(name, NEW[name], 0, {"clip": False})
    m.fit(X.iloc[:120], np.zeros(120))
    z = m.predict(X.iloc[120:])
    assert np.abs(z).max() < (5e-2 if name == "CNN" else 1e-6)
    p_hat, valid = np.linspace(5, 50, 40), np.r_[np.ones(39, bool), False]
    np.testing.assert_array_equal(compose(p_hat, np.zeros(40), valid), np.r_[p_hat[:39], 0.0])   # z = 0 -> P_hat_A, invalid -> 0
    np.testing.assert_allclose(compose(p_hat, z, valid)[:39], p_hat[:39], rtol=0.06)


def test_cv_folds_never_see_the_scored_fold(monkeypatch):
    """Grouped CV of an iterative and a non-iterative new model: every fit inside the CV gets rows of the other folds only."""
    X, y = toy_xy(n=200)
    X.index = [f"r{i}" for i in range(200)]
    groups = np.arange(200) % 4
    seen, real = [], T.Model.fit
    monkeypatch.setattr(T.Model, "fit", lambda self, X_, y_, *a, **k: seen.append(set(X_.index)) or real(self, X_, y_, *a, **k))
    fold = {i: set(X.index[groups == i]) for i in range(4)}
    for name in ("CatBoost", "RandomForest"):
        seen.clear()
        T.tune_grouped_cv(name, X, np.log(y), groups, 0, max_evals=2, X_final=X.iloc[:10], y_final=np.log(y[:10]))
        cv_fits = seen[:-1]                                                        # the last fit is the final refit on X_final
        assert cv_fits and all(any(not (s & fold[k]) for k in range(4)) for s in cv_fits)
        assert all(s == set().union(*(fold[k] for k in range(4) if s & fold[k])) for s in cv_fits)   # whole folds only


# ------------------------------------------------------------------ bias-variance columns and oracle sentinel (Tasks 1b, 1c)
def toy_tab(seed=0):
    rng = np.random.default_rng(seed)
    n = 240
    split = np.array(["train"] * 120 + ["inner"] * 80 + ["test"] * 40)
    size = rng.choice([10, 20, 40], n)
    p = rng.choice([0.1, 0.5], n)
    nhp = np.maximum(1, np.round(p * size)).astype(int)
    cap = rng.uniform(4, 8, n) * nhp
    s_net = cap * 0.02 + size * 0.005 + rng.normal(0, 0.02, n)
    tab = pd.DataFrame({"split": split, "fold": np.where(split == "inner", np.arange(n) % 4, -1), "station": "A", "size": size, "p": p,
                        "HP_Count": nhp, "HP_Peak": cap, "peak": cap + size * 0.8, "s_h_net": s_net, "P_base_net": size * 0.5,
                        "T_h_net": 15.0, "delta_net": s_net * 20, "hdh_slope_net": s_net / 24,
                        "s_h": cap * 0.02, "T_h_hp": 15.0, "hinge_inside_hp": True, "P_base_nonhp": size * 0.5, "r": 0.1},
                       index=[f"s{i}" for i in range(n)])
    F = pd.DataFrame({"nf_all_s_h": s_net, "nf_all_P_base": size * 0.5, "nf_noise": rng.normal(size=n)}, index=tab.index)
    return tab, F


def toy_cfg():
    return {"cv": {"hyperopt": {"max_evals": 2}}, "paperA": {"target": "HP_Peak"}, "physics_baselines": ["slope_base", "hdh"],
            "models": ["Lasso", "RandomForest"], "residual_models": ["Lasso"], "anchors": ["size"], "feature_sets": ["netfit"],
            "modes": ["direct", "residual"], "target_transforms": ["log"], "anchor_only_baselines": {"models": ["Linear"], "features": [["size"]]}}


def toy_pa(tab, m=0.02):
    p, v = PH.paperA_estimate(tab["s_h_net"], m)
    return {"paperA_sh_mh": (p, v, np.zeros(len(tab), bool)), "cf": {"paperA_sh_mh": (p, v)}}


def test_train_inner_test_wape_on_disjoint_sets():
    T.configure(xgb_n_jobs=2)
    tab, F = toy_tab()
    out, extra = RB.predictions(toy_cfg(), tab, F, tab["HP_Peak"], 0, [], lambda m: None, toy_pa(tab))
    ml = [s for s in out if s[0] in ("Lasso", "RandomForest", "anchor_only_Linear")]
    assert len(ml) == 4
    for s in ml:
        e = extra[s]
        assert e["n_overlap_sub"] == 0 and e["n_test_sub"] == 40 and e["n_inner_sub"] == 80 and e["n_train_sub"] == 120
        assert np.isfinite(e["wape_train"]) and np.isfinite(e["wape_inner"])
    lin = T.tune_grouped_cv("Lasso", T.feature_matrix(F, tab, "size", "netfit")[tab["split"].eq("inner").to_numpy()],
                            tab.loc[tab["split"].eq("inner"), "HP_Peak"].to_numpy(), tab.loc[tab["split"].eq("inner"), "fold"], 0, 2,
                            T.feature_matrix(F, tab, "size", "netfit")[tab["split"].eq("train").to_numpy()],
                            tab.loc[tab["split"].eq("train"), "HP_Peak"].to_numpy(), {"target_transform": "log"})[0]
    y_tr = tab.loc[tab["split"].eq("train"), "HP_Peak"].to_numpy()
    p_tr = lin.predict(T.feature_matrix(F, tab, "size", "netfit")[tab["split"].eq("train").to_numpy()])
    assert extra[("Lasso", "size", "netfit", "direct", "log")]["wape_train"] == pytest.approx(100 * np.abs(p_tr - y_tr).sum() / y_tr.sum())


def test_oracle_columns_never_reach_non_oracle_rows():
    """Sentinel: replacing every label-side column (HP-aggregate fits, own m_h) changes the oracle rows and nothing else."""
    T.configure(xgb_n_jobs=2)
    tab, F = toy_tab()
    run = lambda t: RB.predictions(toy_cfg(), t, F, t["HP_Peak"], 0, [], lambda m: None, toy_pa(t))[0]   # noqa: E731
    a = run(tab)
    sent = tab.assign(s_h=1e6, T_h_hp=-99.0, hinge_inside_hp=False, P_base_nonhp=1e6, r=1e6)
    b = run(sent)
    assert a.keys() == b.keys()
    for s in a:
        np.testing.assert_array_equal(a[s], b[s])
    te = tab["split"].eq("test")
    o_a = OR.oracle_predictions(tab[te], 0.02, pd.Series(0.02, index=tab.index[te]))
    o_b = OR.oracle_predictions(sent[te], 0.02, pd.Series(0.02, index=tab.index[te]))
    assert not np.allclose(o_a["oracle_O1"][0], o_b["oracle_O1"][0])
    assert not any(k.startswith("oracle_") for k in (s[0] for s in RB.specs({**toy_cfg(), "oracle_rows": True})))


# ------------------------------------------------------------------ learning-curve fit and family selection (Task 1a)
@pytest.mark.parametrize("a,b,c", [(20.0, 80.0, 0.5), (12.0, 300.0, 1.2), (30.0, 40.0, 0.3)])
def test_lc_fit_recovers_known_curve(a, b, c):
    n = np.array([16, 32, 62, 100, 200, 293.0])
    f = LC.fit_curve(n, LC.power_law(n, a, b, c))
    assert (f["a"], f["b"], f["c"]) == pytest.approx((a, b, c), rel=1e-3)
    assert not f["flag_c_bound"] and not f["flag_a_neg"]
    w = LC.power_law(n, a, b, c) + np.random.default_rng(1).normal(0, 0.05, len(n))
    assert LC.fit_curve(n, w)["a"] == pytest.approx(a, abs=1.5)
    assert LC.n_star(a, b, c, a + b * 50 ** -c) == pytest.approx(50)
    assert LC.n_star(a, b, c, a - 1) == np.inf


def test_lc_fit_flags_bounds_and_negative_asymptote():
    n = np.array([16, 32, 62, 100, 200, 293.0])
    assert LC.fit_curve(n, 50 - 0.01 * n)["flag_c_bound"]                       # no power-law decay: c runs to a bound
    assert LC.fit_curve(n, LC.power_law(n, -5.0, 100.0, 0.4))["flag_a_neg"]


def test_family_winner_uses_inner_cv_only():
    rng = np.random.default_rng(0)
    cand = pd.DataFrame([{"split_seed": s, "method": m, "anchor": a, "feature_set": "netfit", "mode": "direct", "target_transform": "log",
                          "wape_inner": rng.uniform(10, 30), "wape": rng.uniform(10, 30)}
                         for s in range(3) for m in ("Lasso", "Ridge", "XGBoost", "CatBoost", "CNN") for a in ("size", "size_peak")])
    w1 = LC.family_winners(cand, ["split_seed"])
    w2 = LC.family_winners(cand.assign(wape=-cand["wape"] * 1e3), ["split_seed"])          # sentinel: scramble the test column
    pd.testing.assert_frame_equal(w1.drop(columns="wape"), w2.drop(columns="wape"))
    best = cand.assign(family=cand["method"].map(LC.FAMILY_OF)).groupby(["split_seed", "family"])["wape_inner"].min()
    np.testing.assert_allclose(w1.set_index(["split_seed", "family"])["wape_inner"].sort_index(), best.sort_index())
    assert set(w1["family"]) == {"linear", "trees", "rawseries"}


# ------------------------------------------------------------------ Arm 7 / A7 response scaling (Task 1c)
def test_scaled_fillers_scale_s0_and_keep_P_base_synthetic():
    rng = np.random.default_rng(0)
    days = 365
    T_d = 10 + 9 * np.sin(2 * np.pi * (np.arange(days) - 110) / 365) + rng.normal(0, 2, days)
    L = [np.outer(0.3 + rng.uniform(0, 0.03) * np.maximum(0, rng.uniform(13, 17) - T_d) + rng.normal(0, 0.05, days), rng.uniform(0.5, 1.5, 48))
         for _ in range(200)]
    agg = lambda Ls: PH.fit_daily(T_d, np.sum([x.mean(axis=1) for x in Ls], axis=0))                  # noqa: E731
    f1 = agg(L)
    for k in (0.5, 1.5, 0.0):
        fk = agg([OR.scale_days(x, T_d, k)[0] for x in L])
        assert fk["s_h"] == pytest.approx(k * f1["s_h"], rel=0.02, abs=0.02 * f1["s_h"])
        assert fk["P_base"] == pytest.approx(f1["P_base"], rel=0.01)
    x0 = OR.scale_days(L[0], T_d, 0.5)[0]
    warm = T_d > 20.5
    np.testing.assert_allclose(x0[warm], L[0][warm])                              # days above every T_h are unchanged


@needs_lcl
def test_scaled_lcl_fillers_scale_s0_and_keep_P_base_real():
    """Real LCL fillers (400 random flat-rate households, Heathrow T): the aggregate's s0 scales by the factor within 2 %, P_base within 1 %."""
    from paperb.fill_analog import build_lcl
    cfg = load_config("configs/pool_gb_eoh_2122.yaml")
    S, D, _, _ = build_lcl(cfg["pool"]["fill"], verbose=False)
    idx = np.sort(np.random.default_rng(0).choice(S.shape[0], 400, replace=False))
    T_d = D["T"].to_numpy()
    base = [np.asarray(S[j], np.float64) for j in idx]
    agg = lambda Ls: PH.fit_daily(T_d, np.sum([x.mean(axis=1) for x in Ls], axis=0))                  # noqa: E731
    f1 = agg(base)
    for k in (0.5, 1.5):
        fk = agg([OR.scale_days(x, T_d, k)[0] for x in base])
        assert fk["s_h"] / f1["s_h"] == pytest.approx(k, rel=0.02)
        assert fk["P_base"] == pytest.approx(f1["P_base"], rel=0.01)


# ------------------------------------------------------------------ paperA_corr_own (A7)
def toy_pool(k=0.02, s0=0.0, m=0.03, cap=6.0, n_hp=8, n_fill=40, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", "2023-12-31 23:00", freq="h")
    day = np.arange(len(idx)) // 24
    T_ = pd.Series(8 + 11 * np.sin(2 * np.pi * (day - 110) / 365) + np.repeat(rng.normal(0, 2, 365), 24), index=idx)
    heat = np.maximum(0, 15 - T_.to_numpy())
    hp = pd.DataFrame({f"h{i}": cap * m * heat for i in range(n_hp)}, index=idx)
    own = pd.DataFrame({f"h{i}": 0.3 + k * heat for i in range(n_hp)}, index=idx)
    fill = pd.DataFrame({f"f{i}": 0.4 + s0 * heat for i in range(n_fill)}, index=idx)
    meta = pd.DataFrame({"station": "A", "hp_peak": cap}, index=list(hp.columns) + list(fill.columns))
    return SimpleNamespace(hp=hp, own=own, fill=fill, temp=pd.DataFrame({"A": T_}), meta=meta, index=idx, analog=None)


@pytest.mark.parametrize("k,s0", [(0.02, 0.0), (0.03, 0.006)])
def test_paperA_corr_own_recovers_capacity_and_corr_is_biased(k, s0):
    m, cap = 0.03, 6.0
    pool = toy_pool(k=k, s0=s0, m=m, cap=cap)
    caps = pool.meta.loc[pool.hp.columns, "hp_peak"]
    pilot_hh = ["h0", "h1", "h2", "h3", "h4"]
    s0_hat = PH.household_sensitivity(pool, list(pool.fill.columns), fill_station="A")["s0"]
    m_h = PH.pool_pilot(pool, pilot_hh, caps)["m"]
    m_own = PH.pilot_whole(pool, pilot_hh, caps, {h: s0_hat for h in pilot_hh})["m"]
    sub_hp, sub_fill = ["h5", "h6", "h7"], [f"f{i}" for i in range(7)]               # 3 HP homes (+ their own load) + 7 fillers
    net = pool.hp[sub_hp].sum(axis=1) + pool.own[sub_hp].sum(axis=1) + pool.fill[sub_fill].sum(axis=1)
    s_h = PH.fit_daily(*PH.daily_means(pool.temp["A"], net))["s_h"]
    truth = 3 * cap
    p_own = PH.paperA_corrected([s_h], [10], s0_hat, m_own)[0][0]
    p_corr = PH.paperA_corrected([s_h], [10], s0_hat, m_h)[0][0]
    assert m_h == pytest.approx(m, rel=1e-3)
    assert p_own == pytest.approx(truth, rel=0.01)
    assert p_corr - truth == pytest.approx(3 * (k - s0) / m_h, rel=0.02)        # k / m_h per HP home (net of the fillers' s0)


# ------------------------------------------------------------------ pilot cache (A4)
@needs_bstar
def test_cached_pilot_equals_fresh(tmp_path):
    cfg = copy.deepcopy(load_config("configs/iter03b_quick.yaml"))
    cfg.update(models=[], residual_models=[], modes=["direct"], physics_baselines=[], anchor_only_baselines={"models": [], "features": []},
               learning_curve=None, pilot_cache_dir=str(tmp_path))
    cfg["paperA"].update(estimators=["paperA_sh_mh", "paperA_corr", "paperA_corr_cal", "paperA_corr_own"], cap_def_check=False)
    cfg["parallel"]["threads"] = 4
    fresh = RB.run_seed({**cfg, "pilot_cache": False}, 0)
    first = RB.run_seed(cfg, 0)
    assert len(list(tmp_path.glob("*.json"))) == 1
    cached = RB.run_seed(cfg, 0)
    for r in (first, cached):
        pd.testing.assert_frame_equal(r["pilots"], fresh["pilots"], check_dtype=False)
        pd.testing.assert_frame_equal(r["preds"].reset_index(drop=True), fresh["preds"].reset_index(drop=True))
    assert "paperA_corr_own" in set(fresh["preds"]["method"]) and (fresh["pilots"]["pilot"] == "own").sum() == 1


@needs_bstar
def test_lc_only_job_returns_lc_rows_without_preds(tmp_path):
    """A queue learning-curve job (lc_only) scores only the n-design; it has no full-split predictions and must not fail on them."""
    cfg = copy.deepcopy(load_config("configs/iter03b_quick.yaml"))
    cfg.update(models=[], residual_models=[], modes=["direct"], physics_baselines=[], anchor_only_baselines={"models": [], "features": []},
               pilot_cache_dir=str(tmp_path), lc_only=True)
    cfg["learning_curve"].update(n=[16], draws=1, draw_ids=[0], specs=["paperA_sh_mh|none|-|-|-"])
    cfg["paperA"].update(estimators=["paperA_sh_mh"], cap_def_check=False)
    cfg["parallel"]["threads"] = 4
    res = RB.run_seed(cfg, 0)
    assert res["preds"].empty and res["metrics"].empty
    assert len(res["lc"]) and set(res["lc"]["n_train_hp"]) == {16} and set(res["lc"]["method"]) == {"paperA_sh_mh"}


# ------------------------------------------------------------------ TabPFN (Task 1e) and secrets
@needs_tabpfn
def test_tabpfn_is_the_local_v35_checkpoint_with_recorded_hash():
    from tabpfn.constants import ModelVersion
    from tabpfn.model_loading import resolve_model_version
    m = T.tabpfn_regressor(0)
    assert Path(m.model_path).name == T.TABPFN_CHECKPOINT and Path(m.model_path) == T.tabpfn_checkpoint()
    assert resolve_model_version(m.model_path) == ModelVersion.V3_5
    info = T.tabpfn_info()
    assert info["checkpoint"] == T.TABPFN_CHECKPOINT and re.fullmatch(r"[0-9a-f]{64}", info["sha256"]) and info["package"] >= "9.0.0"
    for f in (ROOT / "results" / "iter05b_data_limit").rglob("config.yaml"):                  # every recorded hash is this file's
        c = yaml.safe_load(f.read_text(encoding="utf-8"))
        q, arm = c.get("queue") or {}, f.parent.name                  # an arm with TabPFN jobs must record it; physics-only arms need not
        runs = any("TabPFN" in q["families"][fam].get("models", []) + q["families"][fam].get("residual_models", [])
                   for a in q.get("arms", []) if a["name"] == arm for fam in a["families"])
        if runs or "tabpfn" in c:
            assert c["tabpfn"]["sha256"] == info["sha256"], f


def test_no_token_in_outputs_or_tracked_files():
    tokens = [v for k in ("HF_TOKEN", "TABPFN_TOKEN", "HUGGING_FACE_HUB_TOKEN") if (v := os.environ.get(k))]
    pat = re.compile(r"hf_[A-Za-z0-9]{30,}")
    roots = [ROOT / "results" / "iter05b_data_limit", ROOT / "configs", ROOT / "scripts", ROOT / "tests"]
    for f in (f for r in roots if r.exists() for f in r.rglob("*") if f.is_file() and f.suffix in (".csv", ".txt", ".md", ".yaml", ".json", ".py", ".log")):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        assert not pat.search(txt), f
        assert not any(t in txt for t in tokens), f
    assert ".env" in (ROOT / ".gitignore").read_text().split()


# ------------------------------------------------------------------ queue: learning-curve jobs
def test_queue_learning_curve_jobs():
    q = {"families": {"physics": {}, "linear": {"models": ["Lasso"], "residual_models": ["Lasso"]}},
         "arms": [{"name": "a", "config": "configs/iter05b_arm1.yaml", "seeds": [0, 1], "n": [16, "all"], "draws": [0, 1], "families": ["physics", "linear"]}]}
    js = RQ.jobs(q)
    assert len(js) == 2 * 2 * (2 + 1) and all(j["draw"] == 0 for j in js if j["n"] == "all")
    cfg, fam = RQ.job_config(q, q["arms"][0], next(j for j in js if j["n"] == 16 and j["draw"] == 1 and j["family"] == "linear"), 2)
    assert cfg["lc_only"] and cfg["learning_curve"]["n"] == [16] and cfg["learning_curve"]["draw_ids"] == [1] and cfg["learning_curve"]["specs"] == "all"
    assert {s[0] for s in RB.specs(cfg)} == {"Lasso", "paperA_sh_mh"} and fam == {"Lasso"}      # paperA_sh_mh: residual base, dropped by keep_family
    cfg_p, _ = RQ.job_config(q, q["arms"][0], next(j for j in js if j["n"] == "all" and j["family"] == "physics"), 2)
    assert not cfg_p.get("lc_only") and "paperA_corr_own" in cfg_p["paperA"]["estimators"]


def test_cnn_reads_raw_only_and_others_never_read_raw():
    cfg = load_config("configs/iter05b_arm2.yaml")
    cfg.update(models=["Lasso", "CNN"], residual_models=["Lasso", "CNN"])
    sp = RB.specs(cfg)
    assert {s[2] for s in sp if s[0] == "CNN"} == {"raw"} and "raw" not in {s[2] for s in sp if s[0] == "Lasso"}
    assert len([s for s in sp if s[0] == "CNN"]) == 2 * 2                         # anchors {size, size_peak} x {direct-log, residual}


# ------------------------------------------------------------------ timing probe and runtime estimate (Task 2)
def test_probe_jobs_are_stage1_jobs():
    """The probe's work is reused: its job ids, output folder and arm configs are those of stage 1."""
    import yaml as _y
    p, s = (_y.safe_load((ROOT / f"configs/iter05b_{k}.yaml").read_text()) for k in ("probe", "stage1"))
    assert (p["exp_id"], p["out_dir"]) == (s["exp_id"], s["out_dir"])
    assert all(p["families"][f] == v for f, v in s["families"].items())          # stage 1 runs a subset of the probed families (A8)
    assert not {"catboost", "gp"} & set(s["families"]) and not any({"catboost", "gp"} & set(a["families"]) for a in s["arms"])
    ids = {j["id"] for j in RQ.jobs(s)}
    kept = [j for j in RQ.jobs(p) if j["family"] in s["families"]]
    assert {j["id"] for j in kept} <= ids and len(kept) == len(s["families"])
    for a in p["arms"]:
        assert a["config"] == next(b for b in s["arms"] if b["name"] == a["name"])["config"]


def test_runtime_estimate_05b_from_probe_markers(tmp_path):
    import json
    from paperb import runtime_estimate as RE
    J = tmp_path / "stage1" / "jobs"
    J.mkdir(parents=True)
    for fam, h in {"physics": 1.0, "linear": 1.0, "rawseries": 2.0, "tabpfn": 4.0, "catboost": 5.0}.items():
        (J / f"arm2__s0__d0__nall__{fam}.done").write_text(json.dumps({"seconds": 3600 * h}))
    (J / "arm2__s0__d0__nall__kernel.failed").write_text("boom")
    S = RE.main05b(10, tmp_path)
    lc = 10 * 2 * (16 + 32 + 62 + 100 + 200) / RE.HP_MAIN
    assert S.loc[1, "job hours"] == pytest.approx(20 * 8 + lc * (1 + 0.25 + 1 + 1), abs=0.2)
    txt = (tmp_path / "runtime_estimate_05b.md").read_text()                   # catboost probed but not run (A8): not counted
    assert "Failed probe jobs (not in the estimate): kernel" in txt and "{'catboost': 5.0}" in txt


# ------------------------------------------------------------------ memory and sharding (Stage 1 runtime)
def test_day_sum_streaming_is_bitwise_identical():
    from paperb.fill_analog import AnalogFill
    rng = np.random.default_rng(1)
    S = rng.gamma(1.0, 0.3, (300, 40, 48)).astype(np.float32)
    hh = [f"L{i}" for i in range(300)]
    af = AnalogFill(S, hh, pd.DataFrame({"pos": [0]}), {}, None, None, {})
    for members in (["L7"], ["L3", "L250", "L1"], list(rng.choice(hh, 200, replace=False))):
        old = np.asarray(S[sorted(af.pos[h] for h in members)], np.float64).sum(axis=0)
        assert np.array_equal(af.day_sum(members), old)
    assert np.array_equal(af.day_sum([]), np.zeros((40, 48)))


def test_queue_shards_are_disjoint_and_cover_every_job():
    import yaml as _y
    q = _y.safe_load((ROOT / "configs/iter05b_stage1.yaml").read_text())
    js = RQ.jobs(q)
    parts = [RQ.shard(js, f"{i}/3") for i in range(3)]
    ids = [{j["id"] for j in p} for p in parts]
    assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])
    assert set().union(*ids) == {j["id"] for j in js} and RQ.shard(js, None) == js
    assert max(len(p) for p in parts) - min(len(p) for p in parts) <= 1
    with pytest.raises(ValueError):
        RQ.shard(js, "3/3")


# ------------------------------------------------------------------ Stage 1 report: the pre-registered rule on synthetic results
def _fake_stage1(root, rng):
    scopes = ["all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"]
    curves = {("slope_base", "none", "-", "-", "-"): lambda n: 25.0, ("paperA_corr", "none", "-", "-", "-"): lambda n: 26.0,
              ("hdh", "none", "-", "-", "-"): lambda n: 5.0, ("oracle_O2", "none", "-", "-", "-"): lambda n: 0.1,  # sentinels: never "best physics"
              ("Lasso", "size", "netfit", "direct", "log"): lambda n: 15.0 + 60.0 * n ** -0.5,             # data-limited, beats physics
              ("Ridge", "size", "netfit", "direct", "log"): lambda n: 3.0,                                 # test-best, inner-CV worst: never chosen
              ("XGBoost", "size", "netfit", "direct", "log"): lambda n: 27.0,                              # flat, above physics
              ("CNN", "size", "raw", "direct", "log"): lambda n: 30.0}
    inner = {"Ridge": 99.0}

    def rows(seed, draw, n, extra):
        out = []
        for cfg, f in curves.items():
            w = f(n) + rng.normal(0, 0.05)
            spec = dict(zip(["method", "anchor", "feature_set", "mode", "target_transform"], cfg))
            for s in scopes:
                out.append({"split_seed": seed, "target": "HP_Peak", **spec, "cell": s, "metric": "wape", "value": w, **extra})
            if cfg[0] in ("Lasso", "Ridge", "XGBoost", "CNN"):
                out += [{"split_seed": seed, "target": "HP_Peak", **spec, "cell": "all", "metric": m, "value": v, **extra}
                        for m, v in (("wape_inner", inner.get(cfg[0], w + 1)), ("wape_train", w - 2))]
        return out
    a1 = [r for s in range(10) for d in (0, 1) for n in (16, 32, 62, 100, 200) for r in rows(s, d, n, {"n_train_hp": n, "lc_draw": d})]
    a2 = [r for s in range(20) for r in rows(s, 0, 292, {})]
    for arm, data in (("arm1", a1), ("arm2", a2)):
        (root / arm).mkdir(parents=True)
    pd.DataFrame(a1).to_csv(root / "arm1" / "metrics_lc.csv", index=False)
    pd.DataFrame(a2).to_csv(root / "arm2" / "metrics.csv", index=False)
    pd.DataFrame([{"split_seed": s, "n": "main", "pilot": "all", "n_hh": 292} for s in range(20)]).to_csv(root / "arm2" / "pilots.csv", index=False)


def test_stage1_report_applies_the_preregistered_rule(tmp_path):
    from paperb import iter05b_report as R
    _fake_stage1(tmp_path, np.random.default_rng(3))
    V, F = R.main(tmp_path)
    v = V.set_index(["family", "scope"])["verdict"]
    assert (v.xs("linear", level="family") == "D").all()
    assert (v.xs("trees", level="family") == "I or features").all() and (v.xs("rawseries", level="family") == "I or features").all()
    assert not any(F.values())
    D = pd.read_csv(tmp_path / "report" / "lc_paired.csv")
    assert set(D["phys"]) == {"slope_base"}                                     # oracle / HDH sentinels never chosen
    assert not D["winner"].str.startswith("Ridge").any()                        # selection by inner CV only
    assert (tmp_path / "report" / "fig_learning_curve.png").exists() and "† = filler-variability-limited" in (tmp_path / "report" / "stage1_report.md").read_text()


def test_gpu_queue_has_the_same_jobs_and_moves_only_cnn_and_tabpfn():
    import yaml as _y
    q, g = (_y.safe_load((ROOT / f"configs/{f}.yaml").read_text()) for f in ("iter05b_stage1", "iter05b_stage1_gpu"))
    assert [j["id"] for j in RQ.jobs(q)] == [j["id"] for j in RQ.jobs(g)] and (q["exp_id"], q["out_dir"]) == (g["exp_id"], g["out_dir"])
    js = RQ.jobs(g)
    for fam in g["families"]:
        cfg, _ = RQ.job_config(g, g["arms"][1], next(j for j in js if j["family"] == fam and j["arm"] == "arm2"), 2)
        assert cfg.get("device", "cpu") == ("cuda" if fam in ("rawseries", "tabpfn") else "cpu")


def test_cnn_cpu_device_path_is_deterministic():
    from paperb.models_rawseries import RawSeriesCNN
    X, y = toy_xy(120, seed=4, cnn=True)
    p = NEW["CNN"]
    a = RawSeriesCNN(p, 7, 1, "cpu"); a.fit(X, np.log(y), n_iter=3)
    b = RawSeriesCNN(p, 7, 1, "cpu"); b.fit(X, np.log(y), n_iter=3)
    assert np.array_equal(a.predict(X), b.predict(X))


def _cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


@pytest.mark.skipif(not _cuda(), reason="no CUDA device")
def test_cnn_and_tabpfn_run_on_cuda():
    """GPU smoke test (05b GPU machine): the CNN is deterministic on CUDA and close to its CPU result; TabPFN fits on CUDA."""
    from paperb.models_rawseries import RawSeriesCNN
    X, y = toy_xy(120, seed=4, cnn=True)
    runs = []
    for dev in ("cuda", "cuda", "cpu"):
        m = RawSeriesCNN(NEW["CNN"], 7, 1, dev)
        m.fit(X, np.log(y), n_iter=3)
        runs.append(m.predict(X))
    assert np.array_equal(runs[0], runs[1]) and np.allclose(runs[0], runs[2], atol=1e-2)
    if (Path(os.environ.get("TABPFN_MODEL_CACHE_DIR", "-")) / T.TABPFN_CHECKPOINT).is_file():
        T.configure(1, device="cuda")
        Xt, yt = toy_xy(200, seed=5)
        p = T.tabpfn_regressor(0).fit(Xt.fillna(0), np.log(yt)).predict(Xt.fillna(0))
        T.configure(1, device="cpu")
        assert np.isfinite(p).all()


def test_check_jobs_reports_missing_failed_and_wrong_device(tmp_path):
    import json
    import yaml as _y
    from paperb import check_jobs as CJ
    q = _y.safe_load((ROOT / "configs/iter05b_stage1_gpu.yaml").read_text())
    js = [j for j in RQ.jobs(q) if j["family"] == "tabpfn"]
    J = tmp_path / "jobs"
    J.mkdir()
    for k, j in enumerate(js[:-2]):
        (J / f"{j['id']}.done").write_text(json.dumps({"seconds": 1, "device": "cpu" if k == 0 else "cuda", "host": "B"}))
        (J / f"{j['id']}.lc.parquet").write_text("x")
    (J / f"{js[-2]['id']}.failed").write_text("boom")
    skip, lost = js[1]["id"], js[2]["id"]                      # done without frames: inner CV infeasible (recorded) vs unexplained
    for i in (skip, lost):
        (J / f"{i}.lc.parquet").unlink()
    pd.DataFrame({"reason": ["inner CV infeasible: substations in 2 of 4 folds"]}).to_parquet(J / f"{skip[:-len('tabpfn')]}physics.lc_dropped.parquet")
    rows, problems = CJ.check(q, tmp_path, {"tabpfn"}, {"tabpfn": "cuda"})
    assert sum(r["skipped_inner_cv"] for r in rows) == 1 and sum(r["done_without_frames"] for r in rows) == 1
    assert sum(r["done"] for r in rows) == len(js) - 2 and sum(r["failed"] for r in rows) == 1 and sum(r["missing"] for r in rows) == 1
    text = "\n".join(problems)
    assert "1 failed" in text and "1 missing" in text and "1 device != cuda" in text
