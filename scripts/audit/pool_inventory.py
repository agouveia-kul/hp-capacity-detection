"""Iteration 01, Task 1 -- household pool inventory (counts only; no load series built).

Stage 1 (scan, cached in data/_paperb/iter01/): for every household / meter and every
window, the number of valid readings per channel. Stage 2 (report): distinct households
meeting each requirement with >= 90 % coverage, per station and window.

Windows: heating seasons Nov-Mar (label "2019/20" = 2019-11-01 .. 2020-03-31, UTC) and
calendar years (label "cal2023"), because the legacy pool is calendar 2023.

    python scripts/audit/pool_inventory.py --config configs/iter01_quick.yaml
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
HEAPO = DATA / "heapo_data"
KAISER = DATA / "Swiss_dataset"
COVERAGE = 0.90
DWELLING_TYPES = ("Apartment", "Single-family house")
TCL_FLAGS = ("1_hp", "1_hp-add", "1_hp-wh", "1_ewh", "1_storage_heating", "1_direct_heating")
SRC = "scripts/audit/pool_inventory.py"


def windows():
    """label -> (start, end) as naive-UTC datetime64, end exclusive."""
    w = {f"{y}/{(y + 1) % 100:02d}": (f"{y}-11-01", f"{y + 1}-04-01") for y in range(2019, 2025)}
    w.update({f"cal{y}": (f"{y}-01-01", f"{y + 1}-01-01") for y in range(2019, 2025)})
    return {k: (np.datetime64(a), np.datetime64(b)) for k, (a, b) in w.items()}


def _utc(s):
    s = s.astype(str)
    assert s.str.endswith("+00:00").all(), "non-UTC timestamp"
    return pd.to_datetime(s.str.slice(0, 19), format="%Y-%m-%d %H:%M:%S").to_numpy()


def count_windows(ts, masks, step):
    """Valid readings per window and channel; ts may be unsorted / duplicated."""
    ts, first = np.unique(ts, return_index=True)
    out = []
    for w, (a, b) in windows().items():
        i0, i1 = np.searchsorted(ts, a), np.searchsorted(ts, b)
        n_exp = int((b - a) / step)
        out.append({"window": w, "n_expected": n_exp,
                    **{ch: int(m[first][i0:i1].sum()) for ch, m in masks.items()}})
    return out


# ------------------------------------------------------------------- scans --
def scan_heapo(res, limit=None):
    folder = HEAPO / "smart_meter_data" / res
    step = np.timedelta64(15, "m") if res == "15min" else np.timedelta64(1, "D")
    rows = []
    for f in sorted(os.listdir(folder))[:limit]:
        d = pd.read_csv(folder / f, sep=";", usecols=["Timestamp", "kWh_received_Total",
                                                      "kWh_received_HeatPump", "kWh_received_Other"])
        tot = d["kWh_received_Total"].notna().to_numpy()
        hp = tot & d["kWh_received_HeatPump"].notna().to_numpy()
        masks = {"total": tot, "hp": hp, "hp_other": hp & d["kWh_received_Other"].notna().to_numpy()}
        for r in count_windows(_utc(d["Timestamp"]), masks, step):
            rows.append({"id": int(f[:-4]), **r})
    return pd.DataFrame(rows)


def scan_kaiser(limit=None):
    folder = KAISER / "smart_meter_data"
    rows = []
    for f in sorted(os.listdir(folder))[:limit]:
        d = pd.read_csv(folder / f, sep=";", usecols=["timestamp_utc", "kWh_to_installation"])
        masks = {"total": d["kWh_to_installation"].notna().to_numpy()}
        for r in count_windows(_utc(d["timestamp_utc"]), masks, np.timedelta64(15, "m")):
            rows.append({"id": int(f[:-4]), **r})
    return pd.DataFrame(rows)


def scan_wpuq():
    import h5py
    parts = {}
    for year in (2019, 2020):
        with h5py.File(DATA / f"{year}_data_15min.hdf5", "r") as h:
            for grp in ("NO_PV", "WITH_PV"):
                for name, node in h[grp].items():
                    if "HEATPUMP" not in node or "HOUSEHOLD" not in node:
                        continue
                    s = [pd.Series(node[k]["table"]["P_TOT"],
                                   index=pd.to_datetime(node[k]["table"]["index"], unit="s"))
                         for k in ("HEATPUMP", "HOUSEHOLD")]
                    s = [x[~x.index.duplicated()] for x in s]
                    both = pd.concat(s, axis=1).notna().all(axis=1)
                    parts.setdefault(name, []).append(both)
    rows = []
    for name, lst in parts.items():
        m = pd.concat(lst)
        for r in count_windows(m.index.to_numpy(), {"hp_other": m.to_numpy()}, np.timedelta64(15, "m")):
            rows.append({"id": name, **r})
    return pd.DataFrame(rows)


def load_scans(cache, limit=None):
    cache.mkdir(parents=True, exist_ok=True)
    scans = {"heapo15": lambda: scan_heapo("15min", limit), "heapo_daily": lambda: scan_heapo("daily", limit),
             "kaiser": lambda: scan_kaiser(limit), "wpuq": scan_wpuq}
    out = {}
    for name, fn in scans.items():
        p = cache / f"coverage_{name}.parquet"
        if not p.exists():
            print(f"scanning {name} ...", flush=True)
            fn().to_parquet(p)
        out[name] = pd.read_parquet(p)
    return out


def covered(scan, channel):
    """Long frame (id, window) of households meeting the channel at >= COVERAGE."""
    ok = scan[scan[channel] >= COVERAGE * scan["n_expected"]]
    return ok[["id", "window"]]


# ------------------------------------------------------------------ report --
def kaiser_meta():
    m = pd.read_csv(KAISER / "metadata.csv", sep=";", encoding="utf-8-sig")
    for c in TCL_FLAGS + ("2_hp_control", "2_wh_control"):
        m[c] = m[c].astype(str).eq("True")
    return m


def kaiser_units(m):
    """Requirement -> DataFrame(id=dwelling or HP meter, hp_meter, dwelling)."""
    dw = m[m["0_installation_type"].isin(DWELLING_TYPES)]
    hp = m[m["0_installation_type"] == "Heat pump"]
    pair = hp.dropna(subset=["0_object_id"]).merge(dw.dropna(subset=["0_object_id"]), on="0_object_id", suffixes=("_hp", "_dw"))
    units = {
        "K(a) dwelling + paired HP meter": pd.DataFrame({"id": pair["0_meter_id_dw"], "hp_meter": pair["0_meter_id_hp"]}),
        "K(a') HP meter, no dwelling meter": pd.DataFrame({"id": hp.loc[~hp["0_meter_id"].isin(pair["0_meter_id_hp"]), "0_meter_id"]}),
        "K(a'') dwelling with 1_hp inside its meter": pd.DataFrame({"id": dw.loc[dw["1_hp"] & ~dw["0_meter_id"].isin(pair["0_meter_id_dw"]), "0_meter_id"]}),
        "K(b) clean dwelling (no TCL flag)": pd.DataFrame({"id": dw.loc[~dw[list(TCL_FLAGS)].any(axis=1)  # paired dwellings
                                                                    & ~dw["0_meter_id"].isin(pair["0_meter_id_dw"]), "0_meter_id"]}),
    }
    for f in TCL_FLAGS[1:]:
        units[f"K(c) dwelling flag {f}"] = pd.DataFrame({"id": dw.loc[dw[f], "0_meter_id"]})
    for f in ("2_hp_control", "2_wh_control"):
        units[f"K(d) any meter {f}"] = pd.DataFrame({"id": m.loc[m[f], "0_meter_id"]})
    return units


def inventory(scans):
    hh = pd.read_csv(HEAPO / "meta_data" / "households.csv", sep=";").set_index("Household_ID")["Weather_ID"]
    rows = []

    def add(source, req, ok):
        ok = ok.assign(station=ok["station"].astype(str))
        for (st, w), g in ok.groupby(["station", "window"]):
            rows.append({"source": source, "requirement": req, "station": st, "window": w,
                         "n_households": g["id"].nunique()})

    for src, key, reqs in (("HEAPO 15-min", "heapo15", {"H15(a) HP submeter + other": "hp_other", "H15(b) total": "total"}),
                           ("HEAPO daily", "heapo_daily", {"Hd(a) HP submeter daily": "hp", "Hd(b) total daily": "total"})):
        for req, ch in reqs.items():
            ok = covered(scans[key], ch)
            add(src, req, ok.assign(station=ok["id"].map(hh)))
    ok_hp, ok_tot = covered(scans["heapo15"], "hp_other"), covered(scans["heapo15"], "total")
    only = ok_tot.merge(ok_hp, how="left", indicator=True).query("_merge == 'left_only'").drop(columns="_merge")
    add("HEAPO 15-min", "H15(b') total, no HP submeter", only.assign(station=only["id"].map(hh)))

    km = kaiser_meta()
    ok_k = covered(scans["kaiser"], "total")
    for req, u in kaiser_units(km).items():
        ok = u.merge(ok_k, on="id")
        if "hp_meter" in u:
            ok = ok.merge(ok_k.rename(columns={"id": "hp_meter"}), on=["hp_meter", "window"])
        add("Kaiser", req, ok.assign(station="KLO"))
    ok = covered(scans["wpuq"], "hp_other")
    add("WPuQ", "W HP + household", ok.assign(station="WPUQ"))
    return pd.DataFrame(rows)


def nameplate(scans):
    """HEAPO households with a nameplate x data availability, per window."""
    p = pd.read_csv(HEAPO / "reports" / "protocols.csv", sep=";", low_memory=False)
    col = {"Normpoint_ElectricPower": "HeatPump_Installation_Normpoint_ElectricPower",
           "HeatingCapacity": "HeatPump_Installation_HeatingCapacity"}
    rows = []
    for name, c in col.items():
        ids = set(p.loc[p[c].notna(), "Household_ID"].dropna().astype(int))
        for data, (key, ch) in {"15-min HP submeter": ("heapo15", "hp_other"), "15-min total": ("heapo15", "total"),
                                "daily HP submeter": ("heapo_daily", "hp"), "daily total": ("heapo_daily", "total")}.items():
            ok = covered(scans[key], ch)
            ok = ok[ok["id"].isin(ids)]
            for w, g in ok.groupby("window"):
                rows.append({"nameplate": name, "data": data, "window": w, "n_households": g["id"].nunique()})
        rows.append({"nameplate": name, "data": "any (protocol only)", "window": "any", "n_households": len(ids)})
    return pd.DataFrame(rows)


def station_compat():
    """HEAPO hourly station temperature vs MeteoSwiss KLO (Kaiser weather file)."""
    w = pd.read_csv(KAISER / "weather_2020-2029.csv", sep=";", low_memory=False, usecols=["reference_timestamp", "tre200h0"])
    klo = pd.Series(pd.to_numeric(w["tre200h0"], errors="coerce").to_numpy(),
                    index=pd.to_datetime(w["reference_timestamp"], format="%d.%m.%Y %H:%M")).dropna()
    rows = []
    for f in sorted(os.listdir(HEAPO / "weather_data" / "hourly")):
        h = pd.read_csv(HEAPO / "weather_data" / "hourly" / f, sep=";", usecols=["Timestamp", "Temperature_avg_hourly"])
        s = pd.Series(h["Temperature_avg_hourly"].to_numpy(), index=_utc(h["Timestamp"])).dropna()
        j = pd.concat([s, klo], axis=1, join="inner").dropna()
        d = (j.iloc[:, 0] - j.iloc[:, 1]).abs()
        rows.append({"station": f[:-4], "n_hours_overlap": len(j), "max_abs_diff_C": round(float(d.max()), 3),
                     "share_identical": round(float((d < 0.05).mean()), 4), "identical_to_KLO": bool(len(j) and d.max() < 0.05)})
    return pd.DataFrame(rows)


def multi_season(scans):
    rows = []
    for src, key, ch in (("HEAPO 15-min HP submeter + other", "heapo15", "hp_other"), ("HEAPO daily HP submeter", "heapo_daily", "hp"),
                         ("HEAPO daily total", "heapo_daily", "total"), ("Kaiser meter (any)", "kaiser", "total"),
                         ("WPuQ HP + household", "wpuq", "hp_other")):
        ok = covered(scans[key], ch)
        for kind, pat in (("heating seasons", "/"), ("calendar years", "cal")):
            n = ok[ok["window"].str.contains(pat)].groupby("id").size()
            rows.append({"source": src, "window kind": kind, **{f">={k}": int((n >= k).sum()) for k in (1, 2, 3, 4)}})
    return pd.DataFrame(rows)


def md_table(df):
    df = df.astype(str)
    return "\n".join(["| " + " | ".join(df.columns) + " |", "|" + "---|" * df.shape[1]]
                     + ["| " + " | ".join(r) + " |" for r in df.to_numpy()])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    out = ROOT / cfg["out_dir"]
    out.mkdir(parents=True, exist_ok=True)
    scans = load_scans(ROOT / cfg["cache_dir"], cfg.get("scan_limit"))
    inv = inventory(scans)
    inv.to_csv(out / "pool_inventory.csv", index=False)
    wins = list(windows())
    tot = inv.groupby(["source", "requirement", "window"])["n_households"].sum().unstack().reindex(columns=wins).fillna(0).astype(int)
    by_st = inv.pivot_table(index=["source", "requirement", "station"], columns="window", values="n_households",
                            aggfunc="sum").reindex(columns=wins).fillna(0).astype(int)
    npl = nameplate(scans).pivot_table(index=["nameplate", "data"], columns="window", values="n_households", aggfunc="sum").reindex(columns=wins + ["any"]).fillna(0).astype(int)
    parts = [f"# Iteration 01 - pool inventory\n\nSource: `{SRC}` (config `{cfg['exp_id']}`). Distinct households with "
             f">= {COVERAGE:.0%} coverage of the required channel(s) in each window. Seasons are Nov-Mar (UTC); "
             "`calYYYY` are calendar years (the legacy pool is cal2023 with an 80 % rule).",
             "## Totals over stations\n\n" + md_table(tot.reset_index()),
             "## Per weather station\n\n" + md_table(by_st.reset_index()),
             "## Nameplate x data availability (HEAPO protocols)\n\n" + md_table(npl.reset_index()),
             "## Station compatibility (HEAPO hourly vs MeteoSwiss KLO, identical = max |diff| < 0.05 C)\n\n" + md_table(station_compat()),
             "## Multi-window households (count of households usable in >= k windows)\n\n" + md_table(multi_season(scans))]
    (out / "pool_inventory.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {out / 'pool_inventory.md'}")


if __name__ == "__main__":
    sys.exit(main())
