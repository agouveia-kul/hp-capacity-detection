"""Iteration 07 (transfer validation), Task 2 tests (a)-(e) of the brief, on the real 06 caches and persisted models.

(a) no target label reaches any fit; (b) c comes from source train rows only; (c) round trip: a pool's models on its own 06
test set reproduce the 06 predictions (physics and linear here; TabPFN and CNN with PAPERB_SLOW=1); (d) the 30-min rebuild of
CH aggregates leaves the daily-mean features unchanged; (e) seed pairing s -> s. No transfer error metric is computed.
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

import paperb.transfer as T  # noqa: E402
from paperb.labels_hl import substation_labels  # noqa: E402
from paperb.run_benchmark import SPEC_COLS  # noqa: E402
from paperb.substations import evaluate_members  # noqa: E402

LINEAR = ["Linear", "Ridge", "Lasso", "ElasticNet", "PLS"]


def job_cfg(source, target=None, families=("physics", "linear"), roundtrip=False, seed_threads=2):
    cfg = T.arm_cfg(source)
    cfg["transfer"] = {"source": source, "target": target, "roundtrip": roundtrip}
    cfg["parallel"] = {**cfg.get("parallel", {}), "threads": seed_threads}
    if "physics" not in families:
        cfg["physics_baselines"] = []
    ml = {"linear": LINEAR, "tabpfn": ["TabPFN"], "cnn": ["CNN"]}
    cfg["models"] = sum((ml[f] for f in families if f in ml), [])
    cfg["residual_models"] = list(cfg["models"])
    cfg["modes"] = ["direct", "residual", "l4a"]
    return cfg


def roundtrip_check(arm, seed, families, tol_pp=0.001):
    res = T.run_seed(job_cfg(arm, families=families, roundtrip=True), seed)
    P = res["preds"]
    ref = pd.read_csv(T.DIR06 / arm / "predictions.csv")
    ref = ref[ref["split_seed"] == seed]
    K = ["sub_id", *SPEC_COLS]
    m = P.merge(ref[K + ["pred"]], on=K, suffixes=("", "_06"))
    assert len(m) == len(P) and len(P), "every round-trip row has its 06 prediction"
    for k, g in m.groupby(SPEC_COLS):
        d_pp = 100 * (np.abs(g["pred"] - g["y"]).sum() - np.abs(g["pred_06"] - g["y"]).sum()) / g["y"].sum()
        assert abs(d_pp) <= tol_pp, (k, d_pp)
    return res


@pytest.fixture(scope="module")
def ch_to_gb():
    """CH->GB, seed 0, physics + linear; and the same with the target's labels permuted."""
    seed = 0
    plain = T.run_seed(job_cfg("a_ch", "a_gb"), seed)
    side0 = T.side

    def permuted(arm, sd, **kw):
        s = side0(arm, sd, **kw)
        if arm == "a_gb":
            rng = np.random.default_rng(1)
            s["caps"] = s["caps"].copy()
            s["caps"][["native", "hl"]] = s["caps"][["native", "hl"]].to_numpy()[rng.permutation(len(s["caps"]))]
            s["tab"] = s["tab"].assign(HP_Peak=s["tab"]["HP_Peak"].to_numpy()[rng.permutation(len(s["tab"]))])
        return s

    T.side = permuted
    try:
        perm = T.run_seed(job_cfg("a_ch", "a_gb"), seed)
    finally:
        T.side = side0
    return seed, plain, perm


def test_a_target_labels_never_reach_a_fit(ch_to_gb):
    _, plain, perm = ch_to_gb
    K = ["sub_id", *SPEC_COLS, "label_def"]
    a, b = plain["preds"].set_index(K).sort_index(), perm["preds"].set_index(K).sort_index()
    assert a.index.equals(b.index)
    assert np.array_equal(a["pred"].to_numpy(), b["pred"].to_numpy())           # bit-identical
    assert not np.allclose(a["y"].to_numpy(), b["y"].to_numpy())                # the labels did change


def test_b_c_from_source_train_rows_only(ch_to_gb):
    seed, plain, _ = ch_to_gb
    src = T.side("a_ch", seed)
    tr = src["members"]["split"] == "train"
    lab = substation_labels(src["members"][tr], src["caps"])
    assert np.isclose(plain["preds"]["c_src"].iloc[0], float((lab["HL"] / lab["native"]).median()))
    test_hh = sorted(set().union(*src["members"].loc[src["members"]["split"] == "test", "hp_members"]))
    caps = src["caps"].copy()
    caps.loc[test_hh, "hl"] *= 0.5                                              # source test labels: no effect on c
    assert T.c_source({**src, "caps": caps}) == T.c_source(src)
    hl = plain["preds"].query("label_def == 'HL'")["pred"].to_numpy()
    raw = plain["preds"].query("label_def == 'HL_uncorrected'")["pred"].to_numpy()
    assert np.allclose(hl, plain["preds"]["c_src"].iloc[0] * raw)


