"""GB-EoH pool (iteration 05a, Task 2): EoH heat-pump homes (UKDS SN 9050) with analog-day LCL fillers (fill_analog.py).

Homes: non-hybrid (ASHP, HT-ASHP, GSHP) by iteration 04's typing (`type` in data/_paperb/iter04/eoh_units.parquet:
`HP_Installed` of the USmart property table, channel-based type where it is missing). Channel: whole heating-system
electricity P_ws (compressor, back-up, immersion, pumps), 30-min UTC bins of the 2-min counters (iteration 04 conversion);
a bin is valid with >= 12 of its 15 two-minute diffs and is rescaled by 15 / n to the bin's mean power.
Cleaning, before the coverage check: a run of exact zeros >= 6 h that starts on a day with station daily mean T < 12 degC,
while the heat meter or the circulation pump records output during the run, is missing.
Window: 12 months from the 1st of each month in `window_months` of `window_year`; the one with the most homes at
>= `coverage_min` valid bins is taken (ties: the earliest), unless `window_fixed_month` is set (replication: the main
window's month, one year later). Eligible homes meet `coverage_min` before filling; gaps
<= 2 h are interpolated, longer ones take the slots of the home's day of the same day type with the nearest station
daily T (`fill_analog.fill_gaps`, UTC days, GB-ENG calendar); filled days are counted.
Stations: weather groups = homes whose daily outdoor temperature agrees with the group's first home within 0.2 degC
(median |difference|, iteration 04 rule) over the loaded span. Station T = median over the group's homes per bin, then
time-interpolated; groups with > 5 % missing bins in the window or values outside [-30, 40] degC are flagged.
Labels (substations.py, unchanged) at 30 min: hp_peak = 99.9th percentile of the valid, uncleaned-by-filling bins.
Cached in data/_paperb/pools/gb_eoh_<year>{.parquet,_meta.parquet,_windows.csv,_stations.csv}.
"""
import numpy as np
import pandas as pd

from hp_capacity import robust_series_peak
from paperb import ROOT
from paperb.fill_analog import TZ_GB, AnalogFill, build_lcl, day_type, fill_gaps, station_targets

EOH = ROOT / "data" / "_paperb" / "pools_raw" / "eoh"
UNITS = ROOT / "data" / "_paperb" / "iter04" / "eoh_units.parquet"
CH = ["P_ws", "n_P_ws", "Q_hp", "P_cp", "P_ih", "P_buh", "T_ext"]


def _wide(props, a, b):
    """Channels -> DataFrames [30-min UTC stamp x home] over [a, b)."""
    idx = pd.date_range(a, b, freq="30min", inclusive="left")
    parts = {c: [] for c in CH}
    for f in sorted(EOH.glob("eoh_30min_set*.parquet")):
        x = pd.read_parquet(f, columns=["property", "ts", *CH], filters=[("ts", ">=", a), ("ts", "<", b)])
        x = x[x["property"].isin(props)].astype({"property": str})
        for c in CH:
            parts[c].append(x.pivot(index="ts", columns="property", values=c))
    return {c: pd.concat(v, axis=1).reindex(idx) for c, v in parts.items()}


def _groups(T):
    """Weather groups of homes (columns of 30-min T) -> Series home -> 'Gnnn' (no temperature: 'G_none')."""
    Td, reps, lab = T.resample("D").mean(), {}, {}
    for p in sorted(T.columns):
        if Td[p].notna().sum() < 30:
            lab[p] = "G_none"
            continue
        g = next((g for g, r in reps.items() if (Td[p] - Td[r]).abs().median() < 0.2), None)
        if g is None:
            g = f"G{len(reps):03d}"
            reps[g] = p
        lab[p] = g
    return pd.Series(lab)


