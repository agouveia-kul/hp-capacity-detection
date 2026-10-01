"""Iteration 03a invariants: holiday calendar, Paper A pilot fixture, transforms and residual composition, monotone
constraints, learning-curve memberships and pilot, WAPE, and fold-only imputer/scaler fits. Pool-dependent tests need
data/_paperb/pools/bstar_2023*.parquet and are skipped without it."""
import copy
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from paperb import load_config  # noqa: E402
from paperb import train as T  # noqa: E402
from paperb.features_netfit import COLUMNS, netfit_features, weekend_or_holiday  # noqa: E402
from paperb.learning_curve import lc_designs  # noqa: E402
from paperb.metrics import compute_metrics  # noqa: E402
from paperb.physics import paperA_estimate, pilot_fit  # noqa: E402
from paperb.residual import compose, log_ratio, residual_predict  # noqa: E402
from paperb.splits import household_splits  # noqa: E402
from paperb.substations import build_substations  # noqa: E402

CFG = load_config("configs/iter03_quick.yaml")
POOL_META = ROOT / "data" / "_paperb" / "pools" / "bstar_2023_meta.parquet"
needs_pool = pytest.mark.skipif(not POOL_META.exists(), reason="B* pool cache not built")
XGB = {"eta": 0.1, "max_depth": 3, "gamma": 0, "subsample": 1, "reg_alpha": 0, "reg_lambda": 1, "colsample_bytree": 1,
       "min_child_weight": 1, "n_estimators": 50}
PARAMS = {"Linear": {}, "Ridge": {"alpha": 0.1}, "Lasso": {"alpha": 0.01}, "XGBoost": XGB}
ZH_2023 = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 4, 7), date(2023, 4, 10), date(2023, 5, 1), date(2023, 5, 18),
           date(2023, 5, 29), date(2023, 8, 1), date(2023, 12, 25), date(2023, 12, 26)]


def test_zh_holidays_and_disjoint_day_partition():
    days = pd.date_range("2023-01-01", "2023-12-31", freq="D", tz="UTC")
    we = weekend_or_holiday(days)
    marked = set(days[we].date)
    assert set(ZH_2023) <= marked                                   # incl. weekday holidays (Good Friday, Ascension)
    assert all(d.dayofweek >= 5 or d.date() in ZH_2023 for d in days[we])
    assert (days[~we].dayofweek < 5).all() and not set(days[~we].date) & set(ZH_2023)
    assert we.sum() + (~we).sum() == len(days) == 365 and we.sum() == 105 + 9   # 105 weekend days + 9 weekday holidays (1 Jan: Sunday; Berchtoldstag added in 03b)


def test_paperA_pilot_fixture():
    """Our port of Paper A `_pilot_fit` on Paper A's own Kloten inputs reproduces its committed pilots."""
    f = np.load(ROOT / "tests" / "fixtures" / "paperA_pilot_fixture.npz")
    for A, committed, again in zip(f["A"], f["committed"], f["paperA"]):
        mine = pilot_fit(f["T"], f["hp"][A].sum(0), f["own"][A].sum(0), f["cap"][A].sum())
        np.testing.assert_allclose(mine, committed, rtol=0, atol=1e-6)
        np.testing.assert_allclose(mine, again, rtol=0, atol=1e-6)
    assert round(float(f["committed"][0, 1]), 4) == 0.0187         # draft: pilot split 0, m_h = 0.019 (0.0187)
    assert round(float(np.median(f["committed"][:, 1])), 3) == 0.018  # draft: median over the 20 splits


def test_paperA_invalid_estimates_are_zero_and_flagged():
    p, ok = paperA_estimate([2.0, 0.0, -1.0, np.nan, 3.0], np.array([0.02, 0.02, 0.02, 0.02, np.nan]))
    np.testing.assert_array_equal(ok, [True, False, False, False, False])
    np.testing.assert_allclose(p, [100.0, 0, 0, 0, 0])


def test_log_transform_round_trip():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(50, 3)), columns=list("abc"))
    y = np.exp(0.5 + 0.3 * X["a"] - 0.2 * X["c"]).to_numpy()
    m = T.Model("Linear", {}, 0, {"target_transform": "log"})
    m.fit(X, y)
    np.testing.assert_allclose(m.predict(X), y, rtol=1e-10)
    with pytest.raises(ValueError):
        T.Model("Linear", {}, 0, {"target_transform": "log"}).fit(X, y - y.max())