def test_e_pairing_s_to_s(ch_to_gb):
    seed, plain, _ = ch_to_gb
    assert (plain["preds"]["split_seed"] == seed).all()
    assert plain["preds"]["sub_id"].str.startswith(f"{seed}|test|").all()     # the target seed's 06 test substations
    dirs = plain["diag"]["dir"].dropna()
    assert len(dirs) and dirs.str.contains(rf"[\\/]s{seed}[\\/]", regex=True).all() and dirs.str.contains("a_ch").all()
    assert set(plain["preds"]["direction"]) == {"CH->GB"}


@pytest.mark.parametrize("arm", ["a_gb", "a_ch"])
def test_c_roundtrip_physics_linear(arm):
    roundtrip_check(arm, 0, ("physics", "linear"))


@pytest.mark.skipif(not os.environ.get("PAPERB_SLOW"), reason="slow (TabPFN refits its context): set PAPERB_SLOW=1")
@pytest.mark.parametrize("arm", ["a_gb", "a_ch"])
def test_c_roundtrip_tabpfn_cnn(arm):
    roundtrip_check(arm, 0, ("tabpfn", "cnn"))


def test_d_30min_rebuild_keeps_daily_mean_features():
    cfg = T.arm_cfg("a_ch")
    from paperb.pools import build_pool
    pool = build_pool("bstar", cfg, verbose=False)
    src = T.side("a_ch", 0)
    mem = src["members"][src["members"]["split"] == "test"].iloc[::30]
    t15, f15 = evaluate_members(pool, mem, cfg)
    t30, f30 = evaluate_members(T.at_30min(pool), mem, cfg)
    daily = [c for c in f15.columns if c.startswith(("nf_", "rs_"))]
    assert len(daily) > 700
    ycol = [c for c in daily if c.startswith("rs_y_")]
    np.testing.assert_array_equal(f30[ycol].to_numpy(float), f15[ycol].to_numpy(float))         # net-load daily means: exact
    # the pool stores temperature as float32 and pandas averages it in float32 at 15 min: <= 1e-7 relative (seen 8.9e-8)
    np.testing.assert_allclose(f30[daily].to_numpy(float), f15[daily].to_numpy(float), rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(t30[["s_h_net", "P_base_net", "T_h_net"]].to_numpy(float),
                               t15[["s_h_net", "P_base_net", "T_h_net"]].to_numpy(float), rtol=1e-6)
    assert (t30["peak"] <= t15["peak"] + 1e-9).all()                            # a sub-daily input does move (reported shift)


def test_doy_perm_aligns_calendars():
    p = T.doy_perm("2023-01-01", "2021-11-01")                                  # CH source day i -> GB target day
    assert p[0] == 61 and p[-1] == 60 and sorted(p) == list(range(365))         # 1 Jan = day 61 of Nov-Oct; 31 Dec = day 60
    assert (T.doy_perm("2021-11-01", "2021-11-01") == np.arange(365)).all()


RUNNER = '''import time
import pandas as pd


def run_seed(cfg, seed):
    time.sleep(float(cfg.get("toy_sleep", 0)))
    return {"metrics": pd.DataFrame([{"exp_id": "toy", "split_seed": seed, "dataset": "toy", "target": "HP_Peak", "method": m,
                                      "anchor": "size", "feature_set": "-", "mode": "direct", "target_transform": "none", "cell": "all",
                                      "metric": "wape", "value": 1.0, "n_substations": 1, "n_hp_households": 1} for m in cfg["models"]])}
'''


def test_watchdog_kills_a_blocked_job_on_time_and_spares_the_others(tmp_path):
    """Task 3: a job blocked in one native call (time.sleep) past its limit is killed within the grace period, not when the call
    returns (06: up to 2.5 h late); a job running beside it finishes; a relaunch never retries the killed job in a loop."""
    import time
    import yaml
    from paperb import run_queue as RQ
    (tmp_path / "toy07_runner.py").write_text(RUNNER)
    arm = {"name": "a", "config": "tests/fixtures/toy_queue_arm.yaml", "runner": "toy07_runner:run_seed", "seeds": [0],
           "families": ["blocked", "ok"]}
    q = {"exp_id": "toy07", "out_dir": str(tmp_path / "out"), "workers": 2, "threads": 1, "sys_path": [str(tmp_path)],
         "watchdog": True, "watchdog_grace_s": 2,
         "families": {"blocked": {"models": ["Lasso"], "set": ["toy_sleep=120"], "timeout_s": 1},
                      "ok": {"models": ["Ridge"], "set": ["toy_sleep=8"]}}, "arms": [arm]}
    cfg = tmp_path / "toy07.yaml"
    cfg.write_text(yaml.safe_dump(q))
    t0 = time.time()
    prog = RQ.main(["--config", str(cfg)])
    took = time.time() - t0
    J = tmp_path / "out" / "jobs"
    assert prog == {**prog, "done": 1, "failed": 1, "remaining": 0}
    txt = (J / "a__s0__d0__nall__blocked.failed").read_text()
    assert txt.startswith("reason: timeout") and "killed by the watchdog" in txt
    assert (J / "a__s0__d0__nall__ok.done").exists()
    assert took < 60, took                                                       # killed at ~1 + 2 s, not after the 120 s call
    assert RQ.main(["--config", str(cfg)])["failed"] == 1
