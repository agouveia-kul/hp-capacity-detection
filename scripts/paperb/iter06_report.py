"""Iteration 06 report (Part B): the ladder, step, claim and L5 tables, the checks the review asked for, and the figures.

Written and committed before any 06 result was read (DECISIONS.md 2026-10-12). It applies the pre-registered rules of
iterations/06-hybrid-ladder.md as written; every choice the brief leaves open is fixed here, in this docstring.

    python scripts/paperb/iter06_report.py [--root results/iter06_hybrid_ladder]

Inputs (merged by the queue): <root>/{a_gb,a_ch,r_x05,r_x15,r_rep}/metrics.csv, <root>/s_gb/metrics_lc.csv, <arm>/pilots.csv,
<arm>/l4.csv, and the persisted L4 winners <root>/models/{a_gb,a_ch}/L4/s<seed>/<family>/ (L5). Outputs: <root>/report/*.csv,
report.md, figures/*.{png,pdf}. A missing arm or family is reported as missing, never filled in.

Definitions
- Families: linear (Linear, Ridge, Lasso, ElasticNet, PLS), tabpfn, cnn. Rung of a configuration: scale_model.rung.
- Rung winner: per (arm, seed [, draw, n], family, rung) the configuration with the lowest inner-CV WAPE, ties to the configuration
  label; L4 = the winner over l4a and l4b. Test columns are never read for a choice. In the R arms the configuration is the
  A-GB winner of the seed (the queue runs nothing else there).
- L0 reference: of paperA_corr, paperA_corr_own, paperA_cal, slope_base, the row with the lowest median WAPE over the units of the
  reading (the brief's rule; the four rows are always listed).
- "Better" (brief): the paired difference is < 0 in >= 80 % of the units (8 of 10 seeds; seed x draws on S) and its median is
  <= -1 pp. "Worse": the mirror image. Otherwise "no difference".
Readings
- A: WAPE of the rung winners at n = all, GB (a_gb) and CH (a_ch), overall and per Paper A bin; unit = seed.
- S (decision 2026-10-12, cut 2): anchor size and one feature set per rung (L1 whdd / raw, L2-L4 netfit / rawphys). Primary reading:
  GB at n = 62, unit = seed x draw. Second reading (B4): CH at n = all on the same configurations, unit = seed. n*: per seed, the
  curve a + b n^-c (lc_fit) through the medians over draws at n = 32, 62, 100 and n = all, where n = all is A-GB restricted to the S
  configurations and its n is the seed's number of train HP households; n* = the n at which the curve reaches the seed's L0
  reference at n = all. The n = all point of S therefore differs from axis A.
- R, as degradations (brief: "compare the degradation instead of the level"): (i) x0.5 and x1.5: WAPE of the frozen row minus the
  WAPE of the same persisted model at x1.0 (its A-GB row); (ii) replication: WAPE of the configuration refit on the replication
  year minus its A-GB WAPE. A comparison on R is "better" if it is better on at least two of the three readings and worse on none
  ("worse": the mirror image). L0 on R(i): paperA_corr_s0unscaled (frozen s0) minus A-GB's paperA_corr; on R(ii): A-GB's L0
  reference row on the replication year minus itself on A-GB. The update rows (C7: L4 `@update`, and paperA_corr with the scaled
  s0) are listed next to them and are outside the rules.
Rules
- Rule 1: per family, L2 - L1, L3 - L2, L4 - L3 on every reading. A cross-family summary ("better" / "worse" only if every family
  agrees, else "mixed") is given with and without the CNN; a step whose summary changes is flagged CNN-dependent.
- Rule 2: the hybrid = L4 of the family whose L4 winner has the lowest median inner-CV WAPE over the seeds on A-GB; the best pure
  data-driven model = the (family, L1 or L2) with the lowest such median. (a) median WAPE of the hybrid on A-GB, overall, at most
  1 pp above the other; (b) the hybrid better on S (primary reading) and on R. T is pending 07: with (a), "holds" if S and R are
  both better, "open" if one is, "fails" if neither or if (a) fails. The same is computed without the CNN family; a different
  outcome is flagged CNN-dependent. The hybrid against L0 is listed on every reading.
- Rule 3: L5a (plain average) and L5b (r-hat gate, ensemble.py) of the families' persisted L4 winners against the hybrid, on GB:
  kept if "better" by the criterion above on all test substations or on the union of the filler-variability-limited bins
  (penetration <= 65 %). CH and the no-CNN ensemble are listed.
Marks: † = filler-variability-limited bin (GB, penetration <= 65 %). CNN rows on GB carry "inherited hyperparameters" (the seed's
05b Arm 2 values, decision 2026-10-12). Multiplicity: 5 rungs x 3 families x 2 datasets x 3 axes, stated in report.md.
"""
try:                                                                  # torch before pandas / pyarrow (see run_queue.py)
    import torch  # noqa: F401
