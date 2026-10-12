"""05b A10: persist a refit model and reload it (results/iter05b_data_limit/stage1/models/s<seed>/<family>/).

Per model directory: `model.joblib` (the `train.Model`, i.e. the fitted imputer / scaler / target standardisation and the
estimator), `X_test.parquet` (the seed's test design, index = sub_id; `p_hat` / `valid` for residual models),
`pred_refit.parquet` (the refit's own test predictions) and `manifest.json` (spec, params, best_iter, feature columns, package
versions, device, SHA-256 of model.joblib). Two models are not pickled whole: the CNN (its network class is local to
`RawSeriesCNN._net`) stores its state_dict in `cnn_state.pt` and is rebuilt on load; TabPFN (in-context learning) stores its train
context `train_context.parquet` (X, y) plus the checkpoint name and SHA-256, and is refit from that context on load (seeded).
Stage 2 (Arm 7): `frozen_predict` applies a saved model unchanged to the same test substations built from scaled fillers.
06 (hybrid ladder): one directory per rung, <root>/<rung>/s<seed>/<family>/ (the rung's inner-CV winner of the family). A tuned model
also stores `oof_inner.parquet` (its out-of-fold inner-CV predictions in kW, with y and the fold id; input of the L5 ensembles) and an
L4 model `scale.joblib` (`scale_model.Scale`: kappa or g, the test substations' s0, T_design, station climate), from which
`frozen_predict` rebuilds s_hat / m_hat_h on the scaled test substations with everything learned at x1.0.
`reload_check` reloads every model below a directory in this process and compares it with its own saved test predictions:

    python scripts/paperb/check_jobs.py --reload-models results/iter06_hybrid_ladder/models/a_gb     # writes <dir>/reload_check.csv
"""
import hashlib
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from paperb.lc_fit import FAMILY_OF
from paperb.residual import compose

PACKAGES = {"numpy": "numpy", "pandas": "pandas", "scikit-learn": "sklearn", "xgboost": "xgboost", "torch": "torch", "tabpfn": "tabpfn",
            "joblib": "joblib"}


def model_dir(root, seed, spec):
    return Path(root) / f"s{seed}" / FAMILY_OF[spec[0]]


def _versions():
    """Package versions; the module's __version__ first (a dist-info METADATA file on OneDrive can fail to read: OSError 22)."""
    import importlib
    out = {}
    for p, mod in PACKAGES.items():
        try:
            out[p] = str(importlib.import_module(mod).__version__)
        except (ImportError, AttributeError):
            try:
                out[p] = version(p)
            except (PackageNotFoundError, OSError):
                out[p] = None
    return out


def _sha(f):
    return hashlib.sha256(Path(f).read_bytes()).hexdigest()


def save_model(root, seed, spec, f, sub_ids, pred_te, device):
    """f = {model, meta, X_te, X_tr, y_tr[, p_te, valid_te]} from the runner's `tuned` (refit mode)."""
    d = model_dir(root, seed, spec)
    d.mkdir(parents=True, exist_ok=True)
    m, name = f["model"], spec[0]
    X_te = pd.DataFrame(f["X_te"]).set_axis(pd.Index(sub_ids, name="sub_id"))
    if "p_te" in f:
        X_te = X_te.assign(__p_hat=f["p_te"], __valid=f["valid_te"])
    X_te.to_parquet(d / "X_test.parquet")
    pd.DataFrame({"pred": np.asarray(pred_te, float)}, index=X_te.index).to_parquet(d / "pred_refit.parquet")
    extra = {}
    if name == "CNN":
        import torch
        torch.save(m.m.net.state_dict(), d / "cnn_state.pt")
        net, m.m.net = m.m.net, None
        joblib.dump(m, d / "model.joblib")
        m.m.net = net
        extra["cnn_state_sha256"] = _sha(d / "cnn_state.pt")
    elif name == "TabPFN":
        from paperb.train import tabpfn_info
        pd.DataFrame(f["X_tr"]).assign(__y=np.asarray(f["y_tr"], float)).to_parquet(d / "train_context.parquet")
        reg, m.m = m.m, None
        joblib.dump(m, d / "model.joblib")
        m.m = reg
        extra["tabpfn"] = tabpfn_info()
    else:
        joblib.dump(m, d / "model.joblib")
    if f.get("oof") is not None:
        f["oof"].to_parquet(d / "oof_inner.parquet")
    if f.get("scale") is not None:
        joblib.dump(f["scale"], d / "scale.joblib")
    man = {"seed": int(seed), "family": FAMILY_OF[name], "spec": "|".join(spec), "params": f["meta"]["params"], "best_iter": f["meta"]["best_iter"],
           "cv_wape": f["meta"].get("cv_wape"),
           "feature_columns": [str(c) for c in pd.DataFrame(f["X_te"]).columns], "n_train_sub": int(len(f["y_tr"])), "n_test_sub": int(len(X_te)),
           "residual": "p_te" in f, "device": device, "host": platform.node(), "packages": _versions(),
           "model_sha256": _sha(d / "model.joblib"), **extra}
    (d / "manifest.json").write_text(json.dumps(man, indent=1, default=str), encoding="utf-8")
    return d


