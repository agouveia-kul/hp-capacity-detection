## Design envelopes (protocol v1 rules)

Source: `scripts/audit/envelope_v2.py` (config `iter04_inventory`); grid sizes [10, 20, 40, 80, 120], p [0.05, 0.1, 0.2, 0.3, 0.5, 1.0], max_overlap 0.75, >= 3 HP per station and split, {'train': 10, 'test': 5} substations per cell; split seeds 0..19.

| pool | HP households | stations | stations >= 30 HP | train HP (used) | test HP (used) | fill | test subs <=15% | test subs 15-35% | test subs 35-65% | test subs >65% | test subs total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B* (cal2023, reference) | 86 | 5 | 1 | 62.0 | 20.0 | 1291 | 75.0 | 40.0 | 10.0 | 5.0 | 130.0 |
| GB-EoH 2020/21 | 18 | 4 | 0 | 11.0 | 0.0 | 5093 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| GB-EoH 2021/22 | 433 | 29 | 3 | 309.0 | 90.0 | 5093 | 265.0 | 145.0 | 30.0 | 15.0 | 455.0 |
| GB-EoH 2022/23 | 370 | 26 | 3 | 264.0 | 71.0 | 5093 | 190.0 | 110.0 | 30.0 | 15.0 | 345.0 |
| GB-RHPP Nov13-Feb14 | 114 | 1 | 1 | 86.0 | 28.0 | 4796 | 50.0 | 35.0 | 15.0 | 10.0 | 110.0 |
| US-NEEA cal2023 | 57 | 3 | 0 | 42.0 | 13.0 | 49 | 20.0 | 20.0 | 5.0 | 0.0 | 45.0 |

### B* (cal2023, reference)

Fill: Kaiser clean dwellings (same years, KLO).

HP households per station (mean over 20 split seeds; stations with < 3 HP in a split build no substation):

| station | test | train |
|---|---|---|
| HbsbG | 0.0 | 1.0 |
| Hg | 4.0 | 12.0 |
| KLO | 16.0 | 46.0 |
| MqO | 2.0 | 4.0 |
| z6I | 0.0 | 1.0 |

Test substations per Paper A penetration bin (mean per seed): {'<=15%': 75.0, '15-35%': 40.0, '35-65%': 10.0, '>65%': 5.0}

Max feeder size in the grid (<= 120) and uncapped (best test station; median over seeds):

| p=0.05 | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=1.0 | uncapped p=0.05 | uncapped p=0.2 | uncapped p=0.5 | uncapped p=1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 120.0 | 120.0 | 40.0 | 40.0 | 20.0 | 10.0 | 240.0 | 60.0 | 24.0 | 12.0 |

### GB-EoH 2020/21

Fill: LCL 5093 households >= 90 % in 2012/13 (8-10 years earlier, London). HP types (HP_Installed) {'ASHP': 10, 'HT-ASHP': 8}; HP_Size_kW for 18, median 7.0 kW; oversizing HP_Size/MCS_SHLoad median 1.18 [IQR 1.04-1.31]; robust 15-min peak / HP_Size median 0.51.

HP households per station (mean over 20 split seeds; stations with < 3 HP in a split build no substation):

| station | test | train | postcode areas (top 3) |
|---|---|---|---|
| G000 | 2.0 | 7.0 | {'EH': 8, 'KY': 1} |
| G001 | 1.0 | 2.0 | {'TD': 3} |
| G002 | 1.0 | 4.0 | {'NE': 5} |
| G003 | 0.0 | 1.0 | {'G': 1} |

Test substations per Paper A penetration bin (mean per seed): {'<=15%': 0.0, '15-35%': 0.0, '35-65%': 0.0, '>65%': 0.0}

Max feeder size in the grid (<= 120) and uncapped (best test station; median over seeds):

| p=0.05 | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=1.0 | uncapped p=0.05 | uncapped p=0.2 | uncapped p=0.5 | uncapped p=1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 30.0 | 7.0 | 3.0 | 1.0 |

### GB-EoH 2021/22

Fill: LCL 5093 households >= 90 % in 2012/13 (8-10 years earlier, London). HP types (HP_Installed) {'ASHP': 249, 'HT-ASHP': 158, 'GSHP': 26}; HP_Size_kW for 433, median 8.5 kW; oversizing HP_Size/MCS_SHLoad median 1.21 [IQR 1.06-1.38]; robust 15-min peak / HP_Size median 0.48.