except (ImportError, OSError):
    pass
import argparse  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb import ensemble as EN  # noqa: E402
from paperb import lc_fit as LC  # noqa: E402
from paperb.scale_model import rung  # noqa: E402

SPEC = ["method", "anchor", "feature_set", "mode", "target_transform"]
FAMS = {"linear": ["Linear", "Ridge", "Lasso", "ElasticNet", "PLS"], "tabpfn": ["TabPFN"], "cnn": ["CNN"]}
FAM_OF = {m: f for f, ms in FAMS.items() for m in ms}
PERSIST = {"linear": "linear", "tabpfn": "neural", "cnn": "rawseries"}       # family folders of persist.py
L0 = ["paperA_corr", "paperA_corr_own", "paperA_cal", "slope_base"]
BINS = ["pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"]
CELLS = ["all", *BINS]
STEPS = [("L2", "L1"), ("L3", "L2"), ("L4", "L3")]
S_SETS = ("whdd", "netfit", "raw", "rawphys", "-")
K = ["split_seed"]
QUOTES = ("05a D5 swap deltas (fusion bound, pp): linear -0.33, TabPFN -0.42. 05b Arm 7, frozen Stage 1 models, dWAPE vs x1.0 at "
          "x0.5 / x1.5: linear +2.5 / +7.0, TabPFN +1.9 / +8.5, CNN -0.4 / +4.0; best physics row -7.6 / +8.1 (refit). "
          "The frozen robustness of L2 / L3 is therefore partly known from 05b Arm 7 (B3).")


def load(root, arm, name="metrics.csv"):
    f = Path(root) / arm / name
    return pd.read_csv(f, low_memory=False) if f.exists() else pd.DataFrame()


def wide(M, keys):
    """One row per (keys, configuration): WAPE per cell, the inner-CV WAPE, and kind (fit / frozen / update), family, rung."""
    if M.empty:
        return pd.DataFrame(columns=[*keys, *SPEC, *CELLS, "wape_inner", "kind", "base", "fam", "rung"])
    M = M[(M["target"] == "HP_Peak") & M["cell"].isin(CELLS)]
    W = M[M["metric"] == "wape"].pivot_table(index=keys + SPEC, columns="cell", values="value", aggfunc="first").reindex(columns=CELLS)
    inner = M[(M["metric"] == "wape_inner") & (M["cell"] == "all")].groupby(keys + SPEC)["value"].first()
    W = W.join(inner.rename("wape_inner")).reset_index()
    W["kind"] = np.where(W["method"].str.contains("@"), W["method"].str.split("@").str[-1], "fit")
    W["base"] = W["method"].str.split("@").str[0]
    W["fam"] = W["base"].map(FAM_OF)
    W["rung"] = [rung((b, a, fs, mo, tt)) if isinstance(f, str) else ("L0" if b in L0 else None)
                 for b, f, a, fs, mo, tt in W[["base", "fam", *SPEC[1:]]].itertuples(index=False)]
    return W


def winners(W, keys, kind="fit"):
    """The rung winner of every (keys, family, rung) among the rows of `kind`: lowest inner-CV WAPE, ties to the label."""
    D = W[(W["kind"] == kind) & W["fam"].notna()].copy()
    if D.empty:
        return D
    D["_lab"], D["_cv"] = D[SPEC].astype(str).agg("|".join, axis=1), D["wape_inner"].fillna(np.inf)
    g = D.sort_values([*keys, "fam", "rung", "_cv", "_lab"], kind="mergesort").groupby([*keys, "fam", "rung"], sort=False)
    if ((g["_cv"].min() == np.inf) & (g.size() > 1)).any():
        raise ValueError("several configurations without an inner-CV WAPE in one (unit, family, rung): no rule to choose")
    return g.head(1).drop(columns=["_lab", "_cv"]).reset_index(drop=True)


def table(D, keys, col="all"):
    """units x (family, rung) frame of `col`."""
    return D.pivot_table(index=keys, columns=["fam", "rung"], values=col, aggfunc="first") if len(D) else pd.DataFrame()


def l0_ref(W, keys, col="all"):
    """(name, per-unit Series) of the L0 reference among the four L0 rows of W."""
    P = W[W["method"].isin(L0)]
    if P.empty:
        return None, pd.Series(dtype=float)
    name = P.groupby("method")[col].median().idxmin()
    return name, P[P["method"] == name].set_index(keys)[col]


