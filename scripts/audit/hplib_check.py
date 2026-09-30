"""Iteration 04, Task 4 -- hplib conversion-step check on EoH (feasibility, not a benchmark).

For <= n_sites EoH air-source homes (ASHP and HT-ASHP per HP_Installed; hybrids and GSHP excluded) with a complete season of whole-system
electricity and heat output, predict the HP electricity from the MEASURED heat output with hplib's
generic regulated air/water HP (group 1; group 4 on-off as sensitivity):

    P_el_hat = Q / COP(T_ext, T_flow)        (hplib COP map; T_flow = DHW flow in DHW bins, else SH flow,
                                              else return + 5 K)
    if Q > P_th_max(T_ext, T_flow):  P_el_hat = P_el_max + (Q - P_th_max)   (resistance top-up, COP 1)

Rated power: HP_Size_kW from the EoH property table, taken as the thermal output at A7/W35 (EN 14511 nominal
point; assumption, the table does not state it). Sensitivity: the earlier proxy, 99.5th percentile of the home's
30-min heat output at A2/W35. The COP map does not depend on the rated power; only the capacity limit does.
Measured HP electricity = whole system - immersion - back-up heater - circulation pump (EoH definition).
Scores: WAPE and bias (sum(P_hat - P) / sum P) at 30 min and daily, per outdoor-temperature bin and
regime (DHW, back-up active, standby = Q ~ 0), and the seasonal-performance-factor bias per home.

    python scripts/audit/hplib_check.py --config configs/iter04_inventory.yaml
"""
import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import yaml
from hplib import hplib as hpl

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "audit"))
from inventory_v2 import CACHE, D, SEASONS  # noqa: E402
from pool_inventory import md_table  # noqa: E402

TBINS = [-20, -2, 2, 6, 10, 14, 40]
COLS = ["property", "ts", "P_ws", "n_P_ws", "Q_hp", "n_Q_hp", "P_ih", "P_buh", "P_cp", "T_ext", "T_flow_sh", "T_flow_dhw", "T_ret"]


def load(props, season):
    a, b = SEASONS[season]
    out = []
    for f in sorted((D / "_paperb/pools_raw/eoh").glob("eoh_30min_set*.parquet")):
        x = pd.read_parquet(f)
        x = x[x["property"].isin(props) & (x["ts"] >= a) & (x["ts"] < b)]
        out.append(x.reindex(columns=COLS))
    x = pd.concat(out)
    x = x[(x["n_P_ws"] >= 12) & (x["n_Q_hp"] >= 12) & x["T_ext"].notna()].copy()
    x["P"] = (x["P_ws"] - x[["P_ih", "P_buh", "P_cp"]].fillna(0).sum(axis=1)).clip(lower=0)
    x["dhw"] = x["T_flow_dhw"].notna()
    x["T_out"] = x["T_flow_dhw"].where(x["dhw"], x["T_flow_sh"]).fillna(x["T_ret"] + 5)
    x["backup"] = x[["P_ih", "P_buh"]].fillna(0).sum(axis=1) > 0.05
    return x.dropna(subset=["T_out", "Q_hp"])


def predict(g, group, sizing):
    q = g["Q_hp"].to_numpy() * 1000
    if sizing == "nameplate":
        par = hpl.get_parameters("Generic", group_id=group, t_in=7, t_out=35, p_th=float(g["HP_Size_kW"].iloc[0]) * 1000)
    else:
        par = hpl.get_parameters("Generic", group_id=group, t_in=2, t_out=35, p_th=max(np.quantile(q, 0.995), 1000.0))
    r = hpl.HeatPump(par).simulate(t_in_primary=g["T_ext"].to_numpy(), t_in_secondary=g["T_out"].to_numpy() - 5,
                                   t_amb=g["T_ext"].to_numpy())
    cop, pth, pel = (np.asarray(r[k], float) for k in ("COP", "P_th", "P_el"))
    over = q > pth
    p_hat = np.where(over, pel + (q - pth), q / np.maximum(cop, 1.0)) / 1000
    return p_hat, over


