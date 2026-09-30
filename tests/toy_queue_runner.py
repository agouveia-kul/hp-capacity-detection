"""Toy runner for the queue tests: `run_seed(cfg, seed)` returns one metric row per method of the job's config, logs every call
to the file named by $TOY_LOG, sleeps $TOY_SLEEP seconds, and fails for the seeds listed in the file named by $TOY_FAIL."""
import os
import time

import pandas as pd


def run_seed(cfg, seed):
    with open(os.environ["TOY_LOG"], "a") as fh:
        fh.write(f"{seed} {sorted(cfg['physics_baselines'] + cfg['paperA']['estimators'] + cfg['anchor_only_baselines']['models'] + cfg['models'])}\n")
    time.sleep(float(os.environ.get("TOY_SLEEP", "0")))
    fail = os.environ.get("TOY_FAIL")
    if fail and os.path.exists(fail) and str(seed) in open(fail).read().split():
        raise RuntimeError(f"toy failure for seed {seed}")
    methods = cfg["physics_baselines"] + cfg["paperA"]["estimators"] + cfg["anchor_only_baselines"]["models"] + cfg["models"]
    rows = [{"exp_id": "toy", "split_seed": seed, "dataset": "toy", "target": "HP_Peak", "method": m, "anchor": "size", "feature_set": "-",
             "mode": "direct", "target_transform": "none", "cell": "all", "metric": "wape", "value": seed * 10 + len(m),
             "n_substations": 5, "n_hp_households": 3} for m in methods]
    return {"metrics": pd.DataFrame(rows)}
