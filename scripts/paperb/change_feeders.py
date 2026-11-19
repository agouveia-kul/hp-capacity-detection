"""Paired-feeder generator (iteration 08, Task 1; iterations/08-change-detection.md, DECISIONS.md 2026-11-18).

Within GB-EoH, main year (pool 2122r3) and replication year (pool 2223r3), per split seed s:
- households: the 06 A-GB test HP households of seed s (`household_splits` on the main-year pool, as 06 drew them) that are
  eligible in both windows (in both pool tables: >= 90 % valid 30-min bins in each window, silent-electricity rule), and the
  seed's test fillers (LCL Std; the fill split depends on the filler set only, which is the same in both pools);
- halves: both are split into two household-disjoint halves (stream [s, HALF_STREAM]); HP homes stratified by their main-year
  weather group (alternating within a group from a random start, as `grouped_inner_folds` with k = 2), fillers alternating
  over a random permutation;
- cells: per half, main-year weather group, N, p1 and dp: k1 = round(p1 N) existing HP homes, dk = round(dp N) new ones
  (dk >= 1 for dp > 0). The 06 generator rules apply to the year-2 feeder (the larger one): the group's half pool H >=
  min_station_pool, k1 + dk <= max_overlap * H (no stacking), N fillers <= the half's fillers. Infeasible cells are listed;
- feeders: `feeders_per_cell` per cell (stream [s, FEEDER_STREAM, half, crc32(cell)]): k1 + dk distinct HP homes of the group's
  half (the first k1 existing, the other dk new) and N distinct fillers of the half, one per dwelling. Year 1: the k1 HP homes
  and the N fillers; year 2: the same fillers and k1 homes plus the dk new homes (a non-HP dwelling that gains a heat pump keeps
  its filler; N is constant). The year-2 weather group is the main-year group's (one-to-one over the shared homes; asserted);
- labels (native HP_Peak of each year's pool table): C1, C2, dC_added = sum of the new homes' year-2 HP_Peak, dC_total = C2 - C1.
`year_members` gives each year's memberships in the substations.py format (evaluate_members / cached_eval).
"""
import zlib

import numpy as np
import pandas as pd

from paperb.splits import household_splits

HALF_STREAM, FEEDER_STREAM = 7, 8


def test_households(meta1, meta2, seed, split_cfg):
    """The seed's 06 A-GB test HP homes eligible in both years, its test fillers and its train fillers (s0 of E2)."""
    sp = household_splits(meta1, [seed], split_cfg["test_frac"], split_cfg["stratify"])[seed]
    hp2 = set(meta2.index[meta2["role"] == "hp"])
    fill2 = set(meta2.index[meta2["role"] == "fill"])
    if not set(sp["test"]["fill"]) | set(sp["train"]["fill"]) <= fill2:
        raise ValueError("the filler sets of the two pools differ")
    return {"hp": [h for h in sp["test"]["hp"] if h in hp2], "fill": sorted(sp["test"]["fill"]),
            "train_fill": sorted(sp["train"]["fill"]), "n_test_hp_06": len(sp["test"]["hp"])}


def make_halves(hp, fill, meta1, seed):
    """Series household -> half (0 / 1) over the HP homes (stratified by main-year weather group) and the fillers."""
    rng, half = np.random.default_rng([seed, HALF_STREAM]), {}
    st = meta1.loc[hp, "station"]
    for _, g in st.groupby(st, sort=True):
        start = int(rng.integers(2))
        for i, h in enumerate(rng.permutation(sorted(g.index))):
            half[h] = (start + i) % 2
    for i, h in enumerate(rng.permutation(sorted(fill))):
        half[h] = i % 2
    return pd.Series(half, name="half").sort_index()


