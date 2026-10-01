"""Iteration 05a-ii invariants: the EoH zero-run rule (R8), the station-T fill (R5), the window candidates (R2), the London
temperature (R4), the D5 own-station matching (R6) and the D4 diagnostics helpers (pre-registered verdict rule)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from paperb import fill_analog as FA  # noqa: E402
from paperb.d4_diagnostics import cap_equiv, slopes, verdict  # noqa: E402
from paperb.pools import gb_eoh as G  # noqa: E402


def test_zero_run_rule_keeps_real_switch_offs_and_flags_dropouts():
    n = 200
    P, Q, T = np.full((n, 3), 0.5), np.zeros((n, 3)), np.full((n, 3), 5.0)
    P[20:50, 0] = 0.0                                  # col 0: 15 h zero run, heat meter active inside it -> dropout
    Q[30, 0] = 3.0
    P[20:50, 1] = 0.0                                  # col 1: zero run with no heat anywhere near -> real switch-off
    P[20:50, 2] = 0.0                                  # col 2: zero run; heat is delivered within 12 h with silent electricity -> dropout
    P[60:62, 2], Q[60:62, 2] = 0.005, 4.0
    P[110:120, 0] = 0.0                                # col 0: a short (5 h) zero run is never flagged
    Q[112, 0] = 3.0
    zr = G._zero_runs(P, Q, T)
    assert zr[20:50, 0].all() and not zr[:20, 0].any() and not zr[110:120, 0].any()
    assert not zr[:, 1].any()
    assert zr[20:50, 2].all() and not zr[50:, 2].any()
    T_warm = np.full((n, 3), 15.0)                     # a run starting on a day at or above 12 degC is not flagged
    assert not G._zero_runs(P, Q, T_warm).any()


def test_station_fill_uses_best_correlated_unflagged_station_else_drops():
    idx = pd.date_range("2022-01-01", periods=48 * 200, freq="30min")
    rng = np.random.default_rng(0)
    base = 8 + 6 * np.sin(np.arange(len(idx)) / 48 / 12) + rng.normal(0, 0.3, len(idx))
    Tw = pd.DataFrame({"A": base, "B": 1.0 + 0.97 * base + rng.normal(0, 0.05, len(idx)), "C": rng.normal(8, 4, len(idx))}, index=idx)
    Tw.iloc[:48 * 20, 1] = np.nan                      # B misses 10 % of its bins and tracks A (corr ~ 1)
    Tw.iloc[:48 * 20, 2] = np.nan                      # C misses 10 % and is unrelated to A (corr ~ 0)
    filled, log, dropped = G._station_fill(Tw)
    assert dropped == ["C"] and log.set_index("station").loc["B", "action"] == "filled" and log.set_index("station").loc["B", "donor"] == "A"
    assert filled["B"].notna().all() and filled["C"].isna().any()
    expect = 1.0 + 0.97 * base[: 48 * 20]
    assert np.abs(filled["B"].to_numpy()[: 48 * 20] - expect).max() < 0.3           # the linear bias correction is recovered
    np.testing.assert_allclose(filled["A"], Tw["A"])                                # unflagged stations are untouched


def test_window_candidates_end_by_the_last_admissible_date():
    main = G._starts({"first": "2021-06-01", "last_start": "2022-01-01"}, pd.Timestamp("2023-09-29"))
    assert [s.strftime("%Y-%m") for s in main] == ["2021-06", "2021-07", "2021-08", "2021-09", "2021-10", "2021-11", "2021-12", "2022-01"]
    rep = G._starts({"first": "2020-11-01", "last_end": "2023-09-29"}, pd.Timestamp("2023-09-29"))
    assert rep[0] == pd.Timestamp("2020-11-01") and rep[-1] == pd.Timestamp("2022-09-01")             # Oct 2022 would end on 30 Sep 2023
    assert all(s + pd.DateOffset(months=12) - pd.Timedelta("30min") <= pd.Timestamp("2023-09-29") for s in rep)


@pytest.mark.skipif(not FA.HEATHROW.exists(), reason="Meteostat file not downloaded")
def test_london_temperature_is_heathrow_and_complete_over_the_lcl_window():
    h, c = FA.heathrow(), FA.hadcet()
    days = pd.date_range("2012-07-01", "2014-02-27", freq="D")
    assert h.reindex(days).notna().all() and -15 < h.min() and h.max() < 40
    assert 0.95 < np.corrcoef(h.reindex(days), c.reindex(days).interpolate())[0, 1] < 1.0            # London vs Central England: close, not equal
    assert FA.lcl_temperature("heathrow").equals(h) and FA.lcl_temperature("hadcet").equals(c)


def test_per_station_candidate_temperature_is_used_in_the_map():
    cand = pd.DataFrame({"date": pd.date_range("2022-01-01", periods=120, freq="D"), "T": 0.0})
    cand["we"] = FA.day_type(cand["date"], "CH-ZH")
    cand["pos"] = np.arange(len(cand))
    tgt = cand.iloc[[60]].assign(T=10.0).reset_index(drop=True)
    Tg = np.where(np.arange(120) == 75, 10.0, -20.0)                                   # only day 75 matches the target on the station's own T
    cand["we"] = tgt["we"].iloc[0]                                                     # day type cannot decide
    a = FA.AnalogFill(np.zeros((1, 120, 48)), ["h"], cand, {"g": tgt}, np.zeros(48, int), np.arange(48), {"doy_windows": [30], "tol_K": 1.0, "k_nearest": 1},
                      exclude_days=3, cand_T={"g": Tg})
    a.set_seed(0)
    assert int(a.maps["g"]["src"].iloc[0]) == 75


def test_d4_diagnostics_rule_slopes_and_capacity_equivalent():
    T = np.linspace(-2, 20, 120)
    y = 1.0 + 0.3 * np.maximum(16 - T, 0)
    s = slopes(T, y, 16.0)
    assert s["a"] == pytest.approx(0.3, rel=1e-2) and s["b"] == pytest.approx(0.3, rel=1e-6) and s["c"] == pytest.approx(0.3, rel=1e-6)
    ns = (10, 40, 120)
    mk = lambda v: {n: v for n in ns}                                                  # noqa: E731
    assert verdict(mk(0.5), mk(0.9), mk(1.0), mk(1.0)) == "intrinsic filler variability"            # Y >= 0.5 E
    assert verdict(mk(0.1), mk(0.9), mk(0.5), mk(0.3)) == "mapping defect"                            # Y < 0.5 E and (b), (c) > 25 %
    assert verdict(mk(0.1), mk(0.9), mk(0.2), mk(0.3)) == "inconclusive"
    t = cap_equiv({10: 0.05, 40: 0.2}, m_h=0.025, hp_med=3.0, sizes=(10, 40), ps=(0.5, 1.0))
    assert t.loc[10, 0.5] == pytest.approx(100 * 0.05 / (0.025 * 0.5 * 10 * 3.0)) and t.loc[40, 1.0] < t.loc[40, 0.5]


def test_replication_window_is_clipped_to_the_last_full_day():
    pc = {"last_day": "2023-09-28", "windows": {"first": "2022-10-01", "last_start": "2022-10-01"}}
    s = G._starts(pc["windows"], pd.Timestamp("2023-09-29"))
    assert s == [pd.Timestamp("2022-10-01")]                                                          # a start whose 12 months run past the data is kept
    assert G._window_end(s[0], pc) == pd.Timestamp("2023-09-29")                                      # ... and clipped: 1 Oct 2022 - 28 Sep 2023, 363 days
    assert (G._window_end(s[0], pc) - s[0]).days == 363
    assert G._window_end(pd.Timestamp("2021-11-01"), {}) == pd.Timestamp("2022-11-01")


POOLS = ROOT / "data" / "_paperb" / "pools"


@pytest.mark.skipif(not (POOLS / "gb_eoh_2223r3_meta.parquet").exists() or not (POOLS / "gb_eoh_2122r3_meta.parquet").exists(), reason="GB-EoH caches not built")
def test_pools_exclude_silent_electricity_homes_and_replication_has_enough_homes():
    main, rep = (pd.read_parquet(POOLS / f"gb_eoh_{t}_meta.parquet") for t in ("2122r3", "2223r3"))
    for m in (main, rep):
        assert (m["silent_elec_share"] <= 0.05).all() and (m["coverage"] >= 0.90).all()
    assert "E:EOH2291" not in main.index and "E:EOH0836" not in rep.index                              # the two silent-electricity homes
    assert len(rep) >= 300 and len(main) >= 300                                                       # no fallback to Sep 2022 needed
    assert pd.read_csv(POOLS / "gb_eoh_2122r3_excluded.csv")["hh"].tolist() == ["E:EOH2291"]
