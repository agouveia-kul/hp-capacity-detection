"""Iteration 03b invariants: s0 from train households only, cross-fitted pilots household-disjoint from their fold /
substation, the non-TCL correction, cv_wape, Berchtoldstag, Paper A penetration bins, model_anchors. The run_seed
integration test needs data/_paperb/pools/bstar_2023*.parquet and is skipped without it."""
import copy
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from paperb import load_config  # noqa: E402
from paperb import physics as PH  # noqa: E402
from paperb import run_benchmark as RB  # noqa: E402
from paperb import train as T  # noqa: E402
from paperb.features_netfit import weekend_or_holiday  # noqa: E402
from paperb.splits import household_splits  # noqa: E402

CFG = load_config("configs/iter03b_quick.yaml")
POOL_META = ROOT / "data" / "_paperb" / "pools" / "bstar_2023_meta.parquet"
needs_pool = pytest.mark.skipif(not POOL_META.exists(), reason="B* pool cache not built")


def test_berchtoldstag_is_a_zh_holiday():
    days = pd.date_range("2023-01-01", "2024-12-31", freq="D", tz="UTC")
    marked = set(days[weekend_or_holiday(days)].date)
    assert {date(2023, 1, 2), date(2024, 1, 2)} <= marked                   # a Monday and a Tuesday
    assert date(2023, 1, 3) not in marked and date(2024, 1, 3) not in marked


def synthetic_pool(n_fill=10, n_hp=4, s_fill=0.02, s_own=0.01):
    idx = pd.date_range("2023-01-01", "2023-12-31 23:00", freq="h", tz="UTC")
    day = np.arange(len(idx)) // 24
    T_ = pd.Series(10 + 12 * np.sin(2 * np.pi * (day - 110) / 365), index=idx)
    heat = np.maximum(0, 15 - T_)
    fill = pd.DataFrame({f"f{i}": 0.3 + s_fill * heat for i in range(n_fill)}, index=idx)
    own = pd.DataFrame({f"h{i}": 0.2 + s_own * heat for i in range(n_hp)}, index=idx)
    meta = pd.DataFrame({"station": ["KLO"] * n_hp}, index=own.columns)
    return SimpleNamespace(fill=fill, own=own, temp=pd.DataFrame({"KLO": T_}), meta=meta)


def test_household_sensitivity_uses_only_the_households_it_is_given():
    pool = synthetic_pool()
    a = PH.household_sensitivity(pool, list(pool.fill.columns))
    assert a["s0"] == pytest.approx(0.02, rel=0.02) and a["N"] == 10
    b = PH.household_sensitivity(pool, list(pool.fill.columns), list(pool.own.columns))          # + own load of 4 HP hh
    assert b["N"] == 14 and b["s0"] == pytest.approx((10 * 0.02 + 4 * 0.01) / 14, rel=0.02)
    two = PH.household_sensitivity(pool, ["f0", "f1"])                                            # unlisted columns are ignored
    assert two["N"] == 2 and two["s0"] == pytest.approx(0.02, rel=0.02)


def test_paperA_corrected_hand_computed():
    # s_h - N s0: 1 - 0.2 = 0.8 (valid), 1 - 0.8 = 0.2 (valid), 0.5 - 0.4 = 0.1 (valid), 0.5 - 1.0 < 0, NaN slope
    p, ok = PH.paperA_corrected([1.0, 1.0, 0.5, 0.5, np.nan], [10, 40, 20, 50, 10], 0.02, 0.02)
    np.testing.assert_array_equal(ok, [True, True, True, False, False])
    np.testing.assert_allclose(p, [40.0, 10.0, 5.0, 0.0, 0.0])
    _, ok_m = PH.paperA_corrected([1.0], [10], 0.02, np.nan)                 # invalid pilot slope -> invalid, predicted 0
    assert not ok_m[0]


def test_crossfit_pilots_are_household_disjoint(monkeypatch):
    train_hp = [f"h{i}" for i in range(12)]
    folds = pd.Series({h: i % 4 for i, h in enumerate(train_hp)})
    members = pd.DataFrame({"split": ["inner", "inner", "train", "train", "test"], "fold": [0, 2, -1, -1, -1],
                            "hp_members": [["h0", "h4"], ["h2"], ["h1", "h5", "h9"], ["h0", "h3"], ["h7"]]},
                           index=["i0", "i2", "t0", "t1", "x0"])
    seen = []

    def fake(pool, hh, caps):
        seen.append(set(hh))
        return {"m": float(len(hh))}

    monkeypatch.setattr(PH, "pool_pilot", fake)
    m, fold_m = PH.crossfit_pilot_m(None, train_hp, None, folds, members, 99.0)
    fold0 = {h for h in train_hp if folds[h] == 0}
    assert fold_m == {0: 9.0, 2: 9.0}
    assert seen[0] == set(train_hp) - fold0 and not seen[0] & fold0 and not seen[0] & {"h0", "h4"}   # fold 0 pilot: no fold-0 hh
    assert seen[1] == {h for h in train_hp if folds[h] != 2} and not seen[1] & {"h2"}
    assert seen[2] == set(train_hp) - {"h1", "h5", "h9"} and seen[3] == set(train_hp) - {"h0", "h3"}  # train: without own members
    assert (m["i0"], m["i2"], m["t0"], m["t1"], m["x0"]) == (9.0, 9.0, 9.0, 10.0, 99.0)            # test keeps the full pilot


