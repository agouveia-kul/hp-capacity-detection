# Iteration 07, Part A — stopped after Task 2 (split proposed), 2026-11-16

Not the iteration's REVIEW. **No transfer error metric was computed or opened.** The only error numbers computed are the round
trip of test (c): a pool's own models on its own 06 test set, compared with the 06 predictions. Those are in-pool 06 numbers,
already known.

## Why Part A stops here
The brief caps Part A at about 300 logic lines: "if it is bigger, stop after Task 2 plus tests and propose a split". Logic lines
(no blank, comment or docstring lines):
- Tasks 1–2: `labels_hl.py` 75, `iter07_labels.py` 68, `transfer.py` 165, **308 in total**.
- Tasks 3–4 together: about 106 more (`iter07_l4a_refits.py` 48, `run_queue.py` +58).
- Tests: `tests/test_07.py`, 144.

**Proposed split:**
- **A1 = Tasks 0–2**, committed, for review now.
- **A2 = Tasks 3–4.** The code is drafted and committed separately (`A2 draft` commit). Its watchdog unit test passes, but nothing
  else in A2 has run: no L4a refit, no quick run, no probe, no estimate. After your go it needs: the quick run, the probe (seed 0,
  both directions, plus the seed-0 refits), `timeout_s` set from the probe, the runtime estimate and the scheduling command.

## State
- Branch `iter/07-transfer`, from `main` at `78a8ddd` (06 merged and pushed on your request, 2026-11-16).
- Commits: Task 0 `29ff917`; Task 1 `c510505`; Task 2 (A1) `79af062` (with Task 1's CSV tables, force-added: `*.csv` is
  git-ignored); A2 draft `9b1575a`; the opt-in `after_optional` fix, this note and `pytest.log` in the commit after.
- Branch pushed to the remote (the 07 agent prompt: push this branch only, never merge).
- Prerequisite checked: `main` holds the 2026-11-16 DECISIONS lines and `metrics.nmae`.

## Task 0 (first commit, `29ff917`)
- Brief added as `iterations/07-transfer-validation.md`; `07-transfer-notes.md` marked superseded.
- DECISIONS.md: 7 pre-registration lines.
- **Comparators** (06 inner-CV WAPE only, median over seeds; persisted manifests, the same values as 06 `metrics.csv`):

  | source | H\* (L2/L3) | D\* (L1) | L0ref | 06 hybrid (L4a only, T3) |
  |---|---|---|---|---|
  | GB | TabPFN L2, 17.04 | CNN L1, 18.64 | `slope_base` | TabPFN L4a, 19.19 |
  | CH | TabPFN L2, 22.88 | CNN L1, 24.63 | `slope_base` | CNN L4a, 23.73 |

  The runners-up are in the DECISIONS line. D\* is the CNN in both directions, so the CNN's calendar alignment (below) bears
  directly on T1.
- `method_basis.md`: 7 references checked against Crossref. WILDS, CIBSE Guide A and the CH −8 °C source are UNVERIFIED.
  "No precedent retrieved" is stated for frozen cross-country transfer and for HP-label harmonisation.
- CLAUDE.md diff (only the parts Task 0 names):
  - §4: one new paragraph, "Transfer protocol (07; …)", after the multiplicity line.
  - §5: one new row, `HL`, before `HP_CoincPeak`.
  - Nothing else changed (`git show 29ff917 -- CLAUDE.md`: +3 lines).

## Task 1, label audit (`label_harmonisation.md`)
- HL is built for both pools. Both native labels are reproduced exactly first (max diff ≤ 1e-6 kW).
- c_src (median over train substations): CH 0.942 [seed range 0.931–0.965]; GB 0.955 [0.953–0.958]. The shift is −4 to −6 % in
  both pools.
- CH 30/15-min net-peak ratio: 0.944.
- GB immersion share of HP_Peak: 4.5 % (train).
- **Not a stop:** the immersion channel exists and is usable for 247 of 384 homes. 137 have no reading, which the EoH data
  dictionary reads as "no immersion heater".