def load_model(d, device=None):
    """Reload the model in `d` -> (model, manifest)."""
    d = Path(d)
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    if _sha(d / "model.joblib") != man["model_sha256"]:
        raise ValueError(f"{d}: model.joblib SHA-256 does not match the manifest")
    m = joblib.load(d / "model.joblib")
    name = man["spec"].split("|")[0]
    if name == "CNN":
        import torch
        m.m.device = device or man["device"]
        m.m._torch()
        m.m.net = m.m._net(len(m.m.a_mu)).to(torch.device(m.m.device))
        m.m.net.load_state_dict(torch.load(d / "cnn_state.pt", map_location=m.m.device))
    elif name == "TabPFN":
        from paperb.train import SETTINGS, tabpfn_info
        if tabpfn_info()["sha256"] != man["tabpfn"]["sha256"]:
            raise ValueError(f"{d}: TabPFN checkpoint differs from the one the model was fitted with")
        SETTINGS["device"] = device or man["device"]
        C = pd.read_parquet(d / "train_context.parquet")
        m.fit(C.drop(columns="__y"), C["__y"].to_numpy())
    return m, man


def load_predict(d, device=None):
    """Reload the model in `d` and predict its saved test design -> Series of predictions (kW) indexed by sub_id."""
    m, man = load_model(d, device)
    X = pd.read_parquet(Path(d) / "X_test.parquet")
    if man["residual"]:
        p, valid = X.pop("__p_hat").to_numpy(float), X.pop("__valid").to_numpy(bool)
        pred = compose(p, m.predict(X), valid)
    else:
        pred = m.predict(X)
    return pd.Series(np.asarray(pred, float), index=X.index, name="pred")


def reload_check(root, device=None):
    """Every model below `root`: max relative difference and WAPE difference (pp) between the reloaded model's predictions of its
    saved test design and the predictions saved with it (A10: <= 1e-6, CNN / TabPFN <= 0.1 pp). Failures are listed, not raised."""
    rows = []
    for man in sorted(Path(root).rglob("manifest.json")):
        d, ref = man.parent, pd.read_parquet(man.parent / "pred_refit.parquet")["pred"]
        row = {"dir": d.relative_to(root).as_posix(), "spec": json.loads(man.read_text(encoding="utf-8"))["spec"]}
        try:
            p = load_predict(d, device)
            row.update(max_rel_diff=float(np.max(np.abs(p - ref) / np.maximum(np.abs(ref), 1e-9))),
                       d_wape_pp=100 * float(np.abs(p - ref).sum() / ref.sum()))
        except Exception as e:  # noqa: BLE001
            row["error"] = repr(e)[:200]
        rows.append(row)
    return pd.DataFrame(rows)


def frozen_predict(root, seed, spec, X_te, p_valid=None, device=None, tab_te=None):
    """05b Arm 7 frozen-model row: the seed's saved Stage 1 model of `spec` (trained at x1.0), unchanged, applied to another
    version of the same test substations (X_te, index = sub_id; `p_valid` = (P_hat_A, valid) on them for a residual model).
    06: an L4 model's base s_hat / m_hat_h is rebuilt from its saved scale model on `tab_te` (the substation table of X_te)."""
    d = model_dir(root, seed, spec)
    m, man = load_model(d, device)
    if (d / "scale.joblib").exists():
        p_valid = joblib.load(d / "scale.joblib").base(tab_te)
    if man["spec"] != "|".join(spec):
        raise ValueError(f"{d}: saved model is {man['spec']}, not {'|'.join(spec)}")
    saved = pd.read_parquet(d / "X_test.parquet", columns=[]).index.astype(str)
    if not saved.equals(pd.Index(X_te.index).astype(str)):
        raise ValueError(f"{d}: test substations differ from the saved model's test design")
    pred = m.predict(X_te[man["feature_columns"]])
    return compose(p_valid[0], pred, p_valid[1]) if man["residual"] else np.asarray(pred, float)
