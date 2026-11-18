"""Iteration 07b-i -- read-only audit of unseen targets for a label-free local-s0 estimator.

Blindness rule (brief, DECISIONS 2026-11-18 Decision 2): no estimator, prediction or error metric is computed on any
candidate. Computed here: counts, coverage and label descriptives; the per-dwelling temperature slope s0 of non-HP
samples (FeederBW feeders with no registered HP or electric heating, NEEA homes without electric heating); and the
own non-HP load slope of HP homes where whole-house and HP meters coexist (NEEA from the 04 cache, WPuQ). Every file
opened is recorded and written to log.txt.

Candidates scanned from raw files (new since 04): the Belgian home-monitoring sets (two parquet sets with HP, P1, PV
submeters and `DER_capacity_by_installation.csv`), the Fluvius 2024 sample (P6269, 8 categories of 15-min meters),
FeederBW (registry + feeders), UKPN (LV feeders + LCT register), HEAPO beyond B* (iter01 coverage scans). The others
are taken from the 04 inventory (results/iter04_inventory) and cited there.

    python scripts/audit/target_audit_07bi.py --config configs/iter07b_i_quick.yaml   # smoke (~2 min)
    python scripts/audit/target_audit_07bi.py --config configs/iter07b_i_audit.yaml
"""
import argparse
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "audit"))
from envelope_v2 import envelope  # noqa: E402
from paperb.physics import fit_daily  # noqa: E402
from pool_inventory import md_table  # noqa: E402

D = ROOT / "data"
OPENED = []
BE_SETS = {"BE-2024": "95951bd3-6123-4264-bf38-c7c220761a9b", "BE-2025": "26b72e88-1805-4aeb-adae-b82ee8cfe9b8"}
FLU24 = ["P6269_1_50_DMK_Sample_Elek_2024_Deel_1.zip", "P6269_1_50_DMK_Sample_Elek_2024_Deel_2.zip"]
OUTDOOR = r"outdoor|outside|ambient|weather|exterior|buiten"
# the HP and PV meters are renamed between the 2024 and 2025 sets (mid-e/hp -> mid-e/hp1, mid-e/pv -> mid-e/inverter1-pv)
BE_ALIAS = {"HP": ["mid-e/hp/P", "mid-e/hp1/P", "mid-e/hp2/P"], "P1": ["fluvius/p1/P"],
            "PV": ["mid-e/pv/P", "mid-e/inverter1-pv/P", "mid-e/inverter2-pv/P"], "BUF": ["mid-e/buffer-tank-resistance/P"],
            "T": ["hp/hp1-outside-air/T", "hp/outside-air/T", "sensor/outside-air/T", "sensor/outside/T"]}


def op(path, why):
    """Record a file the audit opens (acceptance: log.txt lists every file opened)."""
    p = Path(path)
    OPENED.append((str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), why))
    return p


def cached(cache, name, fn):
    p = cache / f"{name}.parquet"
    if not p.exists():
        print(f"building {p.name} ...", flush=True)
        fn().to_parquet(p)
    return pd.read_parquet(op(p, "audit cache (written by this script)"))


def s0_fit(T, y, n, tmax=None):
    """Per-dwelling non-HP slope: Paper A daily-mean hockey stick (T_h in 8-20 C) of a non-HP aggregate / n dwellings.
    `tmax` keeps days with T <= tmax only (a descriptive variant for sites with summer cooling)."""
    d = pd.DataFrame({"T": T, "y": y}).dropna()
    d = d[d["T"] <= tmax] if tmax is not None else d
    try:
        f = fit_daily(d["T"].to_numpy(), d["y"].to_numpy())
    except (ValueError, RuntimeError) as e:                                # e.g. negative daily load (PV export): listed, not dropped
        return {"n": n, "days": len(d), "s0": np.nan, "T_h": np.nan, "P_base_per_dw": np.nan, "r2": np.nan,
                "hinge_inside": False, "at_bound": False, "fit_error": type(e).__name__}
    return {"n": n, "days": len(d), "s0": f["s_h"] / n, "T_h": f["T_h"], "P_base_per_dw": f["P_base"] / n, "r2": f["r2"],
            "hinge_inside": f["hinge_inside"], "at_bound": f["at_bound"]}


def q(s, k=3):
    s = pd.Series(s, dtype=float).dropna()
    return f"{s.median():.{k}f} [{s.quantile(.25):.{k}f}-{s.quantile(.75):.{k}f}] (n={len(s)})" if len(s) else "n=0"


