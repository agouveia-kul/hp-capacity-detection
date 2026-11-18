# 07b-i facts (iter07b_i_quick, commit 7abe655)

### BE monitoring

- **installations:** 32
- **installations per set:** {'BE-2024': 16, 'BE-2025': 32}
- **period per set:** {'BE-2024': '2024-03-26 .. 2024-12-31', 'BE-2025': '2025-01-08 .. 2025-12-31'}
- **with HP series (mid-e/hp/P, mid-e/hp1/P, mid-e/hp2/P):** 18
- **with P1 series (fluvius/p1/P):** 30
- **with PV series (mid-e/pv/P, mid-e/inverter1-pv/P, mid-e/inverter2-pv/P):** 18
- **with BUF series (mid-e/buffer-tank-resistance/P):** 19
- **with T series (hp/hp1-outside-air/T, hp/outside-air/T, sensor/outside-air/T, sensor/outside/T):** 18
- **with heat meter (mid-c/space-heating/P):** 27
- **HP and P1 both >= 90% of days, season2024/25:** 0
- **HP and P1 both >= 90% of days, cal2025:** 0
- **HP, P1 and outdoor T >= 90%, season2024/25:** 0
- **HP, P1 and outdoor T >= 90%, cal2025:** 0
- **outdoor-temperature series:** ['hp/hp1-outside-air/T', 'hp/hp2-outside-air/T', 'hp/outside-air/T', 'sensor/outside-air/T', 'sensor/outside/T']
- **DER table rows:** 32
- **DER heat pump = yes:** 18
- **DER HP electrical peak kW (median [IQR]):** 3.79 [2.97-4.66] (n=18)
- **DER buffer-tank resistor peak > 0:** 6
- **DER with PV:** 18
- **DER with battery:** 12
- **DER EV charger found:** 0
- **DER installations in series:** 32
- **DER HP homes with a battery (excluded from the own-load slope):** 12
- **own-load homes (HP, no battery, P1+HP):** 6
- **own-load days per home:** 50 [34-61] (n=6)
- **own-load fits per home (all, incl. at bound):** [{'home': '152', 'days': 30, 's0': 0.0171, 'T_h': 20.0, 'r2': 0.3324, 'at_bound': True, 'own_T': True}, {'home': '263', 'days': 63, 's0': 0.0597, 'T_h': 9.2038, 'r2': 0.4794, 'at_bound': False, 'own_T': True}, {'home': '410', 'days': 70, 's0': 0.1136, 'T_h': 8.0, 'r2': 0.317, 'at_bound': True, 'own_T': True}, {'home': '420', 'days': 56, 's0': 0.0, 'T_h': 8.0, 'r2': -0.0, 'at_bound': True, 'own_T': True}, {'home': '430', 'days': 31, 's0': 0.0204, 'T_h': 8.369, 'r2': 0.0595, 'at_bound': False, 'own_T': True}, {'home': '440', 'days': 45, 's0': 0.0, 'T_h': 8.0, 'r2': -0.0, 'at_bound': True, 'own_T': True}]
- **own non-HP slope kW/K per HP home (hinge inside, not at bound):** 0.0400 [0.0302-0.0499] (n=2)
- **own-load T_h:** 8.8 [8.6-9.0] (n=2)
- **own-load r2:** 0.27 [0.16-0.37] (n=2)
- **own slope of the aggregate / n (days with all homes):** only 12 common days

### Fluvius 2024

- **meters:** 600
- **EAN_ID shared between files:** 0
- **period:** 2024-01-01 .. 2024-12-31
- **HP-flagged, no PV, complete (gross whole-house load):** 300
- **HP-flagged, no PV, no EV, complete:** 0
- **non-HP, no PV, no EV, complete (local s0 fill):** 0
- **temperature on disk:** none for Flanders 2024 (Solcast files on disk carry irradiance only)

### FeederBW

- **feeders:** 200
- **feeders read:** 5
- **housing units per feeder:** 32 [18-47] (n=200)
- **feeders with HP kW > 0 (last registry row):** 123
- **feeders whose HP kW changes:** 41
- **HP kW per feeder (HP > 0):** 9.4 [5.2-19.5] (n=123)
- **HP kW per housing unit (HP > 0):** 0.280 [0.122-0.700] (n=123)
- **feeders with storage/electric heaters registered:** 165
- **feeders with HP > 0 and no electric heating:** 11
- **feeders with no HP and no electric heating:** 24
- **feeders with PV registered:** 176
- **feeders with commerce:** 123
- **full days 2023-04-01..2024-04-01 (median feeder):** 366.0
- **s0 feeders fitted:** 1
- **s0 fit errors (listed in feederbw_s0.csv):** 0
- **s0 hinge inside, not at bound:** 0
- **s0 kW/K per housing unit, all:** n=0
- **s0, no PV no commerce:** n=0
- **s0 T_h:** n=0

### UKPN

- **LCT HP rows:** 384
- **HP connections (sum):** 3730
- **HP connections per substation:** 8 [7-11] (n=384)
- **HP import kW per row:** 49.2 [34.9-67.8] (n=384)
- **LV feeders:** 2061
- **secondary substations:** 873
- **devices per feeder:** 19 [12-30] (n=1976)
- **period:** 2024-06-01 .. 2024-06-30
- **datasets:** ['UKPN_July_2024']
- **HP substations present in the feeder file:** 17

### HEAPO beyond B*

- **B* HEAPO HP households:** 47
- **heapo15 total >= 90%, not in B* (per window):** {'2019/20': 8, '2020/21': 116, '2021/22': 264, '2022/23': 841, 'cal2020': 32, 'cal2021': 166, 'cal2022': 304, 'cal2023': 1027}
- **heapo15 hp >= 90%, not in B* (per window):** {'2019/20': 1, '2021/22': 2, '2022/23': 3, 'cal2022': 1}
- **heapo_daily total >= 90%, not in B* (per window):** {'2019/20': 227, '2020/21': 145, '2021/22': 352, '2022/23': 730, '2023/24': 820, 'cal2019': 125, 'cal2020': 198, 'cal2021': 170, 'cal2022': 419, 'cal2023': 774}
- **heapo_daily hp >= 90%, not in B* (per window):** {'2021/22': 2, '2022/23': 6, 'cal2022': 3}
- **HEAPO households:** 1408
- **groups:** {'control': 1194, 'treatment': 214}
- **with nameplate electric power (protocol):** 67
- **with nameplate, not in B*:** 66
- **source-only mapping: B* HP_Peak / nameplate electric power:** 1.14 [1.14-1.14] (n=1)

