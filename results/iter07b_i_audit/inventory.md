# 07b-i — Unseen-target inventory for a label-free local-s₀ estimator

Source: `scripts/audit/target_audit_07bi.py` (config `configs/iter07b_i_audit.yaml`). Numbers come from `facts.md` / `facts.json`, the 04 inventory (`results/iter04_inventory/`) and the files listed in `log.txt`.

**Blindness:** no estimator, prediction or error metric was computed on any candidate. Computed:
- counts, coverage and label descriptives;
- the per-dwelling slope s₀ of non-HP samples (Paper A daily-mean hockey stick, T_h ∈ 8–20 °C);
- the own non-HP slope of HP homes where whole-house and HP meters coexist.

Slopes are in kW/K, given as median [IQR] (n). Reference values from 07: s₀ CH 0.0054, GB 0.0126; CH own-load slope 0.018 per HP home.

## Task 1 — Candidates found

Ten candidates since the 04 inventory, four of them new:
- **BE home monitoring.** Two parquet sets in `data/` (`95951bd3-*` Mar–Dec 2024, `26b72e88-*` 2025) plus `DER_capacity_by_installation.csv`. 32 installations with per-room thermostats, a P1 meter, HP electricity and heat meters, PV inverters, batteries, and stovetop / ventilation / water-heater submeters. The metadata carry `c4a:` keys. **Provenance and licence are not on disk.**
- **Fluvius 2024 sample** (`P6269_..._Elek_2024_Deel_{1,2}.zip`). 2,400 residential meters at 15 min for 2024, 8 categories × 300 (HP / EV / PV combinations). Labels are flags only.
- **FeederBW** is now documented: Treutlein et al. 2026, *Scientific Data*; see `method_basis.md`.
- **HEAPO total-only households.** The HEAPO 15-min **total** meters of households not in B\* number 1,027 in cal2023 (≥ 90 % coverage). They have no HP submeter.

Listed and rejected without a criteria row:
- Pecan Street (no HP label);
- Irish CER 2009–10, Ausgrid solar homes 2012–13, Slovak smart meters (no HP field);
- the Swiss GWS building register (`HP_building_data/`, canton-level counts, no load);
- PLEIAData (a university building).

`sgsc-ct_*` on the Desktop is outside `data/` and was not inspected.

**Prior exposure:**
- **Paper A** used WPuQ (Tables V, VI), NEEA (Table II, cross-dataset fits), and RHPP, BPA, NREL and COFACTOR (Table VI, transfer) (`hp-sensitivity-paper/DATA.md`).
- **Legacy Paper B** scored FeederBW and WPuQ with estimators: `data/feederbw_paper_test.csv` and `capacity_wpuq_real_feeder.csv`, which I did not open; `results/iter00_baseline/REVIEW.md` reports legacy WPuQ errors.
- **Not used** by Paper A or Paper B: Fluvius 2024, BE monitoring, UKPN.

## Task 2 — Criteria table

Pilot calendars: B\* cal2023; GB-EoH Nov 2021 – Oct 2022 (main) and Oct 2022 – Sep 2023 (replication).

