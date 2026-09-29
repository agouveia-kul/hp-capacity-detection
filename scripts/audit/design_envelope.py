"""Iteration 01, Task 2 -- feasible substation design envelope (counts and memberships only).

Constraints for every option: household-disjoint 75/25 train/test split stratified by
station (fill split globally); no household twice in a substation (HP or fill); all HP
members of a substation share one station and one window. HEAPO 8jB is relabelled KLO
(identical station, see pool_inventory.md). Fill may come from any station (legacy rule).

    python scripts/audit/design_envelope.py --config configs/iter01_full.yaml
"""
import argparse
import sys
from math import comb, log10
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pool_inventory import (HEAPO, ROOT, covered, kaiser_meta, kaiser_units,  # noqa: E402
                            load_scans, md_table)

TEST_FRAC = 0.25
PENS = (0.1, 0.2, 0.3, 0.5, 0.7, 1.0)
CELLS = [(s, p) for s in (20, 50, 100) for p in (0.1, 0.3, 0.5, 1.0)]
TARGETS = ("HP_Peak", "HP_CoincPeak", "HP_Count", "HP_Nameplate_el", "s_h", "r", "P_design")


def heapo_rows(ok, role):
    st = pd.read_csv(HEAPO / "meta_data" / "households.csv", sep=";").set_index("Household_ID")["Weather_ID"]
    return pd.DataFrame({"hh": "H:" + ok["id"].astype(str), "station": ok["id"].map(st).replace("8jB", "KLO"),
                         "window": ok["window"], "role": role})


def kaiser_rows(units, ok_k, role):
    ok = units.merge(ok_k, on="id")
    if "hp_meter" in units:
        ok = ok.merge(ok_k.rename(columns={"id": "hp_meter"}), on=["hp_meter", "window"])
    return pd.DataFrame({"hh": "K:" + ok["id"].astype(str), "station": "KLO", "window": ok["window"], "role": role})


def option_pools(scans):
    """Option -> (membership frame [hh, station, window, role], spec)."""
    km = kaiser_meta()
    ku, ok_k = kaiser_units(km), covered(scans["kaiser"], "total")
    K = {k.split()[0]: v for k, v in ku.items()}          # "K(a)", "K(a')", "K(a'')", "K(b)"
    h15, hd_tot = covered(scans["heapo15"], "hp_other"), covered(scans["heapo_daily"], "total")
    # daily HP series: daily files OR 15-min HP aggregated to daily (daily files of submetered households stop ~2023-09)
    hd_hp = pd.concat([covered(scans["heapo_daily"], "hp"), covered(scans["heapo15"], "hp")]).drop_duplicates()
    legacy = pd.read_parquet(ROOT / "data/_paperb/iter00/legacy_prep_datarange.parquet").reset_index()
    A = pd.DataFrame({"hh": "H:" + legacy["Household_ID"].astype(str), "station": legacy["Weather_ID"],
                      "window": "cal2023", "role": "hp"})

    def B_like(wins):
        hp = pd.concat([heapo_rows(h15, "hp").query("station == 'KLO'"), kaiser_rows(K["K(a)"], ok_k, "hp")])
        return pd.concat([hp, kaiser_rows(K["K(b)"], ok_k, "fill")]).query("window in @wins")

    sfh = km.loc[km["0_object_type"] == "Single-family house", "0_meter_id"]
    Bplus = pd.concat([B_like(["cal2023"]), kaiser_rows(K["K(a')"][K["K(a')"]["id"].isin(sfh)], ok_k, "hp")
                       .query("window == 'cal2023'")])
    Bstar = pd.concat([Bplus, heapo_rows(h15, "hp").query("station != 'KLO' and window == 'cal2023'")])
    only_tot = hd_tot.merge(hd_hp, how="left", indicator=True).query("_merge == 'left_only'").drop(columns="_merge")
    D = pd.concat([heapo_rows(hd_hp, "hp"), kaiser_rows(K["K(a)"], ok_k, "hp"),
                   heapo_rows(only_tot, "hp_countonly"), kaiser_rows(K["K(a'')"], ok_k, "hp_countonly"),
                   kaiser_rows(K["K(b)"], ok_k, "fill")]).query("window in ['2023/24', 'cal2023']")
    return {"A": (A, "HEAPO 2023 legacy pool (57); fill = other HP households' Other channel; 15-min"),
            "B": (B_like(["cal2023"]), "HEAPO 8jB/KLO + Kaiser paired, cal2023; fill = Kaiser clean cal2023; 15-min"),
            "B+": (Bplus, "B + Kaiser single-family HP meters without a dwelling meter (their own non-HP load is not observed); 15-min"),
            "B*": (Bstar, "B+ plus HEAPO 15-min HP households at the other stations (fill = Kaiser clean, any station); cal2023; 15-min"),
            "C": (B_like(["cal2023", "cal2024"]), "B + cal2024 household-years (split by household); fill = Kaiser clean same year; 15-min"),
            "D": (D, "HEAPO all stations daily HP (daily file or 15-min aggregated) + Kaiser paired (hp); HEAPO total-only daily + Kaiser 1_hp-in-meter "
                     "(hp_countonly); fill = Kaiser clean; daily; windows 2023/24 and cal2023")}