HP households per station (mean over 20 split seeds; stations with < 3 HP in a split build no substation):

| station | test | train | postcode areas (top 3) |
|---|---|---|---|
| G000 | 0.0 | 1.0 | {'SL': 1} |
| G001 | 26.0 | 78.0 | {'NE': 93, 'DH': 10, 'SR': 1} |
| G002 | 34.0 | 102.0 | {'EH': 114, 'KY': 18, 'FK': 4} |
| G003 | 1.0 | 3.0 | {'ME': 3, 'TN': 1} |
| G004 | 0.0 | 2.0 | {'NE': 2} |
| G005 | 1.0 | 4.0 | {'ML': 5} |
| G006 | 4.0 | 14.0 | {'KY': 11, 'EH': 6, 'DD': 1} |
| G007 | 2.0 | 7.0 | {'TD': 5, 'EH': 4} |
| G008 | 4.0 | 11.0 | {'TN': 8, 'BN': 7} |
| G009 | 10.0 | 29.0 | {'TD': 27, 'EH': 12} |
| G010 | 1.0 | 4.0 | {'PO': 4, 'GU': 1} |
| G011 | 3.0 | 9.0 | {'BN': 10, 'RH': 2} |
| G012 | 2.0 | 4.0 | {'TN': 4, 'CT': 2} |
| G013 | 4.0 | 10.0 | {'GU': 13, 'RG': 1} |
| G014 | 2.0 | 5.0 | {'G': 7} |
| G015 | 0.0 | 2.0 | {'TD': 2} |
| G016 | 1.0 | 3.0 | {'GU': 3, 'SO': 1} |
| G017 | 5.0 | 15.0 | {'KT': 12, 'TN': 5, 'CR': 2} |
| G018 | 0.0 | 1.0 | {'OX': 1} |
| G019 | 1.0 | 4.0 | {'PH': 4, 'FK': 1} |
| G020 | 1.0 | 2.0 | {'TD': 3} |
| G021 | 0.0 | 2.0 | {'SO': 2} |
| G022 | 2.0 | 7.0 | {'RH': 6, 'KT': 2, 'GU': 1} |
| G023 | 0.0 | 2.0 | {'DL': 2} |
| G024 | 0.0 | 2.0 | {'HP': 1, 'SL': 1} |
| G025 | 1.0 | 2.0 | {'KT': 2, 'TW': 1} |
| G026 | 0.0 | 1.0 | {'CT': 1} |
| G027 | 0.0 | 1.0 | {'IV': 1} |
| G028 | 0.0 | 1.0 | {'OX': 1} |

Test substations per Paper A penetration bin (mean per seed): {'<=15%': 265.0, '15-35%': 145.0, '35-65%': 30.0, '>65%': 15.0}

Max feeder size in the grid (<= 120) and uncapped (best test station; median over seeds):

| p=0.05 | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=1.0 | uncapped p=0.05 | uncapped p=0.2 | uncapped p=0.5 | uncapped p=1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 120.0 | 120.0 | 120.0 | 80.0 | 40.0 | 20.0 | 510.0 | 127.0 | 51.0 | 25.0 |

### GB-EoH 2022/23

Fill: LCL 5093 households >= 90 % in 2012/13 (8-10 years earlier, London). HP types (HP_Installed) {'ASHP': 197, 'HT-ASHP': 150, 'GSHP': 23}; HP_Size_kW for 370, median 8.2 kW; oversizing HP_Size/MCS_SHLoad median 1.22 [IQR 1.07-1.39]; robust 15-min peak / HP_Size median 0.48.

HP households per station (mean over 20 split seeds; stations with < 3 HP in a split build no substation):