def _zero_runs(P, Q, CP, Tday, min_slots=12, t_max=12.0):
    """Mask of bins in runs of exact zeros >= min_slots starting on a day with T < t_max while Q or CP is active."""
    out = np.zeros(P.shape, bool)
    for j in range(P.shape[1]):
        d = np.diff(np.r_[0, (P[:, j] == 0).astype(np.int8), 0])
        for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            if b - a >= min_slots and Tday[a, j] < t_max and (np.nan_to_num(Q[a:b, j]) > 0).any() | (np.nan_to_num(CP[a:b, j]) > 0).any():
                out[a:b, j] = True
    return out


def build_pool_gb_eoh(cfg, verbose=True):
    from paperb.pools import Pool
    pc, fc = cfg["pool"], cfg["pool"]["fill"]
    out = ROOT / cfg["cache_dir"] / "pools"
    base = out / f"gb_eoh_{pc['year']}"
    if not base.with_suffix(".parquet").exists():
        _build(pc, cfg["target_defs"]["robust_q"], base, verbose)
    ser, meta = pd.read_parquet(base.with_suffix(".parquet")), pd.read_parquet(f"{base}_meta.parquet")
    hp, temp = (ser[[c for c in ser.columns if c.startswith(k)]].rename(columns=lambda c: c.split("|", 1)[1]) for k in ("hp|", "T|"))
    S, D, lmeta_all, _ = build_lcl(fc, verbose)
    lmeta = lmeta_all[lmeta_all.eval(fc["subset"])] if fc.get("subset") else lmeta_all    # sensitivity arm, e.g. "gas_ch & no_heater"
    fill_meta = pd.DataFrame({"role": "fill", "source": "lcl_std", "station": "any", "coverage": lmeta["coverage"],
                              "n_filled_days": lmeta["n_filled_days"]}, index=lmeta.index)
    meta = pd.concat([meta, fill_meta])
    pool = Pool("gb_eoh", hp, pd.DataFrame(0.0, index=hp.index, columns=hp.columns, dtype=np.float32),
                pd.DataFrame(index=hp.index), temp, meta)
    targets, t_day, t_slot = station_targets(hp.index, temp, TZ_GB, fc["calendar"], 30)
    cand = D[~D["dst"]].assign(pos=np.flatnonzero(~D["dst"].to_numpy()))
    pool.analog, pool.fill_per_dwelling = AnalogFill(S, list(lmeta_all.index), cand, targets, t_day, t_slot, fc), True
    return pool


