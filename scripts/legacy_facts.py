"""Legacy-pipeline facts (iteration 00), computed from the caches in data/.

Writes results/<exp>/facts.md + facts.json, and two small parquet extracts in
data/_paperb/iter00/ that tests/test_legacy_facts.py uses so the tests do not
have to unpickle the 1.8 GB substation file:

* legacy_prep_datarange.parquet  -- the 57-household HEAPO 2023 pool (data/_regen_prep.pkl)
* legacy_substation_members.parquet -- per-substation membership of data/substations_data_pooled.pkl

`replay_membership` re-runs the random draws of
scripts/legacy/regenerate_substations_pooled.py (lines 106-195) without building
the load series, to check that the legacy design is reproducible from its seed.

    python scripts/legacy_facts.py --config configs/iter00_full.yaml
"""
import argparse
import json
import pickle
import sys
from pathlib import Path
from random import Random

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hp_capacity as hc  # noqa: E402

PAPERB = ROOT / "data" / "_paperb" / "iter00"
PREP_PQ = PAPERB / "legacy_prep_datarange.parquet"
MEMBERS_PQ = PAPERB / "legacy_substation_members.parquet"
# design constants copied from regenerate_substations_pooled.py
PEN_LEVELS = [round(0.1 * k, 1) for k in range(1, 11)]
SIZE_LEVELS = list(range(10, 121, 10))
REPLICATES, MIN_STATION_POOL = 9, 3


# ------------------------------------------------------------------ extracts --
def load_prep():
    if not PREP_PQ.exists():
        PAPERB.mkdir(parents=True, exist_ok=True)
        dr, _ = pickle.load(open(ROOT / "data/_regen_prep.pkl", "rb"))
        dr.rename_axis("Household_ID").to_parquet(PREP_PQ)
    return pd.read_parquet(PREP_PQ)


def load_members():
    if not MEMBERS_PQ.exists():
        PAPERB.mkdir(parents=True, exist_ok=True)
        sub = pickle.load(open(ROOT / "data/substations_data_pooled.pkl", "rb"))
        m = sub[["size", "HP_ratio", "weather_id", "split", "households_hp", "households", "HP_Peak"]].copy()
        m["HP_CoincPeak_legacy"] = sub["HP_Load"].apply(lambda s: float(np.max(s)))
        m["households_hp"] = m["households_hp"].apply(lambda l: [int(h) for h in l])
        m["households"] = m["households"].apply(lambda l: [int(h) for h in l])
        m.to_parquet(MEMBERS_PQ)
    return pd.read_parquet(MEMBERS_PQ)


# -------------------------------------------------------------------- replay --
def legacy_split(datarange, seed=42):
    return hc.household_pool_split(datarange.index.tolist(), test_frac=0.5, seed=seed)


def replay_membership(datarange, seed=42):
    """Re-draw the legacy substation membership (same RNG calls, same order)."""
    train_hh, _ = legacy_split(datarange, seed)
    dr = datarange.copy()
    dr["split"] = ["train" if h in train_hh else "test" for h in dr.index]
    pools = {s: {w: g.index.tolist() for w, g in dr[dr["split"] == s].groupby("Weather_ID")}
             for s in ("train", "test")}
    split_pool = {s: dr[dr["split"] == s].index.tolist() for s in ("train", "test")}
    seeds = {s: [(w, v) for w, v in pools[s].items() if len(v) >= MIN_STATION_POOL]
             for s in ("train", "test")}
    rng, nprng = Random(seed), np.random.default_rng(seed)
    rows = []
    for split in ("train", "test"):
        for pen in PEN_LEVELS:
            for size in SIZE_LEVELS:
                for _ in range(REPLICATES):
                    st = seeds[split]
                    wts = np.array([len(v) for _, v in st], dtype=float)
                    wid = st[nprng.choice(len(st), p=wts / wts.sum())][0]
                    n_hp = int(round(pen * size))
                    hp = [rng.choice(pools[split][wid]) for _ in range(n_hp)]
                    fill = [rng.choice(split_pool[split]) for _ in range(size - n_hp)]
                    rows.append(dict(split=split, HP_ratio=pen, size=size, weather_id=wid,
                                     households_hp=[int(h) for h in hp],
                                     households=[int(h) for h in fill]))
    return pd.DataFrame(rows)


