"""Iteration 05a invariants (Tasks 1-3): analog mapping rules, one source day per substation-day, toy composition and
labels, GB-ENG calendar, LCL Std-only filler and disjoint filler splits, EoH eligibility, D4 candidate exclusion, D5
swap memberships and the +-3 d exclusion, and the B* regression against 03b. Tests that need the pool caches
(data/_paperb/pools/{gb_eoh_2122r3,lcl_std_*,bstar_2023}*) are skipped without them."""
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
from paperb import fill_analog as FA  # noqa: E402
from paperb import run_benchmark as RB  # noqa: E402
from paperb.physics import daily_means, fit_daily  # noqa: E402
from paperb.pools import Pool, build_pool  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import build_substations, evaluate_members  # noqa: E402

POOLS = ROOT / "data" / "_paperb" / "pools"
EOH_CFG = load_config("configs/pool_gb_eoh_2122.yaml")
needs_eoh = pytest.mark.skipif(not (POOLS / "gb_eoh_2122r3_meta.parquet").exists() or not list(POOLS.glob("lcl_std_*.npy")),
                               reason="GB-EoH / LCL caches not built")
needs_bstar = pytest.mark.skipif(not (POOLS / "bstar_2023_meta.parquet").exists(), reason="B* pool cache not built")
FC = {"doy_windows": [30, 45, 60], "tol_K": 1.0, "k_nearest": 3}


def days_frame(a, b, cal="GB-ENG", seed=0):
    d = pd.date_range(a, b, freq="D")
    T = 10 - 8 * np.cos(2 * np.pi * (d.dayofyear - 20) / 365) + np.random.default_rng(seed).normal(0, 2, len(d))
    return pd.DataFrame({"date": d, "T": T, "we": FA.day_type(d, cal)})


def test_gb_eng_calendar_2022_bank_holidays():
    d = pd.date_range("2022-05-30", "2022-09-20", freq="D")
    we = dict(zip(d.date, FA.day_type(d, "GB-ENG")))
    assert we[date(2022, 6, 2)] and we[date(2022, 6, 3)] and we[date(2022, 9, 19)]      # Platinum Jubilee, state funeral
    assert not we[date(2022, 6, 1)] and not we[date(2022, 9, 20)] and not we[date(2022, 6, 6)]
    assert we[date(2022, 8, 29)] and we[date(2022, 6, 4)]                               # late summer bank holiday, Saturday


def test_analog_map_day_type_window_tolerance_and_determinism():
    cand, tgt = days_frame("2012-07-01", "2014-02-27"), days_frame("2021-10-01", "2022-09-30", seed=1)
    m = FA.analog_map(tgt, cand, np.random.default_rng([0, 4]), (30, 45, 60), 1.0, 3)
    src = cand.iloc[m["src"]]
    assert (src["we"].to_numpy() == tgt["we"].to_numpy()).all()                        # same day type
    lim = np.array([30, 45, 60, 60])[m["widen"]]
    assert (m["ddoy"].to_numpy() <= lim).all()                                          # day-of-year window
    assert (m.loc[m["widen"] < 3, "dT"].abs() <= 1.0).all()                             # temperature tolerance
    np.testing.assert_allclose(np.abs(src["T"].to_numpy() - tgt["T"].to_numpy()), m["dT"].abs())
    again = FA.analog_map(tgt, cand, np.random.default_rng([0, 4]), (30, 45, 60), 1.0, 3)
    other = FA.analog_map(tgt, cand, np.random.default_rng([1, 4]), (30, 45, 60), 1.0, 3)
    assert again.equals(m) and not other["src"].equals(m["src"])                       # deterministic given the seed


def toy_analog(n_hh=6, seed=0):
    """AnalogFill on a 30-min UTC index over the March 2022 DST change; S[h, day, slot] = 1000 h + day."""
    cand = days_frame("2012-07-01", "2014-02-27").assign(pos=lambda d: np.arange(len(d)))
    S = (1000.0 * np.arange(n_hh)[:, None, None] + np.arange(len(cand))[None, :, None]) * np.ones((1, 1, 48))
    idx = pd.date_range("2022-03-20", "2022-04-03", freq="30min", inclusive="left")
    temp = pd.DataFrame({"G1": np.full(len(idx), 6.0), "G2": np.full(len(idx), 12.0)}, index=idx)
    targets, t_day, t_slot = FA.station_targets(idx, temp, FA.TZ_GB, "GB-ENG", 30)
    a = FA.AnalogFill(S, [f"L:{i}" for i in range(n_hh)], cand, targets, t_day, t_slot, FC)
    a.set_seed(seed)
    return a, idx, temp


