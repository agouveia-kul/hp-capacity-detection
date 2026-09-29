# Iteration 03b — Fair test of ML against the physics estimator: runs and results
**Goal:** Run the fair test on `HP_Peak` (B\*, 20 seeds) with three added physics rows (non-TCL-corrected, bias-calibrated, cross-fitted) and apply the pre-registered Task 6 criterion.

**Branch / commit:** iter/03b-fair-test-runs @ COMMIT (code 600fdf4; LC fix, tables and results on top). Branched from `main` after 03a.

**Changed:** ≈ 180 logic lines (Tasks 1–4 + harness): `physics.py` +54, `run_benchmark.py` +73/−23, `train.py` +15 (`cv_wape`), `residual.py` +6, `features_netfit.py` +5. Listed separately: `fair_test_tables.py` 264, `select_lc_specs.py` 62, `tests/test_fair_test_03b.py` 154 (**56/56 tests pass**), 4 new configs (`iter03b_lc.yaml` generated) + `protocol_v1.yaml` +4, `.gitignore` +4, DECISIONS.md +4. *Generated:* `results/iter03b_fair_test/` (`arm_main/metrics.csv` 61 MB and `arm_lc/metrics_lc.csv` 33 MB are committed gzipped), `results/iter03b_quick/`, `data/_paperb/features/`. `data/` outside `_paperb/` and `models/` unmodified (mtime check).

**Results** (HP_Peak, test, WAPE %, median [5–90 %] over 20 seeds, 20 test HP households/seed; wall time: main 8 919 s, B 352 s, LC 1 724 s = 3.05 h vs 7.7 h planned; quick 323 s)

| row | 02b / 03a | 03b overall | ≤15 % | 15–35 % | 35–65 % | >65 % |
|---|---|---|---|---|---|---|
| Paper A s_h/m_h | 28.8 (03a, seed 0) | 43.2 [24–64] | 66 | 30 | 21 | 16 |
| `paperA_cal` (× exp(b), b = −0.38) | – | 21.3 [18–31] | 27 | 17 | 18 | 22 |
| `paperA_corr` (non-TCL corrected) | – | 23.1 [17–33] | 29 | 20 | 18 | 15 |
| `paperA_corr_all` / `_corr_cal` | – | 23.9 / 22.8 | 30 / 28 | 20 / 20 | 18 / 17 | 15 / 15 |
| slope + base (**best physics overall**) | 21.1 (02b) | 21.1 [15–32] | 27 | 18 | 16 | 14 |
| slope-only / cal. delta / HDH | 22.3 (02b) | 22.3 / 22.7 / 22.9 | 27 / 30 / 29 | 17 / 15 / 16 | 16 / 15 / 15 | 17 / 17 / 17 |
| anchor-only Linear [size+peak] | – | 26.0 | 36 | 22 | 16 | 13 |
| XGBoost direct, whdd, size_peak | 25.6 (02b) | 25.6 [22–36] | – | – | – | – |
| best direct by inner CV: Lasso [size] both | – | 21.4 [16–31] | 27 | 18 | 15 | 14 |
| best residual by inner CV: Lasso [size_peak] netfit | – | 19.9 [15–31] | 24 | 16 | 16 | 15 |
| *descriptive, test-best:* Ridge [size_peak] netfit direct | – | 19.1 [15–29] | – | – | – | – |

**Task 6** (paired per seed vs the best physics row of each scope): **overall 4 of 166 ML configurations beat physics** (Lasso / ElasticNet / Ridge, direct, `netfit`, anchor size or size_peak; 16/20 seeds, ΔWAPE −1.7 to −2.3 pp vs slope + base); **>65 %: 7**; the other three bins: **0**. None of the inner-CV-selected configurations beats it overall (Lasso residual 8/20, +0.4 pp; Lasso both 8/20, +0.4; SVR 10/20, −0.1). B (10 seeds, threshold 8/10): 1 of 12 (Ridge residual, 9/10, −1.6 pp vs `paperA_cal`). Learning curve: direct ML is worse than physics at n ≤ 32 (+0.6 to +7.8 pp); residual Lasso is level at n = 16 (−1.9 pp, 7/14 feasible designs), n = 32 (+1.2) and n = 48 (−0.2, 16/30), and −2.1 pp at all (6/10 seeds, not a win). Median P̂/y at p = 0.05: 1.93 (`paperA_sh_mh`) vs 1.05 (`paperA_corr`); at p = 1: 1.13 vs 1.09. s₀(fill) = 0.0055 kW/K per dwelling; adding the HP households' own load moves it +15 % [9–18]. Cross-fit fold m_h / full: 0.976 [0.946–0.988] … 1.030 [1.017–1.050].