| Candidate | 1 HP label (type; quality; map to `HL`) | 2 Aggregation | 3 Temperature | 4 Local non-HP sample, s₀ | 5 Own-load observability | 6 Resolution, period; overlap with pilots | 7 Disjoint from B\* / GB-EoH | 8 Size; v1.1 envelope (no stacking) | 9 Access, licence |
|---|---|---|---|---|---|---|---|---|---|
| **NEEA HEMS v9.2** (US PNW) | HP circuits (ducted / ductless) plus backup-strip circuits per home. `HL` is computable from target data: 30-min p99.9 of HP + backup, water-heater circuits excluded. No nameplate. | semi-synthetic (homes) | on disk: outdoor probe per home (`TEMPERATURE15`) and NOAA station | **yes**, same region and period: 49 homes without electric heating with ≥ 330 full days (84 with any data; WA 21, ID 16, OR 11, MT 1). **Summer cooling breaks the all-days fit:** WA s₀ 0.0143 with T_h at bound and R² 0.03. With days T ≤ 18 °C: **WA 0.0268** (R² 0.69), ID 0.0139, OR 0.0153 — 2–5× CH. | **yes**, mains − HP − cooling circuits. Own slope s_res **0.0119 [0.0038–0.0334] (76)** without 04's selection; 0.0069 [0.0006–0.0141] (57) with it, because that rule keeps only s_res ≤ 0.2 s_heat. | 15 min; cal2023 on disk (release 2018-08 – 2025-06); overlaps B\* cal2023 and the GB replication year | yes, by country (US) | **77** HP homes (no gas furnace, no PV, s_heat > 0.05; WA 37, OR 31, ID 9); 57 under 04's rule. Envelope (57 / 49): 15 test HP per split, 45 test substations (20 / 20 / 5 / **0** per bin), max feeder 10 dwellings. Fill-limited. | NEEA data-use terms (not redistributable); **more years need a data request** |
| **FeederBW** (DE, Netze BW) | registry `heat_pumps_kW` per feeder: 123 of 200 feeders > 0; median 9.4 kW [5.2–19.5]; 0.28 kW per housing unit. Semantics (electrical? connection request?) **UNVERIFIED**. `HL` needs registry→peak; no source-only mapping (CH nameplate→peak n = 1; GB `HP_Size` is thermal: 0.48) | **real feeders**: 200, housing units 32 [18–47]; HP kW changes in 41 feeders | on disk, per feeder (hourly; v2 of the paper says 1–3 h forecasts) | label-free route only via feeders with no HP and no electric heating registered (24). Their s₀ per housing unit is 0.0275 [0.0041–0.0752] (12 fits inside the bounds), inflated by commerce and PV. **Without PV or commerce: 0.0032–0.0040 (3 feeders, 1 at T_h bound)**. 2 fits failed (negative daily load from PV), listed in `feederbw_s0.csv`. Selecting the feeders uses the registry. | **no**: embedded in the feeders, not separable | 15 min (1 min upstream); Apr 2023 – Mar 2025, full days 366 / 366 in year 1 (median); overlaps B\* 2023 and the GB replication year | yes, by country | **storage / electric heaters registered on 165 of 200 feeders**. Feeders with HP > 0 and no electric heating: **11**; no HP and no electric heating: 24 | CC BY 4.0 per paper page (Zenodo licence not checked) |
| **Fluvius 2024** (BE) | `Warmtepomp_Indicator` (count only); no capacity, no submeter. `HL` needs a transferred per-HP peak, so the label would be model-based. | semi-synthetic from real whole-house meters | **not on disk** (the Solcast files are irradiance only): download KMI or Open-Meteo 2024 | **yes**, same region and year: 300 meters with no HP, no PV, no EV, complete (`geen_ZP`). s₀ not computable without T. | embedded: the HP homes' gross whole-house load includes it (300 HP, no PV, no EV); not separable | 15 min; cal2024; no overlap | yes (BE); `EAN_ID` disjoint between files; not linkable to 2022 | 300 HP + 300 fill → 75 test HP per split, 125 test substations (35 / 40 / 20 / 30), max feeder 80 at p = 0.2 | Fluvius open data (licence page not retrieved) |
| **BE home monitoring** (`c4a`) | HP submeter: `HL` computable (HP + buffer resistor; water heater is own load). DER table: "Heat pump electrical peak" 3.79 kW [2.97–4.66] (18), definition unknown. | homes (possibly one development: installation ids 152–443, the same submeter layout; not documented) | on disk: HP outdoor-air sensor in 18 homes | none in the set; would come from Fluvius 2024 (`geen_ZP`, same region) | **yes**: P1 (signed net) + \|PV\| − HP − buffer. 6 HP homes without battery: per-home slopes 0.023–0.037 (2 at T_h = 20 °C bound, 1 inside the bounds), 0.0049 / 0.0007 / 0 for three others; R² ≤ 0.45. **Weak.** PV sign flips between homes; 12 homes have batteries. | 15 min; Mar 2024 – Dec 2025; HP meter renamed in 2025 (`hp` → `hp1`) | yes, by country | HP + P1 ≥ 90 % in cal2025: **9** (5 with T) → no v1.1 substation (2 test HP per split; ≥ 3 per station needed) | **provenance and licence unknown** |
| **UKPN LV feeders + LCT** (GB) | LCT register: 384 HP rows (substations), 3,730 connections, 8 [7–11] per substation; Import kW 49 [35–68] per row (kW per substation row, semantics UNVERIFIED) | real LV feeders (2,061; 19 devices per feeder); HP register at secondary substation, not feeder; only 17 HP substations appear in the feeder file | not on disk | no non-HP household sample | no | 30 min; **June 2024 only: no heating season** | not checkable (anonymised). 44 GB-EoH main-window homes are in BN / TN / RH / KT postcode areas, which UKPN may serve (UNVERIFIED) | — | UKPN open data (portal needs a login; licence UNVERIFIED); winter months would need downloading |
| **HEAPO beyond B\*** (CH) | 15-min HP submeter outside B\*: 1–3 households per window. 1,027 total-only meters (cal2023) are HP homes with a count label only. Nameplate (protocols) for 66 households not in B\*; source mapping nameplate→peak has n = 1 (1.14). | semi-synthetic | on disk (HEAPO stations) | only the Kaiser fill of B\*, already used: **not a new s₀** | no for total-only homes | 15 min; 2019–2024 | IDs disjoint from B\* (set difference) | HP-labelled: < 6, too small; count-only: large | CC BY 4.0 |
| **Kaiser cal2024** (CH) | as B\* | semi-synthetic | on disk | Kaiser fill (same homes as B\*) | yes (as B\*) | cal2024 | **no: temporal, 22–24 of the same paired homes (04)** | as B\* | CC BY 4.0 |
| **WPuQ** (DE, 2019–20) | HP submeter (p99.9 computable) | semi-synthetic, 37 homes, one village | on disk | **none**: every home has an HP | yes: own slope 0.0064 [0.0049–0.0094] (19 inside the bounds); aggregate / n 0.0048 | 15 min; 2019–2020; no overlap | yes, by country | 37 HP, no fill | CC BY 4.0. **Used by Paper A and legacy Paper B with errors seen** |
| **RHPP** (+ LCL fill) (GB 2013–15) | installer net capacity (thermal; peak / label 0.47) | semi-synthetic | none in data (HadCET or Heathrow on disk) | LCL, the same filler population as GB-EoH: **not new** | no | 2 min; 114 homes Nov 2013 – Feb 2014 | not linkable to EoH (different scheme and years) | 114 HP | UKDS EUL. **Used by Paper A (Table VI)** |
| **LCL HP trial** | none | — | per home | — | no | 15 min, 9 homes | — | 9 | not documented |
| **EoH outside GB-EoH** | as GB-EoH | — | — | LCL (spent) | no | — | partly the same homes | hybrids or low coverage | — |
| **BPA HPHC / NREL CCASHP** (US) | HP submeter (hourly) | — | per home | none (HP only); NEEA homes would be the only PNW fill | no | hourly | yes | 31 / 11 homes with a season | DOE database. **Used by Paper A (Table VI)** |
| **COFACTOR / Carleton** | blocks; gas-heated houses | — | — | — | — | — | — | — | not usable |

