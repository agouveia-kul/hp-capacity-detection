"""Iteration 05a reports: LCL audit (Task 1), EoH selection (Task 2), analog-mapping diagnostics D1-D4 and the D5 summary
(Task 3). Writes results/iter05a_pool/{lcl_audit,eoh_selection,mapping}.md (+ csv tables). No result is interpreted here.

D1  train-filler aggregate (seed 0 split): Paper A fit (a) on its own LCL days against HadCET, (b) mapped onto every GB-EoH
    station against the station's T (per station, and pooled over the stations' daily points).
D2  |T_London(d') - T_g(d)| over every (station, day); D3 day-of-year distance, widenings and reuse of source days.
D4  LCL self-test: each LCL winter (Nov-Mar inside the LCL window) is held out and rebuilt from the other LCL days with the
    same rule, matching on its own HadCET; aggregates of 10 / 40 / 120 train fillers, 50 draws each, real vs rebuilt.
D5  (after the overnight queue) swapped - real WAPE per spec and per family winner (inner-CV WAPE), overall and per bin,
    and median P_hat / y per bin for the physics rows.
Flag criteria are those pre-registered in iterations/05a-gb-eoh-pool.md.

    python scripts/paperb/iter05a_report.py --part lcl|eoh|mapping|d5 [--config configs/pool_gb_eoh_2122.yaml]
"""
import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import ks_2samp, wasserstein_distance  # noqa: E402

from paperb import ROOT, load_config  # noqa: E402
from paperb.fill_analog import LCL_DIR, LCL_ZIP, analog_map, build_lcl, hadcet  # noqa: E402
from paperb.physics import fit_daily  # noqa: E402
from paperb.pools import build_pool  # noqa: E402
from paperb.splits import household_splits  # noqa: E402

OUT = ROOT / "results" / "iter05a_pool"
PB = ["all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"]
PHYS = ["slope_base", "paperA_corr", "paperA_cal", "paperA_sh_mh", "slope_only", "calibrated_delta", "hdh", "paperA_corr_cal"]
FAMILY = {"Linear": "linear", "Ridge": "linear", "Lasso": "linear", "ElasticNet": "linear", "PLS": "linear", "SVR": "kernel",
          "XGBoost": "trees", "FFNN": "neural"}


def md(df, nd=3):
    df = df.reset_index() if not isinstance(df.index, pd.RangeIndex) else df
    fmt = lambda v: f"{v:.{nd}g}" if isinstance(v, (float, np.floating)) else str(v)            # noqa: E731
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * df.shape[1]]
                     + ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)])


def fit_s0(T, y, N):
    f = fit_daily(np.asarray(T, float), np.asarray(y, float))
    return {"N": N, "s0 (kW/K)": f["s_h"] / N, "T_h": f["T_h"], "P_base/N (kW)": f["P_base"] / N, "r2": f["r2"]}


