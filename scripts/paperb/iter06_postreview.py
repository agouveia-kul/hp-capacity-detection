"""Iteration 06, post-review (2026-11-16): POST-REVIEW, NOT OF RECORD. Saved outputs only (no refit, no rerun).

    python scripts/paperb/iter06_postreview.py [--root results/iter06_hybrid_ladder]

1. 06 in nMAE (DECISIONS 2026-11-16): nMAE = mean|y_hat - y| / max(y) x 100 per seed x arm x cell, with the cell's own maximum,
   recomputed from <arm>/predictions.csv (a_gb, a_ch, r_x05, r_x15, r_rep) and <arm>/l5_predictions.csv. Bins use the actual
   penetration HP_Count / size (from <arm>/l4.csv), as run_benchmark.metric_rows. S-GB saved no predictions: its nMAE is
   mae / max(y) of the seed's A-GB test cell, used only because every S design's test set is checked to be that set
   (same n_substations and mean(y) = mae / wape x 100 per cell; learning_curve.py also asserts it at run time).
   The frozen report's functions (iter06_report.py, unchanged) are reused on these values: rung winners stay chosen by inner-CV
   WAPE, as in the record.
2. Rules 1-3 re-applied in the 2026-11-16 form: "better" = paired per-unit difference < 0 in >= 80 % of the units and median
   per-unit RELATIVE difference <= -5 % ("worse": the mirror image). Relative difference: on A and S (hi - lo) / lo of the levels;
   on R (d_hi - d_lo) / ref_lo, d = the degradation and ref_lo = the lower model's level at x1.0 (A-GB) - choices made here, since
   the decision does not define R. Rule 2 (a) in relative form: median(hybrid) / median(best pure data-driven) - 1 <= +5 % (the
   analogue of the 1 pp margin; also a choice made here). Hybrid, best pure data-driven model, L0 reference and L5 are as in the
   record. The relative form gives the same verdict in nMAE and WAPE on one set; both are computed and compared.
3. exp(z_hat) table (Decision 2): L4 rung winners, per family and bin: median exp(z_hat) [5-90 %] and median y / base, at x1.0
   (A-GB fit row; base = paperA_l4a / paperA_l4b of A-GB) and at x0.5 (update row; base = the same estimate with the re-estimated
   s0 in r_x05). Substations with an invalid base (s_hat <= 0, prediction 0) are counted, not used.
4. S-GB n = 32: inner folds with substations per design (physics job's lc_dropped), job types with rows per design, and n* and the
   n = 32 step / claim readings (WAPE, of record metric) as registered and on the designs feasible for every job type.
Outputs: <root>/report/postreview/*.csv and postreview.md.
"""
try:                                                                  # torch before pandas / pyarrow (see run_queue.py)
    import torch  # noqa: F401
except (ImportError, OSError):
    pass
import argparse  # noqa: E402
import glob  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb import iter06_report as R  # noqa: E402

K, SPEC, CELLS = R.K, R.SPEC, R.CELLS
EDGES = [0, 0.15, 0.35, 0.65, np.inf]
ARMS = ("a_gb", "a_ch", "r_x05", "r_x15", "r_rep")
LABEL = "post-review, not of record"


def bins_of(root, arm):
    """(split_seed, sub_id) -> Paper A bin from the actual penetration of the arm's test substations."""
    L = pd.read_csv(Path(root) / arm / "l4.csv", usecols=["split_seed", "sub_id", "split", "HP_Count", "size"], low_memory=False)
    L = L[L["split"] == "test"].drop_duplicates(["split_seed", "sub_id"])
    return L.assign(bin=pd.cut(L["HP_Count"] / L["size"], EDGES, labels=R.BINS).astype(str))[["split_seed", "sub_id", "bin", "HP_Count"]]