# ------------------------------------------------------------------ BE home monitoring (new) --
def be_scan(lim):
    parts = []
    for tag, pre in BE_SETS.items():
        for f in sorted(D.glob(f"{pre}_*.gz.parquet"))[:lim]:
            pf = pq.ParquetFile(op(f, f"{tag}: series inventory (keys, rows per day); values not read"))
            for b in pf.iter_batches(batch_size=5_000_000, columns=["Timestamp", "Installation", "System", "Subsystem", "Key"]):
                t = pa.Table.from_batches([b])
                day = pc.divide(pc.cast(t["Timestamp"], pa.int64()), 86_400_000)
                t = t.drop_columns(["Timestamp"]).append_column("day", day)
                parts.append(t.group_by(["Installation", "System", "Subsystem", "Key", "day"]).aggregate([("day", "count")])
                             .to_pandas().assign(set=tag))
    x = pd.concat(parts).groupby(["set", "Installation", "System", "Subsystem", "Key", "day"], as_index=False)["day_count"].sum()
    return x.astype({"Installation": str})


def be_monitoring(cfg, cache):
    x = cached(cache, "be_series_days", lambda: be_scan(cfg["limit_files"]))
    x["date"] = pd.to_datetime(x["day"], unit="D")
    key = x["System"] + "/" + x["Subsystem"] + "/" + x["Key"]
    per = x.assign(key=key).groupby(["Installation", "key"]).agg(t0=("date", "min"), t1=("date", "max"), days=("date", "nunique"),
                                                                 rows_per_day=("day_count", "median")).reset_index()
    role = {k: r for r, ks in BE_ALIAS.items() for k in ks}
    xr = x.assign(role=key.map(role)).dropna(subset=["role"])
    cov = {}
    for w, (a, b) in cfg["windows"].items():                                   # share of days with any sample, per role (aliases merged)
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        cov[w] = xr[(xr["date"] >= a) & (xr["date"] < b)].groupby(["Installation", "role"])["date"].nunique().unstack() / (b - a).days
    ok = lambda w, r: set(cov[w].index[cov[w].get(r, pd.Series(0, index=cov[w].index)).fillna(0) >= cfg["coverage"]])  # noqa: E731
    has = lambda r: set(xr.loc[xr["role"] == r, "Installation"])               # noqa: E731
    der = pd.read_csv(op(D / "DER_capacity_by_installation.csv", "BE monitoring: DER table (HP electrical peak = label)"),
                      encoding="utf-8-sig").astype({"Installation": str})
    hp_der = der[der["Heat pump"].astype(str).str.lower().eq("yes")]
    both = {w: sorted(ok(w, "HP") & ok(w, "P1")) for w in cov}
    f = {"installations": int(x["Installation"].nunique()),
         "installations per set": x.groupby("set")["Installation"].nunique().to_dict(),
         "period per set": {s: f"{g['date'].min():%Y-%m-%d} .. {g['date'].max():%Y-%m-%d}" for s, g in x.groupby("set")},
         **{f"with {r} series ({', '.join(ks)})": len(has(r)) for r, ks in BE_ALIAS.items()},
         "with heat meter (mid-c/space-heating/P)": len(set(per.loc[per["key"] == "mid-c/space-heating/P", "Installation"])),
         **{f"HP and P1 both >= {cfg['coverage']:.0%} of days, {w}": len(v) for w, v in both.items()},
         **{f"HP, P1 and outdoor T >= {cfg['coverage']:.0%}, {w}": len(set(v) & ok(w, "T")) for w, v in both.items()},
         "outdoor-temperature series": sorted(set(key[key.str.contains(OUTDOOR, case=False)])),
         "DER table rows": len(der), "DER heat pump = yes": len(hp_der),
         "DER HP electrical peak kW (median [IQR])": q(hp_der["Heat pump electrical peak (kW)"], 2),
         "DER buffer-tank resistor peak > 0": int((hp_der["Buffer-tank resistor peak (kW)"].fillna(0) > 0).sum()),
         "DER with PV": int(der["PV"].astype(str).str.lower().eq("yes").sum()),
         "DER with battery": int(der["Battery"].astype(str).str.lower().eq("yes").sum()),
         "DER EV charger found": int((~der["EV charger"].astype(str).str.lower().isin(["none found", "nan", "no"])).sum()),
         "DER installations in series": len(set(der["Installation"]) & set(x["Installation"]))}
    keys = per.groupby("key").agg(installations=("Installation", "nunique"), median_days=("days", "median"),
                                  median_rows_per_day=("rows_per_day", "median")).reset_index()
    w_env = "cal2025" if "cal2025" in both else next(iter(both))
    f["DER HP homes with a battery (excluded from the own-load slope)"] = int(hp_der["Battery"].astype(str).str.lower().eq("yes").sum())
    f |= be_own_load(cfg, hp_der)
    return f, per, keys, both[w_env]


