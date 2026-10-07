"""Analog-day filler (iteration 05a, Task 3).

GB-EoH has no own non-HP load, so every dwelling of a substation (HP dwellings included) gets one flat-rate LCL
household (`build_lcl`), placed on analog days:
    net(t) = sum_i LCL_i(d'(g, d), slot(t)) + sum_j HP_j(t),
with d the local (Europe/London) calendar day of t, slot(t) its local clock half-hour and d'(g, d) the analog day of
weather group g for day d (`analog_map`), chosen among the candidate days by
  1. same day type (working day vs weekend / bank holiday; England & Wales calendar on both sides);
  2. circular day-of-year distance <= 30 d, widened to 45, then 60 d when no candidate passes 3 (widenings counted);
  3. |T_cand(d') - T_target(d)| <= 1 K (daily means; LCL: London Heathrow, Meteostat WMO 03772 - R4 of 05a-ii; HadCET,
     a Central England composite, is kept as the comparison column `T_hadcet` and as `fill.temp_source: hadcet`);
  4. one of the 3 candidates closest in temperature, drawn at random (seeded).
If no candidate passes 3 even at 60 d, the closest in temperature within 60 d is taken (widen = 3, a > 1 K mismatch).
The same d' applies to every filler of a substation-day (the filler aggregate is indexed once); the map is fixed per
(weather group, split seed). Local clock onto local clock: LCL (UTC in the file) is laid out as 48 local half-hours per
local day (a 25-h day averages its repeated 01:00-02:00 hour; the missing hour of a 23-h day is interpolated), and the
two DST-change days per year are not candidates; a 23-h target day skips local 01:00 and 01:30, a 25-h target day uses
them twice.

D5 (B* swap test, `analog_swap`): the same machinery on B*, with the B* fill households (same year, UTC days) as candidates,
excluding days within +-3 d of the target day; each substation's station is matched on its own temperature on both sides
(R6 of 05a-ii: T_g(d') against T_g(d), not KLO); each substation gets n_hp extra fillers
(`add_own_fillers`) so that every dwelling, HP homes included, carries one analog-day filler, as in GB-EoH.
"""
import json
import zipfile
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from paperb import ROOT
from paperb.features_netfit import weekend_or_holiday
from paperb.physics import fit_daily

LCL_ZIP, LCL_DIR = ROOT / "data" / "LCL_2013.zip", "UKDA-7857-csv/csv/data_collection/data_tables/"
HADCET = ROOT / "data" / "hadcet" / "meantemp_daily_totals.txt"
HEATHROW = ROOT / "data" / "_paperb" / "raw" / "meteostat" / "03772_daily.csv.gz"     # Meteostat bulk daily, London Heathrow
CACHE = ROOT / "data" / "_paperb" / "pools"
MAP_STREAM, SWAP_STREAM = 4, 5
TZ_GB = "Europe/London"


def day_type(days, calendar):
    """True on weekends and public holidays of `calendar` ('GB-ENG', 'CH-ZH')."""
    return weekend_or_holiday(days, *calendar.split("-"))


def hadcet():
    T = pd.read_csv(HADCET, sep=r"\s+", skiprows=1, names=["date", "T"])
    return pd.Series(pd.to_numeric(T["T"], errors="coerce").to_numpy(), index=pd.to_datetime(T["date"], errors="coerce")).dropna()


def heathrow():
    """London Heathrow daily mean temperature (Meteostat bulk `daily/03772.csv.gz`: date, tavg, ...)."""
    d = pd.read_csv(HEATHROW, header=None, usecols=[0, 1], names=["date", "T"])
    return pd.Series(d["T"].to_numpy(float), index=pd.to_datetime(d["date"])).dropna()


def lcl_temperature(source):
    return {"heathrow": heathrow, "hadcet": hadcet}[source]()


def zero_run_max(v):
    """Longest run of exact zeros per column of a 2-D array."""
    out = np.zeros(v.shape[1], int)
    for j in range(v.shape[1]):
        d = np.diff(np.r_[0, (v[:, j] == 0).astype(np.int8), 0])
        s, e = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        out[j] = (e - s).max() if len(s) else 0
    return out


