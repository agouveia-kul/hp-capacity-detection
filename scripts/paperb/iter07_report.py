"""Iteration 07 report (Part B): transfer table, T1/T2, T3 steps, labels, validity, figures.

Written and committed before any 07 transfer result was read (brief Part B; DECISIONS.md 2026-11-16). It applies the
pre-registered rules of iterations/07-transfer-validation.md as written; every choice the brief leaves open is fixed here.

    python scripts/paperb/iter07_report.py [--root results/iter07_transfer] [--out <dir>] [--blind]

Inputs: <root>/{ch_gb,gb_ch}/predictions.csv (+ physics_diagnostics.csv), <root>/refit_{ch,gb}/predictions.csv,
<root>/l4a_refits.csv, <root>/labels/label_audit.csv, results/iter06_hybrid_ladder/{a_gb,a_ch}/predictions.csv and the persisted
06 manifests (rung winners). Outputs in <out> (default <root>/report): *.csv, report.md, figures/*.{png,pdf}.
`--blind` replaces every prediction by y * exp(N(0, 0.25)) (seed 0) before scoring: a dry run of the code that reveals nothing.

Definitions
- Evaluation set: one seed x direction x cell; cells = all + Paper A bins by actual penetration HP_Count / size (06's rule).
  nMAE = mean|pred - y| / max(y) * 100 (metrics.nmae); y_max (kW) is reported beside it; WAPE is secondary. Bias (own-load check,
  brief) = mean(pred - y) / max(y) * 100. Rows with a non-finite prediction are dropped from a set and counted (06's rule).
- Label: headline = label_def HL (prediction c_src * y_hat, scored on HL). Sensitivity rows: HL_uncorrected, native.
- Row: L0 = one physics method (rung L0); ML = (rung, family), family = linear | tabpfn | cnn (queue families tabpfn_d/_r/_h and
  cnn_d/_r/_h merged; each seed has exactly one winner per rung and family). Secondary rows (domain adaptation, label-free, outside
  the rules): paperA_corr@tgt_s0, paperA_corr_own. 06 never had paperA_corr_own GB->CH: listed n/a.
- In-pool reference (brief): the target pool's own 06 test predictions x c_tgt, scored on HL, same target substations.
  c_tgt = the target pool's seed c from its train substations (label_audit: split train, cell all, quantity c, median).
  ML: the target's 06 rung winner of the same family (persisted manifest spec). L4: where the target's 06 winner is L4b, the 07
  L4a refit of that seed (its in-pool test predictions, refit_<arm>/predictions.csv), else the 06 L4a winner; i.e. the same
  model kind that is transferred. L0: the same method in the target's 06 predictions; paperA_corr@tgt_s0 -> the target's
  paperA_corr (its in-pool form); paperA_corr_own -> the target's paperA_corr_own where 06 has it (GB's is built on the GB
  own-stream pilot, a different construction: flagged), else n/a.
- Transfer gap = nMAE(transfer, HL) - nMAE(in-pool, HL), per row, seed and cell.
- Summaries over seeds: median and the 5 % / 90 % quantiles (numpy, linear interpolation).
Rules (brief; unit = seed, overall cell, nMAE on HL)
- "Better": paired difference A - B < 0 in >= 8 of the seeds present in both **and** median of (A - B) / B <= -5 %. "Worse": > 0 in
  >= 8 and median >= +5 %. Else "no difference". On one evaluation set nMAE = WAPE * mean(y) / max(y), so the per-seed signs and
  relative differences are identical in WAPE: the WAPE verdict is computed as a check and must agree.
- Comparators (DECISIONS 2026-11-16, by source pool): source CH (direction CH->GB): H* = tabpfn L2, D* = cnn L1, 06 hybrid =
  cnn L4; source GB (GB->CH): H* = tabpfn L2, D* = cnn L1, 06 hybrid = tabpfn L4. L0ref = slope_base (both).
- T1: H* vs D* per direction. Confirmed: better in both; partly confirmed: better in one, no difference in the other; refuted:
  worse in either; not confirmed: otherwise (no difference in both).
- T2: H* vs L0ref per direction; "beats physics under transfer" if better in both.
- T3: per family and direction L2 vs L1, L3 vs L2, L4 vs L3; and the 06 hybrid vs D* per direction. 06 rule 2 stays failed.
- The rules are also evaluated on HL_uncorrected and native, labelled sensitivity (outside the rules).
- Per-bin verdicts are reported, never used for an outcome.
Marks: GB-target bins <= 65 % carry † (filler-variability-limited, 05a). Multiplicity: primary 4 comparisons (T1, T2 x 2
directions); T3 18 + 2; no correction, stated in report.md.
"""
try:                                                                  # torch before pandas / pyarrow (see run_queue.py)
    import torch  # noqa: F401
