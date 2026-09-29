"""Learning-curve harness (iteration 03a, Task 5).

Within one split seed the TRAIN HP households are subsampled to n in `learning_curve.n` (e.g. 16, 32, 48, all),
`learning_curve.draws` draws per n (one draw for `all`, since every draw is the full set). Each draw is a simple
random sample without replacement (stream [seed, LC_STREAM, n, draw]); the train fill pool is unchanged. The train
substations and the household-grouped inner folds are rebuilt from the subsample only, with the same generator rules
(`build_substations`), so cells that become infeasible are listed (dropped_cells, with n and draw). The TEST
substations are identical across n (checked here). The Paper A pilot is the subsample, so the estimator and the ML
models see the same labelled HP households. The runner scores each draw into metrics_lc.csv (usual columns plus
n_train_hp and lc_draw).
"""
import numpy as np

from paperb.splits import grouped_inner_folds
from paperb.substations import build_substations

LC_STREAM = 3


def lc_subsample(train_hp, n, seed, draw):
    """Sorted random subset of `n` train HP households (`all` -> every one of them)."""
    hp = sorted(train_hp)
    if n == "all":
        return hp
    if int(n) > len(hp):
        raise ValueError(f"n = {n} > {len(hp)} train HP households")
    return sorted(np.random.default_rng([seed, LC_STREAM, int(n), draw]).choice(hp, int(n), replace=False).tolist())


def lc_designs(cfg, meta, split, seed, test_members):
    """Yield (n, draw, subsample, members, dropped) per learning-curve draw of one split seed.

    `split` is household_splits(...)[seed]; `test_members` the main run's test memberships, which every draw must
    reproduce. An n larger than the train HP pool yields members = None and a one-row `dropped` frame."""
    lc = cfg["learning_curve"]
    key = ["hp_members", "fill_members"]
    for n in lc["n"]:
        for draw in range(1 if n == "all" else lc["draws"]):
            try:
                sub = lc_subsample(split["train"]["hp"], n, seed, draw)
            except ValueError as e:
                yield n, draw, None, None, [{"split_seed": seed, "split": "train", "n": n, "lc_draw": draw, "reason": str(e)}]
                continue
            sp = {"train": {"hp": sub, "fill": split["train"]["fill"]}, "test": split["test"]}
            folds = grouped_inner_folds(sp["train"], meta, cfg["cv"]["k"], seed)
            members, dropped = build_substations(meta, sp, seed, cfg, folds)
            te = members[members["split"] == "test"]
            if not (te.index.equals(test_members.index) and te[key].astype(str).equals(test_members[key].astype(str))):
                raise AssertionError(f"learning curve n={n} draw={draw}: test substations differ from the main run")
            yield n, draw, sub, members, dropped.assign(n=n, lc_draw=draw).to_dict("records")
