"""Substation generator v1 (Task 4, fixes F12) and per-substation targets.

For every (split seed, split, station, size, penetration) cell the generator draws substations whose
  * dwellings are distinct households (no household twice),
  * HP members are all from one station and fill members are never HP households,
  * fill comes from the same split's (or inner fold's) fill pool.
A cell outside the design envelope (n_hp > max_overlap * H, fill pool too small, or a station with fewer
than min_station_pool HP households) raises InfeasibleCellError, or is listed in dropped_cells.csv when
`grid.on_infeasible: drop`. Nothing is truncated: every stored `size` is the true membership size.

Only memberships are stored; `evaluate_members` builds each aggregate on the fly and returns targets,
anchors, physics features and (optionally) the feature columns of `cfg['feature_sets']`: the legacy
windowed-HDD features (`whdd`) and/or the net-load fit features (`netfit`, 03a); `both` computes both.
"""
import numpy as np
import pandas as pd

from hp_capacity import extract_windowed_hdd_features_from_series
from paperb.features_netfit import netfit_features
from paperb.physics import daily_means, fit_daily, net_features

SPLIT_CODE = {"train": 1, "test": 2, "inner": 3}


class InfeasibleCellError(ValueError):
    pass


def plan_cells(hp_by_station, n_fill, grid, tag, shared=False, fill_all=False):
    """Feasible cells and dropped cells (with reason) of one household pool. `shared`: the fill pool contains
    the HP households, so a substation's HP members are unavailable as its fill. `fill_all` (05a, GB-EoH): every
    dwelling, HP dwellings included, gets one filler household, so a cell needs `size` fillers."""
    cells, dropped = [], []
    for st, hs in sorted(hp_by_station.items()):
        H = len(hs)
        for size in grid["size"]:
            for p in grid["penetration"]:
                n_hp = max(1, int(round(p * size)))
                why = ("station pool < min_station_pool" if H < grid["min_station_pool"] else
                       "n_hp > max_overlap * H" if n_hp > grid["max_overlap"] * H else
                       "fill pool too small" if size - (0 if fill_all else n_hp) > n_fill - (n_hp if shared else 0) else None)
                rec = {**tag, "station": st, "size": size, "p": p, "n_hp": n_hp, "H": H, "F": n_fill}
                if why is None:
                    cells.append(rec)
                elif grid["on_infeasible"] == "raise":
                    raise InfeasibleCellError(f"{rec}: {why}")
                else:
                    dropped.append({**rec, "reason": why})
    return cells, dropped


def draw_cells(cells, hp_by_station, fill, n_per_cell, rng, shared=False, fill_all=False):
    rows = []
    for c in cells:
        for rep in range(n_per_cell):
            hp = rng.choice(hp_by_station[c["station"]], c["n_hp"], replace=False)
            used = set(map(str, hp))
            avail = [h for h in fill if h not in used] if shared else fill
            fl = rng.choice(avail, c["size"] - (0 if fill_all else c["n_hp"]), replace=False)
            rows.append({**c, "rep": rep, "hp_members": sorted(map(str, hp)), "fill_members": sorted(map(str, fl))})
    return rows


def build_substations(meta, split, seed, cfg, folds=None):
    """Memberships of one split seed: train, test and (if `folds` is given) inner-fold substations.

    `split` is household_splits(...)[seed]; `folds` is grouped_inner_folds(...) over the train households.
    Returns (members, dropped) DataFrames; members.index is a readable sub_id.
    """
    g, shared, fall = cfg["grid"], cfg["pool"].get("shared_fill", False), cfg["pool"].get("option") == "gb_eoh"
    pools = [("train", -1, split["train"], g["substations_per_cell"]["train"]),
             ("test", -1, split["test"], g["substations_per_cell"]["test"])]
    if folds is not None:
        for f in sorted(folds.unique()):
            inner = {k: [h for h in split["train"][k] if folds[h] == f] for k in ("hp", "fill")}
            pools.append(("inner", int(f), inner, cfg["cv"]["inner_substations_per_cell"]))
    rows, dropped = [], []
    for name, fold, hh, n in pools:
        rng = np.random.default_rng([seed, SPLIT_CODE[name], fold + 1])
        by_st = meta.loc[hh["hp"], "station"].groupby(meta.loc[hh["hp"], "station"]).groups
        by_st = {st: sorted(ix) for st, ix in by_st.items()}
        cells, d = plan_cells(by_st, len(hh["fill"]), g, {"split_seed": seed, "split": name, "fold": fold}, shared, fall)
        rows += draw_cells(cells, by_st, sorted(hh["fill"]), n, rng, shared, fall)
        dropped += d
    members = pd.DataFrame(rows)
    members.index = [f"{r.split_seed}|{r.split}{'' if r.fold < 0 else r.fold}|{r.station}|{r.size}|{r.p}|{r.rep}"
                     for r in members.itertuples()]
    return members.rename_axis("sub_id"), pd.DataFrame(dropped)


