"""Overnight queue (iteration 05a, Task 4b): kill mid-run and relaunch gives the merged metrics of an uninterrupted run, finished
jobs are skipped, a failing job is logged and skipped, and --retry-failed reruns only the failed jobs. Toy runner, no pool data."""
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "scripts" / "paperb" / "run_queue.py"
SEEDS = [0, 1, 2]


def write_queue(tmp, name):
    cfg = {"exp_id": name, "out_dir": str(tmp / name), "workers": 1, "sys_path": [str(ROOT / "tests")],
           "families": {"physics": {}, "linear": {"models": ["Lasso", "Ridge"]}},
           "arms": [{"name": "toy", "config": "tests/fixtures/toy_queue_arm.yaml", "runner": "toy_queue_runner:run_seed",
                     "seeds": SEEDS, "families": ["physics", "linear"]}]}
    p = tmp / f"{name}.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p, tmp / name


def launch(cfg, env, *args):
    return subprocess.Popen([sys.executable, str(QUEUE), "--config", str(cfg), *args], env={**os.environ, **env},
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def merged(out):
    m = pd.read_csv(out / "toy" / "metrics.csv")
    return m.sort_values(["family", "split_seed", "method"]).reset_index(drop=True)


@pytest.fixture
def env(tmp_path):
    return {"TOY_LOG": str(tmp_path / "calls.log"), "TOY_SLEEP": "0", "TOY_FAIL": str(tmp_path / "fail.txt")}


def test_kill_and_resume_equals_uninterrupted(tmp_path, env):
    ref_cfg, ref_out = write_queue(tmp_path, "ref")
    p = launch(ref_cfg, env)
    assert p.wait(timeout=300) == 0, p.stdout.read()
    want = merged(ref_out)
    assert len(want) == 3 * (3 + 2) and set(want["family"]) == {"physics", "linear"}               # per seed: 3 physics-job rows + 2 models

    cfg, out = write_queue(tmp_path, "killed")
    p = launch(cfg, {**env, "TOY_SLEEP": "2", "TOY_LOG": str(tmp_path / "calls2.log")})
    jobs = out / "jobs"
    t0 = time.time()
    while not list(jobs.glob("*.done")) and time.time() - t0 < 120:                                   # wait for the first finished job
        time.sleep(0.2)
    p.kill()
    p.wait()
    done_before = {f.name: f.read_text() for f in jobs.glob("*.done")}
    assert 1 <= len(done_before) < 6 and not (out / "toy" / "metrics.csv").exists()                   # crashed mid-run: nothing merged
    calls_before = len(Path(tmp_path / "calls2.log").read_text().splitlines())
    p = launch(cfg, {**env, "TOY_LOG": str(tmp_path / "calls2.log")})
    assert p.wait(timeout=300) == 0, p.stdout.read()
    assert {f.name: f.read_text() for f in jobs.glob("*.done") if f.name in done_before} == done_before   # finished jobs untouched
    calls_after = len(Path(tmp_path / "calls2.log").read_text().splitlines())
    assert calls_after - calls_before == 6 - len(done_before)                                          # only the unfinished jobs ran again
    pd.testing.assert_frame_equal(merged(out), want)
    assert "remaining 0" in (out / "STATUS.md").read_text()


def test_failed_job_is_skipped_and_retry_failed_reruns_only_it(tmp_path, env):
    cfg, out = write_queue(tmp_path, "fail")
    Path(env["TOY_FAIL"]).write_text("1")
    p = launch(cfg, env)
    assert p.wait(timeout=300) == 0, p.stdout.read()
    assert len(list((out / "jobs").glob("*.failed"))) == 2 and len(list((out / "jobs").glob("*.done"))) == 4   # seed 1, both families
    status = (out / "STATUS.md").read_text()
    assert "FAILED" in status and "toy failure for seed 1" in status and "failed 2" in status
    n_calls = len(Path(env["TOY_LOG"]).read_text().splitlines())
    p = launch(cfg, env)                                                                               # plain relaunch: nothing is retried
    assert p.wait(timeout=300) == 0
    assert len(Path(env["TOY_LOG"]).read_text().splitlines()) == n_calls and len(list((out / "jobs").glob("*.failed"))) == 2
    Path(env["TOY_FAIL"]).unlink()
    p = launch(cfg, env, "--retry-failed")
    assert p.wait(timeout=300) == 0, p.stdout.read()
    assert len(Path(env["TOY_LOG"]).read_text().splitlines()) == n_calls + 2                           # only the two failed jobs
    assert not list((out / "jobs").glob("*.failed")) and len(list((out / "jobs").glob("*.done"))) == 6
    assert set(merged(out)["split_seed"]) == set(SEEDS)