def be_own_load(cfg, hp_der):
    """Own non-HP load of BE HP homes without a battery: P1 (signed net, export < 0) + |PV| - HP - buffer resistor, daily
    means of 15-min bins (>= 80 per day), against the home's outdoor-air sensor (site median if it has none). PV is taken
    as |PV| because its sign differs between homes and within a year. Input statistic only (brief: own-load slope)."""
    homes = sorted(hp_der.loc[~hp_der["Battery"].astype(str).str.lower().eq("yes"), "Installation"])
    role = {k: r for r, ks in BE_ALIAS.items() for k in ks}
    files = [op(p, "BE monitoring: P1, HP, PV, buffer and outdoor-T values of HP homes without battery (own-load slope)")
             for pre in BE_SETS.values() for p in sorted(D.glob(f"{pre}_*.gz.parquet"))[:cfg["limit_files"]]]
    import pyarrow.dataset as pads
    flt = pc.field("Installation").isin(homes) & pc.field("Subsystem").isin(sorted({k.split("/")[1] for k in role}))
    t = pads.dataset([str(p) for p in files], format="parquet").to_table(
        columns=["Timestamp", "Installation", "System", "Subsystem", "Key", "Unit", "Value"], filter=flt).to_pandas()
    t["k"] = t["System"] + "/" + t["Subsystem"] + "/" + t["Key"]
    t = t[t["k"].isin(role)].assign(role=lambda d: d["k"].map(role))
    t["Value"] = np.where(t["Unit"].eq("W"), t["Value"] / 1000, t["Value"])
    t["bin"] = t["Timestamp"].dt.tz_convert(None).dt.floor("15min")
    b = t.groupby(["Installation", "role", "k", "bin"])["Value"].mean().groupby(level=[0, 1, 3]).sum().reset_index()
    b.loc[b["role"] == "PV", "Value"] = b.loc[b["role"] == "PV", "Value"].abs()
    b["day"] = b["bin"].dt.floor("D")
    d = b.groupby(["Installation", "role", "day"])["Value"].agg(["mean", "count"])
    d = d.loc[(d["count"] >= 80) | (d.index.get_level_values("role") == "T"), "mean"].unstack("role")
    site_T = d["T"].groupby(level="day").median()
    pv_homes = set(hp_der.loc[hp_der["PV"].astype(str).str.lower().eq("yes"), "Installation"])
    rows, own_all = [], []
    for h, g in d.groupby(level="Installation"):
        g = g.droplevel(0)
        if not {"P1", "HP"} <= set(g.columns):
            continue
        pv = g["PV"] if "PV" in g else (pd.Series(np.nan if h in pv_homes else 0.0, index=g.index))
        own = g["P1"] + pv - g["HP"] - g.get("BUF", pd.Series(0.0, index=g.index)).fillna(0)
        T = g["T"].fillna(site_T) if "T" in g else site_T.reindex(g.index)
        own_all.append(own.rename(h))
        rows.append(s0_fit(T, own, 1) | {"home": h, "own_T": "T" in g})
    r = pd.DataFrame(rows)
    if not len(r):
        return {"own-load slope": "no BE HP home without battery has P1 and HP"}
    ok = r[r["hinge_inside"] & ~r["at_bound"]]
    agg = pd.concat(own_all, axis=1).dropna()
    return {"own-load homes (HP, no battery, P1+HP)": len(r), "own-load days per home": q(r["days"], 0),
            "own-load fits per home (all, incl. at bound)": r[["home", "days", "s0", "T_h", "r2", "at_bound", "own_T"]].round(4).to_dict("records"),
            "own non-HP slope kW/K per HP home (hinge inside, not at bound)": q(ok["s0"], 4),
            "own-load T_h": q(ok["T_h"], 1), "own-load r2": q(ok["r2"], 2),
            "own slope of the aggregate / n (days with all homes)": (round(s0_fit(site_T.reindex(agg.index), agg.sum(axis=1), agg.shape[1])["s0"], 4)
                                                                     if len(agg) > 60 else f"only {len(agg)} common days")}


