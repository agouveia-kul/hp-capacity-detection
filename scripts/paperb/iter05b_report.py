"""05b Stage 1 report: the pre-registered verdict (D / I-or-features / inconclusive, and F) per family and overall, per scope
(overall and Paper A penetration bin), plus the Task 3 tables and the learning-curve figure. Written and committed before any
Stage 1 result was read (CLAUDE.md hard rule 12); the rule is iterations/05b-data-limit-test.md, "Pre-registered decision rule".

Inputs: <stage1>/arm1/metrics_lc.csv (n in {16, 32, 62, 100, 200}, 10 seeds x 2 draws), <stage1>/arm2/metrics.csv (n = all,
20 seeds), <stage1>/arm2/pilots.csv (number of train HP households at n = all). Outputs: <stage1>/report/*.md|csv and figures.

Choices that the brief leaves open, fixed here before the results:
- Learning-curve framework (Arm 1): candidates per family are Arm 1's configurations (netfit x size x {direct-log, residual};
  CNN raw x size x {direct-log, residual}). The n = all point is Arm 2 restricted to these configurations, seeds of Arm 1,
  draw 0 (arm1 config comment), placed at n_all = the split's number of train HP households (pilot "all").
- Family winner = lowest inner-CV WAPE (`wape_inner`) per (seed, draw, n, family) (lc_fit.family_winners); a bin's WAPE is the
  overall winner's WAPE in that bin (the winner is not re-chosen per bin).
- Best physics row = per (n, scope), the row with the lowest median test WAPE over seed x draws among PHYS_CAND (03b Task 6
  rows + paperA_corr_own, A7); never HDH, anchor-only or oracle rows.
- Condition 1 (data helps): pairs (seed, draw) at n = 100 with the same seed at n = all; drop = WAPE(100) - WAPE(all);
  met iff median drop >= 1 pp and drop > 0 in >= 80 % of pairs.
- Condition 2: at n = all, dWAPE = family winner - best physics < 0 in >= 80 % of seeds and median dWAPE <= -1 pp (03b
  criterion, Arm 1 framework, 10 seeds), OR the per-seed fitted asymptote a < that seed's best-physics WAPE at n = all in
  >= 80 % of seeds (fit to the median over draws at each n, n = all included).
- D = condition 1 and condition 2. Not data-limited (I or features) = |median drop| < 1 pp and median dWAPE >= 0 at each of
  n = 100, 200 and all. Otherwise inconclusive, with n* median [5-90 %] over seeds. Overall D if any family is D (5 families).
- F = the raw-series family is D, or its Arm 2 winner (20 seeds, full configuration set) meets the 03b criterion against every
  tabular family's Arm 2 winner.
- The headline (Arm 2, 20 seeds) applies the 03b criterion to every configuration and every family winner, per scope.

    python scripts/paperb/iter05b_report.py [--stage1 results/iter05b_data_limit/stage1]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb.lc_fit import CONFIG_COLS, FAMILY_OF, family_winners, seed_fits, summarise  # noqa: E402

SCOPES = ["all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"]
FLAGGED = {"pbin<=15", "pbin15-35", "pbin35-65"}                       # filler-variability-limited (A2)
PHYS_CAND = ["paperA_sh_mh", "paperA_sh_mh_station", "paperA_cal", "paperA_corr", "paperA_corr_all", "paperA_corr_cal",
             "paperA_corr_own", "slope_only", "slope_base", "calibrated_delta"]
FAMILIES = ["linear", "kernel", "trees", "neural", "rawseries"]
WIN_SHARE, WIN_PP, DROP_PP = 0.8, -1.0, 1.0
REF_ML = {"Lasso [size] netfit direct": ("Lasso", "size", "netfit", "direct", "log"),
          "Lasso [size] netfit residual": ("Lasso", "size", "netfit", "residual", "log"),
          "XGBoost [size] netfit direct": ("XGBoost", "size", "netfit", "direct", "log")}
KEYS = ["split_seed", "lc_draw", "n"]


def wide(m, keys):
    """Long metric rows -> one row per (keys + configuration): wape per scope, wape_inner, wape_train (cell 'all')."""
    m = m[m["target"] == "HP_Peak"] if "target" in m else m
    w = m[(m["metric"] == "wape") & m["cell"].isin(SCOPES)].pivot_table(index=keys + CONFIG_COLS, columns="cell", values="value", aggfunc="first")
    w.columns = [f"wape_{c}" for c in w.columns]
    x = m[(m["cell"] == "all") & m["metric"].isin(["wape_inner", "wape_train"])].pivot_table(index=keys + CONFIG_COLS, columns="metric", values="value", aggfunc="first")
    return w.join(x, how="left").reset_index()


def lc_table(a1, a2, n_all):
    """Learning-curve candidates and physics rows on the Arm 1 configuration set, n = all from Arm 2 (see module doc)."""
    L = wide(a1.rename(columns={"n_train_hp": "n"}), KEYS)
    arm1_cfg = set(map(tuple, L.loc[L["method"].isin(FAMILY_OF), CONFIG_COLS].to_numpy()))
    A = wide(a2.assign(lc_draw=0, n=a2["split_seed"].map(n_all)), KEYS)
    keep = A["method"].isin(PHYS_CAND) | A[CONFIG_COLS].apply(tuple, axis=1).isin(arm1_cfg)
    A = A[keep & A["split_seed"].isin(L["split_seed"].unique())]
    return pd.concat([L.assign(is_all=False), A.assign(is_all=True)], ignore_index=True)


def best_physics(T, by):
    """Per value of column `by` and scope: the PHYS_CAND row with the lowest median test WAPE -> {(value, scope): method}."""
    P = T[T["method"].isin(PHYS_CAND)]
    out = {}
    for g, d in P.groupby(by):
        for s in SCOPES:
            med = d.groupby("method")[f"wape_{s}"].median().dropna() if f"wape_{s}" in d else pd.Series(dtype=float)
            if len(med):
                out[(g, s)] = med.idxmin()
    return out


def paired(T, winners):
    """Family-winner WAPE and paired dWAPE vs the best physics row at the same n, long over scopes."""
    bp = best_physics(T, "n")
    P = T[T["method"].isin(PHYS_CAND)].set_index(KEYS + ["method"])
    rows = []
    for r in winners.to_dict("records"):                                  # dict access: bin columns are not identifiers
        for s in SCOPES:
            w = r.get(f"wape_{s}", np.nan)
            if (r["n"], s) not in bp or not np.isfinite(w):
                continue
            ph = P[f"wape_{s}"].get((r["split_seed"], r["lc_draw"], r["n"], bp[(r["n"], s)]), np.nan)
            rows.append({"split_seed": r["split_seed"], "lc_draw": r["lc_draw"], "n": r["n"], "is_all": bool(r.get("is_all", False)),
                         "family": r["family"], "scope": s, "winner": f"{r['method']}|{r['anchor']}|{r['feature_set']}|{r['mode']}",
                         "wape": w, "phys": bp[(r["n"], s)], "wape_phys": ph, "d": w - ph})
    return pd.DataFrame(rows)


def criterion(d):
    d = pd.Series(d, dtype=float).dropna()
    return {"n": len(d), "wins": int((d < 0).sum()), "median_d": float(d.median()) if len(d) else np.nan,
            "meets": bool(len(d) and (d < 0).mean() >= WIN_SHARE and d.median() <= WIN_PP)}


def verdicts(D):
    """D = paired() of the learning-curve framework -> one row per (family, scope) with the rule's inputs and verdict."""
    rows = []
    for (fam, s), g in D.groupby(["family", "scope"]):
        at_all = g[g["is_all"]]
        w100 = g[g["n"] == 100].set_index(["split_seed", "lc_draw"])["wape"]
        wall = at_all.set_index("split_seed")["wape"]
        drop = pd.Series({k: v - wall[k[0]] for k, v in w100.items() if k[0] in wall.index}, dtype=float)
        c1 = bool(len(drop) and drop.median() >= DROP_PP and (drop > 0).mean() >= WIN_SHARE)
        c2a = criterion(at_all["d"])
        fit_in = g.groupby(["split_seed", "n"])["wape"].median().reset_index().rename(columns={"n": "n_train_hp"})
        fits = seed_fits(fit_in.assign(lc_draw=0), at_all.set_index("split_seed")["wape_phys"].to_dict())
        c2b = bool(len(fits) and fits["a_below_phys"].mean() >= WIN_SHARE)
        med_d = {n: g.loc[g["n"] == n, "d"].median() for n in (100, 200)}
        med_d["all"] = at_all["d"].median()
        not_dl = bool(len(drop) and abs(drop.median()) < DROP_PP and all(np.isfinite(v) and v >= 0 for v in med_d.values()))
        verdict = "D" if c1 and (c2a["meets"] or c2b) else "I or features" if not_dl else "inconclusive"
        ns = summarise(fits["n_star"].replace(np.inf, np.nan)) if len(fits) else summarise([])
        rows.append({"family": fam, "scope": s, "flagged": s in FLAGGED, "drop100_all_median": drop.median() if len(drop) else np.nan,
                     "drop_share_pos": (drop > 0).mean() if len(drop) else np.nan, "n_pairs": len(drop), "cond1": c1,
                     "all_wins": f"{c2a['wins']}/{c2a['n']}", "all_median_d": c2a["median_d"], "cond2_criterion": c2a["meets"],
                     "asym_below_share": fits["a_below_phys"].mean() if len(fits) else np.nan, "cond2_asymptote": c2b,
                     "n_star_median": ns["median"], "n_star_q05": ns["q05"], "n_star_q90": ns["q90"],
                     "n_star_inf_seeds": int(np.isinf(fits["n_star"]).sum()) if len(fits) else 0,
                     "fit_flags": int((fits["flag_c_bound"] | fits["flag_a_neg"]).sum()) if len(fits) else 0, "verdict": verdict})
    V = pd.DataFrame(rows)
    if len(V):
        V = V.assign(_o=V["scope"].map(SCOPES.index)).sort_values(["family", "_o"]).drop(columns="_o").reset_index(drop=True)
    return V