def summ(v):
    v = pd.Series(v, dtype=float).dropna()
    return {"median": v.median(), "q05": v.quantile(0.05), "q90": v.quantile(0.90), "n": len(v)} if len(v) else {"median": np.nan, "q05": np.nan, "q90": np.nan, "n": 0}


def verdict(d, share=0.8, min_pp=1.0):
    """The brief's criterion on a Series of paired differences (pp)."""
    d = pd.Series(d, dtype=float).dropna()
    if d.empty:
        return {"n": 0, "n_neg": 0, "median": np.nan, "verdict": "missing"}
    v = ("better" if (d < 0).mean() >= share and d.median() <= -min_pp else
         "worse" if (d > 0).mean() >= share and d.median() >= min_pp else "no difference")
    return {"n": len(d), "n_neg": int((d < 0).sum()), "median": float(d.median()), "verdict": v}


def combine_r(vs):
    """R verdict from its three readings: better on at least two and worse on none (and the mirror image)."""
    vs = [v for v in vs if v != "missing"]
    if not vs:
        return "missing"
    return "better" if vs.count("better") >= 2 and "worse" not in vs else "worse" if vs.count("worse") >= 2 and "better" not in vs else "no difference"


def col(T, key):
    """Column (family, rung) of a reading; all-NaN on the reading's units when that family or rung was not run."""
    return T[key] if len(T) and key in T.columns else pd.Series(np.nan, index=T.index if len(T) else None, dtype=float)


def degradation(W, gb, kind):
    """Per (seed, family, rung): WAPE of the `kind` row minus the A-GB WAPE of the same configuration (all cells)."""
    D = winners(W, K, kind)
    R = gb[gb["kind"] == "fit"][[*K, "base", *SPEC[1:], *CELLS]].rename(columns={c: f"{c}_ref" for c in CELLS})
    D = D.merge(R, on=[*K, "base", *SPEC[1:]], how="left")
    for c in CELLS:
        D[f"d_{c}"] = D[c] - D[f"{c}_ref"]
    return D


def readings(root):
    """Everything the tables need: {reading: units x (family, rung)}, {reading: L0 Series}, and the wide frames."""
    gb, ch = wide(load(root, "a_gb"), K), wide(load(root, "a_ch"), K)
    lc = wide(load(root, "s_gb", "metrics_lc.csv"), [*K, "lc_draw", "n_train_hp"])
    on_s = lambda W: W[W["anchor"].isin(["size", "none"]) & W["feature_set"].isin(S_SETS)]          # noqa: E731
    T, Z, names = {}, {}, {}
    for ds, W in (("GB", gb), ("CH", ch)):
        A = winners(W, K)
        for c in CELLS:
            T[f"A-{ds} {c}"] = table(A, K, c)
            names[f"A-{ds} {c}"], Z[f"A-{ds} {c}"] = l0_ref(W, K, c)
    S = winners(lc, [*K, "lc_draw", "n_train_hp"])
    for n in sorted(S["n_train_hp"].unique()) if len(S) else []:
        key = f"S-GB n={int(n)}"
        T[key] = table(S[S["n_train_hp"] == n], [*K, "lc_draw"])
        names[key], Z[key] = l0_ref(lc[lc["n_train_hp"] == n], [*K, "lc_draw"])
    for ds, W in (("GB", gb), ("CH", ch)):                             # n = all on the S configurations
        key = f"S-{ds} n=all"
        T[key] = table(winners(on_s(W), K), K)
        names[key], Z[key] = l0_ref(W, K)
    for key, arm in (("R x0.5", "r_x05"), ("R x1.5", "r_x15")):
        W = wide(load(root, arm), K)
        D = degradation(W, gb, "frozen")
        T[key], T[f"{key} update"] = table(D, K, "d_all"), table(degradation(W, gb, "update"), K, "d_all")
        ref = gb[gb["method"] == "paperA_corr"].set_index(K)["all"]
        for k2, m in ((key, "paperA_corr_s0unscaled"), (f"{key} update", "paperA_corr")):
            names[k2], Z[k2] = m, W[W["method"] == m].set_index(K)["all"].sub(ref).dropna()
    rep = wide(load(root, "r_rep"), K)
    T["R rep"] = table(degradation(rep, gb, "fit"), K, "d_all")
    T["R rep level"] = table(winners(rep, K), K)
    nm = names.get("A-GB all")
    names["R rep"], Z["R rep"] = nm, (rep[rep["method"] == nm].set_index(K)["all"].sub(gb[gb["method"] == nm].set_index(K)["all"]).dropna()
                                      if nm else pd.Series(dtype=float))
    names["R rep level"], Z["R rep level"] = l0_ref(rep, K)
    return T, Z, names, {"gb": gb, "ch": ch, "lc": lc, "S": S}