def cell_metrics(P, keys):
    """Per (keys, cell): nMAE, WAPE, y_max, mean(y), n. P has y, pred, bin."""
    P = P.assign(ae=(P["pred"] - P["y"]).abs())
    out = []
    for cell, D in [("all", P), *[(b, P[P["bin"] == b]) for b in R.BINS]]:
        g = D.groupby(keys, dropna=False).agg(ae=("ae", "mean"), ae_s=("ae", "sum"), y_s=("y", "sum"), y_max=("y", "max"), y_mean=("y", "mean"),
                                              n=("y", "size")).reset_index()
        g["nmae"] = np.where(g["y_max"] > 0, g["ae"] / g["y_max"] * 100, np.nan)
        g["wape"] = np.where(g["y_s"] > 0, g["ae_s"] / g["y_s"] * 100, np.nan)
        out.append(g.assign(cell=cell))
    return pd.concat(out, ignore_index=True)


def long_frame(C, M_rec, metric):
    """A metrics.csv-like long frame whose 'wape' rows hold `metric`, plus the record's inner-CV WAPE (selection unchanged)."""
    v = C[[*K, *SPEC, "cell", metric]].rename(columns={metric: "value"}).assign(metric="wape", target="HP_Peak")
    inner = M_rec[(M_rec["metric"] == "wape_inner") & (M_rec["cell"] == "all") & (M_rec["target"] == "HP_Peak")][[*K, *SPEC, "cell", "metric", "value", "target"]]
    return pd.concat([v, inner], ignore_index=True)


def build(root):
    """nMAE / recomputed-WAPE frames per arm, the normalisers, and the checks against the record."""
    frames, norms, chk = {}, [], []
    for arm in ARMS:
        P = pd.read_csv(Path(root) / arm / "predictions.csv", low_memory=False)
        P = P[P["target"] == "HP_Peak"].merge(bins_of(root, arm), on=["split_seed", "sub_id"], how="left")
        if P["bin"].isna().any():
            raise ValueError(f"{arm}: test substations without a bin")
        for c in SPEC:
            P[c] = P[c].astype(str)
        C = cell_metrics(P, [*K, *SPEC])
        M = R.load(root, arm)
        for c in SPEC:
            M[c] = M[c].astype(str)
        rec = M[(M["metric"] == "wape") & (M["target"] == "HP_Peak") & M["cell"].isin(CELLS)][[*K, *SPEC, "cell", "value"]]
        j = C.merge(rec, on=[*K, *SPEC, "cell"], how="left")
        chk.append({"arm": arm, "rows": len(j), "rows_without_record": int(j["value"].isna().sum()),       # relative: a few log-linear CH rows reach 1e257 kW
                    "max_rel_wape_diff": float(((j["wape"] - j["value"]).abs() / j["value"].abs()).max()),
                    "max_rel_nmae_identity": float(((j["nmae"] - j["wape"] * j["y_mean"] / j["y_max"]).abs() / j["nmae"].abs()).max())})
        frames[arm] = {"nmae": long_frame(C, M, "nmae"), "wape": long_frame(C, M, "wape"), "C": C}
        Y = C.drop_duplicates([*K, "cell"])[[*K, "cell", "y_max", "y_mean", "n"]]
        norms.append(Y.assign(arm=arm, mean_over_max=Y["y_mean"] / Y["y_max"]))
    return frames, pd.concat(norms, ignore_index=True), pd.DataFrame(chk)