## Task 3 — Rung requirements per viable candidate

Viable means it passes 1 (a capacity label mappable to `HL`), 4 (a new local non-HP sample) and 7 (unseen):
- **NEEA** passes all three.
- **FeederBW** passes with a noisy label.
- **Fluvius 2024** passes 4 and 7 but has no capacity label, so it is viable only for a count-labelled side check.
- BE monitoring is too small for a target. It is an own-load source at most.

Estimator forms:
- **(a) `paperA_corr`, local s₀, transferred m_h:** P̂ = max(s_h(net) − N·s₀,loc, 0) / m_h,src.
- **(b) (a) plus an own-load term.** n_HP is unknown, so the term must enter the scale:
  - **(b-i) transferred ratio:** m̂_h = m_h,src + ρ_src·s₀,loc / P̄_src, with ρ = own slope / filler slope and P̄ = mean `HL` per HP home, both from the source. ρ_src is CH 0.018 / 0.0054 = 3.3. GB has no whole-house meter, so only CH supplies ρ.
  - **(b-ii) local pilot (whole-house − HP):** m_h′ = [s_h(whole-house of local pilot homes) − n_pilot·s₀,loc] / P_pilot, as `paperA_corr_own`. It uses target labels on pilot homes (household-disjoint from test), so it is **not fully label-free**.
- **(c) frozen 07 rows:** L1 TabPFN and H\* (TabPFN L2), both source pools, as comparison.

| | NEEA (recommended) | FeederBW (fallback) | Fluvius 2024 (side check only) |
|---|---|---|---|
| (a) | yes. s₀ from the 49–84 fill homes; **a heating-side fit window must be pre-registered** (all-days fit hits the bound; T ≤ 18 °C works: R² 0.24–0.69) | yes, with N = housing units; s₀ from feeders with no HP and no electric heating (uses registry zeros, so state it); commerce and PV contaminate s₀ | s₀ yes once T is downloaded; no capacity label to score |
| (b-i) | yes; ρ_src = 3.3 (CH). The target's own ratio is about 0.4–0.9 (0.0119 against 0.014–0.027), so **ρ does not look transferable**: the main risk | yes, same risk; not checkable (no own load) | — |
| (b-ii) | **yes**: whole-house and HP meters on the same homes (pilot homes from the train split) | no | no (BE homes are too few and from one development) |
| (c) | yes. Needs the 07 input pipeline at 30 min; N ≤ 10 sits at the lower edge of the 06 grid (sizes 10–120), and US climate is out of domain | yes (real feeders, N = housing units; registry label) | no label |
| label mapping | p99.9 of HP + backup circuits at 30 min: from target data, no transfer | registry kW → `HL`: no source mapping available. Score against registry kW with a sensitivity band (EoH 0.48 is thermal, so not applicable) | count × transferred peak (model-based) |
| effort | `pools/neea.py` ≈ 150 lines (circuits → HL, mains − HP own load, fill, state stations) + heating-window rule ≈ 20; **2–3 days** after the download | real-feeder builder ≈ 100–120 lines (part in `hp_capacity.feederbw_targets`, legacy); **1–2 days** | T download + label rule; ≈ 1 day |
| risks | fill-limited feeders (≤ 10 dwellings, ≤ 15 test HP per split) give noisy slopes; cooling season; US stock (s₀ 2–5× CH); Paper A Table II exposure (fits, not capacity errors: verify); the 04 "fully submetered" rule selects on own load and must not be reused | label semantics unverified; electric heating on 165 / 200 feeders leaves 11 clean HP feeders; legacy notebook estimates on FeederBW exist (seen in 2025) | no capacity label; would test s₀ only |