# ---------------------------------------------------------------- Task 1
def part_lcl(cfg):
    fc = cfg["pool"]["fill"]
    S, D, meta, audit = build_lcl(fc)
    with zipfile.ZipFile(LCL_ZIP) as Z:
        files = pd.DataFrame([(i.filename.replace("UKDA-7857-csv/", ""), i.file_size) for i in Z.infolist()], columns=["file", "bytes"])
        sv = pd.read_csv(Z.open(LCL_DIR + "survey_answers.csv"), encoding="latin-1", low_memory=False)
        qs = pd.read_csv(Z.open(LCL_DIR + "survey_questions.csv"), encoding="latin-1").set_index("Question_id")["Question"]
    shift = pd.DataFrame([(c, qs[c], qs[f"Q{int(c[1:]) + 1}"], "; ".join(f"{k}: {v}" for k, v in sv[c].value_counts().head(4).items()))
                          for c in ("Q246", "Q247", "Q248", "Q303", "Q304", "Q305")],
                         columns=["answer column", "label of that id", "label of id + 1", "top answers"])
    s = sv.drop_duplicates("Household_id").set_index("Household_id").reindex([h[2:] for h in meta.index])
    q248 = s["Q248"].astype(str)
    sub = {"all kept Std": np.ones(len(meta), bool),
           "04 def.: Q248 gas boiler for CH & Q304 = 0 (= 0 TVs)": (q248.str.contains("gas boiler", case=False) & q248.str.contains("central heating", case=False)
                                                                  & s["Q304"].eq(0)).to_numpy(),
           "corrected: CH = Gas (col Q246) & 0 portable heaters (col Q303)": (meta["gas_ch"] & meta["no_heater"]).to_numpy(),
           "CH = Gas (col Q246)": meta["gas_ch"].to_numpy()}
    daily, rows = S.mean(axis=2), []                                     # [hh, day] kW
    for per, (a, b) in {"Jul 2012 - Jun 2013 (as 04)": ("2012-07-01", "2013-07-01"), "LCL window": (fc["lcl_window"][0], fc["lcl_window"][1])}.items():
        dm = ((D["date"] >= a) & (D["date"] < b)).to_numpy()
        for name, m in sub.items():
            if m.sum() >= 5:
                rows.append({"period": per, "subset": name, **fit_s0(D.loc[dm, "T"], daily[m][:, dm].mean(axis=0), 1) | {"N": int(m.sum())}})
    s0 = pd.DataFrame(rows)
    txt = [f"# 05a Task 1 - LCL filler audit\n\nSource: `scripts/paperb/iter05a_report.py --part lcl`, cache `fill_analog.build_lcl` "
           f"(config `{cfg['exp_id']}`).\n",
           "## 1. Release on disk\n", md(files), "",
           f"UKDS SN 7857 edition 2 (DOI 10.5255/UKDA-SN-7857-2, 'Low Carbon London Project: Data from the Dynamic Time-of-Use Electricity "
           f"Pricing Trial, 2013', distributed Aug 2024). Consumption: one column per household (kWh per half hour) and a `GMT` stamp; the "
           f"tariff is given by the file, not a column: `consumption_n.csv` = standard flat rate (**{audit['std_households']}** households, "
           f"ids N....), `consumption_d.csv` = dynamic time-of-use (**{audit['tou_households']}**, ids D....), total "
           f"{audit['std_households'] + audit['tou_households']}. Stamps {audit['file_span'][0]} .. {audit['file_span'][1]}, regular 30-min grid "
           f"{audit['steps_30min']} with no gap or duplicate at the DST changes, i.e. UTC. Extra fields: appliance/attitude survey "
           f"({sv['Household_id'].nunique()} households, {len(sv)} rows, 344 answer columns) and the 2013 ToU price schedule (`tariff_d.csv`). "
           f"Against the public London Datastore release (5,567 households, Nov 2011 - Feb 2014, `Std`/`ToU` column; figure from the iteration "
           f"brief, not re-checked here) this is a **subset in households** ({5567 - audit['std_households'] - audit['tou_households']} fewer) "
           f"and a **superset in fields** (survey, price schedule).\n",
           "## 2. The 'gas-only' subset of iteration 04\n",
           "Traced to `scripts/audit/envelope_v2.py::lcl_scan` (04): `gas` = survey answer column `Q248` contains 'gas boiler' and 'central "
           "heating'; `clean` = gas and answer column `Q304` = 0 ('Paper A: Q304 = portable electric heaters'); s0 = 0.0070 kW/K on 78 households. "
           "It comes from the survey, not from electricity, so it is **not circular**. But the appliance-survey answer columns are shifted by one "
           "against the ids of `survey_questions.csv` (answer column Qk holds question Q(k+1)):\n", md(shift), "",
           "So 04's `Q248` is the hot-water system (whose answers name the central-heating fuel, so the gas part holds), but its `Q304` is the "
           "**number of televisions**; the 04 'clean' subset is 'gas boiler for CH and hot water, and no TV'. Paper A (`hp-sensitivity-paper` "
           "`scripts/outputs.py::_lcl_base`) applies the shift to Q248 but not to Q304, so its 'clean' / 'heater-rich' LCL bases carry the same "
           "mislabel (reported, not changed). Corrected label: central heating = 'Gas' (answer column Q246) and 0 portable electric heaters "
           "(answer column Q303); it is carried as `fill.subset: \"gas_ch & no_heater\"` for a sensitivity arm.\n",
           "## 3-4. Tariff and quality (Std only; ToU households dropped for their whole record)\n",
           f"Window for coverage and analog candidates: local days [{fc['lcl_window'][0]}, {fc['lcl_window'][1]}). Over the full file span only "
           f"**{audit['cov90_full_span']}** Std households reach 90 % (staggered recruitment Nov 2011 - Dec 2012), so the window starts at "
           f"Jul 2012 (every calendar day at least once; Jul-Feb twice).\n",
           md(pd.DataFrame({"rule": list(audit["rules_alone"]), "drops (alone)": list(audit["rules_alone"].values()),
                            "drops (in order)": list(audit["rules_sequential"].values())})),
           f"\nKept: **{audit['kept']}** of {audit['std_households']} Std households. Donor-filled days per kept household (gaps > 2 h): median "
           f"{meta['n_filled_days'].median():.0f}, 90th pct {meta['n_filled_days'].quantile(.9):.0f}. Surveyed: {int(meta['surveyed'].sum())}.\n",
           "## 5. Temperature and s0\n",
           "Temperature: HadCET daily mean (`data/hadcet/meantemp_daily_totals.txt`), the series used in 04. It is the Central England "
           "composite, not a London station. Per-dwelling s0 = Paper A fit of the households' mean daily load against HadCET (B* fill: 0.0055; "
           "04: all LCL 0.0133, 04 'gas-only' 0.0070):\n", md(s0)]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lcl_audit.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    s0.to_csv(OUT / "lcl_s0.csv", index=False)


