"""Iteration 07 post-review additions (07 close-out, 2026-11-18). POST-REVIEW, NOT OF RECORD.

Reads saved outputs only (no refit, no new prediction): results/iter07_transfer/report/metrics_per_seed.csv (written by the frozen
iter07_report.py) and the 06 pilots.csv (s0, m_h per seed). Writes results/iter07_transfer/report/postreview/.

1. wape_nmae.csv / .md: the REVIEW's results rows with nMAE and WAPE (HL), transfer and in-pool, overall and in the <= 15 % bin.
2. bias.csv / .md: per direction and bin, the median over seeds of the set's mean signed error mean(pred - y) / max(y) * 100 for the
   physics rows with source s0 (paperA_corr, slope_base), with target s0 (paperA_corr@tgt_s0), paperA_sh_mh (no s0), H* and
   L1 TabPFN; next to the s0 and m_h values in use (06 pilots.csv: median [min-max] over seeds).
3. seed6.csv: T3 L4a vs L3 CNN per direction with seed 6 excluded (the collapsed GB L4a refit), by the brief's verdict rule.

    python scripts/paperb/iter07_postreview.py
"""
try:                                                                  # torch before pandas / pyarrow (see run_queue.py)
    import torch  # noqa: F401
except (ImportError, OSError):
    pass
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb.iter07_report import COMP, fmt, q, verdict  # noqa: E402

R07 = ROOT / "results" / "iter07_transfer" / "report"
OUT = R07 / "postreview"
DIR06 = ROOT / "results" / "iter06_hybrid_ladder"
ROWS = {"CH->GB": ["L2 tabpfn", "L1 cnn", "slope_base", "L4 cnn", "L1 tabpfn", "paperA_corr@tgt_s0", "calibrated_delta"],
        "GB->CH": ["L2 tabpfn", "L1 cnn", "slope_base", "L4 tabpfn", "paperA_corr@tgt_s0", "L3 linear", "paperA_sh_mh"]}
ROLE = {"L2 tabpfn": "H*", "L1 cnn": "D*", "slope_base": "L0ref", "L4 cnn": "06 hybrid", "L4 tabpfn": "06 hybrid"}
BIAS_ROWS = ["paperA_corr", "slope_base", "paperA_corr@tgt_s0", "paperA_sh_mh", "L2 tabpfn", "L1 tabpfn"]
CELLS = ["all", "pbin<=15", "pbin15-35", "pbin35-65", "pbin>65"]
SRC = {"CH->GB": ("a_ch", "a_gb"), "GB->CH": ("a_gb", "a_ch")}


def tab(df):
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)])


def pilots(arm):
    P = pd.read_csv(DIR06 / arm / "pilots.csv")
    P = P[(P["arm"] == arm) & (P["family"] == "physics") & (P["n"].astype(str) == "main")]
    s0 = P[P["pilot"] == "s0:paperA_corr"].groupby("split_seed")["s0"].first()
    mh = P[P["pilot"] == "all"].groupby("split_seed")["m"].first()
    return s0, mh


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    M = pd.read_csv(R07 / "metrics_per_seed.csv")
    tr, ip = M[M["label_def"] == "HL"], M[M["label_def"] == "inpool"]
    get = lambda D, dr, r, c, m: D[(D["direction"] == dr) & (D["row"] == r) & (D["cell"] == c)][m]  # noqa: E731
    w, lines = [], ["# 07 post-review additions (2026-11-18) — POST-REVIEW, NOT OF RECORD", ""]
    for dr, rows in ROWS.items():
        for r in rows:
            rec = {"direction": dr, "row": r, "role": ROLE.get(r, "outside the rules") + (" (DA)" if r.endswith("tgt_s0") else "")}
            for c in ("all", "pbin<=15"):
                for m in ("nmae", "wape"):
                    rec[f"{m} {c}"] = fmt(q(get(tr, dr, r, c, m)))
                    rec[f"in-pool {m} {c}"] = fmt(q(get(ip, dr, r, c, m)))
            w.append(rec)
    W = pd.DataFrame(w)
    W.to_csv(OUT / "wape_nmae.csv", index=False)
    lines += ["## 1. nMAE and WAPE on HL (%), median [5–90 %] over seeds; transfer and in-pool", "", tab(W), ""]

    b, s0rows = [], []
    for dr, (src, tgt) in SRC.items():
        (s0s, mhs), (s0t, mht) = pilots(src), pilots(tgt)
        s0rows.append({"direction": dr, "source s0 (kW/K)": fmt(q(s0s), 4), "target s0 (kW/K)": fmt(q(s0t), 4),
                       "source m_h": fmt(q(mhs), 4), "target m_h": fmt(q(mht), 4)})
        for r in BIAS_ROWS:
            b.append({"direction": dr, "row": r, **{c: round(float(get(tr, dr, r, c, "bias").median()), 1) for c in CELLS}})
    B, S0 = pd.DataFrame(b), pd.DataFrame(s0rows)
    B.to_csv(OUT / "bias.csv", index=False)
    S0.to_csv(OUT / "s0_mh.csv", index=False)
    lines += ["## 2. Bias: median over seeds of mean(pred − y) / max(y) (%), HL, by Paper A bin", "", tab(B), "",
              "s0 and m_h in use (06 pilots.csv, source train fillers / pilot homes; median [min–max] over seeds)", "", tab(S0), ""]

    s6 = []
    for dr, C in COMP.items():
        a, c = (tr[(tr["direction"] == dr) & (tr["row"] == x) & (tr["cell"] == "all")].set_index("split_seed")["nmae"] for x in ("L4 cnn", "L3 cnn"))
        for label, keep in (("all seeds (of record)", a.index), ("seed 6 excluded (not of record)", a.index.drop(6))):
            v, nneg, n, med = verdict(a.loc[keep], c.loc[keep])
            s6.append({"direction": dr, "step": "T3 L4a vs L3, CNN", "seeds": label, "seeds_A<B": nneg, "n": n, "median_rel_diff_pct": round(med, 1), "verdict": v})
    S6 = pd.DataFrame(s6)
    S6.to_csv(OUT / "seed6.csv", index=False)
    lines += ["## 3. T3 L4a vs L3 CNN without seed 6 (collapsed GB L4a refit)", "", tab(S6), ""]
    (OUT / "postreview.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"post-review additions in {OUT}")


if __name__ == "__main__":
    main()
