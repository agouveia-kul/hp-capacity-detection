# Iteration 04 — Usability matrix and pool envelopes

Sources: counts from `scripts/audit/inventory_v2.py` (→ `inventory.md/.csv`), envelopes from `scripts/audit/envelope_v2.py` (→ `envelopes.md`, full per-station tables), EoH conversion `scripts/audit/eoh_convert.py`, hplib check `scripts/audit/hplib_check.py`. Config `configs/iter04_inventory.yaml`. "Season" = Nov–Mar with ≥ 90 % valid samples.

## 1. Usability matrix

Criteria (from the iteration file): **P** HP submeter ≤ 30 min, ≥ 1 complete season, capacity label, same-period/climate non-HP load, ≥ 30 HP households per climate region · **T** net load (real or constructible) + capacity label, population ≠ B\* · **C** same HP households over ≥ 2–3 seasons · **S** HP electricity **and** heat output with outdoor temperature (+ flow temperature, type/capacity) · **R** real feeder measurement with registered HP/TCL counts or kW.

| Dataset | P – capacity pool | T – transfer | C – change detection | S – simulation | R – real aggregate |
|---|---|---|---|---|---|
| **EoH (SN 9050 + USmart property table)** | **partial (fill only).** 739 homes with 2-min HP-system data; 505 non-hybrid homes with ≥ 1 season (2021/22: 433, 2022/23: 370); robust peak computable; **rated size `HP_Size_kW` and MCS design heat load for every home**; postcode district for every home; 30 shared weather-station groups (Edinburgh/Fife, Tyneside, Borders, SE England), **3 with ≥ 30 HP**. **No whole-house load** → fill must come from another dataset (the only household electricity is annual pre-install bills, 220 of 742) | **yes (constructed).** GB population, 30-min, different climate/stock/control from B\* | **partial.** 300 non-hybrid homes with both 2021/22 and 2022/23; only 11 have 3 seasons | **yes.** Heat meter in 608 homes with a complete season; SH and DHW flow temperature, return, T_ext per home, internal temperature; type (`HP_Installed`: ASHP / HT-ASHP / GSHP / hybrid), brand/model, rated size, design heat load and design flow temperature | no |
| **RHPP B2 (SN 8151)** | **partial.** 418 sites, 2-min; only 169 with a complete Nov–Mar season (B2 is one year per site, any start month); **114** cover Nov 2013–Feb 2014 at ≥ 90 %; **installer capacity for 405/418**; no outdoor temperature, no location (single GB region, HadCET) | **yes (constructed with LCL fill, concurrent)** | no (one year per site) | **partial.** Heat output, flow and condenser temperatures, DHW/boost split, type; **no outdoor-air temperature** (T_in is refrigerant/ground loop) | no |
| **LCL smart meters (SN 7857)** | fill only: 5 198 households (30 min, 2011-11 → 2014-02); 5 093 cover 2012/13 at ≥ 90 %, 4 796 cover Nov 13–Feb 14 | fill for GB pools | no | no | no |
| **LCL HP trial (`lcl_heatpump/`)** | no: 9 homes, 6 with 2 seasons, no capacity label, no whole-house load | no | too small (6) | no heat output | no |
| **NEEA HEMS (2023 on disk)** | **no.** 205 homes with a HP circuit, 195 also with mains; 139 fitted; **57 with heating fully submetered** (criterion below) — WA 28 / OR 22 / ID 7, none ≥ 30; **0 complete seasons on disk** (calendar 2023 only; the release covers 2018-08 → 2025-06) | **partial.** Real whole-home + circuits, US PNW; label = robust peak only; would need the 2022/23 and 2023/24 power files | not on disk (would be yes with 2018–2025 files) | no heat output | no |
| **BPA HPHC** | no: HP only, hourly, no non-HP load | no (only with synthetic fill; Paper A did that) | partial: 6 of 57 with 2 seasons | partial: HP + backup electricity and T_out; no heat output | no |
| **NREL CCASHP** | no: 12 sites, hourly | no | partial: 6 with 2 seasons | partial: power split (ODU, fan, aux) + T_out; no heat output in files used | no |
| **COFACTOR DS1** | no: 29 apartment **blocks**; 3 with GSHP space heating (block level) | partial (block-level HP, Oslo) | no | partial (6499 has heat and electricity of HP) | partial (block = small aggregate, no count) |
| **Carleton** | no: 12 gas-heated houses (furnace fan and AC only) | no | no | no | no |
| **Pecan Street (on disk)** | no: 25 Austin homes (2018) + 25 New York homes (2019-05 → 10); heat pumps not labelled | no | no | no | no |
| **HEAPO / Kaiser / WPuQ beyond B\*** | +5 HEAPO 15-min households (seasons 2019/20–2021/22, no concurrent Kaiser fill) and +2 Kaiser paired (cal2024); 69 extra Kaiser HP meters are 66 apartment buildings + 3 garages (not households); no HEAPO 15-min season after 2022/23 | WPuQ 2019/20: 30 HP+household (existing stress test) | HEAPO multi-season (iteration 01 inventory) | no heat output | no |
| **Fluvius 15-min** | no submeter; 1 300 residential meters (2022), **300 flagged HP** | **partial.** Real household net load + HP flag (count label only), Flanders; no weather on disk | no (one year) | no | constructible aggregates of real meters (count label only) |
| **FeederBW** | – | yes (existing) | 2 years (2023-04 → 2025-03) | no | **yes:** 200 feeders, registered `heat_pumps_kW` > 0 in 123 |
| **UKPN LV + LCT** | – | partial (one month, June 2024: no heating season) | no | no | **partial:** 2 061 LV feeders, 30 min, June 2024 only; LCT register 384 HP rows at 384 secondary substations |
| `dataset.zip` / `pleiadata.zip` | duplicate of Kaiser (`Swiss_dataset`) / PLEIAData university building | – | – | – | – |