- **Flag:** 40 of those 137 homes have `MCS_Immersion` > 0 (10.3 % of the summed native peak). If they were given the typical
  immersion share, the GB HL total would move by −0.46 % (Decision 2).

## Task 2, transfer evaluator (`scripts/paperb/transfer.py`, tests `tests/test_07.py`)
### Rules written in Part A, before any transfer prediction is scored
1. **Calendar alignment (the brief's day-of-year rule).** Of all the inputs, only the CNN's daily series depend on calendar
   position: `rs_y_<i>` and `rs_T_<i>` are day i from the pool's first UTC day. They are reordered so that position i holds the
   target day with the source day i's (month, day) (`transfer.doy_perm`). Both windows have 365 days and no 29 February, so the
   map is a bijection; CH day 0 (1 Jan) = GB day 61.
   - Not aligned, because they depend only on daily means or time-of-day windows, not on calendar position: `whdd` (summary
     statistics over weekday bins), `netfit` (fits on daily means), the `rawphys` scalars.
   - Weekday and holiday flags come from each target's own timestamps; `netfit` uses the target pool's holiday calendar
     (GB-ENG / CH-ZH).
2. **Source pipeline on the target.** The two 06 arm configs have identical feature kwargs (`whdd` at `resolution: 15`, T_base
   12 °C, the same `netfit` and raw settings), so "the source pipeline" is the shared 06 pipeline.
   - GB→CH: the CH pool's series are averaged to 30 min (`at_30min`, float64) before evaluation. `whdd` then ffills them back to
     15 min, as it did for GB in 06.
   - CH→GB: the GB features are the 06 caches, unchanged.
3. **s₀ of a source on target rows.** The source's s₀ for the target row's station, else the source seed's median s₀ (the
   `s0:paperA_corr` row of its 06 `pilots.csv`).
   - A CH source has one s₀ (KLO fillers), so this is that value.
   - A GB source on CH rows uses the median over its substations' station s₀.
   - In a round trip this reproduces 06 exactly.
4. **Source quantities from 06 outputs.**
   - Pilot m_h, κ (L4a), m_h′ (`paperA_corr_own`, CH only) and s₀: the source seed's 06 `pilots.csv`, physics job.
   - `cal_b` of `paperA_cal` / `paperA_corr_cal`: 06 `metrics.csv`.
   - The four `physics_baselines` maps: refit on the source train substations with the native label, as 06 did.
   - All of these were computed on the source train set in 06.
5. **L0 rows carried.** `slope_only`, `slope_base`, `calibrated_delta`, `hdh`, `paperA_sh_mh`, `paperA_corr`, `paperA_cal`,
   `paperA_corr_cal`, `paperA_l4a`; plus `paperA_corr_own` (CH→GB).
   - Secondary row `paperA_corr@tgt_s0`: s₀ from the target's train fillers, from the target's 06 `pilots.csv`; label-free.
   - `paperA_corr_own` GB→CH is listed as n/a ("no whole-house meters in GB").
6. **L4 source.** The 07 refit directory (`transfer.models_dir`, default `results/iter07_transfer/models`) where 06 kept L4b;
   else the 06 winner, which must then be `l4a`. A transfer job that meets an L4b winner without its refit lists a load error and
   predicts nothing for it.
7. **Output.** `preds` in the 06 format, plus `direction`, `label_def`, `c_src`, `rung` and `HP_Count`, with three
   `label_def` values:
   - `HL`: c_src · ŷ vs HL;
   - `HL_uncorrected`: ŷ vs HL;
   - `native`: ŷ vs the target's native label.

   `diag` holds validity counts only (`n_pred_nan`, `n_invalid_base`, `load_error`). No metric is computed.

