# 05a Task 1 - LCL filler audit

Source: `scripts/paperb/iter05a_report.py --part lcl`, cache `fill_analog.build_lcl` (config `protocol_v1_1`).

## 1. Release on disk

| file | bytes |
|---|---|
| csv/data_collection/readme_v0-13.pdf | 264769 |
| csv/data_collection/data_tables/consumption_d.csv | 199768439 |
| csv/data_collection/data_tables/consumption_n.csv | 798611867 |
| csv/data_collection/data_tables/survey_answers.csv | 4614612 |
| csv/data_collection/data_tables/survey_questions.csv | 37515 |
| csv/data_collection/data_tables/tariff_d.csv | 495757 |
| csv/data_collection/references/lcl_learning_report_a2_residential_consumer_attitudes_to_time_varying_pricing.pdf | 4749768 |
| csv/data_collection/references/lcl_learning_report_a3_residential_consumer_responsiveness_to_time_varying_pricing.pdf | 4348835 |
| csv/data_collection/references/schofield-j-2015-phd-thesis.pdf | 4952331 |
| csv/data_collection/survey_forms/survey_appliance.pdf | 241139 |
| csv/data_collection/survey_forms/survey_attitudes.pdf | 1292511 |
| 7857_file_information.rtf | 56896 |
| mrdoc/pdf/7857_userguide.pdf | 385294 |
| read7857.htm | 2956 |
| mrdoc/UKDA/UKDA_Study_7857_Information.htm | 2754 |

UKDS SN 7857 edition 2 (DOI 10.5255/UKDA-SN-7857-2, 'Low Carbon London Project: Data from the Dynamic Time-of-Use Electricity Pricing Trial, 2013', distributed Aug 2024). Consumption: one column per household (kWh per half hour) and a `GMT` stamp; the tariff is given by the file, not a column: `consumption_n.csv` = standard flat rate (**4173** households, ids N....), `consumption_d.csv` = dynamic time-of-use (**1025**, ids D....), total 5198. Stamps 2011-11-23 09:00:00 .. 2014-02-28 00:00:00, regular 30-min grid True with no gap or duplicate at the DST changes, i.e. UTC. Extra fields: appliance/attitude survey (2770 households, 2785 rows, 344 answer columns) and the 2013 ToU price schedule (`tariff_d.csv`). Against the public London Datastore release (5,567 households, Nov 2011 - Feb 2014, `Std`/`ToU` column; figure from the iteration brief, not re-checked here) this is a **subset in households** (369 fewer) and a **superset in fields** (survey, price schedule).

## 2. The 'gas-only' subset of iteration 04

Traced to `scripts/audit/envelope_v2.py::lcl_scan` (04): `gas` = survey answer column `Q248` contains 'gas boiler' and 'central heating'; `clean` = gas and answer column `Q304` = 0 ('Paper A: Q304 = portable electric heaters'); s0 = 0.0070 kW/K on 78 households. It comes from the survey, not from electricity, so it is **not circular**. But the appliance-survey answer columns are shifted by one against the ids of `survey_questions.csv` (answer column Qk holds question Q(k+1)):

| answer column | label of that id | label of id + 1 | top answers |
|---|---|---|---|
| Q246 | Insulation: Other | Central heating | Gas: 2113; No central heating: 128; Electric (including storage heaters): 114; Other central heating: 81 |
| Q247 | Central heating | Central heating - control | The heating switches on and off automatically at set times of the day: 553; I switch the heating on manually at the boiler when needed: 389; The heating is controlled automatically by a thermostatic temperature control: 341; The heating switches on and off automatically at set times of the day;The heating is controlled automatically by a thermostatic temperature control: 226 |
| Q248 | Central heating - control | Heating water | Hot water storage tank with gas boiler - used for both central heating and hot water: 1057; Gas boiler (without hot water storage tank) - used for both central heating and hot water ('combi' boiler): 902; Hot water storage tank with electric immersion heater: 248; Hot water storage tank with gas boiler - used for hot water only: 85 |
| Q303 | No. Over-sink electric water heater | No. Portable electric heater | 0.0: 1777; 1.0: 540; 2.0: 199; 3.0: 70 |
| Q304 | No. Portable electric heater | No. Television | 1.0: 1292; 2.0: 665; 3.0: 323; 0.0: 133 |
| Q305 | No. Television | No. Desktop PC/computer | 0.0: 1433; 1.0: 993; 2.0: 148; 3.0: 25 |

