"""Diff reproduced legacy outputs against the original copies in data/.

For every legacy CSV, rows are aligned on the file's key columns, and each
numeric column gets its max absolute and max relative difference
(|repro - legacy| / |legacy|). Anything above 1 % relative is flagged.

Also writes the reproduced numbers (and, separately, the original legacy
numbers) in the long metrics format of CLAUDE.md section 8, tagged
protocol=legacy.

    python scripts/compare_to_legacy.py --config configs/iter00_full.yaml
"""
import argparse
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
REL_TOL = 0.01

# file -> key columns used to align rows
KEYS = {
    "capacity_model_benchmark.csv": ["model"],
    "capacity_wpuq_real_feeder.csv": ["method"],
    "xgb_feature_selection_cv.csv": ["k"],
    "xgb_hockey_ci_metrics.csv": ["set", "method"],
    "hockey_variants_transfer.csv": ["reduction", "map", "set"],
    "hockey_delta_calibrated.csv": ["set", "method"],
    "wpuq_penetration_sweep.csv": ["n_hp"],
    "wpuq_penetration_variants.csv": ["_row"],
    "penetration_calibrated_delta.csv": ["penetration"],
    "swiss_penetration_sweep.csv": ["penetration"],
}
# evaluation-only reproductions (scripts/legacy_eval_only.py) -> legacy file they reproduce
EVAL_ONLY = {"xgb_feature_selection_cv_evalonly.csv": "xgb_feature_selection_cv.csv"}

# distinct HP households behind each evaluation set (see facts.md)
N_HP = {"HEAPO test": 28, "HEAPO train (CV)": 27, "WPUQ synthetic": 37, "WPUQ real feeder": 37}
SET_NAMES = {"Swiss test": "HEAPO test", "Swiss test (unseen subs)": "HEAPO test",
             "synthetic WPUQ": "WPUQ synthetic", "synthetic WPUQ substations": "WPUQ synthetic",
             "real WPUQ feeder": "WPUQ real feeder"}
ML = {"LinearReg", "Lasso", "Ridge", "ElasticNet", "SVR", "XGBoost", "FFNN", "XGB"}


def read(path):
    df = pd.read_csv(path)
    df["_row"] = np.arange(len(df))
    return df


def compare(name, legacy, repro, keys):
    num = [c for c in legacy.columns if c not in keys and c != "_row"
           and pd.api.types.is_numeric_dtype(legacy[c])]
    m = legacy.merge(repro, on=keys, how="outer", suffixes=("_leg", "_rep"), indicator=True)
    unmatched = int((m["_merge"] != "both").sum())
    m = m[m["_merge"] == "both"]
    rows = []
    for c in num:
        if f"{c}_rep" not in m:
            rows.append(dict(file=name, column=c, n_rows=0, max_abs=np.nan, max_rel=np.nan,
                             flag="MISSING_COLUMN", unmatched_rows=unmatched))
            continue
        a, b = m[f"{c}_leg"].astype(float).to_numpy(), m[f"{c}_rep"].astype(float).to_numpy()
        both_nan = np.isnan(a) & np.isnan(b)
        d = np.where(both_nan, 0.0, np.abs(b - a))
        rel = np.where(both_nan | (d == 0), 0.0, d / np.maximum(np.abs(a), 1e-12))
        mx_abs, mx_rel = float(np.nanmax(d)) if len(d) else np.nan, float(np.nanmax(rel)) if len(rel) else np.nan
        nan_mismatch = int((np.isnan(a) ^ np.isnan(b)).sum())
        bad = ["/".join(map(str, r)) for r in m.loc[rel > REL_TOL, keys].itertuples(index=False)]
        flag = "OK" if (mx_rel <= REL_TOL and nan_mismatch == 0 and unmatched == 0) else "GT_1PCT"
        rows.append(dict(file=name, column=c, n_rows=len(m), max_abs=mx_abs, max_rel=mx_rel,
                         flag=flag, unmatched_rows=unmatched, nan_mismatch=nan_mismatch,
                         rows_gt_tol=";".join(bad)))
    return rows


# ------------------------------------------------------------ long metrics --
def _row(dataset, method, metric, value, n_sub, anchor=None, n_hp=None):
    base = dataset.split(" pen=")[0]
    return dict(dataset=dataset, target="HP_Peak", method=method,
                anchor=anchor or ("size+peak" if method.split()[0] in ML else "none"),
                metric=metric, value=value, n_substations=n_sub,
                n_hp_households=n_hp if n_hp is not None else N_HP.get(base, np.nan))


