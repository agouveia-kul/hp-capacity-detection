# 07b-i facts (iter07b_i_audit, commit 7abe655)

### BE monitoring

- **installations:** 32
- **installations per set:** {'BE-2024': 16, 'BE-2025': 32}
- **period per set:** {'BE-2024': '2024-03-26 .. 2024-12-31', 'BE-2025': '2025-01-01 .. 2025-12-31'}
- **with HP series (mid-e/hp/P, mid-e/hp1/P, mid-e/hp2/P):** 18
- **with P1 series (fluvius/p1/P):** 30
- **with PV series (mid-e/pv/P, mid-e/inverter1-pv/P, mid-e/inverter2-pv/P):** 18
- **with BUF series (mid-e/buffer-tank-resistance/P):** 19
- **with T series (hp/hp1-outside-air/T, hp/outside-air/T, sensor/outside-air/T, sensor/outside/T):** 18
- **with heat meter (mid-c/space-heating/P):** 27
- **HP and P1 both >= 90% of days, season2024/25:** 9
- **HP and P1 both >= 90% of days, cal2025:** 9
- **HP, P1 and outdoor T >= 90%, season2024/25:** 6
- **HP, P1 and outdoor T >= 90%, cal2025:** 5
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
- **own-load days per home:** 258 [217-339] (n=6)
- **own-load fits per home (all, incl. at bound):** [{'home': '152', 'days': 210, 's0': 0.0253, 'T_h': 20.0, 'r2': 0.4465, 'at_bound': True, 'own_T': True}, {'home': '263', 'days': 359, 's0': 0.023, 'T_h': 20.0, 'r2': 0.4221, 'at_bound': True, 'own_T': True}, {'home': '410', 'days': 400, 's0': 0.0374, 'T_h': 15.2391, 'r2': 0.1439, 'at_bound': False, 'own_T': True}, {'home': '420', 'days': 279, 's0': 0.0, 'T_h': 8.0, 'r2': -0.0, 'at_bound': True, 'own_T': True}, {'home': '430', 'days': 147, 's0': 0.0049, 'T_h': 20.0, 'r2': 0.3142, 'at_bound': True, 'own_T': True}, {'home': '440', 'days': 238, 's0': 0.0007, 'T_h': 20.0, 'r2': 0.0243, 'at_bound': True, 'own_T': True}]
- **own non-HP slope kW/K per HP home (hinge inside, not at bound):** 0.0374 [0.0374-0.0374] (n=1)
- **own-load T_h:** 15.2 [15.2-15.2] (n=1)
- **own-load r2:** 0.14 [0.14-0.14] (n=1)
- **own slope of the aggregate / n (days with all homes):** 0.0

### Fluvius 2024

- **meters:** 2400
- **EAN_ID shared between files:** 0
- **period:** 2024-01-01 .. 2024-12-31
- **HP-flagged, no PV, complete (gross whole-house load):** 600
- **HP-flagged, no PV, no EV, complete:** 300
- **non-HP, no PV, no EV, complete (local s0 fill):** 300
- **temperature on disk:** none for Flanders 2024 (Solcast files on disk carry irradiance only)

### FeederBW