### Tests (`tests/test_07.py`)
- (a) Permuting the target's labels (household caps and `tab.HP_Peak`) leaves every CH→GB prediction bit-identical: pass.
- (b) c_src = the median of HL / native over the source train substations; halving the source test households' HL leaves it
  unchanged; HL rows = c_src × uncorrected rows: pass.
- (c) Round trip, seed 0 (c = 1, native labels), every 06 row reproduced:

  | pool | physics (9 rows) | linear L1–L4 | CNN L1–L4 | TabPFN L1–L4 |
  |---|---|---|---|---|
  | GB | max \|Δpred\| 5e-13 kW, ΔWAPE 0.0 pp | 9e-13, 0.0 | 1.7e-12, 0.0 | 2.6e-4 kW, \|ΔWAPE\| ≤ 1.8e-5 pp |
  | CH (10 rows, incl. `paperA_corr_own`) | 7e-13, 0.0 | 1.3e-13, 0.0 | 1.1e-13, 0.0 | 4.1e-4 kW, ≤ 4.3e-5 pp |

  All 06 test rows matched (no unmatched row); y equal in every row. The bar is |ΔWAPE| ≤ 0.001 pp. TabPFN refits its train
  context on load, as in 06's reload check (1.6e-5 relative there). The CH L4 winners of seed 0 (linear, TabPFN, CNN) are L4b and
  went through their saved scale model; GB's are L4a.

  Physics and linear run in the default suite; TabPFN and CNN run with `PAPERB_SLOW=1` (the repo has no registered `slow`
  marker, so this env variable gates them).
- (d) The 30-min rebuild of CH aggregates leaves the net-load daily series identical. Temperature-derived inputs differ by
  ≤ 9e-8 relative, because the pool stores temperature as float32 and pandas averages it in float32 at 15 min (tolerance
  1e-6). The 30-min peak is lower, as it should be: pass.
- (e) Pairing s→s: every target `sub_id` starts with `s|test|`, and every model directory is `.../s<s>/...` of the source arm:
  pass.
- Day-of-year map: pass.
- Full suite (`pytest.log`): 175 passed, 3 skipped (CUDA; the two `PAPERB_SLOW` round trips, run by hand above), 1 xfailed
  (the documented CNN CPU-vs-GPU case).

## A2 draft (committed, not run)
- **`iter07_l4a_refits.py`**, which writes `l4a_refits.csv`.
  - 31 cells: GB 11 (linear 2, TabPFN 4, CNN 5); CH 20 (7 / 6 / 7).
  - Each has the L4a inner-CV-best configuration and its logged params and epoch count, matched uniquely in the 06 logs on
    (seed, spec, cv_wape ± 0.05).
  - CNN epochs: GB 101–168, CH 53–133.
- **`run_queue.py`:**
  - `watchdog: true`: one process per job; a job still alive 60 s after its family's `timeout_s` is killed, without touching the
    others. Test: a job blocked in a 120 s native call with a 1 s limit is killed at about 3 s, while the job beside it finishes.
  - `persist_dir`, `frozen_arm`, `seeds_by_family`: the refit arms.
  - `after_optional: true` (07 transfer arms only): wait only for a dependency job that exists. By default a missing one keeps
    the job waiting, as 06's test requires. My first version changed the default and broke that test; it is now opt-in.
- **Configs:** `configs/iter07.yaml` (2 refit arms, 2 transfer arms × 8 families × 10 seeds; 5 workers × 4 threads = 20 physical
  cores), `iter07_probe.yaml`, `iter07_quick.yaml`, `iter07_{ch_gb,gb_ch}.yaml`. Every `timeout_s` there is provisional, to be
  set at 3 × the probe's longest job.
- **Rough size, not probed:** 160 transfer jobs (predictions only) plus 31 refits. The five GB CNN refits dominate, about 1.3 h
  each at 3 threads in 06 (an R-arm refit, 4,526 s). Expected under one night; to be measured by the probe.
- **OneDrive:** pause the sync for the probe and the run, and resume it only after the merge.

