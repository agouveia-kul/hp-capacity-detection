"""Iteration 04, Task 1 -- dataset inventory v2 (read-only; counts computed from the files).

EoH is joined to the USmart Property/Design/Installation table (data/_paperb/raw/eoh/eoh_property_design_installation.csv).
Writes results/iter04_inventory/inventory.{md,csv} and per-unit tables for Task 2 in
data/_paperb/iter04/ (eoh_units, rhpp_units, neea_units, fluvius_units parquet).
Heavy scans (Fluvius, Pecan Street, NEEA per-home fits) are cached there.

A "complete heating season" is Nov 1 - Mar 31 (naive timestamps as stored) with >= 90 % of
the expected samples valid for the unit's key channel (listed per dataset).

    python scripts/audit/inventory_v2.py --config configs/iter04_inventory.yaml
"""
import argparse
import glob
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "audit"))
from hp_common import fit_hockey_stick  # noqa: E402
from pool_inventory import HEAPO, covered, kaiser_meta, kaiser_units, load_scans, md_table  # noqa: E402

D = ROOT / "data"
CACHE = D / "_paperb" / "iter04"
SEASONS = {f"{y}/{(y + 1) % 100:02d}": (pd.Timestamp(f"{y}-11-01"), pd.Timestamp(f"{y + 1}-04-01")) for y in range(2009, 2025)}
NEEA_HEAT = ("Ductless Heatpump", "Ducted Heatpump", "Electric Baseboard Heaters", "Electric Furnace", "Other Zonal Heat")
NEEA_COOL = ("Central AC", "Room AC")
PROP_COLS = ["HP_Installed", "HP_Installed_Detail", "HP_Size_kW", "HP_Brand", "MCS_SHLoad", "MCS_Flow_Temp", "Postcode_1",
             "Delivery_Contractor", "House_Form", "House_Age", "Total_Floor_Area", "Tenure", "Elec_currentuse"]


def seasons_ok(t, step, cov=0.9):
    """Complete Nov-Mar seasons of a unit given the timestamps of its valid samples."""
    t = pd.DatetimeIndex(t)
    return [s for s, (a, b) in SEASONS.items() if ((t >= a) & (t < b)).sum() >= cov * ((b - a) / step)]


def cached(name, fn):
    p = CACHE / f"{name}.parquet"
    if not p.exists():
        print(f"building {p.name} ...", flush=True)
        fn().to_parquet(p)
    return pd.read_parquet(p)


def hist(n):
    return ", ".join(f"{k}: {v}" for k, v in sorted(pd.Series(n).value_counts().items()))


