"""Iteration 07, Task 3: the L4a configurations to refit (results/iter07_transfer/l4a_refits.csv; the queue's frozen.models_csv).

For every (pool, seed, family) whose persisted 06 L4 winner is L4b (GB 11, CH 20 of 30): the L4a configuration with the lowest
06 inner-CV WAPE (`wape_inner` in results/iter06_hybrid_ladder/<arm>/metrics.csv; ties to the configuration label, as the 06
report), and its logged hyperparameters and epoch count. They come from the 06 run logs (log.txt, probe_log.txt,
probe_log_first.txt; not the aborted first-grid probe): the line "HP_Peak <spec>: cv_mse .., cv_wape W, .., best_iter B, ..,
params {..}" of that seed whose cv_wape (printed to 0.1) matches the metric within 0.05. Exactly one distinct (params,
best_iter) must match, else the script stops. Refit = the configuration on the same source train set with these values, no
search (run_queue frozen arm, `train.tune_grouped_cv` fixed path; the CNN trains best_iter epochs with B1's three
initialisations).

    python scripts/paperb/iter07_l4a_refits.py
"""
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb.lc_fit import FAMILY_OF  # noqa: E402

D06 = ROOT / "results" / "iter06_hybrid_ladder"
LOGS = ["log.txt", "probe_log.txt", "probe_log_first.txt"]
QUEUE_FAMILY = {"linear": "linear", "neural": "tabpfn_h", "rawseries": "cnn_h"}
LINE = re.compile(r"^\[s(\d+)\s.*?\]\s+HP_Peak (\S+): cv_mse \S+, cv_wape ([\d.]+|nan), train_wape \S+, best_iter (\S+), \d+ evals, \S+, params (\{.*\})$")
SPEC = ["method", "anchor", "feature_set", "mode", "target_transform"]


def logged():
    rows = []
    for f in LOGS:
        for line in (D06 / f).read_text(encoding="utf-8", errors="replace").splitlines():
            if (m := LINE.match(line.strip())) and m.group(2).split("/")[3] == "l4a":
                rows.append({"split_seed": int(m.group(1)), "spec": m.group(2).replace("/", "|"), "cv_wape_log": float(m.group(3)),
                             "best_iter": None if m.group(4) == "None" else int(m.group(4)), "params": json.dumps(ast.literal_eval(m.group(5))),
                             "log": f})
    return pd.DataFrame(rows)


def main():
    L, out = logged(), []
    for arm in ("a_gb", "a_ch"):
        M = pd.read_csv(D06 / arm / "metrics.csv", usecols=["split_seed", *SPEC, "cell", "metric", "value"])
        I = M[(M["metric"] == "wape_inner") & (M["cell"] == "all") & (M["mode"] == "l4a")].copy()
        I["family"], I["spec"] = I["method"].map(FAMILY_OF), I[SPEC].astype(str).agg("|".join, axis=1)
        best = I.sort_values(["value", "spec"]).groupby(["split_seed", "family"]).first().reset_index()
        for man in sorted((D06 / "models" / arm / "L4").glob("s*/*/manifest.json")):
            mf = json.loads(man.read_text(encoding="utf-8"))
            if mf["spec"].split("|")[3] != "l4b":
                continue
            b = best[(best["split_seed"] == mf["seed"]) & (best["family"] == mf["family"])].iloc[0]
            hit = L[(L["split_seed"] == mf["seed"]) & (L["spec"] == b["spec"]) & ((L["cv_wape_log"] - b["value"]).abs() <= 0.05)]
            if hit[["params", "best_iter"]].astype(str).drop_duplicates().shape[0] != 1:
                raise SystemExit(f"{arm} s{mf['seed']} {b['spec']}: {len(hit)} matching log lines, no unique (params, best_iter); stop")
            h = hit.iloc[0]
            out.append({"arm": arm, "split_seed": int(mf["seed"]), "family": mf["family"], "queue_family": QUEUE_FAMILY[mf["family"]],
                        "spec": b["spec"], "params": h["params"], "best_iter": h["best_iter"], "cv_wape_06": float(b["value"]),
                        "persisted_l4b": mf["spec"], "log": h["log"], "carried_model": True})
    R = pd.DataFrame(out)
    R.to_csv(ROOT / "results" / "iter07_transfer" / "l4a_refits.csv", index=False)
    print(R.groupby(["arm", "family"]).size().to_string())
    return R


if __name__ == "__main__":
    main()
