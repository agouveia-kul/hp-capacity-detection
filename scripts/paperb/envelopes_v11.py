"""05a Task 4: design envelopes of B* and GB-EoH under protocol v1.1 (counts only, no model is run).

For every split seed (0..19) the real generator (`substations.build_substations`, fill_all for GB-EoH) is run on the pool's household
split, and the HP households that actually seed substations, the substations per split and the test substations per Paper A
penetration bin (actual p = n_hp / size) are counted. Target: >= 20 test substations in every bin. Writes
results/iter05a_pool/envelopes.md and envelopes.csv.

    python scripts/paperb/envelopes_v11.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from paperb import ROOT, load_config  # noqa: E402
from paperb.iter05a_report import md  # noqa: E402
from paperb.pools import build_pool  # noqa: E402
from paperb.splits import grouped_inner_folds, household_splits  # noqa: E402
from paperb.substations import build_substations  # noqa: E402

POOLS = [("B* (cal2023, 15 min)", "configs/pool_bstar.yaml", "bstar"), ("GB-EoH 2021/22 main (Nov 2021 - Oct 2022)", "configs/pool_gb_eoh_2122.yaml", "gb_eoh"),
         ("GB-EoH replication as written (= main window)", "configs/pool_gb_eoh_2223.yaml", "gb_eoh"),
         ("GB-EoH replication, latest start (Sep 2022 - Aug 2023)", "configs/pool_gb_eoh_2223sep.yaml", "gb_eoh")]
BINS = [("<=15 %", 0, .15), ("15-35 %", .15, .35), ("35-65 %", .35, .65), (">65 %", .65, 9)]
SEEDS = range(20)


def envelope(cfg, option):
    pool = build_pool(option, cfg, verbose=False)
    rows = []
    for seed, sp in household_splits(pool.meta, SEEDS, cfg["split"]["test_frac"], cfg["split"]["stratify"], cfg["pool"].get("shared_fill", False)).items():
        mem, dropped = build_substations(pool.meta, sp, seed, cfg, grouped_inner_folds(sp["train"], pool.meta, cfg["cv"]["k"], seed))
        r = {"seed": seed, "HP train (pool)": len(sp["train"]["hp"]), "HP test (pool)": len(sp["test"]["hp"]), "dropped cells": len(dropped)}
        for s in ("train", "test"):
            m = mem[mem["split"] == s]
            r[f"HP {s} used"] = len(set().union(*m["hp_members"])) if len(m) else 0
            r[f"{s} substations"] = len(m)
        te = mem[mem["split"] == "test"]
        pen = te["n_hp"] / te["size"]
        r.update({f"test n, p {b}": int(((pen > lo) & (pen <= hi)).sum()) for b, lo, hi in BINS})
        rows.append(r)
    return pd.DataFrame(rows), pool


def main():
    out = ROOT / "results" / "iter05a_pool"
    txt = ["# 05a Task 4 - envelopes under protocol v1.1\n", "Source: `scripts/paperb/envelopes_v11.py`; the real generator on 20 split seeds, grid of "
           "`configs/protocol_v1_1.yaml` (sizes x p in {0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0}). Median (min-max over seeds). Target: >= 20 test substations in every Paper A bin.\n"]
    allrows = []
    for name, path, option in POOLS:
        d, pool = envelope(load_config(path), option)
        allrows.append(d.assign(pool=name))
        s = d.drop(columns="seed").agg(["median", "min", "max"]).T
        tab = pd.DataFrame({"quantity": s.index, "median": s["median"].to_numpy(), "min": s["min"].to_numpy(), "max": s["max"].to_numpy()})
        bin_cols = [c for c in d.columns if c.startswith("test n, p")]
        low = [c[len("test n, p "):] for c in bin_cols if d[c].min() < 20]
        txt += [f"## {name}\n", f"HP households in the pool: {int((pool.meta['role'] == 'hp').sum())}; stations: {pool.meta.loc[pool.meta['role'] == 'hp', 'station'].nunique()}.\n", md(tab), "",
                f"Bins with fewer than 20 test substations in the worst seed: {low or 'none'}; in the median seed: "
                f"{[c[len('test n, p '):] for c in bin_cols if d[c].median() < 20] or 'none'}.\n"]
    pd.concat(allrows).to_csv(out / "envelopes.csv", index=False)
    (out / "envelopes.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
