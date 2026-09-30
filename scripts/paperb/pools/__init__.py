"""Protocol v1 household pools at 15 min, calendar year (UTC): B* (main arm), B (sensitivity arm) and A (02b).

B  = HEAPO households at KLO (8jB aliased) with HP submeter + Other + Total, and Kaiser dwellings with a
     paired HP meter.
B* = B + HEAPO households at the other stations + Kaiser HP meters in single-family objects without a
     dwelling meter. Each of those is given ONE clean Kaiser dwelling (drawn once, with `pool.seed`, from the
     clean dwellings of type `sfh_own_load_type`) as its own non-HP load; that dwelling leaves the fill pool.
Fill = Kaiser Apartment / SFH dwellings with no TCL flag and not paired (any station).
A  = the 57-household HEAPO 2023 legacy pool (iter-00 `legacy_prep_datarange.parquet`, legacy 80 % coverage rule,
     no coverage re-check). Fill is SHARED: the fill pool of a split is its HP households' non-HP (Other) channel,
     and a household is never both an HP member and a fill member of one substation (`pool.shared_fill`).

Every meter needs >= `coverage_min` valid raw samples in the year, checked BEFORE gaps are interpolated
(F11 lesson). Gaps are then filled as in the legacy readers (time interpolation, then 0). Series are kW.
Candidates come from the iteration-01 coverage scans; the coverage is re-checked here on the raw series.

    pool = build_pool_bstar(cfg)   # cached to data/_paperb/pools/bstar_2023{,_meta}.parquet
"""
import sys

import numpy as np
import pandas as pd

from paperb import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "audit"))
from hp_capacity import robust_series_peak  # noqa: E402
from pool_inventory import HEAPO, KAISER, _utc, covered, kaiser_meta, kaiser_units, load_scans  # noqa: E402

SCAN_CACHE = ROOT / "data" / "_paperb" / "iter01"


class Pool:
    """Series (DataFrames, index = 15-min UTC stamps) plus a household table.

    hp / own: one column per HP household (HP submeter, own non-HP load); fill: one column per fill
    household; temp: one column per station; meta: index `hh` with role, source, station, has_hp_add,
    has_ewh_in_own_load, has_protocol, n_valid_days, coverage, hp_peak (robust, kW), own_meter.
    """

    def __init__(self, name, hp, own, fill, temp, meta):
        self.name, self.hp, self.own, self.fill, self.temp, self.meta = name, hp, own, fill, temp, meta
        self.index, self.shared_fill = hp.index, name == "a"
        self.analog, self.fill_per_dwelling = None, False           # 05a: analog-day fillers, one per dwelling


def year_index(year):
    return pd.date_range(f"{year}-01-01", f"{year}-12-31 23:45", freq="15min")


def _raw(path, ts_col, cols, index):
    d = pd.read_csv(path, sep=";", usecols=[ts_col, *cols])
    d.index = _utc(d.pop(ts_col))
    return d[~d.index.duplicated()].reindex(index) * 4.0            # kWh per 15 min -> kW


def _coverage(raw):
    """(share of valid samples, days with >= 90 % valid samples); valid = every channel present."""
    ok = raw.notna().all(axis=1)
    return float(ok.mean()), int((ok.groupby(ok.index.date).mean() >= 0.9).sum())


def _fill_gaps(s):
    return s.interpolate(method="time").fillna(0.0).astype(np.float32)


def _temperature(station, index):
    if station == "KLO":
        w = pd.read_csv(KAISER / "weather_2020-2029.csv", sep=";", low_memory=False)
        s = pd.Series(pd.to_numeric(w["tre200h0"], errors="coerce").to_numpy(),
                      index=pd.to_datetime(w["reference_timestamp"], format="%d.%m.%Y %H:%M"))
    else:
        w = pd.read_csv(HEAPO / "weather_data" / "hourly" / f"{station}.csv", sep=";",
                        usecols=["Timestamp", "Temperature_avg_hourly"])
        s = pd.Series(w["Temperature_avg_hourly"].to_numpy(), index=_utc(w["Timestamp"]))
    s = s[~s.index.duplicated()].sort_index().dropna()                # hourly -> 15 min as the legacy readers (F6)
    return s.reindex(s.index.union(index)).interpolate(method="time").reindex(index).ffill().bfill().astype(np.float32)


def _heapo_flags():
    meta = pd.read_csv(HEAPO / "meta_data" / "meta_data.csv", sep=";").set_index("Household_ID")
    prot = pd.read_csv(HEAPO / "reports" / "protocols.csv", sep=";", low_memory=False)
    survey = meta["Survey_DHW_Production_ByElectricWaterHeater"].astype(str)
    p_ewh = prot.groupby("Household_ID")["DHW_Production_ByElectricWaterHeater"].agg(lambda x: x.astype(str).eq("True").any())
    ewh = pd.Series(pd.NA, index=meta.index.union(p_ewh.index), dtype="boolean")
    ewh[p_ewh.index] = p_ewh.astype(bool)                            # protocol states True / False
    ewh[survey.index[survey.eq("True")]] = True                      # survey states only True (else unknown)
    return ewh, set(prot["Household_ID"].dropna().astype(int))


