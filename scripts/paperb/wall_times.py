"""Actual wall time of a queue's jobs per arm and per machine, from the `.done` markers (`seconds`, `start`, `end`, `host`,
`device`). Wall time = the length of the union of the jobs' [start, end] intervals on that machine (busy time, idle gaps between
sessions excluded); span = first start to last end. Markers written before commit a64e65f carry no host: they ran on the CPU of
machine A and are labelled so (`--unrecorded-host`). Jobs outside the config's job list (e.g. the A8 probe's CatBoost / GP jobs) are
listed separately and not counted. Read-only on the jobs folder.

    python scripts/paperb/wall_times.py --config configs/iter05b_stage1.yaml [--unrecorded-host P240003]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from paperb import ROOT  # noqa: E402


def busy_hours(iv):
    """Length of the union of [start, end] intervals, in hours."""
    tot, cur_s, cur_e = 0.0, None, None
    for s, e in sorted(iv):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                tot += (cur_e - cur_s).total_seconds()
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        tot += (cur_e - cur_s).total_seconds()
    return tot / 3600


def load(jobs, unrecorded):
    rows = []
    for f in jobs.glob("*.done"):
        d = json.loads(f.read_text())
        parts = f.stem.split("__")
        rows.append({"job": f.stem, "arm": parts[0], "family": parts[-1], "host": d.get("host", unrecorded),
                     "device": d.get("device", "cpu"), "seconds": d["seconds"],
                     "start": pd.Timestamp(d["start"]), "end": pd.Timestamp(d["end"])})
    return pd.DataFrame(rows)


def main(cfg_path, unrecorded):
    q = yaml.safe_load(Path(cfg_path).read_text())
    out = ROOT / q["out_dir"]
    J = load(out / "jobs", unrecorded)
    ids = {f"{a['name']}__s{s}__d{d}__n{n}__{f}" for a in q["arms"] for f in a["families"] for s in a["seeds"]   # = run_queue.jobs ids
           for n in a.get("n", ["all"]) for d in ([0] if n == "all" else a.get("draws", [0]))}
    extra = J[~J["job"].isin(ids)]
    J = J[J["job"].isin(ids)]
    if missing := len(ids) - len(J):
        print(f"{missing} jobs of the list have no .done marker yet")
    rows = []
    for (arm, host), g in J.groupby(["arm", "host"]):
        rows.append({"arm": arm, "host": host, "devices": ",".join(sorted(g["device"].unique())), "jobs": len(g),
                     "job_hours": round(g["seconds"].sum() / 3600, 1), "wall_hours_busy": round(busy_hours(zip(g["start"], g["end"])), 1),
                     "first_start": g["start"].min().isoformat(), "last_end": g["end"].max().isoformat()})
    for host, g in J.groupby("host"):
        rows.append({"arm": "all", "host": host, "devices": ",".join(sorted(g["device"].unique())), "jobs": len(g),
                     "job_hours": round(g["seconds"].sum() / 3600, 1), "wall_hours_busy": round(busy_hours(zip(g["start"], g["end"])), 1),
                     "first_start": g["start"].min().isoformat(), "last_end": g["end"].max().isoformat()})
    T = pd.DataFrame(rows)
    fam = J.groupby(["arm", "family"])["seconds"].agg(jobs="size", job_hours=lambda s: round(s.sum() / 3600, 1),
                                                      median_job_h=lambda s: round(s.median() / 3600, 2), max_job_h=lambda s: round(s.max() / 3600, 2)).reset_index()
    T.to_csv(out / "wall_times.csv", index=False)
    fam.to_csv(out / "job_times_family.csv", index=False)
    print(T.to_string(index=False), "\n")
    print(fam.to_string(index=False), "\n")
    if len(extra):
        print("not in the job list (not counted):", ", ".join(sorted(extra["job"])))
    return T, fam


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--unrecorded-host", default="P240003", help="host of markers without one (CPU jobs before a64e65f, machine A)")
    a = ap.parse_args()
    main(a.config, a.unrecorded_host)
