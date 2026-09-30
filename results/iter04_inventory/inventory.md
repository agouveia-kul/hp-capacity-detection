# Iteration 04 - dataset inventory

Source: `scripts/audit/inventory_v2.py` (config `iter04_inventory`); EoH via `scripts/audit/eoh_convert.py`. Complete heating season = Nov-Mar with >= 90 % valid samples of the unit's key channel (EoH: whole-system electricity, 30-min bin valid with >= 12 of 15 two-minute diffs; RHPP: days with >= 80 % of 2-min slots; field studies: hourly HP_system_pwr_kW).

## Summary

| dataset | unit | units_total | hp_submeter_units | hp_submeter_units_>=1_season | whole_house_units | resolution | period |
|---|---|---|---|---|---|---|---|
| EoH (UKDS SN 9050) | home (HP system only) | 742 | 739.0 | 629.0 | 0.0 | 2 min (converted to 30 min) | 2020-10 .. 2023-09 |
| RHPP Sample B2 (UKDS SN 8151) | home (HP system only) | 418 | 418.0 | 169.0 | 0.0 | 2 min | 2012-02 .. 2015-03 |
| LCL heat-pump trial (lcl_heatpump/) | home (HP only) | 9 | 9.0 | 6.0 | 0.0 | 15 min (cumulative kWh) | 2011-12 .. 2014-03 |
| LCL smart meters (UKDS SN 7857) | household | 5198 | 0.0 |  | 5198.0 | 30 min | 2011-11 .. 2014-02 (consumption_d) |
| NEEA HEMS v9.2 (2023 on disk) | home (whole home + circuits) | 419 | 205.0 | 0.0 | 397.0 | 15 min | 2023-01 .. 2023-12 on disk (release 2018-08 .. 2025-06) |
| BPA HPHC (US PNW) | home (HP system only) | 57 | 57.0 | 31.0 | 0.0 | hourly | 2022-05 .. 2025-04 |
| NREL CCASHP (US cold climate) | home (HP system only) | 12 | 12.0 | 11.0 | 0.0 | hourly | 2020-12 .. 2023-05 |
| COFACTOR DS1 (Oslo/Baerum) | apartment block (building) | 29 | 3.0 |  | 29.0 | hourly |  |
| Carleton (Ottawa, 12 houses) | house | 12 | 0.0 |  | 12.0 | 1 min | 2009-07 .. 2010-09 (README) |
| Pecan Street 15-min (austin) | home | 25 | 0.0 |  | 25.0 | 15 min | 2018-01 .. 2018-12 |
| Pecan Street 15-min (newyork) | home | 25 | 0.0 |  | 25.0 | 15 min | 2019-05 .. 2019-10 |
| HEAPO / Kaiser / WPuQ beyond B* | household | 86 | 52.0 |  |  | 15 min |  |
| Fluvius 15-min (Flanders) | household meter (net) | 1300 | 0.0 |  | 1300.0 | 15 min | 2022-01 .. 2022-12 |
| FeederBW (200 LV feeders, DE) | feeder | 200 |  |  |  | 15 min | 2023-04 .. 2025-03 (metadata dates) |
| UKPN LV feeder smart-meter aggregates + LCT register | LV feeder / secondary substation | 2061 |  |  |  | 30 min | 2024-06-01 .. 2024-06-30 |
| dataset.zip (zip index only) |  | 2447 |  |  |  |  |  |
| pleiadata.zip (zip index only) |  | 30 |  |  |  |  |  |

## Details

### EoH (UKDS SN 9050)

- **unit:** home (HP system only)
- **units_total:** 742
- **empty_files:** 3
- **hp_submeter_units:** 739
- **hp_submeter_units_>=1_season:** 629
- **whole_house_units:** 0
- **resolution:** 2 min (converted to 30 min)
- **period:** 2020-10 .. 2023-09
- **complete_seasons_per_unit:** 0: 113, 1: 267, 2: 351, 3: 11
- **units_per_season:** {'2020/21': 18, '2021/22': 524, '2022/23': 460}
- **units_with_heat_meter_>=1_season:** 608
- **weather:** T_ext per home (local weather station), >=50% of 30-min bins in 737 homes; no coordinates on disk
- **capacity_label:** robust peak (P_ws); HP_Size_kW and MCS_SHLoad exist only in the USmart Property/Design/Installation table (not on disk)
- **hp_type:** ASHP/HT-ASHP (inferred): 549 / hybrid: 151 / GSHP: 39 / empty: 3 (from channels; HP_Installed not on disk)
- **backup_channels:** immersion (P_ih) 379, back-up heater (P_buh) 24
- **dhw_channels:** DHW flow temperature 583 (no separate DHW heat/electricity)
- **building_metadata:** none on disk (House_Form, House_Age, floor area, tenure are in the USmart table)
- **location:** none on disk (Postcode_1 in the USmart table)
- **licence:** Open Government Licence v2.0 (UKDA_Study_9050_Information.htm); cite DOI 10.5255/UKDA-SN-9050-2

