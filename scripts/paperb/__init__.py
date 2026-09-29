"""Protocol v1 (iteration 02a) implementation for Paper B. See configs/protocol_v1.yaml."""
import copy
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path):
    """Load a protocol config. A file with `base:` is merged onto its base; `apply_quick: true`
    then applies the base's `quick:` block (dotted keys, e.g. `grid.size`)."""
    with open(ROOT / path) as fh:
        cfg = yaml.safe_load(fh)
    if "base" in cfg:
        top = {k: v for k, v in cfg.items() if k not in ("base", "apply_quick")}
        quick = cfg.get("apply_quick", False)
        cfg = load_config(cfg["base"])
        if quick:
            for key, val in cfg["quick"].items():
                *head, last = key.split(".")
                d = cfg
                for h in head:
                    d = d[h]
                d[last] = copy.deepcopy(val)
        cfg.update(top)
    return cfg


def git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001 - not a git checkout
        return "unknown"
