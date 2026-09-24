# Data-driven heat-pump installed-capacity detection

Estimating the aggregated **installed heat-pump capacity** behind an LV
substation from its net load and ambient temperature with supervised models,
trained on synthetic substations and tested for transfer to unseen datasets.

## Contents

| Path | What |
|------|------|
| `HeatPumpDetection_clean.ipynb` | Main notebook: household hockey-stick fits, synthetic substation generation, feature sets (time-of-day, piecewise-linear coefficients, windowed HDD bins, PLS), model benchmark, XGBoost feature selection, Swiss → WPuQ transfer, real WPuQ feeder penetration sweep, penetration-gated ensemble, calibrated hockey-stick delta, FeederBW. |
| `scripts/hp_common.py` | Hockey-stick / bathtub fitting primitives. |
| `scripts/hp_pools.py` | Household pools (HEAPO, Swiss smart-meter, WPuQ) and substation sampling. |
| `scripts/hp_capacity.py` | Robust peak / installed-capacity helpers. |
| `src/heapo.py` | HEAPO dataset loader. |
| `models/` | Trained capacity models, selected feature list, hockey-delta calibration and ensemble gate. |
| `feature_cache/` | Cached windowed-HDD feature matrices (Swiss, German). |

`scripts/hp_common.py`, `hp_pools.py`, `hp_capacity.py` and `src/heapo.py` are
shared with **hp-sensitivity-paper**; the copies were identical at the split
(2026-09) and may diverge from here on.

## Data

Raw data is not in the repository. The notebook reads from `data/` (HEAPO,
Swiss smart-meter pool, WPuQ, FeederBW and their cached pools/features). On the
author's machine `data/` is a directory junction to a shared data folder.
Dataset licensing notes are kept in the **hp-sensitivity-paper** repository
(`LICENSING.md`).

## Related repositories

- **NILM** — the original PV installed-capacity work this repository was split from.
- **hp-sensitivity-paper** — physics-based estimation (bathtub fit + simultaneity factor).

## Setup

```bash
pip install -r requirements.txt
```
