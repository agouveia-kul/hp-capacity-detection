"""05a Task 6: extrapolate the runtime of the (amended) 05b arms from the timing probe and from the measured D5 run
(GB-EoH main window, seed 0, full v1.1 grid, one queue job per family; B* D5 arms through the queue). Writes
results/iter05a_pool/runtime_estimate.md.

Per-seed cost on GB-EoH (seconds, measured; 3,875 substations, 5 concurrent jobs at 4-5 threads): F = feature evaluation of the
seed's substations (once per seed and design), P = the Paper A pilot and cross-fit that every job repeats (05b caches it per design,
amendment A4, so only one P is paid), R = the remaining physics work, L / K / T / N = linear / kernel / trees / neural tuning and
fitting. Cost is assumed proportional to the number of substations, i.e. to the train HP households at a fixed grid (x n / 274 in the
learning curve; x substations per cell in arm 3). B* costs `B_STAR` x GB-EoH per seed, MEASURED in D5 (job-hours of the d5_real arm per
seed over the GB-EoH seed cost). The 05b models that do not exist yet (Kernel Ridge, GP, Random Forest, Extra Trees, CatBoost, TabPFN,
1D-CNN) are assumed to double the tuning cost of the five 05a families (`EXTRA`); the GP (cubic in the substations) and TabPFN are the
unknowns. Arm 1 runs netfit x size only (a quarter of the probe's feature-set x anchor grid). Wall time = job time / workers; a night is
22:00 - 07:30, a continuous day 24 h.

    python scripts/paperb/runtime_estimate.py [--workers 6]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402

OUT = ROOT / "results" / "iter05a_pool"
JOBS = OUT / "overnight" / "jobs"
EXTRA, NIGHT_H, SUBS_GB, HP_MAIN, HP_REP = 2.0, 9.5, 3875, 274, 226


def measured():
    sec = {f.name.split("__")[-1].split(".")[0]: json.loads(f.read_text())["seconds"] for f in JOBS.glob("timing_probe__*.done")}
    T = pd.concat([pd.read_parquet(f) for f in JOBS.glob("timing_probe__*.timing.parquet")])
    F = float(T.loc[T["method"] == "evaluate_members", "seconds"].sum())
    fam = {k: float(T[(T["family"] == k) & (T["method"] != "evaluate_members") & ~T["method"].str.startswith("anchor_only")]["seconds"].sum())
           for k in ("linear", "kernel", "trees", "neural")}
    P = sec["neural"] - fam["neural"]                                   # the neural job started from the feature cache
    return {"F": F, "P": P, "R": sec["physics"] - F - P, **fam}, sec


def d5_hours(arm):
    return sum(json.loads(f.read_text())["seconds"] for f in JOBS.glob(f"{arm}__*.done")) / 3600


def main(workers):
    m, sec = measured()
    models = sum(m[k] for k in ("linear", "kernel", "trees", "neural"))
    fixed = m["F"] + 5 * m["P"] + m["R"]                                # features + five pilots + physics (the probe, uncached)
    probe_h = (fixed + models) / 3600
    b_star = d5_hours("d5_real") / 10 / probe_h                         # measured: B* seed / GB-EoH seed (D5 real arm, 05a families)
    cost = lambda mf=1.0, extra=EXTRA: (fixed - 4 * m["P"] + mf * extra * models) / 3600     # noqa: E731  job-hours of one full-size GB-EoH seed, pilot cached
    lc = 2 * (16 + 32 + 62 + 100 + 200) / HP_MAIN + 1
    arms = [("1 learning curve (GB-EoH main, 10 seeds x (2 draws x 5 n + all); netfit x size)", 1, 10 * lc, cost(0.25)),
            ("2 headline (GB-EoH main, 20 seeds, n = all, full grid)", 1, 20, cost()),
            ("7 filler uncertainty (10 seeds x factors 0.5, 1.5)", 2, 20, cost()),
            ("4 oracles (GB-EoH 20 seeds, one extra family pass; B* physics only)", 2, 20 + 20 * b_star * (cost(0) / cost()), cost()),
            ("3 households vs substations (10 seeds, n in {62, all} x spc {10, 40})", 2, 10 * (62 / HP_MAIN + 1) * (1 + 4), cost()),
            ("5 B* under v1.1 (20 seeds, full grid)", 2, 20 * b_star, cost()),
            ("6 temporal replication (GB-EoH Oct 2022 - Sep 2023, 10 seeds)", 2, 10 * HP_REP / HP_MAIN, cost())]
    R = pd.DataFrame([{"stage": st, "arm": a, "full-size seeds": round(e, 1), "job hours": round(e * c, 1), "wall h": round(e * c / workers, 1),
                       "nights": round(e * c / workers / NIGHT_H, 2)} for a, st, e, c in [(a, st, e, c) for a, st, e, c in arms]])
    S = R.groupby("stage")[["job hours", "wall h", "nights"]].sum().round(1)
    S["continuous days"] = (S["wall h"] / 24).round(1)
    nox = sum(e * (fixed - 4 * m["P"] + mf * models) / 3600 for (a, st, e, _), mf in zip(arms, (0.25, 1, 1, 1, 1, 1, 1))) / workers / NIGHT_H
    md = lambda d: "\n".join(["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * d.shape[1]] + ["| " + " | ".join(map(str, r)) + " |" for r in d.itertuples(index=False)])  # noqa: E731
    d5r, d5s = d5_hours("d5_real"), d5_hours("d5_swap")
    txt = ["# 05a Task 6 - timing probe, D5 and the 05b runtime estimate\n",
           f"Probe: GB-EoH main window (pool `gb_eoh_2122r2`, before the silent-home exclusion), seed 0, full v1.1 grid (7 penetrations x 5 sizes), feature sets {{netfit, both}} x anchors "
           f"{{size, size_peak}} x {{direct-log, residual}}, FFNN at the full budget (50 evals, patience 20), {SUBS_GB} substations. Four jobs ran together (5 workers x 5 threads); the neural "
           "job failed at its first attempt (a Windows `os.replace` race on the shared feature cache, fixed) and was rerun alone with 4 threads.\n",
           "Measured (seconds, seed 0): " + ", ".join(f"{k} {v:.0f}" for k, v in m.items() if k != "R") + " (the physics job, 1302 s, contains F and one P); job wall times "
           + ", ".join(f"{k} {v:.0f}" for k, v in sec.items()) + f".\n One full-size GB-EoH seed, all five 05a families, uncached pilots: {probe_h:.2f} job-hours.\n",
           f"**D5 as run** (6 workers x 4 threads, 105 jobs, all done, none failed): 1.5 h wall, d5_real {d5r:.2f} job-h ({d5r / 10:.2f} per seed), d5_swap {d5s:.2f} job-h. "
           f"My pre-run estimate of 17 job-hours (B* = 0.3 x GB-EoH) was 2x too high: measured B* = {b_star:.2f} x GB-EoH per seed. This ratio is used below.\n",
           f"## 05b estimate (amended brief, A4 reductions applied) at {workers} workers\n", md(R), "", md(S.reset_index()), "",
           f"Stage 1 (arms 1 + 2): {S.loc[1, 'wall h']:.0f} h wall = {S.loc[1, 'nights']:.1f} nights or {S.loc[1, 'continuous days']:.1f} continuous days. Stage 2 (arms 7, 4, 3, 5, 6): "
           f"{S.loc[2, 'wall h']:.0f} h wall = {S.loc[2, 'nights']:.1f} nights or {S.loc[2, 'continuous days']:.1f} continuous days. Without the assumed doubling for the new models: "
           f"{nox:.1f} nights in total.\n",
           "Assumptions: cost proportional to the number of substations; the 05b models, the oracles and arm 7's filler scaling are not measured; contention at 6 workers as in the probe; "
           "more workers (RAM allows ~10) would shorten it.\n"]
    (OUT / "runtime_estimate.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    main(ap.parse_args().workers)
