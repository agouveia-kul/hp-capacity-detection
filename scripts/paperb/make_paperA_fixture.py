"""Build tests/fixtures/paperA_fixture.npz: Paper A's own fit outputs on six B* HP households.

Phase 1 (this repo) stores each household's 15-min station temperature, HP series and net series
(HP + own load) and its robust HP peak. Phase 2 runs in a child process with ONLY Paper A's scripts/ on
sys.path (both repos have a module named hp_common), applies Paper A's daily reduction
(outputs._daily_pools), net-load fit (outputs._evaluate: fit_hockey_stick with T_BALANCE_BOUNDS) and SF
arm (utils._sf_arm), and adds the outputs to the fixture. Paper A is only read.

    python scripts/paperb/make_paperA_fixture.py --config configs/protocol_v1.yaml
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "paperA_fixture.npz"
N_HH = 6


def phase_paper_a(repo):
    """Child process: Paper A code on the stored inputs."""
    sys.path.insert(0, str(Path(repo) / "scripts"))
    import pandas as pd
    import utils as U
    from hp_common import T_BALANCE_BOUNDS, fit_hockey_stick
    f = dict(np.load(FIXTURE, allow_pickle=False))
    idx = pd.date_range(str(f["start"]), periods=f["T"].shape[1], freq="15min")
    out = []
    for T15, hp15, net15, cap in zip(f["T"], f["hp"], f["net"], f["cap"]):
        T = pd.Series(T15, index=idx).resample("D").mean().to_numpy()                 # _daily_pools
        hp = pd.DataFrame(hp15[None].T, index=idx).resample("D").mean().to_numpy().T[0]
        net = pd.DataFrame(net15[None].T, index=idx).resample("D").mean().to_numpy().T[0]
        ok = np.isfinite(T)
        T, hp, net = T[ok], hp[ok], net[ok]
        base, sh, th, r2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)                 # _evaluate
        b, m, sfc, r2s = U._sf_arm(T, np.clip(hp / cap, 0, 1), th, "h")
        out.append([base, sh, th, r2, b, m, sfc, r2s])
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    np.savez_compressed(FIXTURE, **f, paperA=np.array(out), paperA_commit=commit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--paper-a-phase")
    a = ap.parse_args()
    if a.paper_a_phase:
        return phase_paper_a(a.paper_a_phase)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from paperb import ROOT, load_config
    from paperb.pools import build_pool
    cfg = load_config(a.config)
    pool = build_pool("bstar", cfg)
    m = pool.meta[pool.meta["role"] == "hp"]
    pick = [m.index[m["source"] == s][i] for s, i in (("heapo", 0), ("heapo", 5), ("heapo", 20), ("kaiser_paired", 0),
                                                       ("kaiser_paired", 7), ("kaiser_sfh", 0))]
    assert len(pick) == N_HH
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(FIXTURE, hh=np.array(pick), start=str(pool.index[0]),
                        T=np.stack([pool.temp[m.at[h, "station"]].to_numpy() for h in pick]).astype(np.float32),
                        hp=np.stack([pool.hp[h].to_numpy() for h in pick]).astype(np.float32),
                        net=np.stack([(pool.hp[h] + pool.own[h]).to_numpy() for h in pick]).astype(np.float32),
                        cap=m.loc[pick, "hp_peak"].to_numpy(float))
    repo = (ROOT / cfg["paper_a_repo"]).resolve()
    subprocess.run([sys.executable, __file__, "--paper-a-phase", str(repo)], check=True, cwd=repo)
    print(f"wrote {FIXTURE} ({FIXTURE.stat().st_size / 1e6:.1f} MB) with Paper A outputs from {repo}")


if __name__ == "__main__":
    main()
