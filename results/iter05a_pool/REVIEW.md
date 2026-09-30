# Iteration 05a-i — GB-EoH pool with analog-day LCL filler (Tasks 0–3)
**Goal:** Build GB-EoH as a second pool (EoH heat pumps + analog-matched flat-rate LCL fillers) and bound the fusion error, before any 05b run.

**Branch / commit:** iter/05a-gb-eoh-pool @ 534aee4 (code; Task 0 = 8d3f03a); results and this REVIEW in the next commit. Branched from `iter-04` (fd3ebdb): `main` does not contain 04 yet.

**Changed:** **Over budget → split per the brief:** Tasks 0–3 plus their tests are ~570 logic lines (`fill_analog.py` 160, `pools/gb_eoh.py` 120, `iter05a_report.py` 237 incl. report text and the D5 summary, 52 changed lines in `substations.py`, `run_benchmark.py`, `features_netfit.py`, `pools/__init__.py`). Adding Tasks 4/4b/6 would take the diff to ~800, so I stopped here and wrote this 05a-i REVIEW. Other changes: `pools.py` → `pools/__init__.py` (moved unchanged); tests `test_gb_eoh.py` 168; configs `protocol_v1_1`, `pool_{bstar,gb_eoh_2122,gb_eoh_2223}`, `iter05a_d5_{real,swap}`; CLAUDE.md fixes (EoH property table is on disk, HadCET path) + DECISIONS 1–10. *Generated:* `lcl_audit.md`, `eoh_selection.md`, `mapping.md` (D1–D4), `method_basis.md`, csvs; caches `data/_paperb/pools/{lcl_std_20120701_20140228*, gb_eoh_2122*, gb_eoh_2223*}` (≈ 400 MB). pytest: 66 passed, including the B\* seed-0 regression against 03b (metrics equal; fresh features equal the cache). Stash: `stash@{0}` no longer exists; the tags `iter-02b`, `iter-03b` and `iter-04` exist (local and origin).

**Results** (not interpreted; flags pre-registered in the brief)

| item | 04 / reference | 05a-i |
|---|---|---|
| LCL release on disk | public 5,567 hh | UKDS SN 7857 ed. 2: 4,173 Std + 1,025 ToU (tariff = file); a subset in households, a superset in fields (survey) |
| Std filler kept | – | 3,199 (coverage < 90 %: −875, > 10 kWh: −1, zero run ≥ 24 h: −98) |
| filler s₀ (kW/K per dwelling, HadCET) | B\* 0.0055; LCL 0.0133; "gas-only" 0.0070 (78 hh) | all kept 0.0131; 04 definition 0.0067 (47); **corrected gas CH & 0 heaters 0.0082 (777)** |
| GB-EoH 2021/22: window, homes | 433 (Nov–Mar, ≥ 90 %) | Oct 2021–Sep 2022, **295** (≥ 95 %; 373 at ≥ 90 %); 15 stations ≥ 3 HP |
| GB-EoH 2022/23 (same month + 1 y) | 371 | Oct 2022–Sep 2023, **244** (Jun 2022 start: 293) |
| D1 s₀ own days vs mapped | flag > 15 % | +0.7 % (per station −6 … +13 %): not raised |
| D2 share of days with abs(ΔT) > 1 K | flag > 5 % | 1.1 % (worst station 2.7 %): not raised |
| D3 day-of-year distance | – | median 15 d; 91 widenings; 62 days (1.1 %) without a 1 K match; ≤ 8 uses per source day |
| D4 LCL self-test, median abs(Δs_h) / abs(Δp99.9) | flag > 10 % | **58–99 % / 4–8 %: RAISED** (2012/13 −58…−64 %, 22.7 % of its days > 1 K; 2013/14 +60…+84 %, 0 % > 1 K) |
| D5 B\* swap test | flag > 2 pp | code and tests done; **not run** (needs the Task 4b queue) |
| B\* 30-min / 15-min HP_Peak | – | median 0.974 (IQR 0.916–0.993) |

