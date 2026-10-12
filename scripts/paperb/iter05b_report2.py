"""05b Stage 2 report (Task 3 tables 5-8, the S test, amendment A12). Written and committed before any Stage 2 result was read
(CLAUDE.md hard rule 12); rules: iterations/05b-data-limit-test.md ("Pre-registered decision rule", A7, A10, A12).

Inputs: <stage2>/<arm>/metrics.csv (arm3_*: metrics_lc.csv), <stage1>/arm2/metrics.csv, <stage1>/refit/carry_forward_models.csv,
<stage1>/report/verdict.csv, results/iter05a_pool/mapping_d5_family_winners.csv. Outputs: <stage2>/report/stage2_report.md, *.csv,
fig_error_decomposition.png|pdf.

Choices that the brief and A12 leave open, fixed here before the results:
- Family rows. In the frozen arms (2-CPU, 7, 4-O1, 3, 6) a carried family's row is its one frozen Arm 2 spec per seed (A10; no
  selection). Arm 2 rows are those specs in the Stage 1 file. In Arm 5 (B*, tuned) the family winner is the lowest inner-CV WAPE
  (lc_fit.family_winners; neural = FFNN and TabPFN together); FFNN alone and TabPFN alone are also reported (the FFNN fair test).
- Best physics row = per arm and scope, the row with the lowest median test WAPE over seeds among PHYS_CAND (Stage 1 list). In Arm 7
  `paperA_corr` uses s0 of the scaled train fillers and `paperA_corr_s0unscaled` (the mis-specified correction) is ALSO a candidate:
  the reading of A12 that is hardest for ML. A12 (b) is also shown without it, as a sensitivity (not the rule).
- 03b criterion: dWAPE = family row - best physics row, paired per seed; met iff dWAPE < 0 in >= 80 % of the seeds and the median
  dWAPE <= -1 pp (8/10 or 16/20).
- A12, per carried family. (a): the family meets the 03b criterion overall in Arm 2 (20 seeds, its frozen spec = its inner-CV winner)
  and in Arm 6 (10 seeds). (b): the `@frozen` row beats the best physics row of the same scaled arm in >= 8/10 seeds, at x0.5 and at
  x1.5 (no median condition, as A12 is written), overall; "every bin above 15 %" = pbin15-35, pbin35-65 and pbin>65. The outcome is
  given per family; the lead outcome is read for the families together only if they agree, else "families differ: Alex decides".
- Arm 7 deltas vs x1.0, paired over seeds 0-9: physics rows vs the same row in Arm 2 (`paperA_corr_s0unscaled` vs Arm 2's
  `paperA_corr`); refit family rows vs `arm2_cpu` (same device); `@frozen` rows vs the family's Arm 2 row (the saved model itself).
- S test (pre-registered): per family and n in {62, all}, drop = WAPE(10 per cell) - WAPE(40 per cell), paired per seed; S iff the
  median drop >= 1 pp and drop > 0 in >= 80 % of the seeds. Overall S if it holds for any family at any n (3 families x 2 n tested).
- Error decomposition of `paperA_sh_mh` per seed and scope: fill contamination = WAPE(net) - WAPE(O1), scale dispersion = WAPE(O1) -
  WAPE(O2), fit noise = WAPE(O2); medians over seeds. B* split (A7): (i) fillers' response = WAPE(real) - WAPE(O1a pool), (ii) HP
  homes' own non-HP response = WAPE(real) - WAPE(O1b pool), for `paperA_sh_mh`, `paperA_corr`, `paperA_corr_own` and `slope_base`.
- `paperA_corr_own` on B* (Arm 5): paired difference to the best label-calibrated row (lowest median among LABEL_CAL) and to
  `paperA_corr`, per scope.
- Used HP households = `n_hp_households` of the `slope_base` rows `at_bound_share_train` / `_test` (the households that are members
  of the split's substations).

    python scripts/paperb/iter05b_report2.py
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
from paperb.iter05b_report import PHYS_CAND, SCOPES, band, fmt, md, scope_name, wide  # noqa: E402
from paperb.lc_fit import CONFIG_COLS, FAMILY_OF, family_winners  # noqa: E402

FROZEN = "@frozen"
CARRIED = ["linear", "neural", "rawseries"]
LABEL_CAL = ["paperA_cal", "paperA_corr_cal", "slope_base", "slope_only", "calibrated_delta"]
PHYS_SHOW = ["slope_base", "paperA_corr", "paperA_corr_own", "paperA_cal", "paperA_sh_mh"]
BINS_GT15 = ["pbin15-35", "pbin35-65", "pbin>65"]
WIN_SHARE, WIN_PP, DROP_PP = 0.8, -1.0, 1.0
K = ["split_seed"]


def crit(d, median_rule=True):
    d = pd.Series(d, dtype=float).dropna()
    ok = bool(len(d) and (d < 0).mean() >= WIN_SHARE and (not median_rule or d.median() <= WIN_PP))
    return {"n": len(d), "wins": int((d < 0).sum()), "median_d": float(d.median()) if len(d) else np.nan, "meets": ok}


def fam_rows(A, frozen=False):
    """Family rows of a frozen arm: the `@frozen` rows (frozen=True) or the refit rows; column `family` added."""
    base = A["method"].str.replace(FROZEN, "", regex=False)
    keep = A["method"].str.endswith(FROZEN) if frozen else A["method"].isin(FAMILY_OF)
    return A[keep].assign(family=base[keep].map(FAMILY_OF))


def arm2_rows(A2, carry):
    """Arm 2 rows of each seed's carried spec (the family's inner-CV winner, A10)."""
    key = A2["split_seed"].astype(str) + "#" + A2[CONFIG_COLS].astype(str).agg("|".join, axis=1)
    want = dict(zip(carry["split_seed"].astype(str) + "#" + carry["spec"], carry["family"]))
    return A2[key.isin(want)].assign(family=key[key.isin(want)].map(want))


def best_phys(A, cands):
    out = {}
    for s in SCOPES:
        med = A[A["method"].isin(cands)].groupby("method")[f"wape_{s}"].median().dropna() if f"wape_{s}" in A else pd.Series(dtype=float)
        if len(med):
            out[s] = med.idxmin()
    return out


def paired(F, A, cands, keys=K):
    """Long rows (keys, family, scope): WAPE of the family row, of the best physics row of the scope, and their difference."""
    bp = best_phys(A, cands)
    P = A[A["method"].isin(cands)].set_index(keys + ["method"])
    rows = []
    for r in F.to_dict("records"):
        for s, b in bp.items():
            w, ph = r.get(f"wape_{s}", np.nan), P[f"wape_{s}"].get(tuple(r[k] for k in keys) + (b,), np.nan)
            rows.append({**{k: r[k] for k in keys}, "family": r["family"], "scope": s, "wape": w, "phys": b, "wape_phys": ph, "d": w - ph})
    return pd.DataFrame(rows)


def crit_table(D, median_rule=True):
    rows = []
    for (fam, s), g in D.groupby(["family", "scope"], sort=False):
        c = crit(g["d"], median_rule)
        rows.append({"family": fam, "scope": s, "best physics": g["phys"].iloc[0], "WAPE": band(g["wape"]), "physics WAPE": band(g["wape_phys"]),
                     "seeds ML < physics": f"{c['wins']}/{c['n']}", "median dWAPE pp": fmt(c["median_d"], 2), "meets": c["meets"]})
    return pd.DataFrame(rows)


def head_table(A, F, extra=()):
    rows = [{"row": m, **{scope_name(s): band(A.loc[A["method"] == m, f"wape_{s}"]) for s in SCOPES if f"wape_{s}" in A}}
            for m in [*PHYS_SHOW, *extra] if (A["method"] == m).any()]
    for fam, g in F.groupby("family", sort=False):
        rows.append({"row": f"{fam} ({', '.join(sorted(g['method'].unique()))})", **{scope_name(s): band(g[f"wape_{s}"]) for s in SCOPES if f"wape_{s}" in g}})
    return pd.DataFrame(rows)


def delta(a, b, label):
    """Paired a - b per seed and scope -> one row of medians (a, b: frames indexed by split_seed with wape_<scope> columns)."""
    j = a.join(b, how="inner", lsuffix="_a", rsuffix="_b")
    return {"row": label, "seeds": len(j), **{scope_name(s): fmt((j[f"wape_{s}_a"] - j[f"wape_{s}_b"]).median(), 2) for s in SCOPES if f"wape_{s}_a" in j}}


def used_households(m):
    r = m[(m["method"] == "slope_base") & m["metric"].isin(["at_bound_share_train", "at_bound_share_test"])]
    g = r.groupby("metric")["n_hp_households"].agg(["median", "min", "max"])
    return {k.replace("at_bound_share_", ""): f"{int(v['median'])} [{int(v['min'])}-{int(v['max'])}]" for k, v in g.iterrows()}


def decomposition(A):
    """Per seed and scope: fill contamination, scale dispersion, fit noise of paperA_sh_mh (see module doc) -> long frame."""
    W = {m: A[A["method"] == m].set_index("split_seed") for m in ("paperA_sh_mh", "oracle_O1", "oracle_O2")}
    rows = []
    for s in SCOPES:
        c = f"wape_{s}"
        if all(c in w for w in W.values()):
            d = pd.DataFrame({"net": W["paperA_sh_mh"][c], "o1": W["oracle_O1"][c], "o2": W["oracle_O2"][c]}).dropna()
            rows += [{"split_seed": i, "scope": s, "wape_net": r.net, "fill_contamination": r.net - r.o1, "scale_dispersion": r.o1 - r.o2,
                      "fit_noise": r.o2} for i, r in d.iterrows()]
    return pd.DataFrame(rows)


def decomp_table(D):
    g = D.groupby("scope", sort=False)[["wape_net", "fill_contamination", "scale_dispersion", "fit_noise"]].median().reindex([s for s in SCOPES if s in set(D["scope"])])
    return g.round(1).reset_index().assign(scope=lambda d: d["scope"].map(scope_name))


def figure(dec, marks, out):
    """Stacked bars (fit noise / scale dispersion / fill contamination, medians over seeds) per Paper A bin, one panel per dataset;
    markers: the best physics row and the carried families' rows (median WAPE)."""
    fig, axes = plt.subplots(1, len(dec), figsize=(5.2 * len(dec), 4.2), sharey=True, squeeze=False)
    cols = {"fit_noise": "#adb5bd", "scale_dispersion": "#2a78d6", "fill_contamination": "#eb6834"}
    mk = {"best physics": ("s", "#212529"), "linear": ("o", "#2f9e44"), "neural": ("^", "#9c36b5"), "rawseries": ("D", "#c92a2a")}
    for ax, (name, D) in zip(axes[0], dec.items()):
        g = D.groupby("scope")[list(cols)].median().reindex([s for s in SCOPES if s in set(D["scope"])])
        x, bottom = np.arange(len(g)), np.zeros(len(g))
        for c, col in cols.items():
            ax.bar(x, g[c].to_numpy(), bottom=bottom, color=col, width=0.6, label=c.replace("_", " "))
            bottom = bottom + g[c].to_numpy()
        for lab, v in marks[name].items():
            ax.plot(x, [v.get(s, np.nan) for s in g.index], mk[lab][0], color=mk[lab][1], ms=6, ls="none", label=lab)
        ax.set_xticks(x, [scope_name(s).replace("pbin", "") for s in g.index])
        ax.set(title=f"{name}: error of s_h / m_h (paperA_sh_mh)", xlabel="Paper A penetration bin")
    axes[0][0].set_ylabel("WAPE [%] (test), median over seeds")
    axes[0][-1].legend(fontsize=7)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig_error_decomposition.{ext}", dpi=150)
    plt.close(fig)