# ------------------------------------------------------------------ Fluvius 2024 sample (new) --
def flu24_scan(lim):
    parts = []
    cols = ["EAN_ID", "Datum", "Volume_Afname_KWh", "Volume_Injectie_KWh", "Warmtepomp_Indicator", "Elektrisch_Voertuig_Indicator",
            "PV_Installatie_Indicator"]
    for z in FLU24:
        with zipfile.ZipFile(op(D / z, "Fluvius 2024 sample: daily import/export per meter")) as Z:
            for name in Z.namelist()[:lim]:
                for ch in pd.read_csv(Z.open(name), usecols=cols, chunksize=4_000_000):
                    g = ch.groupby(["EAN_ID", "Datum", "Warmtepomp_Indicator", "Elektrisch_Voertuig_Indicator", "PV_Installatie_Indicator"])
                    parts.append(pd.DataFrame({"imp_kWh": g["Volume_Afname_KWh"].sum(), "exp_kWh": g["Volume_Injectie_KWh"].sum(),
                                               "n": g.size()}).reset_index().assign(file=name.removeprefix("P6269_Open_Data_")[:-4]))
    x = pd.concat(parts)
    k = ["file", "EAN_ID", "Datum", "Warmtepomp_Indicator", "Elektrisch_Voertuig_Indicator", "PV_Installatie_Indicator"]
    return x.groupby(k, as_index=False)[["imp_kWh", "exp_kWh", "n"]].sum()


def fluvius24(cfg, cache):
    x = cached(cache, "fluvius24_daily", lambda: flu24_scan(cfg["limit_files"]))
    full = x["n"] >= 92                                                      # >= 92 of 96 quarter-hours (DST days: 92 / 100)
    u = x.assign(full=full).groupby(["file", "EAN_ID"]).agg(
        days=("Datum", "nunique"), full_days=("full", "sum"), hp=("Warmtepomp_Indicator", "max"), hp_flags=("Warmtepomp_Indicator", "nunique"),
        ev=("Elektrisch_Voertuig_Indicator", "max"), pv=("PV_Installatie_Indicator", "max"), imp_MWh=("imp_kWh", "sum"),
        exp_MWh=("exp_kWh", "sum")).reset_index()
    u[["imp_MWh", "exp_MWh"]] /= 1000
    u["complete"] = u["full_days"] >= cfg["coverage"] * 366
    t = u.groupby("file").agg(meters=("EAN_ID", "nunique"), complete=("complete", "sum"), hp=("hp", "sum"), ev=("ev", "sum"),
                              pv=("pv", "sum"), flag_changes=("hp_flags", lambda s: int((s > 1).sum())),
                              import_MWh_median=("imp_MWh", "median"), export_MWh_median=("exp_MWh", "median")).reset_index()
    f = {"meters": int(u["EAN_ID"].nunique()), "EAN_ID shared between files": int(u.duplicated("EAN_ID").sum()),
         "period": f"{x['Datum'].min()} .. {x['Datum'].max()}",
         "HP-flagged, no PV, complete (gross whole-house load)": int((u["hp"].eq(1) & u["pv"].eq(0) & u["complete"]).sum()),
         "HP-flagged, no PV, no EV, complete": int((u["hp"].eq(1) & u["pv"].eq(0) & u["ev"].eq(0) & u["complete"]).sum()),
         "non-HP, no PV, no EV, complete (local s0 fill)": int((u["hp"].eq(0) & u["pv"].eq(0) & u["ev"].eq(0) & u["complete"]).sum()),
         "temperature on disk": "none for Flanders 2024 (Solcast files on disk carry irradiance only)"}
    return f, t, u