### RHPP Sample B2 (UKDS SN 8151)

- **unit:** home (HP system only)
- **units_total:** 418
- **hp_submeter_units:** 418
- **hp_submeter_units_>=1_season:** 169
- **whole_house_units:** 0
- **resolution:** 2 min
- **period:** 2012-02 .. 2015-03
- **complete_seasons_per_unit:** 0: 249, 1: 169
- **units_per_season:** {'2012/13': 32, '2013/14': 101, '2014/15': 36}
- **units_with_heat_meter_>=1_season:** 169
- **weather:** none in data (T_in is evaporator/ground-loop temperature); national HadCET used by Paper A
- **capacity_label:** installer net capacity (kW) for 405 of 418; robust peak
- **hp_type:** ASHP: 319 / GSHP: 99 (on-off/inverter not recorded)
- **backup_channels:** E_sp > 0: 23, E_boost > 0: 10
- **dhw_channels:** E_dhw > 0: 225; H_hw and T_wf (cylinder flow)
- **building_metadata:** property type 64, age 115, emitter 418, tenure (Site.type RSL/Domestic) 418
- **location:** none
- **licence:** UKDS End User Licence (not redistributable)
- **notes:** 0 sites flagged 'Monitoring Problem'

### LCL heat-pump trial (lcl_heatpump/)

- **unit:** home (HP only)
- **units_total:** 9
- **hp_submeter_units:** 9
- **hp_submeter_units_>=1_season:** 6
- **whole_house_units:** 0
- **resolution:** 15 min (cumulative kWh)
- **period:** 2011-12 .. 2014-03
- **complete_seasons_per_unit:** 0: 3, 2: 6
- **weather:** external_temperature per home
- **capacity_label:** none
- **hp_type:** not recorded
- **backup_channels:** immersion_heater_energy_consumption in 5
- **dhw_channels:** cylinder pipe temperatures
- **building_metadata:** none
- **location:** London (trial)
- **licence:** not documented on disk

### LCL smart meters (UKDS SN 7857)

- **unit:** household
- **units_total:** 5198
- **hp_submeter_units:** 0
- **whole_house_units:** 5198
- **resolution:** 30 min
- **period:** 2011-11 .. 2014-02 (consumption_d)
- **weather:** none (London)
- **capacity_label:** none
- **hp_type:** survey Q248: gas boiler central heating 2140, 'heat pump' mentioned 0, electric 265 of 2785 surveyed
- **building_metadata:** survey (appliances, heating)
- **location:** London
- **licence:** UKDS (open data edition)
- **notes:** standard tariff 4173, dynamic ToU 1025 households (header counts)

### NEEA HEMS v9.2 (2023 on disk)

- **unit:** home (whole home + circuits)
- **units_total:** 419
- **hp_submeter_units:** 205
- **whole_house_units:** 397
- **hp_submeter_units_>=1_season:** 0
- **resolution:** 15 min
- **period:** 2023-01 .. 2023-12 on disk (release 2018-08 .. 2025-06)
- **complete_seasons_per_unit:** 0 (only calendar 2023 on disk: Jan-Mar and Nov-Dec of different seasons)
- **weather:** outdoor-air probe per home (TEMPERATURE15) + NOAA station id
- **capacity_label:** robust peak only
- **hp_type:** ducted 128, ductless 81 (air-source, US)
- **backup_channels:** electric furnace / baseboard / zonal circuits
- **dhw_channels:** water-heater circuits (ERWH, HPWH)
- **building_metadata:** RBSA tables (not on disk)
- **location:** state + NOAA station ({'WA': 205, 'OR': 140, 'ID': 65, 'MT': 9})
- **licence:** NEEA data-use terms (not redistributable)
- **notes:** HP + mains: 195; fitted (>= 120 full days, >= 30 below 10 C): 139; heating fully submetered (s_heat > 0.05 kW/K, residual slope <= 20 % of it, no gas-furnace circuit): 57 ({'WA': 28, 'OR': 22, 'ID': 7}), of which with solar 2

### BPA HPHC (US PNW)

- **unit:** home (HP system only)
- **units_total:** 57
- **hp_submeter_units:** 57
- **hp_submeter_units_>=1_season:** 31
- **whole_house_units:** 0
- **resolution:** hourly
- **period:** 2022-05 .. 2025-04
- **complete_seasons_per_unit:** 0: 26, 1: 25, 2: 6
- **weather:** OA_temp_F per home
- **capacity_label:** none in files (robust peak)
- **hp_type:** air-source (ducted, US)
- **backup_channels:** backup_system_kW > 0.1 kW in 48
- **location:** site code (utility)
- **licence:** US DOE Heat Pump Database

### NREL CCASHP (US cold climate)

