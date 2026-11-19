"""Iteration 08 (change detection), Tasks 1-2 tests of the brief.

Task 1 (synthetic pools): no household in both halves; year-2 members contain year-1 members; new HP homes are never already in
the feeder; N constant; dC_added = the new homes' year-2 peaks; no stacking. Task 2: a threshold never uses evaluation-half
feeders (synthetic); on the real pools: E2's year-1 local s0 equals 06's train-filler s0 map, permuting the households' labels
leaves dhat bit-identical (physics; with E1 under PAPERB_SLOW=1), E1 on the 06 test substations reproduces the 06 predictions
(|dWAPE| <= 0.001 pp; PAPERB_SLOW=1, TabPFN refits its context). No detection or error metric of 08 is computed.
"""
try:
    import torch  # noqa: F401
except (ImportError, OSError):
    pass
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import paperb.change_eval as CE  # noqa: E402
from paperb import load_config  # noqa: E402
from paperb.change_feeders import build_feeders, year_members  # noqa: E402

SLOW = pytest.mark.skipif(not os.environ.get("PAPERB_SLOW"), reason="slow (TabPFN refits its context): set PAPERB_SLOW=1")
CC = {"N": [20, 40], "p1": [0.05, 0.1, 0.2], "dp": [0.0, 0.05, 0.1, 0.2], "feeders_per_cell": 4, "max_overlap": 0.75, "min_station_pool": 3}
SPLIT = {"test_frac": 0.25, "stratify": "station"}


def synthetic_metas(seed=1):
    rng = np.random.default_rng(seed)
    hp = [f"E:{i:03d}" for i in range(160)]
    st1 = np.array([f"G{i % 4:03d}" for i in range(160)])
    fill = [f"L:{i:04d}" for i in range(600)]
    m1 = pd.concat([pd.DataFrame({"role": "hp", "station": st1, "hp_peak": rng.uniform(1, 9, 160)}, index=hp),
                    pd.DataFrame({"role": "fill", "station": "any", "hp_peak": np.nan}, index=fill)])
    keep = [h for h in hp if rng.random() > 0.15]                       # some homes are not eligible in year 2
    m2 = pd.concat([pd.DataFrame({"role": "hp", "station": [f"H{s}" for s in m1.loc[keep, "station"]],
                                  "hp_peak": rng.uniform(1, 9, len(keep))}, index=keep),
                    pd.DataFrame({"role": "fill", "station": "any", "hp_peak": np.nan}, index=fill)])
    return m1, m2


@pytest.fixture(scope="module")
def feeders():
    m1, m2 = synthetic_metas()
    F, dropped, info = build_feeders(m1, m2, 3, CC, SPLIT)
    return m1, m2, F, dropped, info


def test_halves_disjoint(feeders):
    m1, m2, F, _, info = feeders
    half = info["half"]
    assert half.index.is_unique and set(half.unique()) == {0, 1}
    for h in (0, 1):
        own = F[F["half"] == h]
        used = set().union(*own["hp1"], *own["hp_new"], *own["fill"])
        assert all(half[x] == h for x in used)                          # a feeder only uses its own half
    used = {h: set().union(*(F.loc[F["half"] == h, c].sum() for c in ("hp1", "hp_new", "fill"))) for h in (0, 1)}
    assert not used[0] & used[1]
    assert set(F["hp1"].sum() + F["hp_new"].sum()) <= set(m2.index[m2["role"] == "hp"])   # eligible in both years


def test_year2_contains_year1_and_new_homes(feeders):
    _, _, F, _, _ = feeders
    y1, y2 = year_members(F, 1), year_members(F, 2)
    for a, b, new in zip(y1["hp_members"], y2["hp_members"], F["hp_new"]):
        assert set(a) <= set(b) and set(b) - set(a) == set(new) and not set(new) & set(a)
    assert (y1["fill_members"].map(tuple).to_numpy() == y2["fill_members"].map(tuple).to_numpy()).all()
    assert (F["hp_new"].map(len) == F["dk"]).all() and (F["hp1"].map(len) == F["k1"]).all()
    assert (F.loc[F["dp"] == 0, "dk"] == 0).all() and (F.loc[F["dp"] > 0, "dk"] >= 1).all()


def test_size_constant_and_no_stacking(feeders):
    _, _, F, _, _ = feeders
    for y in (1, 2):
        m = year_members(F, y)
        assert (m["fill_members"].map(len) == F["N"].to_numpy()).all() and (m["size"] == F["N"].to_numpy()).all()
        assert all(len(set(h)) == len(h) for h in m["hp_members"]) and all(len(set(f)) == len(f) for f in m["fill_members"])
    assert (F["k1"] + F["dk"] <= CC["max_overlap"] * F["H"]).all()


def test_labels(feeders):
    m1, m2, F, _, _ = feeders
    for r in F.itertuples():
        assert np.isclose(r.dC_added, m2.loc[r.hp_new, "hp_peak"].sum())
        assert np.isclose(r.C1, m1.loc[r.hp1, "hp_peak"].sum()) and np.isclose(r.C2, m2.loc[r.hp1 + r.hp_new, "hp_peak"].sum())
        assert np.isclose(r.dC_total, r.C2 - r.C1)


def test_one_year2_group_and_dropped_cells(feeders):
    _, m2, F, dropped, _ = feeders
    for r in F.itertuples():
        assert m2.loc[r.hp1 + r.hp_new, "station"].nunique() == 1
    assert len(dropped) and set(dropped["reason"]) <= {"dk < 1 for dp > 0", "station pool < min_station_pool", "k1 + dk > max_overlap * H", "fill pool too small"}