def main(stage1, stage2):
    out = stage2 / "report"
    out.mkdir(parents=True, exist_ok=True)
    raw = {a.name: pd.read_csv(a / "metrics.csv") for a in sorted(stage2.iterdir()) if (a / "metrics.csv").exists()}
    A = {k: wide(v, K) for k, v in raw.items()}
    raw2 = pd.read_csv(stage1 / "arm2" / "metrics.csv")
    A2 = wide(raw2, K)
    carry = pd.read_csv(stage1 / "refit" / "carry_forward_models.csv").query("carried_model")
    F2 = arm2_rows(A2, carry)
    txt = ["# 05b Stage 2 report (generated by scripts/paperb/iter05b_report2.py)", "",
           "† = filler-variability-limited bin (A2). WAPE %, median [5-90 %] over seeds. GB labels are 30-min, B* 15-min: compare gaps to physics, not levels. "
           "Carried families (A10): linear, neural (TabPFN), raw-series (CNN), frozen Arm 2 specs; no inner-CV selection in Stage 2 except Arm 5.", ""]
    used = pd.DataFrame([{"arm": k, **used_households(v)} for k, v in {"arm2 (Stage 1)": raw2, **raw}.items() if (v["method"] == "slope_base").any()])
    txt += ["## Used HP households (median [min-max] over seeds)", "", md(used), ""]

    # ---- Arm 2 reference, Arm 6 (temporal replication), A12 (a)
    D2, D6 = paired(F2, A2, PHYS_CAND), paired(fam_rows(A["arm6"]), A["arm6"], PHYS_CAND)
    cpu = fam_rows(A["arm2_cpu"])
    dev = pd.DataFrame([delta(cpu[cpu["family"] == f].set_index("split_seed"), F2[F2["family"] == f].set_index("split_seed"), f) for f in CARRIED])
    txt += ["## Arm 2 (GB main, 20 seeds): carried families vs the best physics row (result of record)", "", md(head_table(A2, F2)), "",
            md(crit_table(D2)), "", "## arm2_cpu - Arm 2 (CPU refit of the same spec minus the Stage 1 row; median paired dWAPE, pp)", "", md(dev), "",
            "## Arm 6 (GB temporal replication, Oct 2022 - 28 Sep 2023, 10 seeds; frozen specs refit on this pool)", "", md(head_table(A["arm6"], fam_rows(A["arm6"]))), "",
            md(crit_table(D6)), ""]

    # ---- Arm 7 (filler uncertainty), A12 (b)
    a12b, d7 = [], []
    cand7 = PHYS_CAND + ["paperA_corr_s0unscaled"]
    for tag, x in (("x0.5", "arm7_x05"), ("x1.5", "arm7_x15")):
        Ax, ref, froz = A[x], fam_rows(A[x]), fam_rows(A[x], frozen=True)
        txt += [f"## Arm 7, fillers' temperature response {tag} (10 seeds)", "", md(head_table(Ax, pd.concat([ref.assign(family=ref["family"] + " refit"),
                froz.assign(family=froz["family"] + " frozen model")]), extra=["paperA_corr_s0unscaled"])), ""]
        for cands, lab in ((cand7, "rule"), (PHYS_CAND, "without paperA_corr_s0unscaled")):
            Db = paired(froz, Ax, cands)
            for (fam, s), g in Db.groupby(["family", "scope"], sort=False):
                c = crit(g["d"], median_rule=False)
                a12b.append({"candidates": lab, "factor": tag, "family": fam, "scope": s, "best physics": g["phys"].iloc[0], "wins": c["wins"], "n": c["n"],
                             "median_d": c["median_d"], "holds": c["meets"]})
        ix = lambda d, m: d[d["method"] == m].set_index("split_seed")                       # noqa: E731
        d7 += [{"factor": tag, **delta(ix(Ax, m), ix(A2, "paperA_corr" if m.endswith("s0unscaled") else m), m)} for m in [*PHYS_SHOW, "paperA_corr_s0unscaled"] if (Ax["method"] == m).any()]
        d7 += [{"factor": tag, **delta(ref[ref["family"] == f].set_index("split_seed"), cpu[cpu["family"] == f].set_index("split_seed"), f"{f} refit (vs arm2_cpu)")} for f in CARRIED]
        d7 += [{"factor": tag, **delta(froz[froz["family"] == f].set_index("split_seed"), F2[F2["family"] == f].set_index("split_seed"), f"{f} frozen model (vs Arm 2)")} for f in CARRIED]
    B = pd.DataFrame(a12b)
    D7 = pd.DataFrame(d7)
    txt += ["## Arm 7: dWAPE vs x1.0 (median paired over seeds 0-9, pp)", "", md(D7), ""]

    # ---- A12
    rows = []
    for f in CARRIED:
        c2, c6 = crit(D2[(D2["family"] == f) & (D2["scope"] == "all")]["d"]), crit(D6[(D6["family"] == f) & (D6["scope"] == "all")]["d"])
        b = B[(B["candidates"] == "rule") & (B["family"] == f)].set_index(["factor", "scope"])
        hold = lambda s: bool(b["holds"].get(("x0.5", s), False) and b["holds"].get(("x1.5", s), False))    # noqa: E731
        cell = lambda s: " / ".join(f"{b['wins'].get((t, s), '–')}/{b['n'].get((t, s), '–')}" for t in ("x0.5", "x1.5"))   # noqa: E731
        a, b_all, b_bins = c2["meets"] and c6["meets"], hold("all"), all(hold(s) for s in BINS_GT15)
        outcome = ("not eligible (did not meet the criterion in Arm 2)" if not c2["meets"] else "lead stays identifiability-bounded" if not a
                   else "lead: physics-bounded below n*, ML ahead beyond" if b_all else "same lead, restricted to penetrations above 15 %" if b_bins
                   else "other combination: Alex decides")
        rows.append({"family": f, "Arm 2 (20 seeds)": f"{c2['wins']}/{c2['n']}, {fmt(c2['median_d'], 2)} pp", "Arm 6 (10 seeds)": f"{c6['wins']}/{c6['n']}, {fmt(c6['median_d'], 2)} pp",
                     "(a)": a, **{f"(b) {scope_name(s)} x0.5 / x1.5": cell(s) for s in SCOPES}, "(b) overall": b_all, "(b) every bin > 15 %": b_bins, "outcome": outcome})
    A12 = pd.DataFrame(rows)
    agree = A12["outcome"].nunique() == 1
    txt += ["## A12: criterion for the paper-lead change (applied as written; inputs)", "",
            "(a) 03b criterion overall, wins and median dWAPE vs the best physics row; (b) seeds in which the frozen Stage 1 model beats the best physics row "
            "of the same scaled arm (need >= 8/10 at both factors).", "", md(A12), "",
            f"**A12 outcome:** {A12['outcome'].iloc[0] if agree else 'families differ: Alex decides (per-family outcomes above)'}.", "",
            "(b) per family, factor and scope, with and without `paperA_corr_s0unscaled` among the physics candidates:", "",
            md(B.assign(scope=B["scope"].map(scope_name), median_d=B["median_d"].round(2))), ""]

    # ---- Arm 4 (oracles)
    dec = {"GB dataset": decomposition(A["arm4"]), "B*": decomposition(A["arm4_bstar"])}
    O1 = fam_rows(A["arm4_o1"])
    o1 = pd.DataFrame([{"family": f, "anchor": a, "seeds": len(g), **{scope_name(s): band(g[f"wape_{s}"]) for s in SCOPES if f"wape_{s}" in g}}
                       for (f, a), g in O1.groupby(["family", "anchor"])])
    orc = pd.DataFrame([{"row": m, **{scope_name(s): band(A["arm4"].loc[A["arm4"]["method"] == m, f"wape_{s}"]) for s in SCOPES}} for m in ("paperA_sh_mh", "oracle_O1", "oracle_O2")])
    fl = pd.concat([raw[k][raw[k]["method"] == "oracle_floor"].assign(dataset=n) for n, k in (("GB dataset", "arm4"), ("B*", "arm4_bstar"))])
    fl = fl.assign(n_hp=fl["cell"].str.replace("n_hp=", "", regex=False)).groupby(["dataset", "n_hp"])["value"].median().round(3).reset_index()
    fl = fl.assign(_o=pd.to_numeric(fl["n_hp"], errors="coerce").fillna(0)).sort_values(["dataset", "_o"]).drop(columns="_o").rename(columns={"value": "CV of HP_Peak / s_h"})
    Bs, split = A["arm4_bstar"], []
    for m in ("paperA_sh_mh", "paperA_corr", "paperA_corr_own", "slope_base"):
        real = Bs[Bs["method"] == m].set_index("split_seed")
        for lab, k in (("(i) fillers' response (real - O1a)", "arm4_bstar_o1a"), ("(ii) own non-HP response (real - O1b)", "arm4_bstar_o1b")):
            split.append({"estimator": m, "part": lab, **{k2: v for k2, v in delta(real, A[k][A[k]["method"] == m].set_index("split_seed"), "").items() if k2 != "row"}})
    txt += ["## Arm 4: oracles (diagnostics only, never competitors)", "", "GB dataset, 20 seeds:", "", md(orc), "",
            "Error decomposition of `paperA_sh_mh` (median over seeds, pp): fill contamination = net - O1, scale dispersion = O1 - O2, fit noise = O2.", ""]
    for n, D in dec.items():
        txt += [f"{n}:", "", md(decomp_table(D)), ""]
        D.to_csv(out / f"decomposition_{'gb' if n.startswith('GB') else 'bstar'}.csv", index=False)
    txt += ["B* split of the non-HP response (A7), median paired dWAPE in pp (positive = removing that response lowers the error); on the GB dataset (ii) is "
            "structurally absent (each HP dwelling's own load is a random filler):", "", md(pd.DataFrame(split)), "",
            "ML on O1 (GB dataset; frozen Arm 2 spec as is, by anchor: with size_peak the anchor is the HP aggregate's coincident peak):", "", md(o1), "",
            "Dispersion floor (CV of HP_Peak / s_h; `household` = household level, else test substations with that many HP households):", "", md(fl), ""]
    marks = {"GB dataset": {"best physics": {s: A2.loc[A2["method"] == b, f"wape_{s}"].median() for s, b in best_phys(A2, PHYS_CAND).items()},
                            **{f: {s: F2.loc[F2["family"] == f, f"wape_{s}"].median() for s in SCOPES} for f in CARRIED}}}

    # ---- Arm 3 (households vs substations, the S test)
    L = pd.concat([wide(pd.read_csv(stage2 / a / "metrics_lc.csv"), ["split_seed", "n_train_hp", "spc_train"]) for a in ("arm3_spc10", "arm3_spc40")])
    L = L.assign(n=np.where(L["n_train_hp"] == 62, "62", "all"))
    F3, t3, st = fam_rows(L), [], []
    for (n, spc), g in L.groupby(["n", "spc_train"]):
        bp = best_phys(g, PHYS_CAND).get("all")
        t3.append({"n": n, "substations per cell": spc, "best physics": f"{bp} {band(g.loc[g['method'] == bp, 'wape_all'])}",
                   **{f: band(F3[(F3["n"] == n) & (F3["spc_train"] == spc) & (F3["family"] == f)]["wape_all"]) for f in CARRIED}})
    for (f, n), g in F3.groupby(["family", "n"]):
        for s in SCOPES:
            p = g.pivot_table(index="split_seed", columns="spc_train", values=f"wape_{s}") if f"wape_{s}" in g else pd.DataFrame()
            if {10, 40} <= set(p.columns):
                d = (p[10] - p[40]).dropna()
                st.append({"family": f, "n": n, "scope": s, "seeds": len(d), "median drop 10 -> 40 pp": round(float(d.median()), 2), "seeds improving": int((d > 0).sum()),
                           "S": bool(len(d) and d.median() >= DROP_PP and (d > 0).mean() >= WIN_SHARE)})
    S = pd.DataFrame(st)
    S.to_csv(out / "s_test.csv", index=False)
    s_all = S[S["scope"] == "all"]
    txt += ["## Arm 3: households vs substations (10 seeds x 1 draw; frozen specs, tuned at n = all with 10 per cell)", "", md(pd.DataFrame(t3)), "",
            "S test (pre-registered: median drop >= 1 pp and >= 80 % of seeds improving):", "", md(S.assign(scope=S["scope"].map(scope_name))), "",
            f"**S overall:** {'holds for ' + ', '.join(s_all[s_all['S']]['family'] + ' (n = ' + s_all[s_all['S']]['n'] + ')') if s_all['S'].any() else 'does not hold (no family at any n)'}.", ""]

    # ---- Arm 5 (B* under v1.1, tuned)
    A5 = A["arm5"]
    ml = A5[A5["method"].isin(FAMILY_OF)]
    W5 = family_winners(ml, K)
    sub = pd.concat([family_winners(ml[ml["method"] == m], K).assign(family=f"neural: {m} only") for m in ("FFNN", "TabPFN")])
    D5 = paired(pd.concat([W5, sub]), A5, PHYS_CAND)
    bp5 = best_phys(A5, PHYS_CAND)
    ncfg = [{"scope": scope_name(s), "configurations": ml.groupby(CONFIG_COLS).ngroups,
             "meeting the criterion": sum(crit(g.set_index("split_seed")[f"wape_{s}"] - A5[A5["method"] == b].set_index("split_seed")[f"wape_{s}"])["meets"] for _, g in ml.groupby(CONFIG_COLS))}
            for s, b in bp5.items()]
    own = []
    for s in SCOPES:
        if f"wape_{s}" not in A5:
            continue
        ix = lambda m: A5[A5["method"] == m].set_index("split_seed")[f"wape_{s}"]             # noqa: E731
        lc = A5[A5["method"].isin(LABEL_CAL)].groupby("method")[f"wape_{s}"].median().idxmin()
        d1, d2 = (ix("paperA_corr_own") - ix(lc)).dropna(), (ix("paperA_corr_own") - ix("paperA_corr")).dropna()
        own.append({"scope": scope_name(s), "paperA_corr": band(ix("paperA_corr")), "paperA_corr_own": band(ix("paperA_corr_own")), "best label-calibrated": f"{lc} {band(ix(lc))}",
                    "own - label-calibrated (median pp)": fmt(d1.median(), 2), "seeds own <= label-calibrated": f"{int((d1 <= 0).sum())}/{len(d1)}",
                    "own - paperA_corr (median pp)": fmt(d2.median(), 2), "seeds own < corr": f"{int((d2 < 0).sum())}/{len(d2)}"})
    wins5 = W5.assign(config=W5[CONFIG_COLS].astype(str).agg("|".join, axis=1)).groupby(["family", "config"]).size().rename("seeds").reset_index()
    txt += ["## Arm 5: B* under v1.1 (20 seeds, per-arm tuning; family winner by inner-CV WAPE)", "", md(head_table(A5, W5)), "", md(crit_table(D5)), "",
            md(pd.DataFrame(ncfg)), "", "Win frequency:", "", md(wins5), "", "`paperA_corr_own` (A7, label-free) against the label-calibrated rows:", "", md(pd.DataFrame(own)), ""]
    marks["B*"] = {"best physics": {s: A5.loc[A5["method"] == b, f"wape_{s}"].median() for s, b in bp5.items()},
                   **{f: {s: W5.loc[W5["family"] == f, f"wape_{s}"].median() for s in SCOPES if f"wape_{s}" in W5} for f in CARRIED}}
    figure(dec, marks, out)

    # ---- GB headline with the bounds quoted next to it, verdict table
    d5f = ROOT / "results" / "iter05a_pool" / "mapping_d5_family_winners.csv"
    d5 = pd.read_csv(d5f).query("cell == 'all'").groupby("family")["dWAPE"].median() if d5f.exists() else pd.Series(dtype=float)
    g7 = D7.set_index(["factor", "row"])["all"]
    hl = [{"family": f, "Arm 2 WAPE (all)": band(F2.loc[F2["family"] == f, "wape_all"]),
           "dWAPE vs best physics": fmt(D2[(D2["family"] == f) & (D2["scope"] == "all")]["d"].median(), 2),
           "Arm 7 frozen model x0.5 / x1.5 (pp)": f"{g7.get(('x0.5', f'{f} frozen model (vs Arm 2)'), '–')} / {g7.get(('x1.5', f'{f} frozen model (vs Arm 2)'), '–')}",
           "Arm 7 refit x0.5 / x1.5 (pp)": f"{g7.get(('x0.5', f'{f} refit (vs arm2_cpu)'), '–')} / {g7.get(('x1.5', f'{f} refit (vs arm2_cpu)'), '–')}",
           "05a D5 swap dWAPE (pp)": fmt(d5.get(f, np.nan), 2)} for f in CARRIED]
    V1 = pd.read_csv(stage1 / "report" / "verdict.csv")
    v = V1.pivot_table(index="family", columns="scope", values="verdict", aggfunc="first").reindex(columns=SCOPES).rename(columns=scope_name).reset_index()
    txt += ["## GB headline (Arm 2) with its bounds: Arm 7 sensitivity (dWAPE vs x1.0, overall) and the 05a D5 swap test", "", md(pd.DataFrame(hl)), "",
            "## Verdict table", "", "Stage 1 (pre-registered D / I-or-features / inconclusive rule, Arms 1 + 2):", "", md(v), "",
            f"S (Arm 3): {'holds' if s_all['S'].any() else 'does not hold'}; A12: see above.", ""]
    A12.to_csv(out / "a12.csv", index=False)
    B.to_csv(out / "a12_b_inputs.csv", index=False)
    D7.to_csv(out / "arm7_delta.csv", index=False)
    pd.concat([D2.assign(arm="arm2"), D6.assign(arm="arm6"), D5.assign(arm="arm5")]).to_csv(out / "paired_vs_physics.csv", index=False)
    (out / "stage2_report.md").write_text("\n".join(txt), encoding="utf-8")
    print(f"written {out / 'stage2_report.md'} ({len(txt)} lines)")
    return A12, S


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage1", default=str(ROOT / "results" / "iter05b_data_limit" / "stage1"))
    ap.add_argument("--stage2", default=str(ROOT / "results" / "iter05b_data_limit" / "stage2"))
    a = ap.parse_args()
    main(Path(a.stage1), Path(a.stage2))
