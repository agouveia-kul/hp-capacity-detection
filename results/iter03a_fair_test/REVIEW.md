# Iteration 03a — Fair test of ML against the physics estimator: code and tests
**Goal:** Build (not run) a fair test of ML on `HP_Peak`: Paper A's estimator s_h/m_h, a net-load-fit feature set, small-N models, residual learning on P̂_A and a learning-curve harness, with WAPE as the primary metric.

**Branch / commit:** iter/03a-fair-test-code @ 3e6470e (code; Task 0 bookkeeping ac15ba5); smoke run, timing probe and this REVIEW committed on top. Branched from `main` after 02b.

**Changed:** ≈ **560 logic lines** incl. docstrings (budget ~600): `run_benchmark.py` +150/−46 (spec loop, Paper A pilots, residual, cap-def check, learning curve), `features_netfit.py` 94 (new), `physics.py` +62, `train.py` +61/−13, `learning_curve.py` 50, `residual.py` 42, `tables.py` +42 (ablation), `make_paperA_fixture.py` +28 (`--pilot`), `metrics.py` 17, `substations.py` +10, `summarise.py` +7. Tests: `tests/test_fair_test.py` (15 tests), fixture `tests/fixtures/paperA_pilot_fixture.npz`; **48/48 pass**. Configs: `iter03_quick.yaml`, `iter03_timing.yaml`, `protocol_v1.yaml` (+new keys, defaults = 02b grid), `iter02b_ffnn.yaml` (`ffnn.enabled`). CLAUDE.md §1/§4/§10, DECISIONS.md (+5), `requirements.txt` (+`holidays==0.105`, `python-dateutil` 2.8.2→2.9.0.post0, pulled in by it). *Generated:* `results/iter03_quick/`, `results/iter03_timing/`, `data/_paperb/features/` (new caches). `data/` outside `_paperb/` and `models/` are unmodified (checked by mtime).

**Results** (HP_Peak, test, WAPE % / MAPE %; **1 seed, not interpreted**). Smoke run: **121 s** wall with cached features, ≈ 4 min cold. Timing probe (seed 0, full grid, 50 evals, 7 threads): **376 s**.

| | 02b B\* (20 seeds, WAPE recomputed from predictions) | 03a quick (seed 0, size 10) | 03a probe (seed 0, full grid, netfit, size_peak) |
|---|---|---|---|
| Paper A `paperA_sh_mh` (pilot = 64 train HP hh) | – | 21.7 / 39.5 | 28.8 / 53.9 |
| `paperA_sh_mh_station` (fallbacks: 0) | – | 22.6 / 41.5 | 29.2 / 55.6 |
| physics slope-only / slope+base | 22.3 / 34.9 · 21.1 / 36.4 | 25.4 / 27.4 | 24.3 / 34.9 |
| XGBoost direct [size_peak] | 25.6 (whdd) / 47.8 | 47.1 (whdd), 26.7 (netfit) | 31.9 (netfit, log) |
| best residual on P̂_A | – | 27.2 (Ridge/XGB, netfit) | 27.2 (Lasso, netfit) |
| learning curve n = 16 / 32: P̂_A · residual | – | 21.0 · 23.7 (Ridge) | 30.6 · 29.5 (XGB) |
| pilot m_h (°C⁻¹) all / KLO / Hg | Paper A: 0.0187 (split 0), 0.0178 median | 0.01931 / 0.01933 / 0.01863 | same |
| P̂_A vs Paper A capacity def. (`HP_Peak_A`) | – | 21.76 (vs 21.74) | 28.85 (vs 28.82) |

**Assumptions & deviations:**
- **Pilot temperature.** The full pilot spans stations (KLO 46, Hg 12, MqO/others 6 in seed 0); its daily T is the capacity-weighted mean of the members' stations. Single-station pilots use that station's T.
- **Pilot is in-sample for train/inner residual targets.** z on train and inner substations uses the seed's full pilot, which contains those households; test is clean (as specified).
- **Residual models keep an intercept**: their "all-zero" is a constant log-bias exp(b)·P̂_A, not P̂_A; P̂_A is reported as the zero-residual row. CV loss = MSE of the model output (kW for direct models, also under `log`; z for residual).
- netfit: `R2_h` = Paper A's arm R² below T_h (not the all-day R²); `n_heat_days` counts days below T_h(all); CH-ZH holidays for all stations, UTC days (the package has no Berchtoldstag 2 Jan); kW columns carry scale, so the `none` anchor arm is not scale-free for netfit.
- WAPE lives in `paperb/metrics.py` (wraps `hp_capacity.compute_metrics`, whose shared API is unchanged). `XGBoost_mono` is a registry alias; skipped on `whdd` (no `nf_*` column → identical to XGBoost).
- Learning curve: simple random subsample (not station-stratified), `all` = one draw and recomputed (not reused from the main run); rows in `metrics_lc.csv`.
- **Feature-cache key now hashes memberships and feature sets** (sub_ids alone collide across learning-curve draws); 02b caches are not reused.
- FFNN gated by `ffnn.enabled` (default false); `iter02b_ffnn.yaml` sets it true, so 02b stays reproducible.

**Problems found:**
- **P̂_A over-estimates at low penetration**: median P̂/y = 1.75 at p = 0.05, 1.28 at 0.1, ≈ 1.0 at p ≥ 0.5 (probe). The fill households' temperature response enters s_h (cf. Paper A's zero-HP control). slope-only, calibrated with an intercept, has 0.7–1.1. This is what the residual model should learn.
- **02b's MAPE overstated the physics–ML gap:** in WAPE (B\*, 20 seeds) slope+base 21.1 vs XGBoost 25.6 (MAPE 36 vs 48).
- `XGBoost_mono` is 2.8× (probe) to 17× (quick, 28 threads) slower than XGBoost.
- MqO never has ≥ 3 test HP households, so the station fallback never fires on test in seed 0; in the learning curve (n = 16) Hg falls back.
- In the quick grid (size 10 only), anchor-only [size+peak] = [peak].

**Decisions for Alex:**
1. **Pilot:** all train HP households (multi-station, cap-weighted T) or station-matched? They agree within 1 pp WAPE; station-matched adds a fallback rule. *Recommended:* **all-train pilot as the headline**, station-matched as a sensitivity row.
2. **Invalid P̂_A** (s_h ≤ 0 or failed fit → predict 0, counted; 0 cases so far) and **capacity definition:** the two definitions differ only in the sample set (raw valid vs gap-filled 15-min), −0.001 % median per household, max 0.22 %; WAPE moves by 0.03 pp. *Recommended:* **keep predict-0 + count, score against `HP_Peak`**, and footnote Paper A's definition.
3. **03b budget.** As specified (3 anchors × 3 feature sets × {direct × 2 transforms, residual} × 7 models, +`XGBoost_mono` on all anchors, learning curve on 20 seeds × 3 draws, B 10 seeds) ≈ **10.8 h** (4 workers; main 4.5 h, mono 2.5 h, learning curve 3.5 h, B 0.3 h; ±30 %, probe had no worker contention). *Recommended cuts to ≈ 7.7 h:* `XGBoost_mono` only on `size_peak` (0.8 h) and the learning curve on 10 seeds (2.1 h).
4. **Residual intercept:** keep it (bias correction, as now) or force z through 0 so the all-zero model is P̂_A? *Recommended:* **keep the intercept** (it is the fix for the low-p bias above) and report P̂_A alongside.