def s_frame(root, norms, keep_designs=None):
    """S-GB metrics_lc as a long frame in nMAE (mae / A-GB test max) and in WAPE, after checking the test sets; optional n = 32 filter."""
    M = R.load(root, "s_gb", "metrics_lc.csv")
    M = M[(M["target"] == "HP_Peak") & M["cell"].isin(CELLS)]
    w = M[M["metric"].isin(["wape", "mae"])].pivot_table(index=[*K, "lc_draw", "n_train_hp", *SPEC, "cell"], columns="metric", values="value", aggfunc="first")
    n_sub = M[M["metric"] == "wape"].groupby([*K, "lc_draw", "n_train_hp", *SPEC, "cell"])["n_substations"].first()
    w = w.join(n_sub).reset_index()
    ref = norms[norms["arm"] == "a_gb"][[*K, "cell", "y_max", "y_mean", "n"]]
    w = w.merge(ref, on=[*K, "cell"], how="left")
    w["mean_from_lc"] = w["mae"] / w["wape"] * 100
    ok = np.isclose(w["mean_from_lc"], w["y_mean"], rtol=1e-6) & (w["n_substations"] == w["n"])
    check = {"rows": len(w), "rows_matching_a_gb_test_cell": int(ok.sum()), "max_rel_mean_diff": float((w["mean_from_lc"] / w["y_mean"] - 1).abs().max())}
    w["nmae"] = w["mae"] / w["y_max"] * 100
    if keep_designs is not None:
        n32 = w["n_train_hp"] == 32
        w = w[~n32 | w.set_index([*K, "lc_draw"]).index.isin(keep_designs)]
    out = {}
    for metric in ("nmae", "wape"):
        v = w[[*K, "lc_draw", "n_train_hp", *SPEC, "cell", metric]].rename(columns={metric: "value"}).assign(metric="wape", target="HP_Peak")
        inner = M[(M["metric"] == "wape_inner") & (M["cell"] == "all")][[*K, "lc_draw", "n_train_hp", *SPEC, "cell", "metric", "value", "target"]]
        if keep_designs is not None:
            inner = inner[(inner["n_train_hp"] != 32) | inner.set_index([*K, "lc_draw"]).index.isin(keep_designs)]
        out[metric] = pd.concat([v, inner], ignore_index=True)
    return out, check, bool(ok.all())


def readings_with(root, frames, metric, s_frames=None, l0_names=None):
    """R.readings on the given frames (R.load patched; the report file itself is unchanged), plus the x1.0 references of the R arms.
    `l0_names`: the L0 reference rows of the record's (WAPE) readings, replayed in R.readings' call order so that a reading keeps the
    record's L0 row (in nMAE the lowest-median rule can pick another row); the names used are returned in `used`."""
    orig, orig_l0, used = R.load, R.l0_ref, []

    def l0(W, keys, col="all"):
        if l0_names is None:
            name, s = orig_l0(W, keys, col)
        else:
            name = l0_names[len(used)]
            s = W[W["method"] == name].set_index(keys)[col] if name else pd.Series(dtype=float)
        used.append(name)
        return name, s

    def load(r, arm, name="metrics.csv"):
        if name == "metrics.csv" and arm in frames:
            return frames[arm][metric].copy()
        if name == "metrics_lc.csv" and arm == "s_gb":
            return s_frames[metric].copy() if s_frames is not None else pd.DataFrame()
        return orig(r, arm, name)
    R.load, R.l0_ref = load, l0
    try:
        T, Z, names, W = R.readings(root)
        ref = {}
        for key, arm in (("R x0.5", "r_x05"), ("R x1.5", "r_x15")):
            Wr = R.wide(load(root, arm), K)
            ref[key] = R.table(R.degradation(Wr, W["gb"], "frozen"), K, "all_ref")
        ref["R rep"] = R.table(R.degradation(R.wide(load(root, "r_rep"), K), W["gb"], "fit"), K, "all_ref")
        pilots = orig(root, "a_gb", "pilots.csv")
        for k in Z:
            Z[k] = pd.Series(Z[k], dtype=float).rename(names.get(k) or "")
        ns = R.n_star(T, Z, pilots) if s_frames is not None else pd.DataFrame()
    finally:
        R.load, R.l0_ref = orig, orig_l0
    l0_ref = {"R x0.5": W["gb"][W["gb"]["method"] == "paperA_corr"].set_index(K)["all"]}
    l0_ref["R x1.5"] = l0_ref["R x0.5"]
    nm = names.get("A-GB all")
    l0_ref["R rep"] = W["gb"][W["gb"]["method"] == nm].set_index(K)["all"]
    return T, Z, names, W, ref, l0_ref, ns, used


