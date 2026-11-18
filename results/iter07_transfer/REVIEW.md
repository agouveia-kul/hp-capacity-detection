# Iteration 07 — Transfer validation (CH ↔ GB, frozen 06 models, harmonised label HL)
**Goal:** test confirmatorily, on the pool it was not selected on, whether identifiability-guided hybridisation (L2/L3) beats pure data-driven (T1) and physics (T2), and close the 06 record on axis T (T3).
**Branch / commit:** iter/07-transfer @ 6f97acc (report script `0238677`, committed and pushed before any transfer result was read)
**Changed:**
- Logic lines:
  - `labels_hl.py` 75, `iter07_labels.py` 68, `transfer.py` 165 (Part A1);
  - `iter07_l4a_refits.py` 48, `run_queue.py` +62 (watchdog, refit arms, `after_optional`, durable), `paperb/__init__.py` + `persist.py` + `run_benchmark.py` +10 (`durable`, fsync) (A2);
  - `iter07_report.py` 97 (Part B).
- Tests: `tests/test_07.py`.
- Configs: `iter07{,_quick,_probe,_ch_gb,_gb_ch}.yaml`.
- Results: `report/` (tables, `report.md`, figures), `labels/`, `l4a_refits.csv`, `{ch_gb,gb_ch}/predictions.csv.gz`, `refit_{ch,gb}/`, `log.txt`.

**Results:** nMAE on HL (%), median over seeds 0–9 [5–90 %]; in-pool = the target's own 06 models × c_tgt; gap = transfer − in-pool (pp). Verdicts use the pre-registered rule (≥ 8/10 seeds and median relative difference ≤ −5 %); WAPE gives the same verdicts by construction.

| direction (HP households: source train / target test) | H\* = L2 TabPFN | D\* = L1 CNN | L0ref `slope_base` | 06 hybrid (L4a) | best observed rows, outside the rules |
|---|---|---|---|---|---|
| CH→GB (62 / 81) | 10.9 [6.3–12.5]; in-pool 3.5, gap +7.3 | 10.3 [9.4–12.3]; in-pool 3.7, gap +7.0 | 18.2 [15.6–20.6]; in-pool 5.5, gap +12.7 | CNN 11.6 [9.0–13.3] | L1 TabPFN 8.8; `paperA_corr@tgt_s0` (DA) 8.8; `calibrated_delta` 9.4 |
| GB→CH (274 / 20) | 10.1 [6.1–12.4]; in-pool 5.0, gap +5.2 | 12.3 [8.1–15.8]; in-pool 6.8, gap +5.3 | 14.0 [11.0–15.5]; in-pool 5.4, gap +9.3 | TabPFN 10.8 [8.8–12.6] | `paperA_corr@tgt_s0` (DA) 5.6; L3 linear 6.4; `paperA_sh_mh` 6.4 |

- **T1, H\* vs D\*: not confirmed.** No difference in both directions: CH→GB 7/10 seeds at −6.3 %, GB→CH 7/10 at −17.3 %. The verdict is the same on HL_uncorrected and on the native label.
- **T2, H\* vs L0ref: better in both directions (10/10 seeds; −42 %, −27 %)**, so H\* "beats physics under transfer" against the pre-registered L0ref. **However, `slope_base` is a weak row under transfer.** Outside the rules, by median only, `calibrated_delta` (CH→GB) and `paperA_sh_mh` (GB→CH) are below H\*, and so is the label-free target-s₀ row (DA) in both directions.
- **T3 steps** (better / no difference / worse), CH→GB | GB→CH:

  | step | linear | TabPFN | CNN |
  |---|---|---|---|
  | L2 vs L1 | no diff \| no diff | no diff \| no diff | no diff \| no diff |
  | L3 vs L2 | worse (0/10, +59 %) \| better (9/10, −29 %) | worse \| no diff | worse (0/10, +68 %) \| no diff |
  | L4a vs L3 | no diff \| worse (+143 %) | better (10/10) \| no diff | better (10/10) \| worse |

  The 06 hybrid vs D\*: worse (CH→GB), no difference (GB→CH). 06 rule 2 stays failed.