def test_cv_wape_matches_manual_out_of_fold_wape():
    rng = np.random.default_rng(0)
    n, g = 80, np.arange(80) % 4
    X = pd.DataFrame(rng.normal(size=(n, 2)), columns=["a", "b"])
    y = 20 + 3 * X["a"].to_numpy() + rng.normal(scale=0.5, size=n)
    _, meta, _ = T.tune_grouped_cv("Linear", X, y, g, 0, 1, eval_on=(y, None))
    err = 0.0
    for f in range(4):
        m = T.Model("Linear", {}, 0)
        m.fit(X[g != f], y[g != f])
        err += np.abs(m.predict(X[g == f]) - y[g == f]).sum()
    assert meta["cv_wape"] == pytest.approx(100 * err / y.sum())
    p_hat = np.exp(rng.normal(size=n)) * 5 + 10                                     # residual: y_hat = p_hat * exp(z_hat)
    z = np.log(y) - np.log(p_hat)
    _, meta_r, _ = T.tune_grouped_cv("Linear", X, z, g, 0, 1, opts={"clip": False}, eval_on=(y, p_hat))
    err = 0.0
    for f in range(4):
        m = T.Model("Linear", {}, 0, {"clip": False})
        m.fit(X[g != f], z[g != f])
        err += np.abs(p_hat[g == f] * np.exp(m.predict(X[g == f])) - y[g == f]).sum()
    assert meta_r["cv_wape"] == pytest.approx(100 * err / y.sum())


def test_model_anchors_restrict_a_model_and_paperA_rows_are_listed():
    sp = RB.specs(CFG)
    mono = {(s[1], s[2]) for s in sp if s[0] == "XGBoost_mono"}
    assert mono and {a for a, _ in mono} == {"size_peak"} and "whdd" not in {f for _, f in mono}
    assert {s[0] for s in sp if s[0].startswith("paperA_")} >= {"paperA_cal", "paperA_corr", "paperA_corr_all", "paperA_corr_cal"}
    assert {s[1] for s in sp if s[0] == "XGBoost"} == {"none", "size_peak"}


def test_penetration_bins_partition_the_test_substations():
    te = pd.DataFrame({"HP_Count": [1, 2, 3, 4, 6, 10, 20, 7], "size": [10, 10, 10, 20, 20, 10, 40, 10], "p": 0.1,
                       "HP_Peak": np.arange(1.0, 9.0)})              # actual p = .1 .2 .3 .2 .3 1 .5 .7
    mem = pd.DataFrame({"hp_members": [{str(i)} for i in range(8)]}, index=te.index)
    rows = RB.metric_rows({"uncertainty": {"bootstrap": False}}, 0, "HP_Peak", te, te["HP_Peak"].to_numpy() * 1.1, mem)
    n = {r["cell"]: r["n_substations"] for r in rows if r["metric"] == "wape"}
    assert n["all"] == 8 and sum(n[c] for c in ("pbin<=15", "pbin15-35", "pbin35-65", "pbin>65")) == 8
    assert (n["pbin<=15"], n["pbin15-35"], n["pbin35-65"], n["pbin>65"]) == (1, 4, 1, 2)


@needs_pool
def test_run_seed_03b_train_only_s0_calibration_and_bins(monkeypatch):
    cfg = copy.deepcopy(CFG)
    cfg.update(models=["Linear"], model_anchors={}, feature_sets=["netfit"], modes=["direct", "residual"],
               target_transforms=["none"], residual_models=["Ridge"], anchors=["size_peak"], physics_baselines=[],
               anchor_only_baselines={"models": [], "features": []}, pilot_cache=False)       # 05b: the s0 calls are what is tested
    cfg["paperA"]["estimators"] = ["paperA_sh_mh", "paperA_cal", "paperA_corr", "paperA_corr_cal"]
    cfg["learning_curve"].update(specs=["paperA_corr|none|-|-|-"], feature_sets=["netfit"])
    cfg["parallel"]["threads"] = 4
    calls, real = [], PH.household_sensitivity
    monkeypatch.setattr(RB, "household_sensitivity",
                        lambda pool, fill, own=(), st="KLO": calls.append((set(fill), set(own))) or real(pool, fill, own, st))
    res = RB.run_seed(cfg, 0)
    sp = household_splits(pd.read_parquet(POOL_META), [0], cfg["split"]["test_frac"])[0]
    test_hh = set(sp["test"]["hp"]) | set(sp["test"]["fill"])
    assert calls and all(fill == set(sp["train"]["fill"]) and own <= set(sp["train"]["hp"]) and not (fill | own) & test_hh
                         for fill, own in calls)
    m = res["metrics"]
    b = m[(m["method"] == "paperA_cal") & (m["metric"] == "cal_b")]["value"].iloc[0]
    pr = res["preds"]
    a = pr[pr["method"] == "paperA_sh_mh"].set_index("sub_id")["pred"]
    c = pr[pr["method"] == "paperA_cal"].set_index("sub_id")["pred"]
    np.testing.assert_allclose((c / a)[a > 0], np.exp(b))
    assert {"all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"} <= set(m["cell"])
    assert {"s0:paperA_corr", "s0:paperA_corr_all"} <= set(res["pilots"]["pilot"]) and res["pilots"]["pilot"].str.startswith("cf:").any()
    assert res["timing"]["cv_wape"].notna().any()
