"""05a-ii Task A: why did D4 flag? Writes results/iter05a_pool/d4_diagnostics.md (+ csv, figures/d4_capacity_equiv.{png,pdf}).

All with the London (Heathrow) temperature (R4). Winter = 1 Nov - end of Feb of the winters 2012/13 and 2013/14 (the common span:
the LCL window ends on 27 Feb 2014). Households = the seed-0 train fillers of GB-EoH, 10 / 40 / 120 per aggregate, 50 draws.
Slope definitions, all in kW/K on daily means: (a) hockey stick with latent T_h (Paper A); (b) hockey stick with T_h fixed at the
pooled LCL value (the fit on the train-filler mean over every LCL day); (c) minus the OLS slope of the load on T over days with T < 12 degC.
  1. Real year-to-year stability: |s(2013/14) / s(2012/13) - 1| for the same aggregates, both directions.
  2. D4 error E: a winter rebuilt from the LCL days outside that winter (analog_map, rule of fill_analog.py), |rebuilt / real - 1|.
  3. The same with donors from every LCL day outside +-30 days of the target day, both winters included (how the EoH pool is built).
  4. Capacity-equivalent error: dP = |d s_h| (aggregate of N dwellings) / m_h, m_h = the GB-EoH pilot slope (all train HP homes), as a
     share of HP_Peak = p N x the pool's median household HP_Peak.

PRE-REGISTERED RULE (DECISIONS.md, 2026-09-30; fixed before any run). Y = median real year-to-year error (item 1), E = median D4 error
of item 2, per slope definition and aggregate size n; E_b, E_c under (b), (c).
  - intrinsic filler variability: Y_a >= 0.5 E_a at every n -> accept the mapping; 05b adds the filler-uncertainty sensitivity (the fillers'
    temperature response x0.5 and x1.5);
  - mapping defect: Y_a < 0.5 E_a at every n and E_b, E_c > 25 % at every n -> add a 3-day mean-T criterion, rerun D1-D4, then stop;
  - otherwise: inconclusive (reported; 05b runs the sensitivity arm, the mapping is not changed).
  - in every case a capacity-equivalent error > 5 % of HP_Peak marks the penetration bin as fusion-limited in every later table.

    python scripts/paperb/d4_diagnostics.py [--config configs/pool_gb_eoh_2122.yaml]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from paperb import ROOT, load_config  # noqa: E402
from paperb.fill_analog import analog_map, build_lcl  # noqa: E402
from paperb.physics import fit_daily, household_caps, pool_pilot  # noqa: E402
from paperb.pools import build_pool  # noqa: E402
from paperb.splits import household_splits  # noqa: E402

OUT = ROOT / "results" / "iter05a_pool"
SIZES, DRAWS, WINTERS = (10, 40, 120), 50, (2012, 2013)
PENETRATION = (0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0)
RATIO, DEFECT_ERR, FLAG_PCT, T_LOW = 0.5, 0.25, 5.0, 12.0
DEFS = {"a": "hockey stick, latent T_h", "b": "hockey stick, T_h fixed (pooled LCL)", "c": "OLS slope, days below 12 degC"}


def winter_days(D, y):
    return ((D["date"] >= f"{y}-11-01") & (D["date"] < f"{y + 1}-03-01")).to_numpy()


def slopes(T, y, t_h):
    """kW/K under the three definitions (nan where a fit is impossible)."""
    T, y = np.asarray(T, float), np.asarray(y, float)
    out = {}
    try:
        out["a"] = fit_daily(T, y)["s_h"]
    except (RuntimeError, ValueError):
        out["a"] = np.nan
    out["b"] = np.linalg.lstsq(np.c_[np.ones(len(T)), np.maximum(t_h - T, 0)], y, rcond=None)[0][1]
    m = T < T_LOW
    out["c"] = -np.polyfit(T[m], y[m], 1)[0] if m.sum() >= 10 else np.nan
    return out


def rebuild_map(D, y, variant, rng, fc, col="T", k=None):
    """(target days, candidate days, analog map) of winter y. variant 'winter': donors outside the winter; 'band': donors outside +-30 d of
    each target day (both winters)."""
    tm = winter_days(D, y) & ~D["dst"].to_numpy()
    cm = ~winter_days(D, y) & ~D["dst"].to_numpy() if variant == "winter" else ~D["dst"].to_numpy()
    tgt, cand = D[tm].assign(T=D.loc[tm, col]), D[cm].assign(T=D.loc[cm, col], pos=np.flatnonzero(cm))
    return tgt, cand, analog_map(tgt, cand, rng, tuple(fc["doy_windows"]), fc["tol_K"], k or fc["k_nearest"], exclude_days=30 if variant == "band" else 0)


def verdict(Y, E, E_b, E_c):
    """The pre-registered rule; Y, E, E_b, E_c: {n: median relative error} under (a), (a), (b), (c)."""
    if all(Y[n] >= RATIO * E[n] for n in E):
        return "intrinsic filler variability"
    if all(Y[n] < RATIO * E[n] and E_b[n] > DEFECT_ERR and E_c[n] > DEFECT_ERR for n in E):
        return "mapping defect"
    return "inconclusive"


def cap_equiv(err_abs, m_h, hp_med, sizes=SIZES, ps=PENETRATION):
    """% of HP_Peak: |d s_h| of an aggregate of N dwellings / m_h over p N hp_med (rows N, columns p)."""
    return pd.DataFrame({p: {N: 100 * err_abs[N] / (m_h * p * N * hp_med) for N in sizes} for p in ps}).rename_axis("N")


def main(cfg_path):
    from paperb.iter05a_report import md
    cfg = load_config(cfg_path)
    fc, seed = cfg["pool"]["fill"], 0
    pool = build_pool("gb_eoh", cfg, verbose=False)
    S, D, _, _ = build_lcl(fc)
    sp = household_splits(pool.meta, [seed], cfg["split"]["test_frac"])[seed]
    idx = np.array(sorted(pool.analog.pos[h] for h in sp["train"]["fill"]))
    Sd = np.asarray(S[idx], np.float64).mean(axis=2)                      # [train filler, day] kW
    th_pool = fit_daily(D["T"].to_numpy(), Sd.mean(axis=0))["T_h"]
    rng = np.random.default_rng([seed, 11])
    draws = {n: [rng.choice(len(idx), n, replace=False) for _ in range(DRAWS)] for n in SIZES}
    rows, changes = [], []
    for w_i, y in enumerate(WINTERS):
        maps = {v: rebuild_map(D, y, v, np.random.default_rng([seed, 12, w_i]), fc) for v in ("winter", "band")}
        ch = [rebuild_map(D, y, "winter", np.random.default_rng([seed, 12, w_i]), fc, col=c, k=kk)[2]["src"].to_numpy() for kk in (None, 1) for c in ("T", "T_hadcet")]
        changes.append({"winter": f"{y}/{(y + 1) % 100:02d}", "days": len(maps["winter"][0]),
                        "share of matches that change with HadCET (rule, random among 3)": float((ch[0] != ch[1]).mean()),
                        "share whose nearest-T day changes (k = 1)": float((ch[2] != ch[3]).mean()),
                        "share |dT| > 1 K (Heathrow)": float((maps["winter"][2]["dT"].abs() > 1).mean())})
        for n in SIZES:
            for d, h in enumerate(draws[n]):
                X = Sd[h].sum(axis=0)
                o = WINTERS[1 - w_i]
                s_y, s_o = (slopes(D.loc[winter_days(D, yy), "T"], X[winter_days(D, yy)], th_pool) for yy in (y, o))
                for v, (tgt, cand, mp) in maps.items():
                    real = slopes(tgt["T"], X[tgt.index], th_pool)
                    reb = slopes(tgt["T"], X[cand["pos"].to_numpy()[mp["src"].to_numpy()]], th_pool)
                    for k in DEFS:
                        rows.append({"winter": y, "n": n, "draw": d, "variant": v, "def": k, "rel_err": reb[k] / real[k] - 1, "abs_err": abs(reb[k] - real[k]),
                                     "yoy": s_o[k] / s_y[k] - 1 if v == "winter" else np.nan})
    R = pd.DataFrame(rows)
    E = R.assign(a=R["rel_err"].abs()).groupby(["variant", "def", "n"])["a"].median().unstack("n")
    Yy = R[R["variant"] == "winter"].assign(a=lambda d: d["yoy"].abs()).groupby(["def", "n"])["a"].median().unstack("n")
    cmp = pd.DataFrame({f"{k}, n={n}": {"Y (real year-to-year)": Yy.loc[k, n], "E (D4, winter donors)": E.loc["winter", k][n],
                                        "Y / E": Yy.loc[k, n] / E.loc["winter", k][n], "E (D4, +-30 d band)": E.loc["band", k][n]}
                        for k in DEFS for n in SIZES}).T
    ver = verdict(Yy.loc["a"].to_dict(), E.loc["winter", "a"].to_dict(), E.loc["winter", "b"].to_dict(), E.loc["winter", "c"].to_dict())
    caps = household_caps(pool)
    sp_all = household_splits(pool.meta, list(range(10)), cfg["split"]["test_frac"])
    m_h = pd.Series({s: pool_pilot(pool, sp_all[s]["train"]["hp"], caps)["m"] for s in sp_all})
    hp_med = float(caps.median())
    tabs = {v: cap_equiv(R[(R["variant"] == v) & (R["def"] == "a")].groupby("n")["abs_err"].median().to_dict(), float(m_h.median()), hp_med) for v in ("winter", "band")}
    R.to_csv(OUT / "d4_diagnostics_draws.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 3))
    for a_, (v, t) in zip(ax, tabs.items()):
        im = a_.imshow(t.to_numpy(), aspect="auto", cmap="viridis_r", norm=matplotlib.colors.LogNorm(vmin=1, vmax=max(100, t.to_numpy().max())))
        a_.set_xticks(range(len(t.columns)), [f"{p:g}" for p in t.columns])
        a_.set_yticks(range(len(t.index)), [str(i) for i in t.index])
        a_.set_xlabel("penetration p")
        a_.set_ylabel("feeder size N")
        a_.set_title(f"capacity-equivalent error, % of HP_Peak ({'winter donors' if v == 'winter' else '+-30 d band'})", fontsize=8)
        for i in range(t.shape[0]):
            for j in range(t.shape[1]):
                a_.text(j, i, f"{t.iat[i, j]:.0f}" + ("*" if t.iat[i, j] > FLAG_PCT else ""), ha="center", va="center", fontsize=7, color="w" if t.iat[i, j] < 30 else "k")
    fig.colorbar(im, ax=ax, label="%")
    (OUT / "figures").mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"d4_capacity_equiv.{ext}", dpi=90, bbox_inches="tight")
    lim = {v: sorted(t.columns[(t > FLAG_PCT).any()].tolist()) for v, t in tabs.items()}
    txt = ["# 05a-ii Task A - D4 diagnostics\n", f"Source: `scripts/paperb/d4_diagnostics.py` (definitions and the pre-registered rule are in its docstring), pool GB-EoH `{cfg['pool']['year']}`, "
           f"{len(idx)} train fillers (seed 0), {DRAWS} draws per size, London Heathrow temperature. Pooled LCL T_h (definition b) = {th_pool:.2f} degC.\n",
           "## Item 1-3: real year-to-year variation Y against the D4 error E (median |relative error| of s)\n", md(cmp.reset_index().rename(columns={"index": "def, n"}), 3), "",
           "Definitions: " + "; ".join(f"({k}) {v}" for k, v in DEFS.items()) + ".\n",
           f"**Verdict by the pre-registered rule: {ver}.** (a): Y >= 0.5 E at n = {[n for n in SIZES if Yy.loc['a', n] >= 0.5 * E.loc['winter', 'a'][n]]}; "
           f"E under (b) = {E.loc['winter', 'b'].round(3).to_dict()}, under (c) = {E.loc['winter', 'c'].round(3).to_dict()}.\n",
           "## Day matches that change with the temperature source\n", md(pd.DataFrame(changes), 3), "",
           "(HadCET in place of Heathrow, same seed and candidate set; the share includes the random choice among the 3 closest.)\n",
           f"## Item 4: capacity-equivalent error, % of HP_Peak (* = above {FLAG_PCT:g} %, fusion-limited)\n",
           f"m_h = {m_h.median():.4f} (median over 10 split seeds, range {m_h.min():.4f}-{m_h.max():.4f}); median household HP_Peak = {hp_med:.2f} kW; "
           "|d s_h| = median absolute error of definition (a) at that aggregate size.\n", "Winter donors (D4 as defined):\n", md(tabs["winter"].reset_index().round(1)), "",
           "Donors from outside +-30 d of the target day:\n", md(tabs["band"].reset_index().round(1)), "",
           f"Fusion-limited penetrations (any N above {FLAG_PCT:g} %): winter donors {lim['winter']}, band donors {lim['band']}. Figure: `figures/d4_capacity_equiv.png`.\n"]
    (OUT / "d4_diagnostics.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/pool_gb_eoh_2122.yaml")
    main(ap.parse_args().config)