# ------------------------------------------------------------------ FeederBW (registry + feeders) --
def feederbw(cfg):
    m = pd.read_csv(op(D / "FeederBW/feeder_metadata.csv", "FeederBW registry (labels, housing units)")).sort_values(["feeder", "date"])
    m["eheat_kW"] = m["storage_heaters_kW"] + m["electric_heaters_kW"]
    g = m.groupby("feeder")
    r = pd.DataFrame({"units": g["housing_units_count"].median(), "ic": g["industry_and_commerce_count"].max(),
                      "hp_kW_first": g["heat_pumps_kW"].first(), "hp_kW_last": g["heat_pumps_kW"].last(),
                      "hp_kW_values": g["heat_pumps_kW"].nunique(), "eheat_kW_max": g["eheat_kW"].max(), "pv_kW_max": g["PV_systems_kW"].max(),
                      "ev_kW_max": g["EV_chargers_kW"].max(), "metadata_rows": g.size()})
    w = pd.read_parquet(op(D / "FeederBW/weather_data.parquet", "FeederBW per-feeder air temperature"),
                        columns=["feeder", "timestamp_UTC", "air_temperature_C"])
    w["day"] = pd.to_datetime(w["timestamp_UTC"]).dt.floor("D")
    Td = w.groupby(["feeder", "day"])["air_temperature_C"].mean()
    a, b = map(pd.Timestamp, cfg["feederbw_year"])
    cov, s0 = {}, []
    files = sorted((D / "FeederBW").glob("feeder_measurement_data_*/**/feeder_*.parquet"), key=lambda p: p.name)  # 001-040 nested once more
    for fp in files[: (5 if cfg["limit_files"] else None)]:
        p = pd.read_parquet(op(fp, "FeederBW feeder active power (coverage; s0 if no HP/electric heating registered)"),
                            columns=["feeder", "timestamp_UTC", "active_power_kW"])
        fid = int(p["feeder"].iloc[0])
        p["day"] = pd.to_datetime(p["timestamp_UTC"]).dt.floor("D")
        dd = p.groupby("day")["active_power_kW"].agg(["mean", "count"])
        dd = dd[dd["count"] >= 0.9 * 96]
        cov[fid] = {"t0": dd.index.min(), "t1": dd.index.max(), "full_days": len(dd), "full_days_year": int(((dd.index >= a) & (dd.index < b)).sum())}
        rr = r.loc[fid]
        if rr["hp_kW_first"] == 0 and rr["hp_kW_values"] == 1 and rr["eheat_kW_max"] == 0 and rr["units"] > 0:
            y = dd.loc[(dd.index >= a) & (dd.index < b), "mean"]
            if len(y) >= cfg["coverage"] * (b - a).days:
                s0.append({"feeder": fid, "pv_kW": rr["pv_kW_max"], "ic": rr["ic"], **s0_fit(Td.loc[fid].reindex(y.index), y, rr["units"])})
    r = r.join(pd.DataFrame(cov).T)
    s0 = pd.DataFrame(s0)
    hp = r[r["hp_kW_last"] > 0]
    f = {"feeders": len(r), "feeders read": len(cov), "housing units per feeder": q(r["units"], 0),
         "feeders with HP kW > 0 (last registry row)": len(hp), "feeders whose HP kW changes": int((r["hp_kW_values"] > 1).sum()),
         "HP kW per feeder (HP > 0)": q(hp["hp_kW_last"], 1), "HP kW per housing unit (HP > 0)": q(hp["hp_kW_last"] / hp["units"], 3),
         "feeders with storage/electric heaters registered": int((r["eheat_kW_max"] > 0).sum()),
         "feeders with HP > 0 and no electric heating": int(((r["hp_kW_last"] > 0) & (r["eheat_kW_max"] == 0)).sum()),
         "feeders with no HP and no electric heating": int(((r["hp_kW_values"] == 1) & (r["hp_kW_first"] == 0) & (r["eheat_kW_max"] == 0)).sum()),
         "feeders with PV registered": int((r["pv_kW_max"] > 0).sum()), "feeders with commerce": int((r["ic"] > 0).sum()),
         f"full days {cfg['feederbw_year'][0]}..{cfg['feederbw_year'][1]} (median feeder)": float(r["full_days_year"].median()) if len(cov) else None}
    if len(s0):
        ok = s0[s0["hinge_inside"] & ~s0["at_bound"]]
        f |= {"s0 feeders fitted": len(s0), "s0 fit errors (listed in feederbw_s0.csv)": int(s0.get("fit_error", pd.Series(dtype=str)).notna().sum()),
              "s0 hinge inside, not at bound": len(ok), "s0 kW/K per housing unit, all": q(ok["s0"], 4),
              "s0, no PV no commerce": q(ok.loc[(ok["pv_kW"] == 0) & (ok["ic"] == 0), "s0"], 4), "s0 T_h": q(ok["T_h"], 1)}
    return f, r, s0