### NEEA

- **HP homes, heating fully submetered (04 rule, selects on s_res):** 57
- **own non-HP slope s_res kW/K per HP home (04 rule):** 0.0069 [0.0006-0.0141] (n=57)
- **HP homes, no gas furnace, no PV, s_heat > 0.05 (no s_res cut):** 77
- **per state (no s_res cut):** {'WA': 37, 'OR': 31, 'ID': 9}
- **own non-HP slope s_res kW/K per HP home (no s_res cut):** 0.0119 [0.0038-0.0334] (n=76)
- **fill homes (no electric heating, >= 330 full days):** 49
- **fill homes per state:** {'WA': 21, 'ID': 16, 'OR': 11, 'MT': 1}
- **s0 WA aggregate, all days:** {'n': 21, 'days': 365, 's0': 0.0143, 'T_h': 8.0, 'P_base_per_dw': 1.2201, 'r2': 0.0288, 'hinge_inside': True, 'at_bound': True}
- **s0 WA aggregate, days T <= 18 C (no cooling):** {'n': 21, 'days': 270, 's0': 0.0268, 'T_h': 12.0692, 'P_base_per_dw': 1.0502, 'r2': 0.6917, 'hinge_inside': True, 'at_bound': False}
- **s0 ID aggregate, all days:** {'n': 16, 'days': 365, 's0': 0.0, 'T_h': 8.0, 'P_base_per_dw': 0.8771, 'r2': -0.0, 'hinge_inside': True, 'at_bound': True}
- **s0 ID aggregate, days T <= 18 C (no cooling):** {'n': 16, 'days': 242, 's0': 0.0139, 'T_h': 12.4142, 'P_base_per_dw': 0.7001, 'r2': 0.3579, 'hinge_inside': True, 'at_bound': False}
- **s0 OR aggregate, all days:** {'n': 11, 'days': 365, 's0': 0.0006, 'T_h': 8.0, 'P_base_per_dw': 1.0626, 'r2': 0.0, 'hinge_inside': True, 'at_bound': True}
- **s0 OR aggregate, days T <= 18 C (no cooling):** {'n': 11, 'days': 269, 's0': 0.0153, 'T_h': 13.5147, 'P_base_per_dw': 0.9, 'r2': 0.2364, 'hinge_inside': True, 'at_bound': False}

### WPuQ

- **HP homes with household meter:** 37
- **own non-HP slope kW/K per home:** 0.0064 [0.0049-0.0094] (n=19)
- **own slope of the aggregate / n:** 0.0048
- **period:** 2019-01-01 .. 2019-12-31

### BE series keys

