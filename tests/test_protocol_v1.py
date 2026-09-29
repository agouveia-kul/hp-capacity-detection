"""Protocol v1 invariants (iteration 02a). Pool-dependent tests need data/_paperb/pools/bstar_2023*.parquet
(build with scripts/paperb/pools.py via run_benchmark or make_paperA_fixture); they are skipped without it."""
import copy
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from paperb import load_config  # noqa: E402
from paperb import train as T  # noqa: E402
from paperb.physics import daily_means, fit_daily, sf_arm  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import InfeasibleCellError, build_substations, evaluate_members  # noqa: E402
from paperb.uncertainty import cluster_bootstrap  # noqa: E402

CFG = load_config("configs/protocol_v1.yaml")
SEEDS = CFG["split"]["seeds"]
POOL_META = ROOT / "data" / "_paperb" / "pools" / "bstar_2023_meta.parquet"
needs_pool = pytest.mark.skipif(not POOL_META.exists(), reason="B* pool cache not built")


@pytest.fixture(scope="module")
def meta():
    return pd.read_parquet(POOL_META)


@pytest.fixture(scope="module")
def splits(meta):
    return household_splits(meta, SEEDS, CFG["split"]["test_frac"])


@pytest.fixture(scope="module")
def built(meta, splits):
    out = {}
    for s in SEEDS[:3]:
        folds = grouped_inner_folds(splits[s]["train"], meta, CFG["cv"]["k"], s)
        out[s] = (folds, *build_substations(meta, splits[s], s, CFG, folds))
    return out


@needs_pool
def test_bstar_pool_counts(meta):
    assert (meta["role"] == "hp").sum() == 86 and (meta["role"] == "fill").sum() == 1291
    assert meta["coverage"].min() >= CFG["pool"]["coverage_min"]


@needs_pool
def test_train_test_household_disjoint(meta, splits):
    hp, fill = set(meta.index[meta["role"] == "hp"]), set(meta.index[meta["role"] == "fill"])
    for s in SEEDS:
        for k, allk in (("hp", hp), ("fill", fill)):
            tr, te = set(splits[s]["train"][k]), set(splits[s]["test"][k])
            assert not tr & te and tr | te == allk
        for st, g in meta[meta["role"] == "hp"].groupby("station"):          # stratified by station
            assert len(set(g.index) & set(splits[s]["test"]["hp"])) == round(0.25 * len(g))


@needs_pool
def test_substation_membership_rules(meta, built, splits):
    for s, (folds, members, _) in built.items():
        for r in members.itertuples():
            hp, fl = set(r.hp_members), set(r.fill_members)
            assert len(hp) == len(r.hp_members) and len(fl) == len(r.fill_members)   # no household twice
            assert len(hp) + len(fl) == r.size and len(hp) == r.n_hp                 # no silent truncation (F12)
            assert not hp & fl and (meta.loc[list(fl), "role"] == "fill").all()     # no HP / fill overlap
            assert (meta.loc[list(hp), "station"] == r.station).all()               # one station
            pool = splits[s]["test" if r.split == "test" else "train"]
            assert hp <= set(pool["hp"]) and fl <= set(pool["fill"])                # same split's pools
            if r.split == "inner":
                assert (folds[list(hp | fl)] == r.fold).all()


@needs_pool
def test_infeasible_cells_raise_or_are_listed(meta, splits):
    cfg = copy.deepcopy(CFG)
    cfg["grid"]["on_infeasible"] = "raise"
    with pytest.raises(InfeasibleCellError):
        build_substations(meta, splits[0], 0, cfg)                         # size 120, p = 1.0 exceeds the envelope
    _, dropped = build_substations(meta, splits[0], 0, CFG)
    assert len(dropped) and dropped["reason"].notna().all()
    assert ((dropped["size"] == 120) & (dropped["p"] == 1.0)).any()


@needs_pool
def test_inner_folds_household_disjoint(meta, built, splits):
    for s, (folds, members, _) in built.items():
        train = set(splits[s]["train"]["hp"]) | set(splits[s]["train"]["fill"])
        assert set(folds.index) == train and set(folds.unique()) == set(range(CFG["cv"]["k"]))
        inner = members[members["split"] == "inner"]
        used = {f: set().union(*(set(a) | set(b) for a, b in zip(g["hp_members"], g["fill_members"])))
                for f, g in inner.groupby("fold")}
        for f in used:
            for g in used:
                assert f == g or not used[f] & used[g]


@needs_pool
def test_same_seed_same_memberships(meta, splits, built):
    f2 = grouped_inner_folds(splits[0]["train"], meta, CFG["cv"]["k"], 0)
    m2, d2 = build_substations(meta, household_splits(meta, [0])[0], 0, CFG, f2)
    pd.testing.assert_series_equal(built[0][0], f2)
    pd.testing.assert_frame_equal(built[0][1], m2)
    assert not built[0][1].equals(built[1][1])


@needs_pool
def test_targets_nonnegative_and_deterministic(built):
    from paperb.pools import build_pool
    pool = build_pool("bstar", CFG)
    m = built[0][1]
    m = m[m["split"] == "test"].groupby("p").head(1)
    t1, _ = evaluate_members(pool, m, CFG, with_features=False)
    t2, _ = evaluate_members(pool, m, CFG, with_features=False)
    pd.testing.assert_frame_equal(t1, t2)
    for c in ("HP_Peak", "HP_CoincPeak", "HP_Count", "s_h", "P_design", "r", "peak"):
        assert (t1[c].dropna() >= 0).all(), c
    viol = t1["HP_CoincPeak"] > t1["HP_Peak"]
    if viol.any():                                                         # allowed by the robust-peak definition
        warnings.warn(f"HP_CoincPeak > HP_Peak in {int(viol.sum())} of {len(t1)} substations")