except (ImportError, OSError):
    pass
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb.metrics import nmae  # noqa: E402
from paperb.run_benchmark import PBINS, SPEC_COLS  # noqa: E402

DIR06 = ROOT / "results" / "iter06_hybrid_ladder"
DIRS = {"CH->GB": dict(sub="ch_gb", src="a_ch", tgt="a_gb", tpool="GB"), "GB->CH": dict(sub="gb_ch", src="a_gb", tgt="a_ch", tpool="CH")}
FAM = {"linear": "linear", "tabpfn_d": "tabpfn", "tabpfn_r": "tabpfn", "tabpfn_h": "tabpfn", "cnn_d": "cnn", "cnn_r": "cnn", "cnn_h": "cnn"}
PERSIST = {"linear": "linear", "tabpfn": "neural", "cnn": "rawseries"}
FAMS, RUNGS = ["linear", "tabpfn", "cnn"], ["L1", "L2", "L3", "L4"]
CELLS = ["all"] + [c for c, _, _ in PBINS]
SECONDARY = ["paperA_corr@tgt_s0", "paperA_corr_own"]
L0REF = "slope_base"
COMP = {"CH->GB": {"H*": "L2 tabpfn", "D*": "L1 cnn", "L0ref": L0REF, "06 hybrid": "L4 cnn"},
        "GB->CH": {"H*": "L2 tabpfn", "D*": "L1 cnn", "L0ref": L0REF, "06 hybrid": "L4 tabpfn"}}
QUOTE_D5 = "05a D5 swap deltas (fusion bound, pp): linear -0.33, TabPFN -0.42."
MULT = ("Multiplicity: primary 4 comparisons (T1 and T2 x 2 directions); T3 3 steps x 3 families x 2 directions + 2 "
        "(06 hybrid vs D*). No correction is applied; verdicts are counts and medians over 10 paired seeds.")


def row_of(d):
    """Row label: the physics method for L0, '<rung> <family>' for ML."""
    fam = d["family"].map(FAM)
    return np.where(d["family"] == "physics", d["method"], d["rung"] + " " + fam.fillna(""))


def cell_masks(d):
    pen = (d["HP_Count"] / d["size"]).to_numpy(float)
    return [("all", np.ones(len(d), bool))] + [(c, (pen > lo) & (pen <= hi) if lo > 0 else pen <= hi) for c, lo, hi in PBINS]


def score(d, keys):
    """One row per (keys, cell): nmae, wape, y_max, bias, n_sub, n_dropped."""
    out = []
    for k, g in d.groupby(keys, sort=False):
        for cell, m in cell_masks(g):
            y, p = g["y"].to_numpy(float)[m], g["pred"].to_numpy(float)[m]
            ok = np.isfinite(y) & np.isfinite(p)
            if not ok.any():
                continue
            y, p = y[ok], p[ok]
            out.append({**dict(zip(keys, k)), "cell": cell, "nmae": nmae(y, p), "wape": np.abs(p - y).sum() / y.sum() * 100,
                        "y_max": y.max(), "bias": (p - y).mean() / y.max() * 100, "n_sub": int(ok.sum()), "n_dropped": int((~ok).sum())})
    return pd.DataFrame(out)


def load_transfer(root, blind):
    P = []
    for dr, D in DIRS.items():
        p = pd.read_csv(root / D["sub"] / "predictions.csv", low_memory=False)
        assert set(p["direction"]) == {dr}, (D["sub"], set(p["direction"]))
        P.append(p)
    P = pd.concat(P, ignore_index=True)
    P["row"] = row_of(P)
    return blinded(P, blind)


