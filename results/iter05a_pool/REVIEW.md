# Iteration 05a-ii-a — R1–R8 rebuild, D4 diagnostics, queue, envelopes, smoke and timing probe (D5 pending)
> **Update 2026-10-01 (after the review decisions; the final 05a-ii REVIEW replaces this file after D5).** Flag renamed "filler-variability-limited" (same rule). Main pool now **384** homes (EOH2291 excluded: silent electricity 15 %). Replication = **temporal replication** Oct 2022 – 28 Sep 2023 (last full day; 363 days): **319** homes, 272 shared with the main pool, no fallback needed (≥ 300); EOH0836 does not reach 90 % coverage there. Envelopes: main 274 / 81 HP households used (train / test), test substations per bin 265 / 125 / 30 / 35; replication 226 / 61, 190 / 105 / 30 / 30. `zipfile -t` passes on all four EoH zips; Meteostat 03772 = "London Heathrow Airport" (WMO 03772, ICAO EGLL). The numbers below that say 385, 338 or "fusion-limited" are the superseded ones.
**Goal:** Apply the 05a-i review decisions, settle the D4 flag, and make the GB-EoH pools and the overnight queue ready; D5 waits for Alex to schedule it.

**Branch / commit:** iter/05a-gb-eoh-pool @ f4d85dc (code), results + this REVIEW in the next commit. **Not started: D5 and the final 05a-ii REVIEW** (they need the scheduled queue). The brief's ~450-line budget is exceeded, so this is the "05a-ii-a" stop.

**Changed** (~840 logic lines, tests excluded): `d4_diagnostics.py` 168 (rule in its docstring, committed before any run), `run_queue.py` 242 and `schedule_overnight.ps1` 52 (drafted on `wip/05a-ii`, tested now), `pools/gb_eoh.py` ~105, `iter05a_report.py` ~145, `envelopes_v11.py` 70, `runtime_estimate.py` 70, `fill_analog.py` 40, `run_benchmark.py` 19, `learning_curve.py` 16. Tests: `test_queue.py` (kill/resume, `--retry-failed`), `test_05a_ii.py` (zero-run, station fill, windows, Heathrow, own-station matching, D4 rule). **pytest 74 passed** (21 min). Configs: `pool_gb_eoh_{2122,2223,2223sep}`, `iter05_quick`, `iter05a_{overnight,timing,d5_quick_queue}`; CLAUDE.md §4, §6, §7, §10; `method_basis.md`; DECISIONS (R1–R8, D4 rule). Results: `d4_diagnostics.md`, `zero_runs.md`, `envelopes.md`, `runtime_estimate.md`, `eoh_selection.md`, `lcl_audit.md`, `mapping.md`, smoke `metrics.csv`. Free disk 423 GB.

**Results** (D5 not run)

| item | 05a-i | 05a-ii |
|---|---|---|
| EoH main window, homes | Oct 2021, 295 (≥ 95 %) | **Nov 2021, 385** (≥ 90 %; 388 before dropping 5 unfillable stations). Candidates Jun→Jan: 225, 275, 315, 355, 373, **388**, 379, 376 |
| replication | Oct 2022, 244 | rule as written = **the main window again** (Nov 2021); latest admissible start Sep 2022: **338** (2-month overlap, 290 shared homes). Candidates from Nov 2020: 24 … 340 |
| filler s₀, all Std / gas-CH & 0 heaters | 0.0131 / 0.0082 (HadCET) | 0.0120 / 0.0075 (Heathrow) |
| D1 / D2 (flags) | +0.7 % / 1.1 % | +5.9 % (G005, G007 > 15 %) / 0.24 %: not raised |
| D4 (Nov–Mar, `mapping.md`) | 58–99 % raised | median abs(Δs_h) 30–100 %, abs(Δp99.9) 3–7 %: raised |
| **Task A**: real year-to-year Y vs D4 error E (def. a), n = 10/40/120 | – | Y 0.78/0.63/0.52 vs E 0.94/0.50/0.38; Y ≥ 0.5 E at all n (same for b, c) → **intrinsic filler variability** |
| capacity-equivalent error, % of HP_Peak (N 10–120) | – | p 0.05: 48–74; 0.2: 12–19; 0.5: 4.8–7.4; 0.8: 3.0–4.7; 1.0: 2.4–3.7. **Fusion-limited: p ≤ 0.5** |
| R4: nearest-T day changes vs HadCET | – | 94 % of (station, day); Heathrow is 1.2 K warmer, r = 0.984 |
| envelopes (used HP train/test; test substations per bin ≤15/15–35/35–65/>65) | B\* 62/20; 75/40/10/10 | GB-EoH main 275/81; 265/125/30/35; Sep-2022: 239/66; 215/110/30/30 |
| smoke run / timing probe | 2.6 min | 3.4 min wall / 3.5 job-h (seed, 5 families: 2.8 job-h; FFNN 1.2 h) |