NEEA "heating fully submetered" criterion: home has a HP circuit and its own `Mains`; ≥ 120 full days (all circuits ≥ 90/96 samples) and ≥ 30 below 10 °C; the hockey-stick slope of (mains − heating − cooling circuits) is ≤ 20 % of the metered heating slope, the heating slope is > 0.05 kW/K, and no `Gas Furnace (Component)` circuit. Temperature = own outdoor probe, else the mean of probes at the same NOAA station.

## 2. Candidate pools under protocol v1 rules

Rules reused unchanged from `scripts/paperb/`: household-disjoint 75/25 split (HP stratified by station, fill global), grid sizes 10–120 × p 0.05–1.0, `max_overlap` 0.75, ≥ 3 HP per station and split, 10 train / 5 test substations per cell; 20 split seeds. B\* reproduces 03b exactly (75 / 40 / 10 / 5 test substations, 62 / 20 HP households used).

| pool | HP hh | stations (≥ 30 HP) | train / test HP used | fill | test subs ≤15 / 15–35 / 35–65 / >65 % | total |
|---|---|---|---|---|---|---|
| **B\*** (cal2023, reference) | 86 | 5 (1) | 62 / 20 | 1 291 Kaiser | 75 / 40 / 10 / 5 | 130 |
| **GB-EoH 2021/22** (non-hybrid) | 433 | 29 (3) | **309 / 90** | 5 093 LCL | 265 / 145 / 30 / 15 | 455 |
| GB-EoH 2022/23 (non-hybrid) | 370 | 26 (3) | 264 / 71 | 5 093 LCL | 190 / 110 / 30 / 15 | 345 |
| GB-EoH 2020/21 | 18 | 4 (0) | 11 / 0 | – | 0 | 0 |
| **GB-RHPP** Nov 13–Feb 14 | 114 | 1 "GB" (1) | 86 / 28 | 4 796 LCL (concurrent) | 50 / 35 / 15 / 10 | 110 |
| B\*+ | 86 + 7 | – | extras fall in windows without concurrent fill or in cells < 3 HP → **envelope identical to B\*** | | | |
| US-NEEA cal2023 | 57 | 3 (0) | 42 / 13 | 49 NEEA non-electric-heat homes | 20 / 20 / 5 / 0 | 45 |

