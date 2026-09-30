"""Iteration 04, Task 2 -- design envelopes of candidate pools under protocol v1's rules (counts only).

Reuses protocol v1 unchanged: `paperb.splits.household_splits` (75/25, HP stratified by station, fill
global) and `paperb.substations.plan_cells` (grid sizes x penetrations, max_overlap 0.75, >= 3 HP per
station). Per pool and split seed: HP households per station, feasible cells, max feeder size per
penetration, and test substations per Paper A penetration bin (actual p = n_hp / size).

Pools: B* (reference), GB-EoH (per complete season, hybrids excluded; station = group of homes with identical
outdoor-temperature series; fill = LCL), GB-RHPP (Nov 2013 - Feb 2014, concurrent with LCL; one region),
US-NEEA (cal2023, heating fully submetered; station = state; fill = NEEA homes without electric heating).
Also estimates the LCL fill temperature response s0 (kW/K per dwelling, HadCET) against B*'s 0.0055.

    python scripts/audit/envelope_v2.py --config configs/iter04_inventory.yaml
"""
import argparse
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
from inventory_v2 import CACHE, D, NEEA_HEAT, cached  # noqa: E402
from paperb.splits import household_splits  # noqa: E402
from paperb.substations import plan_cells  # noqa: E402
from pool_inventory import md_table  # noqa: E402

PBINS = [("<=15%", 0, .15), ("15-35%", .15, .35), ("35-65%", .35, .65), (">65%", .65, 9)]
LCL_W = {"2012/13": ("2012-11-01", "2013-04-01"), "Nov13-Feb14": ("2013-11-01", "2014-03-01"), "year12/13": ("2012-07-01", "2013-07-01")}


def lcl_scan():
    p = "UKDA-7857-csv/csv/data_collection/data_tables/"
    days = []
    with zipfile.ZipFile(D / "LCL_2013.zip") as Z:
        a = pd.read_csv(Z.open(p + "survey_answers.csv"), encoding="latin-1", low_memory=False)
        for f in ("consumption_n.csv", "consumption_d.csv"):
            x = pd.read_csv(Z.open(p + f), converters={"GMT": str})
            x.index = pd.to_datetime(x.pop("GMT"))
            x = x.loc["2012-07-01":"2014-02-28 23:59"].astype("float32")
            days.append((x.resample("D").mean() * 2.0).where(x.resample("D").count() >= 44))     # kWh/30 min -> kW
    L = pd.concat(days, axis=1)
    q = a.set_index(a["Household_id"].astype(str))
    q = q[~q.index.duplicated()]
    gas = q["Q248"].astype(str).str.contains("gas boiler", case=False) & q["Q248"].astype(str).str.contains("central heating", case=False)
    clean = gas & pd.to_numeric(q["Q304"], errors="coerce").eq(0)          # Paper A: Q304 = portable electric heaters
    L.columns = pd.MultiIndex.from_arrays([L.columns, L.columns.map(gas).fillna(False), L.columns.map(clean).fillna(False)],
                                          names=["hh", "gas", "clean"])
    return L.T.reset_index().astype({"gas": bool, "clean": bool}).rename(columns=str)


def lcl_fill():
    L = cached("lcl_daily", lcl_scan).set_index(["hh", "gas", "clean"]).T
    L.index = pd.to_datetime(L.index)
    cov = {w: L.loc[a:pd.Timestamp(b) - pd.Timedelta("1D")].notna().mean() >= 0.9 for w, (a, b) in LCL_W.items()}
    T = pd.read_csv(D / "hadcet/meantemp_daily_totals.txt", sep=r"\s+", skiprows=1, names=["date", "T"])
    T = pd.Series(pd.to_numeric(T["T"], errors="coerce").to_numpy(), index=pd.to_datetime(T["date"], format="%Y-%m-%d", errors="coerce")).dropna()
    s0 = {}
    for name, sel in (("all", True), ("gas, 0 heaters", L.columns.get_level_values("clean").to_numpy(bool))):
        y = L.loc["2012-07-01":"2013-06-30", cov["year12/13"].to_numpy() & sel]
        d = pd.DataFrame({"T": T, "y": y.mean(axis=1)}).dropna()
        b, s, th, r2 = fit_hockey_stick(d["T"].to_numpy(), d["y"].to_numpy(), (8, 20))
        s0[name] = {"n": y.shape[1], "P_base": round(b, 3), "s0 (kW/K)": round(s, 4), "T_h": round(th, 1), "r2": round(r2, 2)}
    return {w: int(c.sum()) for w, c in cov.items()}, pd.DataFrame(s0).T.reset_index().rename(columns={"index": "LCL fill"})


