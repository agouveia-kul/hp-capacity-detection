"""Across-split summary (02b): metrics.csv -> summary.csv.

Groups the per-seed values by (arm, pool, target, method, anchor, metric, cell) and reports n_seeds (seeds with a
finite value), median, mean, std (ddof = 1) and the band quantiles from the config (`uncertainty.summary_band`,
default [0.05, 0.90] -> columns q05, q90). No bootstrap: the spread over split seeds is the uncertainty.

    python scripts/paperb/summarise.py --metrics results/iter02b_benchmark/metrics.csv \
        --out results/iter02b_benchmark/summary.csv --config configs/protocol_v1.yaml
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from paperb import ROOT, load_config  # noqa: E402

KEYS = ["arm", "pool", "target", "method", "anchor", "metric", "cell"]


def summarise(metrics, band=(0.05, 0.90)):
    """Long metrics (metrics.csv format; `exp_id` = arm, `dataset` = pool) -> one row per group."""
    m = metrics.rename(columns={"exp_id": "arm", "dataset": "pool"})
    if "cell" not in m:
        m["cell"] = "all"
    lo, hi = (f"q{round(100 * b):02d}" for b in band)
    g = m.groupby(KEYS, sort=True)
    out = pd.DataFrame({"n_seeds": g["value"].agg(lambda v: int(v.notna().sum())), "median": g["value"].median(),
                        "mean": g["value"].mean(), "std": g["value"].std(ddof=1),
                        lo: g["value"].quantile(band[0]), hi: g["value"].quantile(band[1]),
                        "n_hp_households_median": g["n_hp_households"].median(),
                        "n_substations_median": g["n_substations"].median()})
    return out.reset_index()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default="configs/protocol_v1.yaml")
    a = ap.parse_args()
    band = load_config(a.config)["uncertainty"]["summary_band"]
    summarise(pd.read_csv(ROOT / a.metrics), band).to_csv(ROOT / a.out, index=False)