| key | installations | median_days | median_rows_per_day |
|---|---|---|---|
| buffer-tank/circulation-pump/status | 1 | 64.0 | 96.0 |
| buffer-tank/hp-valve-supply/status | 2 | 64.0 | 96.0 |
| buffer-tank/hp-valves-dhw-heating/status | 17 | 86.0 | 96.0 |
| cooling/hp-valves/status | 8 | 75.0 | 96.0 |
| fluvius/p1-L1/I | 30 | 64.0 | 96.0 |
| fluvius/p1-L1/P | 30 | 62.5 | 96.0 |
| fluvius/p1-L1/U | 30 | 64.0 | 96.0 |
| fluvius/p1-L2/I | 20 | 87.0 | 96.0 |
| fluvius/p1-L2/P | 20 | 63.0 | 96.0 |
| fluvius/p1-L2/U | 20 | 87.5 | 96.0 |
| fluvius/p1-L3/I | 20 | 87.5 | 96.0 |
| fluvius/p1-L3/P | 20 | 63.0 | 96.0 |
| fluvius/p1-L3/U | 20 | 87.5 | 96.0 |
| fluvius/p1-fwd-t1/E | 30 | 63.5 | 96.0 |
| fluvius/p1-fwd-t2/E | 30 | 63.5 | 96.0 |
| fluvius/p1-fwd-tot/E | 30 | 64.0 | 96.0 |
| fluvius/p1-rev-t1/E | 21 | 82.0 | 96.0 |
| fluvius/p1-rev-t2/E | 26 | 64.0 | 96.0 |
| fluvius/p1-rev-tot/E | 27 | 64.0 | 96.0 |
| fluvius/p1-water/V | 8 | 51.0 | 96.0 |
| fluvius/p1/P | 30 | 64.0 | 96.0 |
| geothermal/hp-valve1/status | 2 | 82.5 | 96.0 |
| hp/3-way-valve/status | 4 | 18.0 | 1435.0 |
| hp/booster-heater/status | 4 | 18.0 | 1435.0 |
| hp/circulation-pump/status | 14 | 12.5 | 668.5 |
| hp/compressor/status | 14 | 12.5 | 668.5 |
| hp/cooling/T | 8 | 12.0 | 768.0 |
| hp/desinfection/status | 4 | 17.5 | 1435.0 |
| hp/dhw-booster/status | 2 | 23.0 | 1426.0 |
| hp/dhw-reheat/T | 2 | 23.0 | 1426.0 |
| hp/dhw-reheat/status | 2 | 23.0 | 1426.0 |
| hp/dhw/T | 4 | 17.5 | 1440.0 |
| hp/flow-rate/Q | 14 | 12.5 | 768.0 |
| hp/heating/T | 14 | 12.5 | 768.0 |
| hp/hp1-brine-in/T | 2 | 51.5 | 96.0 |
| hp/hp1-brine-out/T | 2 | 51.5 | 96.0 |
| hp/hp1-brine-pump-speed/pos | 2 | 51.5 | 192.0 |
| hp/hp1-circulation-pump/status | 16 | 77.0 | 96.0 |
| hp/hp1-compressor/f | 2 | 51.5 | 96.0 |
| hp/hp1-compressor/status | 18 | 76.5 | 96.0 |
| hp/hp1-cooling/T | 9 | 77.0 | 96.0 |
| hp/hp1-defrost-startup/status | 10 | 63.0 | 96.0 |
| hp/hp1-discharge/T | 2 | 51.5 | 96.0 |
| hp/hp1-flow-rate/Q | 18 | 76.5 | 96.0 |
| hp/hp1-heating/T | 18 | 76.5 | 96.0 |
| hp/hp1-hot-water-charging/T | 2 | 51.5 | 96.0 |
| hp/hp1-hot-water-top/T | 2 | 51.5 | 96.0 |
| hp/hp1-leaving-water-pre-phe/T | 16 | 77.0 | 96.0 |
| hp/hp1-liquid-line/T | 2 | 51.5 | 96.0 |
| hp/hp1-liquid-refrigerant/T | 16 | 77.0 | 96.0 |
| hp/hp1-operation-mode/status | 18 | 76.5 | 96.0 |
| hp/hp1-outside-air/T | 18 | 61.0 | 96.0 |
| hp/hp1-return-water/T | 18 | 76.5 | 96.0 |
| hp/hp1-reversing-valve/status | 2 | 51.5 | 96.0 |
| hp/hp1-start-dhw/T | 2 | 51.5 | 96.0 |
| hp/hp1-stop-dhw/T | 2 | 51.5 | 96.0 |
| hp/hp1-suction-gas/T | 2 | 51.5 | 96.0 |
| hp/hp1-supply-line/T | 2 | 51.5 | 96.0 |
| hp/hp1-unit/error | 18 | 76.5 | 96.0 |
| hp/hp1-unit/error-code | 18 | 76.5 | 96.0 |
| hp/hp1-unit/error-sub-code | 16 | 77.0 | 96.0 |
| hp/hp1-water-leaving-cooling/T | 16 | 77.0 | 96.0 |
| hp/hp1-water-leaving-heating-min/T | 2 | 51.5 | 96.0 |
| hp/hp1-water-leaving-heating/T | 18 | 76.5 | 96.0 |
| hp/hp2-circulation-pump/status | 1 | 64.0 | 96.0 |
| hp/hp2-compressor/status | 1 | 64.0 | 96.0 |
| hp/hp2-flow-rate/Q | 1 | 63.0 | 96.0 |
| hp/hp2-heating/T | 1 | 63.0 | 96.0 |
| hp/hp2-leaving-water-pre-phe/T | 1 | 63.0 | 96.0 |
| hp/hp2-liquid-refrigerant/T | 1 | 63.0 | 96.0 |
| hp/hp2-operation-mode/status | 1 | 63.0 | 96.0 |
| hp/hp2-outside-air/T | 1 | 63.0 | 96.0 |
| hp/hp2-return-water/T | 1 | 63.0 | 96.0 |
| hp/hp2-unit/error | 1 | 63.0 | 96.0 |
| hp/hp2-unit/error-code | 1 | 63.0 | 96.0 |
| hp/hp2-unit/error-sub-code | 1 | 63.0 | 96.0 |
| hp/hp2-water-leaving-cooling/T | 1 | 63.0 | 96.0 |
| hp/hp2-water-leaving-heating/T | 1 | 63.0 | 96.0 |
| hp/leaving-water-pre-buh/T | 4 | 16.5 | 1435.0 |
| hp/leaving-water-pre-phe/T | 14 | 13.0 | 668.5 |
| hp/liquid-refrigerant/T | 14 | 13.0 | 1095.5 |
| hp/operation-mode/status | 14 | 12.5 | 768.0 |
| hp/outside-air/T | 8 | 18.0 | 1440.0 |
| hp/return-water/T | 14 | 12.5 | 768.0 |
| hp/unit/error | 14 | 13.0 | 1095.5 |
| hp/unit/error-code | 14 | 13.0 | 1095.5 |
| hp/unit/error-sub-code | 14 | 13.0 | 1095.5 |
| hp/water-leaving-cooling/T | 14 | 13.0 | 1095.5 |
| hp/water-leaving-heating/T | 14 | 13.0 | 1095.5 |
| ilubat/PV/P | 6 | 1.0 | 1423.5 |
| ilubat/battery-charge/E | 7 | 69.0 | 96.0 |
| ilubat/battery-discharge/E | 7 | 69.0 | 96.0 |
| ilubat/battery/P | 7 | 69.0 | 96.0 |
| ilubat/battery/soc | 7 | 69.0 | 96.0 |
| ilubat/pv/P | 7 | 68.0 | 96.0 |
| inverter/ac-L1/I | 8 | 9.5 | 96.0 |
| inverter/ac-L1N/U | 14 | 11.5 | 431.5 |
| inverter/ac-L2/I | 1 | 21.0 | 40.0 |
| inverter/ac-L2N/U | 1 | 11.0 | 96.0 |
| inverter/ac-L3/I | 1 | 21.0 | 40.0 |
| inverter/ac-L3N/U | 1 | 11.0 | 96.0 |
| inverter/ac/E | 12 | 11.0 | 1102.0 |
| inverter/ac/E_app | 14 | 11.0 | 302.5 |
| inverter/ac/E_rea | 14 | 11.0 | 302.5 |
| inverter/ac/I | 11 | 12.0 | 240.0 |
| inverter/ac/P | 14 | 11.5 | 741.5 |
| inverter/ac/f | 14 | 11.5 | 756.75 |
| inverter/battery-charge-direction/status | 4 | 11.5 | 304.0 |
| inverter/battery-charge/E_tot | 4 | 11.0 | 304.0 |
| inverter/battery-charge/I_max | 4 | 11.0 | 303.0 |
| inverter/battery-dc/I | 4 | 11.5 | 607.5 |
| inverter/battery-dc/P | 4 | 11.5 | 607.5 |
| inverter/battery-dc/U | 4 | 12.0 | 705.0 |
| inverter/battery-discharge/E_tot | 4 | 11.5 | 607.0 |
| inverter/battery-discharge/I_max | 4 | 11.5 | 606.0 |
| inverter/battery-health/soc | 4 | 7.5 | 976.0 |
| inverter/battery/soc | 4 | 7.5 | 976.0 |
| inverter/bms-charge/I_max | 4 | 10.5 | 96.0 |
| inverter/bms-discharge/I_max | 4 | 10.5 | 96.0 |
| inverter/cabinet/T | 14 | 12.0 | 756.5 |
| inverter/dc-s1/I | 8 | 9.5 | 96.0 |
| inverter/dc-s1/P | 4 | 8.5 | 49.25 |
| inverter/dc-s1/U | 8 | 9.5 | 96.0 |
| inverter/dc-s2/I | 8 | 9.5 | 96.0 |
| inverter/dc-s2/P | 4 | 8.5 | 49.75 |
| inverter/dc-s2/U | 8 | 9.0 | 96.0 |
| inverter/dc/I | 2 | 3.5 | 1410.5 |
| inverter/dc/P | 2 | 3.0 | 1425.25 |
| inverter/dc/U | 2 | 3.0 | 1425.25 |
| inverter/grid-battery-charge/E | 4 | 10.0 | 96.0 |
| inverter/grid-consumption/E | 4 | 10.0 | 96.0 |
| inverter/grid-injection/E | 4 | 10.0 | 96.0 |
| inverter/grid-meter/P | 4 | 10.0 | 96.0 |
| inverter/household-load/P | 4 | 10.0 | 96.0 |
| inverter/inv1-ac-L1/I | 18 | 63.5 | 68.5 |
| inverter/inv1-ac-L1N/U | 18 | 76.0 | 96.0 |
| inverter/inv1-ac-L2/I | 4 | 51.0 | 63.75 |
| inverter/inv1-ac-L2N/U | 4 | 55.5 | 96.0 |
| inverter/inv1-ac-L3/I | 4 | 51.0 | 63.75 |
| inverter/inv1-ac-L3N/U | 4 | 55.5 | 96.0 |
| inverter/inv1-ac/E | 10 | 3.0 | 96.0 |
| inverter/inv1-ac/E_app | 14 | 1.0 | 96.0 |
| inverter/inv1-ac/E_rea | 14 | 1.0 | 96.0 |
| inverter/inv1-ac/P | 18 | 71.0 | 68.5 |
| inverter/inv1-ac/P_app | 18 | 70.0 | 68.5 |
| inverter/inv1-ac/P_rea | 16 | 69.5 | 68.0 |
| inverter/inv1-ac/f | 18 | 71.0 | 74.0 |
| inverter/inv1-battery-charge-direction/status | 5 | 74.0 | 96.0 |
| inverter/inv1-battery-charge/E | 5 | 73.0 | 96.0 |
| inverter/inv1-battery-charge/E_tot | 4 | 2.0 | 96.0 |
| inverter/inv1-battery-charge/I_max | 5 | 74.0 | 96.0 |
| inverter/inv1-battery-dc/I | 5 | 75.0 | 96.0 |
| inverter/inv1-battery-dc/P | 5 | 74.0 | 96.0 |
| inverter/inv1-battery-dc/U | 5 | 76.0 | 96.0 |
| inverter/inv1-battery-discharge/E | 5 | 73.0 | 96.0 |
| inverter/inv1-battery-discharge/E_tot | 4 | 2.0 | 96.0 |
| inverter/inv1-battery-discharge/I_max | 5 | 74.0 | 96.0 |
| inverter/inv1-battery-health/soc | 5 | 74.0 | 96.0 |
| inverter/inv1-battery/soc | 5 | 74.0 | 96.0 |
| inverter/inv1-bms-charge/I_max | 5 | 73.0 | 96.0 |
| inverter/inv1-bms-discharge/I_max | 5 | 73.0 | 96.0 |
| inverter/inv1-cabinet/T | 18 | 71.0 | 94.75 |
| inverter/inv1-grid-battery-charge/E | 5 | 74.0 | 96.0 |
| inverter/inv1-grid-consumption/E | 5 | 74.0 | 96.0 |
| inverter/inv1-grid-injection/E | 18 | 74.0 | 96.0 |
| inverter/inv1-grid-meter/P | 5 | 35.0 | 95.0 |
| inverter/inv1-household-load/P | 5 | 35.0 | 96.0 |
| inverter/inv1-inverted-total/E | 5 | 74.0 | 96.0 |
| inverter/inv1-pv-dc-s1/I | 18 | 64.5 | 65.75 |
| inverter/inv1-pv-dc-s1/P | 13 | 58.0 | 63.0 |
| inverter/inv1-pv-dc-s1/U | 18 | 64.5 | 75.25 |
| inverter/inv1-pv-dc-s2/I | 18 | 63.5 | 68.5 |
| inverter/inv1-pv-dc-s2/P | 13 | 58.0 | 63.0 |
| inverter/inv1-pv-dc-s2/U | 18 | 65.0 | 75.25 |
| inverter/inv1-pv-dc/P | 5 | 74.0 | 96.0 |
| inverter/inv1-pv/E | 5 | 62.0 | 96.0 |
| inverter/inv1-rectifier/P | 5 | 35.0 | 96.0 |
| inverter/inv2-ac-L1/I | 1 | 61.0 | 96.0 |
| inverter/inv2-ac-L1N/U | 1 | 63.0 | 96.0 |
| inverter/inv2-ac/P | 1 | 61.0 | 96.0 |
| inverter/inv2-ac/P_app | 1 | 61.0 | 96.0 |
| inverter/inv2-ac/P_rea | 1 | 61.0 | 96.0 |
| inverter/inv2-ac/f | 1 | 63.0 | 96.0 |
| inverter/inv2-cabinet/T | 1 | 63.0 | 96.0 |
| inverter/inv2-grid-injection/E | 1 | 21.0 | 45.0 |
| inverter/inv2-inverted-total/E | 1 | 23.0 | 44.0 |
| inverter/inv2-pv-dc-s1/I | 1 | 61.0 | 96.0 |
| inverter/inv2-pv-dc-s1/U | 1 | 63.0 | 96.0 |
| inverter/inv2-pv-dc-s2/I | 1 | 61.0 | 96.0 |
| inverter/inv2-pv-dc-s2/U | 1 | 63.0 | 96.0 |
| inverter/inv2-pv-dc/P | 1 | 61.0 | 96.0 |
| inverter/inv2-pv/E | 1 | 23.0 | 44.0 |
| inverter/inv2-rectifier/P | 1 | 61.0 | 96.0 |
| inverter/inverted-total/E | 4 | 10.0 | 96.0 |
| inverter/pv-dc/P | 4 | 10.0 | 96.0 |
| inverter/rectifier/P | 4 | 10.0 | 96.0 |
| mid-c/btes-in/T | 8 | 69.5 | 96.0 |
| mid-c/btes-out/T | 8 | 69.5 | 96.0 |
| mid-c/btes-regeneration/E | 6 | 83.5 | 96.0 |
| mid-c/btes/E | 6 | 83.5 | 96.0 |
| mid-c/btes/P | 8 | 69.5 | 96.0 |
| mid-c/btes/Q | 8 | 69.5 | 96.0 |
| mid-c/dhw-cooling/E | 13 | 7.0 | 1440.0 |
| mid-c/dhw-heat/E | 19 | 83.0 | 96.0 |
| mid-c/dhw-in/T | 19 | 84.0 | 96.0 |
| mid-c/dhw-out/T | 19 | 85.0 | 96.0 |
| mid-c/dhw/P | 19 | 85.0 | 96.0 |
| mid-c/dhw/Q | 19 | 85.0 | 96.0 |
| mid-c/dhw/V | 19 | 81.0 | 96.0 |
| mid-c/hp-cooling/E | 13 | 13.0 | 1440.0 |
| mid-c/hp-heat/E | 13 | 13.0 | 1440.0 |
| mid-c/hp-in/T | 13 | 13.0 | 1440.0 |
| mid-c/hp-out/T | 13 | 13.0 | 1440.0 |
| mid-c/hp/P | 13 | 13.0 | 1440.0 |
| mid-c/hp/Q | 13 | 13.0 | 1440.0 |
| mid-c/hp1-cooling/E | 17 | 76.0 | 96.0 |
| mid-c/hp1-heat/E | 17 | 76.0 | 96.0 |
| mid-c/hp1-in/T | 19 | 76.0 | 96.0 |
| mid-c/hp1-out/T | 19 | 76.0 | 96.0 |
| mid-c/hp1/P | 19 | 76.0 | 96.0 |
| mid-c/hp1/Q | 19 | 76.0 | 96.0 |
| mid-c/hp2-cooling/E | 1 | 63.0 | 96.0 |
| mid-c/hp2-heat/E | 1 | 63.0 | 96.0 |
| mid-c/hp2-in/T | 1 | 63.0 | 96.0 |
| mid-c/hp2-out/T | 1 | 63.0 | 96.0 |
| mid-c/hp2/P | 1 | 63.0 | 96.0 |
| mid-c/hp2/Q | 1 | 63.0 | 96.0 |
| mid-c/solar-thermal-cooling/E | 2 | 41.5 | 96.0 |
| mid-c/solar-thermal-heat/E | 2 | 42.0 | 96.0 |
| mid-c/solar-thermal-in/T | 2 | 81.5 | 96.0 |
| mid-c/solar-thermal-out/T | 2 | 81.5 | 96.0 |
| mid-c/solar-thermal/P | 2 | 81.5 | 96.0 |
| mid-c/solar-thermal/Q | 2 | 81.0 | 96.0 |
| mid-c/space-heating-cooling/E | 25 | 64.0 | 96.0 |
| mid-c/space-heating-dhw/V | 12 | 51.0 | 96.0 |
| mid-c/space-heating-heat/E | 27 | 79.0 | 96.0 |
| mid-c/space-heating-in/T | 27 | 79.0 | 96.0 |
| mid-c/space-heating-out/T | 27 | 80.0 | 96.0 |
| mid-c/space-heating/P | 27 | 80.0 | 96.0 |
| mid-c/space-heating/Q | 27 | 80.0 | 96.0 |
| mid-e/buffer-tank-resistance/E | 19 | 88.0 | 96.0 |
| mid-e/buffer-tank-resistance/P | 19 | 95.0 | 96.0 |
| mid-e/hp-L1/I | 8 | 9.5 | 96.0 |
| mid-e/hp-L1/P | 2 | 26.0 | 96.0 |
| mid-e/hp-L1/U | 8 | 9.5 | 96.0 |
| mid-e/hp-L2/I | 2 | 12.5 | 667.25 |
| mid-e/hp-L2/P | 2 | 26.0 | 96.0 |
| mid-e/hp-L2/U | 2 | 12.5 | 667.5 |
| mid-e/hp-L3/I | 2 | 12.5 | 667.25 |
| mid-e/hp-L3/P | 2 | 26.0 | 96.0 |
| mid-e/hp-L3/U | 2 | 12.5 | 667.5 |
| mid-e/hp/E | 14 | 28.0 | 1438.0 |
| mid-e/hp/P | 14 | 29.0 | 1438.0 |
| mid-e/hp/f | 8 | 9.5 | 96.0 |
| mid-e/hp1-L1/I | 12 | 1.0 | 96.0 |
| mid-e/hp1-L1/U | 8 | 1.0 | 96.0 |
| mid-e/hp1-L2/I | 6 | 57.5 | 96.0 |
| mid-e/hp1-L2/U | 2 | 14.5 | 96.0 |
| mid-e/hp1-L3/I | 6 | 57.5 | 96.0 |
| mid-e/hp1-L3/U | 2 | 14.5 | 96.0 |
| mid-e/hp1/E | 18 | 76.5 | 96.0 |
| mid-e/hp1/P | 18 | 76.5 | 96.0 |
| mid-e/hp1/f | 18 | 68.0 | 96.0 |
| mid-e/hp2-L1/I | 1 | 63.0 | 96.0 |
| mid-e/hp2-L2/I | 1 | 63.0 | 96.0 |
| mid-e/hp2-L3/I | 1 | 63.0 | 96.0 |
| mid-e/hp2/E | 1 | 9.0 | 96.0 |
| mid-e/hp2/P | 1 | 63.0 | 96.0 |
| mid-e/hp2/f | 1 | 63.0 | 96.0 |
| mid-e/inverter1-pv-L1/I | 18 | 76.5 | 96.0 |
| mid-e/inverter1-pv-L1/U | 18 | 76.5 | 96.0 |
| mid-e/inverter1-pv-L2/I | 4 | 57.5 | 96.0 |
| mid-e/inverter1-pv-L2/U | 4 | 57.5 | 96.0 |
| mid-e/inverter1-pv-L3/I | 4 | 57.5 | 96.0 |
| mid-e/inverter1-pv-L3/U | 4 | 57.5 | 96.0 |
| mid-e/inverter1-pv-fwd/E | 17 | 77.0 | 96.0 |
| mid-e/inverter1-pv-rev/E | 17 | 77.0 | 96.0 |
| mid-e/inverter1-pv/P | 18 | 76.5 | 96.0 |
| mid-e/inverter2-pv-L1/I | 1 | 63.0 | 96.0 |
| mid-e/inverter2-pv-L1/U | 1 | 63.0 | 96.0 |
| mid-e/inverter2-pv-fwd/E | 1 | 25.0 | 96.0 |
| mid-e/inverter2-pv-rev/E | 1 | 25.0 | 96.0 |
| mid-e/inverter2-pv/P | 1 | 63.0 | 96.0 |
| mid-e/lito-box-L1/I | 8 | 3.5 | 1433.0 |
| mid-e/lito-box-L1/U | 8 | 3.5 | 1433.0 |
| mid-e/lito-box-fwd/E | 13 | 103.0 | 96.0 |
| mid-e/lito-box-rev/E | 13 | 104.0 | 96.0 |
| mid-e/lito-box-rev/P | 1 | 14.0 | 1438.0 |
| mid-e/lito-box/I | 13 | 102.0 | 96.0 |
| mid-e/lito-box/P | 13 | 104.0 | 96.0 |
| mid-e/lito-box/U | 13 | 102.0 | 96.0 |
| mid-e/pv-L1/I | 14 | 23.0 | 1437.0 |
| mid-e/pv-L1/P | 1 | 26.0 | 96.0 |
| mid-e/pv-L1/U | 14 | 23.0 | 1437.0 |
| mid-e/pv-L2/I | 1 | 13.0 | 557.0 |
| mid-e/pv-L2/P | 1 | 26.0 | 96.0 |
| mid-e/pv-L2/U | 1 | 13.0 | 557.0 |
| mid-e/pv-L3/I | 1 | 13.0 | 557.0 |
| mid-e/pv-L3/P | 1 | 26.0 | 96.0 |
| mid-e/pv-L3/U | 1 | 13.0 | 557.0 |
| mid-e/pv-fwd/E | 14 | 24.0 | 1437.0 |
| mid-e/pv-rev/E | 14 | 23.0 | 1437.0 |
| mid-e/pv/P | 14 | 23.0 | 1437.0 |
| mid-e/radiation-panel-bathroom/E | 21 | 64.0 | 96.0 |
| mid-e/radiation-panel-bathroom/P | 21 | 64.0 | 96.0 |
| mid-e/stovetop/E | 26 | 64.0 | 96.0 |
| mid-e/stovetop/P | 27 | 68.0 | 96.0 |
| mid-e/ventilation/E | 20 | 93.5 | 96.0 |
| mid-e/ventilation/P | 20 | 93.0 | 96.0 |
| mid-e/water-heater/E | 27 | 87.0 | 96.0 |
| mid-e/water-heater/P | 27 | 87.0 | 96.0 |
| plc/control/day | 1 | 76.0 | 96.0 |
| plc/control/time | 1 | 76.0 | 96.0 |
| pv/battery-charge-direction/status | 1 | 6.0 | 1440.0 |
| pv/battery-charge/E_tot | 8 | 7.0 | 1432.0 |
| pv/battery-charge/I_max | 1 | 6.0 | 1440.0 |
| pv/battery-dc/P | 8 | 7.0 | 1432.0 |
| pv/battery-dc/U | 1 | 6.0 | 1440.0 |
| pv/battery-discharge/E_tot | 8 | 7.0 | 1432.0 |
| pv/battery-discharge/I_max | 1 | 6.0 | 1440.0 |
| pv/battery-health/soc | 1 | 6.0 | 1440.0 |
| pv/battery-pv-dc/P | 7 | 7.0 | 1432.0 |
| pv/battery/soc | 8 | 7.0 | 1432.0 |
| pv/inverter-ac-L1/I | 1 | 2.0 | 999.0 |
| pv/inverter-ac-L1N/U | 11 | 16.0 | 1440.0 |
| pv/inverter-ac-L2/I | 1 | 2.0 | 999.0 |
| pv/inverter-ac-L2N/U | 2 | 4.0 | 1219.25 |
| pv/inverter-ac-L3/I | 1 | 2.0 | 999.0 |
| pv/inverter-ac-L3N/U | 2 | 4.0 | 1219.25 |
| pv/inverter-ac/E | 11 | 16.0 | 1440.0 |
| pv/inverter-ac/E_app | 11 | 16.0 | 1440.0 |
| pv/inverter-ac/E_rea | 11 | 16.0 | 1440.0 |
| pv/inverter-ac/I | 10 | 16.0 | 1440.0 |
| pv/inverter-ac/P | 11 | 16.0 | 1440.0 |
| pv/inverter-ac/f | 11 | 16.0 | 1440.0 |
| pv/inverter-cabinet/T | 11 | 16.0 | 1440.0 |
| pv/inverter-dc-s1/I | 1 | 2.0 | 998.5 |
| pv/inverter-dc-s1/P | 1 | 2.0 | 997.0 |
| pv/inverter-dc-s1/U | 1 | 2.0 | 998.5 |
| pv/inverter-dc-s2/I | 1 | 2.0 | 998.5 |
| pv/inverter-dc-s2/P | 1 | 2.0 | 998.0 |
| pv/inverter-dc-s2/U | 1 | 2.0 | 998.5 |
| pv/inverter-dc/I | 1 | 6.0 | 1440.0 |
| pv/inverter-dc/P | 1 | 6.0 | 1440.0 |
| pv/inverter-dc/U | 1 | 6.0 | 1440.0 |
| radiation-panel/infrared/status | 21 | 64.0 | 192.0 |
| relay/buffer-tank-heating-resistance/status | 19 | 78.0 | 96.0 |
| sensor/bathroom-window-front/status | 8 | 51.0 | 96.0 |
| sensor/bedroom1-window-back/status | 6 | 51.0 | 96.0 |
| sensor/bedroom1-window-front/status | 21 | 86.0 | 96.0 |
| sensor/bedroom2-window-back/status | 25 | 84.0 | 96.0 |
| sensor/bedroom2-window-back2/status | 3 | 51.0 | 96.0 |
| sensor/bedroom2-window-front/status | 18 | 87.0 | 96.0 |
| sensor/bedroom2-window-side/status | 3 | 51.0 | 96.0 |
| sensor/bedroom3-window-back/status | 2 | 57.0 | 96.0 |
| sensor/bedroom3-window-front/status | 5 | 51.0 | 96.0 |
| sensor/bedroom3-window-roof/status | 17 | 87.0 | 96.0 |
| sensor/bedroom3-window-side/status | 3 | 51.0 | 96.0 |
| sensor/bedroom4-window-front/status | 3 | 51.0 | 96.0 |
| sensor/buffer-tank-bottom/T | 19 | 86.0 | 96.0 |
| sensor/buffer-tank-cascade/T | 1 | 64.0 | 96.0 |
| sensor/buffer-tank-mid-bottom/T | 19 | 86.0 | 96.0 |
| sensor/buffer-tank-mid-top/T | 19 | 86.0 | 96.0 |
| sensor/buffer-tank-top/T | 19 | 86.0 | 96.0 |
| sensor/central-heating/p | 7 | 95.0 | 96.0 |
| sensor/dw-supply-cold/T | 18 | 86.0 | 96.0 |
| sensor/dw-supply-hot/T | 18 | 86.0 | 96.0 |
| sensor/entrance-hall-window-front/status | 23 | 85.0 | 96.0 |
| sensor/entrance-hall-window-side/status | 19 | 86.0 | 96.0 |
| sensor/hp-geothermal-return/T | 2 | 9.0 | 96.0 |
| sensor/hp-geothermal-supply/T | 2 | 9.0 | 96.0 |
| sensor/hp1-geothermal-return/T | 4 | 63.5 | 96.0 |
| sensor/hp1-geothermal-supply/T | 4 | 63.5 | 96.0 |
| sensor/hp1-geothermal/p | 2 | 43.5 | 95.0 |
| sensor/kitchen-window-back/status | 4 | 51.0 | 96.0 |
| sensor/kitchen-window-back2/status | 1 | 51.0 | 96.0 |
| sensor/kitchen-window-front/status | 6 | 51.0 | 96.0 |
| sensor/litobox/T | 4 | 91.0 | 96.0 |
| sensor/living-room-window-back/status | 27 | 83.0 | 96.0 |
| sensor/living-room-window-back2/status | 1 | 51.0 | 96.0 |
| sensor/living-room-window-front/status | 3 | 51.0 | 96.0 |
| sensor/living-room-window-side/status | 17 | 87.0 | 96.0 |
| sensor/outside-air/T | 3 | 52.0 | 96.0 |
| sensor/outside/T | 2 | 14.5 | 1440.0 |
| sensor/solar-thermal-collector/T | 4 | 73.5 | 96.0 |
| sensor/solar-thermal-return/T | 4 | 11.0 | 60.0 |
| sensor/solar-thermal-supply/T | 4 | 11.0 | 60.0 |
| sensor/solar-thermal/p | 4 | 68.5 | 96.0 |
| sensor/space-heating-return/T | 19 | 86.0 | 96.0 |
| sensor/space-heating-supply/T | 19 | 86.0 | 96.0 |
| sensor/storage-window-back/status | 2 | 51.0 | 96.0 |
| sensor/storage-window-front/status | 5 | 51.0 | 96.0 |
| sensor/ventilation-bathroom-extraction/T | 4 | 99.0 | 96.0 |
| sensor/ventilation-bedroom-extraction/T | 4 | 99.5 | 96.0 |
| sensor/ventilation-extraction/T | 23 | 64.0 | 96.0 |
| sensor/ventilation-inflow-fresh/T | 13 | 84.0 | 96.0 |
| sensor/ventilation-kitchen-extraction/T | 4 | 99.5 | 96.0 |
| sensor/ventilation-outflow-waste/Q | 14 | 57.0 | 96.0 |
| sensor/ventilation-outflow-waste/T | 20 | 84.5 | 96.0 |
| sensor/ventilation-pulsion/T | 13 | 84.0 | 96.0 |
| sensor/ventilation-storage-extraction/T | 4 | 99.5 | 96.0 |
| sensor/ventilation-toilet-extraction/T | 4 | 99.5 | 96.0 |
| solar-collector/circulation-pump/status | 4 | 68.5 | 96.0 |
| solar-collector/hp-valve2/status | 2 | 82.0 | 96.0 |
| space-cooling/source-pump/status | 1 | 51.0 | 96.0 |
| space-heating/circulation-pump/status | 19 | 86.0 | 96.0 |
| space-heating/mix-valve-supply/pos | 19 | 85.0 | 96.0 |
| space-heating/valve-supply/T | 4 | 5.0 | 1407.25 |
| space-heating/valve-supply/status | 4 | 12.0 | 1440.0 |
| switch/user-mode-hvac/status | 1 | 5.0 | 96.0 |
| thermostat/bathroom-co2/c | 27 | 83.0 | 96.0 |
| thermostat/bathroom-cooling/T | 3 | 51.0 | 96.0 |
| thermostat/bathroom-display/T | 27 | 83.0 | 96.0 |
| thermostat/bathroom-heating/T | 27 | 83.0 | 96.0 |
| thermostat/bathroom-radiator-2-way-valve/pos | 8 | 89.0 | 192.0 |
| thermostat/bathroom-radiator-control-value/pos | 2 | 18.5 | 1405.0 |
| thermostat/bathroom/RH | 27 | 83.0 | 96.0 |
| thermostat/bathroom/T | 27 | 83.0 | 96.0 |
| thermostat/bedroom1-co2/c | 27 | 83.0 | 96.0 |
| thermostat/bedroom1-cooling/T | 17 | 64.0 | 96.0 |
| thermostat/bedroom1-display/T | 27 | 83.0 | 96.0 |
| thermostat/bedroom1-heating/T | 27 | 83.0 | 96.0 |
| thermostat/bedroom1-radiator-2-way-valve/pos | 8 | 89.0 | 192.0 |
| thermostat/bedroom1-radiator-control-value/pos | 2 | 19.0 | 1405.0 |
| thermostat/bedroom1-ventilo-2-way-valve/status | 19 | 79.0 | 192.0 |
| thermostat/bedroom1-ventilo-convector-fan/pos | 19 | 79.0 | 192.0 |
| thermostat/bedroom1-ventilo-convector-fan/status | 2 | 14.5 | 2880.0 |
| thermostat/bedroom1/RH | 27 | 83.0 | 96.0 |
| thermostat/bedroom1/T | 27 | 83.0 | 96.0 |
| thermostat/bedroom2-co2/c | 25 | 84.0 | 96.0 |
| thermostat/bedroom2-cooling/T | 15 | 83.0 | 96.0 |
| thermostat/bedroom2-display/T | 25 | 84.0 | 96.0 |
| thermostat/bedroom2-heating/T | 25 | 84.0 | 96.0 |
| thermostat/bedroom2-radiator-2-way-valve/pos | 8 | 90.0 | 192.0 |
| thermostat/bedroom2-ventilo-2-way-valve/status | 17 | 83.0 | 192.0 |
| thermostat/bedroom2-ventilo-convector-fan/pos | 17 | 83.0 | 192.0 |
| thermostat/bedroom2-ventilo-convector-fan/status | 2 | 14.5 | 2880.0 |
| thermostat/bedroom2/RH | 25 | 84.0 | 96.0 |
| thermostat/bedroom2/T | 25 | 84.0 | 96.0 |
| thermostat/bedroom3-co2/c | 25 | 84.0 | 96.0 |
| thermostat/bedroom3-cooling/T | 15 | 83.0 | 96.0 |
| thermostat/bedroom3-display/T | 25 | 84.0 | 96.0 |
| thermostat/bedroom3-heating/T | 25 | 84.0 | 96.0 |
| thermostat/bedroom3-radiator-2-way-valve/pos | 8 | 90.5 | 192.0 |
| thermostat/bedroom3-ventilo-2-way-valve/status | 17 | 83.0 | 192.0 |
| thermostat/bedroom3-ventilo-convector-fan/pos | 17 | 83.0 | 192.0 |
| thermostat/bedroom3-ventilo-convector-fan/status | 2 | 14.5 | 2880.0 |
| thermostat/bedroom3/RH | 25 | 84.0 | 96.0 |
| thermostat/bedroom3/T | 25 | 84.0 | 96.0 |
| thermostat/bedroom4-co2/c | 3 | 51.0 | 96.0 |
| thermostat/bedroom4-cooling/T | 2 | 51.0 | 96.0 |
| thermostat/bedroom4-display/T | 3 | 51.0 | 96.0 |
| thermostat/bedroom4-heating/T | 3 | 51.0 | 96.0 |
| thermostat/bedroom4-radiator-2-way-valve/pos | 1 | 51.0 | 192.0 |
| thermostat/bedroom4-ventilo-2-way-valve/status | 2 | 56.5 | 192.0 |
| thermostat/bedroom4-ventilo-convector-fan/pos | 2 | 56.5 | 192.0 |
| thermostat/bedroom4/RH | 3 | 51.0 | 96.0 |
| thermostat/bedroom4/T | 3 | 51.0 | 96.0 |
| thermostat/entrance-hall-co2/c | 25 | 84.0 | 96.0 |
| thermostat/entrance-hall-cooling/T | 3 | 51.0 | 96.0 |
| thermostat/entrance-hall-display/T | 25 | 84.0 | 96.0 |
| thermostat/entrance-hall-heating/T | 25 | 84.0 | 96.0 |
| thermostat/entrance-hall-radiator-2-way-valve/pos | 25 | 84.0 | 192.0 |
| thermostat/entrance-hall-radiator-control-value/pos | 2 | 18.5 | 1405.0 |
| thermostat/entrance-hall-ventilo-2-way-valve/status | 2 | 9.5 | 2818.5 |
| thermostat/entrance-hall/RH | 27 | 83.0 | 96.0 |
| thermostat/entrance-hall/T | 27 | 83.0 | 96.0 |
| thermostat/kitchen-co2/c | 27 | 83.0 | 96.0 |
| thermostat/kitchen-cooling/T | 17 | 64.0 | 96.0 |
| thermostat/kitchen-display/T | 27 | 83.0 | 96.0 |
| thermostat/kitchen-heating/T | 27 | 83.0 | 96.0 |
| thermostat/kitchen-radiator-2-way-valve/pos | 8 | 89.0 | 192.0 |
| thermostat/kitchen-radiator-control-value/pos | 2 | 19.0 | 1405.0 |
| thermostat/kitchen-ventilo-2-way-valve/status | 19 | 79.0 | 192.0 |
| thermostat/kitchen-ventilo-convector-fan/pos | 19 | 79.0 | 192.0 |
| thermostat/kitchen-ventilo-convector-fan/status | 2 | 13.5 | 2880.0 |
| thermostat/kitchen/RH | 27 | 83.0 | 96.0 |
| thermostat/kitchen/T | 27 | 83.0 | 96.0 |
| thermostat/living-room-co2/c | 27 | 83.0 | 96.0 |
| thermostat/living-room-cooling/T | 17 | 64.0 | 96.0 |
| thermostat/living-room-display/T | 27 | 83.0 | 96.0 |
| thermostat/living-room-heating/T | 27 | 83.0 | 96.0 |
| thermostat/living-room-operation-mode/status | 2 | 14.5 | 1440.0 |
| thermostat/living-room-radiator-2-way-valve/pos | 8 | 89.0 | 192.0 |
| thermostat/living-room-radiator-control-value/pos | 2 | 19.0 | 1405.0 |
| thermostat/living-room-ventilo-2-way-valve/status | 19 | 79.0 | 192.0 |
| thermostat/living-room-ventilo-convector-fan/pos | 19 | 79.0 | 192.0 |
| thermostat/living-room-ventilo-convector-fan/status | 2 | 14.0 | 2880.0 |
| thermostat/living-room/RH | 27 | 83.0 | 96.0 |
| thermostat/living-room/T | 27 | 83.0 | 96.0 |
| thermostat/operation-mode/status | 27 | 79.0 | 96.0 |
| thermostat/storage/RH | 27 | 83.0 | 96.0 |
| thermostat/storage/T | 27 | 83.0 | 96.0 |
| thermostat/toilet1/RH | 23 | 83.0 | 96.0 |
| thermostat/toilet1/T | 23 | 83.0 | 96.0 |
| thermostat/toilet2/RH | 15 | 87.0 | 96.0 |
| thermostat/toilet2/T | 15 | 87.0 | 96.0 |
| ventilation/damper-extraction/status | 10 | 51.0 | 96.0 |
| ventilation/fan/Q | 4 | 14.5 | 1440.0 |
| ventilation/fan/pos | 17 | 79.0 | 96.0 |

### Fluvius 2024 files

| file | meters | complete | hp | ev | pv | flag_changes | import_MWh_median | export_MWh_median |
|---|---|---|---|---|---|---|---|---|
| WP_EV_geen_ZP | 300 | 300 | 300 | 300 | 0 | 0 | 8.6972745 | 0.0 |
| WP_met_ZP | 300 | 300 | 300 | 0 | 300 | 0 | 4.6618155 | 2.8113355 |

### Envelopes (v1.1)

| pool | HP | fill | note | HP per split (test) | HP per split (train) | test subs <=15% | test subs 15-35% | test subs 35-65% | test subs >65% | max size p=0.05 | max size p=0.1 | max size p=0.2 | max size p=0.3 | max size p=0.5 | max size p=0.8 | max size p=1.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BE monitoring (HP+P1 complete) + Fluvius 2024 fill | 0 | 0 | too few HP for a split | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| Fluvius 2024 HP-flag (no PV, no EV) + Fluvius 2024 fill | 0 | 0 | too few HP for a split | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| US-NEEA cal2023 | 57 | 49 | nan | 15.0 | 42.0 | 20.0 | 20.0 | 5.0 | 0.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 0.0 | 0.0 |