def blinded(d, blind):
    if blind:
        rng = np.random.default_rng(0)
        d = d.assign(pred=d["y"].to_numpy(float) * np.exp(rng.normal(0, 0.25, len(d))))
    return d


def c_of(root, pool, split="train"):
    A = pd.read_csv(root / "labels" / "label_audit.csv")
    A = A[(A["pool"] == pool) & (A["split"] == split) & (A["cell"] == "all") & (A["quantity"] == "c")]
    return A.set_index("split_seed")["median"]


def inpool(root, P, blind):
    """The target pools' own predictions x c_tgt on HL, for every transfer row that has an in-pool counterpart."""
    refits = pd.read_csv(root / "l4a_refits.csv")
    frames = []
    for dr, D in DIRS.items():
        tgt = D["tgt"]
        hl = P[(P["direction"] == dr) & (P["label_def"] == "HL")].drop_duplicates("sub_id").set_index("sub_id")[["y", "HP_Count", "size", "split_seed"]]
        c_t = c_of(root, D["tpool"])
        p06 = pd.read_csv(DIR06 / tgt / "predictions.csv", low_memory=False)
        p06 = p06[p06["sub_id"].isin(hl.index)]
        ref = pd.read_csv(root / f"refit_{tgt[2:]}" / "predictions.csv", low_memory=False)
        rows = sorted(set(P.loc[P["direction"] == dr, "row"]))
        for s in sorted(hl["split_seed"].unique()):
            for r in rows:
                if r in SECONDARY:
                    m = {"paperA_corr@tgt_s0": "paperA_corr", "paperA_corr_own": "paperA_corr_own"}[r]
                    sel, src = (p06["split_seed"] == s) & (p06["method"] == m), p06
                elif " " not in r:
                    sel, src = (p06["split_seed"] == s) & (p06["method"] == r), p06
                else:
                    rung, fam = r.split(" ")
                    man = json.loads((DIR06 / "models" / tgt / rung / f"s{s}" / PERSIST[fam] / "manifest.json").read_text(encoding="utf-8"))
                    spec, src = man["spec"].split("|"), p06
                    if rung == "L4" and spec[3] == "l4b":
                        rr = refits[(refits["arm"] == tgt) & (refits["split_seed"] == s) & (refits["family"] == PERSIST[fam])]
                        assert len(rr) == 1, (tgt, s, fam)
                        spec, src = rr["spec"].iloc[0].split("|"), ref
                    sel = (src["split_seed"] == s) & np.logical_and.reduce([src[c].astype(str) == v for c, v in zip(SPEC_COLS, spec)])
                g = src[sel]
                if g.empty:
                    continue
                assert g["sub_id"].is_unique and len(g) == int((hl["split_seed"] == s).sum()), (dr, s, r, len(g))
                frames.append(pd.DataFrame({"direction": dr, "row": r, "split_seed": s, "sub_id": g["sub_id"].to_numpy(),
                                            "pred": g["pred"].to_numpy(float) * c_t.loc[s], "y": hl.loc[g["sub_id"], "y"].to_numpy(float),
                                            "HP_Count": hl.loc[g["sub_id"], "HP_Count"].to_numpy(), "size": hl.loc[g["sub_id"], "size"].to_numpy()}))
    return blinded(pd.concat(frames, ignore_index=True), blind)


def verdict(a, b):
    """Paired over seeds: (verdict, n_neg, n, median relative difference %)."""
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    d, rel = j["a"] - j["b"], (j["a"] - j["b"]) / j["b"]
    med = float(rel.median() * 100) if len(j) else np.nan
    if (d < 0).sum() >= 8 and med <= -5:
        v = "better"
    elif (d > 0).sum() >= 8 and med >= 5:
        v = "worse"
    else:
        v = "no difference"
    return v, int((d < 0).sum()), int(len(j)), med


def per_seed(S, dr, row, ld="HL", cell="all", metric="nmae"):
    g = S[(S["direction"] == dr) & (S["row"] == row) & (S["label_def"] == ld) & (S["cell"] == cell)]
    return g.set_index("split_seed")[metric]


