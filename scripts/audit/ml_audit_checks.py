"""Iteration 01, Task 3 -- numbers behind the ML-pipeline audit (read-only; fixes nothing).

One pass over the legacy substation pickle is cached as scalars in
data/_paperb/iter01/legacy_sub_scalars.parquet (peak, targets, hockey-stick fits).
Writes results/<exp>/ml_audit_checks.md, which ml_audit.md cites.

    python scripts/audit/ml_audit_checks.py --config configs/iter01_full.yaml
"""
import argparse
import json
import pickle
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import hp_capacity as hc  # noqa: E402
from hp_common import (T_BALANCE_BOUNDS, daily_mean_mean_heating_season,  # noqa: E402
                       daily_min_max_heating_season, fit_hockey_stick)
from pool_inventory import md_table  # noqa: E402

DATA = ROOT / "data"
REDUCE = {"min/max": daily_min_max_heating_season, "mean/mean": daily_mean_mean_heating_season}
BINS = ("warm", "mild", "cold", "extreme")


def hockey(load, temp, thresh):
    """Legacy hs_features: (T_balance, max x, n days) or NaN; mirrors hockey_variants_compare.py:29."""
    out = {}
    for name, fn in REDUCE.items():
        x, y = fn(temp, load, heating_season_thresh=thresh)
        try:
            tb = fit_hockey_stick(x, y)[2] if len(x) >= 20 else np.nan
        except Exception:
            tb = np.nan
        out[name] = (tb, float(np.max(x)) if len(x) else np.nan, len(x))
    return out


def scalars(frame, thresh, extra):
    rows = []
    for i in frame.index:
        load, temp = frame.at[i, "Total_Load"], frame.at[i, "Temperature"]
        r = {"id": i, "peak": hc.series_peak(load), "HP_Peak": float(frame.at[i, "HP_Peak"])}
        r.update({c: frame.at[i, c] for c in extra})
        for name, (tb, xmax, n) in hockey(load, temp, thresh).items():
            r.update({f"tbal {name}": tb, f"xmax {name}": xmax, f"ndays {name}": n})
        rows.append(r)
    return pd.DataFrame(rows)


def load_scalars(cache):
    p = cache / "legacy_sub_scalars.parquet"
    if not p.exists():
        warnings.filterwarnings("ignore")
        sub = pickle.load(open(DATA / "substations_data_pooled.pkl", "rb"))
        a = scalars(sub, 12.0, ["split", "size", "HP_ratio", "weather_id"]).assign(dataset="HEAPO legacy")
        temps = {w: sub.loc[sub["weather_id"] == w, "Temperature"].iloc[0] for w in sub["weather_id"].unique()}
        del sub
        wpool = pickle.load(open(DATA / "_wpuq_pool_cache.pkl", "rb"))
        wp = hc.build_wpuq_substations(wpool, n=400, size_range=(10, 37), pen_max=0.5, seed=7)
        b = scalars(wp, 15.0, ["size"]).assign(dataset="WPuQ synthetic", split="transfer")
        pd.concat([a, b]).to_parquet(p)
        pd.DataFrame(temps).to_parquet(cache / "heapo_station_temps_2023.parquet")
        pd.DataFrame({"WPUQ": wpool["temperature"]["WPUQ"]}, index=wpool["index"]).to_parquet(cache / "wpuq_temp_2019.parquet")
    return pd.read_parquet(p)


# ------------------------------------------------------------------ checks --
def check_scale_peak(s):
    rows = []
    for ds, g in s.groupby(["dataset", "split"]):
        r = np.corrcoef(g["peak"], g["HP_Peak"])[0, 1]
        rows.append({"set": " ".join(ds), "n": len(g), "corr(Scale_peak, HP_Peak)": round(r, 3),
                     "corr(size, HP_Peak)": round(np.corrcoef(g["size"], g["HP_Peak"])[0, 1], 3),
                     "median HP_Peak / Scale_peak": round((g["HP_Peak"] / g["peak"]).median(), 3)})
    tr, te = s[s["split"] == "train"], s[s["split"] == "test"]
    coef = np.polyfit(tr["peak"], tr["HP_Peak"], 1)
    pred = np.polyval(coef, te["peak"])
    r2 = 1 - np.sum((te["HP_Peak"] - pred) ** 2) / np.sum((te["HP_Peak"] - te["HP_Peak"].mean()) ** 2)
    by_pen = te.groupby("HP_ratio")[["peak", "HP_Peak"]].apply(lambda g: np.corrcoef(g["peak"], g["HP_Peak"])[0, 1]).round(3)
    return rows, r2, by_pen