def eoh_stations(props, season):
    """Group EoH homes whose daily outdoor-temperature series agree within 0.2 C (shared weather station)."""
    a, b = f"20{season[2:4]}-11-01", f"20{season[5:7]}-04-01"
    T = []
    for f in sorted((D / "_paperb/pools_raw/eoh").glob("eoh_30min_set*.parquet")):
        x = pd.read_parquet(f, columns=["property", "ts", "T_ext"])
        x = x[x["property"].isin(props) & (x["ts"] >= a) & (x["ts"] < b)]
        T.append(x.groupby(["property", x["ts"].dt.floor("D")], observed=True)["T_ext"].mean().unstack(0))
    T = pd.concat(T, axis=1)
    lab, cur = {}, 0
    for p in T.columns:                                                  # greedy: join the first group within 0.2 C
        for q, g in lab.items():
            if (T[p] - T[q]).abs().median() < 0.2:
                lab[p] = g
                break
        else:
            lab[p], cur = cur, cur + 1
    return pd.Series(lab).map(lambda g: f"G{g:03d}")


def envelope(meta, seeds, grid):
    """Mean over split seeds of HP per station/split, feasible cells, max sizes and test substations per bin."""
    st_rows, bins, sizes = [], [], []
    for seed, sp in household_splits(meta, seeds).items():
        for part in ("train", "test"):
            hp = meta.loc[sp[part]["hp"]]
            by_st = {s: list(g.index) for s, g in hp.groupby("station")}
            cells, _ = plan_cells(by_st, len(sp[part]["fill"]), grid, {}, False)
            n = grid["substations_per_cell"][part]
            st_rows += [{"seed": seed, "split": part, "station": s, "H": len(v)} for s, v in by_st.items()]
            c = pd.DataFrame(cells)
            if part == "test":
                pen = c["n_hp"] / c["size"] if len(c) else pd.Series(dtype=float)
                bins.append({"seed": seed, **{b: int(((pen > lo) & (pen <= hi)).sum()) * n for b, lo, hi in PBINS}})
                H, F = max(len(v) for v in by_st.values()), len(sp[part]["fill"])
                sizes.append({"seed": seed, **{f"p={p}": int(c.loc[c["p"] == p, "size"].max()) if (len(c) and (c["p"] == p).any()) else 0
                                               for p in grid["penetration"]},
                              **{f"uncapped p={p}": int(min(np.floor(grid["max_overlap"] * H / p), np.floor(F / (1 - p)) if p < 1 else 1e9))
                                 for p in (0.05, 0.2, 0.5, 1.0)}})
    S = pd.DataFrame(st_rows).groupby(["split", "station"])["H"].mean().unstack(0).round(1).fillna(0)
    return S, pd.DataFrame(bins).drop(columns="seed").mean().round(1), pd.DataFrame(sizes).drop(columns="seed").median()


def pools(cfg):
    out = {}
    m = pd.read_parquet(D / "_paperb/pools/bstar_2023_meta.parquet")
    out["B* (cal2023, reference)"] = (m[["role", "station"]], "Kaiser clean dwellings (same years, KLO)")
    E = pd.read_parquet(CACHE / "eoh_units.parquet")
    n_lcl, s0 = lcl_fill()
    for season in ("2020/21", "2021/22", "2022/23"):
        ok = E[E["seasons_ws_str"].str.contains(season, regex=False) & E["peak15_ws_kW"].notna() & (E["type"] != "hybrid")]
        st = eoh_stations(set(ok["property"]), season)
        hp = pd.DataFrame({"role": "hp", "station": st.reindex(ok["property"]).fillna("G_none").to_numpy()}, index="E:" + ok["property"])
        fill = pd.DataFrame({"role": "fill", "station": "any"}, index=[f"L:{i}" for i in range(n_lcl["2012/13"])])
        out[f"GB-EoH {season}"] = (pd.concat([hp, fill]), f"LCL {n_lcl['2012/13']} households >= 90 % in 2012/13 (8-10 years earlier, London)")
    R = pd.read_parquet(D / "rhpp_daily.parquet")
    R = R[(R["day"] >= "2013-11-01") & (R["day"] < "2014-03-01")].groupby("site").size()
    R = R[R >= 0.9 * 120]
    hp = pd.DataFrame({"role": "hp", "station": "GB"}, index="R:" + R.index)
    fill = pd.DataFrame({"role": "fill", "station": "any"}, index=[f"L:{i}" for i in range(n_lcl["Nov13-Feb14"])])
    out["GB-RHPP Nov13-Feb14"] = (pd.concat([hp, fill]), f"LCL {n_lcl['Nov13-Feb14']} households >= 90 % in the same window (concurrent)")
    N = pd.read_parquet(CACHE / "neea_units.parquet")
    hp = N[N["full_submeter"]].set_index("ee_site_id")[["state"]].rename(columns={"state": "station"}).assign(role="hp")
    nf = neea_fill()
    fill = pd.DataFrame({"role": "fill", "station": "any"}, index=[f"N:{i}" for i in nf])
    out["US-NEEA cal2023"] = (pd.concat([hp.rename(index=lambda i: f"N:{i}"), fill]), f"NEEA homes without electric heating, >= 330 full days: {len(nf)}")
    return out, s0