**Assumptions & deviations:**
- The LCL coverage window is Jul 2012 – Feb 2014, not the full span. Over Nov 2011 – Feb 2014 only 450 Std households reach 90 %, because recruitment was staggered. The window covers every calendar day at least once.
- **Typing and window.**
  - Typing is 04's `type` (HP_Installed, with a channel fallback).
  - A 30-min bin is valid with ≥ 12 of its 15 two-minute diffs and is rescaled by 15/n.
  - "Other channels active" means heat output or circulation pump > 0 during the zero run.
  - Stations are re-derived over the 05a span with 04's 0.2 °C rule (32 groups in 2021/22, 29 in 2022/23).
  - The replication is fixed to the main window's month, as the brief says. Nov/Dec starts are reported for information only.
- **Mapping details.**
  - DST-change days are not candidates.
  - The map seed is the split seed.
  - `paperA_corr` uses s₀ per station, from the train fillers under that station's map.
  - The Paper A pilot for EoH uses the HP series alone to find T_h, because EoH has no own load.
- D1(b) is judged on the fit pooled over stations; per-station values are listed.
- D4 has only 2 winters (2011/12 falls outside the window), and its fits use winter days only.
- D5 swap: each substation keeps its fillers and gets n_hp extra fillers from the same split or fold, all on analog days. Candidates are matched on KLO temperature.
- **Assumed values.** `P_design` uses T_design = −3 °C for GB (unverified). HadCET is a Central England series, not a London station.

**Problems found:**
- **The LCL survey answers are shifted by one column against `survey_questions.csv`.** Iteration 04's "0 portable heaters" filter (answer Q304) actually selects **0 TVs**. Paper A's `_lcl_base` makes the same mistake for its clean and heater-rich splits. I reported this and did not change Paper A.
- **Fewer eligible homes than 04 counted:** 295 / 244 against 433 / 371. The 12-month window at ≥ 95 % is stricter than 04's season rule. The 2021/22 count still rises at the last candidate month (Oct), and the 2022/23 window loses the end of September because the data stop on 29 Sep 2023.
- **Station data.**
  - Two weather groups with homes have more than 5 % missing temperature: G009 (27 homes) and G004 (2 homes).
  - The zero-run rule removes 554 bins in 2021/22 but 2,130 in 2022/23.
  - 41 homes have heat-meter dropout days (kept for the simulator).
- 123 of 295 homes have immersion or back-up heating active in some of their top 0.1 % bins, so `HP_Peak` includes that draw.
- The line budget was exceeded (see Changed). Drafted 05a-ii code (queue, scheduler, learning-curve harness, smoke and timing configs) is kept only in a local backup. One end-to-end GB-EoH pipeline run (1 seed, sizes {10, 40} × p {0.1, 0.5}) finished in 2.6 min; its outputs are kept for 05a-ii and not interpreted.

**Decisions for Alex:**
1. **LCL and "gas-only".** *Recommended:* use the Std filler (3,199 households) as the main arm. Keep the "gas-only" subset, since it comes from the survey and is not circular, but only with the corrected columns (CH = Gas and 0 portable heaters; 777 households, s₀ 0.0082), as a sensitivity arm. Drop 04's definition. Also flag the Q304 error in Paper A.
2. **Windows.** *Recommended:* accept Oct 2021 (295 homes) and Oct 2022 (244), as specified. The alternative is to allow ≥ 90 % coverage (373 / 315) or a Jun 2022 replication start (293). Either would be a rule change that needs your approval.
3. **Mapping.** D1–D2 pass and D4 raises its flag: the winter-only slope is not preserved when a winter is rebuilt from another winter. *Recommended:* run D5 before deciding. If D5 also flags, add previous-day temperature conditioning, or restrict GB-EoH to the targets D5 shows are robust.
4. **05a-ii.** *Recommended:* approve 05a-ii for Task 4 (envelopes, learning-curve harness), Task 4b (queue and scheduler), D5 on the queue, and Task 6 (smoke run and timing probe). All of it is drafted; the queue and scheduler still need their tests (kill/resume, `--retry-failed`) and a dry run.
