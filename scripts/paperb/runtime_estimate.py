"""05a Task 6: extrapolate the runtime of the 05b arms and of D5 from the timing probe (GB-EoH 2021/22, seed 0, full v1.1 grid,
one queue job per family). Writes results/iter05a_pool/runtime_estimate.md.

Per-seed cost on GB-EoH (seconds, measured; 3,875 substations, 5 concurrent jobs at 4-5 threads): F = feature evaluation of the
seed's substations (once per seed and design), P = the Paper A pilot and cross-fit that every job repeats (residual models need it),
R = the remaining physics work, L / K / T / N = linear / kernel / trees / neural tuning and fitting. Cost is assumed proportional
to the number of substations, i.e. to the train HP households at a fixed grid (x n / 293 in the learning curve; x substations per
cell in arm 3). B* has ~0.3 x the substations of GB-EoH (assumption, `B_STAR`). The 05b models that do not exist yet (Kernel Ridge,
GP, Random Forest, Extra Trees, CatBoost, TabPFN, 1D-CNN) are assumed to double the tuning cost of the five 05a families (`EXTRA`);
the GP (cubic in the substations) and TabPFN are the unknowns. Wall time = job time / workers; a night is 22:00 - 07:30.

    python scripts/paperb/runtime_estimate.py [--workers 6]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402

OUT = ROOT / "results" / "iter05a_pool"
JOBS = OUT / "overnight" / "jobs"
B_STAR, EXTRA, NIGHT_H, SUBS_GB = 0.3, 2.0, 9.5, 3875


def measured():
    sec = {f.name.split("__")[-1].split(".")[0]: json.loads(f.read_text())["seconds"] for f in JOBS.glob("*.done")}
    T = pd.concat([pd.read_parquet(f) for f in JOBS.glob("*.timing.parquet")])
    F = float(T.loc[T["method"] == "evaluate_members", "seconds"].sum())
    fam = {k: float(T[(T["family"] == k) & (T["method"] != "evaluate_members") & ~T["method"].str.startswith("anchor_only")]["seconds"].sum())
           for k in ("linear", "kernel", "trees", "neural")}
    P = sec["neural"] - fam["neural"]                                   # the neural job started from the feature cache
    R = sec["physics"] - F - P
    return {"F": F, "P": P, "R": R, **{k: v for k, v in fam.items()}}, sec


def main(workers):
    m, sec = measured()
    models = sum(m[k] for k in ("linear", "kernel", "trees", "neural"))
    fixed = m["F"] + 5 * m["P"] + m["R"]                                # features + five pilots + physics
    per_seed = lambda extra=1.0, cache=False: fixed - (4 * m["P"] if cache else 0) + extra * models    # noqa: E731  full-size GB-EoH seed, five families
    arms = [("D5 real + swap (B*, 10 seeds x 2 arms, 05a families)", 20 * B_STAR, 1.0),
            ("05b 1 learning curve (GB-EoH, 10 seeds x (3 draws x 5 n + all); n / 293 each)", 10 * (3 * (16 + 32 + 62 + 100 + 200) / 293 + 1), EXTRA),
            ("05b 2 headline (GB-EoH, 20 seeds, n = all)", 20, EXTRA),
            ("05b 3 households vs substations (10 seeds, n in {62, all} x spc {10, 20, 40})", 10 * (62 / 293 + 1) * (1 + 2 + 4), EXTRA),
            ("05b 4 oracles (GB-EoH + B*, 20 seeds each, one extra family pass)", 20 * (1 + B_STAR), EXTRA),
            ("05b 5 B* under v1.1 (20 seeds)", 20 * B_STAR, EXTRA),
            ("05b 6 replication (GB-EoH 2022/23, 10 seeds)", 10 * 239 / 293, EXTRA)]
    rows = [{"arm": a, "full-size seeds": round(e, 1), "job hours": round(e * per_seed(x) / 3600, 1), "wall h": round(e * per_seed(x) / 3600 / workers, 1),
             "nights": round(e * per_seed(x) / 3600 / workers / NIGHT_H, 2)} for a, e, x in arms]
    R = pd.DataFrame(rows)
    red = {0: 10 * (2 * (16 + 32 + 62 + 100 + 200) / 293 + 1), 2: 20, 3: 10 * (62 / 293 + 1) * (1 + 4), 4: 20 * (1 + B_STAR), 5: 20 * B_STAR, 6: 10 * 239 / 293}   # arms 1-6 with the reductions
    red_h = sum(e * per_seed(EXTRA, cache=True) for e in red.values()) / 3600
    tot = R[R["arm"].str.startswith("05b")][["job hours", "wall h", "nights"]].sum()
    md = lambda d: "\n".join(["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * d.shape[1]] + ["| " + " | ".join(map(str, r)) + " |" for r in d.itertuples(index=False)])  # noqa: E731
    txt = ["# 05a Task 6 - timing probe and runtime estimate\n",
           f"Probe: GB-EoH 2021/22 (pool `gb_eoh_2122r2`), seed 0, full v1.1 grid (7 penetrations x 5 sizes), feature sets {{netfit, both}} x anchors {{size, size_peak}} x "
           f"{{direct-log, residual}}, FFNN at the full budget (50 evals, patience 20), {SUBS_GB} substations. Four jobs ran together (5 workers x 5 threads); the neural job "
           "failed at its first attempt (a Windows `os.replace` race on the shared feature cache, fixed) and was rerun alone with 4 threads.\n",
           "Measured (seconds, seed 0): " + ", ".join(f"{k} {v:.0f}" for k, v in m.items() if k != "R") + " (the physics job, 1302 s, contains F and one P); job wall times " + ", ".join(f"{k} {v:.0f}" for k, v in sec.items()) + ".\n",
           f"One full-size GB-EoH seed, all five families: {per_seed() / 3600:.2f} job-hours ({fixed / 3600:.2f} h features + pilots + physics, {models / 3600:.2f} h model tuning). "
           f"The pilot and cross-fit ({m['P']:.0f} s) are recomputed by every family job: caching it would save {4 * m['P'] / 3600:.2f} h per seed "
           f"({100 * 4 * m['P'] / per_seed():.0f} %).\n", f"## Estimate at {workers} workers\n", md(R), "",
           f"05b total: **{tot['job hours']:.0f} job-hours, {tot['wall h']:.0f} h wall, {tot['nights']:.1f} nights** (assuming the new 05b models double the tuning cost; "
           f"without that factor: {sum(e * per_seed() for a, e, x in arms[1:]) / 3600 / workers / NIGHT_H:.1f} nights). This is above the ~3-night threshold of the brief.\n",
           f"With the first three reductions listed below applied (pilot cached per design, 2 learning-curve draws, arm 3 with spc {{10, 40}}; FFNN and workers unchanged): "
           f"{red_h:.0f} job-hours, {red_h / workers:.0f} h wall, **{red_h / workers / NIGHT_H:.1f} nights** at {workers} workers.\n",
           "Assumptions: cost proportional to the number of substations; B* = 0.3 x GB-EoH; the 05b models and oracles are not measured; contention at 6 workers "
           "is taken as in the probe. Where a reduction would come from (not applied): cache the pilot per (seed, n, draw) design; 2 instead of 3 learning-curve draws; "
           "arm 3 with spc {10, 40}; FFNN in the learning curve only at n in {62, all}; more workers (RAM allows ~10).\n"]
    (OUT / "runtime_estimate.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    main(ap.parse_args().workers)
