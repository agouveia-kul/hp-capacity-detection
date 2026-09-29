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
        deep_update(cfg, top)
    return cfg


def deep_update(cfg, top):
    """Merge dict `top` onto `cfg` in place, recursing into dicts (lists and scalars are replaced)."""
    for k, v in top.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            deep_update(cfg[k], v)
        else:
            cfg[k] = copy.deepcopy(v)
    return cfg


def set_dotted(cfg, assignments):
    """Apply `a.b=value` overrides (value parsed as YAML), e.g. ['parallel.workers=1', 'split.seeds=[0, 1]']."""
    for a in assignments:
        key, val = a.split("=", 1)
        *head, last = key.split(".")
        d = cfg
        for h in head:
            d = d.setdefault(h, {})
        d[last] = yaml.safe_load(val)
    return cfg


def git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001 - not a git checkout
        return "unknown"
