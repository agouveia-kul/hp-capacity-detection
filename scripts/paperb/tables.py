"""02b tables and figures from the four arms' metrics.csv / predictions.csv -> results/iter02b_benchmark/.

Combines the arms into metrics.csv, writes summary.csv (summarise.py) and four tables (csv + md), each with a
figure (png + pdf). Every figure shows the distribution over split seeds (box = quartiles, whiskers = the
summary band, points = seeds); the legacy column of the protocol-effect table is a single split (seed 42).

    python scripts/paperb/tables.py [--config configs/protocol_v1.yaml]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from hp_capacity import compute_metrics  # noqa: E402
from paperb import ROOT, load_config  # noqa: E402
from paperb.summarise import summarise  # noqa: E402

OUT = ROOT / "results" / "iter02b_benchmark"
ARM = {"main": "iter02b_main", "ffnn": "iter02b_ffnn", "sens_b": "iter02b_sens_b", "legacy_a": "iter02b_legacy_a"}
PHYS = ["slope_only", "slope_base", "calibrated_delta", "hdh"]
ANCHOR_ONLY = [(f"anchor_only_{m}", a) for m in ("Linear", "XGBoost") for a in ("size", "peak", "size+peak")]
COLOR = {"XGBoost": "#2a78d6", "Ridge": "#eb6834", "ElasticNet": "#1baf7a", "SVR": "#eda100", "PLS": "#e87ba4",
         "FFNN": "#4a3aa7", "phys": "#52514e", "anchor": "#9a9993"}
INK = "#0b0b0b"


def label(method, anchor):
    if method in PHYS:
        return {"hdh": "physics: HDH (fixed 12 °C base)"}.get(method, "physics: " + method.replace("_", "-"))
    if method.startswith("anchor_only_"):
        return f"anchor-only {method[12:]} [{anchor}]"
    return f"{method}{' (reduced budget)' if method == 'FFNN' else ''} [{anchor}]"


def color(method):
    return COLOR["phys"] if method in PHYS else COLOR["anchor"] if method.startswith("anchor_only") else COLOR[method]


class Arms:
    def __init__(self, band):
        self.band = band
        self.M = pd.concat([pd.read_csv(OUT / f"arm_{a}" / "metrics.csv") for a in ARM if (OUT / f"arm_{a}" / "metrics.csv").exists()],
                           ignore_index=True)
        self.M.to_csv(OUT / "metrics.csv", index=False)
        summarise(self.M, band).to_csv(OUT / "summary.csv", index=False)
        self.preds = {a: pd.read_csv(OUT / f"arm_{a}" / "predictions.csv") for a in ARM if (OUT / f"arm_{a}" / "predictions.csv").exists()}

    def wide(self, arm, metric, cell="all"):
        m = self.M[(self.M["exp_id"] == ARM[arm]) & (self.M["metric"] == metric) & (self.M["cell"] == cell)]
        return m.pivot_table(index="split_seed", columns=["method", "anchor"], values="value", aggfunc="first")

    def fmt(self, v, nd=3):
        v = pd.Series(v).dropna()
        if v.empty:
            return "n/a"
        lo, hi = v.quantile(self.band[0]), v.quantile(self.band[1])
        return f"{v.median():.{nd}f} [{lo:.{nd}f}–{hi:.{nd}f}]"

    def best(self, arm, cols):
        """Column of `cols` (present in the arm) with the highest median R2 over seeds."""
        r2 = self.wide(arm, "r2")
        cols = [c for c in cols if c in r2.columns]
        return max(cols, key=lambda c: r2[c].median())


def save(name, df, note=""):
    df.to_csv(OUT / f"{name}.csv", index=False)
    md = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    md += "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in df.itertuples(index=False))
    (OUT / f"{name}.md").write_text(f"{note}\n\n{md}\n" if note else md + "\n", encoding="utf-8")


def savefig(fig, name):
    (OUT / "figures").mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"{name}.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)


def boxstrip(ax, items, band, horizontal=True, rng=np.random.default_rng(0)):
    """items: [(label, values, color)]. Box = quartiles, whiskers = band quantiles, points = seeds."""
    for i, (_, v, c) in enumerate(items):
        v = np.asarray(pd.Series(v).dropna(), float)
        if not len(v):
            continue
        bp = ax.boxplot([v], positions=[i], vert=not horizontal, widths=0.6, whis=(100 * band[0], 100 * band[1]),
                        showfliers=False, patch_artist=True, medianprops={"color": INK, "lw": 1.5},
                        boxprops={"facecolor": c, "alpha": 0.35, "edgecolor": c}, whiskerprops={"color": c}, capprops={"color": c})
        j = rng.uniform(-0.18, 0.18, len(v))
        ax.scatter(v, i + j, s=9, color=c, zorder=3) if horizontal else ax.scatter(i + j, v, s=9, color=c, zorder=3)
    ticks = [it[0] for it in items]
    (ax.set_yticks if horizontal else ax.set_xticks)(range(len(items)))
    (ax.set_yticklabels if horizontal else ax.set_xticklabels)(ticks, fontsize=7, **({} if horizontal else {"rotation": 60, "ha": "right"}))
    if horizontal:
        ax.invert_yaxis()
    ax.grid(axis="x" if horizontal else "y", lw=0.4, alpha=0.5)


# ---------------------------------------------------------------- table 1
def table1(A):
    rows, series = [], {"r2": [], "mape": []}
    W = {m: A.wide("main", m) for m in ("r2", "mape", "rmse")}
    Wf = {m: A.wide("ffnn", m) for m in ("r2", "mape", "rmse")} if "ffnn" in A.preds else None
    bound = A.wide("main", "at_bound_share_test")
    ml = [c for c in W["r2"].columns if c[0] not in PHYS and not c[0].startswith("anchor_only")]
    cols = [(b, "none") for b in PHYS] + [c for c in ANCHOR_ONLY if c in W["r2"].columns] + sorted(ml, key=lambda c: (c[1], c[0]))
    entries = [("main", W, c) for c in cols] + ([("ffnn", Wf, c) for c in Wf["r2"].columns if c[0] == "FFNN"] if Wf else [])
    n_hp = A.M[(A.M["exp_id"] == ARM["main"]) & (A.M["cell"] == "all") & (A.M["metric"] == "rmse")].groupby(["method", "anchor"])["n_hp_households"].median()
    for arm, w, c in entries:
        rows.append({"method [anchor]": label(*c), "arm": arm, "n_seeds": int(w["r2"][c].notna().sum()),
                     "R2 median [5%-90%]": A.fmt(w["r2"][c]), "MAPE % median [5%-90%]": A.fmt(w["mape"][c], 2),
                     "RMSE kW median [5%-90%]": A.fmt(w["rmse"][c], 2),
                     "test HP households (median)": n_hp.get(c, np.nan),
                     "T_h at bound, test share": f"{bound[(c[0], 'none')].median():.3f}" if c[0] in PHYS[:3] else ""})
        series["r2"].append((label(*c), w["r2"][c], color(c[0])))
        series["mape"].append((label(*c), w["mape"][c], color(c[0])))
    save("table1_main", pd.DataFrame(rows), "Main table, pool B* (HP_Peak, test). Median [5%-90% band] across split seeds. "
                                            "FFNN: reduced budget (5 seeds, 20 evals, patience 10). MAPE excludes zero targets.")
    fig, axs = plt.subplots(1, 2, figsize=(11, 0.28 * len(entries) + 1.5), sharey=True)
    for ax, k, t in zip(axs, ("r2", "mape"), ("R²", "MAPE (%)")):
        boxstrip(ax, series[k], A.band)
        ax.set_xlabel(t + ", test, per split seed")
    axs[0].set_xlim(left=max(-0.2, axs[0].get_xlim()[0]))
    fig.suptitle("Pool B*, HP_Peak: distribution over split seeds", fontsize=9)
    savefig(fig, "fig_table1_main")


# ---------------------------------------------------------------- table 2
def legacy_column():
    xgb = pd.read_csv(ROOT / "data" / "capacity_model_benchmark.csv").set_index("model").loc["XGBoost"]
    hv = pd.read_csv(ROOT / "data" / "hockey_variants_transfer.csv").query("set == 'Swiss test'")
    ph = hv.loc[hv["r2"].idxmax()]
    audit = (ROOT / "results" / "iter01_pool_audit" / "ml_audit_checks.md").read_text(encoding="utf-8")
    r2_peak = float(re.search(r"R2 = \*\*([0-9.]+)\*\*", audit).group(1))
    return {"xgb": (xgb["test_r2"], xgb["test_mape"], xgb["test_rmse"]),
            "phys": (ph["r2"], ph["mape"], np.nan, f"legacy {ph['reduction']} {ph['map']}"),
            "peak": (r2_peak, np.nan, np.nan)}


def subset_metrics(pr, method, anchor, mask):
    g = pr[(pr["method"] == method) & (pr["anchor"] == anchor) & mask(pr)]
    out = []
    for _, s in g.groupby("split_seed"):
        s = s[np.isfinite(s["pred"])]
        out.append(compute_metrics(s["y"], s["pred"]) if len(s) > 1 else dict(r2=np.nan, mape=np.nan, rmse=np.nan))
    return pd.DataFrame(out)


def table2(A):
    leg = legacy_column()
    pools = [("A under v1 (57 HH, shared fill)", "legacy_a"), ("B* under v1", "main"), ("B under v1", "sens_b")]
    pick = {arm: {"xgb": ("XGBoost", "size_peak"),
                  "phys": (A.best(arm, [(b, "none") for b in PHYS]), "none"),
                  "peak": A.best(arm, [("anchor_only_Linear", "peak"), ("anchor_only_XGBoost", "peak")])}
            for _, arm in pools}
    pick = {a: {k: (v if isinstance(v[0], str) else v) for k, v in d.items()} for a, d in pick.items()}
    rows, series = [], {}
    names = {"xgb": "XGBoost [size_peak]", "phys": "best physics baseline", "peak": "peak-only baseline"}
    for key in ("xgb", "phys", "peak"):
        for mk, mname, nd in (("r2", "R2", 3), ("mape", "MAPE %", 2), ("rmse", "RMSE kW", 2)):
            row = {"method": names[key], "metric": mname}
            l = leg[key]
            row["legacy CSV (legacy protocol, pool A, split seed 42)"] = ("n/a" if np.isnan(l[("r2", "mape", "rmse").index(mk)]) else
                                                                          f"{l[('r2', 'mape', 'rmse').index(mk)]:.{nd}f}") + \
                (f" ({l[3]})" if key == "phys" and mk == "r2" else "")
            for pname, arm in pools:
                c = pick[arm][key]
                w = A.wide(arm, mk)[c]
                row[pname] = A.fmt(w, nd) + (f" ({label(*c)})" if mk == "r2" and key != "xgb" else "")
                series.setdefault((key, pname), w) if mk == "r2" else None
            main_c = pick["main"][key]                                    # B* restricted to A's test cells
            sub = subset_metrics(A.preds["main"], *main_c, lambda d: (d["size"] == 10) & (d["p"] <= 0.3))
            row["B* under v1, A's test cells only (size 10, p <= 0.3)"] = A.fmt(sub[mk], nd)
            rows.append(row)
            if mk == "r2":
                series[(key, "B* on A cells")] = sub["r2"]
    info = {"method": "seeds / test HP households / test substations (median)", "metric": "",
            "legacy CSV (legacy protocol, pool A, split seed 42)": "1 / 28 / 1080"}
    for pname, arm in pools:
        m = A.M[(A.M["exp_id"] == ARM[arm]) & (A.M["cell"] == "all") & (A.M["metric"] == "rmse") & (A.M["method"] == "XGBoost")
                & (A.M["anchor"] == "size_peak")]
        info[pname] = f"{m['split_seed'].nunique()} / {m['n_hp_households'].median():.0f} / {m['n_substations'].median():.0f}"
    m = A.M[(A.M["exp_id"] == ARM["main"]) & (A.M["cell"].isin([f"p{p}|n10" for p in (0.05, 0.1, 0.2, 0.3)])) & (A.M["metric"] == "rmse")
            & (A.M["method"] == "XGBoost") & (A.M["anchor"] == "size_peak")]
    info["B* under v1, A's test cells only (size 10, p <= 0.3)"] = f"{m['split_seed'].nunique()} / – / {m.groupby('split_seed')['n_substations'].sum().median():.0f}"
    rows.append(info)
    save("table2_protocol_effect", pd.DataFrame(rows),
         "Protocol effect: XGBoost (size_peak), best physics baseline and peak-only baseline. v1 columns: median [5%-90%] over split seeds; "
         "the legacy column is ONE split (seed 42, unseeded hyperopt, stacked substations up to 120 dwellings, legacy min/max physics). "
         "Legacy -> A-v1 = stacking/leakage effect (plus the much smaller v1 test grid); A-v1 -> B*-v1 = pool effect. Best baseline = highest median R2.")
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharey=False)
    cats = [p for p, _ in pools] + ["B* on A cells"]
    for ax, key in zip(axs, ("xgb", "phys", "peak")):
        boxstrip(ax, [(("A-v1", "B*-v1", "B-v1", "B*-v1 on A's cells")[i], series[(key, c)], color("XGBoost" if key == "xgb" else "x" if False else
                       ("XGBoost" if key == "xgb" else "ElasticNet" if key == "phys" else "Ridge"))) for i, c in enumerate(cats)],
                 A.band, horizontal=False)
        ax.axhline(leg[key][0], color=INK, ls="--", lw=1)
        ax.text(0.02, 0.02, "dashed: legacy CSV (one split)", transform=ax.transAxes, fontsize=6.5)
        ax.set_title(names[key], fontsize=8)
        ax.set_ylabel("R², test")
    savefig(fig, "fig_table2_protocol_effect")


# ---------------------------------------------------------------- table 3
def table3(A):
    rows, series = [], []
    for arm in ARM:
        if arm not in A.preds:
            continue
        r2, mape = A.wide(arm, "r2"), A.wide(arm, "mape")
        ml = [c for c in r2.columns if c[0] not in PHYS and not c[0].startswith("anchor_only")]
        for c in sorted(ml, key=lambda c: (c[1], c[0])):
            pool = {"size_peak": ["size+peak"], "size": ["size"], "none": ["size", "peak", "size+peak"]}[c[1]]
            base = [b for b in ANCHOR_ONLY if b[1] in pool and b in r2.columns]
            d_r2, d_mape = [], []
            for sd in r2.index:
                bb = max(base, key=lambda b: r2.loc[sd, b] if np.isfinite(r2.loc[sd, b]) else -np.inf)
                d_r2.append(r2.loc[sd, c] - r2.loc[sd, bb])
                d_mape.append(mape.loc[sd, c] - mape.loc[sd, bb])
            d_r2, d_mape = pd.Series(d_r2), pd.Series(d_mape)
            rows.append({"arm": arm, "method [anchor]": label(*c), "vs anchor-only set": "+".join(pool) if c[1] != "none" else "best of all",
                         "n_seeds": int(d_r2.notna().sum()), "dR2 median [5%-90%]": A.fmt(d_r2), "dMAPE pp median [5%-90%]": A.fmt(d_mape, 2),
                         "share of seeds ML R2 > baseline": f"{(d_r2 > 0).mean():.2f}"})
            series.append((f"{arm}: {label(*c)}", d_r2, color(c[0])))
    save("table3_ml_gain", pd.DataFrame(rows),
         "ML gain over the best anchor-only baseline (F1), per seed then summarised. Baseline = the anchor-only model (Linear or XGBoost) with the "
         "highest test R2 on that seed, chosen among those using the same anchor columns (anchor none: among all three), which favours the "
         "baseline. dR2 = R2(ML) - R2(baseline); dMAPE = MAPE(ML) - MAPE(same baseline), in percentage points (negative = ML better).")
    fig, ax = plt.subplots(figsize=(8, 0.26 * len(series) + 1.5))
    boxstrip(ax, series, A.band)
    ax.axvline(0, color=INK, lw=1)
    ax.set_xlabel("ΔR² of ML over best anchor-only baseline, per split seed (right of 0 = ML better)")
    savefig(fig, "fig_table3_ml_gain")


# ---------------------------------------------------------------- table 4
def table4(A):
    pr = A.preds["main"]
    ms = [("XGBoost", "size_peak"), (A.best("main", [("anchor_only_Linear", "peak"), ("anchor_only_XGBoost", "peak")])),
          (A.best("main", [(b, "none") for b in PHYS]))]
    rows, fig_data = [], {}
    for by, col in (("penetration p", "p"), ("size", "size")):
        for m, a in ms:
            g = pr[(pr["method"] == m) & (pr["anchor"] == a) & np.isfinite(pr["pred"])]
            for b, gb in g.groupby(col):
                per = [dict(mape=compute_metrics(s["y"], s["pred"])["mape"], rmse=compute_metrics(s["y"], s["pred"])["rmse"])
                       for _, s in gb.groupby("split_seed") if len(s) > 1]
                per = pd.DataFrame(per)
                rows.append({"by": by, "method [anchor]": label(m, a), "bin": b, "n_seeds": len(per),
                             "MAPE % median [5%-90%]": A.fmt(per["mape"], 2), "RMSE kW median [5%-90%]": A.fmt(per["rmse"], 2)})
                fig_data[(by, m, a, b)] = per
    save("table4_error_vs_penetration_size", pd.DataFrame(rows),
         "Error by penetration bin and by feeder size, pool B*, XGBoost [size_peak] vs the best peak-only baseline vs the best physics baseline. "
         "Per seed, over that seed's test substations in the bin (all sizes for a p bin, all p for a size bin); median [5%-90%] over seeds.")
    fig, axs = plt.subplots(2, 2, figsize=(11, 7))
    for j, (by, col) in enumerate((("penetration p", "p"), ("size", "size"))):
        bins = sorted(pr[col].unique())
        for i, (k, t) in enumerate((("mape", "MAPE (%)"), ("rmse", "RMSE (kW)"))):
            ax = axs[i, j]
            for mi, ((m, a), c) in enumerate(zip(ms, (COLOR["XGBoost"], COLOR["anchor"], COLOR["phys"]))):
                for bi, b in enumerate(bins):
                    v = fig_data.get((by, m, a, b))
                    if v is None or v.empty:
                        continue
                    x = bi + (mi - 1) * 0.27
                    ax.boxplot([v[k].dropna()], positions=[x], widths=0.22, whis=(100 * A.band[0], 100 * A.band[1]), showfliers=False,
                               patch_artist=True, medianprops={"color": INK}, boxprops={"facecolor": c, "alpha": 0.4, "edgecolor": c},
                               whiskerprops={"color": c}, capprops={"color": c})
                ax.plot([], [], color=c, lw=6, alpha=0.5, label=label(m, a))
            ax.set_xticks(range(len(bins)))
            ax.set_xticklabels(bins)
            ax.set_xlabel(by)
            ax.set_ylabel(t)
            ax.grid(axis="y", lw=0.4, alpha=0.5)
            if k == "mape":
                ax.set_yscale("log")
    axs[0, 0].legend(fontsize=7, loc="upper right")
    savefig(fig, "fig_table4_error_vs_penetration_size")
    # per-cell heatmap of the median MAPE (cell rows of metrics.csv)
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.2))
    sizes, ps = sorted(pr["size"].unique()), sorted(pr["p"].unique())
    for ax, (m, a) in zip(axs, ms):
        w = A.M[(A.M["exp_id"] == ARM["main"]) & (A.M["method"] == m) & (A.M["anchor"] == a) & (A.M["metric"] == "mape") & (A.M["cell"] != "all")]
        grid = np.full((len(ps), len(sizes)), np.nan)
        for cell, g in w.groupby("cell"):
            p_, n_ = cell[1:].split("|n")
            grid[ps.index(float(p_)), sizes.index(int(n_))] = g["value"].median()
        im = ax.imshow(grid, origin="lower", cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(sizes)))
        ax.set_xticklabels(sizes)
        ax.set_yticks(range(len(ps)))
        ax.set_yticklabels(ps)
        ax.set_xlabel("size")
        ax.set_ylabel("penetration p")
        ax.set_title(label(m, a), fontsize=7.5)
        for (r, cc), v in np.ndenumerate(grid):
            if np.isfinite(v):
                ax.text(cc, r, f"{v:.0f}", ha="center", va="center", fontsize=7, color=INK if v < np.nanmax(grid) * 0.6 else "white")
        fig.colorbar(im, ax=ax, label="median MAPE (%)")
    savefig(fig, "fig_table4b_cell_heatmap_mape")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/protocol_v1.yaml")
    A = Arms(load_config(ap.parse_args().config)["uncertainty"]["summary_band"])
    for f in (table1, table2, table3, table4):
        f(A)