def neea_fill():
    def scan():
        P = pd.read_csv(D / "POINTS v9.2.csv", low_memory=False)
        uses = P.groupby("ee_site_id")["circuit_label_type_desc"].agg(set)
        ok = uses[uses.apply(lambda s: "Mains" in s and not s & (set(NEEA_HEAT) | {"Mains With Solar", "Solar"}))].index
        p = pd.read_parquet(D / "neea_base_circuits_2023.parquet", columns=["ee_site_id", "End Use", "MIN_T_l"])
        p = p[p["ee_site_id"].isin(ok) & (p["End Use"] == "Mains")]
        n = p.groupby(["ee_site_id", p["MIN_T_l"].dt.floor("D")]).size()
        good = (n >= 90).groupby(level=0).sum()
        return pd.DataFrame({"ee_site_id": good.index, "full_days": good.to_numpy()})
    f = cached("neea_fill", scan)
    return list(f.loc[f["full_days"] >= 330, "ee_site_id"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    grid = yaml.safe_load(open(ROOT / "configs/protocol_v1.yaml"))["grid"]
    seeds = [cfg["seeds"]["split"] + i for i in range(cfg["seeds"]["n_split_seeds"])]
    P, s0 = pools(cfg)
    parts, comp = [], []
    for name, (meta, fill_note) in P.items():
        S, B, Z = envelope(meta, seeds, grid)
        hpn = meta[meta["role"] == "hp"]
        comp.append({"pool": name, "HP households": len(hpn), "stations": hpn["station"].nunique(),
                     "stations >= 30 HP": int((hpn["station"].value_counts() >= 30).sum()),
                     **{f"{k} HP (used)": round(S[k][S[k] >= grid["min_station_pool"]].sum(), 1) if k in S else 0 for k in ("train", "test")},
                     "fill": int((meta["role"] == "fill").sum()),
                     **{f"test subs {k}": v for k, v in B.items()}, "test subs total": round(B.sum(), 1)})
        parts.append(f"### {name}\n\nFill: {fill_note}.\n\nHP households per station (mean over {len(seeds)} split seeds; stations with "
                     f"< {grid['min_station_pool']} HP in a split build no substation):\n\n{md_table(S.reset_index())}\n\n"
                     f"Test substations per Paper A penetration bin (mean per seed): {B.to_dict()}\n\n"
                     f"Max feeder size in the grid (<= {max(grid['size'])}) and uncapped (best test station; median over seeds):\n\n"
                     f"{md_table(Z.to_frame('size').T)}")
    txt = (f"## Design envelopes (protocol v1 rules)\n\nSource: `scripts/audit/envelope_v2.py` (config `{cfg['exp_id']}`); "
           f"grid sizes {grid['size']}, p {grid['penetration']}, max_overlap {grid['max_overlap']}, >= {grid['min_station_pool']} HP per "
           f"station and split, {grid['substations_per_cell']} substations per cell; split seeds {seeds[0]}..{seeds[-1]}.\n\n"
           + md_table(pd.DataFrame(comp)) + "\n\n" + "\n\n".join(parts)
           + "\n\n## Fill temperature response (LCL, HadCET daily, Jul 2012 - Jun 2013)\n\nB* Kaiser fill: s0 = 0.0055 kW/K per dwelling.\n\n"
           + md_table(s0))
    out = ROOT / cfg["out_dir"]
    (out / "envelopes.md").write_text(txt + "\n", encoding="utf-8")
    print(f"wrote {out / 'envelopes.md'}")


if __name__ == "__main__":
    sys.exit(main())