# ------------------------------------------------------------------ UKPN, HEAPO beyond B*, NEEA, WPuQ --
def ukpn():
    L = pd.read_csv(op(D / "ukpn-low-carbon-technologies-secondary.csv", "UKPN LCT register (HP rows = label)"), encoding="utf-8-sig")
    hp = L[L["Type"].astype(str).str.contains("Heat Pump", case=False)]
    F = pd.read_csv(op(D / "ukpn-smart-meter-consumption-lv-feeder.csv", "UKPN LV feeder smart-meter aggregates (counts, period)"),
                    encoding="utf-8-sig", usecols=["dataset_id", "secondary_substation_id", "lv_feeder_id", "aggregated_device_count_active",
                                                   "data_collection_log_timestamp"])
    t = pd.to_datetime(F["data_collection_log_timestamp"], utc=True)
    fd = F.drop_duplicates(["secondary_substation_id", "lv_feeder_id"])
    return {"LCT HP rows": len(hp), "HP connections (sum)": int(hp["LCT_Connections"].sum()),
            "HP connections per substation": q(hp["LCT_Connections"], 0), "HP import kW per row": q(hp["Import"], 1),
            "LV feeders": len(fd), "secondary substations": int(F["secondary_substation_id"].nunique()),
            "devices per feeder": q(fd["aggregated_device_count_active"], 0), "period": f"{t.min():%Y-%m-%d} .. {t.max():%Y-%m-%d}",
            "datasets": F["dataset_id"].unique().tolist(),
            "HP substations present in the feeder file": int(hp["FunctionalLocation"].isin(F["secondary_substation_id"]).sum())}


def heapo_extra(cfg):
    m = pd.read_parquet(op(D / "_paperb/pools/bstar_2023_meta.parquet", "B* membership (disjointness check)"))
    bstar = {i.removeprefix("H:") for i in m.index[(m["role"] == "hp") & (m["source"] == "heapo")]}
    out = {"B* HEAPO HP households": len(bstar)}
    for name in ("heapo15", "heapo_daily"):
        sc = pd.read_parquet(op(D / f"_paperb/iter01/coverage_{name}.parquet", "HEAPO coverage scan (iter01)"))
        sc["id"] = sc["id"].astype(str)
        new = sc[~sc["id"].isin(bstar)]
        for ch in ("total", "hp"):
            ok = new[new[ch] >= cfg["coverage"] * new["n_expected"]]
            out[f"{name} {ch} >= {cfg['coverage']:.0%}, not in B* (per window)"] = ok.groupby("window")["id"].nunique().to_dict()
    hh = pd.read_csv(op(D / "heapo_data/meta_data/households.csv", "HEAPO households (group, protocols)"), sep=None, engine="python")
    pr = pd.read_csv(op(D / "heapo_data/reports/protocols.csv", "HEAPO protocols (nameplate label)"), sep=None, engine="python")
    np_col = "HeatPump_Installation_Normpoint_ElectricPower"
    rid = hh[["Household_ID", "Protocols_ReportIDs"]].dropna()                # protocols.csv leaves Household_ID empty for many rows
    rid = rid.assign(Report_ID=rid["Protocols_ReportIDs"].str.strip("[]").str.split(",")).explode("Report_ID")
    rid = rid.assign(Report_ID=pd.to_numeric(rid["Report_ID"], errors="coerce")).dropna(subset=["Report_ID"])
    pr = pr.drop(columns="Household_ID").merge(rid[["Report_ID", "Household_ID"]], on="Report_ID").dropna(subset=[np_col])
    pr = pr.astype({"Household_ID": str}).sort_values("Visit_Year").drop_duplicates("Household_ID", keep="last")
    out |= {"HEAPO households": len(hh), "groups": hh["Group"].value_counts().to_dict(),
            "with nameplate electric power (protocol)": len(pr), "with nameplate, not in B*": int((~pr["Household_ID"].isin(bstar)).sum())}
    bp = m[(m["role"] == "hp") & (m["source"] == "heapo")].assign(id=lambda d: d.index.str.removeprefix("H:"))
    r = bp.merge(pr[["Household_ID", np_col]], left_on="id", right_on="Household_ID")
    out["source-only mapping: B* HP_Peak / nameplate electric power"] = q(r["hp_peak"] / pd.to_numeric(r[np_col], errors="coerce"), 2)
    return out