Max feeder size (best test station, median over seeds; grid ≤ 120 / uncapped): B\* p = 0.2: 40 / 60, p = 1: 10 / 12. GB-EoH 2021/22 p = 0.2: 120 / 127, p = 0.5: 40 / 51, p = 1: 20 / 25. GB-RHPP and GB-EoH 2022/23 p = 0.2: 80 / 105, p = 1: 20 / 21. US-NEEA is fill-limited (49 dwellings): p = 0.2: 10 / 15. The top bin is thin in every pool because the grid has only one p > 0.65 value (p = 1.0); ≥ 20 per bin needs more substations per cell or an extra p (e.g. 0.8), not more households.

## 3. Fill mismatch (for pools whose fill comes from another dataset)

| pool | HP period / climate | fill period / climate | mismatch |
|---|---|---|---|
| GB-EoH | Nov 2021–Mar 2022 (or 2022/23); 29 weather-station groups: Edinburgh/Fife/Borders (Warmworks), Tyneside (E.ON), SE England (OVO) | LCL, London, 2011-11 → 2014-02 | **8–10 years** (appliance stock, lighting, COVID-era occupancy vs 2012); London vs Scotland / NE / SE England weather → the fill's weather-driven load is not aligned in time with the substation temperature unless days are re-matched |
| GB-RHPP | Nov 2013–Feb 2014, GB-wide, no location | LCL, London, same window | concurrent; spatial mismatch unknown (RHPP has no location); 4-month window, not a full season |

Fill temperature response, LCL (daily mean per dwelling vs HadCET, Jul 2012–Jun 2013, hockey-stick, T_h free in 8–20 °C): **all 4 329 households s₀ = 0.0133 kW/K** (T_h 14.2 °C, R² 0.84), **2.4× B\*'s 0.0055**; gas-heated with no portable electric heater (survey subset, 78 households) s₀ = 0.0070 kW/K (R² 0.60). Choosing the "clean" LCL subset brings s₀ close to B\* but shrinks the fill pool to the ~80 surveyed households, which caps feeder size (like NEEA).

## 4. Population notes

- EoH 2021/22 non-hybrid (433): 249 ASHP, 158 HT-ASHP, 26 GSHP (`HP_Installed`); 154 hybrids excluded (boiler counter unreliable: 724 k negative 2-min diffs). Channel-inferred types agreed with `HP_Installed` for all but 4 monitored homes (3 hybrids without a boiler meter, 1 HT-ASHP with brine channels).
- Rated size `HP_Size_kW` median **8.5 kW** (IQR 7.0–11.2); MCS design heat load median 6.9 kW (IQR 5.0–8.5); **oversizing HP_Size / MCS_SHLoad median 1.21 (IQR 1.06–1.38)**. Robust 15-min electrical peak median **3.8 kW** (IQR 3.3–5.0), i.e. **0.48 × rated size** (IQR 0.41–0.55; RHPP 0.47), vs B\* HP_Peak median 5.4 kW (IQR 4.0–8.6). Immersion + back-up = 1.7 % of HP-system energy (median; > 5 % in 76 of 433 homes).
- Stock: 197 detached, 122 semi, 87 terraced, 27 flats; floor area median 101 m² (IQR 83–130); all age bands, most 1945–1980.
- RHPP window homes: robust peak median 3.9 kW vs installer capacity median 8.5 kW (peak/label median 0.47; label is thermal "net capacity"); 94 ASHP / 20 GSHP.
- Timestamps: EoH has no gap or duplicate at the DST changes → UTC/GMT; RHPP and LCL as in Paper A.