def wpuq_synthetic_members(n_house=37, n=400, size_range=(10, 37), pen_max=0.5, seed=7):
    """Replay of the draws in hc.build_wpuq_substations (members only)."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        size = int(rng.integers(size_range[0], size_range[1] + 1))
        n_hp = int(round(float(rng.uniform(0.0, pen_max)) * size))
        hp = rng.integers(0, n_house, n_hp)
        fill = rng.integers(0, n_house, size - n_hp)
        out.append(dict(size=size, n_hp=n_hp, hp=hp.tolist(), fill=fill.tolist()))
    return pd.DataFrame(out)


# --------------------------------------------------------------------- facts --
def _pool(name):
    return pickle.load(open(ROOT / "data" / name, "rb"))


def _robust_median(pool):
    return float(np.median([hc.robust_series_peak(r, 0.999) for r in pool["hp_mat"]]))


def compute_facts(seed=42):
    F = {}
    dr = load_prep()
    mem = load_members()
    train_hh, test_hh = legacy_split(dr, seed)

    # pools
    swiss, comb, design, wpuq = (_pool(n) for n in ("_swiss_pool_cache.pkl", "_combined_pool_cache.pkl",
                                                    "_design_pool_cache.pkl", "_wpuq_pool_cache.pkl"))

    def per_station(pool, hp_only=True):
        ids = pool["hp_households"] if hp_only else pool["households"]
        return pool["weather_of"].reindex(ids).value_counts().to_dict()

    F["pools"] = {
        "heapo_2023_legacy (data/_regen_prep.pkl)": {"hp_households": len(dr),
                                                      "per_station": dr["Weather_ID"].value_counts().to_dict()},
        "heapo_design (data/_design_pool_cache.pkl)": {"hp_households": len(design["hp_households"]),
                                                        "consumers": len(design["households"]),
                                                        "per_station": per_station(design),
                                                        "hp_set_equals_legacy": set(map(int, design["hp_households"])) == set(map(int, dr.index))},
        "swiss_kaiser_paired (data/_swiss_pool_cache.pkl)": {"hp_households": len(swiss["hp_households"]),
                                                              "consumers": len(swiss["households"]),
                                                              "eheat_households": len(swiss["eheat_households"]),
                                                              "per_station": per_station(swiss)},
        "combined (data/_combined_pool_cache.pkl)": {"hp_households": len(comb["hp_households"]),
                                                      "consumers": len(comb["households"]),
                                                      "eheat_households": len(comb["eheat_households"]),
                                                      "per_station": per_station(comb)},
        "wpuq (data/_wpuq_pool_cache.pkl)": {"hp_households": len(wpuq["hp_households"]),
                                              "per_station": per_station(wpuq)},
    }

    # split
    used = {s: sorted({h for l in mem.loc[mem.split == s, "households_hp"] for h in l}) for s in ("train", "test")}
    fill = {s: sorted({h for l in mem.loc[mem.split == s, "households"] for h in l}) for s in ("train", "test")}
    st = {s: dr.loc[sorted(train_hh if s == "train" else test_hh), "Weather_ID"].value_counts().to_dict()
          for s in ("train", "test")}
    F["split"] = {
        "seed": seed, "test_frac": 0.5,
        "train_hh": len(train_hh), "test_hh": len(test_hh),
        "per_station": st,
        "hp_households_used_in_substations": {s: len(used[s]) for s in used},
        "fill_households_used": {s: len(fill[s]) for s in fill},
        "train_test_overlap_hp": len(set(used["train"]) & set(used["test"])),
        "train_test_overlap_any": len((set(used["train"]) | set(fill["train"])) & (set(used["test"]) | set(fill["test"]))),
        "legacy_members_consistent_with_seed_split": bool(set(used["train"]) | set(fill["train"]) <= train_hh
                                                          and set(used["test"]) | set(fill["test"]) <= test_hh),
    }

    # design + replacement
    rep = replay_membership(dr, seed)
    same = all((rep[c].tolist() == mem[c].tolist()) for c in ("split", "size", "weather_id"))
    same_members = all(list(a) == list(b) for a, b in zip(rep["households_hp"], mem["households_hp"])) and \
        all(list(a) == list(b) for a, b in zip(rep["households"], mem["households"]))
    peak = dr["HP_robust_kW"].to_dict()
    hp_peak_replay = np.array([sum(peak[h] for h in l) for l in mem["households_hp"]])
    m = mem.copy()
    m["n_hp"] = m["households_hp"].apply(len)
    m["n_unique_hp"] = m["households_hp"].apply(lambda l: len(set(l)))
    m["hp_in_fill"] = [len(set(a) & set(b)) for a, b in zip(m["households_hp"], m["households"])]
    big = m[(m.split == "train") & (m["size"] == 120) & (m.HP_ratio == 1.0)]
    reps_tbl = (m.assign(rep=m.n_hp / m.n_unique_hp.replace(0, np.nan))
                .groupby(["split", "size"])["rep"].mean().unstack(0).round(2))
    F["design"] = {
        "n_substations": {k: int(v) for k, v in mem["split"].value_counts().items()},
        "sizes": sorted(mem["size"].unique().tolist()), "penetrations": sorted(mem["HP_ratio"].unique().tolist()),
        "replicates_per_cell": REPLICATES,
        "hp_draws": "with replacement, from the substation's weather-station pool of the split",
        "fill_draws": "with replacement, from the whole split pool (all 57 are HP households; fill contributes their 'Other' channel)",
        "stations_used": {s: sorted(mem.loc[mem.split == s, "weather_id"].unique().tolist()) for s in ("train", "test")},
        "substations_per_station": {s: mem.loc[mem.split == s, "weather_id"].value_counts().to_dict() for s in ("train", "test")},
        "train_120_pen100": {"n": len(big), "mean_unique_hp": float(big.n_unique_hp.mean()),
                             "mean_appearances_per_hp_profile": float((big.n_hp / big.n_unique_hp).mean())},
        "mean_appearances_by_size_split": reps_tbl.to_dict(),
        "substations_with_hh_as_both_hp_and_fill": int((m.hp_in_fill > 0).sum()),
        "replay_matches_legacy_meta": bool(same), "replay_matches_legacy_members": bool(same_members),
        "HP_Peak_replay_max_abs_diff_kW": float(np.max(np.abs(hp_peak_replay - mem["HP_Peak"].to_numpy()))),
    }
    wm = wpuq_synthetic_members()
    wm_hp = wm[wm.n_hp > 0]
    F["wpuq_synthetic"] = {"n": len(wm), "n_zero_hp": int((wm.n_hp == 0).sum()),
                           "size_range": [int(wm["size"].min()), int(wm["size"].max())],
                           "draws": "with replacement from 37 houses (HP and fill)",
                           "mean_appearances_per_hp_profile": float((wm_hp.n_hp / wm_hp.hp.apply(lambda l: len(set(l)))).mean())}

    # targets
    q = [0, .05, .25, .5, .75, .95, 1]
    F["targets"] = {
        "HP_Peak_quantiles_kW": {s: mem.loc[mem.split == s, "HP_Peak"].quantile(q).round(1).to_dict() for s in ("train", "test")},
        "HP_Peak_mean_by_pen_test": mem[mem.split == "test"].groupby("HP_ratio")["HP_Peak"].mean().round(1).to_dict(),
        "coincidence_ratio_HP_CoincPeak_over_HP_Peak_median": float((mem["HP_CoincPeak_legacy"] / mem["HP_Peak"]).median()),
        "per_hp_robust_peak_median_kW": {"HEAPO (57)": float(dr["HP_robust_kW"].median()),
                                         "Swiss/Kaiser (24)": _robust_median(swiss),
                                         "WPUQ (37)": _robust_median(wpuq)},
        "WPUQ_real_feeder_HP_Peak_kW": float(sum(hc.robust_series_peak(r, 0.999) for r in wpuq["hp_mat"])),
    }

    # coverage
    F["coverage"] = {
        "HEAPO legacy": ["2023-01-01 00:00 UTC", "2023-12-31 23:45 UTC", "15 min; household kept if >80% of 2023 rows"],
        "Swiss/Kaiser pool": [str(swiss["index"][0]), str(swiss["index"][-1]), "not used by the 10 legacy capacity scripts"],
        "WPUQ": [str(wpuq["index"][0]), str(wpuq["index"][-1]), "2019 only (2020 file unused)"],
        "FeederBW": ["-", "-", "not used by the 10 legacy scripts (only a housing-units printout)"],
    }

    # protocol overlap
    p = pd.read_csv(ROOT / "data/heapo_data/reports/protocols.csv", sep=";")
    pe = p[p["HeatPump_Installation_Normpoint_ElectricPower"].notna() & p["Household_ID"].notna()]
    ids = set(pe["Household_ID"].astype(int))
    F["protocols"] = {"protocol_rows": len(p), "rows_with_normpoint_el": int(p["HeatPump_Installation_Normpoint_ElectricPower"].notna().sum()),
                      "households_with_normpoint_el": len(ids),
                      "in_legacy_2023_pool": len(ids & set(dr.index)),
                      "in_train": len(ids & train_hh), "in_test": len(ids & test_hh),
                      "households_with_heating_capacity_in_pool": len(set(p.loc[p["HeatPump_Installation_HeatingCapacity"].notna()
                                                                               & p["Household_ID"].notna(), "Household_ID"].astype(int)) & set(dr.index))}
    return F


def _dict_table(d):
    return "; ".join(f"{k}: {v}" for k, v in d.items())


def write_facts_md(F, path):
    P, S, D, T = F["pools"], F["split"], F["design"], F["targets"]
    L = ["# Iteration 00 - legacy facts (computed by `scripts/legacy_facts.py`)", "",
         "## HP households per pool", "", "| pool | HP households | consumers | per station (HP) |", "|---|---|---|---|"]
    for k, v in P.items():
        L.append(f"| {k} | {v['hp_households']} | {v.get('consumers', '')} | {_dict_table(v['per_station'])} |")
    L += ["", "**81 vs 57 resolved.** Every legacy capacity result (all 10 scripts) is trained and tested on the "
          f"**{P['heapo_2023_legacy (data/_regen_prep.pkl)']['hp_households']}-household HEAPO 2023 pool** "
          "(`data/_regen_prep.pkl`, same HP set as `_design_pool_cache.pkl`). "
          f"81 is the HP count of the *combined* HEAPO+Swiss pool (57 + 24), which the legacy capacity scripts never load. "
          "Notebook cell 160 (\"81-household dataset\") is wrong; cell 178 (\"57\") is right. "
          "The \"Swiss\" in legacy names (`swiss_penetration_sweep`, `capacity_swiss.pkl`, `_X_swiss_pooled.pkl`) means HEAPO (Swiss households), not the Kaiser et al. dataset.",
          "", "## Split", "",
          f"- `household_pool_split(seed={S['seed']}, test_frac={S['test_frac']})`: train {S['train_hh']} / test {S['test_hh']} HP households.",
          f"- per station: train {_dict_table(S['per_station']['train'])}; test {_dict_table(S['per_station']['test'])}.",
          f"- HP households actually used in substations (stations with >= 3 in the split): train {S['hp_households_used_in_substations']['train']}, test {S['hp_households_used_in_substations']['test']}.",
          f"- fill households used: train {S['fill_households_used']['train']}, test {S['fill_households_used']['test']}.",
          f"- train/test overlap (any role): {S['train_test_overlap_any']}; legacy members consistent with the seed-42 split: {S['legacy_members_consistent_with_seed_split']}.",
          "", "## Substation design", "",
          f"- substations: {_dict_table(D['n_substations'])}; sizes {D['sizes'][0]}..{D['sizes'][-1]} step 10; penetration {D['penetrations'][0]}..{D['penetrations'][-1]} step 0.1; {D['replicates_per_cell']} replicates per (split, pen, size) cell.",
          f"- HP draws: {D['hp_draws']}. Fill draws: {D['fill_draws']}.",
          f"- stations used: train {D['stations_used']['train']}, test {D['stations_used']['test']}; substations per station: train {_dict_table(D['substations_per_station']['train'])}, test {_dict_table(D['substations_per_station']['test'])}.",
          f"- **120-dwelling, 100 %-penetration train substations** (n={D['train_120_pen100']['n']}): {D['train_120_pen100']['mean_unique_hp']:.1f} distinct HP profiles on average, so **each HP profile appears {D['train_120_pen100']['mean_appearances_per_hp_profile']:.1f} times** on average.",
          f"- substations where a household is both an HP member and a fill member: {D['substations_with_hh_as_both_hp_and_fill']} of 2160.",
          f"- replay of the seed-42 draws reproduces the legacy membership: meta {D['replay_matches_legacy_meta']}, members {D['replay_matches_legacy_members']}; HP_Peak recomputed from members, max |diff| = {D['HP_Peak_replay_max_abs_diff_kW']:.2e} kW.",
          "", "Mean appearances per HP profile (n_hp / distinct), by size:", "", "| size | train | test |", "|---|---|---|"]
    for size in D["sizes"]:
        L.append(f"| {size} | {D['mean_appearances_by_size_split']['train'][size]} | {D['mean_appearances_by_size_split']['test'][size]} |")
    W = F["wpuq_synthetic"]
    L += ["", f"Synthetic WPUQ set: {W['n']} substations, sizes {W['size_range']}, {W['n_zero_hp']} with zero HP, {W['draws']}; mean appearances per HP profile {W['mean_appearances_per_hp_profile']:.2f}.",
          "", "## Targets", "",
          f"- HP_Peak quantiles (kW), train: {_dict_table(T['HP_Peak_quantiles_kW']['train'])}",
          f"- HP_Peak quantiles (kW), test: {_dict_table(T['HP_Peak_quantiles_kW']['test'])}",
          f"- mean test HP_Peak by penetration: {_dict_table(T['HP_Peak_mean_by_pen_test'])}",
          f"- median HP_CoincPeak / HP_Peak over all substations: {T['coincidence_ratio_HP_CoincPeak_over_HP_Peak_median']:.3f}",
          f"- per-HP robust (q99.9) peak median: {_dict_table({k: round(v, 2) for k, v in T['per_hp_robust_peak_median_kW'].items()})} kW",
          f"- real WPUQ feeder HP_Peak: {T['WPUQ_real_feeder_HP_Peak_kW']:.1f} kW",
          "", "## Coverage", "", "| dataset | start | end | note |", "|---|---|---|---|"]
    L += [f"| {k} | {a} | {b} | {c} |" for k, (a, b, c) in F["coverage"].items()]
    Pr = F["protocols"]
    L += ["", "## HEAPO protocol overlap", "",
          f"- {Pr['protocol_rows']} protocol rows; {Pr['rows_with_normpoint_el']} have `Normpoint_ElectricPower`, covering {Pr['households_with_normpoint_el']} households with a Household_ID.",
          f"- of these, **{Pr['in_legacy_2023_pool']}** are in the 57-household 2023 pool (train {Pr['in_train']}, test {Pr['in_test']}).",
          f"- for comparison, households in the pool with any `HeatingCapacity` protocol entry: {Pr['households_with_heating_capacity_in_pool']}."]
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ap.parse_args().config))
    F = compute_facts(seed=cfg["seeds"]["split"])
    out = ROOT / cfg["out_dir"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "facts.json").write_text(json.dumps(F, indent=2, default=str), encoding="utf-8")
    write_facts_md(F, out / "facts.md")
    print((out / "facts.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