def rel_verdict(hi, lo, ref=None, share=0.8, thr=0.05):
    """2026-11-16 form: sign share on the paired difference, median of the relative difference (lo, or ref on R)."""
    d = (hi - lo).dropna()
    r = (d / (lo if ref is None else ref).reindex(d.index)).replace([np.inf, -np.inf], np.nan).dropna()
    if d.empty or r.empty:
        return {"n": 0, "n_neg": 0, "median_rel": np.nan, "median_diff": np.nan, "verdict": "missing"}
    v = ("better" if (d < 0).mean() >= share and r.median() <= -thr else "worse" if (d > 0).mean() >= share and r.median() >= thr else "no difference")
    return {"n": len(d), "n_neg": int((d < 0).sum()), "median_rel": float(r.median()), "median_diff": float(d.median()), "verdict": v}


def is_r(key):
    return key in ("R x0.5", "R x1.5", "R rep")


def steps_rel(T, ref):
    rows = []
    for key in [k for k in T if not k.endswith(("update", "level"))]:
        for fam in R.FAMS:
            for hi, lo in R.STEPS:
                a, b = R.col(T[key], (fam, hi)), R.col(T[key], (fam, lo))
                rows.append({"reading": key, "family": fam, "step": f"{hi} vs {lo}", **rel_verdict(a, b, R.col(ref[key], (fam, lo)) if is_r(key) else None)})
    S = pd.DataFrame(rows)
    comb = (S[S["reading"].isin(["R x0.5", "R x1.5", "R rep"])].groupby(["family", "step"])["verdict"].apply(lambda v: R.combine_r(list(v))).reset_index()
            .assign(reading="R (combined)"))
    return pd.concat([S, comb], ignore_index=True)


def claim_rel(T, Z, ref, l0ref, rec):
    """Rule 2 in relative form with the record's hybrid and best pure data-driven model; the hybrid vs L0 in relative form."""
    hyb, dd = (rec["hybrid"].split(" ")[0], "L4"), tuple(rec["best_pure_dd"].split(" "))
    A = T["A-GB all"]
    gap_rel = R.col(A, hyb).median() / R.col(A, dd).median() - 1
    s = rel_verdict(R.col(T["S-GB n=62"], hyb), R.col(T["S-GB n=62"], dd)) if "S-GB n=62" in T else {"verdict": "missing"}
    r = {k: rel_verdict(R.col(T[k], hyb), R.col(T[k], dd), R.col(ref[k], dd)) for k in ("R x0.5", "R x1.5", "R rep")}
    r_all = R.combine_r([v["verdict"] for v in r.values()])
    a_ok, nb = bool(gap_rel <= 0.05), (s["verdict"] == "better") + (r_all == "better")
    out = "fails" if not a_ok or nb == 0 else "holds regardless of T" if nb == 2 else "open: needs T (07)"
    res = {"hybrid": f"{hyb[0]} L4", "best_pure_dd": " ".join(dd), "A_median_hybrid": R.col(A, hyb).median(), "A_median_dd": R.col(A, dd).median(),
           "A_gap": R.col(A, hyb).median() - R.col(A, dd).median(), "A_gap_rel": gap_rel, "a_holds": a_ok, "S_n62": s["verdict"],
           **{f"{k}": v["verdict"] for k, v in r.items()}, "R": r_all, "outcome": out}
    vs = []
    for k in [k for k in T if not k.endswith(("update", "level")) and k in Z]:
        z = Z[k]
        vs.append({"reading": k, **rel_verdict(R.col(T[k], hyb), z, l0ref.get(k) if is_r(k) else None)})
    return res, pd.DataFrame(vs)