def step_table(T):
    """Rule 1: every step x family x reading, the R combination, and the cross-family summary with and without the CNN."""
    rows = []
    for key in [k for k in T if not k.endswith(("update", "level"))]:
        for fam in FAMS:
            for hi, lo in STEPS:
                rows.append({"reading": key, "family": fam, "step": f"{hi} vs {lo}", **verdict(col(T[key], (fam, hi)) - col(T[key], (fam, lo)))})
    R = pd.DataFrame(rows)
    comb = (R[R["reading"].isin(["R x0.5", "R x1.5", "R rep"])].groupby(["family", "step"])["verdict"].apply(lambda v: combine_r(list(v))).reset_index()
            .assign(reading="R (combined)"))
    R = pd.concat([R, comb], ignore_index=True)
    agree = lambda v: v.iloc[0] if v.nunique() == 1 else "mixed"                                   # noqa: E731
    X = pd.DataFrame({"all_families": R.groupby(["reading", "step"], sort=False)["verdict"].apply(agree),
                      "without_cnn": R[R["family"] != "cnn"].groupby(["reading", "step"], sort=False)["verdict"].apply(agree)}).reset_index()
    return R, X.assign(cnn_dependent=X["all_families"] != X["without_cnn"])


def claim(T, Z, gb, fams):
    """Rule 2 with the families `fams` -> dict (inputs and outcome) and the hybrid-vs-L0 rows."""
    cv = winners(gb, K)
    cv = cv[cv["fam"].isin(fams)].groupby(["fam", "rung"])["wape_inner"].median()
    if not (cv.index.get_level_values("rung") == "L4").any() or not cv.index.get_level_values("rung").isin(["L1", "L2"]).any():
        return {"families": "+".join(fams), "outcome": "missing"}, pd.DataFrame()
    hyb = (cv.xs("L4", level="rung").idxmin(), "L4")
    dd = cv[cv.index.get_level_values("rung").isin(["L1", "L2"])].idxmin()
    A = T["A-GB all"]
    gap = col(A, hyb).median() - col(A, dd).median()
    s = verdict(col(T.get("S-GB n=62", pd.DataFrame()), hyb) - col(T.get("S-GB n=62", pd.DataFrame()), dd))
    r = {k: verdict(col(T[k], hyb) - col(T[k], dd)) for k in ("R x0.5", "R x1.5", "R rep")}
    r_all = combine_r([v["verdict"] for v in r.values()])
    a_ok, n_better = bool(gap <= 1.0), (s["verdict"] == "better") + (r_all == "better")
    out = "fails" if not a_ok or n_better == 0 else "holds regardless of T" if n_better == 2 else "open: needs T (07)"
    res = {"families": "+".join(fams), "hybrid": f"{hyb[0]} L4", "best_pure_dd": f"{dd[0]} {dd[1]}", "cv_hybrid": cv[hyb], "cv_dd": cv[dd],
           "A_median_hybrid": col(A, hyb).median(), "A_median_dd": col(A, dd).median(), "A_gap_pp": gap, "a_holds": a_ok,
           "S_n62": s["verdict"], "S_median": s["median"], "S_n_neg": f"{s['n_neg']}/{s['n']}",
           **{f"{k} verdict": v["verdict"] for k, v in r.items()}, **{f"{k} median": v["median"] for k, v in r.items()}, "R": r_all, "T": "pending 07",
           "outcome": out}
    vs = [{"reading": k, "hybrid": res["hybrid"], "L0": Z[k].name if hasattr(Z[k], "name") else "", **verdict(col(T[k], hyb).sub(Z[k]).dropna() if len(Z[k]) else [])}
          for k in T if not k.endswith(("update", "level")) and k in Z]
    return res, pd.DataFrame(vs)


def wape(y, p, m):
    return 100 * float(np.abs(p[m] - y[m]).sum() / y[m].sum()) if m.any() and y[m].sum() > 0 else np.nan