# ---------------------------------------------------------------- datasets --
def eoh():
    S = pd.read_parquet(D / "_paperb/pools_raw/eoh/eoh_sites.parquet")
    summ = pd.read_csv(D / "_paperb/raw/eoh/clean/eoh_summary_for_publication.csv")
    units = []
    for f in sorted(glob.glob(str(D / "_paperb/pools_raw/eoh/eoh_30min_set*.parquet"))):
        F = pd.read_parquet(f, columns=["property", "ts", "n_P_ws", "n_Q_hp", "T_ext", "T_flow_sh"])
        for pid, g in F.groupby("property", observed=True):
            ws = g["n_P_ws"] >= 12
            units.append({"property": pid, "seasons_ws": seasons_ok(g.loc[ws, "ts"], pd.Timedelta("30min")),
                          "seasons_ws_q": seasons_ok(g.loc[ws & (g["n_Q_hp"] >= 12), "ts"], pd.Timedelta("30min")),
                          "T_ext_share": float(g["T_ext"].notna().mean()), "T_flow_share": float(g["T_flow_sh"].notna().mean())})
    U = S.merge(pd.DataFrame(units), on="property", how="left").merge(
        summ[["Property_ID", "Included_SPF_analysis"]].rename(columns={"Property_ID": "property"}), on="property", how="left")
    ch = U["channels"].fillna("")
    U["type_channels"] = np.select([ch == "EMPTY FILE", ch.str.contains("T_brine"), ch.str.contains("Q_boiler")],
                                   ["empty", "GSHP", "hybrid"], "ASHP/HT-ASHP")
    P = pd.read_csv(D / "_paperb/raw/eoh/eoh_property_design_installation.csv", low_memory=False)     # USmart table (user-supplied)
    U = U.merge(P[["Property_ID"] + PROP_COLS].rename(columns={"Property_ID": "property"}), on="property", how="left")
    U["type"] = U["HP_Installed"].map({"ASHP": "ASHP", "HT_ASHP": "HT-ASHP", "GSHP": "GSHP", "Hybrid": "hybrid"}).fillna(U["type_channels"])
    U["area"] = U["Postcode_1"].str.extract(r"^([A-Z]+)", expand=False)
    U["oversize"] = U["HP_Size_kW"] / U["MCS_SHLoad"].where(U["MCS_SHLoad"] > 0)
    for c in ("seasons_ws", "seasons_ws_q"):
        U["n_" + c] = U[c].apply(lambda x: len(x) if isinstance(x, (list, np.ndarray)) else 0)
        U[c + "_str"] = U[c].apply(lambda x: ";".join(x) if isinstance(x, (list, np.ndarray)) else "")
    U["share_ih_buh"] = (U[["E_P_ih_kWh", "E_P_buh_kWh"]].fillna(0).sum(axis=1) / U["E_P_ws_kWh"]).where(U["E_P_ws_kWh"] > 0)
    U.drop(columns=["seasons_ws", "seasons_ws_q"]).to_parquet(CACHE / "eoh_units.parquet")
    ok = U["n_seasons_ws"] >= 1
    per_season = pd.Series([s for x in U["seasons_ws"].dropna() for s in x]).value_counts().sort_index()
    return {"dataset": "EoH (UKDS SN 9050)", "unit": "home (HP system only)",
            "units_total": len(U), "empty_files": int((ch == "EMPTY FILE").sum()),
            "hp_submeter_units": int((U["n_rows"] > 0).sum()), "hp_submeter_units_>=1_season": int(ok.sum()),
            "whole_house_units": 0, "resolution": "2 min (converted to 30 min)",
            "period": f"{U['start'].min():%Y-%m} .. {U['end'].max():%Y-%m}",
            "complete_seasons_per_unit": hist(U["n_seasons_ws"]), "units_per_season": per_season.to_dict(),
            "units_with_heat_meter_>=1_season": int((U["n_seasons_ws_q"] >= 1).sum()),
            "weather": f"T_ext per home (local weather station), >=50% of 30-min bins in {int((U['T_ext_share'] >= .5).sum())} homes; "
                       "postcode district (Postcode_1) for station matching",
            "capacity_label": f"HP_Size_kW (rated, property table) for {int(U['HP_Size_kW'].notna().sum())} homes, median "
                              f"{U['HP_Size_kW'].median():.1f} kW; MCS_SHLoad (design heat load) for {int(U['MCS_SHLoad'].notna().sum())}; "
                              f"oversizing HP_Size/MCS_SHLoad median {U['oversize'].median():.2f}; robust peak (P_ws)",
            "hp_type": " / ".join(f"{k}: {v}" for k, v in U["type"].value_counts().items()) + " (HP_Installed); channel-inferred type agrees for "
                       f"{int((U['type'].replace({'ASHP': 'ASHP/HT-ASHP', 'HT-ASHP': 'ASHP/HT-ASHP'}) == U['type_channels']).sum())} of {len(U)}",
            "backup_channels": f"immersion (P_ih) {ch.str.contains('P_ih').sum()}, back-up heater (P_buh) {ch.str.contains('P_buh').sum()}",
            "dhw_channels": f"DHW flow temperature {ch.str.contains('T_flow_dhw').sum()} (no separate DHW heat/electricity)",
            "building_metadata": f"House_Form {int(U['House_Form'].notna().sum())}, House_Age {int(U['House_Age'].notna().sum())}, "
                                 f"Total_Floor_Area {int(U['Total_Floor_Area'].notna().sum())}, Tenure {int(U['Tenure'].notna().sum())}; "
                                 f"annual pre-install electricity (bills) {int(U['Elec_currentuse'].notna().sum())}",
            "location": f"postcode district for {int(U['Postcode_1'].notna().sum())}; by delivery contractor "
                        f"{U['Delivery_Contractor'].value_counts().to_dict()}; top areas {U['area'].value_counts().head(6).to_dict()}",
            "licence": "performance data: Open Government Licence v2.0 (UKDA_Study_9050_Information.htm), DOI 10.5255/UKDA-SN-9050-2; "
                       f"property table: USmart download supplied by Alex, licence not on disk ({len(P)} properties, "
                       f"{int(P['HP_Installed'].notna().sum())} installed)"}