def neea(cfg):
    U = pd.read_parquet(op(D / "_paperb/iter04/neea_units.parquet", "NEEA per-home fits from 04 (s_res = own non-HP slope)"))
    fs = U[U["full_submeter"]]
    ids = pd.read_parquet(op(D / "_paperb/iter04/neea_fill.parquet", "NEEA fill homes from 04 (no electric heating)"))
    ids = list(ids.loc[ids["full_days"] >= 330, "ee_site_id"])
    S = pd.read_csv(op(D / "SITES v9.2.csv", "NEEA site states"))
    p = pd.read_parquet(op(D / "neea_base_circuits_2023.parquet", "NEEA mains of fill homes (s0)"), columns=["ee_site_id", "End Use", "MIN_T_l", "power"])
    p = p[p["ee_site_id"].isin(ids) & (p["End Use"] == "Mains")]
    y = p.groupby(["ee_site_id", p["MIN_T_l"].dt.floor("D")])["power"].mean().unstack(0)
    t = pd.read_parquet(op(D / "neea_temp_2023.parquet", "NEEA outdoor probes"))
    t = t[t["regname"].astype(str).str.contains("_oa_")]
    T = ((t["temp"] - 32) * 5 / 9).groupby([t["ee_site_id"].astype(int), t["MIN_T_l"].dt.floor("D")]).mean().unstack(0)
    st = S.set_index("ee_site_id")["state"]
    k = U[U["s_heat"].notna() & ~U["gas_furnace"] & ~U["solar"] & (U["s_heat"] > 0.05)]     # 04's rule without its s_res <= 0.2 s_heat cut
    out = {"HP homes, heating fully submetered (04 rule, selects on s_res)": len(fs), "own non-HP slope s_res kW/K per HP home (04 rule)": q(fs["s_res"], 4),
           "HP homes, no gas furnace, no PV, s_heat > 0.05 (no s_res cut)": len(k), "per state (no s_res cut)": k["state"].value_counts().to_dict(),
           "own non-HP slope s_res kW/K per HP home (no s_res cut)": q(k["s_res"], 4),
           "fill homes (no electric heating, >= 330 full days)": len(ids), "fill homes per state": st.reindex(ids).value_counts().to_dict()}
    for s in st.reindex(ids).value_counts().index:
        h = [i for i in ids if st.get(i) == s and i in y.columns]
        if len(h) >= 10:
            Ts = T.reindex(columns=[c for c in T.columns if st.get(c) == s]).mean(axis=1)
            for lab, tmax in (("all days", None), ("days T <= 18 C (no cooling)", 18)):
                r = s0_fit(Ts.reindex(y.index), y[h].mean(axis=1) * len(h), len(h), tmax)
                out[f"s0 {s} aggregate, {lab}"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
    return out


def wpuq():
    import pickle
    with open(op(D / "_wpuq_pool_cache.pkl", "WPuQ legacy pool cache (household meters of HP homes = own load)"), "rb") as fh:
        P = pickle.load(fh)
    idx = P["index"]
    own = pd.DataFrame(P["other_mat"].T, index=idx, columns=P["households"]).resample("D").mean()
    T = pd.Series(P["temperature"]["WPUQ"], index=idx).resample("D").mean()
    rows = [s0_fit(T, own[h], 1) | {"home": h} for h in own.columns]
    r = pd.DataFrame(rows)
    ok = r[r["hinge_inside"] & ~r["at_bound"]]
    return {"HP homes with household meter": len(r), "own non-HP slope kW/K per home": q(ok["s0"], 4),
            "own slope of the aggregate / n": round(s0_fit(T, own.sum(axis=1), own.shape[1])["s0"], 4),
            "period": f"{idx.min():%Y-%m-%d} .. {idx.max():%Y-%m-%d}"}


# ------------------------------------------------------------------ envelopes (v1.1, no stacking) --
def envelopes(cfg, be_ok, flu_u, grid):
    seeds = [cfg["seeds"]["split"] + i for i in range(cfg["seeds"]["n_split_seeds"])]
    fill = flu_u[flu_u["hp"].eq(0) & flu_u["pv"].eq(0) & flu_u["ev"].eq(0) & flu_u["complete"]]
    fill = pd.DataFrame({"role": "fill", "station": "any"}, index="F:" + fill["EAN_ID"].astype(str))
    hpf = flu_u[flu_u["hp"].eq(1) & flu_u["pv"].eq(0) & flu_u["ev"].eq(0) & flu_u["complete"]]
    pools = {"BE monitoring (HP+P1 complete) + Fluvius 2024 fill": pd.concat([pd.DataFrame({"role": "hp", "station": "BE"}, index=[f"B:{i}" for i in be_ok]), fill]),
             "Fluvius 2024 HP-flag (no PV, no EV) + Fluvius 2024 fill": pd.concat([pd.DataFrame({"role": "hp", "station": "BE"}, index="F:" + hpf["EAN_ID"].astype(str)), fill])}
    U = pd.read_parquet(op(D / "_paperb/iter04/neea_units.parquet", "NEEA HP homes (envelope)"))
    nf = pd.read_parquet(op(D / "_paperb/iter04/neea_fill.parquet", "NEEA fill (envelope)"))
    pools["US-NEEA cal2023"] = pd.concat([U[U["full_submeter"]].set_index("ee_site_id")[["state"]].rename(columns={"state": "station"})
                                          .assign(role="hp").rename(index=lambda i: f"N:{i}"),
                                          pd.DataFrame({"role": "fill", "station": "any"}, index=[f"N:{i}" for i in nf.loc[nf["full_days"] >= 330, "ee_site_id"]])])
    rows = []
    for name, meta in pools.items():
        nh = int((meta["role"] == "hp").sum())
        if nh < 2 * grid["min_station_pool"]:
            rows.append({"pool": name, "HP": nh, "fill": int((meta["role"] == "fill").sum()), "note": "too few HP for a split"})
            continue
        S, B, Z = envelope(meta, seeds, grid)
        rows.append({"pool": name, "HP": nh, "fill": int((meta["role"] == "fill").sum()),
                     **{f"HP per split ({k})": round(S[k].sum(), 1) for k in S},**{f"test subs {k}": v for k, v in B.items()},
                     **{f"max size {k}": v for k, v in Z.items() if not k.startswith("uncapped")}})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    out, cache = ROOT / cfg["out_dir"], ROOT / cfg["cache_dir"]
    out.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    grid = yaml.safe_load(open(ROOT / "configs/protocol_v1.yaml"))["grid"] | yaml.safe_load(open(ROOT / "configs/protocol_v1_1.yaml"))["grid"]
    t0, facts = time.time(), {}
    facts["BE monitoring"], be_per, be_keys, be_ok = be_monitoring(cfg, cache)
    facts["Fluvius 2024"], flu_t, flu_u = fluvius24(cfg, cache)
    facts["FeederBW"], fb_r, fb_s0 = feederbw(cfg)
    facts["UKPN"] = ukpn()
    facts["HEAPO beyond B*"] = heapo_extra(cfg)
    facts["NEEA"] = neea(cfg)
    facts["WPuQ"] = wpuq()
    env = envelopes(cfg, be_ok, flu_u, grid)
    be_per.to_csv(out / "be_series.csv", index=False)
    flu_t.to_csv(out / "fluvius24_files.csv", index=False)
    fb_r.to_csv(out / "feederbw_feeders.csv")
    fb_s0.to_csv(out / "feederbw_s0.csv", index=False)
    env.to_csv(out / "envelopes.csv", index=False)
    (out / "facts.json").write_text(json.dumps(facts, indent=1, default=str), encoding="utf-8")
    long = [{"exp_id": cfg["exp_id"], "dataset": d, "metric": k, "value": json.dumps(v, default=str)} for d, f in facts.items() for k, v in f.items()]
    pd.DataFrame(long).to_csv(out / "metrics.csv", index=False)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    (out / "config.yaml").write_text(yaml.safe_dump({**cfg, "git_commit": commit, "grid": grid}), encoding="utf-8")
    md = "\n\n".join(f"### {d}\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in f.items()) for d, f in facts.items())
    (out / "facts.md").write_text(f"# 07b-i facts ({cfg['exp_id']}, commit {commit[:7]})\n\n{md}\n\n### BE series keys\n\n{md_table(be_keys)}\n\n"
                                  f"### Fluvius 2024 files\n\n{md_table(flu_t)}\n\n### Envelopes (v1.1)\n\n{md_table(env)}\n", encoding="utf-8")
    log = [f"07b-i audit, config {cfg['exp_id']}, commit {commit}, runtime {time.time() - t0:.0f} s",
           "Blindness: no estimator, prediction or error metric computed on any candidate.", "", "Files opened (path | purpose):"]
    log += [f"{p} | {w}" for p, w in dict.fromkeys(OPENED)]
    log += ["", "Raw sources read when the caches above were first built (same script):"]   # cached runs do not reopen them
    log += [f"data\\{pre}_*.gz.parquet (all parts) | BE monitoring: series inventory (keys, rows per day)" for pre in BE_SETS.values()]
    log += [f"data\\{z} (all 8 CSVs) | Fluvius 2024 sample: daily import/export per meter" for z in FLU24]
    (out / "log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"wrote {out} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    sys.exit(main())