def check_nans(s):
    """Same matrix as benchmark_capacity_models.load_data (legacy/benchmark_capacity_models.py:53-60)."""
    sub = pd.read_parquet(DATA / "_paperb" / "iter00" / "legacy_substation_members.parquet")
    h = s[s["dataset"] == "HEAPO legacy"].set_index("id")
    Xraw = pickle.load(open(DATA / "_X_swiss_pooled.pkl", "rb"))
    sel = json.load(open(ROOT / "models" / "xgb_selected_features.json"))["selected_features"]
    sf = hc.select_scale_free_columns(Xraw)
    X = hc.capacity_feature_matrix(Xraw, sf, size=sub["size"], peak=h["peak"].reindex(sub.index))
    sf = list(X.columns)
    Xw, _ = pickle.load(open(DATA / "_X_wpuq_bench.pkl", "rb"))
    Xr, _ = pickle.load(open(DATA / "_X_wpuq_real.pkl", "rb"))
    sets = {"HEAPO train": X[sub["split"].to_numpy() == "train"], "HEAPO test": X[sub["split"].to_numpy() == "test"],
            "WPuQ synthetic": Xw, "WPuQ real feeder": Xr}
    rows = []
    for name, D in sets.items():
        for cols_name, cols in ((f"all {len(sf)} (scale-free + 2 anchors)", sf), (f"{len(sel)} selected", [c for c in sel if c in D.columns])):
            V = D.reindex(columns=cols)
            rows.append({"set": name, "features": cols_name, "rows": len(V), "NaN cells %": round(100 * V.isna().to_numpy().mean(), 2),
                         "rows with any NaN": int(V.isna().any(axis=1).sum()), "cols with any NaN": int(V.isna().any().sum()),
                         "|value| > 1e3 cells": int((V.abs() > 1e3).sum().sum())})
    return rows


def hdd_bins(temp, t_base, mild=10.0, cold=25.0):
    """Weekday counts per bin, as in extract_windowed_hdd_features_from_series (hp_capacity.py:187-212)."""
    t = temp.resample("15min").mean().ffill()
    t = t[t.index.weekday < 5]
    sev = (np.maximum(t_base - t, 0) * 0.25).groupby(t.index.date).sum()
    lab = np.select([sev <= 0, sev <= mild, sev <= cold], ["warm", "mild", "cold"], "extreme")
    return pd.Series(lab).value_counts().reindex(BINS, fill_value=0)


def check_hdd(cache):
    h = pd.read_parquet(cache / "heapo_station_temps_2023.parquet")
    w = pd.read_parquet(cache / "wpuq_temp_2019.parquet")["WPUQ"]
    fbw = pd.read_parquet(DATA / "FeederBW" / "weather_data.parquet")
    fbw["timestamp_UTC"] = pd.to_datetime(fbw["timestamp_UTC"], utc=True)
    f24 = fbw[fbw["timestamp_UTC"].dt.year == 2024]
    series = {f"HEAPO {c} 2023": h[c] for c in h.columns} | {"WPuQ 2019": w}
    series["FeederBW 2024 (feeder-mean T)"] = f24.groupby("timestamp_UTC")["air_temperature_C"].mean()
    rows = []
    for name, s in series.items():
        for tb in (12.0, 15.0):
            rows.append({"dataset": name, "T_base": tb, **hdd_bins(s, tb).to_dict()})
    return rows


def check_hockey(s):
    rows = []
    lo, hi = T_BALANCE_BOUNDS
    for ds, g in s.groupby("dataset"):
        for red in REDUCE:
            tb, xm = g[f"tbal {red}"], g[f"xmax {red}"]
            ok = tb.notna()
            rows.append({"set": ds, "reduction": red, "fits": int(ok.sum()), "failed / <20 days": int((~ok).sum()),
                         f"at lower bound {lo}": int((tb[ok] <= lo + 0.01).sum()), f"at upper bound {hi}": int((tb[ok] >= hi - 0.01).sum()),
                         "T_bal > max observed T (hinge outside data)": int((tb[ok] > xm[ok]).sum()),
                         "median T_bal": round(float(tb.median()), 2), "median max T": round(float(xm.median()), 2)})
    return rows