def rhpp():
    Dd = pd.read_parquet(D / "rhpp_daily.parquet")
    S = pd.read_parquet(D / "rhpp_sites.parquet")
    with zipfile.ZipFile(D / "RHPP_GB.zip") as z:
        M = pd.read_excel(io.BytesIO(z.read("UKDA-8151-csv/mrdoc/excel/8151_rhpp_metadata.xlsx")))
    M["site"] = M["Site.ID"].str.upper()
    S["site"] = S["site"].str.upper()
    sea = Dd.assign(site=Dd["site"].str.upper()).groupby("site")["day"].apply(lambda d: seasons_ok(d, pd.Timedelta("1D")))
    comp = Dd.assign(site=Dd["site"].str.upper()).groupby("site")[["Edhw", "Esp", "Eboost", "Hhp"]].sum()
    U = S.merge(M, on="site", how="left").set_index("site").join(sea.rename("seasons")).join(comp)
    U["n_seasons"] = U["seasons"].apply(len)
    U["cap_label_kW"] = pd.to_numeric(U["Installer.net.capacity.corrected"], errors="coerce")
    U["flagged"] = U["Incorrect.Monitoring"].notna()
    U.drop(columns=["seasons"]).astype({c: str for c in U.columns if U[c].dtype == object and c != "seasons"}).to_parquet(CACHE / "rhpp_units.parquet")
    per_season = pd.Series([s for x in U["seasons"] for s in x]).value_counts().sort_index()
    return {"dataset": "RHPP Sample B2 (UKDS SN 8151)", "unit": "home (HP system only)", "units_total": len(U),
            "hp_submeter_units": len(U), "hp_submeter_units_>=1_season": int((U["n_seasons"] >= 1).sum()),
            "whole_house_units": 0, "resolution": "2 min", "period": f"{S['start'].min():%Y-%m} .. {S['end'].max():%Y-%m}",
            "complete_seasons_per_unit": hist(U["n_seasons"]), "units_per_season": per_season.to_dict(),
            "units_with_heat_meter_>=1_season": int(((U["n_seasons"] >= 1) & (U["Hhp"] > 0)).sum()),
            "weather": "none in data (T_in is evaporator/ground-loop temperature); national HadCET used by Paper A",
            "capacity_label": f"installer net capacity (kW) for {int(U['cap_label_kW'].notna().sum())} of {len(U)}; robust peak",
            "hp_type": " / ".join(f"{k}: {v}" for k, v in U["Heat.pump.type"].value_counts().items()) + " (on-off/inverter not recorded)",
            "backup_channels": f"E_sp > 0: {int((U['Esp'] > 0).sum())}, E_boost > 0: {int((U['Eboost'] > 0).sum())}",
            "dhw_channels": f"E_dhw > 0: {int((U['Edhw'] > 0).sum())}; H_hw and T_wf (cylinder flow)",
            "building_metadata": f"property type {int(U['Property.Type'].notna().sum())}, age {int(U['Age.of.property'].notna().sum())}, "
                                 f"emitter {int(U['Emitter.type'].notna().sum())}, tenure (Site.type RSL/Domestic) {int(U['Site.type'].notna().sum())}",
            "location": "none", "licence": "UKDS End User Licence (not redistributable)",
            "notes": f"{int(U['flagged'].sum())} sites flagged 'Monitoring Problem'"}


