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
        if "tabpfn" in (txt := f.read_text(encoding="utf-8")):
            assert info["sha256"] in txt


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