def test_residual_composition_round_trip():
    p = np.array([10.0, 20.0, 5.0, 7.0])
    valid = np.array([True, True, False, True])
    np.testing.assert_array_equal(compose(p, np.zeros(4), valid), [10.0, 20.0, 0.0, 7.0])     # z_hat = 0 -> P_hat exactly
    y = np.array([12.0, 18.0, 9.0, 7.5])
    z = log_ratio(y, p, valid)
    assert np.isnan(z[2])
    np.testing.assert_allclose(compose(p, np.nan_to_num(z), valid)[valid], y[valid], rtol=1e-12)


def test_residual_excludes_invalid_and_uses_fallback():
    n = 12
    split = np.array(["inner"] * 4 + ["train"] * 4 + ["test"] * 4)
    p = np.full(n, 10.0)
    valid = np.ones(n, bool)
    valid[[1, 5, 9]] = False
    y = p * np.exp(0.2)
    seen = {}

    def tuned(name, X, z, m_in, m_tr, opts, space, eval_on=None):         # stands in for the grouped-CV tuner: predicts mean z
        seen.update(z_in=z[m_in], z_tr=z[m_tr], opts=opts)
        return np.full(int((split == "test").sum()), z[m_tr].mean())

    yh, c = residual_predict(tuned, "Ridge", pd.DataFrame({"a": np.arange(n)}), y, p, valid,
                             split == "inner", split == "train", split == "test")
    assert np.isfinite(seen["z_in"]).all() and len(seen["z_in"]) == 3 and len(seen["z_tr"]) == 3
    assert c == {"n_resid_excluded_train": 1, "n_resid_excluded_inner": 1} and seen["opts"] == {"clip": False}
    np.testing.assert_allclose(yh, [y[8], 0.0, y[10], y[11]])


def test_monotone_constraints_only_on_sh_and_cold_resp():
    cols = ["nf_all_s_h", "nf_wd_cold_resp", "nf_all_T_h", "nf_ratio_sh_we_wd", "nf_we_s_h", "nf_all_r_hat",
            "Feature night_ratio_Mean", "Feature Scale_size", "nf_theta_cold"]
    rng = np.random.default_rng(1)
    X = pd.DataFrame(rng.normal(size=(80, len(cols))), columns=cols)
    y = 5 + X["nf_all_s_h"] - X["nf_all_T_h"] + rng.normal(scale=0.1, size=80)
    params = XGB
    m = T.Model("XGBoost_mono", params, 0)
    m.fit(X, y)
    assert m.monotone_constraints() == (1, 1, 0, 0, 1, 0, 0, 0, 0)
    assert m.m.get_params()["monotone_constraints"] == (1, 1, 0, 0, 1, 0, 0, 0, 0)
    grid = pd.concat([X.iloc[[0]]] * 40, ignore_index=True)
    grid["nf_all_s_h"] = np.linspace(-3, 3, 40)
    assert (np.diff(m.predict(grid)) >= -1e-9).all()
    plain = T.Model("XGBoost", params, 0)
    plain.fit(X, y)
    assert "monotone_constraints" not in plain.m.get_params() or plain.m.get_params()["monotone_constraints"] is None


def test_wape_hand_computed():
    out = compute_metrics([10.0, 20.0, 30.0], [12.0, 18.0, 33.0])
    assert list(out)[0] == "wape" and out["wape"] == pytest.approx(7 / 60 * 100)


@pytest.mark.parametrize("name", ["Linear", "Ridge", "Lasso", "XGBoost"])
def test_imputer_and_scaler_fitted_on_training_folds_only(monkeypatch, name):
    """Leakage sentinel. (1) Column `sentinel` is 1e6 on every row of a held-out fold and 0 or NaN elsewhere: the imputer
    median and the scaler mean fitted on the other folds must be 0. (2) Inside tune_grouped_cv the sentinel is 1000 x
    fold id: every fit's imputer / scaler statistics must equal those of the rows it was given, which never span all
    four folds."""
    rng = np.random.default_rng(0)
    n, g = 120, np.arange(120) % 4
    X = pd.DataFrame(rng.normal(size=(n, 3)), columns=list("abc"))
    y = 3 * X["a"].to_numpy() + 10 + rng.normal(scale=0.3, size=n)
    fits, real = [], T.Model._prep

    def spy(self, Xa, ya):
        out = real(self, Xa, ya)
        fits.append((Xa.index.to_numpy(), Xa["sentinel"].to_numpy(), self.imp.statistics_[-1], self.xs.mean_[-1]))
        return out

    monkeypatch.setattr(T.Model, "_prep", spy)
    for held in range(4):
        Xs = X.assign(sentinel=np.where(g == held, 1e6, np.where(rng.random(n) < 0.3, np.nan, 0.0)))
        m = T.Model(name, PARAMS[name], 0)
        m.fit(Xs[g != held], y[g != held])
        assert fits[-1][2] == 0.0 and fits[-1][3] == 0.0                  # 1e6 would dominate had the fold leaked
    fits.clear()
    Xs = X.assign(sentinel=np.where(rng.random(n) < 0.2, np.nan, 1000.0 * g))
    T.tune_grouped_cv(name, Xs, y, g, seed=0, max_evals=1)
    assert len(fits) >= 5                                                 # 4 CV fits + the final refit
    for idx, sent, med, mean in fits[:-1]:
        assert len(set(g[idx])) < 4
        assert med == np.nanmedian(sent) and mean == pytest.approx(np.where(np.isnan(sent), np.nanmedian(sent), sent).mean())