def f_verdict(V, H):
    """F per scope: raw-series is D, or its Arm 2 winner meets the 03b criterion against every tabular family's winner."""
    out = {}
    for s in SCOPES:
        rs_d = bool(((V["family"] == "rawseries") & (V["scope"] == s) & (V["verdict"] == "D")).any())
        h = H[H["scope"] == s].pivot_table(index="split_seed", columns="family", values="wape")
        beats = "rawseries" in h and all(criterion(h["rawseries"] - h[f])["meets"] for f in FAMILIES[:-1] if f in h)
        out[s] = rs_d or bool(beats)
    return out


def fmt(v, nd=1):
    return "–" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{nd}f}"


def band(x):
    s = summarise(x)
    return f"{fmt(s['median'])} [{fmt(s['q05'])}–{fmt(s['q90'])}]"


def md(df):
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * df.shape[1]]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])


def scope_name(s):
    return s + (" †" if s in FLAGGED else "")


def headline(a2, d5_dir):
    """Arm 2 (20 seeds): reference rows and family winners, median [5-90] per scope, 03b criterion per configuration and winner."""
    A = wide(a2.assign(lc_draw=0, n=-1), KEYS)
    W = family_winners(A[A["method"].isin(FAMILY_OF)], KEYS).assign(is_all=True)
    H = paired(A.assign(is_all=True), W)
    bp = best_physics(A, "n")
    rows, crit = [], []
    for label, cfg in [*[(m, (m, "none", "-", "-", "-")) for m in ["slope_base", "paperA_corr", "paperA_cal", "paperA_sh_mh", "paperA_corr_own"]],
                       *REF_ML.items()]:
        r = A[A[CONFIG_COLS].apply(tuple, axis=1) == cfg]
        if len(r):
            rows.append({"row": label, **{scope_name(s): band(r[f"wape_{s}"]) for s in SCOPES}})
    for fam, g in H.groupby("family"):
        rows.append({"row": f"{fam} winner", **{scope_name(s): band(g.loc[g["scope"] == s, "wape"]) for s in SCOPES}})
        for s in SCOPES:
            c = criterion(g.loc[g["scope"] == s, "d"])
            crit.append({"family winner": fam, "scope": scope_name(s), "best physics": bp.get((-1, s), "–"), "seeds ML < physics": f"{c['wins']}/{c['n']}",
                         "median dWAPE pp": fmt(c["median_d"], 2), "beats physics": c["meets"]})
    per_cfg = []
    ml = A[A["method"].isin(FAMILY_OF)]
    for s in SCOPES:
        if (-1, s) not in bp:
            continue
        ph = A[A["method"] == bp[(-1, s)]].set_index("split_seed")[f"wape_{s}"]
        n_beat = sum(criterion(g.set_index("split_seed")[f"wape_{s}"] - ph)["meets"] for _, g in ml.groupby(CONFIG_COLS))
        per_cfg.append({"scope": scope_name(s), "configurations": ml.groupby(CONFIG_COLS).ngroups, "meeting the criterion": n_beat})
    d5 = d5_dir / "mapping_d5_family_winners.csv"
    d5t = pd.read_csv(d5).groupby(["family", "cell"])["dWAPE"].median().unstack().reindex(columns=SCOPES) if d5.exists() else None
    return pd.DataFrame(rows), pd.DataFrame(crit), pd.DataFrame(per_cfg), H, W, d5t


