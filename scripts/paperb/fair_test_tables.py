"""03b tables and figures (Task 7) from the arms in results/iter03b_fair_test/arm_{main,lc,sens_b}/.

Writes to results/iter03b_fair_test/: summary.csv (main + B sensitivity; the per-arm metrics.csv stay in arm_*/), summary_lc.csv, and
  table1_headline      physics rows, best anchor-only, best direct ML per feature set, best residual ML (WAPE overall and in
                       Paper A's penetration bins, MAPE, R2; median [5%-90%] over split seeds)
  table2_ablation      anchor x model rows, feature set x {direct, direct-log, residual} columns, WAPE; best cell per row marked *
  table3_comparison    the pre-registered Task 6 criterion for every ML configuration, overall and per bin
  table4_pilot_spread  cross-fitted fold m_h against the full pilot, and s0 (fill only vs fill + own load)
  table5_bias          median P_hat / y by penetration for paperA_sh_mh and paperA_corr
  fig_learning_curve, fig_wape_by_bin, fig_bias
"Best" ML rows are chosen by inner-CV WAPE (timing.csv `cv_wape`), never by test WAPE. The best PHYSICS row (Task 6) is
chosen, as pre-registered, by median test WAPE among the Task 5 physics rows (paperA_*, slope-only, slope + base,
calibrated delta; not HDH, not anchor-only), separately for each scope (overall and each bin).

    python scripts/paperb/fair_test_tables.py [--config configs/protocol_v1.yaml]
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

from paperb import ROOT, load_config  # noqa: E402
from paperb.summarise import summarise  # noqa: E402

OUT = ROOT / "results" / "iter03b_fair_test"
SPEC = ["method", "anchor", "feature_set", "mode", "target_transform"]
BINS = ["all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"]
PHYS_CAND = ["paperA_sh_mh", "paperA_sh_mh_station", "paperA_cal", "paperA_corr", "paperA_corr_all", "paperA_corr_cal",
             "slope_only", "slope_base", "calibrated_delta"]
PHYS_ALL = PHYS_CAND + ["hdh"]
WIN_SEEDS, WIN_PP = 0.8, -1.0          # Task 6: dWAPE < 0 in >= 16 of 20 seeds (80 %), median dWAPE <= -1 pp
INK = "#0b0b0b"


def name(spec):
    m, a, fs, mode, tt = spec
    if m in PHYS_ALL:
        return f"physics: {m}"
    if m.startswith("anchor_only_"):
        return f"anchor-only {m[12:]} [{a}]"
    return f"{m} [{a}] {fs}/{mode}{'-log' if tt == 'log' else ''}"


class Arms:
    def __init__(self, band):
        self.band = band
        self.arm = {a: OUT / f"arm_{a}" for a in ("main", "lc", "sens_b") if (OUT / f"arm_{a}" / "metrics.csv").exists()
                    or (OUT / f"arm_{a}" / "metrics_lc.csv").exists()}
        parts = [pd.read_csv(d / "metrics.csv") for a, d in self.arm.items() if (d / "metrics.csv").exists()]
        self.M = pd.concat(parts, ignore_index=True)
        summarise(self.M, band).to_csv(OUT / "summary.csv", index=False)
        if "lc" in self.arm and (self.arm["lc"] / "metrics_lc.csv").exists():
            self.LC = pd.read_csv(self.arm["lc"] / "metrics_lc.csv")
            summarise(self.LC, band).to_csv(OUT / "summary_lc.csv", index=False)
        self.T = pd.read_csv(self.arm["main"] / "timing.csv")
        self.P = pd.read_csv(self.arm["main"] / "predictions.csv")

    def wide(self, metric, cell="all", exp="iter03b_main", M=None):
        m = (self.M if M is None else M)
        m = m[(m["exp_id"] == exp) & (m["metric"] == metric) & (m["cell"] == cell) & (m["target"] == "HP_Peak")]
        return m.pivot_table(index="split_seed", columns=SPEC, values="value", aggfunc="first")

    def fmt(self, v, nd=1):
        v = pd.Series(v).dropna()
        return "n/a" if v.empty else f"{v.median():.{nd}f} [{v.quantile(self.band[0]):.{nd}f}–{v.quantile(self.band[1]):.{nd}f}]"

    def cv(self):
        """Median inner-CV WAPE of every tuned ML spec (direct and residual)."""
        t = self.T[self.T["cv_wape"].notna() & ~self.T["method"].str.startswith("anchor_only")]
        return t.groupby(SPEC)["cv_wape"].median()


def save(name_, df, note=""):
    df.to_csv(OUT / f"{name_}.csv", index=False)
    md = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    md += "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in df.itertuples(index=False))
    (OUT / f"{name_}.md").write_text((f"{note}\n\n" if note else "") + md + "\n", encoding="utf-8")


def savefig(fig, name_):
    (OUT / "figures").mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"{name_}.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)


def picks(A):
    """Specs shown in the headline table / figures: best anchor-only (median WAPE), best direct ML per feature set and best
    residual ML (both by inner-CV WAPE)."""
    w, cv = A.wide("wape"), A.cv()
    ao = [c for c in w.columns if c[0].startswith("anchor_only_")]
    out = {"anchor_only": min(ao, key=lambda c: w[c].median())}
    for fs in ("whdd", "netfit", "both"):
        d = cv[[c for c in cv.index if c[3] == "direct" and c[2] == fs]]
        out[f"direct_{fs}"] = d.idxmin()
    out["residual"] = cv[[c for c in cv.index if c[3] == "residual"]].idxmin()
    return out


def table1(A):
    sp = picks(A)
    specs = [(m, "none", "-", "-", "-") for m in PHYS_ALL] + list(sp.values())
    W = {(m, c): A.wide(m, c) for m in ("wape", "mape", "r2") for c in BINS}
    nh = A.M[(A.M["exp_id"] == "iter03b_main") & (A.M["cell"] == "all") & (A.M["metric"] == "wape")].groupby(SPEC)["n_hp_households"].median()
    rows = []
    for s in specs:
        if s not in W["wape", "all"].columns:
            continue
        rows.append({"row": name(s), "n_seeds": int(W["wape", "all"][s].notna().sum()), "test HP hh (median)": nh.get(s, np.nan),
                     **{f"WAPE % {c}": A.fmt(W["wape", c].get(s, pd.Series(dtype=float))) for c in BINS},
                     "MAPE %": A.fmt(W["mape", "all"][s]), "R2": A.fmt(W["r2", "all"][s], 3)})
    save("table1_headline", pd.DataFrame(rows), "HP_Peak, pool B*, test; median [5%-90%] over split seeds. Bins: Paper A's penetration bins "
         "(actual p = n_HP / size). ML rows are chosen by inner-CV WAPE (not by test): best direct per feature set, best residual.")
    return sp


def table2(A):
    w = A.wide("wape")
    cols = [(fs, mode, tt) for fs in ("whdd", "netfit", "both") for mode, tt in (("direct", "none"), ("direct", "log"), ("residual", "log"))]
    models = sorted({c[0] for c in w.columns if c[3] in ("direct", "residual") and not c[0].startswith("anchor_only")})
    rows = []
    for anchor in ("none", "size", "size_peak"):
        for m in models:
            cell = {c: w.get((m, anchor, *c), pd.Series(dtype=float)) for c in cols}
            med = {c: v.median() for c, v in cell.items() if v.notna().any()}
            best = min(med, key=med.get) if med else None
            rows.append({"anchor": anchor, "model": m, **{f"{fs} {mode}{'-log' if tt == 'log' and mode == 'direct' else ''}":
                         ("n/a" if c not in med else A.fmt(cell[c]) + (" *" if c == best else "")) for c in cols for fs, mode, tt in [c]}})
    save("table2_ablation", pd.DataFrame(rows), "WAPE % (HP_Peak, B*, test), median [5%-90%] over seeds. * = best cell of the row (by test "
         "median; descriptive only, no model is selected from it). Residual models: Ridge, Lasso, ElasticNet, XGBoost.")


def table3(A, exp="iter03b_main", name_="table3_comparison"):
    """Task 6: ML beats physics iff dWAPE < 0 in >= 80 % of the seeds AND median dWAPE <= -1 pp (per scope, vs that scope's best physics row)."""
    rows, summary = [], []
    for scope in BINS:
        w = A.wide("wape", scope, exp)
        phys = [(m, "none", "-", "-", "-") for m in PHYS_CAND if (m, "none", "-", "-", "-") in w.columns]
        if not phys:                                                    # e.g. pool B has no substation with p > 65 %
            summary.append(f"- {scope}: no test substations")
            continue
        best = min(phys, key=lambda c: w[c].median())
        hdh = (("hdh", "none", "-", "-", "-"))
        for c in w.columns:
            if c in phys or c[0] in PHYS_ALL or c[0].startswith("anchor_only"):
                continue
            d = (w[c] - w[best]).dropna()
            wins, n = int((d < 0).sum()), len(d)
            beats = n > 0 and wins >= WIN_SEEDS * n and d.median() <= WIN_PP
            rows.append({"scope": scope, "ML configuration": name(c), "best physics row": name(best), "n_seeds": n,
                         "seeds ML < physics": f"{wins}/{n}", "median dWAPE pp": f"{d.median():.2f}", "verdict": "BEATS physics" if beats else "no better than physics"})
        summary.append(f"- {scope}: best physics row = {name(best)} (median WAPE {w[best].median():.1f} %); "
                       f"HDH median {w[hdh].median():.1f} %; ML configurations meeting the criterion: "
                       f"{sum(1 for r in rows if r['scope'] == scope and r['verdict'] == 'BEATS physics')} of {sum(1 for r in rows if r['scope'] == scope)}")
    df = pd.DataFrame(rows)
    save(name_, df, f"[{exp}] Task 6 (pre-registered): dWAPE = WAPE(ML) - WAPE(best physics row) per seed; ML beats physics iff dWAPE < 0 in >= 16 of 20 "
         "seeds (>= 80 % of the seeds) and median dWAPE <= -1 pp. Best physics row chosen per scope by median WAPE among the Task 5 physics rows.")
    (OUT / f"{name_}_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    best_rows = df.assign(d=df["median dWAPE pp"].astype(float)).sort_values("d").groupby("scope").head(3)
    print("\n".join(summary), "\n", best_rows.to_string(index=False))


def table4(A):
    p = pd.read_csv(A.arm["main"] / "pilots.csv")
    p = p[(p["n"].astype(str) == "main") & (p["cap_def"] == "hp_peak")]
    full = p[p["pilot"] == "all"].set_index("split_seed")["m"]
    cf = p[p["pilot"].str.startswith("cf:")].groupby("split_seed")["m"].agg(["min", "max", "mean"])
    s0 = p[p["pilot"].str.startswith("s0:")].pivot_table(index="split_seed", columns="pilot", values="s0")
    rows = [{"quantity": "full pilot m_h (1/degC)", "median [5%-90%]": A.fmt(full, 5)},
            {"quantity": "cross-fit fold m_h / full m_h: min over folds", "median [5%-90%]": A.fmt(cf["min"] / full, 3)},
            {"quantity": "cross-fit fold m_h / full m_h: max over folds", "median [5%-90%]": A.fmt(cf["max"] / full, 3)},
            {"quantity": "s0, fill households only (kW/K per dwelling)", "median [5%-90%]": A.fmt(s0["s0:paperA_corr"], 5)},
            {"quantity": "s0, fill + own non-HP load of train HP households", "median [5%-90%]": A.fmt(s0["s0:paperA_corr_all"], 5)},
            {"quantity": "s0(all) / s0(fill) - 1", "median [5%-90%]": A.fmt(s0["s0:paperA_corr_all"] / s0["s0:paperA_corr"] - 1, 3)}]
    save("table4_pilot_spread", pd.DataFrame(rows), "Per split seed (main arm, B*): spread of the cross-fitted pilots and the s0 estimates.")


def table5_and_fig(A):
    pr = A.P[A.P["method"].isin(["paperA_sh_mh", "paperA_corr"]) & (A.P["y"] > 0) & (A.P["pred"] > 0)].copy()
    pr["ratio"] = pr["pred"] / pr["y"]
    per = pr.groupby(["method", "split_seed", "p"])["ratio"].median().reset_index()
    rows = [{"method": m, "penetration p": p, "median P_hat/y over seeds [5%-90%]": A.fmt(g["ratio"], 2)} for (m, p), g in per.groupby(["method", "p"])]
    save("table5_bias", pd.DataFrame(rows), "Median P_hat / y of the test substations (valid estimates only), per seed then summarised over seeds.")
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for m, c in (("paperA_sh_mh", "#52514e"), ("paperA_corr", "#2a78d6")):
        g = per[per["method"] == m].groupby("p")["ratio"]
        x = sorted(per["p"].unique())
        ax.plot(x, g.median().loc[x], "-o", color=c, label=m)
        ax.fill_between(x, g.quantile(A.band[0]).loc[x], g.quantile(A.band[1]).loc[x], color=c, alpha=0.2)
    ax.axhline(1, color=INK, lw=0.8, ls="--")
    ax.set(xlabel="penetration p", ylabel="median P_hat / y", xscale="log")
    ax.legend(fontsize=8)
    savefig(fig, "fig_bias")


def fig_bins(A, sp):
    w = {c: A.wide("wape", c) for c in BINS}
    best_phys = min([(m, "none", "-", "-", "-") for m in PHYS_CAND], key=lambda c: w["all"][c].median())
    items = [(best_phys, "#52514e"), (sp["direct_both"], "#2a78d6"), (sp["residual"], "#eb6834")]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for k, (s, c) in enumerate(items):
        for b, cell in enumerate(BINS):
            v = w[cell][s].dropna()
            x = b + (k - 1) * 0.27
            ax.boxplot([v], positions=[x], widths=0.22, whis=(100 * A.band[0], 100 * A.band[1]), showfliers=False, patch_artist=True,
                       medianprops={"color": INK}, boxprops={"facecolor": c, "alpha": 0.4, "edgecolor": c}, whiskerprops={"color": c}, capprops={"color": c})
        ax.plot([], [], color=c, lw=6, alpha=0.5, label=name(s))
    ax.set_xticks(range(len(BINS)))
    ax.set_xticklabels(["overall", "≤ 15 %", "15–35 %", "35–65 %", "> 65 %"])
    ax.set(xlabel="penetration bin (Paper A)", ylabel="WAPE (%), test, per split seed")
    ax.legend(fontsize=7)
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    savefig(fig, "fig_wape_by_bin")


def fig_lc(A):
    if not hasattr(A, "LC"):
        return
    lc = A.LC[(A.LC["metric"] == "wape") & (A.LC["cell"] == "all") & (A.LC["target"] == "HP_Peak")]
    n_all = lc.groupby("n_train_hp").size().index.tolist()
    fig, ax = plt.subplots(figsize=(10, 4.4))
    cmap = plt.get_cmap("tab20")
    show = [m for m in ("paperA_sh_mh", "paperA_cal", "paperA_corr", "paperA_corr_cal", "slope_only", "slope_base")]
    ml = sorted({tuple(x) for x in lc.loc[lc["mode"].isin(["direct", "residual"]) & ~lc["method"].str.startswith("anchor_only"), SPEC].values})
    lines = [((m, "none", "-", "-", "-"), "--") for m in show] + [(s, "-") for s in ml]
    for i, (s, ls) in enumerate(lines):
        g = lc[(lc[SPEC] == pd.Series(dict(zip(SPEC, s)))).all(axis=1)].groupby("n_train_hp")["value"]
        if g.ngroups == 0:
            continue
        x = sorted(g.groups)
        ax.plot(x, g.median().loc[x], ls, marker="o", ms=3, color=cmap(i), label=name(s))
        if s[0] != "paperA_sh_mh":                                     # its band (up to ~ 95 %) would squash the axis
            ax.fill_between(x, g.quantile(A.band[0]).loc[x], g.quantile(A.band[1]).loc[x], color=cmap(i), alpha=0.06)
    ax.set(xlabel="train HP households (n_train_hp; last point = all)", ylabel="WAPE (%), test", ylim=(10, 55),
           title="Learning curve, B*, HP_Peak: median and 5%-90% band over seeds x draws (no band for paperA_sh_mh)")
    ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.01, 0.5))
    ax.grid(lw=0.4, alpha=0.5)
    savefig(fig, "fig_learning_curve")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/protocol_v1.yaml")
    ap.add_argument("--out", default="results/iter03b_fair_test", help="directory holding arm_main / arm_lc / arm_sens_b")
    a = ap.parse_args()
    OUT = ROOT / a.out
    A = Arms(load_config(a.config)["uncertainty"]["summary_band"])
    sp = table1(A)
    table2(A)
    table3(A)
    if "sens_b" in A.arm:
        table3(A, "iter03b_sens_b", "table3_comparison_sens_b")     # 10 seeds: the criterion is applied as >= 80 % of the seeds (8 of 10)
    table4(A)
    table5_and_fig(A)
    fig_bins(A, sp)
    fig_lc(A)
    print("selected rows:", sp)
