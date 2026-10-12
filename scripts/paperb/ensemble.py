"""L5 of the hybrid ladder (iteration 06, Task 3): ensembles of the families' L4 models (iterations/06-hybrid-ladder.md).

L5a: the plain average of the families' L4 test predictions; no learned weight.
L5b: a gate on r_hat = s_hat / P_base(net) (identifiable, label-free). The inner substations' r_hat is cut at a subset of its
QUANTILES; in every bin the weights are the non-negative least squares of y on the families' OUT-OF-FOLD inner-CV predictions
(kW; stacked regressions, no intercept, weights need not sum to 1; solver `scipy.optimize.lsq_linear`, BVLS). The subset of edges (2^5 candidates, no edge = one global
weight vector) is chosen by household-grouped CV over the inner folds: weights from the other folds, absolute error on the
held-out fold, pooled over the folds. For each number of edges the best subset is kept; the gate takes the smallest number of
edges whose error is within TOL (1 %, relative) of the lowest one, so an edge must pay for itself. A candidate with a bin of
fewer than MIN_BIN rows in a fit is skipped. The weights are then refit on all inner rows. Substations without an r_hat use the
weights of all rows.
`Gate.fit` reads inner-substation rows only: test rows never reach the edges or the weights.

    python scripts/paperb/ensemble.py --arm results/iter06_hybrid_ladder/a_gb --models results/iter06_hybrid_ladder/models/a_gb

reads <models>/L4/s<seed>/<family>/{oof_inner, pred_refit}.parquet (the L4 inner-CV winner of each family, saved by the queue
jobs) and <arm>/l4.csv (r_hat per substation), and writes <arm>/l5_predictions.csv and <arm>/l5_gates.csv.
"""
import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

QUANTILES, MIN_BIN, TOL = (0.05, 0.1, 0.2, 0.35, 0.65), 20, 0.01


def average(P):
    return np.asarray(P, float).mean(axis=1)


def _bins(r, edges):
    """Bin index of each r_hat; a missing r_hat gets the extra index len(edges) + 1 (the all-rows weights)."""
    return np.where(np.isfinite(r), np.searchsorted(edges, r, side="right"), len(edges) + 1)


def _nnls(A, b):
    """Non-negative least squares by bounded-variable least squares (lower bound 0). scipy 1.14's `nnls` fails on proportional
    columns (singular normal equations), and the families' predictions are close to that."""
    return lsq_linear(A, b, bounds=(0, np.inf), method="bvls").x


def _weights(P, y, b, n_bins):
    """NNLS weights per bin, shape [n_bins + 1, families]; the last row is fitted on all rows."""
    return np.array([_nnls(P[m], y[m]) for m in [b == k for k in range(n_bins)] + [np.ones(len(y), bool)]])


class Gate:
    def fit(self, P, y, r, folds):
        """P [rows, families]: out-of-fold predictions of the inner substations; y, r, folds: their target, r_hat, fold id."""
        P, y, r, folds = np.asarray(P, float), np.asarray(y, float), np.asarray(r, float), np.asarray(folds)
        q, by_k = np.nanquantile(r, QUANTILES), []
        for k in range(len(q) + 1):
            best = None
            for edges in map(np.array, itertools.combinations(q, k)):
                b, err = _bins(r, edges), 0.0
                for f in np.unique(folds):
                    tr = folds != f
                    if k and min(int(np.sum(b[tr] == j)) for j in range(k + 1)) < MIN_BIN:
                        err = np.inf
                        break
                    W = _weights(P[tr], y[tr], b[tr], k + 1)
                    err += float(np.abs((P[~tr] * W[b[~tr]]).sum(axis=1) - y[~tr]).sum())
                if best is None or err < best[0]:
                    best = (err, edges)
            by_k.append(best)
        best = next(b for b in by_k if b[0] <= (1 + TOL) * min(e for e, _ in by_k) + 1e-9 * float(y.sum()))
        self.edges, self.cv_wape = best[1], 100 * best[0] / float(y.sum())
        self.W = _weights(P, y, _bins(r, self.edges), len(self.edges) + 1)
        return self

    def predict(self, P, r):
        return (np.asarray(P, float) * self.W[_bins(np.asarray(r, float), self.edges)]).sum(axis=1)


def l5_seed(d, r_hat):
    """L5 of one seed. d = <models>/L4/s<seed>; r_hat: Series over sub_id (inner and test substations).
    Returns (test frame: the families' predictions, L5a, L5b; the fitted Gate; the families)."""
    fams = sorted(p.name for p in Path(d).iterdir() if (p / "oof_inner.parquet").exists())
    oof = {f: pd.read_parquet(d / f / "oof_inner.parquet") for f in fams}
    O = pd.concat([oof[f]["oof"].rename(f) for f in fams], axis=1).dropna()        # rows every family predicted out of fold
    meta = oof[fams[0]].loc[O.index]
    T = pd.concat([pd.read_parquet(d / f / "pred_refit.parquet")["pred"].rename(f) for f in fams], axis=1)
    g = Gate().fit(O.to_numpy(), meta["y"].to_numpy(), r_hat.reindex(O.index).to_numpy(), meta["fold"].to_numpy())
    return T.assign(L5a=average(T[fams]), L5b=g.predict(T[fams].to_numpy(), r_hat.reindex(T.index).to_numpy())), g, fams


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, help="merged arm directory (l4.csv, predictions.csv)")
    ap.add_argument("--models", required=True, help="the arm's persisted models (contains L4/s<seed>/<family>/)")
    a = ap.parse_args(argv)
    arm, root = Path(a.arm), Path(a.models) / "L4"
    l4 = pd.read_csv(arm / "l4.csv")
    preds, gates = [], []
    for d in sorted(root.glob("s*"), key=lambda p: int(p.name[1:])):
        seed = int(d.name[1:])
        s = l4[l4["split_seed"] == seed].set_index("sub_id")
        T, g, fams = l5_seed(d, s["r_hat"])
        if len(fams) < 2:
            print(f"seed {seed}: {len(fams)} family with an L4 model, no ensemble", file=sys.stderr)
            continue
        preds.append(T.rename_axis("sub_id").reset_index().assign(split_seed=seed))
        gates += [{"split_seed": seed, "bin": k, "r_lo": lo, "r_hi": hi, "cv_wape": g.cv_wape, **dict(zip(fams, w))}
                  for k, (lo, hi, w) in enumerate(zip([-np.inf, *g.edges, np.nan], [*g.edges, np.inf, np.nan], g.W))]
    pd.concat(preds).to_csv(arm / "l5_predictions.csv", index=False)
    pd.DataFrame(gates).to_csv(arm / "l5_gates.csv", index=False)
    print(f"L5: {len(preds)} seeds -> {arm / 'l5_predictions.csv'}")


if __name__ == "__main__":
    main()
