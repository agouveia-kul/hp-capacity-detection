"""Harmonised label HL (iteration 07, Task 1; iterations/07-transfer-validation.md, CLAUDE.md s5).

HL = HP_Peak at 30 min, HP unit only (compressor + backup heater + pumps; DHW immersion excluded): per household the 99.9th
percentile (`target_defs.robust_q`) of the 30-min HP series, summed over a substation's HP members. Each household's HL uses the
same valid bins as its native label, which is reproduced first (asserted equal to the pool's `hp_peak`):
- B* (CH): native = the 15-min HP submeter on the samples where every raw channel of the household is present (pools/__init__.py);
  HL = the mean of the two 15-min values of each 30-min bin, on bins whose two samples are both valid. CH electric water heaters
  sit in the own non-HP load, not in the submeter, so nothing is subtracted.
- GB-EoH: native = whole heating-system electricity P_ws on its valid, zero-run-masked bins (pools/gb_eoh.py `_build`, replayed);
  HL = P_ws - P_ih (immersion channel, valid with >= 12 of 15 two-minute diffs, rescaled like P_ws), clipped at 0, on bins where
  both are valid. A home without any valid P_ih bin in the window has no immersion heater (UKDS SN 9050 data dictionary:
  "Where no immersion heater is present then the datapoint is left blank"): immersion 0, HL = native.
Household caps go to data/_paperb/iter07/hl_caps_<pool>.parquet. `substation_labels` sums them over memberships.
"""
import numpy as np
import pandas as pd

from hp_capacity import robust_series_peak
from paperb import ROOT

CACHE = ROOT / "data" / "_paperb" / "iter07"


def _caps_bstar(pool, cfg):
    from paperb.pools import HEAPO, KAISER, _raw, kaiser_meta, kaiser_units, year_index
    index, q = year_index(cfg["pool"]["year"]), cfg["target_defs"]["robust_q"]
    units = {k.split()[0]: v for k, v in kaiser_units(kaiser_meta().reset_index()).items()}
    hp_of_dw = dict(zip(units["K(a)"]["id"].astype(int), units["K(a)"]["hp_meter"].astype(int)))
    kai = lambda mid: _raw(KAISER / "smart_meter_data" / f"{int(mid)}.csv", "timestamp_utc", ["kWh_to_installation"], index)["kWh_to_installation"]  # noqa: E731
    rows = []
    for hh, m in pool.meta[pool.meta["role"] == "hp"].iterrows():
        src, key = m["source"], int(hh.split(":")[1])
        if src == "heapo":
            r = _raw(HEAPO / "smart_meter_data" / "15min" / f"{key}.csv", "Timestamp",
                     ["kWh_received_Total", "kWh_received_HeatPump", "kWh_received_Other"], index)
            h, ok = r["kWh_received_HeatPump"], r.notna().all(axis=1)
        else:                                                           # kaiser_paired: K:<dwelling>; kaiser_sfh: K:<HP meter>
            h = kai(hp_of_dw[key] if src == "kaiser_paired" else key)
            o = kai(int(m["own_meter"].split(":")[1]))
            ok = h.notna() & o.notna()
        both = ok.astype(int).resample("30min").sum() == 2
        h30 = h.resample("30min").mean()[both]
        rows.append({"hh": hh, "station": m["station"], "native": robust_series_peak(h[ok], q), "hl": robust_series_peak(h30, q),
                     "n_bins_hl": int(both.sum()), "immersion_channel": False})
    return pd.DataFrame(rows).set_index("hh")


def _caps_gb_eoh(pool, cfg):
    from paperb.pools import gb_eoh as G
    pc, q = cfg["pool"], cfg["target_defs"]["robust_q"]
    U = pd.read_parquet(G.UNITS)
    U = U[(U["type"] != "hybrid") & (U["n_rows"] > 0)].set_index("property")
    starts = G._starts(pc["windows"], pd.Timestamp(pc["data_end"]))
    W = G._wide(list(U.index), starts[0], starts[-1] + pd.DateOffset(months=12))       # as _build: grouping and zero runs
    grp = G._groups(W["T_ext"])
    Tst = W["T_ext"].T.groupby(grp).median().T.drop(columns="G_none", errors="ignore")
    Tday = Tst.resample("D").mean().reindex(W["P_ws"].index, method="ffill")
    P = (W["P_ws"] * 15.0 / W["n_P_ws"]).where(W["n_P_ws"] >= 12)
    homes = [h[2:] for h in pool.meta.index[pool.meta["role"] == "hp"]]
    P = P[homes]
    P = P.mask(G._zero_runs(P.to_numpy(), W["Q_hp"][homes].to_numpy(), Tday[grp[homes]].to_numpy(), heat_tol=pc["zero_run_heat_tol_kW"]))
    s = pd.Timestamp(pool.index[0])
    idx = pd.date_range(s, G._window_end(s, pc), freq="30min", inclusive="left")
    ih = []
    for f in sorted(G.EOH.glob("eoh_30min_set*.parquet")):
        x = pd.read_parquet(f, columns=["property", "ts", "P_ih", "n_P_ih"], filters=[("ts", ">=", idx[0]), ("ts", "<=", idx[-1])])
        x = x[x["property"].isin(homes)].astype({"property": str})
        ih.append(((x["P_ih"] * 15.0 / x["n_P_ih"]).where(x["n_P_ih"] >= 12)).to_frame("v").assign(p=x["property"], ts=x["ts"])
                  .pivot(index="ts", columns="p", values="v"))
    IH = pd.concat(ih, axis=1).reindex(index=idx, columns=homes)
    rows = []
    for p in homes:
        pw, ip = P[p].reindex(idx), IH[p]
        has = bool(ip.notna().any())
        hl = (pw - (ip if has else 0.0)).clip(lower=0.0)
        rows.append({"hh": f"E:{p}", "station": pool.meta.at[f"E:{p}", "station"], "native": robust_series_peak(pw.dropna(), q),
                     "hl": robust_series_peak(hl.dropna(), q), "n_bins_hl": int(hl.notna().sum()), "immersion_channel": has,
                     "n_bins_ih_missing": int((pw.notna() & ip.isna()).sum()) if has else 0,
                     "n_bins_ih_gt_ws": int(((ip - pw) > 0.05).sum()), "ih_mean_kw": float(ip.mean()) if has else 0.0})
    return pd.DataFrame(rows).set_index("hh")


def household_caps(pool, cfg, rebuild=False):
    """Per HP household: native (reproduced), hl (kW), diagnostics. Raises if the reproduced native differs from pool.meta."""
    f = CACHE / f"hl_caps_{pool.name}.parquet"
    if f.exists() and not rebuild:
        return pd.read_parquet(f)
    caps = (_caps_gb_eoh if pool.name == "gb_eoh" else _caps_bstar)(pool, cfg)
    ref = pool.meta.loc[caps.index, "hp_peak"].astype(float)
    err = float(np.max(np.abs(caps["native"] - ref)))
    if not err <= 1e-6:
        raise ValueError(f"{pool.name}: reproduced native label differs from pool.meta hp_peak by up to {err:.3g} kW")
    CACHE.mkdir(parents=True, exist_ok=True)
    caps.to_parquet(f)
    return caps


def substation_labels(members, caps):
    """Per substation: HP_Peak (native) and HL, summed over the HP members."""
    s = lambda col: members["hp_members"].map(lambda h: float(caps.loc[list(h), col].sum()))  # noqa: E731
    return pd.DataFrame({"native": s("native"), "HL": s("hl")}, index=members.index)
