"""02b determinism: the quick config must give value-identical metrics.csv with 1 worker (28 threads) and with
4 workers (7 threads each). Needs the B* pool cache (data/_paperb/pools/bstar_2023*.parquet); ~4 min."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
needs_pool = pytest.mark.skipif(not (ROOT / "data" / "_paperb" / "pools" / "bstar_2023_meta.parquet").exists(),
                                reason="B* pool cache not built")


def _run(tmp_path, workers):
    out = tmp_path / f"w{workers}"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "paperb" / "run_benchmark.py"), "--config", "configs/iter02b_quick.yaml",
                    "--set", f"out_dir={out}", f"feature_cache_dir={tmp_path / 'features'}_w{workers}", f"parallel.workers={workers}",
                    "split.seeds=[0,1,2,3]", "models=[XGBoost,Ridge,SVR]", "anchors=[none,size_peak]"], cwd=ROOT, check=True)
    return pd.read_csv(out / "metrics.csv")


@needs_pool
def test_metrics_identical_for_1_and_4_workers(tmp_path):
    m1, m4 = _run(tmp_path, 1), _run(tmp_path, 4)
    assert len(m1) > 500 and m1["split_seed"].nunique() == 4
    pd.testing.assert_frame_equal(m1, m4, check_exact=True)
