"""Protocol v1 household splits (Task 3).

`household_splits` partitions households into train / test BEFORE any substation is built. HP households
are split per station (stratified), fill households globally; the two use independent random streams, so
changing the fill pool never changes the HP split. `grouped_inner_folds` partitions the TRAIN households
into K household-disjoint folds (HP households stratified by station); inner substations are then built
inside one fold, so CV folds never share a household.
"""
import numpy as np
import pandas as pd

HP_STREAM, FILL_STREAM, FOLD_STREAM = 0, 1, 2


def _take(ids, n, rng):
    return set(rng.permutation(sorted(ids))[:n])


def household_splits(meta, seeds, test_frac=0.25, stratify="station", shared_fill=False):
    """seed -> {'train'|'test': {'hp': [hh], 'fill': [hh]}}; `meta` is Pool.meta.
    shared_fill (pool A): the fill pool of a split is that split's HP households (their non-HP channel)."""
    hp, fill = meta[meta["role"] == "hp"], meta.index[meta["role"] == "fill"]
    out = {}
    for seed in seeds:
        rng_hp, rng_fill = np.random.default_rng([seed, HP_STREAM]), np.random.default_rng([seed, FILL_STREAM])
        test_hp = set()
        for _, g in hp.groupby(stratify, sort=True):
            test_hp |= _take(g.index, int(round(test_frac * len(g))), rng_hp)
        test_fill = test_hp if shared_fill else _take(fill, int(round(test_frac * len(fill))), rng_fill)
        train_fill = set(hp.index) - test_hp if shared_fill else set(fill) - test_fill
        out[seed] = {"train": {"hp": sorted(set(hp.index) - test_hp), "fill": sorted(train_fill)},
                     "test": {"hp": sorted(test_hp), "fill": sorted(test_fill)}}
    return out


def grouped_inner_folds(train, meta, k=4, seed=0):
    """Series hh -> fold id (0..k-1) over the train HP and fill households of one split seed."""
    rng = np.random.default_rng([seed, FOLD_STREAM])
    fold = {}
    hp = meta.loc[train["hp"]]
    for _, g in hp.groupby("station", sort=True):                   # stratified round robin per station
        start = int(rng.integers(k))
        for i, h in enumerate(rng.permutation(sorted(g.index))):
            fold[h] = (start + i) % k
    for i, h in enumerate(rng.permutation(sorted(set(train["fill"]) - set(fold)))):   # shared fill: HP folds stand
        fold[h] = i % k
    return pd.Series(fold, name="fold").sort_index()