def lcl():
    rows = []
    for f in sorted(glob.glob(str(D / "lcl_heatpump/*.csv"))):
        d = pd.read_csv(f, usecols=["timestamp", "heat_pump_energy_consumption", "external_temperature"])
        t = pd.to_datetime(d["timestamp"])
        ok = d["heat_pump_energy_consumption"].diff().ge(0)
        rows.append({"file": Path(f).name, "start": t.min(), "end": t.max(), "seasons": seasons_ok(t[ok], pd.Timedelta("15min"))})
    L = pd.DataFrame(rows)
    p = "UKDA-7857-csv/csv/data_collection/data_tables/"
    with zipfile.ZipFile(D / "LCL_2013.zip") as Z:
        a = pd.read_csv(io.BytesIO(Z.read(p + "survey_answers.csv")), encoding="latin-1", low_memory=False)
        n_n = len(pd.read_csv(Z.open(p + "consumption_n.csv"), nrows=0).columns) - 1
        n_d = len(pd.read_csv(Z.open(p + "consumption_d.csv"), nrows=0).columns) - 1
        g = pd.read_csv(Z.open(p + "consumption_d.csv"), usecols=[0])
    q = a["Q248"].astype(str)
    return [{"dataset": "LCL heat-pump trial (lcl_heatpump/)", "unit": "home (HP only)", "units_total": len(L),
             "hp_submeter_units": len(L), "hp_submeter_units_>=1_season": int((L["seasons"].apply(len) > 0).sum()),
             "whole_house_units": 0, "resolution": "15 min (cumulative kWh)", "period": f"{L['start'].min():%Y-%m} .. {L['end'].max():%Y-%m}",
             "complete_seasons_per_unit": hist(L["seasons"].apply(len)), "weather": "external_temperature per home",
             "capacity_label": "none", "hp_type": "not recorded", "backup_channels": "immersion_heater_energy_consumption in "
             f"{sum('immersion' in ''.join(pd.read_csv(f, nrows=0).columns) for f in glob.glob(str(D / 'lcl_heatpump/*.csv')))}",
             "dhw_channels": "cylinder pipe temperatures", "building_metadata": "none", "location": "London (trial)", "licence": "not documented on disk"},
            {"dataset": "LCL smart meters (UKDS SN 7857)", "unit": "household", "units_total": n_n + n_d, "hp_submeter_units": 0,
             "whole_house_units": n_n + n_d, "resolution": "30 min", "period": f"{str(g.iloc[0, 0])[:7]} .. {str(g.iloc[-1, 0])[:7]} (consumption_d)",
             "weather": "none (London)", "capacity_label": "none",
             "hp_type": f"survey Q248: gas boiler central heating {int((q.str.contains('gas boiler', case=False)).sum())}, "
                        f"'heat pump' mentioned {int(q.str.contains('heat pump', case=False).sum())}, electric {int(q.str.contains('electric', case=False).sum())} "
                        f"of {len(a)} surveyed", "building_metadata": "survey (appliances, heating)", "location": "London",
             "licence": "UKDS (open data edition)", "notes": f"standard tariff {n_n}, dynamic ToU {n_d} households (header counts)"}]