def l5_table(root, arm, hyb_fam):
    """Rule 3: per-seed WAPE of each family's persisted L4 winner, L5a and L5b (all families, and without the CNN) in the cells
    all / dagger (penetration <= 65 %) / each Paper A bin, and the verdicts against the hybrid's family."""
    l4, mdir = load(root, arm, "l4.csv"), Path(root) / "models" / arm / "L4"
    if l4.empty or not mdir.exists():
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    rows, gates = [], []
    for d in sorted(mdir.glob("s*"), key=lambda p: int(p.name[1:])):
        seed = int(d.name[1:])
        s = l4[l4["split_seed"] == seed].set_index("sub_id")
        for tag, fams in (("all", None), ("no_cnn", [PERSIST["linear"], PERSIST["tabpfn"]])):
            P, g, used = EN.l5_seed(d, s["r_hat"], fams)
            if len(used) < 2:
                continue
            y, pen = s.loc[P.index, "HP_Peak"].to_numpy(float), (s.loc[P.index, "HP_Count"] / s.loc[P.index, "size"]).to_numpy(float)
            cells = {"all": np.ones(len(y), bool), "dagger": pen <= 0.65, "pbin<=15": pen <= 0.15, "pbin15-35": (pen > 0.15) & (pen <= 0.35),
                     "pbin35-65": (pen > 0.35) & (pen <= 0.65), "pbin>65": pen > 0.65}
            rows += [{"split_seed": seed, "ensemble_of": tag, "cell": c, "model": m, "wape": wape(y, P[m].to_numpy(float), mask)}
                     for c, mask in cells.items() for m in P.columns]
            gates.append({"split_seed": seed, "ensemble_of": tag, "n_edges": len(g.edges), "edges": list(np.round(g.edges, 4)), "cv_wape_oof": g.cv_wape,
                          **{f"w_{f}": w for f, w in zip(used, g.W[-1])}})
    L = pd.DataFrame(rows)
    if L.empty:
        return L, L, pd.DataFrame(gates)
    V = []
    for (tag, c), g in L.groupby(["ensemble_of", "cell"], sort=False):
        t = g.pivot_table(index="split_seed", columns="model", values="wape", dropna=False)       # an empty cell stays, as NaN
        h = PERSIST.get(hyb_fam) if PERSIST.get(hyb_fam) in t else None
        for e in ("L5a", "L5b"):
            V.append({"arm": arm, "ensemble_of": tag, "cell": c, "ensemble": e, "hybrid_family": hyb_fam, "median_wape": t[e].median(),
                      **(verdict(t[e] - t[h]) if h else verdict([]))})
    V = pd.DataFrame(V)
    keep = V[V["cell"].isin(["all", "dagger"])].groupby(["ensemble_of", "ensemble"])["verdict"].apply(lambda v: bool((v == "better").any())).rename("kept")
    return L, V.merge(keep.reset_index(), on=["ensemble_of", "ensemble"]), pd.DataFrame(gates)


def n_star(T, Z, pilots):
    """n* per (family, rung): seed-wise curve through n = 32, 62, 100 (median over draws) and n = all on the S configurations."""
    n_all = pilots[(pilots["pilot"] == "all") & (pilots["n"].astype(str) == "main")].groupby("split_seed")["n_hh"].first() if len(pilots) else pd.Series(dtype=float)
    pts = [(int(k.split("=")[1]), T[k]) for k in T if k.startswith("S-GB n=") and not k.endswith("all")]
    rows = []
    for fam in FAMS:
        for r in ("L1", "L2", "L3", "L4"):
            L = [pd.DataFrame({"split_seed": t.index.get_level_values("split_seed"), "n_train_hp": n, "lc_draw": t.index.get_level_values("lc_draw"),
                               "wape": col(t, (fam, r)).to_numpy()}) for n, t in pts if (fam, r) in t]
            a = col(T.get("S-GB n=all", pd.DataFrame()), (fam, r))
            if not L or a.empty or n_all.empty:
                continue
            L.append(pd.DataFrame({"split_seed": a.index, "n_train_hp": n_all.reindex(a.index).to_numpy(), "lc_draw": 0, "wape": a.to_numpy()}))
            F = LC.seed_fits(pd.concat(L).dropna(), Z["S-GB n=all"].to_dict())
            rows.append({"family": fam, "rung": r, "n_star_median": F["n_star"].median(), "n_star_finite": f"{int(np.isfinite(F['n_star']).sum())}/{len(F)}",
                         "flag_c_bound": int(F["flag_c_bound"].sum()), "asymptote_median": F["a"].median()})
    return pd.DataFrame(rows)