**Assumptions & deviations:**
- Physics arm = the main run's own physics rows (same seeds, independent of ML specs). Main: 10 workers × 2 threads, two waves.
- Task 3, train substations (no single fold): the pilot excludes the substation's own HP members; inner substations of fold k use the pilot without fold k, as specified. s₀ is not cross-fitted (it averages ≈ 970 dwellings, which include a substation's fill members).
- s₀ fit: fill dwellings use KLO temperature; `_all` uses the dwelling-weighted station mix. Corrected slope ≤ 0 → predict 0, counted (`paperA_corr` 1 [0–3], `_all` 2 [1–6] of 130 test substations).
- Paper A bins use actual p = n_HP / size; test substations per bin 75 / 40 / 10 / 5 (thin at the top).
- Best physics row = per scope, median WAPE over the Task 5 physics rows (HDH reported, never best). "Best" ML rows (Table 1, LC) are picked by inner-CV WAPE (`cv_wape`, pooled out-of-fold, kW scale), never test. LC "family" = linear / kernel (SVR) / tree; 5 specs.
- Berchtoldstag changes the `netfit` features (cache key `FEATURE_VERSION`), so 03a `netfit` numbers are not reproduced exactly; the 02b whdd XGBoost row (25.6) is.
- The calibration is the specified mean of log ratios (equal weight per substation), not WAPE-optimal.

**Problems found:**
- **`paperA_sh_mh` WAPE is 43 %, not Paper A's 19.3 %:** 75 of 130 test substations sit at ≤ 15 % penetration (WAPE 66 %); per-seed WAPE spans 29–84 %. I lack Paper A's per-bin values, so the comparison is open.
- **LC at n = 16:** in 16 of 30 designs no inner fold has enough HP households (`min_station_pool` = 3), so grouped CV is infeasible; their ML specs are skipped and listed (`dropped_cells_lc.csv`). The first LC launch crashed on 3 of 10 seeds for this reason; I fixed the skip rule and reran all 10.
- **Multiplicity:** the four "beats" are test-identified among 166 configurations; the criterion was pre-registered per configuration.
- `paperA_corr` removes the low-p bias but is not more accurate than `paperA_cal` (23.1 vs 21.3): a constant scale gets most of the correction.
- Residual models are close to the constant intercept (ridge α ≈ 10⁵ in the quick run); `XGBoost_mono` (52 s/fit) shows no gain over XGBoost (36 s). Linear models under `log` are worse (Lasso netfit 31 vs 19 %); SVR / XGBoost improve.

**Decisions for Alex:**
1. **Paper's lead.** Met overall by 4 of 166 configurations (regularised linear, `netfit`, size anchor), and in the >65 % bin by 7; not by any inner-CV-selected one, nor in the other bins. *Recommended:* lead with identifiability and physics-derived features; report the ML gain as ≤ 2 pp WAPE (≈ 10 % relative), hypothesis-generating, to be confirmed on the 04 targets.
2. **`paperA_corr` as the physics reference for 04/05?** *Recommended:* not alone. Carry `slope_base` (best in-domain) and `paperA_corr` (label-free, transfers without target labels); report `paperA_cal` to show how much is a constant scale.
3. **What carries forward.** *Recommended:* feature set `netfit` (`both` adds nothing; `whdd` direct is 2–13 pp worse); regularised linear direct with anchor `size` (Lasso; `peak` adds nothing) as primary, Lasso residual as challenger; drop `XGBoost_mono` and FFNN, keep XGBoost as the tree reference.