def neea():
    P = pd.read_csv(D / "POINTS v9.2.csv", low_memory=False)
    S = pd.read_csv(D / "SITES v9.2.csv")
    uses = P.groupby("ee_site_id")["circuit_label_type_desc"].agg(set)
    hp = uses[uses.apply(lambda s: bool(s & {"Ducted Heatpump", "Ductless Heatpump"}))]
    mains = hp[hp.apply(lambda s: bool(s & {"Mains", "Mains With Solar"}))]

    def fits():
        p = pd.concat([pd.read_parquet(D / f) for f in ("neea_base_circuits_2023.parquet", "neea_heating_circuits_2023.parquet")])
        p = p.drop_duplicates(["ee_site_id", "regname", "MIN_T_l"])
        p = p[p["ee_site_id"].isin(mains.index)]
        p["day"] = p["MIN_T_l"].dt.floor("D")
        n = p.groupby(["ee_site_id", "regname", "day"], observed=True).size()
        full = (n >= 90).groupby(level=[0, 2]).all()
        fam = np.select([p["End Use"].isin(NEEA_HEAT), p["End Use"].isin(NEEA_COOL), p["End Use"].isin(["Mains", "Mains With Solar"])],
                        ["heat", "cool", "mains"], "other")
        dd = p.assign(fam=fam).groupby(["ee_site_id", "day", "fam", "MIN_T_l"], observed=True)["power"].sum().groupby(level=[0, 1, 2]).mean().unstack(fill_value=0)
        dd = dd[full.reindex(dd.index).fillna(False).to_numpy()]
        t = pd.read_parquet(D / "neea_temp_2023.parquet")
        t = t[t["regname"].astype(str).str.contains("_oa_")]
        own = ((t["temp"] - 32) * 5 / 9).groupby([t["ee_site_id"].astype(int), t["MIN_T_l"].dt.floor("D")]).mean()
        stn = S.set_index("ee_site_id")["station_id"]
        by_st = own.groupby([own.index.get_level_values(0).map(stn), own.index.get_level_values(1)]).mean()
        rows = []
        for site, g in dd.groupby(level=0):
            g = g.droplevel(0)
            T = own.get(site, pd.Series(dtype=float)).reindex(g.index)
            T = T.fillna(by_st.get(stn.get(site), pd.Series(dtype=float)).reindex(g.index))
            x = pd.DataFrame({"T": T, "heat": g.get("heat", 0), "res": g["mains"] - g.get("heat", 0) - g.get("cool", 0)}).dropna()
            r = {"ee_site_id": site, "days": len(x)}
            if len(x) >= 120 and (x["T"] < 10).sum() >= 30:
                for k in ("heat", "res"):
                    try:
                        r[f"s_{k}"] = fit_hockey_stick(x["T"].to_numpy(), x[k].to_numpy(), (8, 20))[1]
                    except (RuntimeError, ValueError):          # e.g. negative residual (solar)
                        r[f"s_{k}"] = np.nan
            rows.append(r)
        return pd.DataFrame(rows)
    F = cached("neea_fits", fits)
    F["gas_furnace"] = F["ee_site_id"].map(uses).apply(lambda s: "Gas Furnace (Component)" in s)
    F["solar"] = F["ee_site_id"].map(uses).apply(lambda s: bool(s & {"Mains With Solar", "Solar"}))
    F["full_submeter"] = (F["s_heat"] > 0.05) & (F["s_res"] <= 0.2 * F["s_heat"]) & ~F["gas_furnace"]
    F["state"] = F["ee_site_id"].map(S.set_index("ee_site_id")["state"])
    F.to_parquet(CACHE / "neea_units.parquet")
    fs = F[F["full_submeter"]]
    return {"dataset": "NEEA HEMS v9.2 (2023 on disk)", "unit": "home (whole home + circuits)", "units_total": S.shape[0],
            "hp_submeter_units": len(hp), "whole_house_units": int(uses.apply(lambda s: bool(s & {'Mains', 'Mains With Solar'})).sum()),
            "hp_submeter_units_>=1_season": 0, "resolution": "15 min", "period": "2023-01 .. 2023-12 on disk (release 2018-08 .. 2025-06)",
            "complete_seasons_per_unit": "0 (only calendar 2023 on disk: Jan-Mar and Nov-Dec of different seasons)",
            "weather": "outdoor-air probe per home (TEMPERATURE15) + NOAA station id",
            "capacity_label": "robust peak only", "hp_type": f"ducted {int(hp.apply(lambda s: 'Ducted Heatpump' in s).sum())}, "
            f"ductless {int(hp.apply(lambda s: 'Ductless Heatpump' in s).sum())} (air-source, US)",
            "backup_channels": "electric furnace / baseboard / zonal circuits", "dhw_channels": "water-heater circuits (ERWH, HPWH)",
            "building_metadata": "RBSA tables (not on disk)", "location": f"state + NOAA station ({S['state'].value_counts().to_dict()})",
            "licence": "NEEA data-use terms (not redistributable)",
            "notes": f"HP + mains: {len(mains)}; fitted (>= 120 full days, >= 30 below 10 C): {int(F['s_heat'].notna().sum())}; "
                     f"heating fully submetered (s_heat > 0.05 kW/K, residual slope <= 20 % of it, no gas-furnace circuit): {len(fs)} "
                     f"({fs['state'].value_counts().to_dict()}), of which with solar {int(fs['solar'].sum())}"}


