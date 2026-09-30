# Iteration 04 — Data inventory for larger pools, and HP-profile simulation feasibility
**Goal:** Find which on-disk datasets can form larger household pools under protocol v1, whether past iterations should be rerun on them, and whether hplib-based simulated HP profiles are feasible and faithful.

**Branch / commit:** iter/04-data-inventory @ fcb2740 (code; first version c5a8a8a); results in the next commit. Branched from `main` after 03b was merged.

**Changed:** 710 logic lines, all read-only audit code in `scripts/audit/` (**over the ~400 budget**; see Decision 4): `eoh_convert.py` 86, `inventory_v2.py` 347 (mostly per-dataset report fields), `envelope_v2.py` 160, `hplib_check.py` 117. Also `configs/iter04_inventory.yaml`, `requirements.txt` +1 (`openpyxl==3.1.5`), CLAUDE.md §1 renumbering, DECISIONS.md +1. *Generated:* `results/iter04_inventory/` (inventory.md/.csv, usability.md, envelopes.md, rerun.md, hplib.md, hplib_check.md, simulation_design.md, metrics.csv, hplib_spf.csv, figures/, config.yaml, log.txt); `data/_paperb/pools_raw/eoh/` (347 MB, 30-min parquet streamed from the zips, nothing extracted except docs to `data/_paperb/raw/eoh/`); EoH property table copied to `data/_paperb/raw/eoh/eoh_property_design_installation.csv` (same MD5; original left in `data/`); `data/_paperb/iter04/` caches. Disk: 425 GB free before and after. Nothing in `data/` outside `_paperb/` was modified (mtime check).

**Results** (envelopes: protocol v1 grid and rules unchanged, 20 split seeds; B\* reproduces 03b exactly)

| pool | HP hh | train / test HP used per seed | test subs per seed ≤15 / 15–35 / 35–65 / >65 % | fill (s₀ kW/K per dwelling) | capacity label |
|---|---|---|---|---|---|
| B\* (03b reference) | 86 | 62 / 20 | 75 / 40 / 10 / 5 | Kaiser, same year (0.0055) | robust peak; nameplate ≤ 14 per station-window |
| **GB-EoH 2021/22** (non-hybrid) | 433 | **309 / 90** | 265 / 145 / 30 / 15 | LCL 2012/13, London (**0.0133**; gas-only subset 0.0070) | **`HP_Size_kW` for all 433** (median 8.5 kW); robust peak ≈ 0.48 × rated |
| GB-EoH 2022/23 | 370 | 264 / 71 | 190 / 110 / 30 / 15 | same | same (370) |
| GB-RHPP Nov 13–Feb 14 | 114 | 86 / 28 | 50 / 35 / 15 / 10 | LCL, concurrent | **installer capacity 111 / 114** |
| US-NEEA cal2023 | 57 | 42 / 13 | 20 / 20 / 5 / 0 | 49 NEEA homes | robust peak; 0 complete seasons on disk |
| B\*+ | 86 + 7 | = B\* | = B\* | – | – |

hplib conversion check on 50 EoH air-source homes (2021/22; 34 ASHP + 16 HT-ASHP), rated power = `HP_Size_kW`: Q/COP under-predicts HP electricity (group 1: daily WAPE 26.8 %, bias −25.9 %; 13.3 % after one global rescale; SPF over-predicted by +37 %). On-off group 4: 17.9 % / −12.9 % / 14.6 %. The percentile size proxy used before the property table gave 23.1 % / −21.8 % / 13.8 % on the same homes (first version, other draw: 21.7 % / −19.7 %).

**Assumptions & deviations:**
- EoH has no whole-house meter. "Stations" are the 30 groups of homes whose 30-min outdoor temperature is exactly identical (shared weather station); postcode districts confirm them as regions (Edinburgh/Fife, Tyneside, Borders, SE England). Pools use heating-season windows, not calendar 2023.
- EoH type is `HP_Installed` from the property table supplied by Alex (licence not on disk); hybrids (154) are excluded. The channel inference used first disagreed for 4 monitored homes.
- NEEA "heating fully submetered" is my criterion: residual slope ≤ 20 % of the metered heating slope, heating slope > 0.05 kW/K, no gas-furnace circuit.
- hplib check: rated power = `HP_Size_kW` taken as output at A7/W35 (rating point not stated in the table; percentile proxy kept as sensitivity); T_flow = DHW flow, else SH flow, else return + 5 K; HP electricity = whole system − immersion − back-up − pump. RHPP was not checked (no outdoor-air temperature).
- Rerun wall times are scaled estimates, not measurements. Citations marked "unverified" in simulation_design.md were not retrieved (scite quota exhausted).

**Problems found:**
- EoH: 3 empty property files; the hybrid boiler counter is unreliable (724 k negative diffs); one home reports 0 heat output for 100 days while drawing 10–30 kWh/day (heat-meter dropout recorded as 0, not missing). The UKDA summary's whole-dataset start/end dates differ from the file contents by > 30 days for 187 of 739 homes (e.g. EOH0001). The inventory uses the files.
- Only calendar 2023 NEEA power is on disk, so NEEA has no complete season. RHPP B2 is one year per site (169 / 418 with a full season). Pecan Street on disk is 25 + 25 homes with no HP labels. COFACTOR and Carleton are not usable for P.
- The > 65 % bin is grid-limited (only p = 1.0) in every pool, so no pool reaches ≥ 20 test substations per seed in every bin without a grid change.
- The hplib README swaps the COP and P_th MAPE labels. The generic COP is optimistic in the field at every temperature bin; defrost is not identifiable in 2021/22.

**Decisions for Alex:**
1. **New pool.** *Recommended:* build **GB-EoH** (2021/22 main, 2022/23 replication) as a **second full-grid pool**, not a replacement for B\*. Fill = LCL re-matched to EoH days by temperature and day type (analog days); `HP_Nameplate` returns as a GB-EoH target (rated size for all homes). In parallel, request **SERL Secure Access (UKDS SN 8666)**, the household-level smart-meter edition (Aug 2019 onwards, ~13 000 GB homes). Secure Access needs accredited-researcher status and an approved project; all analysis runs in UKDS SecureLab, with disclosure-checked outputs, so GB-EoH substations would be built there. SN 8963, the safeguarded edition, holds only aggregated averages and cannot provide fill; download it now to benchmark the 2020–23 fill s₀ against LCL. GB-RHPP is optional (concurrent fill; installer capacity 111/114).
2. **Reruns (`rerun.md`).** *Recommended:* 02b no; **03b partial on GB-EoH** (carry-forward specs, learning curve extended to n = 100 / 200 / 300; add p = 0.8 so the top bin reaches ≥ 20). 05 then runs on B\* and GB-EoH.
3. **Simulator.** *Recommended:* **conditional go, demand source (i)** (measured EoH heat + resimulated device with a calibrated COP scale, standby, DHW and cycling layers), built only after the GB-EoH learning curve. No-go for the TABULA/5R1C option for now.
4. **Line budget.** *Recommended:* accept the 710 audit lines as-is (read-only, no pipeline change), or ask me to split `inventory_v2.py` per dataset in a follow-up.
