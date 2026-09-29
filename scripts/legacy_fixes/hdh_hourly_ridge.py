"""F14 fix: notebook cell 88 (time-of-day HDH-sensitivity RidgeCV) refitted on TRAIN, scored on test.

Legacy protocol (the notebook's substations, data/substations_data.pkl, read-only; split
train_test_split(test_size=0.5, random_state=42) as notebook cell 27). Features are the four
time-of-day HDH sensitivities of notebook cells 78 / 85 (hourly means, `daily_hdh_energy` per window,
`fit_hdh_linear`, >= MIN_HEATING_DAYS days). Reports both
  * old: RidgeCV fitted on the test substations and scored on them (cell 88, F14), and
  * new: RidgeCV fitted on the train substations and scored on test.

    python scripts/legacy_fixes/hdh_hourly_ridge.py --config configs/iter02a_hdh_ridge_quick.yaml
"""
import argparse
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402
from sklearn.linear_model import RidgeCV  # noqa: E402
from sklearn.metrics import mean_absolute_percentage_error, r2_score, root_mean_squared_error  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from hp_common import HDH_THRESH, MIN_HEATING_DAYS, daily_hdh_energy, fit_hdh_linear, hour_groups  # noqa: E402


def window_sensitivities(temp, load):
    """Cells 78 / 85 for one substation: {<window>_Sensitivity: slope}."""
    sm = pd.DataFrame({"Temperature": temp.resample("h").mean(), "Total_Load": load.resample("h").mean()}).dropna()
    out = {}
    for name, hours in hour_groups.items():
        g = sm[sm.index.hour.isin(hours)]
        x, y = daily_hdh_energy(g["Temperature"], g["Total_Load"], hdh_thresh=HDH_THRESH)
        if len(x) < MIN_HEATING_DAYS:
            continue
        try:
            out[f"{name}_Sensitivity"] = fit_hdh_linear(x, y)[1]
        except Exception:  # noqa: BLE001 - the notebook skips failed fits the same way
            continue
    return out


def score(y, p):
    m = y != 0
    return {"rmse": root_mean_squared_error(y, p), "mape": mean_absolute_percentage_error(y[m], p[m]) * 100,
            "r2": r2_score(y, p)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    out = ROOT / cfg["out_dir"]
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(ROOT / "data" / "substations_data.pkl", "rb") as fh:
        sub = pickle.load(fh)
    sub = sub[[c for c in sub.columns if c in ("Temperature", "Total_Load", "HP_Peak")]]
    tr, te = train_test_split(sub, test_size=0.5, random_state=cfg["seeds"]["notebook_split"])
    if cfg.get("max_substations"):
        tr, te = tr.iloc[:cfg["max_substations"]], te.iloc[:cfg["max_substations"]]
    feats = {k: pd.DataFrame.from_dict({i: window_sensitivities(d.at[i, "Temperature"], d.at[i, "Total_Load"])
                                        for i in d.index}, orient="index") for k, d in (("train", tr), ("test", te))}
    cols = [c for c in feats["train"].columns if c.endswith("_Sensitivity")]      # cell 79
    rows = []
    for name, fit_on in (("old: fit on test (cell 88, F14)", "test"), ("new: fit on train", "train")):
        fit = feats[fit_on][cols].join(sub["HP_Peak"]).dropna()
        ev = feats["test"][cols].join(sub["HP_Peak"]).dropna()                    # cell 87
        m = RidgeCV(alphas=np.logspace(-3, 4, 50), cv=5).fit(fit[cols], fit["HP_Peak"])
        p = np.maximum(m.predict(ev[cols]), 0)
        rows.append({"variant": name, "alpha": m.alpha_, "n_fit": len(fit), "n_test": len(ev),
                     **score(ev["HP_Peak"].to_numpy(), p)})
    res = pd.DataFrame(rows)
    res.to_csv(out / "hdh_hourly_ridge.csv", index=False)
    msg = res.to_string(index=False)
    print(msg)
    (out / "hdh_hourly_ridge_log.txt").write_text(f"{msg}\nruntime {time.time() - t0:.0f}s; notebook figure: "
                                                  "RMSE 55.22 kW, MAPE 19.59 %, alpha 10.0\n", encoding="utf-8")


if __name__ == "__main__":
    main()