def split(pool, seed):
    """Household-level 75/25 split, HP households stratified by (first) station, fill globally."""
    rng = np.random.default_rng(seed)
    hh = pool.drop_duplicates("hh").assign(grp=lambda d: np.where(d["role"] == "fill", "fill", d["station"]))
    test = set()
    for _, g in hh.groupby("grp"):
        ids = sorted(g["hh"])
        test |= set(rng.permutation(ids)[:int(round(TEST_FRAC * len(ids)))])
    return pool.assign(split=np.where(pool["hh"].isin(test), "test", "train"))


def cell_counts(pool, seeds, shared_fill):
    """Mean over split seeds of H (HP per station), H_all (incl. count-only) and F (fill) per split/window."""
    rows = []
    for seed in seeds:
        s = split(pool, seed)
        for (sp, w), g in s.groupby(["split", "window"]):
            F = g["hh"].nunique() if shared_fill else g.loc[g["role"] == "fill", "hh"].nunique()
            for st, gs in g[g["role"] != "fill"].groupby("station"):
                rows.append({"split": sp, "window": w, "station": st, "H": (gs["role"] == "hp").sum(),
                             "H_all": len(gs), "F": F})
    return pd.DataFrame(rows).groupby(["split", "window", "station"]).mean().round(1).reset_index()


def size_max(H, F, p, shared_fill):
    by_hp = int(np.floor(H / p + 1e-9))
    return min(by_hp, int(F)) if shared_fill else (by_hp if p == 1.0 else min(by_hp, int(np.floor(F / (1 - p) + 1e-9))))


def envelope(name, pool, spec, seeds, nameplate_ids):
    shared = name == "A"
    if pool[pool["role"] == "hp"].empty:
        return f"## Option {name}\n\n{spec}. **No HP households in this pool.**", {"option": name}
    cc = cell_counts(pool, seeds, shared)
    if set(cc["split"]) != {"train", "test"}:
        return f"## Option {name}\n\n{spec}. **Too few HP households to populate both splits.**", {"option": name}
    best = cc.loc[cc.groupby("split")["H"].idxmax()].set_index("split")
    hp = pool[pool["role"] == "hp"].drop_duplicates("hh")
    s0 = split(pool, seeds[0]).drop_duplicates("hh")
    n_tr, n_te = [int(((s0["role"] == "hp") & (s0["split"] == sp)).sum()) for sp in ("train", "test")]
    sizes = pd.DataFrame([{"split": sp, "station/window": f"{best.at[sp, 'station']} {best.at[sp, 'window']}",
                           "H": best.at[sp, "H"], **{f"p={p}": size_max(best.at[sp, "H"], best.at[sp, "F"], p, shared) for p in PENS}}
                          for sp in ("train", "test")])
    if (cc["H_all"] > cc["H"]).any():      # count-only HP members (HP_Count / nameplate arms only)
        ba = cc.loc[cc.groupby("split")["H_all"].idxmax()].set_index("split")
        sizes = pd.concat([sizes, pd.DataFrame([{"split": f"{sp} incl. count-only", "station/window": f"{ba.at[sp, 'station']} {ba.at[sp, 'window']}",
                                                 "H": ba.at[sp, "H_all"], **{f"p={p}": size_max(ba.at[sp, "H_all"], ba.at[sp, "F"], p, shared) for p in PENS}}
                                                for sp in ("train", "test")])])
    Ht, Ft = best.at["test", "H"], best.at["test", "F"]
    sat = []
    for size, p in CELLS:
        k = int(round(p * size))
        ok = k <= Ht and size <= size_max(Ht, Ft, p, shared)
        sat.append({"size": size, "p": p, "n_hp": k, "log10 #HP combos (test)": round(log10(comb(int(Ht), k)), 1) if ok else "infeasible",
                    "HP overlap of 2 random subs (n_hp/H)": round(k / Ht, 2) if ok else "-"})
    hpa = pool[(pool["role"] != "fill") & pool["hh"].isin(nameplate_ids)]
    n_np = hpa["hh"].nunique()
    np_cell = hpa.groupby(["window", "station"])["hh"].nunique()
    n_np_cell = int(np_cell.max()) if len(np_cell) else 0
    daily = name == "D"
    sub = len(hp)
    feas = {"HP_Peak": (not daily, sub), "HP_CoincPeak": (not daily, sub),
            "HP_Count": (True, pool[pool["role"] != "fill"]["hh"].nunique()),
            "HP_Nameplate_el": (n_np_cell >= 20, n_np), "s_h": (True, sub), "r": (True, sub), "P_design": (True, sub)}
    tg = pd.DataFrame([{"target": t, "feasible": "yes" if f else "no", "HP households": n} for t, (f, n) in feas.items()])
    txt = (f"## Option {name}\n\n{spec}. Distinct HP households: **train {n_tr} / test {n_te}** (seed {seeds[0]}); "
           f"fill households: {pool[pool['role'] == 'fill']['hh'].nunique() if not shared else 'shared with HP pool'}.\n\n"
           f"Pool per split / window / station (mean over {len(seeds)} split seeds):\n\n{md_table(cc)}\n\n"
           f"Max feeder size (best station, no household twice):\n\n{md_table(sizes)}\n\n"
           f"Saturation at representative cells (test split, best station):\n\n{md_table(pd.DataFrame(sat))}\n\n"
           f"Targets:\n\n{md_table(tg)}")
    comp = {"option": name, "HP train": n_tr, "HP test": n_te, "resolution": "daily" if daily else "15-min",
            **{f"max size test p={p}": sizes.iloc[1][f"p={p}"] for p in (0.1, 0.3, 0.5, 1.0)},
            "nameplate HP hh (best station-window)": f"{n_np} ({n_np_cell})", "targets": ", ".join(t for t, (f, _) in feas.items() if f)}
    return txt, comp


