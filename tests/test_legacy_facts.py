"""Legacy facts (iteration 00) that later iterations must not change silently.

Values are pinned from results/iter00_baseline/facts.md. The tests read the
shared data/ caches (skipped if data/ is absent) and the small parquet extracts
that scripts/legacy_facts.py writes to data/_paperb/iter00/.
"""
import hashlib
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

pytestmark = pytest.mark.skipif(not (ROOT / "data" / "_regen_prep.pkl").exists(),
                                reason="shared data/ folder not available")

import legacy_facts as lf  # noqa: E402

SEED = 42


@pytest.fixture(scope="module")
def prep():
    return lf.load_prep()


@pytest.fixture(scope="module")
def members():
    return lf.load_members()


def _pool(name):
    with open(ROOT / "data" / name, "rb") as fh:
        return pickle.load(fh)


# ------------------------------------------------------------------ pools ----
def test_heapo_legacy_pool(prep):
    assert len(prep) == 57
    assert prep["Weather_ID"].value_counts().to_dict() == {"8jB": 26, "Hg": 21, "MqO": 6, "HbsbG": 3, "z6I": 1}


@pytest.mark.parametrize("name, n_hp, n_consumers", [
    ("_design_pool_cache.pkl", 57, 58),
    ("_swiss_pool_cache.pkl", 24, 1644),
    ("_combined_pool_cache.pkl", 81, 1702),
    ("_wpuq_pool_cache.pkl", 37, 37),
])
def test_pool_sizes(name, n_hp, n_consumers):
    pool = _pool(name)
    assert len(pool["hp_households"]) == n_hp
    assert len(pool["households"]) == n_consumers


def test_design_pool_is_legacy_pool(prep):
    assert set(map(int, _pool("_design_pool_cache.pkl")["hp_households"])) == set(map(int, prep.index))


# ------------------------------------------------------------------ split ----
def test_split_reproducible_from_seed(prep, members):
    train, test = lf.legacy_split(prep, SEED)
    assert (len(train), len(test)) == (29, 28)
    assert not train & test
    for split, pool in (("train", train), ("test", test)):
        m = members[members["split"] == split]
        used = {h for col in ("households_hp", "households") for l in m[col] for h in l}
        assert used <= pool


def test_split_is_deterministic(prep):
    assert lf.legacy_split(prep, SEED) == lf.legacy_split(prep, SEED)


# ----------------------------------------------------------------- design ----
def test_design_grid(members):
    assert members["split"].value_counts().to_dict() == {"train": 1080, "test": 1080}
    cells = members.groupby(["split", "HP_ratio", "size"]).size()
    assert len(cells) == 2 * 10 * 12 and (cells == 9).all()


def test_membership_replay_matches_legacy(prep, members):
    rep = lf.replay_membership(prep, SEED)
    assert rep["weather_id"].tolist() == members["weather_id"].tolist()
    assert all(list(a) == list(b) for a, b in zip(rep["households_hp"], members["households_hp"]))
    assert all(list(a) == list(b) for a, b in zip(rep["households"], members["households"]))


def test_hp_peak_is_sum_of_robust_member_peaks(prep, members):
    peak = prep["HP_robust_kW"].to_dict()
    recomputed = np.array([sum(peak[h] for h in l) for l in members["households_hp"]])
    np.testing.assert_allclose(recomputed, members["HP_Peak"].to_numpy(), rtol=1e-6, atol=1e-6)


def test_stacking_in_largest_train_substations(members):
    big = members[(members.split == "train") & (members["size"] == 120) & (members.HP_ratio == 1.0)]
    reps = big["households_hp"].apply(lambda l: len(l) / len(set(l)))
    assert reps.mean() == pytest.approx(16.7, abs=0.05)


# ----------------------------------------------------- read-only artefacts ----
@pytest.mark.parametrize("rel, md5", [
    ("models/xgb_selected_features.json", "9777b047cebc91fe75234e890db7076b"),
    ("models/hockey_delta_calibration.json", "cc91ca3750e26f5e64a38f38d6f8a72a"),
    ("models/capacity_swiss.pkl", "4313e7344b6387b4cddb9cf313af8e00"),
    ("data/capacity_model_benchmark.csv", "d825e37ea41005b7a73ae879fc172612"),
    ("data/xgb_hockey_ci_metrics.csv", "00089c53872da1a9c4eb77250721ecb0"),
    ("data/_X_swiss_pooled.pkl", "9408199b73cfa04ea16660ff107d6e11"),
])
def test_legacy_artefacts_unchanged(rel, md5):
    assert hashlib.md5((ROOT / rel).read_bytes()).hexdigest() == md5
