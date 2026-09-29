"""Evaluation-only checks of the legacy tuned artefacts (no hyperopt re-tuning).

1. Score the saved models/capacity_swiss.pkl (Ridge + XGB from
   train_swiss_capacity.py) on the HEAPO test split, the synthetic WPUQ set and
   the real WPUQ feeder.
2. Rebuild the feature-selection CV curve (xgb_feature_selection_cv.csv) from the
   LEGACY ranking and base_meta stored in models/xgb_selected_features.json, i.e.
   feature_select_xgb.py step 3 without its unseeded hyperopt step 1.

A gap between (2) and the legacy curve points at data/code; a gap only in the
full re-run points at hyperopt randomness. Outputs go to <out_dir>/reproduced/.

    python scripts/legacy_eval_only.py --config configs/iter00_full.yaml
"""
import argparse
import json
import pickle
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts" / "legacy"), str(ROOT / "scripts")]
import hp_capacity as hc  # noqa: E402
import benchmark_capacity_models as B  # noqa: E402  (legacy, unchanged)
import feature_select_xgb as FS  # noqa: E402  (legacy, unchanged)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ap.parse_args().config))
    out = ROOT / cfg["out_dir"] / "reproduced"
    out.mkdir(parents=True, exist_ok=True)

    import os
    os.chdir(ROOT)
    X, y, tr, te, Xw, yw, Xr, yr = B.load_data()

    # 1) saved capacity_swiss.pkl
    m = pickle.load(open(ROOT / "models/capacity_swiss.pkl", "rb"))
    cols, med = m["feature_cols"], m["train_median"]
    rows = []
    for name, mdl, fill in (("Ridge", m["ridge"], False), ("XGBoost", m["xgb"], True)):
        prep = (lambda D: D[cols].fillna(med)) if fill else (lambda D: D[cols])
        for ds, XX, yy in (("HEAPO test", X.loc[te], y.loc[te]), ("WPUQ synthetic", Xw, yw)):
            met = hc.compute_metrics(yy.to_numpy(), hc.clip_non_negative(mdl.predict(prep(XX))))
            rows.append(dict(model=name, set=ds, **met))
        pred = float(hc.clip_non_negative(mdl.predict(prep(Xr)))[0])
        rows.append(dict(model=name, set="WPUQ real feeder", pred=pred, true=yr,
                         mape=abs(pred - yr) / yr * 100))
    pd.DataFrame(rows).to_csv(out / "capacity_swiss_pkl_evalonly.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))

    # 2) feature-selection curve from the legacy ranking + base_meta
    meta = json.load(open(ROOT / "models/xgb_selected_features.json"))
    Xtr_f = X.loc[tr].fillna(X.loc[tr].median())
    ranked, base_meta = meta["ranking"], meta["base_meta"]
    ks = sorted({k for k in [5, 10, 15, 20, 30, 40, 60, 80, 120, 160, 220, len(ranked)] if k <= len(ranked)})
    curve = []
    for k in ks:
        mu, sd = FS.cv_rmse(Xtr_f, y.loc[tr], ranked[:k], base_meta)
        curve.append(dict(k=k, cv_rmse_mean=mu, cv_rmse_std=sd))
        print(f"k={k:4d}: CV RMSE {mu:6.2f} +/- {sd:4.2f}", flush=True)
    pd.DataFrame(curve).to_csv(out / "xgb_feature_selection_cv_evalonly.csv", index=False)


if __name__ == "__main__":
    main()