| station | test | train | postcode areas (top 3) |
|---|---|---|---|
| G000 | 25.0 | 76.0 | {'NE': 90, 'DH': 10, 'SR': 1} |
| G001 | 28.0 | 86.0 | {'EH': 96, 'KY': 15, 'FK': 3} |
| G002 | 10.0 | 30.0 | {'TD': 27, 'EH': 10, 'NE': 3} |
| G003 | 1.0 | 3.0 | {'ML': 4} |
| G004 | 4.0 | 11.0 | {'KY': 10, 'EH': 4, 'DD': 1} |
| G005 | 2.0 | 6.0 | {'EH': 4, 'TD': 4} |
| G006 | 2.0 | 8.0 | {'BN': 7, 'TN': 3} |
| G007 | 2.0 | 8.0 | {'BN': 8, 'RH': 2} |
| G008 | 1.0 | 3.0 | {'TN': 3, 'CT': 1} |
| G009 | 4.0 | 14.0 | {'GU': 16, 'RG': 2} |
| G010 | 2.0 | 6.0 | {'G': 8} |
| G011 | 0.0 | 1.0 | {'OX': 1} |
| G012 | 1.0 | 3.0 | {'PH': 3, 'FK': 1} |
| G013 | 2.0 | 6.0 | {'KT': 4, 'TN': 2, 'ME': 1} |
| G014 | 1.0 | 2.0 | {'TD': 3} |
| G015 | 1.0 | 2.0 | {'SO': 3} |
| G016 | 1.0 | 2.0 | {'PO': 2, 'GU': 1} |
| G017 | 1.0 | 2.0 | {'TW': 2, 'KT': 1} |
| G018 | 1.0 | 4.0 | {'RH': 4, 'GU': 1} |
| G019 | 0.0 | 2.0 | {'DL': 2} |
| G020 | 0.0 | 1.0 | {'TD': 1} |
| G021 | 0.0 | 1.0 | {'DA': 1} |
| G022 | 0.0 | 1.0 | {'DL': 1} |
| G023 | 0.0 | 1.0 | {'CT': 1} |
| G024 | 0.0 | 1.0 | {'NE': 1} |
| G025 | 0.0 | 1.0 | {'OX': 1} |

Test substations per Paper A penetration bin (mean per seed): {'<=15%': 190.0, '15-35%': 110.0, '35-65%': 30.0, '>65%': 15.0}

Max feeder size in the grid (<= 120) and uncapped (best test station; median over seeds):

| p=0.05 | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=1.0 | uncapped p=0.05 | uncapped p=0.2 | uncapped p=0.5 | uncapped p=1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 120.0 | 120.0 | 80.0 | 40.0 | 40.0 | 20.0 | 420.0 | 105.0 | 42.0 | 21.0 |

### GB-RHPP Nov13-Feb14

Fill: LCL 4796 households >= 90 % in the same window (concurrent).

HP households per station (mean over 20 split seeds; stations with < 3 HP in a split build no substation):

| station | test | train |
|---|---|---|
| GB | 28.0 | 86.0 |

Test substations per Paper A penetration bin (mean per seed): {'<=15%': 50.0, '15-35%': 35.0, '35-65%': 15.0, '>65%': 10.0}

Max feeder size in the grid (<= 120) and uncapped (best test station; median over seeds):

| p=0.05 | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=1.0 | uncapped p=0.05 | uncapped p=0.2 | uncapped p=0.5 | uncapped p=1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 120.0 | 120.0 | 80.0 | 40.0 | 40.0 | 20.0 | 420.0 | 105.0 | 42.0 | 21.0 |

### US-NEEA cal2023

Fill: NEEA homes without electric heating, >= 330 full days: 49.

HP households per station (mean over 20 split seeds; stations with < 3 HP in a split build no substation):

| station | test | train |
|---|---|---|
| ID | 2.0 | 5.0 |
| OR | 6.0 | 16.0 |
| WA | 7.0 | 21.0 |

Test substations per Paper A penetration bin (mean per seed): {'<=15%': 20.0, '15-35%': 20.0, '35-65%': 5.0, '>65%': 0.0}

Max feeder size in the grid (<= 120) and uncapped (best test station; median over seeds):

| p=0.05 | p=0.1 | p=0.2 | p=0.3 | p=0.5 | p=1.0 | uncapped p=0.05 | uncapped p=0.2 | uncapped p=0.5 | uncapped p=1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 0.0 | 12.0 | 15.0 | 10.0 | 5.0 |

## Fill temperature response (LCL, HadCET daily, Jul 2012 - Jun 2013)

B* Kaiser fill: s0 = 0.0055 kW/K per dwelling.

| LCL fill | n | P_base | s0 (kW/K) | T_h | r2 |
|---|---|---|---|---|---|
| all | 4329.0 | 0.337 | 0.0133 | 14.2 | 0.84 |
| gas, 0 heaters | 78.0 | 0.267 | 0.007 | 14.3 | 0.6 |
