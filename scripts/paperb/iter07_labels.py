"""Iteration 07, Task 1: label audit (labels only; no model, no prediction). Writes results/iter07_transfer/labels/.

Per pool (06 arm configs a_gb, a_ch) and split seed 0-9, on the 06 A-arm memberships (rebuilt deterministically):
- c = HL / native label per substation; c_src of a seed = its median over the TRAIN substations (the headline mapping),
  with the 5-90 % spread, overall and per Paper A bin (actual penetration HP_Count / size); test substations are summarised
  too (they give c_tgt's counterpart, not used for any mapping);
- CH: the 30/15-min ratio of the net-aggregate peak on the train substations (net = HP + own load + fillers, the pool's
  gap-filled 15-min series; 30 min = the mean of the two 15-min values);
- GB: the immersion share of HP_Peak, 1 - HL / native, by bin.

    python scripts/paperb/iter07_labels.py
"""
try:                                                                  # torch before pandas / pyarrow (05b DLL clash)
    import torch  # noqa: F401
except (ImportError, OSError):
    pass
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb.labels_hl import household_caps, substation_labels  # noqa: E402
from paperb.pools import build_pool  # noqa: E402
from paperb.run_benchmark import PBINS  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import build_substations  # noqa: E402

ARMS = {"CH": "a_ch", "GB": "a_gb"}
OUT = ROOT / "results" / "iter07_transfer" / "labels"


def arm_cfg(arm):
    return yaml.safe_load((ROOT / "results" / "iter06_hybrid_ladder" / arm / "config.yaml").read_text(encoding="utf-8"))


def members_of(pool, cfg, seed):
    """The 06 memberships of one seed (train, test, inner), as run_benchmark.run_seed builds them."""
    sp = household_splits(pool.meta, [seed], cfg["split"]["test_frac"], cfg["split"]["stratify"], cfg["pool"].get("shared_fill", False))[seed]
    folds = grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], seed)
    return build_substations(pool.meta, sp, seed, cfg, folds)[0]


def pbin(members):
    pen = members["n_hp"] / members["size"]
    return pd.cut(pen, [-np.inf] + [hi for _, _, hi in PBINS], labels=[c for c, _, _ in PBINS])


def net_peak_ratio(pool, members):
    """30/15-min ratio of the net-aggregate peak per substation (B*: HP + own load + fillers)."""
    hp, own, fill = (np.ascontiguousarray(d.to_numpy(np.float64).T) for d in (pool.hp, pool.own, pool.fill))
    ph, pf = {h: i for i, h in enumerate(pool.hp.columns)}, {h: i for i, h in enumerate(pool.fill.columns)}
    out = {}
    for sid, m in members.iterrows():
        ih = [ph[h] for h in m["hp_members"]]
        net = hp[ih].sum(0) + own[ih].sum(0) + fill[[pf[h] for h in m["fill_members"]]].sum(0)
        out[sid] = net.reshape(-1, 2).mean(1).max() / net.max()
    return pd.Series(out)


def q(s):
    return {"median": s.median(), "q05": s.quantile(0.05), "q90": s.quantile(0.90), "n": int(s.notna().sum())}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, caps_out = [], []
    for pname, arm in ARMS.items():
        cfg = arm_cfg(arm)
        pool = build_pool(cfg["pool"]["option"], cfg, verbose=False)
        caps = household_caps(pool, cfg)
        caps_out.append(caps.assign(pool=pname, c_hh=caps["hl"] / caps["native"]))
        for seed in cfg["split"]["seeds"]:
            mem = members_of(pool, cfg, seed)
            lab = substation_labels(mem, caps)
            c, b = lab["HL"] / lab["native"], pbin(mem)
            for split in ("train", "test"):
                sel = (mem["split"] == split).to_numpy()
                for cell, mm in [("all", sel)] + [(k, sel & (b == k).to_numpy()) for k, _, _ in PBINS]:
                    rows.append({"pool": pname, "split_seed": seed, "split": split, "cell": cell, "quantity": "c", **q(c[mm])})
                    if pname == "GB":
                        rows.append({"pool": pname, "split_seed": seed, "split": split, "cell": cell, "quantity": "immersion_share", **q(1 - c[mm])})
            if pname == "CH":
                tr = mem[mem["split"] == "train"]
                r = net_peak_ratio(pool, tr)
                for cell, mm in [("all", np.ones(len(tr), bool))] + [(k, (pbin(tr) == k).to_numpy()) for k, _, _ in PBINS]:
                    rows.append({"pool": pname, "split_seed": seed, "split": "train", "cell": cell, "quantity": "net_peak_30_15", **q(r[mm])})
            print(f"{pname} seed {seed}: c_src {c[(mem['split'] == 'train').to_numpy()].median():.4f}", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "label_audit.csv", index=False)
    pd.concat(caps_out).to_csv(OUT / "household_caps.csv")
    return R


if __name__ == "__main__":
    main()
