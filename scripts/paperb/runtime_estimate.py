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
    python scripts/paperb/runtime_estimate.py --probe05b --workers 10     # 05b, after configs/iter05b_probe.yaml
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from paperb import ROOT  # noqa: E402

OUT = ROOT / "results" / "iter05a_pool"
JOBS = OUT / "overnight" / "jobs"
EXTRA, NIGHT_H, SUBS_GB, HP_MAIN, HP_REP = 2.0, 9.5, 3875, 274, 226
B_STAR = 0.11                                                           # B* / GB-EoH job-hours per seed, measured in 05a D5 (runtime_estimate.md)


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


def main05b(workers, out=ROOT / "results" / "iter05b_data_limit"):
    """05b: re-estimate from the 05b probe (configs/iter05b_probe.yaml: arm 2, seed 0, full size, every queue family; pilots cached),
    measured per queue family instead of the 05a probe x EXTRA. Same arm scaling as main(); arm 1's n = all point is arm 2 (not rerun),
    its tabular families run netfit x size (1/4 of arm 2's specs), the CNN size only (1/2). Writes <out>/runtime_estimate_05b.md."""
    J = out / "stage1" / "jobs"
    fam = {f.name.split("__")[-1][:-len(".done")]: json.loads(f.read_text())["seconds"] / 3600 for f in J.glob("arm2__s0__d0__nall__*.done")}
    failed = sorted(f.name.split("__")[-1][:-len(".failed")] for f in J.glob("arm2__s0__d0__nall__*.failed"))
    if not fam:
        raise SystemExit(f"no probe job in {J}: run the queue with configs/iter05b_probe.yaml first")
    q = yaml.safe_load((ROOT / "configs" / "iter05b_stage1.yaml").read_text())
    run = set(next(a for a in q["arms"] if a["name"] == "arm2")["families"])
    dropped = {k: round(v, 2) for k, v in fam.items() if k not in run}  # A8: probed, not run in stage 1
    fam = {k: v for k, v in fam.items() if k in run}
    failed = [f for f in failed if f in run]
    seed = sum(fam.values())                                            # job-hours of one full-size GB-EoH seed (arm 2)
    frac = {k: 1.0 if k == "physics" else 0.5 if k == "rawseries" else 0.25 for k in fam}
    lc_seeds = 10 * 2 * (16 + 32 + 62 + 100 + 200) / HP_MAIN           # arm 1 in full-size seeds at arm 2's specs
    arm1 = lc_seeds * sum(frac[k] * v for k, v in fam.items()) / seed
    arms = [("1 learning curve (10 seeds x 2 draws x n in {16, 32, 62, 100, 200}; netfit x size)", 1, arm1),
            ("2 headline (20 seeds, n = all, full grid)", 1, 20),
            ("7 filler uncertainty (10 seeds x factors 0.5, 1.5)", 2, 20),
            ("4 oracles (GB-EoH 20 seeds, one extra family pass; B* physics only)", 2, 20 + 20 * B_STAR * fam.get("physics", 0) / seed),
            ("3 households vs substations (10 seeds, n in {62, all} x spc {10, 40})", 2, 10 * (62 / HP_MAIN + 1) * (1 + 4)),
            ("5 B* under v1.1 (20 seeds, full grid)", 2, 20 * B_STAR),
            ("6 temporal replication (GB-EoH Oct 2022 - Sep 2023, 10 seeds)", 2, 10 * HP_REP / HP_MAIN)]
    R = pd.DataFrame([{"stage": st, "arm": a, "full-size seeds": round(e, 1), "job hours": round(e * seed, 1), "wall h": round(e * seed / workers, 1),
                       "nights": round(e * seed / workers / NIGHT_H, 2)} for a, st, e in arms])
    S = R.groupby("stage")[["job hours", "wall h", "nights"]].sum().round(1)
    S["continuous days"] = (S["wall h"] / 24).round(1)
    F = pd.DataFrame([{"queue family": k, "probe job hours (seed 0)": round(v, 2), "share of a seed": f"{v / seed:.0%}",
                       "stage 1 job hours": round(v * (20 + lc_seeds * frac[k]), 1)} for k, v in sorted(fam.items(), key=lambda kv: -kv[1])])
    md = lambda d: "\n".join(["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * d.shape[1]] + ["| " + " | ".join(map(str, r)) + " |" for r in d.itertuples(index=False)])  # noqa: E731
    txt = ["# 05b runtime estimate from the 05b timing probe\n",
           f"Probe: arm 2 (GB-EoH main, full v1.1 grid, every model x anchors {{size, size_peak}} x feature sets {{netfit, both}} x {{direct-log, residual}}), seed 0, "
           f"one queue job per family, pilots cached: {seed:.1f} job-hours for one full-size seed of the families stage 1 runs. Failed probe jobs (not in the estimate): {', '.join(failed) or 'none'}. "
           f"Probed but not run in stage 1 (A8), job-hours per seed: {dropped or 'none'}. "
           f"B* = {B_STAR} x GB-EoH per seed (measured in 05a D5 on the 05a families; not re-measured for the new models).\n", md(F), "",
           f"## Arms at {workers} workers\n", md(R), "", md(S.reset_index()), "",
           f"Stage 1 (arms 1 + 2): {S.loc[1, 'wall h']:.0f} h wall = {S.loc[1, 'nights']:.1f} nights or {S.loc[1, 'continuous days']:.1f} continuous days; "
           f"the probe already paid {seed:.1f} of its job-hours. Stage 2: {S.loc[2, 'wall h']:.0f} h wall = {S.loc[2, 'nights']:.1f} nights or {S.loc[2, 'continuous days']:.1f} continuous days.\n",
           "Assumptions: cost proportional to the number of substations (the GP is cubic in the train substations and TabPFN's context grows with them, "
           "so arm 1 is overestimated for those two and arm 3 at spc 40 underestimated); wall = job hours / workers, although TabPFN runs at most 3 jobs at once; "
           "contention as in the probe (9 jobs at once).\n"]
    (out / "runtime_estimate_05b.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))
    return S


def main05b_stage2(workers, out=ROOT / "results" / "iter05b_data_limit", night_h=NIGHT_H):
    """05b Stage 2: estimate from the probe (configs/iter05b_probe_stage2.yaml: seed 0 of every arm, full size, same job ids as
    configs/iter05b_stage2.yaml). Remaining job hours = probe job hours x (seeds - 1) per (arm, design, family). Upper bound = the probe
    times as measured; lower bound = family jobs whose physics job (same arm, design) was still running when they started did that
    job's feature evaluation and pilot themselves (the cache was empty): that cost is removed, floored at the family's arm2_cpu job
    (features and pilot cached, same grid). In the full queue a seed's physics job mostly runs before its family jobs (arm -> family ->
    seed order), so the lower bound is the likely case. Wall = max(job hours / workers, TabPFN job hours / its max_concurrent)."""
    q = yaml.safe_load((ROOT / "configs" / "iter05b_stage2.yaml").read_text())
    J, rows = out / "stage2" / "jobs", []
    done = {f.name[:-5]: json.loads(f.read_text()) for f in J.glob("*__s0__*.done")}
    for arm in q["arms"]:
        for n in arm.get("n", ["all"]):
            for fam in arm["families"]:
                jid = f"{arm['name']}__s0__d0__n{n}__{fam}"
                d = done.get(jid)
                ph = done.get(f"{arm['name']}__s0__d0__n{n}__physics")
                rows.append({"arm": arm["name"], "n": n, "family": fam, "seeds": len(arm["seeds"]), "probe_h": None if d is None else d["seconds"] / 3600,
                             "start": None if d is None else d["start"], "phys_end": None if ph is None else ph["end"],
                             "phys_h": None if ph is None else ph["seconds"] / 3600})
    R = pd.DataFrame(rows)
    ref = {r["family"]: r["probe_h"] for r in rows if r["arm"] == "arm2_cpu"}
    overlap = (R["family"] != "physics") & R["phys_end"].notna() & (R["start"] < R["phys_end"])
    floor = R["family"].map(ref).fillna(0) * R["arm"].str.contains("spc40").map({True: 4, False: 1})
    R["lower_h"] = np.where(overlap, np.maximum(R["probe_h"] - R["phys_h"].fillna(0), floor), R["probe_h"])
    for c, s in (("upper", "probe_h"), ("lower", "lower_h")):
        R[f"{c}_rest_h"] = R[s] * (R["seeds"] - 1)
    missing = [f"{r.arm}/{r.n}/{r.family}" for r in R[R["probe_h"].isna()].itertuples()]
    A = R.groupby("arm", sort=False)[["probe_h", "lower_rest_h", "upper_rest_h"]].sum().round(1).reset_index()
    tab = R[R["family"] == "tabpfn"][["lower_rest_h", "upper_rest_h"]].sum()
    cap = q["families"]["tabpfn"].get("max_concurrent", workers)
    tot = {c: float(R[f"{c}_rest_h"].sum()) for c in ("lower", "upper")}
    wall = {c: max(tot[c] / workers, float(tab[f"{c}_rest_h"]) / cap) for c in tot}
    md = lambda d: "\n".join(["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * d.shape[1]] + ["| " + " | ".join(map(str, r)) + " |" for r in d.itertuples(index=False)])  # noqa: E731
    txt = ["# 05b Stage 2 runtime estimate from the probe (seed 0 of every arm)\n",
           f"Probe jobs: {R['probe_h'].notna().sum()} of {len(R)} done ({R['probe_h'].sum():.1f} job-h); missing (not in the estimate): {', '.join(missing) or 'none'}.\n",
           md(A.rename(columns={"probe_h": "probe job-h (seed 0)", "lower_rest_h": "remaining job-h, lower", "upper_rest_h": "remaining job-h, upper"})), "",
           f"Remaining Stage 2 at {workers} workers (TabPFN at most {cap} at once): lower {tot['lower']:.0f} job-h -> {wall['lower']:.0f} h wall "
           f"({wall['lower'] / 24:.1f} continuous days, {wall['lower'] / night_h:.1f} nights); upper {tot['upper']:.0f} job-h -> {wall['upper']:.0f} h wall "
           f"({wall['upper'] / 24:.1f} continuous days, {wall['upper'] / night_h:.1f} nights).\n",
           "Lower = feature evaluation and pilot paid once per (arm, design, seed) by the physics job; upper = probe times as measured "
           "(some family jobs redid them). Contention as in the probe (6 workers).\n"]
    (out / "stage2" / "runtime_estimate_stage2.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--probe05b", action="store_true", help="05b: estimate from the 05b probe (configs/iter05b_probe.yaml)")
    ap.add_argument("--stage2", action="store_true", help="05b Stage 2: estimate from configs/iter05b_probe_stage2.yaml")
    a = ap.parse_args()
    main05b_stage2(a.workers) if a.stage2 else main05b(a.workers) if a.probe05b else main(a.workers)