def proposal_grid(name, pool, seeds, grid):
    """Apply the proposal's size x penetration rule (configs/protocol_v1_proposal.yaml) to one pool."""
    cc = cell_counts(pool, seeds, shared_fill=False)
    rows, dropped = [], set()
    for r in cc.itertuples():
        H = int(r.H)
        if H < grid["min_station_pool"]:
            continue
        keep = [(s, p) for s in grid["size"] for p in grid["penetration"]
                if max(1, round(p * s)) <= grid["max_overlap"] * H and s - max(1, round(p * s)) <= r.F]
        dropped |= {(s, p) for s in grid["size"] for p in grid["penetration"]} - set(keep)
        rows.append({"option": name, "split": r.split, "window": r.window, "station": r.station, "H": H,
                     "cells kept": len(keep), "substations": len(keep) * grid["substations_per_cell"][r.split]})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    out = ROOT / cfg["out_dir"]
    out.mkdir(parents=True, exist_ok=True)
    seeds = [cfg["seeds"]["split"] + i for i in range(cfg["seeds"]["n_split_seeds"])]
    scans = load_scans(ROOT / cfg["cache_dir"], cfg.get("scan_limit"))
    prot = pd.read_csv(HEAPO / "reports" / "protocols.csv", sep=";", low_memory=False)
    npl = set("H:" + prot.loc[prot["HeatPump_Installation_Normpoint_ElectricPower"].notna(), "Household_ID"]
              .dropna().astype(int).astype(str))
    texts, comps = [], []
    pools = option_pools(scans)
    for name, (pool, spec) in pools.items():
        t, c = envelope(name, pool, spec, seeds, npl)
        texts.append(t)
        comps.append(c)
    grid = yaml.safe_load(open(ROOT / "configs" / "protocol_v1_proposal.yaml"))["grid"]
    pg = pd.concat([proposal_grid("B*", pools["B*"][0], seeds, grid),
                    proposal_grid("D (submetered)", pools["D"][0], seeds, grid)])
    texts.append(f"## Proposal grid (configs/protocol_v1_proposal.yaml: sizes {grid['size']}, p {grid['penetration']}, "
                 f"keep n_hp <= {grid['max_overlap']} x H, >= {grid['min_station_pool']} HP per station)\n\n"
                 f"{md_table(pg)}\n\nTotal substations per split seed: "
                 + (", ".join(f"{o} {sp}: {int(g['substations'].sum())}" for (o, sp), g in pg.groupby(['option', 'split']))
                    if len(pg) else "none (no station reaches the minimum pool)"))
    head = (f"# Iteration 01 - design envelope\n\nSource: `scripts/audit/design_envelope.py` (config `{cfg['exp_id']}`), "
            "counts from `pool_inventory.py` scans; no load series built. HP_Nameplate_el is marked feasible only with "
            ">= 20 nameplate HP households.\n\n## Comparison\n\n" + md_table(pd.DataFrame(comps)))
    (out / "design_envelope.md").write_text(head + "\n\n" + "\n\n".join(texts) + "\n", encoding="utf-8")
    print(f"wrote {out / 'design_envelope.md'}")


if __name__ == "__main__":
    sys.exit(main())