def build_pool(option, cfg, verbose=True):
    """Read (or build and cache) pool `option` in {'bstar', 'b', 'a', 'gb_eoh'}. 05a: `pool.analog_swap` (D5) replaces
    every non-HP load of the pool by analog days of its fill households (fill_analog.analog_swap)."""
    pc = cfg["pool"]
    if option == "gb_eoh":
        from paperb.pools.gb_eoh import build_pool_gb_eoh
        return build_pool_gb_eoh(cfg, verbose)
    if pc.get("analog_swap"):
        from paperb.fill_analog import analog_swap
        return analog_swap(build_pool(option, {**cfg, "pool": {k: v for k, v in pc.items() if k != "analog_swap"}}, verbose), cfg)
    year, cov_min = pc["year"], pc["coverage_min"]
    out = ROOT / cfg["cache_dir"] / "pools"
    f_ser, f_meta = out / f"{option}_{year}.parquet", out / f"{option}_{year}_meta.parquet"
    if f_ser.exists() and f_meta.exists():
        ser, meta = pd.read_parquet(f_ser), pd.read_parquet(f_meta)
        part = {k: ser[[c for c in ser.columns if c.startswith(k + "|")]].rename(columns=lambda c: c.split("|", 1)[1])
                for k in ("hp", "own", "fill", "T")}
        return Pool(option, part["hp"], part["own"], part["fill"], part["T"], meta)

    if option == "a":
        return _build_pool_a(cfg, f_ser, f_meta, verbose)
    index, win = year_index(year), f"cal{year}"
    alias = pc["station_alias"]
    scans = load_scans(SCAN_CACHE)
    km = kaiser_meta().set_index("0_meter_id")
    units = {k.split()[0]: v for k, v in kaiser_units(km.reset_index()).items()}
    ok_k = set(covered(scans["kaiser"], "total").query("window == @win")["id"])
    station_of = pd.read_csv(HEAPO / "meta_data" / "households.csv", sep=";").set_index("Household_ID")["Weather_ID"].replace(alias)
    ewh_h, prot_h = _heapo_flags()
    rows, hp, own, fill, dropped = [], {}, {}, {}, []

    def add(hh, role, source, station, raw_cols, hp_s=None, own_s=None, **flags):
        cov, days = _coverage(raw_cols)
        if cov < cov_min:
            dropped.append(f"{hh}: coverage {cov:.3f} < {cov_min}")
            return False
        if role == "hp":
            hp[hh], own[hh] = _fill_gaps(hp_s), _fill_gaps(own_s)
            flags["hp_peak"] = robust_series_peak(hp_s[raw_cols.notna().all(axis=1)], cfg["target_defs"]["robust_q"])
        else:
            fill[hh] = _fill_gaps(own_s)
        rows.append(dict(hh=hh, role=role, source=source, station=station, coverage=cov, n_valid_days=days, **flags))
        return True

    # HEAPO HP households (B: KLO only)
    h15 = covered(scans["heapo15"], "hp_other").query("window == @win")["id"]
    for hid in sorted(h15):
        st = station_of.get(hid)
        if option == "b" and st != "KLO":
            continue
        r = _raw(HEAPO / "smart_meter_data" / "15min" / f"{hid}.csv", "Timestamp",
                 ["kWh_received_Total", "kWh_received_HeatPump", "kWh_received_Other"], index)
        add(f"H:{hid}", "hp", "heapo", st, r, r["kWh_received_HeatPump"], r["kWh_received_Other"],
            has_hp_add=pd.NA, has_ewh_in_own_load=ewh_h.get(hid, pd.NA), has_protocol=hid in prot_h, own_meter=f"H:{hid}")

    def kaiser(mid):
        return _raw(KAISER / "smart_meter_data" / f"{int(mid)}.csv", "timestamp_utc", ["kWh_to_installation"], index)["kWh_to_installation"]

    def kflag(f, *mids):
        return bool(any(km.at[int(m), f] for m in mids))

    # Kaiser dwellings with a paired HP meter
    for dw, hm in units["K(a)"][["id", "hp_meter"]].itertuples(index=False):
        if dw in ok_k and hm in ok_k:
            h, o = kaiser(hm), kaiser(dw)
            add(f"K:{int(dw)}", "hp", "kaiser_paired", "KLO", pd.concat([h, o], axis=1), h, o,
                has_hp_add=kflag("1_hp-add", dw, hm), has_ewh_in_own_load=kflag("1_ewh", dw), has_protocol=False,
                own_meter=f"K:{int(dw)}")

    clean = sorted(int(i) for i in units["K(b)"]["id"] if i in ok_k)
    if option == "bstar":                                            # SFH HP meters + one clean own-load dwelling each
        sfh = units["K(a')"]["id"][units["K(a')"]["id"].map(km["0_object_type"]).eq("Single-family house")]
        cand = [d for d in clean if km.at[d, "0_installation_type"] == pc["sfh_own_load_type"]]
        rng = np.random.default_rng(pc["seed"])
        for hm in sorted(int(i) for i in sfh if i in ok_k):
            while True:                                              # redraw if the dwelling fails coverage
                dw = int(cand.pop(rng.integers(len(cand))))
                h, o = kaiser(hm), kaiser(dw)
                if _coverage(o.to_frame())[0] >= cov_min:
                    break
            clean.remove(dw)
            add(f"K:{hm}", "hp", "kaiser_sfh", "KLO", pd.concat([h, o], axis=1), h, o,
                has_hp_add=kflag("1_hp-add", hm), has_ewh_in_own_load=False, has_protocol=False, own_meter=f"K:{dw}")

    for k, dw in enumerate(clean):
        o = kaiser(dw)
        add(f"K:{dw}", "fill", "kaiser_fill", "any", o.to_frame(), own_s=o,
            has_hp_add=False, has_ewh_in_own_load=False, has_protocol=False, own_meter=f"K:{dw}", hp_peak=np.nan)
        if verbose and (k + 1) % 300 == 0:
            print(f"  fill {k + 1}/{len(clean)}", flush=True)

    meta = pd.DataFrame(rows).set_index("hh")
    meta["has_hp_add"] = meta["has_hp_add"].astype("boolean")
    meta["has_ewh_in_own_load"] = meta["has_ewh_in_own_load"].astype("boolean")
    stations = sorted(meta.loc[meta["role"] == "hp", "station"].unique())
    temp = pd.DataFrame({st: _temperature(st, index) for st in stations}, index=index)
    frames = {"hp": pd.DataFrame(hp, index=index), "own": pd.DataFrame(own, index=index),
              "fill": pd.DataFrame(fill, index=index), "T": temp}
    out.mkdir(parents=True, exist_ok=True)
    pd.concat([v.add_prefix(k + "|") for k, v in frames.items()], axis=1).rename_axis("ts").to_parquet(f_ser)
    meta.attrs = {}
    meta.to_parquet(f_meta)
    (out / f"{option}_{year}_dropped.txt").write_text("\n".join(dropped) + "\n", encoding="utf-8")
    if verbose:
        n = meta["role"].value_counts().to_dict()
        print(f"pool {option} {year}: {n}; dropped {len(dropped)} meters (coverage); stations {stations}")
    return Pool(option, frames["hp"], frames["own"], frames["fill"], temp, meta)


