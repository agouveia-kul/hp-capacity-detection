# Iteration 01 — Pool capacity and protocol design audit
**Goal:** Measure how large a clean, household-disjoint pool can be, which substation designs it permits, and what else in the ML pipeline is unsound; then propose protocol v1 (read-only, no results).

**Branch / commit:** iter/01-pool-audit @ 0ea0301 (code); results committed on top.

**Changed:** `DECISIONS.md` (new, 3 decisions). New logic in `scripts/audit/pool_inventory.py` (205), `design_envelope.py` (159) and `ml_audit_checks.py` (175) = **539 logic lines**. Configs: `configs/iter01_{quick,full}.yaml` and `configs/protocol_v1_proposal.yaml`. CLAUDE.md §2 (§6 table), §3 rule 10 and §10 were edited **locally only**, because CLAUDE.md is gitignored. *Generated:* `results/iter01_pool_audit/` (pool_inventory.{md,csv}, design_envelope.md, ml_audit_checks.md, ml_audit.md, protocol_v1_proposal.md, config.yaml, log.txt), `results/iter01_pool_audit_quick/`, and `data/_paperb/iter01{,_quick}/*.parquet` (1.2 MB).

**Results:** legacy pool (iter 00) vs the proposed main arm B\*. Sources: design_envelope.md and ml_audit_checks.md.

| quantity | legacy (iter 00) | iter 01 |
|---|---|---|
| HP households, 15-min, train / test | 57 (29 / 28; 27 effective train) | **B\***: 86 (64 / 22); B: 47 (35 / 12); A at 75/25: 57 (43 / 14) |
| stacking per HP profile (120 dwellings, p = 1) | 16.7× | 1× (no household twice) |
| substations with HP/fill overlap | 1786 / 2160 | 0 by construction |
| max test feeder size at p = 0.3 / 1.0 | 120 / 120 (drawn with replacement) | 53 / 16 (A: 14 / 6) |
| substations per split seed, train / test; seeds | 1080 / 1080; 1 | 460 / 130; 20 |
| households with `Normpoint_ElectricPower` | 2 | 1 (15-min pool); 37 at daily resolution, at most 14 per station-window |
| HP_Count pool (daily arm, incl. households without HP submeter) | – | 1099 |
| test R² from a single Scale_peak feature | not reported | **0.891** (legacy XGBoost 0.934) |
| hockey-stick fits with T_bal above all observed T | not reported | **1990 / 2160** |

**Assumptions & deviations:**
- CLAUDE.md and `iterations/00-setup-baseline.md` were missing from the working tree. A GitHub Desktop stash (`stash@{0}`, together with iter00 `models/` outputs) had swept them away. I restored both text files with `git show` and left the stash intact.
- I branched from `iter/00-baseline`, not `main`, because iter 00 is not merged yet and I must not merge.
- Windows are heating seasons (Nov–Mar, UTC) and calendar years. The design options use calendar years, because the windowed-HDD features need warm reference days.
- The spec defines B and C as KLO-only. I added **B+** (15 Kaiser single-family HP meters without a dwelling meter) and **B\*** (B+ plus the HEAPO households at the other stations), since those enlarge the pool.
- D pools daily HP files with 15-min HP aggregated to daily. HEAPO total-only households count as HP members for count-only targets: 1354 of the 1358 surveyed households report an HP type.
- Fill is allowed across stations (the legacy rule). HP_Nameplate_el counts as "feasible" only with >= 20 nameplate households in one station-window (my threshold).
- The diff is 539 logic lines against the ~300 guideline. It splits cleanly into 01a (inventory + envelope) and 01b (ML checks) if you prefer.

**Problems found:**
- **Time coverage is the hard limit.** HEAPO 15-min data end on 2024-02-27, and the daily files of submetered households end on 2023-09-06. Kaiser covers only cal2023–2024 (one full season). So **cal2023 is the only year** with both HP members and clean fill. Adding cal2024 (option C) adds 2 households, and 15-min multi-season HP households number 13. RQ4 is thin at 15 min.
- **F1:** Scale_peak alone gives test R² 0.891, and it is the #1 selected feature. **F2:** the season filter (T_min < 12) and the T_bal bounds (8, 20) put the hinge outside the data in 92 % of fits, so base and T_bal are not identified. **F12:** `build_substations_norepl` truncates the fill silently. **F14:** notebook cell 88 fits its RidgeCV on test.
- **F10:** 37 FeederBW feeders are "unstable" only because the 2024 end metadata row is missing. I could not reproduce "26 changed feeders" (17 in 2024, 20, 43 over the full period). Where does 26 come from?
- **F11:** the WPuQ coverage check is a no-op; 5 of 37 houses are below 90 % (min 22.5 %). **M9:** 13 of 26 Kaiser paired dwellings and 28 of 57 HEAPO households have an electric water heater in the HP member's own load.
- Bugs in my own first inventory pass, fixed before these results: NaN `0_object_id` values joined to each other (Kaiser pairs inflated to 1388), and paired dwellings were counted as clean fill.

**Decisions for Alex:**
1. **Pool option?** Recommended: **B\*** for the main 15-min arm (86 HP households, cal2023). It includes the 15 Kaiser SFH HP meters, each paired with one unused clean dwelling as its own non-HP load. Do not adopt C; keep cal2024 for RQ4. Alternatives: B\* without the SFH meters (71), or B (47, KLO only).
2. **Daily arm in the paper?** Recommended: **yes, as a secondary arm.** It runs HP_Count on 1099 HP households (the only large-N test of count identifiability) and s_h / r / P_design on 71 submetered households. **HP_Nameplate_el leaves the substation benchmark** (37 households, at most 14 per station-window) and stays as a household-level descriptive check.
3. **Which findings to fix in iteration 02?** Recommended high severity: **F1** (anchor-only baseline plus a no-anchor arm), **F2** (season filter vs T_bal bounds), **F12** (silent fill truncation) and **F14** (drop or re-fit cell 88 on train), plus **F13** (early stopping on the scored fold), which the new CV replaces anyway. Defer F3–F8 to 03 and F10 / F11 to the transfer iteration.