**Assumptions & deviations:**
- **R8 rule is mine.** Runs are classified per run plus 12-h context. 2022/23: 122 of 124 runs (2,037 bins) belong to one home, EOH0836, whose electricity reads ≈ 0 while it delivers 8–10 kW of heat: a **meter dropout, not energy-crisis behaviour**. The exemption as worded would have un-flagged its gaps, so the rule is: missing if heat > 0.1 kW in the run or heat > 1 kW with electricity < 0.02 kW within 12 h. Real switch-offs exist (2021/22: 5 runs; 2022/23: 2) and stay valid.
- Task A uses winters Nov–Feb (common span; the LCL window ends 27 Feb 2014). The rule's operationalisation (per n, definition a, medians) is in the docstring, committed before the run.
- R4 Meteostat file 03772 (309 KB, CC BY-NC 4.0) fetched; the name of station 03772 is not verified on Meteostat. R7: −3.0 °C kept, now referenced (London 99.6 %, CIBSE Guide A via MCS): a London value; other sites run −1.5 to −5.9 (not verified at source).
- Weather groups are derived per loaded span, so main and replication-as-written give 385 vs 388 homes in the same window. New caches `2122r2`, `2223r2`, `2223sep`.
- Queue: `--arms` flag and atomic feature-cache writes added. Learning-curve jobs (n ≠ all) are 05b.

**Problems found:**
- **Silent-electricity homes** the exact-zero rule misses: EOH2291 (15 % of its heat bins, in the main pool) and EOH0836 (35 %, eligible in the Sep-2022 window). Kept and listed, not dropped.
- The probe's neural job failed once (Windows `os.replace` race on the shared cache, fixed) and was rerun alone. Every family job repeats the pilot (441 s, 17 % of a seed).
- B\* has 10 test substations in the 35–65 % and > 65 % bins even with p = 0.8 (target ≥ 20).
- The mtimes of the four EoH originals changed at 22:47–22:50 today, one per minute, sizes unchanged; nothing here opens them, probably OneDrive (not verified).
- The winter-only slope is a pessimistic proxy: the estimators fit a full year (D1 differs by 6 %).

**Decisions for Alex:**
1. **D4 → intrinsic** (Y ≥ 0.5 E at every n). *Recommended:* accept the mapping; 05b adds the filler-uncertainty arm (fillers' temperature response ×0.5, ×1.5); mark p ≤ 0.5 (Paper A bins ≤ 15, 15–35, 35–65) fusion-limited in every GB-EoH table.
2. **Replication window and silent homes.** *Recommended:* take Sep 2022 – Aug 2023 (338 homes, 2-month overlap) as the replication, and exclude homes with silent electricity > 5 % of their heat bins (2 homes; 4-min rebuild). The literal rule gives no replication.
3. **Schedule D5, then 05b scope.** D5 ≈ 2.8 h wall at 6 workers. **05b ≈ 16.5 nights** (942 job-h, new models assumed to double tuning; 9.7 without); with cached pilots, 2 LC draws and arm 3 at spc {10, 40} ≈ 12. *Recommended:* approve those three reductions and drop B\* oracles from arm 4; you choose the rest. Pause OneDrive sync overnight. Run:
`powershell -ExecutionPolicy Bypass -File scripts\schedule_overnight.ps1 -Config configs\iter05a_overnight.yaml -StartAt 22:00 -StopAt 07:30`