def field(name, pattern, cols, backup):
    rows = []
    for f in sorted(glob.glob(str(D / pattern))):
        d = pd.read_csv(f, low_memory=False, usecols=lambda c: c in cols)
        t = pd.to_datetime(d["local_datetime"].astype(str).str[:19], errors="coerce", format="mixed")
        ok = pd.to_numeric(d["HP_system_pwr_kW"], errors="coerce").notna() & t.notna()
        rows.append({"site": str(d["site_id"].iloc[0]), "start": t.min(), "end": t.max(), "seasons": seasons_ok(t[ok], pd.Timedelta("1h")),
                     "backup": backup in d and pd.to_numeric(d[backup], errors="coerce").fillna(0).gt(0.1).any()})
    U = pd.DataFrame(rows).drop_duplicates("site")
    return {"dataset": name, "unit": "home (HP system only)", "units_total": len(U), "hp_submeter_units": len(U),
            "hp_submeter_units_>=1_season": int((U["seasons"].apply(len) > 0).sum()), "whole_house_units": 0, "resolution": "hourly",
            "period": f"{U['start'].min():%Y-%m} .. {U['end'].max():%Y-%m}", "complete_seasons_per_unit": hist(U["seasons"].apply(len)),
            "weather": "OA_temp_F per home", "capacity_label": "none in files (robust peak)", "hp_type": "air-source (ducted, US)",
            "backup_channels": f"{backup} > 0.1 kW in {int(U['backup'].sum())}", "location": "site code (utility)", "licence": "US DOE Heat Pump Database"}


def cofactor():
    rows = []
    for f in sorted(glob.glob(str(D / "cofactor_ds1/building_*.txt"))):
        head = dict(l.strip().split(";", 1) for l in open(f, encoding="utf-8").readlines()[1:16] if ";" in l)
        rows.append({"id": head.get("building_id"), "units": int(head.get("number_of_units", 0) or 0), "sh": head.get("sh_heat_source", "")})
    C = pd.DataFrame(rows)
    hp = C["sh"].str.contains("HP")
    return {"dataset": "COFACTOR DS1 (Oslo/Baerum)", "unit": "apartment block (building)", "units_total": len(C),
            "hp_submeter_units": int(hp.sum()), "whole_house_units": len(C), "resolution": "hourly",
            "hp_type": f"space-heating sources: {C['sh'].value_counts().to_dict()}", "weather": "Tout per building",
            "capacity_label": "none", "building_metadata": f"year, floor area, {C['units'].sum()} apartments in total",
            "location": "Oslo / Baerum", "licence": "CC BY 4.0"}


def carleton():
    fuel = [re.search(r"Space heating,([^,]*)", open(f, encoding="latin-1").read()).group(1)
            for f in sorted(glob.glob(str(D / "carleton/Saldanha_Beausoleil-Morrison/processed_data/H*.csv")))]
    return {"dataset": "Carleton (Ottawa, 12 houses)", "unit": "house", "units_total": len(fuel), "hp_submeter_units": 0,
            "whole_house_units": len(fuel), "resolution": "1 min", "period": "2009-07 .. 2010-09 (README)",
            "hp_type": f"space heating: {pd.Series(fuel).value_counts().to_dict()} (furnace fan and AC submetered)",
            "capacity_label": "none", "licence": "free with citation (README)"}


def pecan():
    def scan():
        rows = []
        for city, f in (("austin", "15minute_data_austin/15minute_data_austin.csv"), ("newyork", "15minute_data_newyork/15minute_data_newyork.csv")):
            cols = ["dataid", "local_15min", "grid", "air1", "furnace1", "heater1"]
            for ch in pd.read_csv(D / f, usecols=lambda c: c in cols, chunksize=500_000):
                g = ch.groupby("dataid")
                rows.append(pd.DataFrame({"city": city, "n": g.size(), "grid": g["grid"].count(), "air1": g["air1"].count(),
                                          "heat": g[["furnace1", "heater1"]].count().sum(axis=1),
                                          "t0": g["local_15min"].min().str[:10], "t1": g["local_15min"].max().str[:10]}))
        return pd.concat(rows).groupby(["city", "dataid"]).agg({"n": "sum", "grid": "sum", "air1": "sum", "heat": "sum", "t0": "min", "t1": "max"}).reset_index()
    P = cached("pecan_scan", scan)
    out = []
    for city, g in P.groupby("city"):
        out.append({"dataset": f"Pecan Street 15-min ({city})", "unit": "home", "units_total": len(g),
                    "hp_submeter_units": 0, "whole_house_units": int((g["grid"] > 0).sum()),
                    "resolution": "15 min", "period": f"{g['t0'].min()[:7]} .. {g['t1'].max()[:7]}",
                    "hp_type": f"air1 (AC or HP compressor) circuit in {int(((g['air1'] > 0) & (g['grid'] > 0)).sum())}, furnace/heater circuit in "
                               f"{int((g['heat'] > 0).sum())}; heat pumps not labelled, so no HP submeter can be identified",
                    "capacity_label": "none", "licence": "Dataport academic licence (not redistributable)"})
    return out