def test_threshold_never_uses_evaluation_half():
    rng = np.random.default_rng(0)
    n = 400
    P = pd.DataFrame({"split_seed": 0, "estimator": "E2", "N": rng.choice([20, 40], n), "half": rng.integers(0, 2, n),
                      "dp": rng.choice([0.0, 0.1], n), "dhat": rng.normal(size=n)})
    f0 = CE.flags(P, CE.thresholds(P))
    Q = P.copy()
    Q.loc[Q["half"] == 1, "dhat"] += rng.normal(5, 3, int((Q["half"] == 1).sum()))   # change half 1 only
    f1 = CE.flags(Q, CE.thresholds(Q))
    t0 = f0.drop_duplicates(["N", "calib_half"]).set_index(["N", "calib_half"])["tau"].sort_index()
    t1 = f1.drop_duplicates(["N", "calib_half"]).set_index(["N", "calib_half"])["tau"].sort_index()
    assert (t0.xs(0, level=1) == t1.xs(0, level=1)).all()              # tau of calibration half 0 ignores half 1
    assert (f1.loc[f1["half"] == 1, "calib_half"] == 0).all()          # half 1 is scored with half 0's tau
    exp = P[(P["half"] == 0) & (P["dp"] == 0)].groupby("N")["dhat"].quantile(0.95)
    got = f0[f0["half"] == 1].groupby("N")["tau"].first()
    assert np.allclose(exp.sort_index().to_numpy(), got.sort_index().to_numpy())


def tiny_cfg(tmp, names=()):
    return {"parallel": {"threads": 2}, "models": list(names),
            "change": {**{**CC, "N": [20], "p1": [0.05], "dp": [0.0, 0.1], "feeders_per_cell": 2},
                       "year1": "configs/iter06_a_gb.yaml", "year2": "configs/iter06_r_rep.yaml", "feature_cache_dir": str(tmp)}}


def test_local_s0_year1_equals_06():
    from paperb.change_feeders import test_households
    pool, cfg = CE.year_pool("configs/iter06_a_gb.yaml", 0)
    P = pd.read_csv(CE.DIR06_MODELS.parents[1] / "a_gb" / "pilots.csv")
    P = P[(P["split_seed"] == 0) & (P["n"].astype(str) == "main") & (P["family"] == "physics")].set_index("pilot")["s0"]
    st = [k.split(":", 1)[1] for k in P.index if str(k).startswith("s0map:")]
    s0 = CE.local_s0(pool, test_households(pool.meta, pool.meta, 0, cfg["split"])["train_fill"], st)
    assert len(s0) == len(st) >= 3
    for k, v in s0.items():
        assert abs(v - P[f"s0map:{k}"]) <= 1e-12 * abs(v)


def _permuted_pool(orig):
    def yp(path, seed):
        pool, cfg = orig(path, seed)
        hp = pool.meta.index[pool.meta["role"] == "hp"]
        pool.meta.loc[hp, "hp_peak"] = np.random.default_rng(11).permutation(pool.meta.loc[hp, "hp_peak"].to_numpy())
        return pool, cfg
    return yp


def _check_permutation(tmp_path, monkeypatch, names):
    a = CE.run_seed(tiny_cfg(tmp_path / "a", names), 0)["preds"]
    monkeypatch.setattr(CE, "year_pool", _permuted_pool(CE.year_pool))
    b = CE.run_seed(tiny_cfg(tmp_path / "b", names), 0)["preds"]
    assert len(a) and (a["feeder_id"] == b["feeder_id"]).all()
    assert not np.allclose(a["C2"], b["C2"])                            # the labels did change
    assert (a["dhat"].to_numpy() == b["dhat"].to_numpy()).all() and (a["P1"].to_numpy() == b["P1"].to_numpy()).all()


def test_label_permutation_physics(tmp_path, monkeypatch):
    _check_permutation(tmp_path, monkeypatch, [])


@SLOW
def test_label_permutation_tabpfn(tmp_path, monkeypatch):
    _check_permutation(tmp_path, monkeypatch, ["E1", "E4"])


@SLOW
def test_e1_reproduces_06_on_06_test_substations():
    from paperb.run_benchmark import cached_eval
    from paperb.splits import grouped_inner_folds, household_splits
    from paperb.substations import build_substations
    from paperb.train import configure
    configure(4)
    for seed in (0, 3):                                                 # anchors size (s0) and size_peak (s3)
        pool, cfg = CE.year_pool("configs/iter06_a_gb.yaml", seed)
        sp = household_splits(pool.meta, [seed], cfg["split"]["test_frac"], cfg["split"]["stratify"])[seed]
        mem = build_substations(pool.meta, sp, seed, cfg, grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], seed))[0]
        tab, X, _ = cached_eval(pool, mem, cfg, seed, print)              # the 06 memberships: the 06 feature cache
        te = tab.index[tab["split"] == "test"]
        tab, X = tab.loc[te], X.loc[te]
        p = CE.ml_estimates(tab, X, seed, ["E1"])[0]["E1"][0]
        ref = pd.read_parquet(CE.DIR06_MODELS / "L2" / f"s{seed}" / "neural" / "pred_refit.parquet")["pred"].reindex(tab.index)
        assert ref.notna().all()
        y = tab["HP_Peak"].to_numpy(float)
        wape = lambda q: 100 * np.abs(q - y).sum() / y.sum()            # noqa: E731
        assert abs(wape(p) - wape(ref.to_numpy())) <= 1e-3