def l5_rel(root, metric, hyb_fam="tabpfn"):
    """Rule 3 in relative form from l5_predictions.csv (the all-family ensembles; the no-CNN ensemble is not saved there)."""
    rows = []
    for arm in ("a_gb", "a_ch"):
        P = pd.read_csv(Path(root) / arm / "l5_predictions.csv").merge(bins_of(root, arm), on=["split_seed", "sub_id"])
        y = pd.read_csv(Path(root) / arm / "l4.csv", usecols=["split_seed", "sub_id", "split", "HP_Peak"]).query("split == 'test'").drop_duplicates(["split_seed", "sub_id"])
        P = P.merge(y[["split_seed", "sub_id", "HP_Peak"]], on=["split_seed", "sub_id"]).rename(columns={"HP_Peak": "y"})
        for m in ("linear", "neural", "rawseries", "L5a", "L5b"):
            Q = P.assign(pred=P[m])
            C = cell_metrics(Q, K)
            dag = Q[Q["bin"] != "pbin>65"].assign(bin="dagger")
            C = pd.concat([C, cell_metrics(dag, K).query("cell == 'all'").assign(cell="dagger")])
            rows.append(C.assign(arm=arm, model=m))
    L = pd.concat(rows, ignore_index=True)
    V = []
    for (arm, cell), g in L.groupby(["arm", "cell"], sort=False):
        t = g.pivot_table(index="split_seed", columns="model", values=metric)
        h = R.PERSIST[hyb_fam]
        for e in ("L5a", "L5b"):
            V.append({"arm": arm, "cell": cell, "ensemble": e, f"median_{metric}": t[e].median(), f"hybrid_median_{metric}": t[h].median(), **rel_verdict(t[e], t[h])})
    V = pd.DataFrame(V)
    keep = V[(V["arm"] == "a_gb") & V["cell"].isin(["all", "dagger"])].groupby("ensemble")["verdict"].apply(lambda v: bool((v == "better").any()))
    return L, V.assign(kept_rel=V["ensemble"].map(keep))


def expf(root, W_gb):
    """exp(z_hat) and y / base of the L4 rung winners, per family and bin: x1.0 fit row (A-GB) and x0.5 update row (r_x05)."""
    win = R.winners(W_gb, K)
    win = win[win["rung"] == "L4"]
    rows = []
    for arm, suffix, label in (("a_gb", "", "x1.0 (A-GB fit row)"), ("r_x05", "@update", "x0.5 (update row)")):
        P = pd.read_csv(Path(root) / arm / "predictions.csv", low_memory=False).merge(bins_of(root, arm), on=["split_seed", "sub_id"])
        for c in SPEC:
            P[c] = P[c].astype(str)
        base = P[P["method"].isin(["paperA_l4a", "paperA_l4b"])][["split_seed", "sub_id", "method", "pred"]].rename(columns={"pred": "base"})
        for w in win.itertuples(index=False):
            spec = dict(zip(SPEC, [str(getattr(w, c)) for c in SPEC]))
            q = P[(P["split_seed"] == w.split_seed) & (P["method"] == spec["method"] + suffix)
                  & (P["anchor"] == spec["anchor"]) & (P["feature_set"] == spec["feature_set"]) & (P["mode"] == spec["mode"])]
            b = base[(base["split_seed"] == w.split_seed) & (base["method"] == f"paperA_{spec['mode']}")]
            rows.append(q.merge(b[["sub_id", "base"]], on="sub_id").assign(family=w.fam, variant=spec["mode"], row=label))
    D = pd.concat(rows, ignore_index=True)
    D["valid"] = D["base"] > 0
    D["exp_z"] = np.where(D["valid"], D["pred"] / D["base"], np.nan)
    D["y_over_base"] = np.where(D["valid"], D["y"] / D["base"], np.nan)
    q = lambda s, p: s.quantile(p)  # noqa: E731
    out = D.groupby(["row", "family", "bin"]).agg(n=("y", "size"), n_invalid_base=("valid", lambda v: int((~v).sum())), exp_z_median=("exp_z", "median"),
                                                 exp_z_q05=("exp_z", lambda s: q(s, 0.05)), exp_z_q90=("exp_z", lambda s: q(s, 0.90)),
                                                 y_over_base_median=("y_over_base", "median")).reset_index()
    return out