def checks(root, W):
    """The review's extra tables: L4b alpha per seed, invalid-slope share per bin, zero-residual rows, CNN initialisations."""
    out = {}
    al = []
    for arm in ("a_gb", "a_ch", "r_rep"):
        P = load(root, arm, "pilots.csv")
        if len(P) and "l4b_alpha" in P:
            al.append(P[(P["pilot"] == "l4")][["split_seed", "l4b_alpha", "l4b_cv_mse", "n_cf_fallback", "l4a_kappa"]].assign(arm=arm))
    out["alpha"] = pd.concat(al) if al else pd.DataFrame()
    inv = []
    for arm in ("a_gb", "a_ch"):
        L = load(root, arm, "l4.csv")
        if len(L):
            L = L[L["split"] == "test"].assign(pen=lambda d: d["HP_Count"] / d["size"], invalid=lambda d: ~(d["s_hat"] > 0))
            L["bin"] = pd.cut(L["pen"], [0, 0.15, 0.35, 0.65, np.inf], labels=BINS)
            inv.append(L.groupby(["split_seed", "bin"], observed=True)["invalid"].mean().groupby("bin", observed=True).agg(["median", "max"]).reset_index().assign(arm=arm))
    out["invalid_slope"] = pd.concat(inv) if inv else pd.DataFrame()
    zr = []
    for ds, key in (("GB", "gb"), ("CH", "ch")):
        t = W[key][W[key]["method"].isin(["paperA_corr", "paperA_l4a", "paperA_l4b"])].pivot_table(index=K, columns="method", values="all")
        for m in ("paperA_l4a", "paperA_l4b"):
            if m in t and "paperA_corr" in t:
                zr.append({"dataset": ds, "row": m, "median_wape": t[m].median(), "paperA_corr_median": t["paperA_corr"].median(), **verdict(t[m] - t["paperA_corr"])})
    out["zero_residual"] = pd.DataFrame(zr)
    ini = []
    for arm in ("a_gb", "a_ch"):
        M = load(root, arm)
        if len(M):
            I = M[M["metric"].astype(str).str.startswith("init") & (M["cell"] == "all")]
            if len(I):
                P = I.pivot_table(index=[*K, *SPEC], columns="metric", values="value")
                tw = P[[c for c in P if c.endswith("test_wape")]]
                ini.append({"arm": arm, "fits": len(P), "share_not_first_init": float((P["init_chosen"] != 0).mean()),
                            "median_spread_test_wape_pp": float((tw.max(axis=1) - tw.min(axis=1)).median()), "max_spread_test_wape_pp": float((tw.max(axis=1) - tw.min(axis=1)).max())})
    out["cnn_inits"] = pd.DataFrame(ini)
    return out


def ladder(T, Z, names, ns):
    """Rows L0-L4 x family; columns = the readings (median [5 %, 90 %] over the units)."""
    keys = [k for k in T if k.startswith(("A-", "S-", "R "))]
    rows = [{"rung": "L0", "family": "physics", **{k: fmt(Z.get(k, [])) + (f" ({names.get(k)})" if names.get(k) else "") for k in keys}}]
    for r in ("L1", "L2", "L3", "L4"):
        for fam in FAMS:
            row = {"rung": r, "family": fam + (" (inherited hyperparameters on GB)" if fam == "cnn" else ""), **{k: fmt(col(T[k], (fam, r))) for k in keys}}
            if len(ns):
                m = ns[(ns["family"] == fam) & (ns["rung"] == r)]
                row["S-GB n*"] = f"{m['n_star_median'].iloc[0]:.0f} (finite {m['n_star_finite'].iloc[0]})" if len(m) else "missing"
            rows.append(row)
    return pd.DataFrame(rows)


def step_pivot(steps, rd):
    """family x step rows, one column per reading: verdict (median difference in pp, units with a negative difference)."""
    S = steps[steps["reading"].isin(rd)].copy()
    if S.empty:
        return S
    S["cell"] = [v if pd.isna(m) else f"{v} ({m:+.1f} pp, {int(k)}/{int(n)})" for v, m, k, n in S[["verdict", "median", "n_neg", "n"]].fillna({"n_neg": 0, "n": 0}).itertuples(index=False)]
    return S.pivot_table(index=["family", "step"], columns="reading", values="cell", aggfunc="first", sort=False).reindex(columns=[r for r in rd if r in set(S["reading"])]).reset_index()


def fmt(v):
    s = summ(v)
    return "missing" if s["n"] == 0 else f"{s['median']:.1f} [{s['q05']:.1f}, {s['q90']:.1f}] (n={s['n']})"