def figure(D, T, out):
    """WAPE vs n (log x): family winners and the best physics row per n, median and 5-90 % band over seed x draws; B* 03b overlay."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    cols = dict(zip(FAMILIES + ["physics"], ["#2a78d6", "#eb6834", "#2f9e44", "#9c36b5", "#c92a2a", "#52514e"]))
    g = D[D["scope"] == "all"]
    for fam, d in g.groupby("family"):
        q = d.groupby("n")["wape"].quantile([0.05, 0.5, 0.9]).unstack()
        ax.plot(q.index, q[0.5], "o-", color=cols.get(fam), label=f"{fam} winner")
        ax.fill_between(q.index, q[0.05], q[0.9], color=cols.get(fam), alpha=0.12)
    q = g.drop_duplicates(["split_seed", "lc_draw", "n"]).groupby("n")["wape_phys"].quantile([0.05, 0.5, 0.9]).unstack()
    ax.plot(q.index, q[0.5], "s--", color=cols["physics"], label="best physics row")
    ax.fill_between(q.index, q[0.05], q[0.9], color=cols["physics"], alpha=0.10)
    b = ROOT / "results" / "iter03b_fair_test" / "summary_lc.csv"
    if b.exists():
        s = pd.read_csv(b)
        s = s[(s["metric"] == "wape") & (s["cell"] == "all")]
        phys = s[s["method"].isin(PHYS_CAND)]
        top = phys[phys["n_train_hp"] == phys["n_train_hp"].max()].sort_values("median")["method"].iloc[0]
        for lab, d in (("B* 03b best physics", phys[phys["method"] == top]), ("B* 03b Lasso residual", s[(s["method"] == "Lasso") & (s["mode"] == "residual")])):
            ax.plot(d["n_train_hp"], d["median"], ":", color="#868e96", marker="x" if "Lasso" in lab else "+", label=lab)
        ax.axvline(62, color="#adb5bd", lw=0.8)
        ax.text(62, ax.get_ylim()[1], " n = 62 (B*)", va="top", fontsize=8, color="#868e96")
    ax.set(xscale="log", xlabel="distinct train HP households n", ylabel="WAPE [%] (test)", title="GB dataset, learning curve (overall)")
    ticks = sorted(set(g["n"].unique()) | {62})
    ax.set_xticks(ticks, [str(int(t)) for t in ticks])
    ax.minorticks_off()
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig_learning_curve.{ext}", dpi=150)
    plt.close(fig)


def main(stage1):
    out = stage1 / "report"
    (out).mkdir(parents=True, exist_ok=True)
    a1, a2 = pd.read_csv(stage1 / "arm1" / "metrics_lc.csv"), pd.read_csv(stage1 / "arm2" / "metrics.csv")
    pil = stage1 / "arm2" / "pilots.csv"
    n_all = (pd.read_csv(pil).query("pilot == 'all' and n == 'main'").drop_duplicates("split_seed").set_index("split_seed")["n_hh"].astype(int).to_dict()
             if pil.exists() else {})
    n_all = {s: n_all.get(s, 292) for s in a2["split_seed"].unique()}
    T = lc_table(a1, a2, n_all)
    W = family_winners(T[T["method"].isin(FAMILY_OF)], KEYS)
    D = paired(T, W)
    V = verdicts(D)
    head, crit, per_cfg, H, W2, d5 = headline(a2, ROOT / "results" / "iter05a_pool")
    F = f_verdict(V, H)
    V.to_csv(out / "verdict.csv", index=False)
    D.to_csv(out / "lc_paired.csv", index=False)
    lc = D[D["scope"] == "all"].groupby(["family", "n"]).agg(
        WAPE=("wape", band), dWAPE_vs_physics=("d", lambda x: fmt(x.median(), 2)), win_share=("d", lambda x: fmt((x < 0).mean(), 2)),
        seed_draws=("d", "size")).reset_index()
    bv = T.merge(W[KEYS + CONFIG_COLS], on=KEYS + CONFIG_COLS).assign(family=lambda d: d["method"].map(FAMILY_OF)).groupby(["family", "n"]).agg(
        train=("wape_train", lambda x: fmt(x.median())), inner_cv=("wape_inner", lambda x: fmt(x.median())), test=("wape_all", lambda x: fmt(x.median()))).reset_index()
    wins = W.groupby(["family", "n", "method"]).size().rename("wins").reset_index()
    wins2 = W2.assign(config=W2[CONFIG_COLS].astype(str).agg("|".join, axis=1)).groupby(["family", "config"]).size().rename("seeds").reset_index()
    asym = V[V["scope"] == "all"][["family", "n_star_median", "n_star_q05", "n_star_q90", "n_star_inf_seeds", "asym_below_share", "fit_flags"]]
    figure(D, T, out)
    vt = V.assign(scope=V["scope"].map(scope_name))[["family", "scope", "drop100_all_median", "drop_share_pos", "cond1", "all_wins", "all_median_d",
                                                    "cond2_criterion", "asym_below_share", "cond2_asymptote", "verdict"]]
    overall = {s: ("D (" + ", ".join(V[(V["scope"] == s) & (V["verdict"] == "D")]["family"]) + ")") if ((V["scope"] == s) & (V["verdict"] == "D")).any()
               else ("I or features" if (V[V["scope"] == s]["verdict"] == "I or features").all() else "inconclusive") for s in SCOPES}
    txt = ["# 05b Stage 1 report (generated by scripts/paperb/iter05b_report.py)", "",
           "† = filler-variability-limited bin (A2). Five families are tested (multiplicity). GB labels are 30-min: compare gaps to physics across datasets, not levels.", "",
           "## Verdict per family (learning-curve framework, Arm 1 configurations, 10 seeds x 2 draws; n = all from Arm 2)", "", md(vt.round(2)), "",
           "## Overall verdict and F", "", md(pd.DataFrame([{"scope": scope_name(s), "overall": overall[s], "F": F[s]} for s in SCOPES])), "",
           "## Learning curve (overall)", "", md(lc), "", "## Asymptote and n* (overall)", "", md(asym.round(2)), "",
           "## Bias-variance (family winners, median WAPE)", "", md(bv), "", "## Win frequency, learning curve", "", md(wins), "",
           "## Headline, Arm 2 (20 seeds): median [5-90 %] WAPE", "", md(head), "",
           "## 03b criterion per family winner, Arm 2", "", md(crit), "", "## 03b criterion per configuration, Arm 2", "", md(per_cfg), "",
           "## Win frequency, Arm 2", "", md(wins2), ""]
    if d5 is not None:
        txt += ["## 05a D5 swap test, family winners (median dWAPE swapped - real, pp; the bound on the fusion error)", "", md(d5.round(2).reset_index()), ""]
    (out / "stage1_report.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt[:12]))
    return V, F


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage1", default=str(ROOT / "results" / "iter05b_data_limit" / "stage1"))
    main(Path(ap.parse_args().stage1))