def n32(root):
    """Per n = 32 design: inner folds with substations (physics job's lc_dropped) and the job types with ML rows."""
    J = Path(root) / "jobs"
    rows = []
    for f in glob.glob(str(J / "s_gb__s*__d*__n32__physics.lc_dropped.parquet")):
        s, d = map(int, re.search(r"s(\d+)__d(\d+)", f).groups())
        D = pd.read_parquet(f)
        r = D[D["reason"].astype(str).str.startswith("inner CV infeasible")]
        n_in = int(re.search(r"in (\d) of", r["reason"].iloc[0])[1]) if len(r) else 4
        row = {"split_seed": s, "lc_draw": d, "inner_folds_with_substations": n_in}
        for job in ("linear", "tabpfn_d", "tabpfn_r", "tabpfn_h", "cnn_d", "cnn_r", "cnn_h"):
            p = J / f"s_gb__s{s}__d{d}__n32__{job}.lc.parquet"
            row[job] = int(len(pd.read_parquet(p))) if p.exists() else 0
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["split_seed", "lc_draw"]).reset_index(drop=True)


def fmt(v):
    s = R.summ(v)
    return "missing" if s["n"] == 0 else f"{s['median']:.1f} [{s['q05']:.1f}, {s['q90']:.1f}]"


def main(root):
    root = Path(root)
    out = root / "report" / "postreview"
    out.mkdir(parents=True, exist_ok=True)
    frames, norms, chk = build(root)
    S, s_check, s_ok = s_frame(root, norms)
    rec_claim = pd.read_csv(root / "report" / "claim.csv").iloc[0]
    rec_steps = pd.read_csv(root / "report" / "steps.csv")
    res, l0_seq = {}, None
    for metric in ("wape", "nmae"):                                    # WAPE first: its L0 rows (the record's rule) are kept in nMAE
        T, Z, names, W, ref, l0r, ns, used = readings_with(root, frames, metric, S if s_ok else None, l0_seq)
        l0_seq = used
        st = steps_rel(T, ref)
        cl, vs = claim_rel(T, Z, ref, l0r, rec_claim)
        res[metric] = {"T": T, "Z": Z, "names": names, "W": W, "steps": st, "claim": cl, "vs_l0": vs, "n_star": ns}
    Tn, Zn, nn = res["nmae"]["T"], res["nmae"]["Z"], res["nmae"]["names"]
    lad = R.ladder(Tn, Zn, nn, res["nmae"]["n_star"])
    keys = ["A-GB all", "A-CH all"]
    head = [{"rung": "L0", "family": "physics", **{k: f"{fmt(Zn[k])} ({nn[k]})" for k in keys}}]
    head += [{"rung": r, "family": f, **{k: fmt(R.col(Tn[k], (f, r))) for k in keys}} for r in ("L1", "L2", "L3", "L4") for f in R.FAMS]
    L5n, V5n = l5_rel(root, "nmae")
    _, V5w = l5_rel(root, "wape")
    head += [{"rung": "L5", "family": e, **{f"A-{ds} all": fmt(L5n[(L5n["arm"] == arm) & (L5n["model"] == e) & (L5n["cell"] == "all")]["nmae"])
                                           for ds, arm in (("GB", "a_gb"), ("CH", "a_ch"))}} for e in ("L5a", "L5b")]
    head = pd.DataFrame(head)
    nz = norms[norms["cell"] == "all"].groupby("arm").agg(y_max_median=("y_max", "median"), y_max_min=("y_max", "min"), y_max_max=("y_max", "max"),
                                                          mean_over_max_median=("mean_over_max", "median"), mean_over_max_min=("mean_over_max", "min"),
                                                          mean_over_max_max=("mean_over_max", "max")).reset_index()
    nzb = norms.groupby(["arm", "cell"])["y_max"].median().unstack("cell").reset_index()
    # differences against the record (WAPE, 1 pp) and between the relative form in nMAE and in WAPE
    sn = res["nmae"]["steps"].rename(columns={"verdict": "verdict_rel_nmae"})
    sw = res["wape"]["steps"][["reading", "family", "step", "verdict"]].rename(columns={"verdict": "verdict_rel_wape"})
    dif = sn.merge(sw, on=["reading", "family", "step"]).merge(rec_steps[["reading", "family", "step", "verdict", "median"]].rename(
        columns={"verdict": "verdict_record", "median": "median_record_pp"}), on=["reading", "family", "step"], how="left")
    rec_l5 = pd.read_csv(root / "report" / "l5.csv").query("ensemble_of == 'all'")[["arm", "cell", "ensemble", "verdict"]].rename(columns={"verdict": "verdict_record"})
    V5 = V5n.merge(V5w[["arm", "cell", "ensemble", "verdict"]].rename(columns={"verdict": "verdict_rel_wape"}), on=["arm", "cell", "ensemble"]).merge(rec_l5, on=["arm", "cell", "ensemble"], how="left")
    rec_vs = pd.read_csv(root / "report" / "hybrid_vs_L0.csv")[["reading", "verdict"]].rename(columns={"verdict": "verdict_record"})
    VS = res["nmae"]["vs_l0"].merge(res["wape"]["vs_l0"][["reading", "verdict"]].rename(columns={"verdict": "verdict_rel_wape"}), on="reading").merge(rec_vs, on="reading", how="left")
    claims = pd.DataFrame([{"form": "record (WAPE, 1 pp)", **rec_claim.to_dict()}, {"form": "relative, nMAE", **res["nmae"]["claim"]}, {"form": "relative, WAPE", **res["wape"]["claim"]}])
    changed = pd.concat([dif.loc[dif["verdict_rel_nmae"] != dif["verdict_record"], ["reading", "family", "step", "verdict_record", "verdict_rel_nmae", "verdict_rel_wape", "median_rel", "median_record_pp"]].assign(table="steps"),
                         V5.loc[V5["verdict"] != V5["verdict_record"], ["arm", "cell", "ensemble", "verdict_record", "verdict", "verdict_rel_wape", "median_rel"]].rename(columns={"verdict": "verdict_rel_nmae"}).assign(table="L5"),
                         VS.loc[VS["verdict"] != VS["verdict_record"], ["reading", "verdict_record", "verdict", "verdict_rel_wape", "median_rel"]].rename(columns={"verdict": "verdict_rel_nmae"}).assign(table="hybrid vs L0")],
                        ignore_index=True)
    ef = expf(root, R.wide(frames["a_gb"]["wape"], K))
    # S-GB n = 32: two readings (WAPE, the record's metric)
    D32 = n32(root)
    feas = D32[D32["inner_folds_with_substations"] == 4].set_index(["split_seed", "lc_draw"]).index
    S7, _, _ = s_frame(root, norms, keep_designs=feas)
    T7, Z7, n7, _, ref7, l0r7, ns7, _ = readings_with(root, frames, "wape", S7)
    Tw = res["wape"]["T"]
    two = []
    for lab, TT, ZZ, nsx in (("as registered (all designs)", Tw, res["wape"]["Z"], res["wape"]["n_star"]), ("designs feasible for every job type", T7, Z7, ns7)):
        for fam in R.FAMS:
            for r in ("L1", "L2", "L3", "L4"):
                m = nsx[(nsx["family"] == fam) & (nsx["rung"] == r)]
                two.append({"reading": lab, "family": fam, "rung": r, "n32_wape_median": R.col(TT.get("S-GB n=32", pd.DataFrame()), (fam, r)).median(),
                            "n32_units": int(R.col(TT.get("S-GB n=32", pd.DataFrame()), (fam, r)).notna().sum()),
                            "n_star_median": m["n_star_median"].iloc[0] if len(m) else np.nan, "n_star_finite": m["n_star_finite"].iloc[0] if len(m) else ""})
        two.append({"reading": lab, "family": "physics", "rung": "L0", "n32_wape_median": pd.Series(ZZ.get("S-GB n=32", [])).median(),
                    "n32_units": int(pd.Series(ZZ.get("S-GB n=32", [])).notna().sum())})
    two = pd.DataFrame(two)
    st7 = steps_rel(T7, ref7)
    for name, d in {"normalisers_all": nz, "normalisers_by_cell": nzb, "check_recompute": chk, "check_s_testset": pd.DataFrame([{**s_check, "s_in_nmae": s_ok}]),
                    "ladder_nmae": lad, "headline_nmae": head, "steps_rel": dif, "claim_rel": claims, "hybrid_vs_L0_rel": VS, "l5_rel": V5,
                    "l5_seed_nmae": L5n, "changed_vs_record": changed, "expf": ef, "n32_designs": D32, "n32_two_readings": two,
                    "n32_steps_feasible_only_wape_1pp": pd.DataFrame([{"reading": "S-GB n=32 (feasible designs)", "family": f, "step": f"{hi} vs {lo}",
                                                                       **R.verdict(R.col(T7["S-GB n=32"], (f, hi)) - R.col(T7["S-GB n=32"], (f, lo)))}
                                                                      for f in R.FAMS for hi, lo in R.STEPS]) if "S-GB n=32" in T7 else pd.DataFrame()}.items():
        d.to_csv(out / f"{name}.csv", index=False)
    txt = [f"# Iteration 06, post-review (2026-11-16): {LABEL}", "",
           "Generated by `scripts/paperb/iter06_postreview.py` from saved outputs (no refit). The record is `report/` (WAPE, rules as registered).",
           "nMAE = mean|y_hat - y| / max(y) x 100 per seed x arm x cell (each Paper A bin with its own maximum); rung winners chosen by inner-CV WAPE, as in the record.", "",
           "## Checks", R.md(chk), "", "S-GB test sets against A-GB:", R.md(pd.DataFrame([{**s_check, "s_in_nmae": s_ok}])), "",
           "## Normalisers max(y) (kW) and mean/max, cell all (over seeds)", R.md(nz), "", "Median max(y) per cell (kW):", R.md(nzb), "",
           "## Headline (nMAE %, median [5 %, 90 %] over seeds)", R.md(head), "", "## Ladder in nMAE (all readings)", R.md(lad), "",
           "## Rule 2 (claim)", R.md(claims.T.reset_index()), "", "## Outcomes that differ from the record (relative form)", R.md(changed), "",
           "## Rule 1 in relative form", R.md(dif[dif["reading"].isin(["A-GB all", "A-CH all", "S-GB n=62", "S-CH n=all", "R (combined)"])]), "",
           "## Rule 3 in relative form", R.md(V5), "", "## Hybrid vs L0 in relative form", R.md(VS), "",
           "## exp(z_hat) of the L4 winners (Decision 2)", R.md(ef), "",
           "## S-GB n = 32", R.md(D32), "", R.md(two), "", "Rule 1 at n = 32 on the feasible designs (relative form, WAPE):",
           R.md(st7[st7["reading"] == "S-GB n=32"]) if len(st7) else "_missing_", ""]
    (out / "postreview.md").write_text("\n".join(txt), encoding="utf-8")
    print(f"post-review -> {out}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "results" / "iter06_hybrid_ladder"))
    main(ap.parse_args().root)