def _build_pool_a(cfg, f_ser, f_meta, verbose):
    year, index = cfg["pool"]["year"], year_index(cfg["pool"]["year"])
    legacy = pd.read_parquet(ROOT / "data" / "_paperb" / "iter00" / "legacy_prep_datarange.parquet")
    ewh_h, prot_h = _heapo_flags()
    hp, own, rows = {}, {}, []
    for hid, st in legacy["Weather_ID"].items():
        r = _raw(HEAPO / "smart_meter_data" / "15min" / f"{hid}.csv", "Timestamp",
                 ["kWh_received_Total", "kWh_received_HeatPump", "kWh_received_Other"], index)
        cov, days = _coverage(r)
        hp[f"H:{hid}"], own[f"H:{hid}"] = _fill_gaps(r["kWh_received_HeatPump"]), _fill_gaps(r["kWh_received_Other"])
        rows.append(dict(hh=f"H:{hid}", role="hp", source="heapo_legacy", station=st, coverage=cov, n_valid_days=days,
                         has_hp_add=pd.NA, has_ewh_in_own_load=ewh_h.get(hid, pd.NA), has_protocol=hid in prot_h,
                         own_meter=f"H:{hid}", hp_peak=robust_series_peak(r["kWh_received_HeatPump"][r.notna().all(axis=1)],
                                                                          cfg["target_defs"]["robust_q"])))
    meta = pd.DataFrame(rows).set_index("hh")
    meta["has_hp_add"], meta["has_ewh_in_own_load"] = (meta[c].astype("boolean") for c in ("has_hp_add", "has_ewh_in_own_load"))
    stations = sorted(meta["station"].unique())
    frames = {"hp": pd.DataFrame(hp, index=index), "own": pd.DataFrame(own, index=index),
              "fill": pd.DataFrame(own, index=index),                  # shared fill: the same HP households' Other channel
              "T": pd.DataFrame({st: _temperature(st, index) for st in stations}, index=index)}
    f_ser.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([v.add_prefix(k + "|") for k, v in frames.items()], axis=1).rename_axis("ts").to_parquet(f_ser)
    meta.attrs = {}
    meta.to_parquet(f_meta)
    if verbose:
        leg = legacy["HP_robust_kW"].reindex([int(h.split(":")[1]) for h in meta.index]).to_numpy()
        print(f"pool a {year}: {len(meta)} HP households, stations {stations}, min coverage {meta['coverage'].min():.3f}; "
              f"max |hp_peak - legacy HP_robust_kW| = {np.abs(meta['hp_peak'].to_numpy() - leg).max():.3g} kW")
    return Pool("a", frames["hp"], frames["own"], frames["fill"], frames["T"], meta)


def build_pool_bstar(cfg, verbose=True):
    return build_pool("bstar", cfg, verbose)


def build_pool_b(cfg, verbose=True):
    return build_pool("b", cfg, verbose)
