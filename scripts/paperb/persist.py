"""05b A10: persist a refit model and reload it (results/iter05b_data_limit/stage1/models/s<seed>/<family>/).

Per model directory: `model.joblib` (the `train.Model`, i.e. the fitted imputer / scaler / target standardisation and the
estimator), `X_test.parquet` (the seed's test design, index = sub_id; `p_hat` / `valid` for residual models),
`pred_refit.parquet` (the refit's own test predictions) and `manifest.json` (spec, params, best_iter, feature columns, package
versions, device, SHA-256 of model.joblib). Two models are not pickled whole: the CNN (its network class is local to
`RawSeriesCNN._net`) stores its state_dict in `cnn_state.pt` and is rebuilt on load; TabPFN (in-context learning) stores its train
context `train_context.parquet` (X, y) plus the checkpoint name and SHA-256, and is refit from that context on load (seeded).
Stage 2 (Arm 7): `frozen_predict` applies a saved model unchanged to the same test substations built from scaled fillers.
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
    man = {"seed": int(seed), "family": FAMILY_OF[name], "spec": "|".join(spec), "params": f["meta"]["params"], "best_iter": f["meta"]["best_iter"],
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


def frozen_predict(root, seed, spec, X_te, p_valid=None, device=None):
    """05b Arm 7 frozen-model row: the seed's saved Stage 1 model of `spec` (trained at x1.0), unchanged, applied to another
    version of the same test substations (X_te, index = sub_id; `p_valid` = (P_hat_A, valid) on them for a residual model)."""
    d = model_dir(root, seed, spec)
    m, man = load_model(d, device)
    if man["spec"] != "|".join(spec):
        raise ValueError(f"{d}: saved model is {man['spec']}, not {'|'.join(spec)}")
    saved = pd.read_parquet(d / "X_test.parquet", columns=[]).index.astype(str)
    if not saved.equals(pd.Index(X_te.index).astype(str)):
        raise ValueError(f"{d}: test substations differ from the saved model's test design")
    pred = m.predict(X_te[man["feature_columns"]])
    return compose(p_valid[0], pred, p_valid[1]) if man["residual"] else np.asarray(pred, float)