def _build(pc, robust_q, base, verbose):
    U = pd.read_parquet(UNITS)
    U = U[(U["type"] != "hybrid") & (U["n_rows"] > 0)].set_index("property")
    y = pc["window_year"]
    months = pc["window_months"] + pc.get("info_months", [])          # info_months: reported, never chosen
    a, b = pd.Timestamp(f"{y}-{min(months):02d}-01"), pd.Timestamp(f"{y + 1}-{max(months):02d}-01")
    W = _wide(list(U.index), a, b)
    grp = _groups(W["T_ext"])
    Tst = W["T_ext"].T.groupby(grp).median().T.drop(columns="G_none", errors="ignore")
    Tday = Tst.resample("D").mean().reindex(W["P_ws"].index, method="ffill")
    n = W["n_P_ws"]
    P = (W["P_ws"] * 15.0 / n).where(n >= 12)                           # valid bin -> mean power of the bin
    homes = [p for p in P.columns if grp.get(p, "G_none") != "G_none"]
    P = P[homes]
    zr = _zero_runs(P.to_numpy(), W["Q_hp"][homes].to_numpy(), W["P_cp"][homes].to_numpy(), Tday[grp[homes]].to_numpy())
    P, Z = P.mask(zr), pd.DataFrame(zr, index=P.index)
    win = []
    for m in months:
        s = pd.Timestamp(f"{y}-{m:02d}-01")
        e = s + pd.DateOffset(months=12) - pd.Timedelta("1ns")
        cov = P.loc[s:e].notna().mean()
        win.append({"start": s.date(), "n_homes_cov": int((cov >= pc["coverage_min"]).sum()), "n_homes_cov90": int((cov >= 0.9).sum()),
                    "zero_run_bins": int(Z.loc[s:e].sum().sum()), "candidate": m in pc["window_months"]})
    Wn = pd.DataFrame(win)
    s = pd.Timestamp(f"{y}-{pc['window_fixed_month']:02d}-01") if pc.get("window_fixed_month") else \
        pd.Timestamp(Wn[Wn["candidate"]].sort_values("start").set_index("start")["n_homes_cov"].idxmax())                  # replication: the main window's month
    Wn["chosen"] = Wn["start"] == s.date()
    idx = pd.date_range(s, s + pd.DateOffset(months=12), freq="30min", inclusive="left")
    Pw, cov = P.reindex(idx), P.reindex(idx).notna().mean()
    elig = sorted(cov.index[cov >= pc["coverage_min"]])
    days = idx.normalize().unique()
    Tw = Tst.reindex(idx)
    flags = pd.DataFrame({"missing_share": Tw.isna().mean(), "implausible_bins": ((Tw < -30) | (Tw > 40)).sum()})
    Tw = Tw.mask((Tw < -30) | (Tw > 40)).interpolate(method="time").ffill().bfill()
    we, T = day_type(days, "GB-ENG"), Tw.resample("D").mean()
    hp, rows = {}, []
    for p in elig:
        X, nf = fill_gaps(Pw[p].to_numpy().reshape(len(days), 48), we, T[grp[p]].to_numpy(), pc["max_interp_slots"])
        hp[f"E:{p}"] = X.ravel().astype(np.float32)
        raw = Pw[p].dropna()
        top = raw >= raw.quantile(robust_q)
        bu = (W["P_ih"][p].fillna(0) + W["P_buh"][p].fillna(0)).reindex(raw.index)
        qd = W["Q_hp"][p].reindex(idx).resample("D").sum(min_count=1)
        pd_ = Pw[p].resample("D").mean()
        rows.append({"hh": f"E:{p}", "role": "hp", "source": "eoh", "station": grp[p], "coverage": float(cov[p]),
                     "n_filled_days": nf, "hp_peak": robust_series_peak(raw, robust_q), "type": U.at[p, "type"],
                     "HP_Size_kW": U.at[p, "HP_Size_kW"], "area": U.at[p, "area"],
                     "peak_share_backup_active": float((bu[top] > 0.1).mean()),
                     "peak_backup_kw_share": float((bu[top] / raw[top]).clip(0, 1).mean()),
                     "heat_meter_dropout_days": int(((qd == 0) & (pd_ > 0.1)).sum())})
    st = flags.assign(n_homes_all=grp.value_counts().reindex(Tw.columns),
                      n_homes_eligible=pd.Series([grp[p] for p in elig]).value_counts().reindex(Tw.columns))
    st["flag"] = (st["missing_share"] > 0.05) | (st["implausible_bins"] > 0)
    stations = sorted({grp[p] for p in elig})
    frames = {"hp": pd.DataFrame(hp, index=idx), "T": Tw[stations].astype(np.float32)}
    base.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([v.add_prefix(k + "|") for k, v in frames.items()], axis=1).rename_axis("ts").to_parquet(base.with_suffix(".parquet"))
    pd.DataFrame(rows).set_index("hh").to_parquet(f"{base}_meta.parquet")
    Wn.to_csv(f"{base}_windows.csv", index=False)
    st.fillna({"n_homes_eligible": 0}).rename_axis("station").to_csv(f"{base}_stations.csv")
    if verbose:
        print(f"GB-EoH {pc['year']}: window from {s.date()}, {len(elig)} eligible homes of {len(homes)} non-hybrid with T, "
              f"{len(stations)} stations; windows {Wn[['start', 'n_homes_cov']].values.tolist()}", flush=True)