def compare(S, dr, a, b, ld="HL", cell="all"):
    v, nneg, n, med = verdict(per_seed(S, dr, a, ld, cell), per_seed(S, dr, b, ld, cell))
    vw = verdict(per_seed(S, dr, a, ld, cell, "wape"), per_seed(S, dr, b, ld, cell, "wape"))[0]
    return {"direction": dr, "A": a, "B": b, "label_def": ld, "cell": cell, "seeds_A<B": nneg, "n_seeds": n,
            "median_rel_diff_pct": med, "verdict": v, "verdict_wape": vw}


def t1_outcome(v):
    if "worse" in v:
        return "refuted"
    if v.count("better") == 2:
        return "confirmed"
    if v.count("better") == 1:
        return "partly confirmed"
    return "not confirmed"


def q(s):
    s = pd.Series(s).dropna()
    return (s.median(), s.quantile(0.05), s.quantile(0.90)) if len(s) else (np.nan,) * 3


def fmt(t, nd=1):
    return "–" if not np.isfinite(t[0]) else f"{t[0]:.{nd}f} [{t[1]:.{nd}f}–{t[2]:.{nd}f}]"


def row_order(rows):
    l0 = [r for r in rows if " " not in r and r not in SECONDARY]
    l0 = [L0REF] + sorted(r for r in l0 if r != L0REF)
    return l0 + [f"{r} {f}" for r in RUNGS for f in FAMS] + SECONDARY