- **feeders:** 200
- **feeders read:** 200
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
- **s0 feeders fitted:** 20
- **s0 fit errors (listed in feederbw_s0.csv):** 2
- **s0 hinge inside, not at bound:** 12
- **s0 kW/K per housing unit, all:** 0.0275 [0.0041-0.0752] (n=12)
- **s0, no PV no commerce:** 0.0036 [0.0034-0.0038] (n=2)
- **s0 T_h:** 18.1 [14.9-19.0] (n=12)

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
| buffer-tank/circulation-pump/status | 1 | 280.0 | 96.0 |
| buffer-tank/hp-valve-supply/status | 2 | 280.0 | 96.0 |
| buffer-tank/hp-valves-dhw-heating/status | 17 | 395.0 | 96.0 |
| cooling/hp-valves/status | 8 | 333.0 | 96.0 |
| fluvius/p1-L1/I | 30 | 280.0 | 96.0 |
| fluvius/p1-L1/P | 30 | 274.0 | 96.0 |
| fluvius/p1-L1/U | 30 | 280.0 | 96.0 |
| fluvius/p1-L2/I | 20 | 412.5 | 96.0 |
| fluvius/p1-L2/P | 20 | 275.0 | 96.0 |
| fluvius/p1-L2/U | 20 | 412.5 | 96.0 |
| fluvius/p1-L3/I | 20 | 412.5 | 96.0 |
| fluvius/p1-L3/P | 20 | 275.0 | 96.0 |
| fluvius/p1-L3/U | 20 | 412.5 | 96.0 |
| fluvius/p1-fwd-t1/E | 30 | 280.0 | 96.0 |
| fluvius/p1-fwd-t2/E | 30 | 280.0 | 96.0 |
| fluvius/p1-fwd-tot/E | 30 | 280.0 | 96.0 |
| fluvius/p1-rev-t1/E | 21 | 412.0 | 96.0 |
| fluvius/p1-rev-t2/E | 26 | 293.5 | 96.0 |
| fluvius/p1-rev-tot/E | 27 | 280.0 | 96.0 |
| fluvius/p1-water/V | 8 | 239.0 | 96.0 |
| fluvius/p1/P | 30 | 280.0 | 96.0 |
| geothermal/hp-valve1/status | 2 | 384.0 | 96.0 |
| hp/3-way-valve/status | 4 | 127.0 | 1440.0 |
| hp/booster-heater/status | 4 | 127.0 | 1440.0 |
| hp/circulation-pump/status | 14 | 66.5 | 1440.0 |
| hp/compressor/status | 14 | 66.5 | 1440.0 |
| hp/cooling/T | 8 | 57.0 | 1440.0 |
| hp/desinfection/status | 4 | 127.0 | 1440.0 |
| hp/dhw-booster/status | 2 | 155.5 | 1431.5 |
| hp/dhw-reheat/T | 2 | 155.5 | 1431.5 |
| hp/dhw-reheat/status | 2 | 155.5 | 1431.5 |
| hp/dhw/T | 4 | 127.0 | 1440.0 |
| hp/flow-rate/Q | 14 | 66.5 | 1440.0 |
| hp/heating/T | 14 | 66.5 | 1440.0 |
| hp/hp1-brine-in/T | 2 | 239.0 | 96.0 |
| hp/hp1-brine-out/T | 2 | 239.0 | 96.0 |
| hp/hp1-brine-pump-speed/pos | 2 | 239.0 | 192.0 |
| hp/hp1-circulation-pump/status | 16 | 343.0 | 96.0 |
| hp/hp1-compressor/f | 2 | 239.0 | 96.0 |
| hp/hp1-compressor/status | 18 | 341.5 | 96.0 |
| hp/hp1-cooling/T | 9 | 344.0 | 96.0 |
| hp/hp1-defrost-startup/status | 10 | 273.0 | 96.0 |
| hp/hp1-discharge/T | 2 | 239.0 | 96.0 |
| hp/hp1-flow-rate/Q | 18 | 341.5 | 96.0 |
| hp/hp1-heating/T | 18 | 341.5 | 96.0 |
| hp/hp1-hot-water-charging/T | 2 | 239.0 | 96.0 |
| hp/hp1-hot-water-top/T | 2 | 239.0 | 96.0 |
| hp/hp1-leaving-water-pre-phe/T | 16 | 343.0 | 96.0 |
| hp/hp1-liquid-line/T | 2 | 239.0 | 96.0 |
| hp/hp1-liquid-refrigerant/T | 16 | 343.0 | 96.0 |
| hp/hp1-operation-mode/status | 18 | 341.5 | 96.0 |
| hp/hp1-outside-air/T | 18 | 267.5 | 96.0 |
| hp/hp1-return-water/T | 18 | 341.5 | 96.0 |
| hp/hp1-reversing-valve/status | 2 | 239.0 | 96.0 |
| hp/hp1-start-dhw/T | 2 | 239.0 | 96.0 |
| hp/hp1-stop-dhw/T | 2 | 239.0 | 96.0 |
| hp/hp1-suction-gas/T | 2 | 239.0 | 96.0 |
| hp/hp1-supply-line/T | 2 | 239.0 | 96.0 |
| hp/hp1-unit/error | 18 | 341.5 | 96.0 |
| hp/hp1-unit/error-code | 18 | 341.5 | 96.0 |
| hp/hp1-unit/error-sub-code | 16 | 343.0 | 96.0 |
| hp/hp1-water-leaving-cooling/T | 16 | 343.0 | 96.0 |
| hp/hp1-water-leaving-heating-min/T | 2 | 239.0 | 96.0 |
| hp/hp1-water-leaving-heating/T | 18 | 341.5 | 96.0 |
| hp/hp2-circulation-pump/status | 1 | 280.0 | 96.0 |
| hp/hp2-compressor/status | 1 | 280.0 | 96.0 |
| hp/hp2-flow-rate/Q | 1 | 275.0 | 96.0 |
| hp/hp2-heating/T | 1 | 275.0 | 96.0 |
| hp/hp2-leaving-water-pre-phe/T | 1 | 275.0 | 96.0 |
| hp/hp2-liquid-refrigerant/T | 1 | 275.0 | 96.0 |
| hp/hp2-operation-mode/status | 1 | 275.0 | 96.0 |
| hp/hp2-outside-air/T | 1 | 275.0 | 96.0 |
| hp/hp2-return-water/T | 1 | 275.0 | 96.0 |
| hp/hp2-unit/error | 1 | 275.0 | 96.0 |
| hp/hp2-unit/error-code | 1 | 275.0 | 96.0 |
| hp/hp2-unit/error-sub-code | 1 | 275.0 | 96.0 |
| hp/hp2-water-leaving-cooling/T | 1 | 275.0 | 96.0 |
| hp/hp2-water-leaving-heating/T | 1 | 275.0 | 96.0 |
| hp/leaving-water-pre-buh/T | 4 | 127.0 | 1440.0 |
| hp/leaving-water-pre-phe/T | 14 | 66.5 | 1440.0 |
| hp/liquid-refrigerant/T | 14 | 66.5 | 1440.0 |
| hp/operation-mode/status | 14 | 66.5 | 1440.0 |
| hp/outside-air/T | 8 | 126.0 | 1440.0 |
| hp/return-water/T | 14 | 66.5 | 1440.0 |
| hp/unit/error | 14 | 66.5 | 1440.0 |
| hp/unit/error-code | 14 | 66.5 | 1440.0 |
| hp/unit/error-sub-code | 14 | 66.5 | 1440.0 |
| hp/water-leaving-cooling/T | 14 | 66.5 | 1440.0 |
| hp/water-leaving-heating/T | 14 | 66.5 | 1440.0 |
| ilubat/PV/P | 7 | 32.0 | 1416.0 |
| ilubat/battery-charge/E | 7 | 348.0 | 96.0 |
| ilubat/battery-discharge/E | 7 | 348.0 | 96.0 |
| ilubat/battery/P | 7 | 348.0 | 96.0 |
| ilubat/battery/soc | 7 | 348.0 | 96.0 |
| ilubat/pv/P | 7 | 318.0 | 96.0 |
| inverter/ac-L1/I | 8 | 49.5 | 980.0 |
| inverter/ac-L1N/U | 14 | 70.0 | 1440.0 |
| inverter/ac-L2/I | 1 | 141.0 | 48.0 |
| inverter/ac-L2N/U | 2 | 36.0 | 1009.5 |
| inverter/ac-L3/I | 1 | 141.0 | 48.0 |
| inverter/ac-L3N/U | 2 | 36.0 | 1009.5 |
| inverter/ac/E | 12 | 70.0 | 1440.0 |
| inverter/ac/E_app | 14 | 70.0 | 1440.0 |
| inverter/ac/E_rea | 14 | 70.0 | 1440.0 |
| inverter/ac/I | 11 | 71.0 | 1438.0 |
| inverter/ac/P | 14 | 70.0 | 1440.0 |
| inverter/ac/f | 14 | 70.0 | 1440.0 |
| inverter/battery-charge-direction/status | 4 | 59.0 | 1440.0 |
| inverter/battery-charge/E_tot | 4 | 59.0 | 1440.0 |
| inverter/battery-charge/I_max | 4 | 59.0 | 1440.0 |
| inverter/battery-dc/I | 4 | 59.0 | 1440.0 |
| inverter/battery-dc/P | 4 | 59.0 | 1440.0 |
| inverter/battery-dc/U | 4 | 59.0 | 1440.0 |
| inverter/battery-discharge/E_tot | 4 | 59.0 | 1440.0 |
| inverter/battery-discharge/I_max | 4 | 59.0 | 1440.0 |
| inverter/battery-health/soc | 4 | 39.5 | 1440.0 |
| inverter/battery/soc | 4 | 39.5 | 1440.0 |
| inverter/bms-charge/I_max | 4 | 57.5 | 301.0 |
| inverter/bms-discharge/I_max | 4 | 57.5 | 301.0 |
| inverter/cabinet/T | 14 | 70.0 | 1440.0 |
| inverter/dc-s1/I | 8 | 49.5 | 980.0 |
| inverter/dc-s1/P | 4 | 49.5 | 1435.5 |
| inverter/dc-s1/U | 8 | 49.5 | 1439.0 |
| inverter/dc-s2/I | 8 | 49.5 | 1438.0 |
| inverter/dc-s2/P | 4 | 49.5 | 1436.0 |
| inverter/dc-s2/U | 8 | 49.5 | 1438.0 |
| inverter/dc/I | 2 | 21.5 | 1440.0 |
| inverter/dc/P | 2 | 21.5 | 1440.0 |
| inverter/dc/U | 2 | 21.5 | 1440.0 |
| inverter/grid-battery-charge/E | 4 | 49.5 | 501.5 |
| inverter/grid-consumption/E | 4 | 49.5 | 503.0 |
| inverter/grid-injection/E | 4 | 49.5 | 502.0 |
| inverter/grid-meter/P | 4 | 57.5 | 301.5 |
| inverter/household-load/P | 4 | 57.5 | 301.5 |
| inverter/inv1-ac-L1/I | 18 | 304.0 | 67.5 |
| inverter/inv1-ac-L1N/U | 18 | 340.5 | 96.0 |
| inverter/inv1-ac-L2/I | 4 | 250.0 | 60.5 |
| inverter/inv1-ac-L2N/U | 4 | 250.0 | 96.0 |
| inverter/inv1-ac-L3/I | 4 | 250.0 | 60.5 |
| inverter/inv1-ac-L3N/U | 4 | 250.0 | 96.0 |
| inverter/inv1-ac/E | 10 | 22.0 | 96.0 |
| inverter/inv1-ac/E_app | 14 | 16.0 | 96.0 |
| inverter/inv1-ac/E_rea | 14 | 16.0 | 96.0 |
| inverter/inv1-ac/P | 18 | 340.5 | 69.0 |
| inverter/inv1-ac/P_app | 18 | 326.5 | 68.5 |
| inverter/inv1-ac/P_rea | 18 | 319.5 | 64.0 |
| inverter/inv1-ac/f | 18 | 340.5 | 77.25 |
| inverter/inv1-battery-charge-direction/status | 5 | 341.0 | 96.0 |
| inverter/inv1-battery-charge/E | 5 | 326.0 | 96.0 |
| inverter/inv1-battery-charge/E_tot | 4 | 18.0 | 96.0 |
| inverter/inv1-battery-charge/I_max | 5 | 341.0 | 96.0 |
| inverter/inv1-battery-dc/I | 5 | 341.0 | 96.0 |
| inverter/inv1-battery-dc/P | 5 | 341.0 | 96.0 |
| inverter/inv1-battery-dc/U | 5 | 341.0 | 96.0 |
| inverter/inv1-battery-discharge/E | 5 | 326.0 | 96.0 |
| inverter/inv1-battery-discharge/E_tot | 4 | 18.0 | 96.0 |
| inverter/inv1-battery-discharge/I_max | 5 | 341.0 | 96.0 |
| inverter/inv1-battery-health/soc | 5 | 326.0 | 96.0 |
| inverter/inv1-battery/soc | 5 | 326.0 | 96.0 |
| inverter/inv1-bms-charge/I_max | 5 | 333.0 | 96.0 |
| inverter/inv1-bms-discharge/I_max | 5 | 333.0 | 96.0 |
| inverter/inv1-cabinet/T | 18 | 340.5 | 96.0 |
| inverter/inv1-grid-battery-charge/E | 5 | 341.0 | 96.0 |
| inverter/inv1-grid-consumption/E | 5 | 341.0 | 96.0 |
| inverter/inv1-grid-injection/E | 18 | 323.0 | 96.0 |
| inverter/inv1-grid-meter/P | 5 | 179.0 | 96.0 |
| inverter/inv1-household-load/P | 5 | 179.0 | 96.0 |
| inverter/inv1-inverted-total/E | 5 | 341.0 | 96.0 |
| inverter/inv1-pv-dc-s1/I | 18 | 304.0 | 63.5 |
| inverter/inv1-pv-dc-s1/P | 13 | 274.0 | 60.0 |
| inverter/inv1-pv-dc-s1/U | 18 | 304.0 | 76.5 |
| inverter/inv1-pv-dc-s2/I | 18 | 303.0 | 68.0 |
| inverter/inv1-pv-dc-s2/P | 13 | 274.0 | 60.0 |
| inverter/inv1-pv-dc-s2/U | 18 | 304.0 | 76.5 |
| inverter/inv1-pv-dc/P | 5 | 341.0 | 96.0 |
| inverter/inv1-pv/E | 5 | 273.0 | 96.0 |
| inverter/inv1-rectifier/P | 5 | 179.0 | 96.0 |
| inverter/inv2-ac-L1/I | 1 | 275.0 | 96.0 |
| inverter/inv2-ac-L1N/U | 1 | 275.0 | 96.0 |
| inverter/inv2-ac/P | 1 | 275.0 | 96.0 |
| inverter/inv2-ac/P_app | 1 | 275.0 | 96.0 |
| inverter/inv2-ac/P_rea | 1 | 275.0 | 96.0 |
| inverter/inv2-ac/f | 1 | 275.0 | 96.0 |
| inverter/inv2-cabinet/T | 1 | 275.0 | 96.0 |
| inverter/inv2-grid-injection/E | 1 | 122.0 | 45.0 |
| inverter/inv2-inverted-total/E | 1 | 133.0 | 44.0 |
| inverter/inv2-pv-dc-s1/I | 1 | 275.0 | 96.0 |
| inverter/inv2-pv-dc-s1/U | 1 | 275.0 | 96.0 |
| inverter/inv2-pv-dc-s2/I | 1 | 275.0 | 96.0 |
| inverter/inv2-pv-dc-s2/U | 1 | 275.0 | 96.0 |
| inverter/inv2-pv-dc/P | 1 | 275.0 | 96.0 |
| inverter/inv2-pv/E | 1 | 133.0 | 44.0 |
| inverter/inv2-rectifier/P | 1 | 275.0 | 96.0 |
| inverter/inverted-total/E | 4 | 49.5 | 501.5 |
| inverter/pv-dc/P | 4 | 49.5 | 502.0 |
| inverter/rectifier/P | 4 | 57.5 | 302.0 |
| mid-c/btes-in/T | 8 | 320.5 | 96.0 |
| mid-c/btes-out/T | 8 | 320.5 | 96.0 |
| mid-c/btes-regeneration/E | 6 | 384.0 | 96.0 |
| mid-c/btes/E | 6 | 384.0 | 96.0 |
| mid-c/btes/P | 8 | 320.5 | 96.0 |
| mid-c/btes/Q | 8 | 320.5 | 96.0 |
| mid-c/dhw-cooling/E | 13 | 55.0 | 1440.0 |
| mid-c/dhw-heat/E | 19 | 380.0 | 96.0 |
| mid-c/dhw-in/T | 19 | 386.0 | 96.0 |
| mid-c/dhw-out/T | 19 | 386.0 | 96.0 |
| mid-c/dhw/P | 19 | 386.0 | 96.0 |
| mid-c/dhw/Q | 19 | 386.0 | 96.0 |
| mid-c/dhw/V | 19 | 373.0 | 96.0 |
| mid-c/hp-cooling/E | 13 | 57.0 | 1440.0 |
| mid-c/hp-heat/E | 13 | 76.0 | 1440.0 |
| mid-c/hp-in/T | 13 | 76.0 | 1440.0 |
| mid-c/hp-out/T | 13 | 76.0 | 1440.0 |
| mid-c/hp/P | 13 | 76.0 | 1440.0 |
| mid-c/hp/Q | 13 | 76.0 | 1440.0 |
| mid-c/hp1-cooling/E | 17 | 341.0 | 96.0 |
| mid-c/hp1-heat/E | 17 | 341.0 | 96.0 |
| mid-c/hp1-in/T | 19 | 340.0 | 96.0 |
| mid-c/hp1-out/T | 19 | 340.0 | 96.0 |
| mid-c/hp1/P | 19 | 340.0 | 96.0 |
| mid-c/hp1/Q | 19 | 340.0 | 96.0 |
| mid-c/hp2-cooling/E | 1 | 275.0 | 96.0 |
| mid-c/hp2-heat/E | 1 | 275.0 | 96.0 |
| mid-c/hp2-in/T | 1 | 275.0 | 96.0 |
| mid-c/hp2-out/T | 1 | 275.0 | 96.0 |
| mid-c/hp2/P | 1 | 275.0 | 96.0 |
| mid-c/hp2/Q | 1 | 275.0 | 96.0 |
| mid-c/solar-thermal-cooling/E | 2 | 215.5 | 96.0 |
| mid-c/solar-thermal-heat/E | 2 | 218.5 | 96.0 |
| mid-c/solar-thermal-in/T | 2 | 379.5 | 96.0 |
| mid-c/solar-thermal-out/T | 2 | 379.5 | 96.0 |
| mid-c/solar-thermal/P | 2 | 381.5 | 96.0 |
| mid-c/solar-thermal/Q | 2 | 379.5 | 96.0 |
| mid-c/space-heating-cooling/E | 25 | 280.0 | 96.0 |
| mid-c/space-heating-dhw/V | 12 | 239.0 | 96.0 |
| mid-c/space-heating-heat/E | 27 | 376.0 | 96.0 |
| mid-c/space-heating-in/T | 27 | 376.0 | 96.0 |
| mid-c/space-heating-out/T | 27 | 376.0 | 96.0 |
| mid-c/space-heating/P | 27 | 376.0 | 96.0 |
| mid-c/space-heating/Q | 27 | 376.0 | 96.0 |
| mid-e/buffer-tank-resistance/E | 19 | 412.0 | 96.0 |
| mid-e/buffer-tank-resistance/P | 19 | 457.0 | 96.0 |
| mid-e/hp-L1/I | 8 | 47.5 | 1440.0 |
| mid-e/hp-L1/P | 2 | 135.5 | 96.0 |
| mid-e/hp-L1/U | 8 | 47.5 | 1439.0 |
| mid-e/hp-L2/I | 2 | 66.5 | 1438.0 |
| mid-e/hp-L2/P | 2 | 135.5 | 96.0 |
| mid-e/hp-L2/U | 2 | 66.5 | 1438.0 |
| mid-e/hp-L3/I | 2 | 66.5 | 1438.0 |
| mid-e/hp-L3/P | 2 | 135.5 | 96.0 |
| mid-e/hp-L3/U | 2 | 66.5 | 1438.0 |
| mid-e/hp/E | 14 | 201.5 | 1440.0 |
| mid-e/hp/P | 14 | 201.5 | 1440.0 |
| mid-e/hp/f | 8 | 47.5 | 1438.75 |
| mid-e/hp1-L1/I | 13 | 16.0 | 96.0 |
| mid-e/hp1-L1/U | 9 | 16.0 | 96.0 |
| mid-e/hp1-L2/I | 6 | 257.0 | 96.0 |
| mid-e/hp1-L2/U | 2 | 71.0 | 96.0 |
| mid-e/hp1-L3/I | 6 | 257.0 | 96.0 |
| mid-e/hp1-L3/U | 2 | 71.0 | 96.0 |
| mid-e/hp1/E | 18 | 341.0 | 96.0 |
| mid-e/hp1/P | 18 | 341.0 | 96.0 |
| mid-e/hp1/f | 18 | 305.5 | 96.0 |
| mid-e/hp2-L1/I | 1 | 275.0 | 96.0 |
| mid-e/hp2-L2/I | 1 | 275.0 | 96.0 |
| mid-e/hp2-L3/I | 1 | 275.0 | 96.0 |
| mid-e/hp2/E | 1 | 44.0 | 96.0 |
| mid-e/hp2/P | 1 | 275.0 | 96.0 |
| mid-e/hp2/f | 1 | 275.0 | 96.0 |
| mid-e/inverter1-pv-L1/I | 18 | 341.0 | 96.0 |
| mid-e/inverter1-pv-L1/U | 18 | 341.0 | 96.0 |
| mid-e/inverter1-pv-L2/I | 4 | 257.0 | 96.0 |
| mid-e/inverter1-pv-L2/U | 4 | 257.0 | 96.0 |
| mid-e/inverter1-pv-L3/I | 4 | 257.0 | 96.0 |
| mid-e/inverter1-pv-L3/U | 4 | 257.0 | 96.0 |
| mid-e/inverter1-pv-fwd/E | 17 | 341.0 | 96.0 |
| mid-e/inverter1-pv-rev/E | 17 | 341.0 | 96.0 |
| mid-e/inverter1-pv/P | 18 | 340.0 | 96.0 |
| mid-e/inverter2-pv-L1/I | 1 | 275.0 | 96.0 |
| mid-e/inverter2-pv-L1/U | 1 | 275.0 | 96.0 |
| mid-e/inverter2-pv-fwd/E | 1 | 133.0 | 96.0 |
| mid-e/inverter2-pv-rev/E | 1 | 133.0 | 96.0 |
| mid-e/inverter2-pv/P | 1 | 275.0 | 96.0 |
| mid-e/lito-box-L1/I | 8 | 40.0 | 1433.0 |
| mid-e/lito-box-L1/U | 8 | 40.0 | 1433.0 |
| mid-e/lito-box-fwd/E | 13 | 544.0 | 96.0 |
| mid-e/lito-box-rev/E | 13 | 544.0 | 96.0 |
| mid-e/lito-box-rev/P | 1 | 22.0 | 1437.0 |
| mid-e/lito-box/I | 13 | 536.0 | 96.0 |
| mid-e/lito-box/P | 13 | 544.0 | 96.0 |
| mid-e/lito-box/U | 13 | 536.0 | 96.0 |
| mid-e/pv-L1/I | 14 | 154.5 | 1440.0 |
| mid-e/pv-L1/P | 1 | 147.0 | 96.0 |
| mid-e/pv-L1/U | 14 | 154.5 | 1440.0 |
| mid-e/pv-L2/I | 1 | 76.0 | 1440.0 |
| mid-e/pv-L2/P | 1 | 147.0 | 96.0 |
| mid-e/pv-L2/U | 1 | 76.0 | 1440.0 |
| mid-e/pv-L3/I | 1 | 76.0 | 1440.0 |
| mid-e/pv-L3/P | 1 | 147.0 | 96.0 |
| mid-e/pv-L3/U | 1 | 76.0 | 1440.0 |
| mid-e/pv-fwd/E | 14 | 154.5 | 1439.5 |
| mid-e/pv-rev/E | 14 | 154.5 | 1440.0 |
| mid-e/pv/P | 14 | 155.5 | 1440.0 |
| mid-e/radiation-panel-bathroom/E | 21 | 280.0 | 96.0 |
| mid-e/radiation-panel-bathroom/P | 21 | 280.0 | 96.0 |
| mid-e/stovetop/E | 26 | 280.0 | 96.0 |
| mid-e/stovetop/P | 27 | 351.0 | 96.0 |
| mid-e/ventilation/E | 20 | 435.0 | 96.0 |
| mid-e/ventilation/P | 20 | 435.0 | 96.0 |
| mid-e/water-heater/E | 27 | 396.0 | 96.0 |
| mid-e/water-heater/P | 27 | 396.0 | 96.0 |
| plc/control/day | 1 | 342.0 | 96.0 |
| plc/control/time | 1 | 342.0 | 96.0 |
| pv/battery-charge-direction/status | 1 | 43.0 | 1440.0 |
| pv/battery-charge/E_tot | 8 | 64.0 | 1432.0 |
| pv/battery-charge/I_max | 1 | 43.0 | 1440.0 |
| pv/battery-dc/P | 8 | 64.0 | 1432.0 |
| pv/battery-dc/U | 1 | 43.0 | 1440.0 |
| pv/battery-discharge/E_tot | 8 | 64.0 | 1432.0 |
| pv/battery-discharge/I_max | 1 | 43.0 | 1440.0 |
| pv/battery-health/soc | 1 | 43.0 | 1440.0 |
| pv/battery-pv-dc/P | 7 | 64.0 | 1432.0 |
| pv/battery/soc | 8 | 64.0 | 1432.0 |
| pv/inverter-ac-L1/I | 1 | 8.0 | 1440.0 |
| pv/inverter-ac-L1N/U | 11 | 127.0 | 1440.0 |
| pv/inverter-ac-L2/I | 1 | 8.0 | 1440.0 |
| pv/inverter-ac-L2N/U | 2 | 25.5 | 1440.0 |
| pv/inverter-ac-L3/I | 1 | 8.0 | 1440.0 |
| pv/inverter-ac-L3N/U | 2 | 25.5 | 1440.0 |
| pv/inverter-ac/E | 11 | 127.0 | 1440.0 |
| pv/inverter-ac/E_app | 11 | 127.0 | 1440.0 |
| pv/inverter-ac/E_rea | 11 | 127.0 | 1440.0 |
| pv/inverter-ac/I | 10 | 130.5 | 1440.0 |
| pv/inverter-ac/P | 11 | 127.0 | 1440.0 |
| pv/inverter-ac/f | 11 | 127.0 | 1440.0 |
| pv/inverter-cabinet/T | 11 | 127.0 | 1440.0 |
| pv/inverter-dc-s1/I | 1 | 8.0 | 1440.0 |
| pv/inverter-dc-s1/P | 1 | 8.0 | 1439.0 |
| pv/inverter-dc-s1/U | 1 | 8.0 | 1440.0 |
| pv/inverter-dc-s2/I | 1 | 8.0 | 1440.0 |
| pv/inverter-dc-s2/P | 1 | 8.0 | 1439.0 |
| pv/inverter-dc-s2/U | 1 | 8.0 | 1440.0 |
| pv/inverter-dc/I | 1 | 43.0 | 1440.0 |
| pv/inverter-dc/P | 1 | 43.0 | 1440.0 |
| pv/inverter-dc/U | 1 | 43.0 | 1440.0 |
| radiation-panel/infrared/status | 21 | 280.0 | 192.0 |
| relay/buffer-tank-heating-resistance/status | 19 | 382.0 | 96.0 |
| sensor/bathroom-window-front/status | 8 | 239.0 | 96.0 |
| sensor/bedroom1-window-back/status | 6 | 239.0 | 96.0 |
| sensor/bedroom1-window-front/status | 21 | 392.0 | 96.0 |
| sensor/bedroom2-window-back/status | 25 | 386.0 | 96.0 |
| sensor/bedroom2-window-back2/status | 3 | 239.0 | 96.0 |
| sensor/bedroom2-window-front/status | 18 | 395.5 | 96.0 |
| sensor/bedroom2-window-side/status | 3 | 239.0 | 96.0 |
| sensor/bedroom3-window-back/status | 2 | 257.0 | 96.0 |
| sensor/bedroom3-window-front/status | 5 | 239.0 | 96.0 |
| sensor/bedroom3-window-roof/status | 17 | 396.0 | 96.0 |
| sensor/bedroom3-window-side/status | 3 | 239.0 | 96.0 |
| sensor/bedroom4-window-front/status | 3 | 239.0 | 96.0 |
| sensor/buffer-tank-bottom/T | 19 | 392.0 | 96.0 |
| sensor/buffer-tank-cascade/T | 1 | 280.0 | 96.0 |
| sensor/buffer-tank-mid-bottom/T | 19 | 392.0 | 96.0 |
| sensor/buffer-tank-mid-top/T | 19 | 392.0 | 96.0 |
| sensor/buffer-tank-top/T | 19 | 392.0 | 96.0 |
| sensor/central-heating/p | 7 | 465.0 | 96.0 |
| sensor/dw-supply-cold/T | 18 | 393.5 | 96.0 |
| sensor/dw-supply-hot/T | 18 | 393.5 | 96.0 |
| sensor/entrance-hall-window-front/status | 23 | 386.0 | 96.0 |
| sensor/entrance-hall-window-side/status | 19 | 395.0 | 96.0 |
| sensor/hp-geothermal-return/T | 2 | 42.0 | 467.75 |
| sensor/hp-geothermal-supply/T | 2 | 42.0 | 467.75 |
| sensor/hp1-geothermal-return/T | 4 | 290.5 | 96.0 |
| sensor/hp1-geothermal-supply/T | 4 | 290.5 | 96.0 |
| sensor/hp1-geothermal/p | 2 | 188.0 | 96.0 |
| sensor/kitchen-window-back/status | 4 | 239.0 | 96.0 |
| sensor/kitchen-window-back2/status | 1 | 239.0 | 96.0 |
| sensor/kitchen-window-front/status | 6 | 239.0 | 96.0 |
| sensor/litobox/T | 4 | 434.0 | 96.0 |
| sensor/living-room-window-back/status | 27 | 382.0 | 96.0 |
| sensor/living-room-window-back2/status | 1 | 239.0 | 96.0 |
| sensor/living-room-window-front/status | 3 | 239.0 | 96.0 |
| sensor/living-room-window-side/status | 17 | 396.0 | 96.0 |
| sensor/outside-air/T | 3 | 239.0 | 96.0 |
| sensor/outside/T | 2 | 114.0 | 1440.0 |
| sensor/solar-thermal-collector/T | 4 | 331.0 | 96.0 |
| sensor/solar-thermal-return/T | 4 | 58.0 | 96.0 |
| sensor/solar-thermal-supply/T | 4 | 58.0 | 96.0 |
| sensor/solar-thermal/p | 4 | 300.5 | 96.0 |
| sensor/space-heating-return/T | 19 | 392.0 | 96.0 |
| sensor/space-heating-supply/T | 19 | 392.0 | 96.0 |
| sensor/storage-window-back/status | 2 | 239.0 | 96.0 |
| sensor/storage-window-front/status | 5 | 239.0 | 96.0 |
| sensor/ventilation-bathroom-extraction/T | 4 | 489.0 | 96.0 |
| sensor/ventilation-bedroom-extraction/T | 4 | 489.0 | 96.0 |
| sensor/ventilation-extraction/T | 23 | 280.0 | 96.0 |
| sensor/ventilation-inflow-fresh/T | 13 | 386.0 | 96.0 |
| sensor/ventilation-kitchen-extraction/T | 4 | 489.0 | 96.0 |
| sensor/ventilation-outflow-waste/Q | 14 | 259.0 | 96.0 |
| sensor/ventilation-outflow-waste/T | 20 | 386.0 | 96.0 |
| sensor/ventilation-pulsion/T | 13 | 386.0 | 96.0 |
| sensor/ventilation-storage-extraction/T | 4 | 489.0 | 96.0 |
| sensor/ventilation-toilet-extraction/T | 4 | 489.0 | 96.0 |
| solar-collector/circulation-pump/status | 4 | 300.5 | 96.0 |
| solar-collector/circulation-pump/time | 4 | 3.5 | 96.0 |
| solar-collector/hp-valve2/status | 2 | 384.0 | 96.0 |
| space-cooling/source-pump/status | 1 | 239.0 | 96.0 |
| space-heating/circulation-pump/status | 19 | 392.0 | 96.0 |
| space-heating/mix-valve-supply/pos | 19 | 386.0 | 96.0 |
| space-heating/valve-supply/T | 4 | 23.5 | 1408.75 |
| space-heating/valve-supply/status | 4 | 103.0 | 1440.0 |
| switch/user-mode-hvac/status | 1 | 22.0 | 96.0 |
| thermostat/bathroom-co2/c | 27 | 382.0 | 96.0 |
| thermostat/bathroom-cooling/T | 3 | 239.0 | 96.0 |
| thermostat/bathroom-display/T | 27 | 382.0 | 96.0 |
| thermostat/bathroom-heating/T | 27 | 382.0 | 96.0 |
| thermostat/bathroom-radiator-2-way-valve/pos | 8 | 413.0 | 192.0 |
| thermostat/bathroom-radiator-control-value/pos | 2 | 96.0 | 1404.5 |
| thermostat/bathroom/RH | 27 | 382.0 | 96.0 |
| thermostat/bathroom/T | 27 | 382.0 | 96.0 |
| thermostat/bedroom1-co2/c | 27 | 382.0 | 96.0 |
| thermostat/bedroom1-cooling/T | 17 | 280.0 | 96.0 |
| thermostat/bedroom1-display/T | 27 | 382.0 | 96.0 |
| thermostat/bedroom1-heating/T | 27 | 382.0 | 96.0 |
| thermostat/bedroom1-radiator-2-way-valve/pos | 8 | 413.0 | 192.0 |
| thermostat/bedroom1-radiator-control-value/pos | 2 | 96.0 | 1404.5 |
| thermostat/bedroom1-ventilo-2-way-valve/status | 19 | 376.0 | 192.0 |
| thermostat/bedroom1-ventilo-convector-fan/pos | 19 | 376.0 | 192.0 |
| thermostat/bedroom1-ventilo-convector-fan/status | 2 | 114.0 | 2880.0 |
| thermostat/bedroom1/RH | 27 | 382.0 | 96.0 |
| thermostat/bedroom1/T | 27 | 382.0 | 96.0 |
| thermostat/bedroom2-co2/c | 25 | 386.0 | 96.0 |
| thermostat/bedroom2-cooling/T | 15 | 382.0 | 96.0 |
| thermostat/bedroom2-display/T | 25 | 386.0 | 96.0 |
| thermostat/bedroom2-heating/T | 25 | 386.0 | 96.0 |
| thermostat/bedroom2-radiator-2-way-valve/pos | 8 | 413.0 | 192.0 |
| thermostat/bedroom2-ventilo-2-way-valve/status | 17 | 382.0 | 192.0 |
| thermostat/bedroom2-ventilo-convector-fan/pos | 17 | 382.0 | 192.0 |
| thermostat/bedroom2-ventilo-convector-fan/status | 2 | 114.0 | 2880.0 |
| thermostat/bedroom2/RH | 25 | 386.0 | 96.0 |
| thermostat/bedroom2/T | 25 | 386.0 | 96.0 |
| thermostat/bedroom3-co2/c | 25 | 386.0 | 96.0 |
| thermostat/bedroom3-cooling/T | 15 | 382.0 | 96.0 |
| thermostat/bedroom3-display/T | 25 | 386.0 | 96.0 |
| thermostat/bedroom3-heating/T | 25 | 386.0 | 96.0 |
| thermostat/bedroom3-radiator-2-way-valve/pos | 8 | 413.0 | 192.0 |
| thermostat/bedroom3-ventilo-2-way-valve/status | 17 | 382.0 | 192.0 |
| thermostat/bedroom3-ventilo-convector-fan/pos | 17 | 382.0 | 192.0 |
| thermostat/bedroom3-ventilo-convector-fan/status | 2 | 114.0 | 2880.0 |
| thermostat/bedroom3/RH | 25 | 386.0 | 96.0 |
| thermostat/bedroom3/T | 25 | 386.0 | 96.0 |
| thermostat/bedroom4-co2/c | 3 | 239.0 | 96.0 |
| thermostat/bedroom4-cooling/T | 2 | 239.0 | 96.0 |
| thermostat/bedroom4-display/T | 3 | 239.0 | 96.0 |
| thermostat/bedroom4-heating/T | 3 | 239.0 | 96.0 |
| thermostat/bedroom4-radiator-2-way-valve/pos | 1 | 239.0 | 192.0 |
| thermostat/bedroom4-ventilo-2-way-valve/status | 2 | 256.5 | 192.0 |
| thermostat/bedroom4-ventilo-convector-fan/pos | 2 | 256.5 | 192.0 |
| thermostat/bedroom4/RH | 3 | 239.0 | 96.0 |
| thermostat/bedroom4/T | 3 | 239.0 | 96.0 |
| thermostat/entrance-hall-co2/c | 25 | 386.0 | 96.0 |
| thermostat/entrance-hall-cooling/T | 3 | 239.0 | 96.0 |
| thermostat/entrance-hall-display/T | 25 | 386.0 | 96.0 |
| thermostat/entrance-hall-heating/T | 25 | 386.0 | 96.0 |
| thermostat/entrance-hall-radiator-2-way-valve/pos | 25 | 386.0 | 192.0 |
| thermostat/entrance-hall-radiator-control-value/pos | 2 | 96.0 | 1404.5 |
| thermostat/entrance-hall-ventilo-2-way-valve/status | 2 | 51.0 | 2806.0 |
| thermostat/entrance-hall/RH | 27 | 382.0 | 96.0 |
| thermostat/entrance-hall/T | 27 | 382.0 | 96.0 |
| thermostat/kitchen-co2/c | 27 | 382.0 | 96.0 |
| thermostat/kitchen-cooling/T | 17 | 280.0 | 96.0 |
| thermostat/kitchen-display/T | 27 | 382.0 | 96.0 |
| thermostat/kitchen-heating/T | 27 | 382.0 | 96.0 |
| thermostat/kitchen-radiator-2-way-valve/pos | 8 | 413.0 | 192.0 |
| thermostat/kitchen-radiator-control-value/pos | 2 | 96.0 | 1404.5 |
| thermostat/kitchen-ventilo-2-way-valve/status | 19 | 376.0 | 192.0 |
| thermostat/kitchen-ventilo-convector-fan/pos | 19 | 376.0 | 192.0 |
| thermostat/kitchen-ventilo-convector-fan/status | 2 | 114.0 | 2880.0 |
| thermostat/kitchen/RH | 27 | 382.0 | 96.0 |
| thermostat/kitchen/T | 27 | 382.0 | 96.0 |
| thermostat/living-room-co2/c | 27 | 382.0 | 96.0 |
| thermostat/living-room-cooling/T | 17 | 280.0 | 96.0 |
| thermostat/living-room-display/T | 27 | 382.0 | 96.0 |
| thermostat/living-room-heating/T | 27 | 382.0 | 96.0 |
| thermostat/living-room-operation-mode/status | 2 | 114.0 | 1440.0 |
| thermostat/living-room-radiator-2-way-valve/pos | 8 | 413.0 | 192.0 |
| thermostat/living-room-radiator-control-value/pos | 2 | 96.0 | 1404.5 |
| thermostat/living-room-ventilo-2-way-valve/status | 19 | 379.0 | 192.0 |
| thermostat/living-room-ventilo-convector-fan/pos | 19 | 376.0 | 192.0 |
| thermostat/living-room-ventilo-convector-fan/status | 2 | 114.0 | 2880.0 |
| thermostat/living-room/RH | 27 | 382.0 | 96.0 |
| thermostat/living-room/T | 27 | 382.0 | 96.0 |
| thermostat/operation-mode/status | 27 | 382.0 | 96.0 |
| thermostat/storage/RH | 27 | 382.0 | 96.0 |
| thermostat/storage/T | 27 | 382.0 | 96.0 |
| thermostat/toilet1/RH | 23 | 382.0 | 96.0 |
| thermostat/toilet1/T | 23 | 382.0 | 96.0 |
| thermostat/toilet2/RH | 15 | 396.0 | 96.0 |
| thermostat/toilet2/T | 15 | 396.0 | 96.0 |
| ventilation/damper-extraction/status | 10 | 239.0 | 96.0 |
| ventilation/fan/Q | 4 | 121.5 | 1440.0 |
| ventilation/fan/pos | 18 | 328.0 | 96.0 |