def fluvius():
    def scan():
        parts = []
        for ch in pd.read_csv(D / "15minuteFluvius.csv", sep=";", usecols=["EAN_ID", "Datum", "Warmtepomp_Indicator", "Contract_Categorie"],
                              chunksize=5_000_000):
            g = ch.groupby("EAN_ID")
            parts.append(pd.DataFrame({"n": g.size(), "hp": g["Warmtepomp_Indicator"].max(), "t0": g["Datum"].min(), "t1": g["Datum"].max(),
                                       "cat": g["Contract_Categorie"].first()}))
        return pd.concat(parts).groupby(level=0).agg({"n": "sum", "hp": "max", "t0": "min", "t1": "max", "cat": "first"})
    F = cached("fluvius_units", scan)
    return {"dataset": "Fluvius 15-min (Flanders)", "unit": "household meter (net)", "units_total": len(F), "hp_submeter_units": 0,
            "whole_house_units": len(F), "resolution": "15 min", "period": f"{F['t0'].min()[:7]} .. {F['t1'].max()[:7]}",
            "capacity_label": f"HP flag only (Warmtepomp_Indicator = 1 for {int((F['hp'] == 1).sum())} meters)",
            "hp_type": "not recorded", "weather": "none (candidate: KMI Uccle / ERA5)", "location": "Flanders (no finer)",
            "notes": f"contract categories {F['cat'].value_counts().to_dict()}; median rows per meter {int(F['n'].median())}",
            "licence": "Fluvius open data (not documented on disk)"}


def swiss_extra():
    sc = load_scans(D / "_paperb/iter01")
    m = pd.read_parquet(D / "_paperb/pools/bstar_2023_meta.parquet")
    bstar = set(m.index[m["role"] == "hp"])
    h = covered(sc["heapo15"], "hp_other").assign(hh=lambda x: "H:" + x["id"].astype(str))
    sea = h[h["window"].str.contains("/")]
    km = kaiser_meta()
    ku = {k.split()[0]: v for k, v in kaiser_units(km).items()}
    ok = covered(sc["kaiser"], "total")
    ka = ku["K(a)"].merge(ok, on="id").merge(ok.rename(columns={"id": "hp_meter"}), on=["hp_meter", "window"])
    kp = ku["K(a')"].merge(ok, on="id")
    kp["otype"] = kp["id"].map(km.set_index("0_meter_id")["0_object_type"])
    w = covered(sc["wpuq"], "hp_other")
    return {"dataset": "HEAPO / Kaiser / WPuQ beyond B*", "unit": "household", "units_total": len(bstar),
            "hp_submeter_units": h["hh"].nunique(), "resolution": "15 min",
            "notes": (f"B* HP households {len(bstar)}. HEAPO 15-min HP+other, any heating season: {sea['hh'].nunique()} distinct, "
                      f"{len(set(sea['hh']) - bstar)} not in B* (per season {sea.groupby('window')['hh'].nunique().to_dict()}); no HEAPO 15-min "
                      f"season after 2022/23. Kaiser paired dwelling+HP: {ka['id'].nunique()} distinct ({ka.groupby('window')['id'].nunique().to_dict()}), "
                      f"{len(set('K:' + ka['id'].astype(str)) - bstar)} not in B*. Kaiser HP meters without dwelling meter: {kp['id'].nunique()} "
                      f"({kp.drop_duplicates('id')['otype'].value_counts().to_dict()}); the non-SFH ones serve whole buildings. "
                      f"WPuQ HP+household: {w['id'].nunique()} distinct ({w.groupby('window')['id'].nunique().to_dict()})"),
            "licence": "CC BY 4.0"}