def households(seeds):
    """Distinct HP households: source train and target test per pool and seed (06 memberships, rebuilt)."""
    try:
        from paperb.iter07_labels import arm_cfg, members_of
        from paperb.pools import build_pool
    except Exception as e:  # noqa: BLE001
        return pd.DataFrame(), f"households not computed: {e}"
    out = []
    for arm in ("a_ch", "a_gb"):
        cfg = arm_cfg(arm)
        pool = build_pool(cfg["pool"]["option"], cfg, verbose=False)
        for s in seeds:
            mem = members_of(pool, cfg, s)
            for split in ("train", "test"):
                hh = set().union(*mem.loc[mem["split"] == split, "hp_members"])
                out.append({"arm": arm, "split_seed": s, "split": split, "n_hp_households": len(hh)})
    return pd.DataFrame(out), ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/iter07_transfer")
    ap.add_argument("--out", default=None)
    ap.add_argument("--blind", action="store_true")
    ap.add_argument("--no-households", action="store_true")
    a = ap.parse_args(argv)
    root = ROOT / a.root
    out = Path(a.out) if a.out else root / "report"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    P = load_transfer(root, a.blind)
    I = inpool(root, P, a.blind)
    S = score(P, ["direction", "row", "label_def", "split_seed"])
    SI = score(I, ["direction", "row", "split_seed"]).assign(label_def="inpool")
    G = S[S["label_def"] == "HL"].merge(SI[["direction", "row", "split_seed", "cell", "nmae"]], on=["direction", "row", "split_seed", "cell"],
                                         how="left", suffixes=("", "_inpool"))
    G["gap"] = G["nmae"] - G["nmae_inpool"]
    pd.concat([S, SI]).to_csv(out / "metrics_per_seed.csv", index=False)
    G.to_csv(out / "gap_per_seed.csv", index=False)

    # Table 1: transfer table (median [5-90 %] over seeds), every cell, HL; anchors and validity
    diag = pd.concat([pd.read_csv(root / D["sub"] / "physics_diagnostics.csv").assign(direction=dr) for dr, D in DIRS.items()])
    diag["row"] = row_of(diag)
    win = P[P["label_def"] == "HL"].drop_duplicates(["direction", "row", "split_seed"])
    T1rows, md = [], []
    for dr in DIRS:
        for r in row_order(set(P.loc[P["direction"] == dr, "row"]) | set(SECONDARY)):
            for cell in CELLS:
                g = G[(G["direction"] == dr) & (G["row"] == r) & (G["cell"] == cell)]
                w = win[(win["direction"] == dr) & (win["row"] == r)]
                dg = diag[(diag["direction"] == dr) & (diag["row"] == r)]
                T1rows.append({"direction": dr, "row": r, "cell": cell, "secondary": r in SECONDARY, "n_seeds": g["split_seed"].nunique(),
                               "nmae": q(g["nmae"]), "gap": q(g["gap"]), "nmae_inpool": q(g["nmae_inpool"]), "wape": q(g["wape"]),
                               "bias": q(g["bias"]), "y_max": q(g["y_max"]), "n_sub": q(g["n_sub"]),
                               "size_peak_seeds": int((w["anchor"] == "size_peak").sum()),
                               "invalid_base": q(pd.to_numeric(dg.get("n_invalid_base", pd.Series(dtype=float)), errors="coerce")),
                               "load_error": "; ".join(sorted(set(dg.get("load_error", pd.Series(dtype=str)).dropna().astype(str)) - {"nan"}))})
    T1 = pd.DataFrame(T1rows)
    flat = T1.copy()
    for c in ("nmae", "gap", "nmae_inpool", "wape", "bias", "y_max", "n_sub", "invalid_base"):
        flat[[f"{c}_med", f"{c}_q05", f"{c}_q90"]] = pd.DataFrame(flat[c].tolist(), index=flat.index)
        flat = flat.drop(columns=c)
    flat.to_csv(out / "table1_transfer.csv", index=False)

    # Table 2: T1 / T2; Table 3: T3 steps; sensitivity on the other label definitions
    rules = []
    for ld in ("HL", "HL_uncorrected", "native"):
        for dr, C in COMP.items():
            rules.append({"rule": "T1", **compare(S, dr, C["H*"], C["D*"], ld)})
            rules.append({"rule": "T2", **compare(S, dr, C["H*"], C["L0ref"], ld)})
            for f in FAMS:
                for hi, lo in (("L2", "L1"), ("L3", "L2"), ("L4", "L3")):
                    rules.append({"rule": f"T3 {hi}-{lo}", "family": f, **compare(S, dr, f"{hi} {f}", f"{lo} {f}", ld)})
            rules.append({"rule": "T3 06hybrid-D*", **compare(S, dr, C["06 hybrid"], C["D*"], ld)})
            for cell in CELLS[1:]:
                rules.append({"rule": "T1 (bin, reported only)", **compare(S, dr, C["H*"], C["D*"], ld, cell)})
                rules.append({"rule": "T2 (bin, reported only)", **compare(S, dr, C["H*"], C["L0ref"], ld, cell)})
    R = pd.DataFrame(rules)
    R.to_csv(out / "rules.csv", index=False)
    head = R[(R["label_def"] == "HL") & (R["cell"] == "all")]
    out1 = t1_outcome(head[head["rule"] == "T1"]["verdict"].tolist())
    t2v = head[head["rule"] == "T2"]["verdict"].tolist()
    assert (R["verdict"] == R["verdict_wape"]).all(), "nMAE and WAPE verdicts differ: check the evaluation sets"

    # Table 4: labels
    A = pd.read_csv(root / "labels" / "label_audit.csv")
    L = A.groupby(["pool", "split", "quantity", "cell"]).agg(seed_median=("median", "median"), seed_min=("median", "min"), seed_max=("median", "max"),
                                                             within_q05=("q05", "median"), within_q90=("q90", "median")).reset_index()
    L.to_csv(out / "table4_labels.csv", index=False)
    hh, hh_note = (pd.DataFrame(), "households skipped (--no-households)") if a.no_households else households(sorted(P["split_seed"].unique()))
    if len(hh):
        hh.to_csv(out / "households.csv", index=False)

    figures(G, SI, P, out)
    write_md(out, T1, R, L, hh, hh_note, out1, t2v, a.blind)
    print(f"T1: {out1}; T2: {t2v}; report in {out}")
    return T1, R


def figures(G, SI, P, out):
    for name, fn in (("nmae_by_rung", fig_rungs), ("gap_by_rung_bin", fig_gap), ("c_distribution", fig_c)):
        fig = fn(G, SI, P)
        for ext in ("png", "pdf"):
            fig.savefig(out / "figures" / f"{name}.{ext}", dpi=150, bbox_inches="tight")
        plt.close(fig)