def test_netfit_columns_and_nan_rule():
    idx = pd.date_range("2023-01-01", periods=96 * 365, freq="15min", tz="UTC")
    day = np.arange(len(idx)) // 96
    T_ = pd.Series(10 + 12 * np.sin(2 * np.pi * (day - 110) / 365), index=idx)
    net = pd.Series(5 + 0.8 * np.maximum(0, 16 - T_) + 0.05 * np.cos(np.arange(len(idx))), index=idx)
    f = netfit_features(T_, net)
    assert list(f) == COLUMNS and len(COLUMNS) == 29
    assert f["nf_all_s_h"] == pytest.approx(0.8, rel=0.02) and f["nf_all_T_h"] == pytest.approx(16, abs=0.3)
    short = netfit_features(T_.iloc[: 96 * 40], net.iloc[: 96 * 40], min_days=20)      # 40 days -> ~12 weekend days
    assert np.isnan(short["nf_we_s_h"]) and 0 < short["nf_we_n_heat_days"] < 20 and np.isfinite(short["nf_wd_s_h"])


@needs_pool
def test_learning_curve_memberships():
    meta = pd.read_parquet(POOL_META)
    cfg = copy.deepcopy(CFG)
    cfg["learning_curve"] = {"n": [16, 32, 48, "all"], "draws": 2, "specs": []}
    sp = household_splits(meta, [0], cfg["split"]["test_frac"])[0]
    from paperb.splits import grouped_inner_folds
    main, _ = build_substations(meta, sp, 0, cfg, grouped_inner_folds(sp["train"], meta, cfg["cv"]["k"], 0))
    test = main[main["split"] == "test"]
    seen = []
    for n, draw, _, sub, mem, _ in lc_designs(cfg, meta, sp, 0, test):
        assert set(sub) <= set(sp["train"]["hp"]) and len(sub) == (len(sp["train"]["hp"]) if n == "all" else n)
        tr = mem[mem["split"] != "test"]
        assert set().union(*tr["hp_members"]) <= set(sub)                       # train and inner use the subsample only
        assert set().union(*tr["fill_members"]) <= set(sp["train"]["fill"])
        te = mem[mem["split"] == "test"]
        assert te.index.equals(test.index) and (te["hp_members"] == test["hp_members"]).all()
        seen.append((n, draw, tuple(sub)))
    assert len(seen) == 3 * 2 + 1 and seen[0][2] != seen[1][2]                   # draws differ


@needs_pool
def test_learning_curve_pilot_is_the_subsample(monkeypatch):
    """run_seed passes exactly the learning-curve subsample to the Paper A pilot (and the train HP pool in the main run)."""
    from paperb import run_benchmark as RB
    cfg = copy.deepcopy(CFG)
    cfg.update(models=["Linear"], modes=["direct"], target_transforms=["none"], physics_baselines=[],
               anchor_only_baselines={"models": [], "features": []}, paperA={**cfg["paperA"], "cap_def_check": False},
               pilot_cache=False)                                              # 05b: the pilot calls are what is tested
    cfg["learning_curve"]["specs"] = ["paperA_sh_mh|none|-|-|-"]
    cfg["parallel"]["threads"] = 4
    calls, real = [], RB.paperA_pilots
    monkeypatch.setattr(RB, "paperA_pilots", lambda pool, hp, caps, k: calls.append(sorted(hp)) or real(pool, hp, caps, k))
    res = RB.run_seed(cfg, 0)
    sp = household_splits(pd.read_parquet(POOL_META), [0], cfg["split"]["test_frac"])[0]
    from paperb.learning_curve import lc_subsample
    assert calls == [sorted(sp["train"]["hp"]), lc_subsample(sp["train"]["hp"], 16, 0, 0)]
    lc = res["lc"]
    assert set(lc["n_train_hp"]) == {16} and set(lc["lc_draw"]) == {0} and (lc["method"] == "paperA_sh_mh").all()
    assert (res["pilots"].loc[res["pilots"]["n"] == 16, "n_hh"].iloc[0] == 16)