def md(d):
    if d is None or len(d) == 0:
        return "_missing_"
    d = d.copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
    return "\n".join(["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * d.shape[1]] + ["| " + " | ".join(map(str, r)) + " |" for r in d.itertuples(index=False)])


def figures(out, T, Z, root):
    fd = out / "figures"
    fd.mkdir(parents=True, exist_ok=True)
    col_f = {"linear": "#1f77b4", "tabpfn": "#d62728", "cnn": "#2ca02c"}
    rl = ["L1", "L2", "L3", "L4"]

    def save(fig, name):
        fig.tight_layout()
        for ext in ("png", "pdf"):
            fig.savefig(fd / f"{name}.{ext}", dpi=150)
        plt.close(fig)

    panels = [k for k in ("A-GB all", "A-CH all", "S-GB n=62", "R x0.5", "R x1.5", "R rep") if k in T and len(T[k])]
    if panels:                                                         # WAPE (or degradation) against the rung, per reading
        fig, axs = plt.subplots(1, len(panels), figsize=(3.2 * len(panels), 3.2), squeeze=False)
        for ax, k in zip(axs[0], panels):
            for fam in FAMS:
                ax.plot(rl, [col(T[k], (fam, r)).median() for r in rl], "o-", color=col_f[fam], label=fam)
            if len(Z.get(k, [])):
                ax.axhline(pd.Series(Z[k]).median(), color="k", ls="--", lw=0.8, label="L0")
            ax.set(title=k, ylabel="dWAPE (pp)" if k.startswith("R") else "WAPE (%)")
        axs[0][0].legend(fontsize=7)
        save(fig, "wape_vs_rung")
    pts = sorted((int(k.split("=")[1]), k) for k in T if k.startswith("S-GB n=") and not k.endswith("all") and len(T[k]))
    if pts:                                                            # learning curves L0-L4 (S configurations)
        fig, axs = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True)
        for ax, fam in zip(axs, FAMS):
            for r in rl:
                ax.plot([n for n, _ in pts], [col(T[k], (fam, r)).median() for _, k in pts], "o-", label=r)
            ax.plot([n for n, _ in pts], [pd.Series(Z[k]).median() for _, k in pts], "k--", label="L0")
            ax.set(title=fam, xlabel="train HP households", xscale="log")
        axs[0].set_ylabel("WAPE (%), median")
        axs[0].legend(fontsize=7)
        save(fig, "learning_curves")
    bars = [k for k in ("R x0.5", "R x0.5 update", "R x1.5", "R x1.5 update", "R rep") if k in T and len(T[k])]
    if bars:                                                           # robustness: degradation of L1-L4 per family
        fig, axs = plt.subplots(1, len(bars), figsize=(3.2 * len(bars), 3.2), squeeze=False, sharey=True)
        for ax, k in zip(axs[0], bars):
            for i, fam in enumerate(FAMS):
                ax.bar(np.arange(4) + 0.27 * (i - 1), [col(T[k], (fam, r)).median() for r in rl], 0.25, color=col_f[fam], label=fam)
            if len(Z.get(k, [])):
                ax.axhline(pd.Series(Z[k]).median(), color="k", ls="--", lw=0.8, label="L0")
            ax.set(title=k, xticks=range(4), xticklabels=rl)
        axs[0][0].set_ylabel("dWAPE vs x1.0 / main year (pp)")
        axs[0][0].legend(fontsize=7)
        save(fig, "robustness")
    L = load(root, "a_gb", "l4.csv")
    if len(L):                                                         # learned m_hat (L4b) against the true m_h, test substations, by station
        L = L[(L["split"] == "test") & L["m_true"].notna()]
        fig, ax = plt.subplots(figsize=(4, 4))
        for st, g in L.groupby("station"):
            ax.scatter(g["m_true"], g["m_l4b"], s=6, alpha=0.5)
        lim = [0, float(np.nanquantile(L[["m_true", "m_l4b"]].to_numpy(), 0.995))]
        ax.plot(lim, lim, "k--", lw=0.8)
        ax.set(xlabel="true m_h (s_h of the HP aggregate / HP_Peak)", ylabel="learned m_hat_h (L4b)", xlim=lim, ylim=lim, title="GB, test substations, colour = station")
        save(fig, "m_hat_vs_true")


def main(root):
    root = Path(root)
    out = root / "report"
    out.mkdir(parents=True, exist_ok=True)
    T, Z, names, W = readings(root)
    for k in Z:
        Z[k] = pd.Series(Z[k], dtype=float).rename(names.get(k) or "")
    ns = n_star(T, Z, load(root, "a_gb", "pilots.csv"))
    steps, summary = step_table(T)
    fams_here = [f for f in FAMS if (f, "L4") in T["A-GB all"]] if len(T["A-GB all"]) else []
    res, vs_l0 = claim(T, Z, W["gb"], fams_here) if fams_here else ({"outcome": "missing"}, pd.DataFrame())
    res_nc, _ = claim(T, Z, W["gb"], [f for f in fams_here if f != "cnn"]) if len(fams_here) > 1 else ({"outcome": "missing"}, None)
    C = pd.DataFrame([res, res_nc]).assign(cnn_dependent=res.get("outcome") != res_nc.get("outcome"))
    hyb = str(res.get("hybrid", " ")).split(" ")[0]
    l5 = {arm: l5_table(root, arm, hyb) for arm in ("a_gb", "a_ch")}
    V5 = pd.concat([v[1] for v in l5.values()]) if any(len(v[1]) for v in l5.values()) else pd.DataFrame()
    ck = checks(root, W)
    lad = ladder(T, Z, names, ns)
    n_hp = {arm: int(M.loc[(M["metric"] == "wape") & (M["cell"] == "all"), "n_hp_households"].max()) for arm in ("a_gb", "a_ch", "r_rep")
            if len(M := load(root, arm)) and "n_hp_households" in M}
    for name, d in {"ladder": lad, "steps": steps, "steps_summary": summary, "claim": C, "hybrid_vs_L0": vs_l0, "l5": V5, "n_star": ns,
                    "l5_seed_wape": pd.concat([v[0].assign(arm=a) for a, v in l5.items() if len(v[0])]) if any(len(v[0]) for v in l5.values()) else pd.DataFrame(),
                    "l5_gates": pd.concat([v[2].assign(arm=a) for a, v in l5.items() if len(v[2])]) if any(len(v[2]) for v in l5.values()) else pd.DataFrame(),
                    **{f"check_{k}": v for k, v in ck.items()}}.items():
        d.to_csv(out / f"{name}.csv", index=False)
    piv = lambda rd: step_pivot(steps, rd)                                                         # noqa: E731
    main_r = ["A-GB all", "A-CH all", "S-GB n=62", "S-CH n=all", "R x0.5", "R x1.5", "R rep", "R (combined)"]
    txt = ["# Iteration 06 report: the hybrid ladder", "",
           "Generated by `scripts/paperb/iter06_report.py` (rules and open choices: its docstring; committed before any result was read).",
           "WAPE in %, median [5 %, 90 %] over the units (seeds; seed x draws on S). † = filler-variability-limited (GB, penetration <= 65 %: "
           "bins <=15, 15-35, 35-65). Test HP households: " + ", ".join(f"{a} {n}" for a, n in n_hp.items()) + " (train: GB main 274, replication 226, B* 62).",
           "Multiplicity: 5 rungs x 3 families x 2 datasets x 3 axes; every selection is by inner CV. Cross-pool comparisons use gaps, not levels "
           "(GB labels are 30-min, B* 15-min).", "", QUOTES, "",
           "**CNN on GB: inherited hyperparameters** (the seed's 05b Arm 2 values, one inner-CV pass per configuration); this favours L1 and n = all, "
           "i.e. it works against the hybrid. Outcomes that change without the CNN family are flagged CNN-dependent.",
           "**Axis S** uses L1 = whdd x size (CNN raw) and L2-L4 = netfit x size (CNN rawphys). Its n = all point is A-GB restricted to these "
           "configurations and differs from axis A; rules 1-2 on S compare these fixed configurations only.",
           "**Axis R** is a degradation (dWAPE vs x1.0, or vs the main year). The `update` columns (L4 with s0 re-estimated from the scaled train "
           "fillers; L0 = paperA_corr with the scaled s0) are the deployment mode and are outside the rules.",
           "Within a pool, L4 - L3 mainly measures the corrected against the uncorrected base (the scale is close to the pilot constant).", "",
           "## 1. Ladder table", md(lad), "", "A-GB per Paper A bin (†: the first three):", md(ladder({k: T[k] for k in T if k.startswith("A-GB pbin")}, Z, names, [])), "",
           "## 2. Step table (rule 1)", md(piv(main_r)), "", "Per Paper A bin on A-GB:", md(piv([f"A-GB {b}" for b in BINS])), "",
           "Cross-family summary and CNN dependence:", md(summary[summary["reading"].isin(main_r)]), "",
           "## 3. Claim table (rule 2)", md(C.T.reset_index().rename(columns={"index": "", 0: "all families", 1: "without CNN"})), "",
           "The hybrid against L0:", md(vs_l0), "", "## 4. L5 table (rule 3)", md(V5), "",
           "## 5. Checks", "L4b alpha per seed:", md(ck["alpha"]), "", "Invalid corrected slope (s_hat <= 0), share of test substations per bin (median, max over seeds):",
           md(ck["invalid_slope"]), "", "Zero-residual L4 rows against paperA_corr (A, overall):", md(ck["zero_residual"]), "",
           "CNN initialisations (B1; diagnostics only):", md(ck["cnn_inits"]), "", "S-GB n*:", md(ns), ""]
    (out / "report.md").write_text("\n".join(txt), encoding="utf-8")
    figures(out, T, Z, root)
    print(f"report -> {out / 'report.md'}")
    return {"T": T, "Z": Z, "steps": steps, "summary": summary, "claim": C, "l5": V5, "ladder": lad, "checks": ck, "n_star": ns}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "results" / "iter06_hybrid_ladder"))
    main(ap.parse_args().root)