def _fit_or_nan(T, y):
    try:
        return fit_daily(*daily_means(T, y))
    except (RuntimeError, ValueError):
        return {"P_base": np.nan, "s_h": np.nan, "T_h": np.nan, "hinge_inside": np.nan}


def evaluate_members(pool, members, cfg, with_features=True):
    """Targets, anchors and physics features per substation (DataFrame), plus windowed features or None."""
    hp_arr, own_arr, fill_arr = (np.ascontiguousarray(d.to_numpy().T) for d in (pool.hp, pool.own, pool.fill))
    hp_pos = {h: i for i, h in enumerate(pool.hp.columns)}
    fill_pos = {h: i for i, h in enumerate(pool.fill.columns)} if pool.analog is None else {}
    peak = pool.meta["hp_peak"]
    t_design = cfg["target_defs"]["T_design_C"]
    sets = set(cfg.get("feature_sets", ["whdd"]))
    cal = tuple(cfg["pool"].get("holidays", "CH-ZH").split("-"))            # 05a: netfit working-day calendar per pool
    rows, feats = {}, {}
    for sid, m in members.iterrows():
        ih, jf = [hp_pos[h] for h in m["hp_members"]], [fill_pos[h] for h in m["fill_members"] if h in fill_pos]
        hp = pd.Series(hp_arr[ih].sum(axis=0, dtype=np.float64), index=pool.index)
        if pool.analog is not None:                                   # 05a: one analog-day filler per dwelling
            nonhp = pd.Series(pool.analog.aggregate(m["fill_members"], m["station"]), index=pool.index)
        else:
            nonhp = pd.Series(own_arr[ih].sum(axis=0, dtype=np.float64) + fill_arr[jf].sum(axis=0, dtype=np.float64),
                              index=pool.index)
        net, T = hp + nonhp, pool.temp[m["station"]]
        f_hp, f_non = _fit_or_nan(T, hp), _fit_or_nan(T, nonhp)
        rows[sid] = {"HP_Peak": float(peak[m["hp_members"]].sum()), "HP_CoincPeak": float(hp.max()),
                     "HP_Count": len(m["hp_members"]), "s_h": f_hp["s_h"],
                     "r": f_hp["s_h"] / f_non["P_base"] if f_non["P_base"] > 0 else np.nan,
                     "P_design": f_hp["P_base"] + f_hp["s_h"] * max(0.0, f_hp["T_h"] - t_design),
                     "peak": float(net.max()),
                     "T_h_hp": f_hp["T_h"], "hinge_inside_hp": f_hp["hinge_inside"], "P_base_nonhp": f_non["P_base"],
                     **net_features(T, net)}
        if with_features:
            feats[sid] = {}
            if sets & {"whdd", "both"}:
                feats[sid].update(extract_windowed_hdd_features_from_series(net, T, T_base=cfg["features"]["T_base"],
                                                                            **cfg["features"]["kwargs"]))
            if sets & {"netfit", "both"}:
                feats[sid].update(netfit_features(T, net, calendar=cal))
    tab = members.drop(columns=["hp_members", "fill_members"]).join(pd.DataFrame.from_dict(rows, orient="index"))
    return tab, (pd.DataFrame.from_dict(feats, orient="index").reindex(tab.index) if with_features else None)