- **Transfer error:**
  - Every ML rung loses nMAE to transfer: +4.3 to +13.0 pp CH→GB (1.9–4.6× its in-pool error) and +1.0 to +13.0 pp GB→CH
    (1.1–3.3×). The largest gaps are in the ≤ 15 % bin (CH→GB) and the > 65 % bin (GB→CH).
  - **Physics bias tracks the filler-slope mismatch (CH s₀ 0.0054 vs GB s₀ 0.0126 kW/K):**
    - CH→GB: the physics rows over-predict, by +16 % to +34 % of max y in the s₀-corrected rows (`paperA_corr`, `slope_base`).
    - GB→CH: they under-predict (`slope_base` −13 %; `paperA_corr` −13 %), and 20–44 of 135 CH substations per seed get ŝ = 0.
    - The upward own-load bias the brief expected for GB→CH is not visible; the s₀ over-correction dominates.
- **Labels:** c (HL / native, source train) is CH 0.942 [seed range 0.931–0.965] and GB 0.955 [0.953–0.958]. The CH 30/15-min net-peak ratio is 0.945, and GB immersion is 4.5 % of `HP_Peak`. The HL mapping changes no T1/T2 verdict; on HL_uncorrected two CH→GB L2 vs L1 steps move from no difference to worse.

**Assumptions & deviations:**
- **In-pool reference for L4:** where 06 kept L4b, it is the 07 L4a refit's own in-pool predictions (the same kind of model that is transferred). For `paperA_corr_own` CH→GB it is GB's own-stream construction (flagged).
- **Probe:** extended with one GB refit per family at seed 3, because seed 0 has none.
- **Timeouts:** `timeout_s` = max(3 × the probe's longest job, 1,800 s) = 1,800 s for every family.
- **Runs:** the probe and the run were started by me, detached on Alex's request; no scheduled task was registered.
- **Crash safety:** `durable()` (fsync) was added after a crash corrupted a renamed cache. No computed value changes.
- **Still open from `PART_A.md`, applied as recommended:** immersion 0 for the 40 GB homes without a channel (bound −0.46 %); CH T_design −8 °C, UNVERIFIED.

**Problems found:**
- **GB seed-6 CNN L4a refit collapsed.** Following B1, it chose the initialisation with the lowest validation loss (0.117), whose in-pool test WAPE is 213.8 %. 06's own fit of the same configuration had nMAE 4.4 %. The other 10 GB refits reproduce 06 within 0.3 pp.
  - Kept as pre-registered.
  - No verdict changes: GB→CH L4a vs L3 CNN is still worse without seed 6 (2/9 seeds, +19 %).
  - It inflates the CH→GB L4 CNN in-pool reference for seed 6.
  - B1's validation loss can pick a degenerate model.
- **Residual blow-ups:** CH→GB L3/L4 linear blow up on single seeds (nMAE 53 and 80 at seeds 3 and 9). The residual exp(f) extrapolates on out-of-range features, as in 06's R(i).
- **Uncorrected 30-min peaks:** the CH→GB L1 linear and TabPFN winners are `size_peak`-anchored in 10/10 seeds. They are fed 30-min peaks (ratio 0.945); this is not corrected, as the brief says.
- **Machine crashes:** the PC crashed twice on 2026-11-17 (bugcheck 0x50; corrected PCIe errors from the GPU). No result was lost after the fix.
- **c above 1:** some CH test substations have c > 1 (up to 1.08). HL uses bins valid in both 15-min halves, so its percentile sample differs slightly from the native one.

**Decisions for Alex:**
1. **What the method section can claim after T1.** *Recommended:*
   - State that L2/L3 is **not confirmed** to beat pure data-driven under transfer. It beats the pre-registered physics reference, but not the best physics rows, and its in-pool gain (06) does not carry over.
   - Frame the contribution around what transfers and what does not. The fill slope s₀ is the transfer bottleneck: the label-free target-s₀ row closes most of the physics gap.
2. **07b.** *Recommended:* yes. Pre-register a **target-s₀ (label-free) rung** and test it on unseen data (FeederBW real feeders, labels noisy, or the replication year), rather than harmonised retraining. 07 points to the non-HP temperature response, not the HP label, as the dominant shift.
3. **Estimator for 08 (within-GB change detection).** *Recommended:*
   - Primary: `paperA_corr` with the site's own s₀, which is label-free and has the smallest physics gap.
   - Comparator: TabPFN L2 refit on GB (best in-pool).
   - Detect changes on differences, so that a stable bias cancels.
