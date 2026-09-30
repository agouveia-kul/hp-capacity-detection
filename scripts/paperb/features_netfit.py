"""Net-load fit feature set `netfit` (iteration 03a, Task 2).

Per substation, Paper A's net-load hockey stick (`physics.fit_daily`: daily means, latent T_h in (8, 20) degC)
is fitted three times: `all` days, `wd` = weekdays that are not public holidays, and `we` = weekends plus
public holidays. Holidays come from the `holidays` package (country CH, subdiv ZH) for every station, plus Berchtoldstag (2 January),
which the package does not carry for ZH (03b; `FEATURE_VERSION` keys the feature cache).
Calendar days are UTC days, as in `physics.daily_means`. T_q05 is the 5th percentile of the daily mean
temperature over all days. A `wd`/`we` fit with fewer than MIN_HEATING_DAYS heating days (days of the
subset with T < T_h of the `all` fit) is NaN, and so is any failed fit; `n_heat_days` is always filled, so it
records why. NaNs are imputed with the train median inside the model pipeline (`train.Model`), never on test.
The kW columns (s_h, P_base, cold_resp) carry scale, as in Paper A's estimator s_h / m_h.

| column (f in all, wd, we) | definition |
|---|---|
| nf_{f}_s_h | heating slope s_h (kW/K) |
| nf_{f}_T_h | hinge temperature T_h (degC) |
| nf_{f}_P_base | base load P_base (kW) |
| nf_{f}_R2_h | R2 of the heating arm on the subset's days below its T_h (Paper A `_arm_r2`; NaN if < 10 days) |
| nf_{f}_n_heat_days | days of the subset with T < T_h(all) |
| nf_{f}_at_bound | 1 if T_h lies within 1e-3 degC of a bound of (8, 20), else 0 |
| nf_{f}_cold_resp | s_h * (T_h - T_q05): heating load of the fit on a T_q05 day (kW) |
| nf_{f}_r_hat | s_h / P_base (1/K) |
| nf_ratio_sh_we_wd | s_h(we) / s_h(wd) |
| nf_ratio_Pbase_we_wd | P_base(we) / P_base(wd) |
| nf_theta_{warm,mild,cold} | mean daily load over the days with theta <= 0 / 0 < theta <= 0.5 / theta > 0.5, divided by P_base(all); theta = (T_h(all) - T) / (T_h(all) - T_q05) |

29 columns in total; the anchors `size` and `peak` are added by `train.feature_matrix`.
"""
import holidays
import numpy as np
import pandas as pd

from hp_common import MIN_HEATING_DAYS
from paperb.physics import fit_daily

FEATURE_VERSION = "03b-berchtoldstag"
FITS = ("all", "wd", "we")
PER_FIT = ("s_h", "T_h", "P_base", "R2_h", "n_heat_days", "at_bound", "cold_resp", "r_hat")
COLUMNS = ([f"nf_{f}_{k}" for f in FITS for k in PER_FIT] + ["nf_ratio_sh_we_wd", "nf_ratio_Pbase_we_wd"]
           + [f"nf_theta_{b}" for b in ("warm", "mild", "cold")])


def weekend_or_holiday(days, country="CH", subdiv="ZH"):
    """Boolean array over calendar days: True on Saturdays, Sundays and public holidays (the `we` days)."""
    idx = pd.DatetimeIndex(days)
    hol = holidays.country_holidays(country, subdiv=subdiv, years=sorted(set(idx.year)))
    berchtold = {pd.Timestamp(y, 1, 2).date() for y in idx.year.unique()}
    return np.asarray((idx.dayofweek >= 5) | np.array([d in hol or d in berchtold for d in idx.date], bool))


def _arm_r2(T, y, th, s, b):
    """Paper A `outputs._arm_r2`: R2 of the heating arm b + s (th - T) on the points below th only."""
    m = T < th
    if m.sum() < 10:
        return np.nan
    yy = y[m]
    ss = np.sum((yy - yy.mean()) ** 2)
    return float(1 - np.sum((yy - (b + s * (th - T[m]))) ** 2) / ss) if ss > 0 else np.nan


def _one_fit(T, y, t_ref, t_q05, min_days):
    """One subset fit; t_ref = None (the `all` fit) skips the heating-day check, a NaN t_ref fails it."""
    out = dict.fromkeys(PER_FIT, np.nan)
    if t_ref is not None:
        out["n_heat_days"] = int(np.sum(T < t_ref)) if np.isfinite(t_ref) else 0
        if out["n_heat_days"] < min_days:
            return out
    try:
        f = fit_daily(T, y)
    except (RuntimeError, ValueError):
        return out
    out.update(s_h=f["s_h"], T_h=f["T_h"], P_base=f["P_base"], R2_h=_arm_r2(T, y, f["T_h"], f["s_h"], f["P_base"]),
               at_bound=float(f["at_bound"]), cold_resp=f["s_h"] * (f["T_h"] - t_q05),
               r_hat=f["s_h"] / f["P_base"] if f["P_base"] > 0 else np.nan)
    return out


def netfit_features(T, net, min_days=MIN_HEATING_DAYS):
    """The 29 `netfit` columns of one substation from its 15-min temperature and net load (Series, UTC index)."""
    d = pd.DataFrame({"T": T, "y": net}).resample("D").mean()
    d = d[np.isfinite(d["T"]) & np.isfinite(d["y"])]
    Td, yd = d["T"].to_numpy(float), d["y"].to_numpy(float)
    we, t_q05 = weekend_or_holiday(d.index), float(np.quantile(Td, 0.05))
    fits = {"all": _one_fit(Td, yd, None, t_q05, min_days)}
    t_ref = fits["all"]["T_h"]
    fits["all"]["n_heat_days"] = int(np.sum(Td < t_ref)) if np.isfinite(t_ref) else 0
    for name, mask in (("wd", ~we), ("we", we)):
        fits[name] = _one_fit(Td[mask], yd[mask], t_ref, t_q05, min_days)
    out = {f"nf_{f}_{k}": v for f, r in fits.items() for k, v in r.items()}
    wd, wk = fits["wd"], fits["we"]
    out["nf_ratio_sh_we_wd"] = wk["s_h"] / wd["s_h"] if wd["s_h"] > 0 else np.nan
    out["nf_ratio_Pbase_we_wd"] = wk["P_base"] / wd["P_base"] if wd["P_base"] > 0 else np.nan
    pb = fits["all"]["P_base"]
    theta = (t_ref - Td) / (t_ref - t_q05) if np.isfinite(t_ref) and t_ref > t_q05 else np.full(len(Td), np.nan)
    for b, m in (("warm", theta <= 0), ("mild", (theta > 0) & (theta <= 0.5)), ("cold", theta > 0.5)):
        out[f"nf_theta_{b}"] = float(yd[m].mean() / pb) if m.any() and pb > 0 else np.nan
    return {c: out[c] for c in COLUMNS}