def score(df, by=None):
    f = lambda d: pd.Series({"n": len(d), "WAPE %": 100 * (d["P_hat"] - d["P"]).abs().sum() / d["P"].sum(),
                             "bias %": 100 * (d["P_hat"] - d["P"]).sum() / d["P"].sum(), "share of energy %": 100 * d["P"].sum() / tot,
                             "WAPE after global rescale % (in-sample)": 100 * (d["P_hat"] * d["P"].sum() / d["P_hat"].sum() - d["P"]).abs().sum() / d["P"].sum()})
    tot = df["P"].sum()
    return (df.groupby(by, observed=True)[["P", "P_hat"]].apply(f) if by else f(df).to_frame().T).round(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ROOT / ap.parse_args().config))
    h = cfg["hplib"]
    out = ROOT / cfg["out_dir"]
    (out / "figures").mkdir(parents=True, exist_ok=True)
    U = pd.read_parquet(CACHE / "eoh_units.parquet")
    cand = U[U["seasons_ws_q_str"].str.contains(h["season"], regex=False) & U["type"].isin(["ASHP", "HT-ASHP"])]
    props = sorted(np.random.default_rng(h["seed"]).choice(sorted(cand["property"]), h["n_sites"], replace=False))
    X = load(set(props), h["season"])
    X = X.merge(U.set_index("property")[["type", "HP_Size_kW"]], left_on="property", right_index=True)
    res, spf = [], []
    for group, sizing in ((1, "nameplate"), (4, "nameplate"), (1, "proxy")):
        parts = []
        for pid, g in X.groupby("property", observed=True):
            p_hat, over = predict(g, group, sizing)
            parts.append(g.assign(P_hat=p_hat, over=over))
            spf.append({"group": group, "sizing": sizing, "property": pid, "SPF_meas": g["Q_hp"].sum() / g["P"].sum(),
                        "SPF_pred": g["Q_hp"].sum() / p_hat.sum()})
        Y = pd.concat(parts)
        Y["T bin"] = pd.cut(Y["T_ext"], TBINS)
        Y["regime"] = np.select([Y["backup"], Y["dhw"], Y["Q_hp"] < 0.05], ["back-up active", "DHW", "standby (Q ~ 0)"], "space heating")
        dd = Y.groupby(["property", Y["ts"].dt.floor("D")], observed=True).agg(P=("P", "sum"), P_hat=("P_hat", "sum"), n=("P", "size"),
                                                                              T_ext=("T_ext", "mean"))
        dd = dd[dd["n"] >= 44]
        dd["T bin"] = pd.cut(dd["T_ext"], TBINS)
        res.append((group, sizing, Y, dd))
    S = pd.DataFrame(spf)
    S["bias %"] = 100 * (S["SPF_pred"] / S["SPF_meas"] - 1)
    txt = [f"Homes: {X['property'].nunique()} EoH ASHP homes (seed {h['seed']}), season {h['season']}; {len(X):,} valid 30-min bins. "
           f"Types {X.drop_duplicates('property')['type'].value_counts().to_dict()}. Source: `scripts/audit/hplib_check.py`. "
           "Rated power = HP_Size_kW at A7/W35 (assumption); 'proxy' = 99.5th pct of 30-min heat output at A2/W35."]
    for group, sizing, Y, dd in res:
        name = {1: "group 1 (regulated air/water)", 4: "group 4 (on-off air/water)"}[group] + f", sizing: {sizing}"
        s = S[(S["group"] == group) & (S["sizing"] == sizing)]
        txt += [f"### hplib generic {name}",
                "Overall (30 min / daily):\n\n" + md_table(pd.concat([score(Y).assign(level="30 min"), score(dd).assign(level="daily")])),
                "By outdoor temperature (daily):\n\n" + md_table(score(dd, "T bin").reset_index()),
                "By outdoor temperature (30 min):\n\n" + md_table(score(Y, "T bin").reset_index()),
                "By regime (30 min):\n\n" + md_table(score(Y, "regime").reset_index()),
                "By HP type (daily):\n\n" + md_table(score(dd.join(Y.drop_duplicates("property").set_index("property")["type"]), "type").reset_index()),
                f"Seasonal performance factor (SPF_H2-like, per home): measured median {s['SPF_meas'].median():.2f}, predicted median "
                f"{s['SPF_pred'].median():.2f}; SPF bias median {s['bias %'].median():+.1f} % (10-90 %: {s['bias %'].quantile(.1):+.1f} to "
                f"{s['bias %'].quantile(.9):+.1f} %). Bins where Q exceeded hplib's full-load output: {100 * Y['over'].mean():.1f} %."]
    Y, dd = res[0][2], res[0][3]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].scatter(dd["P"] * 0.5, dd["P_hat"] * 0.5, s=3, alpha=.3)
    m = float(dd["P"].max() * 0.5)
    ax[0].plot([0, m], [0, m], "k--", lw=.8)
    ax[0].set(xlabel="measured HP electricity (kWh/day)", ylabel="hplib Q/COP (kWh/day)", title="daily, group 1")
    b = score(dd, "T bin")
    ax[1].bar(range(len(b)), b["bias %"])
    ax[1].set_xticks(range(len(b)), [str(i) for i in b.index], rotation=30)
    ax[1].set(ylabel="bias % (daily)", title="bias by outdoor temperature")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / "figures" / f"hplib_conversion.{ext}", dpi=150)
    S.to_csv(out / "hplib_spf.csv", index=False)
    rows = [{"exp_id": cfg["exp_id"], "split_seed": h["seed"], "dataset": f"EoH {h['season']}", "target": "P_el_hp",
             "method": f"hplib_generic_g{g}_{sz}", "anchor": lvl, "metric": k, "value": float(v), "n_substations": 0,
             "n_hp_households": X["property"].nunique()}
            for g, sz, Y, dd in res for lvl, d in (("30min", Y), ("daily", dd))
            for k, v in score(d).iloc[0].items() if k in ("WAPE %", "bias %")]
    pd.DataFrame(rows).to_csv(out / "metrics.csv", index=False)
    (out / "hplib_check.md").write_text("\n\n".join(txt) + "\n", encoding="utf-8")
    print(f"wrote {out / 'hplib_check.md'}")


if __name__ == "__main__":
    sys.exit(main())