def aggregates():
    fm = pd.read_csv(D / "FeederBW/feeder_metadata.csv")
    lct = pd.read_csv(D / "ukpn-low-carbon-technologies-secondary.csv", encoding="utf-8-sig")
    hpl = lct[lct["Type"].astype(str).str.contains("heat pump", case=False)]
    uk = pd.read_csv(D / "ukpn-smart-meter-consumption-lv-feeder.csv", usecols=["secondary_substation_id", "lv_feeder_id", "data_collection_log_timestamp"],
                     encoding="utf-8-sig")
    ts = pd.to_datetime(uk["data_collection_log_timestamp"], utc=True)
    return [{"dataset": "FeederBW (200 LV feeders, DE)", "unit": "feeder", "units_total": fm["feeder"].nunique(), "resolution": "15 min",
             "period": f"{fm['date'].min()[:7]} .. {fm['date'].max()[:7]} (metadata dates)",
             "capacity_label": f"registered heat_pumps_kW > 0 in {int((fm.groupby('feeder')['heat_pumps_kW'].max() > 0).sum())} feeders; "
                               f"storage/electric heaters also registered", "weather": "weather_data.parquet", "licence": "see FeederBW docs"},
            {"dataset": "UKPN LV feeder smart-meter aggregates + LCT register", "unit": "LV feeder / secondary substation",
             "units_total": int(uk.groupby(["secondary_substation_id", "lv_feeder_id"]).ngroups), "resolution": "30 min",
             "period": f"{ts.min():%Y-%m-%d} .. {ts.max():%Y-%m-%d}",
             "capacity_label": f"LCT register: {len(hpl)} heat-pump rows at {hpl['SecondarySubstationAlias'].nunique()} secondary substations "
                               f"(types {hpl['Type'].value_counts().to_dict()})", "licence": "UKPN open data"}]


def unknown_zips():
    out = []
    for f in ("dataset.zip", "pleiadata.zip"):
        n = zipfile.ZipFile(D / f).namelist()
        out.append({"dataset": f"{f} (zip index only)", "units_total": sum(x.endswith(".csv") and "smart_meter_data/" in x for x in n) or sum(x.endswith(".csv") for x in n),
                    "notes": ("Kaiser et al. Swiss smart meters archive (smart_meter_data/*.csv + tariff_data.csv); "
                              "same content as data/Swiss_dataset" if f == "dataset.zip" else
                              "PLEIAData (Data_Nature/processed_data: room, HVAC and consumption of a university building); not residential")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    out = ROOT / cfg["out_dir"]
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in (eoh, rhpp, lcl, neea, lambda: field("BPA HPHC (US PNW)", "bpa_hphc/*_hourly*.csv",
                                                   ["site_id", "local_datetime", "HP_system_pwr_kW", "backup_system_kW"], "backup_system_kW"),
               lambda: field("NREL CCASHP (US cold climate)", "nrel_ccashp/*HOUR*.csv",
                             ["site_id", "local_datetime", "HP_system_pwr_kW", "auxheat_pwr_kW"], "auxheat_pwr_kW"),
               cofactor, carleton, pecan, swiss_extra, fluvius, aggregates, unknown_zips):
        r = fn()
        rows += r if isinstance(r, list) else [r]
        print(f"done: {rows[-1]['dataset']}", flush=True)
    inv = pd.DataFrame(rows)
    inv.to_csv(out / "inventory.csv", index=False)
    cols = ["dataset", "unit", "units_total", "hp_submeter_units", "hp_submeter_units_>=1_season", "whole_house_units", "resolution", "period"]
    detail = "\n\n".join(f"### {r['dataset']}\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in r.items() if k != "dataset" and pd.notna(v) and v != "")
                         for r in rows)
    (out / "inventory.md").write_text(
        f"# Iteration 04 - dataset inventory\n\nSource: `scripts/audit/inventory_v2.py` (config `{cfg['exp_id']}`); EoH via "
        "`scripts/audit/eoh_convert.py`. Complete heating season = Nov-Mar with >= 90 % valid samples of the unit's key channel "
        "(EoH: whole-system electricity, 30-min bin valid with >= 12 of 15 two-minute diffs; RHPP: days with >= 80 % of 2-min slots; "
        "field studies: hourly HP_system_pwr_kW).\n\n## Summary\n\n" + md_table(inv[cols].fillna("")) + "\n\n## Details\n\n" + detail + "\n",
        encoding="utf-8")
    print(f"wrote {out / 'inventory.md'}")


if __name__ == "__main__":
    sys.exit(main())