def test_physics_port_matches_paper_a():
    f = np.load(ROOT / "tests" / "fixtures" / "paperA_fixture.npz")
    idx = pd.date_range(str(f["start"]), periods=f["T"].shape[1], freq="15min")
    assert len(f["hh"]) >= 5
    for i in range(len(f["hh"])):
        T = pd.Series(f["T"][i], index=idx)
        Td, net = daily_means(T, pd.Series(f["net"][i], index=idx))
        r = fit_daily(Td, net)
        mine = [r["P_base"], r["s_h"], r["T_h"], r["r2"]]
        _, hp = daily_means(T, pd.Series(f["hp"][i], index=idx))
        mine += list(sf_arm(Td, np.clip(hp / f["cap"][i], 0, 1), r["T_h"], "h"))
        np.testing.assert_allclose(mine, f["paperA"][i], rtol=0, atol=1e-6)


def _toy(n=120, seed=0):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, 5)), columns=list("abcde"))
    y = 3 * X["a"] - 2 * X["b"] + rng.normal(scale=0.3, size=n) + 10
    return X, y.to_numpy(), np.arange(n) % 4


@pytest.mark.parametrize("name", ["Ridge", "XGBoost"])
def test_same_seed_same_hyperopt_trials(name):
    X, y, g = _toy()
    runs = [T.tune_grouped_cv(name, X, y, g, seed=3, max_evals=3) for _ in range(2)]
    assert runs[0][2].losses() == runs[1][2].losses()
    assert [t["misc"]["vals"] for t in runs[0][2].trials] == [t["misc"]["vals"] for t in runs[1][2].trials]
    np.testing.assert_array_equal(runs[0][0].predict(X), runs[1][0].predict(X))


def test_early_stopping_never_on_scored_fold(monkeypatch):
    X, y, g = _toy()
    X["fold"] = g
    seen, real_fit = [], T.Model.fit

    def spy(self, Xa, ya, n_iter=None, X_es=None, y_es=None):
        if X_es is not None:
            seen.append((set(Xa["fold"]), set(X_es["fold"])))
        return real_fit(self, Xa, ya, n_iter, X_es, y_es)

    monkeypatch.setattr(T.Model, "fit", spy)
    for name in ("XGBoost", "FFNN"):
        T.tune_grouped_cv(name, X, y, g, seed=0, max_evals=1)
    assert len(seen) == 2 * 4
    for fit_folds, es_folds in seen:
        assert len(es_folds) == 1 and len(fit_folds) == 2 and not fit_folds & es_folds  # scored fold is neither


def test_feature_matrix_anchor_arms():
    F = pd.DataFrame({"Feature x_ratio_Mean": [1.0, 2.0], "Feature x_Mean": [5.0, 6.0]}, index=["s1", "s2"])
    tab = pd.DataFrame({"size": [10, 20], "peak": [3.0, 4.0]}, index=["s1", "s2"])
    assert list(T.feature_matrix(F, tab, "none").columns) == ["Feature x_ratio_Mean"]
    assert list(T.feature_matrix(F, tab, "size_peak").columns)[-2:] == ["Feature Scale_size", "Feature Scale_peak"]


def test_bootstrap_resamples_households_not_substations():
    df = pd.DataFrame({"y": [1.0, 2.0, 3.0, 4.0], "p": [1.0, 2.0, 3.0, 4.0],
                       "hp_members": [["h1"], ["h1"], ["h2"], ["h1", "h2"]]})
    kept = []
    cluster_bootstrap(lambda d: kept.append(tuple(d.index)) or 0.0, df, B=200, seed=1)
    for k in kept:                                # substations 0 and 1 share their only household
        assert (0 in k) == (1 in k) and len(set(k)) == len(k)
        assert (3 in k) == ((0 in k) and (2 in k))  # kept iff all its HP households were drawn
    assert any(len(k) < len(df) for k in kept)


POOL_A_META = ROOT / "data" / "_paperb" / "pools" / "a_2023_meta.parquet"


@pytest.mark.skipif(not POOL_A_META.exists(), reason="pool A cache not built")
def test_pool_a_shared_fill_rules():
    """02b pool A: the fill pool of a split is its own HP households; a household is never HP member and fill member."""
    cfg, meta = load_config("configs/iter02b_legacy_a.yaml"), pd.read_parquet(POOL_A_META)
    assert len(meta) == 57 and (meta["role"] == "hp").all()
    for s in SEEDS[:3]:
        sp = household_splits(meta, [s], cfg["split"]["test_frac"], shared_fill=True)[s]
        assert not set(sp["train"]["hp"]) & set(sp["test"]["hp"]) and len(sp["train"]["hp"]) + len(sp["test"]["hp"]) == 57
        assert all(sp[k]["fill"] == sp[k]["hp"] for k in ("train", "test"))
        folds = grouped_inner_folds(sp["train"], meta, cfg["cv"]["k"], s)
        assert set(folds.index) == set(sp["train"]["hp"])
        members, _ = build_substations(meta, sp, s, cfg, folds)
        for r in members.itertuples():
            hp, fl = set(r.hp_members), set(r.fill_members)
            assert not hp & fl and len(hp) + len(fl) == r.size                    # no household twice, no truncation
            pool = sp["test" if r.split == "test" else "train"]["hp"]
            assert hp | fl <= set(pool)                                           # same split
            if r.split == "inner":
                assert (folds[list(hp | fl)] == r.fold).all()