def test_one_source_day_per_substation_day_and_local_clock():
    a, idx, _ = toy_analog()
    members = ["L:1", "L:3", "L:4"]
    agg = pd.Series(a.aggregate(members, "G1"), index=idx)
    src_day = agg - 1000 * (1 + 3 + 4)
    loc_day = idx.tz_localize("UTC").tz_convert(FA.TZ_GB).normalize()
    per_day = (src_day / 3).groupby(loc_day).nunique()
    assert (per_day == 1).all()                                                          # one d' per substation-day
    exp = a.cand["pos"].to_numpy()[a.maps["G1"]["src"].to_numpy()]
    np.testing.assert_allclose((src_day / 3).groupby(loc_day).first().to_numpy(), exp)
    np.testing.assert_allclose(agg, sum(a.aggregate([h], "G1") for h in members))       # fillers share d'
    dst = loc_day == pd.Timestamp("2022-03-27", tz=FA.TZ_GB)
    assert dst.sum() == 46 and not set(a.t_slot[dst]) & {2, 3}                          # 23-h day skips 01:00, 01:30


def test_fill_gaps_interpolates_short_and_donates_long():
    X = np.tile(np.arange(48.0), (4, 1)) + np.array([[0], [100], [200], [300]])
    X[0, 10:12] = np.nan                                                                 # 1 h gap -> interpolated
    X[2, 5:20] = np.nan                                                                  # 7.5 h gap -> donor day
    Y, n = FA.fill_gaps(X, np.array([False, False, False, True]), np.array([5.0, 9.0, 8.0, 8.0]), 4)
    np.testing.assert_allclose(Y[0, 10:12], [10, 11])
    np.testing.assert_allclose(Y[2, 5:20], X[1, 5:20])                                  # same day type, nearest T (9 vs 5)
    assert n == 1


def test_toy_composition_net_is_fillers_plus_hp_and_labels():
    a, idx, temp = toy_analog()
    rng = np.random.default_rng(3)
    hp = pd.DataFrame({f"E:{i}": rng.gamma(2, 0.5, len(idx)) * (1 + (temp["G1"].to_numpy() < 8)) for i in range(3)}, index=idx)
    meta = pd.DataFrame({"role": "hp", "station": "G1", "hp_peak": hp.quantile(0.999)}, index=hp.columns)
    pool = Pool("gb_eoh", hp, hp * 0.0, pd.DataFrame(index=idx), temp, meta)
    pool.analog = a
    members = pd.DataFrame({"station": ["G1"], "size": [5], "n_hp": [2], "hp_members": [["E:0", "E:2"]],
                            "fill_members": [["L:0", "L:1", "L:2", "L:3", "L:5"]]}, index=["s0"])
    cfg = {"target_defs": {"T_design_C": -3.0}, "pool": {"holidays": "GB-ENG"}}
    tab, _ = evaluate_members(pool, members, cfg, with_features=False)
    net = hp[["E:0", "E:2"]].sum(axis=1).to_numpy() + a.aggregate(members.at["s0", "fill_members"], "G1")
    assert tab.at["s0", "peak"] == pytest.approx(net.max(), rel=1e-12)                  # net = sum fillers + sum HP
    assert tab.at["s0", "HP_Peak"] == pytest.approx(meta.loc[["E:0", "E:2"], "hp_peak"].sum())
    assert tab.at["s0", "HP_CoincPeak"] == pytest.approx(hp[["E:0", "E:2"]].sum(axis=1).max())
    assert tab.at["s0", "HP_Count"] == 2


@needs_eoh
def test_filler_is_std_only_and_splits_disjoint():
    pool = build_pool("gb_eoh", EOH_CFG, verbose=False)
    fill = pool.meta.index[pool.meta["role"] == "fill"]
    assert len(fill) and all(h.startswith("L:N") for h in fill)                         # consumption_n = Std; ToU ids are D....
    _, _, lmeta, audit = FA.build_lcl(EOH_CFG["pool"]["fill"], verbose=False)
    assert not any(h.startswith("L:D") for h in lmeta.index) and audit["tou_households"] > 0
    for seed, sp in household_splits(pool.meta, range(5), 0.25).items():
        tr, te = set(sp["train"]["fill"]), set(sp["test"]["fill"])
        assert not tr & te and tr | te == set(fill)


@needs_eoh
def test_eoh_eligibility_and_one_filler_per_dwelling():
    pool = build_pool("gb_eoh", EOH_CFG, verbose=False)
    hp = pool.meta[pool.meta["role"] == "hp"]
    assert (hp["coverage"] >= EOH_CFG["pool"]["coverage_min"]).all()
    assert set(hp["type"]) <= {"ASHP", "HT-ASHP", "GSHP"}
    units = pd.read_parquet(ROOT / "data" / "_paperb" / "iter04" / "eoh_units.parquet").set_index("property")
    assert (units.loc[[h[2:] for h in hp.index], "type"] != "hybrid").all()
    cfg = copy.deepcopy(EOH_CFG)
    sp = household_splits(pool.meta, [0], 0.25)[0]
    mem, _ = build_substations(pool.meta, sp, 0, cfg, grouped_inner_folds(sp["train"], pool.meta, 4, 0))
    assert (mem["fill_members"].map(len) == mem["size"]).all()                          # HP dwellings get a filler too
    te = mem[mem["split"] == "test"]
    assert not set().union(*te["fill_members"]) & set(sp["train"]["fill"])             # train fillers never in test