- **unit:** home (HP system only)
- **units_total:** 12
- **hp_submeter_units:** 12
- **hp_submeter_units_>=1_season:** 11
- **whole_house_units:** 0
- **resolution:** hourly
- **period:** 2020-12 .. 2023-05
- **complete_seasons_per_unit:** 0: 1, 1: 5, 2: 6
- **weather:** OA_temp_F per home
- **capacity_label:** none in files (robust peak)
- **hp_type:** air-source (ducted, US)
- **backup_channels:** auxheat_pwr_kW > 0.1 kW in 11
- **location:** site code (utility)
- **licence:** US DOE Heat Pump Database

### COFACTOR DS1 (Oslo/Baerum)

- **unit:** apartment block (building)
- **units_total:** 29
- **hp_submeter_units:** 3
- **whole_house_units:** 29
- **resolution:** hourly
- **hp_type:** space-heating sources: {'DH': 17, 'EH, EFH': 5, 'GSHP, EB, EFH': 2, 'EB, EFH': 2, 'DH, EFH': 2, 'GSHP, EB': 1}
- **weather:** Tout per building
- **capacity_label:** none
- **building_metadata:** year, floor area, 1582 apartments in total
- **location:** Oslo / Baerum
- **licence:** CC BY 4.0

### Carleton (Ottawa, 12 houses)

- **unit:** house
- **units_total:** 12
- **hp_submeter_units:** 0
- **whole_house_units:** 12
- **resolution:** 1 min
- **period:** 2009-07 .. 2010-09 (README)
- **hp_type:** space heating: {'natural gas': 12} (furnace fan and AC submetered)
- **capacity_label:** none
- **licence:** free with citation (README)

### Pecan Street 15-min (austin)

- **unit:** home
- **units_total:** 25
- **hp_submeter_units:** 0
- **whole_house_units:** 25
- **resolution:** 15 min
- **period:** 2018-01 .. 2018-12
- **hp_type:** air1 (AC or HP compressor) circuit in 24, furnace/heater circuit in 24; heat pumps not labelled, so no HP submeter can be identified
- **capacity_label:** none
- **licence:** Dataport academic licence (not redistributable)

### Pecan Street 15-min (newyork)

- **unit:** home
- **units_total:** 25
- **hp_submeter_units:** 0
- **whole_house_units:** 25
- **resolution:** 15 min
- **period:** 2019-05 .. 2019-10
- **hp_type:** air1 (AC or HP compressor) circuit in 11, furnace/heater circuit in 19; heat pumps not labelled, so no HP submeter can be identified
- **capacity_label:** none
- **licence:** Dataport academic licence (not redistributable)

### HEAPO / Kaiser / WPuQ beyond B*

- **unit:** household
- **units_total:** 86
- **hp_submeter_units:** 52
- **resolution:** 15 min
- **notes:** B* HP households 86. HEAPO 15-min HP+other, any heating season: 48 distinct, 5 not in B* (per season {'2019/20': 1, '2020/21': 3, '2021/22': 14, '2022/23': 46}); no HEAPO 15-min season after 2022/23. Kaiser paired dwelling+HP: 26 distinct ({'2023/24': 22, 'cal2023': 24, 'cal2024': 24}), 2 not in B*. Kaiser HP meters without dwelling meter: 84 ({'Apartment building': 66, 'Single-family house': 15, 'Underground garage': 3}); the non-SFH ones serve whole buildings. WPuQ HP+household: 34 distinct ({'2019/20': 30, 'cal2019': 32, 'cal2020': 27})
- **licence:** CC BY 4.0

### Fluvius 15-min (Flanders)

- **unit:** household meter (net)
- **units_total:** 1300
- **hp_submeter_units:** 0
- **whole_house_units:** 1300
- **resolution:** 15 min
- **period:** 2022-01 .. 2022-12
- **capacity_label:** HP flag only (Warmtepomp_Indicator = 1 for 300 meters)
- **hp_type:** not recorded
- **weather:** none (candidate: KMI Uccle / ERA5)
- **location:** Flanders (no finer)
- **notes:** contract categories {'Residentieel': 1300}; median rows per meter 35040
- **licence:** Fluvius open data (not documented on disk)

### FeederBW (200 LV feeders, DE)

- **unit:** feeder
- **units_total:** 200
- **resolution:** 15 min
- **period:** 2023-04 .. 2025-03 (metadata dates)
- **capacity_label:** registered heat_pumps_kW > 0 in 123 feeders; storage/electric heaters also registered
- **weather:** weather_data.parquet
- **licence:** see FeederBW docs

### UKPN LV feeder smart-meter aggregates + LCT register

- **unit:** LV feeder / secondary substation
- **units_total:** 2061
- **resolution:** 30 min
- **period:** 2024-06-01 .. 2024-06-30
- **capacity_label:** LCT register: 384 heat-pump rows at 384 secondary substations (types {'Heat Pump': 384})
- **licence:** UKPN open data

### dataset.zip (zip index only)

- **units_total:** 2447
- **notes:** Kaiser et al. Swiss smart meters archive (smart_meter_data/*.csv + tariff_data.csv); same content as data/Swiss_dataset

### pleiadata.zip (zip index only)

- **units_total:** 30
- **notes:** PLEIAData (Data_Nature/processed_data: room, HVAC and consumption of a university building); not residential