# ---------------------------------------------------------------- Task 2
def part_eoh(_cfg):
    txt = ["# 05a Task 2 - GB-EoH household selection\n", "Source: `scripts/paperb/pools/gb_eoh.py` (rules in its docstring), report "
           "`scripts/paperb/iter05a_report.py --part eoh`. Iteration 04 counted homes with a complete Nov-Mar season at >= 90 % "
           "(2021/22: 433, 2022/23: 371 / 370); 05a asks for a 12-month window at >= 95 % valid 30-min bins.\n"]
    for tag in ("2122", "2223"):
        pool = build_pool("gb_eoh", load_config(f"configs/pool_gb_eoh_{tag}.yaml"), verbose=False)
        base = ROOT / "data" / "_paperb" / "pools" / f"gb_eoh_{tag}"
        W, St = pd.read_csv(f"{base}_windows.csv"), pd.read_csv(f"{base}_stations.csv")
        m = pool.meta[pool.meta["role"] == "hp"]
        q = lambda c: f"median {m[c].median():.3g}, IQR {m[c].quantile(.25):.3g}-{m[c].quantile(.75):.3g}, max {m[c].max():.3g}"   # noqa: E731
        txt += [f"## GB-EoH {tag}\n", "Candidate windows (12 months from the 1st; `candidate` = the pre-specified Jun-Oct starts; Nov/Dec "
                "reported only):\n", md(W), "",
                f"Eligible homes: **{len(m)}** ({m['type'].value_counts().to_dict()}), {m['station'].nunique()} stations with homes "
                f"({int((m['station'].value_counts() >= 3).sum())} with >= 3). Window {pool.index[0]} .. {pool.index[-1]} UTC.\n",
                f"- donor-filled days (gaps > 2 h): {q('n_filled_days')}",
                f"- HP_Peak per home (30-min 99.9th pct, kW): {q('hp_peak')}; rated `HP_Size_kW` {q('HP_Size_kW')}",
                f"- share of the home's top 0.1 % bins with immersion or back-up > 0.1 kW: {q('peak_share_backup_active')}; "
                f"homes with any: {int((m['peak_share_backup_active'] > 0).sum())}",
                f"- mean share of the peak bins' power drawn by immersion + back-up: {q('peak_backup_kw_share')}",
                f"- heat-meter dropout days (Q_hp = 0 all day while P_ws > 0.1 kW; kept for the simulator, labels unaffected): "
                f"{q('heat_meter_dropout_days')}; homes with any: {int((m['heat_meter_dropout_days'] > 0).sum())}\n",
                "Weather groups (flag: > 5 % missing bins in the window or values outside [-30, 40] degC):\n", md(St), ""]
    b = build_pool("bstar", load_config("configs/protocol_v1.yaml"), verbose=False)
    r = b.hp.resample("30min").mean().quantile(0.999) / b.hp.quantile(0.999)
    txt += [f"## B*: 30-min vs 15-min HP_Peak\n\nPer HP household, 99.9th pct of the 30-min mean / 99.9th pct of the 15-min series "
            f"(gap-filled pool series): median **{r.median():.3f}** (IQR {r.quantile(.25):.3f}-{r.quantile(.75):.3f}, n = {len(r)}); "
            f"substation HP_Peak scales by about this factor.\n"]
    (OUT / "eoh_selection.md").write_text("\n".join(txt) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Task 3, D1-D4
def d4_candidates(D, winter):
    """LCL days that may serve a held-out winter (Nov y - Mar y+1): every non-DST LCL day outside that winter."""
    a, b = pd.Timestamp(f"{winter}-11-01"), pd.Timestamp(f"{winter + 1}-04-01")
    held = (D["date"] >= a) & (D["date"] < b)
    return D[held & ~D["dst"]], D[~held & ~D["dst"]].assign(pos=np.flatnonzero((~held & ~D["dst"]).to_numpy()))


def part_mapping(cfg):
    fc, seed = cfg["pool"]["fill"], 0
    pool = build_pool("gb_eoh", cfg, verbose=False)
    pool.analog.set_seed(seed)
    S, D, _, _ = build_lcl(fc)
    sp = household_splits(pool.meta, [seed], cfg["split"]["test_frac"])[seed]
    fill = sp["train"]["fill"]
    A = pool.analog.day_sum(fill)
    hp_st = pool.meta.loc[pool.meta["role"] == "hp", "station"].value_counts()
    stations = sorted(hp_st.index[hp_st >= cfg["grid"]["min_station_pool"]])
    d1 = [{"fit": "(a) own LCL days vs HadCET", "station": "-", **fit_s0(D["T"], A.mean(axis=1), len(fill))}]
    pts = []
    for st in stations:
        d = pd.DataFrame({"T": pool.temp[st].to_numpy(), "y": pool.analog.aggregate(None, st, A)}, index=pool.index).resample("D").mean()
        pts.append(d)
        d1.append({"fit": "(b) mapped vs station T", "station": st, **fit_s0(d["T"], d["y"], len(fill))})
    P = pd.concat(pts)
    d1.append({"fit": "(b) pooled over stations", "station": f"{len(stations)} stations", **fit_s0(P["T"], P["y"], len(fill))})
    D1 = pd.DataFrame(d1)
    s0a, s0b = D1["s0 (kW/K)"].iloc[0], D1["s0 (kW/K)"].iloc[-1]
    M = pd.concat([pool.analog.maps[st].assign(station=st) for st in stations])
    reuse = M.groupby(["station", "src"]).size()
    d2 = {"median |dT| (K)": M["dT"].abs().median(), "p95 |dT| (K)": M["dT"].abs().quantile(.95), "share |dT| > 1 K": (M["dT"].abs() > 1).mean(),
          "worst station share > 1 K": M.assign(o=M["dT"].abs() > 1).groupby("station")["o"].mean().max()}
    d3 = {"median ddoy": M["ddoy"].median(), "p95 ddoy": M["ddoy"].quantile(.95), "max ddoy": M["ddoy"].max(),
          **{f"days widened to {w}": int((M['widen'] == i).sum()) for i, w in enumerate(fc["doy_windows"]) if i}, "days without a candidate within tol": int((M["widen"] == 3).sum()),
          "source days used per station (median)": reuse.groupby(level=0).size().median(), "max uses of one source day": reuse.max(),
          "mean uses per used source day": reuse.mean()}
    # D4: LCL self-test
    rng, rows = np.random.default_rng([seed, 6]), []
    idx = np.array(sorted(pool.analog.pos[h] for h in fill))
    winters = [y for y in sorted(D["date"].dt.year.unique()) if ((D["date"] >= f"{y}-11-01") & (D["date"] < f"{y + 1}-04-01")).sum() >= 60]
    for w_i, winter in enumerate(winters):
        tgt, cand = d4_candidates(D, winter)
        mp = analog_map(tgt, cand, np.random.default_rng([seed, 7, w_i]), tuple(fc["doy_windows"]), fc["tol_K"], fc["k_nearest"])
        src, real_days = cand["pos"].to_numpy()[mp["src"].to_numpy()], tgt.index.to_numpy()
        for n in (10, 40, 120):
            for draw in range(50):
                X = np.asarray(S[np.sort(rng.choice(idx, n, replace=False))], np.float64).sum(axis=0)
                r_, b_ = X[real_days], X[src]
                fr, fb = fit_daily(tgt["T"].to_numpy(), r_.mean(axis=1)), fit_daily(tgt["T"].to_numpy(), b_.mean(axis=1))
                rows.append({"winter": f"{winter}/{(winter + 1) % 100:02d}", "n": n, "draw": draw, "days": len(tgt),
                             "share_dT_gt1": float((mp["dT"].abs() > 1).mean()), "widened": int((mp["widen"] > 0).sum()),
                             "rel_d_s_h": fb["s_h"] / fr["s_h"] - 1, "d_T_h": fb["T_h"] - fr["T_h"], "rel_d_P_base": fb["P_base"] / fr["P_base"] - 1,
                             "rel_d_p999": np.quantile(b_, .999) / np.quantile(r_, .999) - 1, "rel_d_max": b_.max() / r_.max() - 1,
                             "ks_daily": ks_2samp(r_.mean(axis=1), b_.mean(axis=1)).statistic,
                             "wasserstein_daily_rel": wasserstein_distance(r_.mean(axis=1), b_.mean(axis=1)) / r_.mean()})
    R = pd.DataFrame(rows)
    D4 = R.groupby(["winter", "n"]).agg(days=("days", "first"), share_dT_gt1=("share_dT_gt1", "first"), widened=("widened", "first"), **{f"median |{c}|": (c, lambda x: np.median(np.abs(x))) for c in
                                                                    ("rel_d_s_h", "d_T_h", "rel_d_P_base", "rel_d_p999", "rel_d_max")},
                                         median_ks=("ks_daily", "median"), median_w_rel=("wasserstein_daily_rel", "median"),
                                         median_rel_d_s_h=("rel_d_s_h", "median"), median_rel_d_p999=("rel_d_p999", "median"))
    R.to_csv(OUT / "mapping_d4_draws.csv", index=False)
    D1.to_csv(OUT / "mapping_d1.csv", index=False)
    f1 = abs(s0b / s0a - 1) > 0.15
    f2 = d2["share |dT| > 1 K"] > 0.05
    f4 = bool((D4["median |rel_d_s_h|"] > 0.10).any() or (D4["median |rel_d_p999|"] > 0.10).any())
    txt = ["# 05a Task 3 - analog mapping diagnostics (D1-D4; D5 below once the queue has run)\n",
           f"Source: `scripts/paperb/iter05a_report.py --part mapping`, pool `{cfg['exp_id']}` (GB-EoH {cfg['pool']['year']}), split seed {seed}: "
           f"{len(fill)} train fillers, map seed {seed}; stations with >= {cfg['grid']['min_station_pool']} HP homes: {len(stations)}. Rule: "
           f"`fill_analog.py` docstring (doy windows {fc['doy_windows']}, tol {fc['tol_K']} K, k = {fc['k_nearest']}). "
           "Pre-registered flags: D1 s0 (a) vs (b) differ > 15 %, or > 5 % of days need |dT| > 1 K; D4 median |ds_h| > 10 % or median "
           "|d p99.9| > 10 % at any aggregate size.\n",
           f"## D1 - hockey stick of the train-filler aggregate (per dwelling)\n\n{md(D1)}\n\n(a) vs pooled (b): {100 * (s0b / s0a - 1):+.1f} % "
           f"-> **flag {'RAISED' if f1 else 'not raised'}**; stations beyond 15 %: "
           f"{', '.join(D1.loc[(D1['fit'] == '(b) mapped vs station T') & ((D1['s0 (kW/K)'] / s0a - 1).abs() > .15), 'station']) or 'none'}.\n",
           f"## D2 - temperature mismatch |T_London(d') - T_g(d)|\n\n{md(pd.DataFrame([d2]))}\n\n-> **flag {'RAISED' if f2 else 'not raised'}**.\n",
           f"## D3 - day-of-year distance, widenings, reuse\n\n{md(pd.DataFrame([d3]))}\n",
           f"## D4 - LCL self-test (held-out winter rebuilt from the other LCL days; {R['draw'].nunique()} draws per size)\n\n"
           f"Relative differences are rebuilt / real - 1; T_h difference in K.\n\n{md(D4)}\n\n-> **flag {'RAISED' if f4 else 'not raised'}**.\n"]
    (OUT / "mapping.md").write_text("\n".join(txt) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Task 3, D5
def part_d5(_cfg):
    base = OUT / "overnight"
    M = {a: pd.read_csv(base / a / "metrics.csv") for a in ("d5_real", "d5_swap")}
    Tm = {a: pd.read_csv(base / a / "timing.csv") for a in ("d5_real", "d5_swap")}
    spec = ["method", "anchor", "feature_set", "mode", "target_transform"]
    W = {a: m[(m["metric"] == "wape") & m["cell"].isin(PB)].assign(key=lambda d: d[spec].astype(str).agg("|".join, axis=1))
         for a, m in M.items()}
    wide = {a: w.pivot_table(index=["split_seed", "cell"], columns="key", values="value") for a, w in W.items()}
    dW = (wide["d5_swap"] - wide["d5_real"]).dropna(axis=1, how="all")
    per_spec = dW.groupby(level="cell").median().T.reindex(columns=PB)
    win = {}
    for a, t in Tm.items():                                              # family winner per seed: lowest inner-CV WAPE
        t = t[t["cv_wape"].notna() & t["method"].isin(FAMILY)].assign(key=lambda d: d[spec].astype(str).agg("|".join, axis=1),
                                                                      fam=lambda d: d["method"].map(FAMILY))
        best = t.loc[t.groupby(["split_seed", "fam"])["cv_wape"].idxmin()]
        win[a] = pd.DataFrame([{"split_seed": r.split_seed, "family": r.fam, "cell": c, "winner": r.key,
                                "wape": wide[a].get(r.key, pd.Series(dtype=float)).get((r.split_seed, c), np.nan)} for r in best.itertuples() for c in PB])
    fw = win["d5_real"].merge(win["d5_swap"], on=["split_seed", "family", "cell"], suffixes=("_real", "_swap"))
    fw["dWAPE"] = fw["wape_swap"] - fw["wape_real"]
    fam_tab = fw.pivot_table(index="family", columns="cell", values="dWAPE", aggfunc="median").reindex(columns=PB)
    phys = per_spec[[k.split("|")[0] in PHYS for k in per_spec.index]]
    flag = bool((phys.abs() > 2).any().any() or (fam_tab.abs() > 2).any().any())
    pr = {a: pd.read_csv(base / a / "predictions.csv") for a in M}
    bias = []
    for a, p in pr.items():
        p = p[p["method"].isin(PHYS) & (p["y"] > 0)]
        pen = p["sub_id"].str.split("|").str[4].astype(float)             # grid p (actual p differs by rounding)
        bias.append(p.assign(arm=a, ratio=p["pred"] / p["y"], p_grid=pen).groupby(["arm", "method", "p_grid"])["ratio"].median())
    B = pd.concat(bias).unstack("arm")
    B["change"] = B["d5_swap"] - B["d5_real"]
    fw.to_csv(OUT / "mapping_d5_family_winners.csv", index=False)
    per_spec.to_csv(OUT / "mapping_d5_per_spec.csv")
    txt = [f"## D5 - B* swap test (swapped - real, WAPE pp; median over {dW.index.get_level_values(0).nunique()} seeds)\n",
           "Source: `scripts/paperb/iter05a_report.py --part d5` on `results/iter05a_pool/overnight/d5_{real,swap}/`. Pre-registered flag: "
           "|median dWAPE| > 2 pp for any physics row or family winner, overall or in any bin.\n",
           f"### Physics rows\n\n{md(phys.round(2))}\n", f"### Family winners (inner-CV WAPE per seed and arm)\n\n{md(fam_tab.round(2))}\n",
           f"-> **flag {'RAISED' if flag else 'not raised'}**.\n",
           f"### Median P_hat / y by grid penetration (physics rows)\n\n{md(B.round(3))}\n",
           f"### Every spec\n\n{md(per_spec.round(2))}\n"]
    with open(OUT / "mapping.md", "a", encoding="utf-8") as fh:
        fh.write("\n" + "\n".join(txt) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["lcl", "eoh", "mapping", "d5"])
    ap.add_argument("--config", default="configs/pool_gb_eoh_2122.yaml")
    a = ap.parse_args()
    {"lcl": part_lcl, "eoh": part_eoh, "mapping": part_mapping, "d5": part_d5}[a.part](load_config(a.config))
