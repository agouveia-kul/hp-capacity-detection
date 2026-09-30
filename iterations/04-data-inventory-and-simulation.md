# Iteration 04 — Data inventory for larger pools, and HP-profile simulation feasibility

**Branch:** `iter/04-data-inventory`, from `main` after 03b is merged.
**Type:** read-only analysis plus small audit and validation scripts (≤ ~400 logic lines). No benchmark runs, no changes to the pipeline or to the protocol.
**Output:** facts and proposals for Alex to decide on, not results for the paper.

## Why this iteration
The fair test (03b) is data-limited. B\* has ~62 train and ~20 test HP households per seed. Only low-penetration cells survive for large feeders, so 75 of 130 test substations sit at ≤ 15 % penetration, and ML gains flatten at the size of the pool.

Before iterations 05+ (targets, transfer, change detection), we need to know:
1. which datasets on disk can form **larger household pools** that cover a wide size × penetration grid;
2. whether **past iterations should be rerun** on them;
3. whether **simulated HP profiles** (hplib plus a demand model) can extend the pools in a way that is statistically faithful to real data.

## Plan renumbering (record in CLAUDE.md §1 and DECISIONS.md)

| Iteration | Content |
|---|---|
| 04 | This inventory |
| 05 | Other targets + daily arm (RQ1) |
| 06 | Transfer (RQ3) |
| 07–08 | Change detection (RQ4) |
| 09+ | Freeze and draft |

The 03b decisions (paper lead, physics reference, carry-forward models) are still pending Alex's review. Do not record them.

## Rules specific to this iteration
- **Disk.** Check free disk space before extracting anything. The four EoH zips are ≈ 5.2 GB compressed.
  - Extract **only** into `data/_paperb/raw/<dataset>/`, and convert to parquet in `data/_paperb/pools_raw/<dataset>/`.
  - Read the zip index first (`zipfile.namelist`), then extract selectively.
  - Never modify or move the original zips or any other file in `data/`.
- **Reuse loaders.** `hp-sensitivity-paper` already has loaders for NEEA, RHPP (+LCL), BPA and NREL. Look for them (the caches `_rhpp_lcl_boxes.pkl`, `_neea_base_homes.pkl` and `_bpa_nrel_base_boxes.pkl` come from them), and reuse or port them rather than rewriting.
- **Report, don't decide.** Every "usable?" verdict must state the criterion and the evidence.

## Task 1 — Dataset inventory (`scripts/audit/inventory_v2.py` → `results/iter04_inventory/inventory.md` + `.csv`)
Inspect each dataset below: open files, read schemas and data dictionaries, and count. For each, report:
- unit (household / site / feeder);
- the number of units with an HP (or electric heating) **submeter**;
- the number of units with **whole-house or non-HP load** at the same site;
- resolution;
- period, including the number of complete heating seasons (Nov–Mar) per unit at ≥ 90 % coverage;
- weather: whether it is included, its spatial granularity, and a candidate source otherwise;
- **capacity labels:** nameplate / rated power, heat output meter, or none;
- HP type (air/ground, on-off/inverter);
- backup or immersion-heater channels;
- DHW channels;
- building metadata (age, floor area, type, tenure);
- location granularity;
- licence and access conditions (from the files or docs on disk).

Datasets:

| Dataset | Files in `data/` | Notes |
|---|---|---|
| **Electrification of Heat (EoH), UKDS SN 9050** | `9050csv_cleansed_data_set{1..4}_*.zip` | Nov 2020 – Sep 2023, 30-min, ~742 HPs. Find the Excel data dictionary. Check for whole-house electricity, heat output, flow/return and indoor temperatures, HP capacity/type, property metadata and location. **Highest priority.** |
| RHPP (GB) | `RHPP_GB.zip`, `rhpp_daily.parquet`, `rhpp_sites.parquet`, `rhpp_docs/` | 418 sites with `cap` and `share_boost`; HP only, 2-min. Check for a heat-meter channel. |
| Low Carbon London | `LCL_2013.zip`, `lcl_heatpump/` | What are the `S1_Customer_L_*.csv` files: an HP trial with whole-house load? Check LCL overlap with RHPP and EoH years. |
| NEEA end-use (US PNW) | `neea_*.parquet`, `POWER15_RAW_2023 v9.2.zip`, `SITES v9.2.csv`, `POINTS v9.2.csv`, `TEMPERATURE15 v9.2.zip`, READMEs, `CEMS Data Dictionary v2.0.docx` | Whole-home + circuits, 15-min. Count the homes whose **heating is fully submetered** (Paper A found heating outside metered circuits in Oregon). |
| BPA HPHC, NREL CCASHP | `bpa_hphc/`, `nrel_ccashp/` | HP only, hourly. Label and simulation-validation use only. |
| COFACTOR (Oslo), Carleton | `cofactor_ds1/`, `carleton/` | Check the unit (apartment vs building) and the heating type. |
| Pecan Street | `15minute_data_austin/`, `15minute_data_newyork*` | Count the homes with an HP/heating circuit and whole-home load. |
| HEAPO other seasons, Kaiser 2024, WPuQ 2020 | existing | Extra **distinct** HP households beyond B\*, by season. |
| FeederBW, UKPN LV feeder + LCT, Fluvius 15-min | existing | Real aggregates (transfer / validation only); summarise briefly. |
| Unknown archives | `dataset.zip` (904 MB, Jul 2026), `pleiadata.zip` | Identify from the zip index only. Do not extract unless relevant. |