## A2 progress (split approved 2026-11-17; DECISIONS line)
**Quick run** (`configs/iter07_quick.yaml`, seed 0; 7 jobs): done, 0 failed. Validity counts only, no error metric opened.
- CH→GB (455 target substations) and GB→CH (135): every expected row is present for all three `label_def` values, with 0 NaN
  predictions and no load error. c_src: CH 0.965 and GB 0.958 on seed 0.
- The CH seed-0 linear L4a refit reproduces its `l4a_refits.csv` row (spec ElasticNet|size_peak|netfit|l4a|log, same params).
  The CH→GB L4 linear row used this refit.
- Jobs take 6–34 s. The GB→CH jobs build the 30-min CH feature cache first (22 s).
- **Invalid physics base (ŝ = 0), a count to report:**
  - GB→CH: 25 of 135 for `paperA_corr`, `paperA_corr_cal`, `paperA_l4a` and L4 linear. The GB source's s₀ median is 0.0126 kW/K,
    2.3× CH's 0.0054, so it over-corrects the CH aggregates.
  - CH→GB: 22 of 455 for the secondary row `paperA_corr@tgt_s0`.

**Two machine crashes on 2026-11-17.** Both were unclean shutdowns (Kernel-Power 41).
- 11:56:43: bugcheck 0x50 (PAGE_FAULT_IN_NONPAGED_AREA), and the dump failed. Three GB→CH quick jobs were running.
- 17:15:23: shortly after waking from Modern Standby, with no job running.
- Both boots log corrected PCIe errors (WHEA 17) from the NVIDIA GPU (VEN_10DE DEV_25BC).
- The 11:56 crash left the just-renamed `data/_paperb/features/bstar30_s0_f74e82df29a7_{tab,X}.parquet` without a parquet footer.
  These were files written by 07 that day. I deleted them, waited 90 s (nothing came back), and the rerun rebuilt them.
- Every other file written that day reads back. The refit model's sha256 matches its manifest.
- **Fix (`65e8cca`, 18 lines, no computed value changes):** `paperb.durable()` fsyncs feature caches before `os.replace`, job
  outputs before their `.done`, and persisted model files before their manifest. A crash can now lose only a job that is still
  running, and a relaunch reruns it.

**Probe: not started.** OneDrive restarted with the 21:39 reboot, so its sync is probably running again.

## Assumptions and deviations (for the REVIEW)
- **HL GB:** a home without any P_ih reading has immersion 0 (data dictionary). The 40-home ambiguity is above.
- **c is per substation, then the median over the seed's train substations** (the brief's wording). Per bin, c is reported but
  not used for the mapping.
- **CH→GB `size_peak` shift** (30-min peaks fed to 15-min-trained models) is reported, not corrected. The flagged winners are
  counted in `label_harmonisation.md`.
- **Round trip (c) for L4b winners** goes through their saved `scale.joblib` (round trip only). In transfer, an L4b cell uses
  only its L4a refit.
- **In-pool reference** (the target's 06 test predictions × c_tgt) is left to the report script. Its inputs are the 06
  `predictions.csv` and `labels/label_audit.csv` (c_tgt).

## Decisions for Alex
1. **The split.** Approve A1 (Tasks 0–2) as reviewed, then let me finish A2: refits, quick run, probe, timeouts, estimate, and
   the scheduling command. *Recommended:* yes. A2 is drafted and adds about 106 logic lines.
2. **The 40 GB homes with a design immersion load but no immersion channel.** *Recommended:* keep immersion 0, as the data
   dictionary reads, and report the −0.46 % bound as a sensitivity line in the label table. Excluding the homes would change
   the 06 test sets.
3. **CH design temperature −8 °C has no retrieved source.** L4a uses it as target metadata on GB→CH. *Recommended:* keep it
   (it is the 06 value, and changing it now would change a pre-registered input), and mark it UNVERIFIED in the paper unless you
   have the SIA source.