def plan(by_station, n_fill, cc, tag):
    """Feasible and dropped cells of one half (06 rules on the year-2 feeder)."""
    cells, dropped = [], []
    for st, hs in sorted(by_station.items()):
        H = len(hs)
        for N in cc["N"]:
            for p1 in cc["p1"]:
                for dp in cc["dp"]:
                    k1, dk = int(round(p1 * N)), int(round(dp * N))
                    rec = {**tag, "station": st, "N": N, "p1": p1, "dp": dp, "k1": k1, "dk": dk, "H": H, "F": n_fill}
                    why = ("dk < 1 for dp > 0" if dp > 0 and dk < 1 else
                           "station pool < min_station_pool" if H < cc["min_station_pool"] else
                           "k1 + dk > max_overlap * H" if k1 + dk > cc["max_overlap"] * H else
                           "fill pool too small" if N > n_fill else None)
                    (cells if why is None else dropped).append(rec if why is None else {**rec, "reason": why})
    return cells, dropped


def build_feeders(meta1, meta2, seed, cc, split_cfg):
    """-> (feeders DataFrame indexed by feeder_id, dropped cells DataFrame, info dict)."""
    hh = test_households(meta1, meta2, seed, split_cfg)
    half = make_halves(hh["hp"], hh["fill"], meta1, seed)
    peak1, peak2 = meta1["hp_peak"].astype(float), meta2["hp_peak"].astype(float)
    rows, dropped = [], []
    for h in (0, 1):
        hp_h = sorted(x for x in hh["hp"] if half[x] == h)
        fill_h = sorted(x for x in hh["fill"] if half[x] == h)
        st = meta1.loc[hp_h, "station"]
        by_st = {s: sorted(g.index) for s, g in st.groupby(st)}
        cells, d = plan(by_st, len(fill_h), cc, {"split_seed": seed, "half": h})
        dropped += d
        for c in cells:
            key = f"{c['station']}|{c['N']}|{c['p1']}|{c['dp']}"
            rng = np.random.default_rng([seed, FEEDER_STREAM, h, zlib.crc32(key.encode())])
            for rep in range(cc["feeders_per_cell"]):
                hp = list(map(str, rng.choice(by_st[c["station"]], c["k1"] + c["dk"], replace=False)))
                old, new = sorted(hp[:c["k1"]]), sorted(hp[c["k1"]:])
                st2 = meta2.loc[old + new, "station"].unique()
                if len(st2) != 1:
                    raise ValueError(f"{key}: HP homes of one main-year group fall in {len(st2)} year-2 groups")
                rows.append({**c, "rep": rep, "station2": st2[0], "hp1": old, "hp_new": new,
                             "fill": sorted(map(str, rng.choice(fill_h, c["N"], replace=False))),
                             "C1": float(peak1[old].sum()), "C2": float(peak2[old + new].sum()), "dC_added": float(peak2[new].sum())})
    F = pd.DataFrame(rows)
    F["dC_total"] = F["C2"] - F["C1"]
    F.index = [f"{r.split_seed}|h{r.half}|{r.station}|{r.N}|{r.p1}|{r.dp}|{r.rep}" for r in F.itertuples()]
    info = {"split_seed": seed, "n_test_hp_06": hh["n_test_hp_06"], "n_test_hp_both_years": len(hh["hp"]),
            "n_test_fill": len(hh["fill"]), "n_train_fill": len(hh["train_fill"]),
            **{f"n_hp_half{h}": int(sum(half[x] == h for x in hh["hp"])) for h in (0, 1)},
            **{f"n_fill_half{h}": int(sum(half[x] == h for x in hh["fill"])) for h in (0, 1)}}
    return F.rename_axis("feeder_id"), pd.DataFrame(dropped), {**info, "train_fill": hh["train_fill"], "half": half}


def year_members(F, year):
    """Memberships of year 1 or 2 in the substations.py format (index = feeder_id|y<year>)."""
    hp = F["hp1"] if year == 1 else F["hp1"] + F["hp_new"]
    M = pd.DataFrame({"split_seed": F["split_seed"], "split": "test", "fold": -1, "half": F["half"],
                      "station": F["station"] if year == 1 else F["station2"], "size": F["N"],
                      "p": F["p1"] if year == 1 else (F["k1"] + F["dk"]) / F["N"], "dp": F["dp"], "rep": F["rep"],
                      "hp_members": hp, "fill_members": F["fill"]}, index=F.index)
    return M.set_axis(pd.Index([f"{i}|y{year}" for i in F.index], name="sub_id"))