## Task 2 — Usability matrix and pool envelopes (`results/iter04_inventory/usability.md`)

**Usability matrix.** Rows are datasets; columns are the use cases below. Each cell is yes / partial / no, with the reason.

| Use case | Minimum requirement |
|---|---|
| **P – capacity pool (RQ1/RQ2)** | HP submeter at ≤ 30 min, ≥ 1 complete heating season, a capacity label (robust observed peak computable, nameplate if available), and non-HP household load of the same period and climate (own or fill), with ≥ 30 HP households per climate region |
| **T – transfer domain (RQ3)** | a net load (real or constructible) and a capacity label, in a population different from B\* |
| **C – change detection (RQ4)** | the same HP households over ≥ 2–3 complete heating seasons |
| **S – simulation calibration/validation** | HP electricity **and** heat output (or heat demand) with outdoor temperature (flow temperature preferred) and HP type/capacity |
| **R – real-aggregate validation** | real feeder measurement with registered or known HP/TCL counts or kW |

**Design envelopes.** For every dataset marked P, re-run the design-envelope logic of `scripts/audit/design_envelope.py` (iteration 01) with protocol v1's rules (household-disjoint 75/25 split, `max_overlap` 0.75, station/region-matched HP members). Report:
- the train/test HP households per region;
- the max feeder size per penetration;
- the expected share of test substations per Paper A penetration bin.

Compare against B\* (test: 75 / 40 / 10 / 5 substations per bin). Candidate pools:
- **GB-EoH**: EoH HP loads + EoH whole-house loads if present, otherwise LCL/other GB fill;
- **GB-RHPP**: RHPP + LCL;
- **B\*+**: B\* plus the extra HEAPO/Kaiser seasons;
- **US-NEEA**, if enough homes qualify.

For fill that comes from another dataset, state the temporal and climatic mismatch explicitly (years, regions). Estimate the fill's temperature response (s₀) against B\*'s 0.0055 kW/K per dwelling.

## Task 3 — Rerun recommendation (`results/iter04_inventory/rerun.md`)
Give a table covering iterations 02b, 03b and the plans for 05–08. Columns:
- iteration;
- which new pool(s) would change its conclusions, and how;
- rerun: full / partial / no;
- estimated wall time (use the 03b timings);
- the pre-requisites (new pool builder, weather, labels).

It must answer explicitly:
1. Can the 03b **learning curve** be extended beyond n = 62 train HP households (e.g. to 100–300) on a new pool? This is the direct test of the data-limit diagnosis.
2. Does any new pool give a test set with ≥ 20 substations per seed in each Paper A penetration bin?
3. Should a new pool replace B\* as the headline, or run as a second full-grid pool? Consider population similarity to Paper A (Kloten) and the transfer role.

## Task 4 — hplib capability check (`results/iter04_inventory/hplib.md`)
1. **Version and scope.** Report the installed hplib version (requirements pin 1.9) and what it models. Check against the code, not just the README:
   - which outputs (P_el, P_th, COP) as functions of which inputs (T_in, T_out, T_amb, mode);
   - the parameter database (Keymark source, number of models, groups: air/water, brine/water, water/water × regulated/on-off);
   - generic HP construction by group and rated thermal power;
   - cooling mode.

   Also state what it **does not** model. Expected, to be confirmed: building heat demand, controls, compressor cycling / minimum part load, defrost, DHW, backup heater, blocking periods. Quote the documented fit errors.
2. **Conversion-step validation on real data.** On the S-usable datasets (EoH first, then RHPP):
   - take the measured heat output, flow temperature (or a heating-curve estimate) and outdoor temperature;
   - build hplib's generic HP of the matching group and rated power;
   - predict the electrical load and compare it with the measured HP electricity.

   Report:
   - daily and 30-min error (WAPE, bias) by outdoor-temperature bin;
   - bias of the seasonal performance factor;
   - where it fails: cold days (defrost), DHW periods, backup-heater periods.

   Use ≤ 50 sites and one season; this is a feasibility check, not a benchmark.

