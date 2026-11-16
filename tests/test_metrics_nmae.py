"""nMAE (primary metric from 07, decision 2026-11-16): identity with WAPE, per-bin normaliser, NaN behaviour."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from paperb.metrics import METRIC_ORDER, compute_metrics, nmae  # noqa: E402
from paperb.run_benchmark import metric_rows  # noqa: E402


def test_nmae_first_and_identity_with_wape():
    assert METRIC_ORDER[0] == "nmae"
    rng = np.random.default_rng(0)
    for _ in range(20):
        y = rng.gamma(2.0, 30.0, size=int(rng.integers(5, 200)))
        p = y * rng.lognormal(0, 0.3, size=y.size)
        m = compute_metrics(y, p)
        assert np.isclose(m["nmae"], m["wape"] * y.mean() / y.max())
        assert np.isclose(m["y_max"], y.max())
        assert np.isclose(m["nmae"], np.abs(p - y).mean() / y.max() * 100)


def test_nmae_nan():
    assert np.isnan(nmae([0.0, 0.0], [1.0, 2.0]))
    assert np.isnan(nmae([-1.0, -2.0], [1.0, 2.0]))
    assert np.isnan(nmae([], []))
    assert np.isnan(compute_metrics([0.0, 0.0], [1.0, 1.0])["nmae"])
    assert np.isfinite(nmae([0.0, 5.0], [1.0, 4.0]))


def test_each_bin_uses_its_own_maximum():
    size = np.full(8, 100)
    hp = np.array([5, 10, 12, 20, 30, 50, 80, 100])           # p = 0.05 ... 1.0 -> bins <=15, 15-35, 35-65, >65
    y = hp * 5.0
    p = y * np.array([1.1, 0.9, 1.2, 0.8, 1.05, 0.95, 1.3, 0.7])
    te = pd.DataFrame({"HP_Peak": y, "HP_Count": hp, "size": size, "p": hp / 100})
    members = pd.DataFrame({"hp_members": [{f"h{i}"} for i in range(8)]}, index=te.index)
    rows = pd.DataFrame(metric_rows({"uncertainty": {"bootstrap": False}}, 0, "HP_Peak", te, p, members))
    get = rows.set_index(["cell", "metric"])["value"]
    pen = hp / size
    for cell, m in [("all", np.ones(8, bool)), ("pbin<=15", pen <= 0.15), ("pbin15-35", (pen > 0.15) & (pen <= 0.35)),
                    ("pbin35-65", (pen > 0.35) & (pen <= 0.65)), ("pbin>65", pen > 0.65)]:
        assert np.isclose(get[(cell, "y_max")], y[m].max())
        assert np.isclose(get[(cell, "nmae")], np.abs(p[m] - y[m]).mean() / y[m].max() * 100)
    assert get[("pbin<=15", "y_max")] < get[("all", "y_max")]