So 04's `Q248` is the hot-water system (whose answers name the central-heating fuel, so the gas part holds), but its `Q304` is the **number of televisions**; the 04 'clean' subset is 'gas boiler for CH and hot water, and no TV'. Paper A (`hp-sensitivity-paper` `scripts/outputs.py::_lcl_base`) applies the shift to Q248 but not to Q304, so its 'clean' / 'heater-rich' LCL bases carry the same mislabel (reported, not changed). Corrected label: central heating = 'Gas' (answer column Q246) and 0 portable electric heaters (answer column Q303); it is carried as `fill.subset: "gas_ch & no_heater"` for a sensitivity arm.

## 3-4. Tariff and quality (Std only; ToU households dropped for their whole record)

Window for coverage and analog candidates: local days [2012-07-01, 2014-02-28). Over the full file span only **450** Std households reach 90 % (staggered recruitment Nov 2011 - Dec 2012), so the window starts at Jul 2012 (every calendar day at least once; Jul-Feb twice).

| rule | drops (alone) | drops (in order) |
|---|---|---|
| coverage < 0.9 | 875 | 875 |
| half-hour > 10 kWh | 1 | 1 |
| zero run >= 24 h | 173 | 98 |

Kept: **3199** of 4173 Std households. Donor-filled days per kept household (gaps > 2 h): median 0, 90th pct 9. Surveyed: 1310.

## 5. Temperature and s0

Temperature (R4 of 05a-ii): London Heathrow daily mean, Meteostat bulk `daily/03772.csv.gz` (`data/_paperb/raw/meteostat/`), instead of HadCET (Central England composite, `data/hadcet/meantemp_daily_totals.txt`; the series of 04 and 05a-i), which stays as the comparison rows `T = hadcet`. Per-dwelling s0 = Paper A fit of the households' mean daily load against T (B* fill: 0.0055; 04 with HadCET: all LCL 0.0133, 04 'gas-only' 0.0070):

| period | subset | T | N | s0 (kW/K) | T_h | P_base/N (kW) | r2 |
|---|---|---|---|---|---|---|---|
| Jul 2012 - Jun 2013 (as 04) | all kept Std | heathrow | 3199 | 0.012 | 16.2 | 0.342 | 0.843 |
| Jul 2012 - Jun 2013 (as 04) | all kept Std | hadcet | 3199 | 0.0131 | 14.2 | 0.345 | 0.843 |
| Jul 2012 - Jun 2013 (as 04) | 04 def.: Q248 gas boiler for CH & Q304 = 0 (= 0 TVs) | heathrow | 47 | 0.00617 | 15.9 | 0.275 | 0.609 |
| Jul 2012 - Jun 2013 (as 04) | corrected: CH = Gas (col Q246) & 0 portable heaters (col Q303) | heathrow | 777 | 0.00752 | 16.6 | 0.316 | 0.748 |
| Jul 2012 - Jun 2013 (as 04) | CH = Gas (col Q246) | heathrow | 1078 | 0.00922 | 16.2 | 0.323 | 0.784 |
| LCL window | all kept Std | heathrow | 3199 | 0.0114 | 17.6 | 0.334 | 0.844 |
| LCL window | all kept Std | hadcet | 3199 | 0.0126 | 15.4 | 0.338 | 0.847 |
| LCL window | 04 def.: Q248 gas boiler for CH & Q304 = 0 (= 0 TVs) | heathrow | 47 | 0.00583 | 18 | 0.271 | 0.605 |
| LCL window | corrected: CH = Gas (col Q246) & 0 portable heaters (col Q303) | heathrow | 777 | 0.00726 | 18.5 | 0.307 | 0.761 |
| LCL window | CH = Gas (col Q246) | heathrow | 1078 | 0.00881 | 17.9 | 0.313 | 0.794 |