## Task 5 — Simulation design proposal (`results/iter04_inventory/simulation_design.md`, ≤ 2 pages)
Propose, **without implementing**, a simulator that produces realistic HP electricity profiles with known capacity for arbitrary pool sizes. Structure the proposal as follows.

**A. Demand source.**

| Option | Pros | Cons |
|---|---|---|
| (i) **Measured heat demand** of real monitored homes (EoH/RHPP heat meters), with the HP device resimulated. Preferred: keeps real occupancy, DHW and control behaviour | real behaviour | limited to monitored homes |
| (ii) A building model (e.g. ISO 13790 5R1C with TABULA/EPISCOPE archetypes) with occupancy and DHW profiles | any size of population | less realistic behaviour |

**B. Device and operation layers** added to hplib:
- **Sizing:** rated power = design heat load × an oversizing factor drawn from a distribution. This factor drives m_h (it links to the RQ3 transfer analysis).
- A weather-compensated heating curve for the flow temperature.
- Capacity limit with a **backup/immersion heater** when demand exceeds HP output.
- Minimum part load, with cycling represented as an energy penalty at the chosen resolution.
- A defrost penalty for air-source HPs in the relevant temperature band.
- DHW at a higher sink temperature, with schedules.
- Blocking/ripple-control windows as an option (Swiss/German regimes).

**C. Calibration.** Fit the simulator's population-level parameter distributions so that simulated summary statistics match a real **calibration** population. Parameters include the oversizing, heating-curve slope, balance temperature, DHW share and backup share. Methods:
- approximate Bayesian computation or simulation-based inference;
- or, as a simpler baseline, moment matching.

Target summary statistics (all quantities the paper uses):
- per household: the distribution of the net-load and HP hockey-stick parameters (s_h, T_h, P_base);
- SF(T) and m_h;
- load–duration curve shape;
- the after-diversity maximum demand curve ADMD(n) = coincident peak per household vs group size n;
- the ratio HP_Peak / s_h (per-unit scale).

**D. Statistical validation on a held-out real population.** Never validate on the calibration data. Pass/fail thresholds are stated in advance.

| Level | Checks |
|---|---|
| Marginal | per temperature bin, two-sample KS / Anderson–Darling and Wasserstein distance of 30-min and daily HP power |
| Temporal | autocorrelation functions, mean daily profiles by day type and temperature bin, ramp-rate distributions |
| Multivariate | maximum mean discrepancy (MMD) or energy distance on daily profile vectors, and a **classifier two-sample test** (a classifier trained to tell real from simulated days; AUC ≈ 0.5 = indistinguishable) |
| Aggregate | real vs simulated SF(T), m_h, ADMD(n) and the distribution of feeder-level s_h / capacity. These matter most for this paper |
| Downstream ("TSTR vs TRTR") | train on simulated, test on real, vs train on real, test on real, on the capacity task. The simulator is fit for purpose only if TSTR is within a stated margin of TRTR, and "train on real + simulated" does not degrade real-test performance |

**E. Intended use.** Training augmentation and controlled experiments only: varying the oversizing and climate to study m_h transfer, and covering high-penetration large feeders. **All headline tests stay on real households.**

**F. Effort and risk.** Estimate the implementation cost (logic lines, runtime), the main realism risks, and a go / no-go recommendation based on Task 4's conversion errors.

Search the literature where it helps, e.g. for simulation-to-real validation of load profiles, EoH/RHPP heat pump modelling papers, and TABULA-based heat demand models. Cite what you use in the proposal with DOIs or links, and flag anything unverified.

## Out of scope
- Building any new pool builder into `scripts/paperb/` (that happens after Alex decides).
- Running benchmarks.
- Implementing the simulator.
- Changing protocol v1.

## Acceptance criteria
- [ ] `inventory.md/.csv`, `usability.md`, `rerun.md`, `hplib.md` and `simulation_design.md` are all in `results/iter04_inventory/`. Every count is computed from the files, and every source script is named.
- [ ] The EoH contents are documented from its data dictionary and files (variables, units, number of sites, seasons, metadata).
- [ ] The hplib conversion check has run on ≥ 1 real dataset, or the reason it could not is stated.
- [ ] Nothing in `data/` outside `data/_paperb/` is modified; free disk space is reported before and after.
- [ ] REVIEW.md follows the §9 template. The decisions must cover at least:
  1. which new pool(s) to build, and whether as a replacement or a second pool;
  2. which past iterations to rerun (following `rerun.md`);
  3. whether to proceed with the simulator (go / no-go), and with which demand source.
