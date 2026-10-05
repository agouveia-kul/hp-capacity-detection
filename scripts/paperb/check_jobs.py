"""Merge-readiness check of a queue's jobs folder (05b Stage 1, two machines): per arm and family, how many of the config's jobs
are done / failed / missing, on which device and host they ran, and whether every done job left at least one result frame.
Read-only.

    python scripts/paperb/check_jobs.py --config configs/iter05b_stage1.yaml [--families rawseries,tabpfn] [--expect-device rawseries=cuda,tabpfn=cuda]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml  # noqa: E402

from paperb import ROOT  # noqa: E402
from paperb.run_queue import FRAMES, jobs  # noqa: E402


def check(q, out, families=None, expect=None):
    J = out / "jobs"
    rows, problems = [], []
    sel = [j for j in jobs(q) if families is None or j["family"] in families]
    for (arm, fam) in sorted({(j["arm"], j["family"]) for j in sel}):
        js = [j for j in sel if (j["arm"], j["family"]) == (arm, fam)]
        done = {j["id"]: json.loads((J / f"{j['id']}.done").read_text()) for j in js if (J / f"{j['id']}.done").exists()}
        failed = [j["id"] for j in js if (J / f"{j['id']}.failed").exists() and j["id"] not in done]
        missing = [j["id"] for j in js if j["id"] not in done and j["id"] not in failed]
        no_frames = [i for i in done if not any((J / f"{i}.{k}.parquet").exists() for k in FRAMES)]
        dev = Counter(d.get("device", "cpu (not recorded)") for d in done.values())
        host = Counter(d.get("host", "?") for d in done.values())
        rows.append({"arm": arm, "family": fam, "jobs": len(js), "done": len(done), "failed": len(failed), "missing": len(missing),
                     "devices": dict(dev), "hosts": dict(host), "done_without_frames": len(no_frames)})
        want = (expect or {}).get(fam)
        wrong = [i for i, d in done.items() if want and d.get("device", "cpu") != want]
        for label, ids in (("failed", failed), ("missing", missing), ("done without result frames", no_frames), (f"device != {want}", wrong)):
            if ids:
                problems.append(f"{arm}/{fam}: {len(ids)} {label}: " + ", ".join(sorted(ids)[:8]) + (" ..." if len(ids) > 8 else ""))
    return rows, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--families", default=None)
    ap.add_argument("--expect-device", default=None, help="family=device,... e.g. rawseries=cuda,tabpfn=cuda")
    a = ap.parse_args()
    q = yaml.safe_load(open(ROOT / a.config))
    expect = dict(x.split("=") for x in a.expect_device.split(",")) if a.expect_device else None
    rows, problems = check(q, ROOT / q["out_dir"], set(a.families.split(",")) if a.families else None, expect)
    print("| arm | family | jobs | done | failed | missing | devices | hosts | done without frames |\n|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['arm']} | {r['family']} | {r['jobs']} | {r['done']} | {r['failed']} | {r['missing']} | {r['devices']} | {r['hosts']} | {r['done_without_frames']} |")
    print("\n" + ("\n".join(problems) if problems else "OK: every selected job is done, with result frames" + (" on the expected device" if expect else "") + "."))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