def fig_rungs(G, SI, P):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    for ax, dr in zip(axes, DIRS):
        g = G[(G["direction"] == dr) & (G["cell"] == "all")]
        for k, f in enumerate(FAMS):
            med = [q(g.loc[g["row"] == f"{r} {f}", "nmae"]) for r in RUNGS]
            x = np.arange(1, 5) + (k - 1) * 0.08
            ax.errorbar(x, [m[0] for m in med], yerr=[[m[0] - m[1] for m in med], [m[2] - m[0] for m in med]], marker="o", capsize=3,
                        color=f"C{k}", label=f"{f} transfer")
            ax.plot(x, [g.loc[g["row"] == f"{r} {f}", "nmae_inpool"].median() for r in RUNGS], ls="--", marker="x", color=f"C{k}",
                    alpha=0.7, label=f"{f} in-pool")
        l0 = q(g.loc[g["row"] == L0REF, "nmae"])
        ax.axhline(l0[0], color="k", lw=1, label=f"L0ref {L0REF} (transfer)")
        ax.axhline(g.loc[g["row"] == L0REF, "nmae_inpool"].median(), color="k", lw=1, ls=":", label="L0ref in-pool")
        ax.set_xticks(range(1, 5), RUNGS)
        ax.set_title(dr)
        ax.set_ylabel("nMAE on HL (%), median [5–90 %] over seeds")
    axes[1].legend(fontsize=7)
    return fig


def fig_gap(G, SI, P):
    fig, axes = plt.subplots(2, 3, figsize=(13, 6), sharey="row")
    for i, dr in enumerate(DIRS):
        for j, f in enumerate(FAMS):
            ax = axes[i, j]
            g = G[G["direction"] == dr]
            for k, r in enumerate(RUNGS):
                ax.plot(range(len(CELLS)), [g.loc[(g["row"] == f"{r} {f}") & (g["cell"] == c), "gap"].median() for c in CELLS], marker="o", label=r)
            ax.plot(range(len(CELLS)), [g.loc[(g["row"] == L0REF) & (g["cell"] == c), "gap"].median() for c in CELLS], "k--", label="L0ref")
            ax.axhline(0, color="grey", lw=0.5)
            ax.set_xticks(range(len(CELLS)), [c.replace("pbin", "") + ("†" if DIRS[dr]["tpool"] == "GB" and c in CELLS[1:4] else "") for c in CELLS], fontsize=7)
            ax.set_title(f"{dr} {f}", fontsize=9)
            if j == 0:
                ax.set_ylabel("transfer gap (pp nMAE), median")
    axes[0, 2].legend(fontsize=7)
    return fig


def fig_c(G, SI, P):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for ax, (dr, D) in zip(axes, DIRS.items()):
        d = P[P["direction"] == dr].drop_duplicates(["sub_id", "label_def"]).pivot(index="sub_id", columns="label_def", values="y")
        meta = P[P["direction"] == dr].drop_duplicates("sub_id").set_index("sub_id")
        c = (d["HL"] / d["native"]).rename("c").to_frame().join(meta[["HP_Count", "size"]])
        data = [c.loc[m, "c"].dropna() for _, m in cell_masks(c)]
        ax.boxplot(data, labels=CELLS, showfliers=False)
        cs = P[P["direction"] != dr].drop_duplicates("split_seed").set_index("split_seed")["c_src"]
        ax.scatter(np.full(len(cs), 1.25), cs, color="r", s=12, label="c_src per seed (train)")
        ax.set_title(f"{D['tpool']}: c = HL / native, test substations")
        ax.tick_params(axis="x", labelsize=7)
        ax.legend(fontsize=7)
    return fig