@needs_eoh
def test_d4_heldout_winter_is_never_its_own_candidate():
    from paperb.iter05a_report import d4_candidates
    _, D, _, _ = FA.build_lcl(EOH_CFG["pool"]["fill"], verbose=False)
    for winter in (2012, 2013):
        tgt, cand = d4_candidates(D, winter)
        assert len(tgt) >= 60 and not set(tgt["date"]) & set(cand["date"])
        held = (cand["date"] >= f"{winter}-11-01") & (cand["date"] < f"{winter + 1}-04-01")
        assert not held.any()


@needs_bstar
def test_d5_swap_keeps_members_and_excludes_near_days():
    cfg = load_config("configs/iter05a_d5_swap.yaml")
    pool = build_pool("bstar", cfg, verbose=False)
    pool.analog.set_seed(0)
    real = load_config("configs/iter05a_d5_real.yaml")
    sp = household_splits(pool.meta, [0], 0.25)[0]
    folds = grouped_inner_folds(sp["train"], pool.meta, 4, 0)
    m_real, _ = build_substations(pool.meta, sp, 0, real, folds)
    m_swap = FA.add_own_fillers(m_real, sp, folds, 0)
    assert m_swap.index.equals(m_real.index) and m_swap["split"].equals(m_real["split"])
    assert m_swap["hp_members"].equals(m_real["hp_members"])
    for r_, s_ in zip(m_real.itertuples(), m_swap.itertuples()):
        assert set(r_.fill_members) < set(s_.fill_members) and len(s_.fill_members) == s_.size
        pool_ = sp["test" if s_.split == "test" else "train"]["fill"]
        assert set(s_.fill_members) <= set(pool_)
        if s_.split == "inner":
            assert (folds[list(s_.fill_members)] == s_.fold).all()
    for st, mp in pool.analog.maps.items():
        dd = (pool.analog.cand["date"].to_numpy()[mp["src"].to_numpy()] - pool.analog.targets[st]["date"].to_numpy()) / np.timedelta64(1, "D")
        assert (np.abs(dd) > 3).all()                                                   # +-3 d excluded


@needs_bstar
def test_bstar_seed0_reproduces_03b():
    """B* under protocol v1 (03b main config, restricted to Lasso + every physics row): seed-0 metrics equal 03b's, and
    freshly evaluated substations equal the cached 03b features (the 05a changes to substations.py are inert on B*)."""
    cfg = load_config("configs/iter03b_main.yaml")
    cfg.update(models=["Lasso"], residual_models=["Lasso"], model_anchors={}, anchors=["size"], target_transforms=["none"],
               anchor_only_baselines={"models": ["Linear"], "features": [["size"], ["peak"], ["size", "peak"]]})
    cfg["parallel"]["threads"] = 4
    res = RB.run_seed(cfg, 0)
    ref = pd.read_csv(ROOT / "results" / "iter03b_fair_test" / "arm_main" / "metrics.csv.gz")
    ref = ref[(ref["split_seed"] == 0) & (ref["metric"] == "wape")]
    key = ["method", "anchor", "feature_set", "mode", "target_transform", "cell"]
    got = res["metrics"][res["metrics"]["metric"] == "wape"].astype({c: str for c in key})
    j = got.merge(ref.astype({c: str for c in key}), on=key, suffixes=("", "_03b"))
    assert len(j) == len(got) > 50 and {"paperA_corr", "paperA_cal", "slope_base", "Lasso"} <= set(j["method"])
    np.testing.assert_allclose(j["value"], j["value_03b"], rtol=1e-9, atol=1e-12)
    pool = build_pool("bstar", cfg, verbose=False)
    sp = household_splits(pool.meta, [0], cfg["split"]["test_frac"])[0]
    folds = grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], 0)
    members, _ = build_substations(pool.meta, sp, 0, cfg, folds)
    tab, X, _ = RB.cached_eval(pool, members, cfg, 0, lambda m: None)
    sub = members[members["split"] == "test"].iloc[::25]
    t2, X2 = evaluate_members(pool, sub, cfg)
    num = [c for c in tab.columns if c not in ("split", "station", "split_seed", "fold") and pd.api.types.is_numeric_dtype(tab[c])]
    pd.testing.assert_frame_equal(t2[num].astype(float), tab.loc[sub.index, num].astype(float), check_exact=False, rtol=1e-12)
    pd.testing.assert_frame_equal(X2[X.columns], X.loc[sub.index], check_exact=False, rtol=1e-12)
