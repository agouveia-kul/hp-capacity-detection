"""Write <out_dir>/environment.txt: Python, key library versions, git commit,
and `pip freeze` diffed against requirements.txt.

    python scripts/record_environment.py --config configs/iter00_full.yaml
"""
import argparse
import importlib
import platform
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KEY_LIBS = ["numpy", "pandas", "sklearn", "xgboost", "scipy", "hyperopt", "tensorflow", "keras"]


def _pins(lines):
    out = {}
    for ln in lines:
        ln = ln.strip()
        if ln and not ln.startswith("#") and "==" in ln:
            k, v = ln.split("==", 1)
            out[k.lower().replace("_", "-")] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(open(ap.parse_args().config))
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    inst, req = _pins(freeze.splitlines()), _pins((ROOT / "requirements.txt").read_text().splitlines())

    L = [f"python: {sys.version}", f"platform: {platform.platform()}",
         f"git commit: {git('rev-parse', 'HEAD')} (branch {git('rev-parse', '--abbrev-ref', 'HEAD')})",
         f"git dirty files: {len(git('status', '--porcelain').splitlines())}", "", "key libraries:"]
    for lib in KEY_LIBS:
        try:
            L.append(f"  {lib:12s} {importlib.import_module(lib).__version__}")
        except Exception as e:  # noqa: BLE001
            L.append(f"  {lib:12s} not importable ({type(e).__name__})")
    L += ["", "pip freeze vs requirements.txt:"]
    diff = [f"  version differs: {k} installed {inst[k]} / required {v}" for k, v in req.items() if k in inst and inst[k] != v]
    diff += [f"  missing (required, not installed): {k}=={v}" for k, v in req.items() if k not in inst]
    diff += [f"  extra (installed, not in requirements): {k}=={v}" for k, v in inst.items() if k not in req]
    L += diff or ["  identical"]
    L += ["", "full pip freeze:", *["  " + x for x in freeze.splitlines()]]
    out = ROOT / cfg["out_dir"] / "environment.txt"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:30]))


if __name__ == "__main__":
    main()
