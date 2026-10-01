"""GB-EoH pool (iteration 05a, Task 2): EoH heat-pump homes (UKDS SN 9050) with analog-day LCL fillers (fill_analog.py).

Homes: non-hybrid (ASHP, HT-ASHP, GSHP) by iteration 04's typing (`type` in data/_paperb/iter04/eoh_units.parquet:
`HP_Installed` of the USmart property table, channel-based type where it is missing). Channel: whole heating-system
electricity P_ws (compressor, back-up, immersion, pumps), 30-min UTC bins of the 2-min counters (iteration 04 conversion);
a bin is valid with >= 12 of its 15 two-minute diffs and is rescaled by 15 / n to the bin's mean power.
Cleaning, before the coverage check (R8 of 05a-ii): a run of exact zeros >= 6 h that starts on a day with station daily
mean T < 12 degC is missing (an electricity-meter dropout) when the heat meter reads more than `zero_run_heat_tol_kW` (0.1 kW)
somewhere in the run, or heat (> 1 kW) is delivered with silent electricity (< 0.02 kW) within 12 h of the run. A run with no
heat output in or around it is a real switch-off and stays valid (05a-i also counted a run as missing when only the circulation
pump drew power, which flagged real switch-offs, and missed the gaps between the heat events of a home whose electricity meter
was silent for weeks).
Windows (R2): 12 months from the 1st of each month of `windows` (`first`; `last_start` and / or `last_end`, the latest
admissible end, bound the candidates); the one with the most homes at >= `coverage_min` (0.90, R1) valid bins is taken
(ties: the earliest). Eligible homes meet `coverage_min` before filling; gaps <= 2 h are interpolated, longer ones take the
slots of the home's day of the same day type with the nearest station daily T (`fill_analog.fill_gaps`, UTC days, GB-ENG
calendar); filled days are counted.
Stations: weather groups = homes whose daily outdoor temperature agrees with the group's first home within 0.2 degC
(median |difference|, iteration 04 rule) over the loaded span. Station T = median over the group's homes per bin. R5: a
group with > 5 % missing bins in the window is filled from the unflagged group with the highest daily-T correlation
(>= 0.98) through a linear fit on the overlapping days, or dropped with its homes (`_stationfill.csv` lists every action);
remaining gaps are time-interpolated; groups with values outside [-30, 40] degC are flagged.
Labels (substations.py, unchanged) at 30 min: hp_peak = 99.9th percentile of the valid, uncleaned-by-filling bins.
Homes whose electricity reads < 0.02 kW on more than `silent_elec_max` (5 %) of the bins with heat output > 1 kW are excluded
(`_excluded.csv`; 05a-ii review decision 2). `last_day` clips a window to the last full day of data (replication: Oct 2022 - 28 Sep 2023).
Cached in data/_paperb/pools/gb_eoh_<year>{.parquet,_meta.parquet,_windows.csv,_stations.csv,_stationfill.csv,_excluded.csv}.
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
            parts[c].append(x.pivot(index="ts", columns="property", values=c).astype(np.float32))
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


def _zero_runs(P, Q, Tday, min_slots=12, t_max=12.0, heat_tol=0.1, ctx=24):
    """Mask of bins in runs of exact zeros >= min_slots starting on a day with T < t_max that are electricity dropouts: the heat
    meter exceeds heat_tol in the run, or heat (> 1 kW) is delivered with silent electricity (< 0.02 kW) within `ctx` bins of it."""
    out = np.zeros(P.shape, bool)
    silent = (np.nan_to_num(Q) > 1.0) & (np.nan_to_num(P, nan=1.0) < 0.02)
    for j in range(P.shape[1]):
        d = np.diff(np.r_[0, (P[:, j] == 0).astype(np.int8), 0])
        for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            if b - a >= min_slots and Tday[a, j] < t_max and ((np.nan_to_num(Q[a:b, j]) > heat_tol).any() or silent[max(a - ctx, 0):b + ctx, j].any()):
                out[a:b, j] = True
    return out


def _station_fill(Tw, max_missing=0.05, min_corr=0.98):
    """R5: fill the station series (30-min bins of the window) that miss more than max_missing of their bins from the
    unflagged station with the highest daily-T correlation (>= min_corr, >= 60 overlapping days): T_g = a + b T_h, fitted
    on the overlapping days. Returns (filled frame, log frame, stations to drop)."""
    Td = Tw.resample("D").agg(lambda x: x.mean() if x.notna().sum() >= 36 else np.nan)
    miss = Tw.isna().mean()
    ok, log, drop, Tw = [g for g in Tw.columns if miss[g] <= max_missing], [], [], Tw.copy()
    for g in [g for g in Tw.columns if miss[g] > max_missing]:
        cand = [(np.corrcoef(Td.loc[m, g], Td.loc[m, h])[0, 1], h) for h in ok
                if (m := Td[g].notna() & Td[h].notna()).sum() >= 60]
        r, h = max(cand, default=(np.nan, None))
        row = {"station": g, "missing_share": miss[g], "donor": h, "corr": r}
        if h is None or not r >= min_corr:
            drop.append(g)
            log.append({**row, "action": "dropped"})
            continue
        m = Td[g].notna() & Td[h].notna()
        b, a = np.polyfit(Td.loc[m, h], Td.loc[m, g], 1)
        gap = Tw[g].isna() & Tw[h].notna()
        Tw.loc[gap, g] = a + b * Tw.loc[gap, h]
        log.append({**row, "a": a, "b": b, "n_days_fit": int(m.sum()), "n_bins_filled": int(gap.sum()), "action": "filled"})
    return Tw, pd.DataFrame(log, columns=["station", "missing_share", "donor", "corr", "a", "b", "n_days_fit", "n_bins_filled", "action"]), drop


def _starts(wc, data_end):
    """Candidate window starts (the 1st of each month) of a `windows` config that end on or before `last_end` / the data end."""
    st = pd.date_range(wc["first"], wc.get("last_start", data_end), freq="MS")
    end = pd.Timestamp(wc["last_end"]) if wc.get("last_end") else data_end
    return [s for s in st if "last_start" in wc or s + pd.DateOffset(months=12) - pd.Timedelta("30min") <= end]


def _window_end(s, pc):
    """Exclusive end of the window starting at s: 12 months, clipped to the day after `last_day` (the last full day of data)."""
    e = s + pd.DateOffset(months=12)
    return min(e, pd.Timestamp(pc["last_day"]) + pd.Timedelta("1D")) if pc.get("last_day") else e


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
    starts = _starts(pc["windows"], pd.Timestamp(pc["data_end"]))
    W = _wide(list(U.index), starts[0], starts[-1] + pd.DateOffset(months=12))
    grp = _groups(W["T_ext"])
    Tst = W["T_ext"].T.groupby(grp).median().T.drop(columns="G_none", errors="ignore")
    Tday = Tst.resample("D").mean().reindex(W["P_ws"].index, method="ffill")
    n = W["n_P_ws"]
    P = (W["P_ws"] * 15.0 / n).where(n >= 12)                           # valid bin -> mean power of the bin
    homes = [p for p in P.columns if grp.get(p, "G_none") != "G_none"]
    P = P[homes]
    zr = _zero_runs(P.to_numpy(), W["Q_hp"][homes].to_numpy(), Tday[grp[homes]].to_numpy(), heat_tol=pc["zero_run_heat_tol_kW"])
    P, Z = P.mask(zr), pd.DataFrame(zr, index=P.index)
    win = []
    for s in starts:
        e = _window_end(s, pc) - pd.Timedelta("1ns")
        cov = P.loc[s:e].notna().mean()
        win.append({"start": s.date(), "end": e.date(), "n_homes_cov": int((cov >= pc["coverage_min"]).sum()),
                    "n_homes_cov90": int((cov >= 0.9).sum()), "n_homes_cov95": int((cov >= 0.95).sum()),
                    "zero_run_bins": int(Z.loc[s:e].sum().sum())})
    Wn = pd.DataFrame(win)
    s = pd.Timestamp(Wn["start"].iloc[Wn["n_homes_cov"].argmax()])       # first maximum = the earliest on ties
    Wn["chosen"] = Wn["start"] == s.date()
    idx = pd.date_range(s, _window_end(s, pc), freq="30min", inclusive="left")
    Pw, cov = P.reindex(idx), P.reindex(idx).notna().mean()
    Tw = Tst.reindex(idx)
    flags = pd.DataFrame({"missing_share": Tw.isna().mean(), "implausible_bins": ((Tw < -30) | (Tw > 40)).sum()})
    Tw, sfill, dropped = _station_fill(Tw.mask((Tw < -30) | (Tw > 40)))
    Tw = Tw.interpolate(method="time").ffill().bfill()
    elig = sorted(p for p in cov.index[cov >= pc["coverage_min"]] if grp[p] not in dropped)
    days = idx.normalize().unique()
    we, T = day_type(days, "GB-ENG"), Tw.resample("D").mean()
    hp, rows = {}, []
    for p in elig:
        X, nf = fill_gaps(Pw[p].to_numpy().reshape(len(days), 48), we, T[grp[p]].to_numpy(), pc["max_interp_slots"])
        hp[f"E:{p}"] = X.ravel().astype(np.float32)
        raw = Pw[p].dropna()
        top = raw >= raw.quantile(robust_q)
        bu = (W["P_ih"][p].fillna(0) + W["P_buh"][p].fillna(0)).reindex(raw.index)
        qh = W["Q_hp"][p].reindex(idx)
        qd = qh.resample("D").sum(min_count=1)
        pd_ = Pw[p].resample("D").mean()
        rows.append({"hh": f"E:{p}", "role": "hp", "source": "eoh", "station": grp[p], "coverage": float(cov[p]),
                     "n_filled_days": nf, "hp_peak": robust_series_peak(raw, robust_q), "type": U.at[p, "type"],
                     "HP_Size_kW": U.at[p, "HP_Size_kW"], "area": U.at[p, "area"],
                     "peak_share_backup_active": float((bu[top] > 0.1).mean()),
                     "peak_backup_kw_share": float((bu[top] / raw[top]).clip(0, 1).mean()),
                     "heat_meter_dropout_days": int(((qd == 0) & (pd_ > 0.1)).sum()),
                     "silent_elec_share": float(((Pw[p] < 0.02) & (qh > 1.0)).sum() / max(int((qh > 1.0).sum()), 1))})
    out = [r["hh"] for r in rows if r["silent_elec_share"] > pc["silent_elec_max"]]      # electricity silent while heat is delivered
    pd.DataFrame([{"hh": r["hh"], "silent_elec_share": r["silent_elec_share"], "coverage": r["coverage"]} for r in rows if r["hh"] in out],
                 columns=["hh", "silent_elec_share", "coverage"]).to_csv(f"{base}_excluded.csv", index=False)
    rows, hp = [r for r in rows if r["hh"] not in out], {k: v for k, v in hp.items() if k not in out}
    elig = [p for p in elig if f"E:{p}" not in out]
    st = flags.assign(n_homes_all=grp.value_counts().reindex(Tw.columns),
                      n_homes_eligible=pd.Series([grp[p] for p in elig]).value_counts().reindex(Tw.columns))
    st["flag"] = (st["missing_share"] > 0.05) | (st["implausible_bins"] > 0)
    stations = sorted({grp[p] for p in elig})
    frames = {"hp": pd.DataFrame(hp, index=idx), "T": Tw[stations].astype(np.float32)}
    base.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([v.add_prefix(k + "|") for k, v in frames.items()], axis=1).rename_axis("ts").to_parquet(base.with_suffix(".parquet"))
    pd.DataFrame(rows).set_index("hh").to_parquet(f"{base}_meta.parquet")
    Wn.to_csv(f"{base}_windows.csv", index=False)
    st = st.fillna({"n_homes_eligible": 0}).rename_axis("station")
    st.to_csv(f"{base}_stations.csv")
    sfill.merge(st[["n_homes_all"]], left_on="station", right_index=True, how="left").to_csv(f"{base}_stationfill.csv", index=False)
    if verbose:
        print(f"GB-EoH {pc['year']}: window from {s.date()}, {len(elig)} eligible homes of {len(homes)} non-hybrid with T ({len(out)} excluded: silent electricity), "
              f"{len(stations)} stations, dropped stations {dropped}; windows {Wn[['start', 'n_homes_cov']].values.tolist()}", flush=True)