def write_md(out, T1, R, L, hh, hh_note, out1, t2v, blind):
    def tab(df):
        cols = list(df.columns)
        return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)])
    lines = [f"# Iteration 07 report{' (BLIND DRY RUN: synthetic predictions)' if blind else ''}", "",
             "Headline label HL (c_src x prediction); nMAE (%) median [5–90 %] over seeds; gap = transfer - in-pool (pp). "
             "Secondary rows (domain adaptation, label-free) are marked (DA) and are outside the rules.", "",
             f"**T1 (H\\* vs D\\*): {out1}.** T2 (H\\* vs L0ref) per direction: {', '.join(f'{d}: {v}' for d, v in zip(DIRS, t2v))}"
             f"{' — beats physics under transfer' if t2v.count('better') == 2 else ''}.", "", MULT, ""]
    for dr in DIRS:
        t = T1[(T1["direction"] == dr) & (T1["cell"] == "all")]
        lines += [f"## Table 1, {dr} (overall)", "", tab(pd.DataFrame({
            "row": t["row"] + np.where(t["secondary"], " (DA)", ""), "nMAE": t["nmae"].map(fmt), "gap": t["gap"].map(fmt),
            "in-pool": t["nmae_inpool"].map(fmt), "WAPE": t["wape"].map(fmt), "bias": t["bias"].map(fmt),
            "max y (kW)": t["y_max"].map(lambda x: fmt(x, 0)), "size_peak seeds": t["size_peak_seeds"],
            "invalid ŝ": t["invalid_base"].map(lambda x: fmt(x, 0)), "note": t["load_error"]})), ""]
        tb = T1[(T1["direction"] == dr) & (T1["cell"] != "all")]
        pv = tb.assign(v=tb["nmae"].map(fmt) + " / " + tb["gap"].map(lambda x: f"{x[0]:+.1f}" if np.isfinite(x[0]) else "–")).pivot(index="row", columns="cell", values="v")
        pv = pv.reindex([r for r in row_order(set(tb["row"])) if r in pv.index])[CELLS[1:]]
        if DIRS[dr]["tpool"] == "GB":
            pv.columns = [c + ("†" if c in CELLS[1:4] else "") for c in pv.columns]
        lines += [f"### {dr} per Paper A bin: nMAE median [5–90 %] / gap median", "", tab(pv.reset_index()), ""]
        bias = tb.pivot(index="row", columns="cell", values="bias").map(lambda x: f"{x[0]:+.1f}" if np.isfinite(x[0]) else "–")
        lines += [f"### {dr} bias (mean(pred - y) / max y, %), median per bin", "", tab(bias.reindex([r for r in row_order(set(tb['row'])) if r in bias.index])[CELLS[1:]].reset_index()), ""]
    lines += ["† GB target bins <= 65 %: filler-variability-limited (05a). " + QUOTE_D5,
              "In-pool reference of paperA_corr_own CH->GB: GB's own 06 paperA_corr_own (built on the GB own-stream pilot, a "
              "different construction from the CH whole-house pilot).", ""]
    cols = ["rule", "family", "direction", "cell", "A", "B", "label_def", "seeds_A<B", "n_seeds", "median_rel_diff_pct", "verdict"]
    lines += ["## Table 2, T1 / T2 (HL, overall; per bin reported only)", "",
              tab(R[R["rule"].str.startswith(("T1", "T2")) & (R["label_def"] == "HL")].reindex(columns=cols).round(1).fillna("")), "",
              "## Table 3, T3 steps (HL, overall). 06 rule 2 stays failed on (a).", "",
              tab(R[R["rule"].str.startswith("T3") & (R["label_def"] == "HL")].reindex(columns=cols).round(1).fillna("")), "",
              "## Sensitivity: rules on HL_uncorrected and native (outside the rules)", "",
              tab(R[(R["label_def"] != "HL") & (R["cell"] == "all")].reindex(columns=cols).round(1).fillna("")), "",
              "## Table 4, labels (median over seeds of the seed medians [seed min–max]; within-seed 5–90 %)", "",
              tab(L.round(4)), ""]
    if len(hh):
        lines += ["## HP households (distinct), median [min–max] over seeds", "",
                  tab(hh.groupby(["arm", "split"])["n_hp_households"].agg(["median", "min", "max"]).reset_index()), ""]
    else:
        lines += [hh_note, ""]
    lines += ["Honesty note: H\\* and D\\* were selected in-pool (06 inner-CV WAPE) and their in-pool test results are known; the "
              "transfer targets were never used by any selection; c uses source train labels only; T_design is metadata.", ""]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