def fill_gaps(X, we, T, max_gap):
    """X [days, slots] with NaN gaps -> (filled copy, donor-filled days). NaN runs of <= max_gap slots are linearly
    interpolated along time; a day with a longer run takes its NaN slots from the same household's complete day of the
    same day type with the nearest daily mean temperature."""
    f = np.array(X, np.float64).ravel()
    nan = np.isnan(f)
    if nan.all():
        return f.reshape(X.shape), X.shape[0]
    d = np.diff(np.r_[0, nan.astype(np.int8), 0])
    short = np.zeros(len(f), bool)
    for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
        short[a:b] = b - a <= max_gap
    f[short] = np.interp(np.flatnonzero(short), np.flatnonzero(~nan), f[~nan])
    Y = f.reshape(X.shape)
    bad = np.isnan(Y).any(axis=1)
    for i in np.flatnonzero(bad):
        c = np.flatnonzero(~bad & (we == we[i]))
        Y[i] = np.where(np.isnan(Y[i]), Y[c[np.argmin(np.abs(T[c] - T[i]))]], Y[i])
    return Y, int(bad.sum())


def local_grid(index, tz, step_min):
    """Target index -> (local days, day position, clock slot) of every stamp; tz None = UTC days (B*)."""
    loc = index if tz is None else index.tz_localize("UTC").tz_convert(tz)
    d = loc.normalize() if tz is None else loc.normalize().tz_localize(None)
    days = pd.DatetimeIndex(d.unique())
    return days, days.get_indexer(d), np.asarray((loc.hour * 60 + loc.minute) // step_min)


def build_lcl(fc, verbose=True):
    """Flat-rate (Std) LCL households on the local-clock grid of `fc['lcl_window']` -> (S [hh, day, 48] kW, memory-mapped;
    days DataFrame date / T (`fill.temp_source`, default heathrow) / T_hadcet / we / dst; meta indexed by 'L:<id>'; audit dict). Cached in data/_paperb/pools/."""
    w0, w1 = (pd.Timestamp(x) for x in fc["lcl_window"])
    src = fc.get("temp_source", "heathrow")
    base = CACHE / f"lcl_std_{w0:%Y%m%d}_{w1:%Y%m%d}_{src}"
    if base.with_suffix(".npy").exists():
        return (np.load(base.with_suffix(".npy"), mmap_mode="r"), pd.read_parquet(f"{base}_days.parquet"),
                pd.read_parquet(f"{base}_meta.parquet"), json.loads(Path(f"{base}_audit.json").read_text()))
    with zipfile.ZipFile(LCL_ZIP) as Z:
        cols = pd.read_csv(Z.open(LCL_DIR + "consumption_n.csv"), nrows=0).columns
        x = pd.read_csv(Z.open(LCL_DIR + "consumption_n.csv"), index_col=0, dtype={c: np.float32 for c in cols[1:]})
        n_tou = len(pd.read_csv(Z.open(LCL_DIR + "consumption_d.csv"), nrows=0).columns) - 1
        sv = pd.read_csv(Z.open(LCL_DIR + "survey_answers.csv"), encoding="latin-1", low_memory=False).set_index("Household_id")
    x.index = pd.to_datetime(x.index)                    # 'GMT': regular 30-min UTC grid (no DST gap or duplicate)
    audit = {"std_households": x.shape[1], "tou_households": n_tou, "file_span": [str(x.index.min()), str(x.index.max())],
             "steps_30min": bool((x.index.to_series().diff().dropna() == pd.Timedelta("30min")).all()),
             "cov90_full_span": int((x.notna().mean() >= 0.9).sum())}
    loc = x.index.tz_localize("UTC").tz_convert(TZ_GB)
    dates = loc.normalize().tz_localize(None)
    keep_t = (dates >= w0) & (dates < w1)
    x, loc, dates = x[keep_t], loc[keep_t], dates[keep_t]
    v = x.to_numpy()
    rules = {"coverage < 0.9": np.isfinite(v).mean(0) < fc["lcl_coverage_min"],
             "half-hour > 10 kWh": np.nanmax(np.where(np.isfinite(v), v, 0), 0) > fc["lcl_max_kwh"],
             "zero run >= 24 h": zero_run_max(v) >= fc["lcl_zero_run_slots"]}
    drop, seq = np.zeros(v.shape[1], bool), {}
    for k, r in rules.items():
        seq[k], drop = int((r & ~drop).sum()), drop | r
    keep = ~drop
    audit.update(rules_alone={k: int(r.sum()) for k, r in rules.items()}, rules_sequential=seq, kept=int(keep.sum()))
    days = pd.DatetimeIndex(sorted(set(dates)))
    pos = days.get_indexer(dates) * 48 + loc.hour * 2 + loc.minute // 30
    L = pd.DataFrame(v[:, keep] * 2.0, index=pos).groupby(level=0).mean().reindex(range(len(days) * 48)).to_numpy()   # kWh/30 min -> kW
    T = lcl_temperature(src).reindex(days).interpolate().to_numpy()
    D = pd.DataFrame({"date": days, "T": T, "T_hadcet": hadcet().reindex(days).interpolate().to_numpy(), "we": day_type(days, fc["calendar"]),
                      "dst": pd.Series(dates).value_counts().reindex(days).to_numpy() != 48})
    S = np.empty((keep.sum(), len(days), 48), np.float32)
    n_filled = np.zeros(keep.sum(), int)
    for j in range(keep.sum()):
        S[j], n_filled[j] = fill_gaps(L[:, j].reshape(len(days), 48), D["we"].to_numpy(), T, fc["max_interp_slots"])
    hh = x.columns[keep]
    q = sv[~sv.index.duplicated()].reindex(hh)            # survey columns are shifted by one against survey_questions.csv
    meta = pd.DataFrame({"coverage": np.isfinite(v[:, keep]).mean(0), "n_filled_days": n_filled,
                         "gas_ch": q["Q246"].eq("Gas").to_numpy(), "no_heater": q["Q303"].eq(0).to_numpy(),
                         "surveyed": q["Q246"].notna().to_numpy()}, index="L:" + hh)
    np.save(base.with_suffix(".npy"), S)
    D.to_parquet(f"{base}_days.parquet")
    meta.to_parquet(f"{base}_meta.parquet")
    Path(f"{base}_audit.json").write_text(json.dumps(audit, indent=1))
    if verbose:
        print(f"LCL Std: {audit['kept']} of {audit['std_households']} kept, {len(days)} local days", flush=True)
    return np.load(base.with_suffix(".npy"), mmap_mode="r"), D, meta, audit


def analog_map(target, cand, rng, windows=(30, 45, 60), tol=1.0, k=3, exclude_days=0):
    """Analog day of every target day. target / cand: DataFrames with date, T, we. Returns a DataFrame over target
    (src = row position in cand, dT, ddoy, widen: 0 = 30 d, 1 = 45 d, 2 = 60 d, 3 = no candidate within tol)."""
    c_doy, c_T, c_we = cand["date"].dt.dayofyear.to_numpy(), cand["T"].to_numpy(), cand["we"].to_numpy()
    c_day = cand["date"].to_numpy().astype("datetime64[D]").astype(np.int64)
    rows = []
    for d, T, we in zip(target["date"], target["T"], target["we"]):
        dd = np.abs(c_doy - d.dayofyear)
        dd = np.minimum(dd, 365 - dd)
        base = (c_we == we) & (np.abs(c_day - np.datetime64(d, "D").astype(np.int64)) > exclude_days)
        dT = np.abs(c_T - T)
        for w_i, w in enumerate(windows):
            if (ok := base & (dd <= w) & (dT <= tol)).any():
                break
        else:
            w_i, ok = len(windows), base & (dd <= windows[-1])
        c = np.flatnonzero(ok)
        j = rng.choice(c[np.argsort(dT[c], kind="stable")][:k])
        rows.append((j, T - c_T[j], dd[j], w_i))
    return pd.DataFrame(rows, columns=["src", "dT", "ddoy", "widen"], index=target.index)


class AnalogFill:
    """Filler aggregate on analog days. S [hh, source day, slot]; cand: candidate source days (date, T, we, pos = day
    position in S); targets: {station: DataFrame(date, T, we)} over the target days; t_day / t_slot: target day position
    and clock slot of every stamp of the pool index."""

    def __init__(self, S, hh, cand, targets, t_day, t_slot, fc, exclude_days=0, cand_T=None):
        self.S, self.pos, self.cand, self.targets = S, {h: i for i, h in enumerate(hh)}, cand.reset_index(drop=True), targets
        self.cand_T = cand_T or {}                                     # {station: candidate-day temperatures} where they differ by station
        self.t_day, self.t_slot, self.fc, self.exclude, self.maps, self.seed = t_day, t_slot, fc, exclude_days, {}, None

    def set_seed(self, seed):
        """Map of every station for split seed `seed` (stream [seed, MAP_STREAM, crc32(station)])."""
        self.seed, self._tot = seed, {}
        self.maps = {st: analog_map(t, self.cand if st not in self.cand_T else self.cand.assign(T=self.cand_T[st]), np.random.default_rng([seed, MAP_STREAM, zlib.crc32(st.encode())]),
                                    tuple(self.fc["doy_windows"]), self.fc["tol_K"], self.fc["k_nearest"], self.exclude)
                     for st, t in sorted(self.targets.items())}

    def day_sum(self, members):
        """Sum of the members' source days [source day, slot] in float64. Rows are added one at a time (the order numpy uses
        for an axis-0 sum, so the result is bitwise identical) to avoid a float64 copy of all members (~0.8 GB for 2,399
        train fillers per worker)."""
        idx = sorted(self.pos[h] for h in members)
        if not idx:
            return np.zeros(self.S.shape[1:], np.float64)
        acc = np.array(self.S[idx[0]], np.float64)
        for i in idx[1:]:
            acc += self.S[i]
        return acc

    def aggregate(self, members, station, A=None):
        """Filler aggregate of `members` on the target index (float64 array)."""
        A = self.day_sum(members) if A is None else A
        return A[self.cand["pos"].to_numpy()[self.maps[station]["src"].to_numpy()][self.t_day], self.t_slot]

    def s0(self, fill_hh, index, temp, stations):
        """Per-dwelling non-TCL slope of the train fillers under each station's map (Paper A net-load fit against that
        station's temperature) -> {station: dict(s0, s_h, T_h, P_base, N)}."""
        A, out = self.day_sum(fill_hh), {}
        for st in stations:
            d = pd.DataFrame({"T": temp[st].to_numpy(), "y": self.aggregate(None, st, A)}, index=index).resample("D").mean().dropna()
            f = fit_daily(d["T"].to_numpy(), d["y"].to_numpy())
            out[st] = {"s0": f["s_h"] / len(fill_hh), "s_h": f["s_h"], "T_h": f["T_h"], "P_base": f["P_base"], "N": len(fill_hh)}
        return out


def station_targets(index, temp, tz, calendar, step_min):
    """(targets per station, t_day, t_slot) of a pool index: daily mean station temperature over the (local) day."""
    days, t_day, t_slot = local_grid(index, tz, step_min)
    we = day_type(days, calendar)
    Td = temp.groupby(t_day).mean()
    return {st: pd.DataFrame({"date": days, "T": Td[st].to_numpy(), "we": we}) for st in temp.columns}, t_day, t_slot


def analog_swap(pool, cfg):
    """D5: B* with every non-HP load replaced by analog days of the B* fill households (same year, +-3 d excluded;
    a substation's candidate days are matched on its own station's temperature, R6). Membership augmentation: `add_own_fillers`."""
    fc, step = cfg["pool"]["analog_swap"], int((pool.index[1] - pool.index[0]).total_seconds() // 60)
    targets, t_day, t_slot = station_targets(pool.index, pool.temp, None, fc["calendar"], step)
    days = targets[next(iter(targets))]["date"]
    cand = pd.DataFrame({"date": days, "T": targets[next(iter(targets))]["T"].to_numpy(),
                         "we": day_type(days, fc["calendar"]), "pos": np.arange(len(days))})
    S = pool.fill.to_numpy().T.reshape(pool.fill.shape[1], len(days), -1)
    pool.analog = AnalogFill(S, list(pool.fill.columns), cand, targets, t_day, t_slot, fc, fc["exclude_days"],
                              {st: t["T"].to_numpy() for st, t in targets.items()})
    pool.fill_per_dwelling = True
    return pool


def add_own_fillers(members, split, folds, seed):
    """D5: n_hp extra fillers per substation (the HP homes' own load becomes analog filler days), drawn from the
    substation's own fill pool (train / test split, or its inner fold), disjoint from its fillers, with a stream per
    substation ([seed, SWAP_STREAM, crc32(sub_id)]). HP members, ids and split assignment are unchanged."""
    pools = {("train", -1): sorted(split["train"]["fill"]), ("test", -1): sorted(split["test"]["fill"])}
    pools.update({("inner", k): [h for h in pools["train", -1] if folds[h] == k] for k in sorted(set(folds))})
    out = members.copy()
    out["fill_members"] = [sorted(r.fill_members + list(map(str, np.random.default_rng([seed, SWAP_STREAM, zlib.crc32(sid.encode())]).choice(
                               sorted(set(pools[r.split, r.fold]) - set(r.fill_members)), r.n_hp, replace=False))))
                           for sid, r in zip(members.index, members.itertuples())]
    return out