def check_feederbw():
    m = pd.read_csv(DATA / "FeederBW" / "feeder_metadata.csv")
    m["date"] = pd.to_datetime(m["date"])
    cols = [c for c in hc._FBW_HEAT_COLS if c in m.columns]
    m["eh"] = m[cols].fillna(0).sum(axis=1)
    y = m[(m.date >= "2024-01-01") & (m.date < "2025-01-01")].sort_values("date")
    start, end = y.drop_duplicates("feeder", keep="first").set_index("feeder"), y.drop_duplicates("feeder", keep="last").set_index("feeder")
    static = start.combine_first(m.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder"))
    frame = hc.feederbw_capacity_frame(static.index, static, end)
    return {"feeders in metadata": m.feeder.nunique(), "metadata date range": f"{m.date.min():%Y-%m-%d} .. {m.date.max():%Y-%m-%d}",
            "feeders with a 2024 metadata row": y.feeder.nunique(),
            "feeders whose target falls back to a non-2024 row": int((~static.index.isin(y.feeder)).sum()),
            "feeders flagged elecheat_stable = False (start vs end 2024)": int((~frame["elecheat_stable"]).sum()),
            "  of which only because no 2024 row (end missing)": int((~frame["elecheat_stable"] & ~frame.index.isin(y.feeder)).sum()),
            "feeders whose electric-heating kW changes over the full period": int((m.groupby("feeder")["eh"].nunique() > 1).sum()),
            "feeders whose HP kW changes over the full period": int((m.groupby("feeder")["heat_pumps_kW"].nunique() > 1).sum())}


def check_hp_member_flags():
    """TCL / control flags carried by HP members (own non-HP load and HP meter)."""
    from pool_inventory import kaiser_meta, kaiser_units
    km = kaiser_meta().set_index("0_meter_id")
    pair = kaiser_units(km.reset_index())["K(a) dwelling + paired HP meter"]
    dw, hpm = km.reindex(pair["id"]), km.reindex(pair["hp_meter"])
    rows = [{"pool": "Kaiser paired (dwelling meter)", "n": len(pair), **{f: int(dw[f].sum()) for f in ("1_ewh", "1_hp-add", "2_hp_control", "2_wh_control")}},
            {"pool": "Kaiser paired (HP meter)", "n": len(pair), **{f: int(hpm[f].sum()) for f in ("1_ewh", "1_hp-add", "2_hp_control", "2_wh_control")}}]
    meta = pd.read_csv(DATA / "heapo_data/meta_data/meta_data.csv", sep=";").set_index("Household_ID")
    legacy = pd.read_parquet(DATA / "_paperb/iter00/legacy_prep_datarange.parquet").index
    ewh = meta.reindex(legacy)["Survey_DHW_Production_ByElectricWaterHeater"].astype(str)
    rows.append({"pool": "HEAPO legacy 57 (survey: DHW by electric water heater)", "n": len(legacy),
                 "1_ewh": f"{int(ewh.eq('True').sum())} (unknown {int(ewh.isin(['nan', 'None']).sum())})"})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    out, cache = ROOT / cfg["out_dir"], ROOT / cfg["cache_dir"]
    out.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    s = load_scalars(cache)
    sp_rows, r2, by_pen = check_scale_peak(s)
    zeros = s.groupby(["dataset", "split"])["HP_Peak"].apply(lambda v: f"{int((v == 0).sum())} of {len(v)}")
    wcov = pd.read_parquet(cache / "coverage_wpuq.parquet").query("window == 'cal2019'")
    parts = [f"# Iteration 01 - ML audit checks\n\nSource: `scripts/audit/ml_audit_checks.py` (config `{cfg['exp_id']}`); "
             "legacy caches in `data/` (read-only). Protocol = legacy.",
             "## M1 Scale_peak vs HP_Peak\n\n" + md_table(pd.DataFrame(sp_rows))
             + f"\n\nLinear map HP_Peak ~ Scale_peak fitted on train, scored on test: **R2 = {r2:.3f}**."
             + "\n\nTest corr(Scale_peak, HP_Peak) within each penetration level:\n\n" + md_table(by_pen.rename("corr").reset_index()),
             "## M3 NaN / extreme values in the capacity feature matrix\n\n" + md_table(pd.DataFrame(check_nans(s))),
             "## M4 HDD-bin weekday counts (thresholds 10 / 25 degree-hours per day)\n\n" + md_table(pd.DataFrame(check_hdd(cache))),
             "## M5 Hockey-stick fits (legacy settings: heating_season_thresh = T_base 12 CH / 15 DE, >= 20 days)\n\n" + md_table(pd.DataFrame(check_hockey(s))),
             "## M6 Zero targets (MAPE excludes them)\n\n" + md_table(zeros.rename("HP_Peak == 0").reset_index()),
             "## M7 FeederBW metadata\n\n" + md_table(pd.DataFrame(check_feederbw().items(), columns=["quantity", "value"])),
             "## M9 Flags on HP members (their own non-HP load enters Total_Load)\n\n" + md_table(pd.DataFrame(check_hp_member_flags()).fillna("-")),
             "## M8 WPuQ raw coverage (HP and household both non-NaN, cal2019)\n\n"
             f"houses with >= 90 %: {int((wcov['hp_other'] >= 0.9 * wcov['n_expected']).sum())} of {len(wcov)}; "
             f"min coverage {100 * (wcov['hp_other'] / wcov['n_expected']).min():.1f} %. The legacy pool keeps 37."]
    (out / "ml_audit_checks.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {out / 'ml_audit_checks.md'}")


if __name__ == "__main__":
    sys.exit(main())