### Fluvius 2024 files

| file | meters | complete | hp | ev | pv | flag_changes | import_MWh_median | export_MWh_median |
|---|---|---|---|---|---|---|---|---|
| EV_geen_ZP | 300 | 300 | 0 | 300 | 0 | 0 | 5.0817239999999995 | 0.0 |
| EV_met_ZP | 300 | 300 | 0 | 300 | 300 | 0 | 3.3239545 | 2.1941355 |
| WP_EV_geen_ZP | 300 | 300 | 300 | 300 | 0 | 0 | 8.6972745 | 0.0 |
| WP_EV_met_ZP | 300 | 300 | 300 | 300 | 300 | 0 | 7.822340499999999 | 2.790692 |
| WP_geen_ZP | 300 | 300 | 300 | 0 | 0 | 0 | 6.5451429999999995 | 0.0 |
| WP_met_ZP | 300 | 300 | 300 | 0 | 300 | 0 | 4.6618155 | 2.8113355 |
| enkel_ZP | 300 | 300 | 0 | 0 | 300 | 0 | 1.8506070000000001 | 2.1920785 |
| geen_ZP | 300 | 300 | 0 | 0 | 0 | 0 | 2.3438689999999998 | 0.0 |

### Envelopes (v1.1)

| pool | HP | fill | HP per split (test) | HP per split (train) | test subs <=15% | test subs 15-35% | test subs 35-65% | test subs >65% | max size p=0.05 | max size p=0.1 | max size p=0.2 | max size p=0.3 | max size p=0.5 | max size p=0.8 | max size p=1.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BE monitoring (HP+P1 complete) + Fluvius 2024 fill | 9 | 300 | 2.0 | 7.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Fluvius 2024 HP-flag (no PV, no EV) + Fluvius 2024 fill | 300 | 300 | 75.0 | 225.0 | 35.0 | 40.0 | 20.0 | 30.0 | 40.0 | 80.0 | 80.0 | 80.0 | 80.0 | 40.0 | 40.0 |
| US-NEEA cal2023 | 57 | 49 | 15.0 | 42.0 | 20.0 | 20.0 | 5.0 | 0.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 0.0 | 0.0 |