def to_long(name, df):
    out = []
    if name == "capacity_model_benchmark.csv":
        for _, r in df.iterrows():
            for pre, ds, n in (("test_", "HEAPO test", 1080), ("wpuq_", "WPUQ synthetic", 400)):
                for c in [c for c in df.columns if c.startswith(pre)]:
                    out.append(_row(ds, r["model"], c[len(pre):], r[c], n))
    elif name == "capacity_wpuq_real_feeder.csv":
        anchors = {"baseline:median": "none", "baseline:density": "size"}
        for _, r in df.iterrows():
            for c in ("pred_kW", "err_kW", "abs_pct_err"):
                out.append(_row("WPUQ real feeder", r["method"], c, r[c], 1, anchors.get(r["method"])))
    elif name == "xgb_feature_selection_cv.csv":
        for _, r in df.iterrows():
            for c in ("cv_rmse_mean", "cv_rmse_std"):
                out.append(_row("HEAPO train (CV)", f"XGBoost top-{int(r['k'])}", c, r[c], 1080))
    elif name in ("xgb_hockey_ci_metrics.csv", "hockey_delta_calibrated.csv", "hockey_variants_transfer.csv"):
        for _, r in df.iterrows():
            meth = r["method"] if "method" in df else f"hockey {r['reduction']} {r['map']}"
            if name == "hockey_delta_calibrated.csv":
                meth = f"hockey mean/mean {meth}"
            for c in [c for c in df.columns if c not in ("set", "method", "reduction", "map", "n", "_row")]:
                if pd.notna(r[c]):
                    out.append(_row(SET_NAMES[r["set"]], meth, c, r[c], int(r["n"])))
    elif name == "wpuq_penetration_sweep.csv":
        for _, r in df.iterrows():
            ds = f"WPUQ real feeder pen={r['penetration']:.2f}"
            for meth, pre in (("XGBoost", "xgb_"), ("hockey min/max slope-only", "hockey_")):
                for c in [c for c in df.columns if c.startswith(pre)]:
                    out.append(_row(ds, meth, c[len(pre):], r[c], int(r["reps"])))
    elif name in ("penetration_calibrated_delta.csv", "swiss_penetration_sweep.csv"):
        base = "WPUQ real feeder" if name.startswith("penetration") else "HEAPO test"
        meths = {"XGB": "XGBoost", "calDelta": "hockey mean/mean delta calib (origin)",
                 "slopeMap": "hockey min/max slope-only"}
        for _, r in df.iterrows():
            n = int(r["n"]) if "n" in df else (1 if r["penetration"] == 1.0 else 30)
            for k, meth in meths.items():
                out.append(_row(f"{base} pen={r['penetration']:.2f}", meth, "mape", r[f"{k}_mape"], n))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ap.parse_args().config))
    out_dir = ROOT / cfg["out_dir"]
    repro_dir = out_dir / "reproduced"
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()

    diffs, long_rep, long_leg, missing = [], [], [], []
    for rep_name, name in [*((n, n) for n in KEYS), *EVAL_ONLY.items()]:
        leg_p, rep_p = ROOT / "data" / name, repro_dir / rep_name
        if not rep_p.exists():
            missing.append(rep_name)
            continue
        leg, rep = read(leg_p), read(rep_p)
        diffs += compare(rep_name, leg, rep, KEYS[name])
        if rep_name != name:
            continue
        long_rep += [dict(source_file=name, **r) for r in to_long(name, rep)]
        long_leg += [dict(source_file=name, **r) for r in to_long(name, leg)]

    D = pd.DataFrame(diffs)
    D.to_csv(out_dir / "compare_to_legacy.csv", index=False)
    head = dict(exp_id=cfg["exp_id"], protocol=cfg["protocol"], split_seed=cfg["seeds"]["split"])
    cols = ["exp_id", "protocol", "split_seed", "dataset", "target", "method", "anchor", "metric",
            "value", "n_substations", "n_hp_households", "source_file"]
    for rows, fname in ((long_rep, "metrics.csv"), (long_leg, "metrics_legacy_files.csv")):
        pd.DataFrame([{**head, **r} for r in rows]).reindex(columns=cols).to_csv(out_dir / fname, index=False)

    # per-file summary
    lines = [f"# compare_to_legacy (commit {commit}, tolerance {REL_TOL:.0%} relative)", "",
             "| file | columns | columns > 1 % | worst column | max rel diff | unmatched rows | rows > 1 % |",
             "|---|---|---|---|---|---|---|"]
    for f, g in D.groupby("file", sort=False):
        w = g.loc[g["max_rel"].fillna(np.inf).idxmax()]
        lines.append(f"| {f} | {len(g)} | {(g.flag != 'OK').sum()} | {w['column']} | "
                     f"{w['max_rel']:.1e} | {int(g['unmatched_rows'].max())} | "
                     f"{', '.join(sorted({r for x in g['rows_gt_tol'].fillna('') for r in x.split(';') if r})) or '-'} |")
    for f in missing:
        lines.append(f"| {f} | - | - | NOT REPRODUCED (no output) | - | - | - |")
    (out_dir / "compare_to_legacy.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("\nflagged columns:")
    print(D[D.flag != "OK"].to_string(index=False) if (D.flag != "OK").any() else "  none")


if __name__ == "__main__":
    main()
