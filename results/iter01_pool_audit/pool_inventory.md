# Iteration 01 - pool inventory

Source: `scripts/audit/pool_inventory.py` (config `iter01_pool_audit`). Distinct households with >= 90% coverage of the required channel(s) in each window. Seasons are Nov-Mar (UTC); `calYYYY` are calendar years (the legacy pool is cal2023 with an 80 % rule).

## Totals over stations

| source | requirement | 2019/20 | 2020/21 | 2021/22 | 2022/23 | 2023/24 | 2024/25 | cal2019 | cal2020 | cal2021 | cal2022 | cal2023 | cal2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HEAPO 15-min | H15(a) HP submeter + other | 1 | 3 | 14 | 46 | 0 | 0 | 0 | 1 | 7 | 17 | 47 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | 7 | 116 | 262 | 838 | 0 | 0 | 0 | 32 | 166 | 303 | 1027 | 0 |
| HEAPO 15-min | H15(b) total | 8 | 119 | 276 | 884 | 0 | 0 | 0 | 33 | 173 | 320 | 1074 | 0 |
| HEAPO daily | Hd(a) HP submeter daily | 5 | 5 | 10 | 22 | 0 | 0 | 5 | 5 | 6 | 11 | 0 | 0 |
| HEAPO daily | Hd(b) total daily | 232 | 150 | 360 | 746 | 820 | 0 | 130 | 203 | 176 | 427 | 774 | 0 |
| Kaiser | K(a'') dwelling with 1_hp inside its meter | 0 | 0 | 0 | 0 | 181 | 0 | 0 | 0 | 0 | 0 | 199 | 187 |
| Kaiser | K(a') HP meter, no dwelling meter | 0 | 0 | 0 | 0 | 84 | 0 | 0 | 0 | 0 | 0 | 83 | 81 |
| Kaiser | K(a) dwelling + paired HP meter | 0 | 0 | 0 | 0 | 22 | 0 | 0 | 0 | 0 | 0 | 24 | 24 |
| Kaiser | K(b) clean dwelling (no TCL flag) | 0 | 0 | 0 | 0 | 1256 | 0 | 0 | 0 | 0 | 0 | 1306 | 1000 |
| Kaiser | K(c) dwelling flag 1_direct_heating | 0 | 0 | 0 | 0 | 23 | 0 | 0 | 0 | 0 | 0 | 27 | 18 |
| Kaiser | K(c) dwelling flag 1_ewh | 0 | 0 | 0 | 0 | 451 | 0 | 0 | 0 | 0 | 0 | 464 | 444 |
| Kaiser | K(c) dwelling flag 1_hp-add | 0 | 0 | 0 | 0 | 56 | 0 | 0 | 0 | 0 | 0 | 62 | 57 |
| Kaiser | K(c) dwelling flag 1_hp-wh | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 3 | 2 |
| Kaiser | K(c) dwelling flag 1_storage_heating | 0 | 0 | 0 | 0 | 53 | 0 | 0 | 0 | 0 | 0 | 53 | 52 |
| Kaiser | K(d) any meter 2_hp_control | 0 | 0 | 0 | 0 | 47 | 0 | 0 | 0 | 0 | 0 | 50 | 48 |
| Kaiser | K(d) any meter 2_wh_control | 0 | 0 | 0 | 0 | 55 | 0 | 0 | 0 | 0 | 0 | 57 | 56 |
| WPuQ | W HP + household | 30 | 0 | 0 | 0 | 0 | 0 | 32 | 27 | 0 | 0 | 0 | 0 |

## Per weather station

| source | requirement | station | 2019/20 | 2020/21 | 2021/22 | 2022/23 | 2023/24 | 2024/25 | cal2019 | cal2020 | cal2021 | cal2022 | cal2023 | cal2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HEAPO 15-min | H15(a) HP submeter + other | 8jB | 0 | 0 | 5 | 23 | 0 | 0 | 0 | 0 | 1 | 4 | 23 | 0 |
| HEAPO 15-min | H15(a) HP submeter + other | HbsbG | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| HEAPO 15-min | H15(a) HP submeter + other | Hg | 1 | 3 | 6 | 14 | 0 | 0 | 0 | 1 | 4 | 7 | 16 | 0 |
| HEAPO 15-min | H15(a) HP submeter + other | MqO | 0 | 0 | 2 | 6 | 0 | 0 | 0 | 0 | 1 | 5 | 6 | 0 |
| HEAPO 15-min | H15(a) HP submeter + other | z6I | 0 | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | 8jB | 1 | 25 | 95 | 462 | 0 | 0 | 0 | 6 | 48 | 117 | 514 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | HbsbG | 0 | 7 | 10 | 24 | 0 | 0 | 0 | 0 | 7 | 11 | 34 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | Hg | 6 | 51 | 92 | 221 | 0 | 0 | 0 | 25 | 59 | 106 | 317 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | MqO | 0 | 1 | 15 | 19 | 0 | 0 | 0 | 0 | 10 | 11 | 20 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | ceOxS | 0 | 3 | 5 | 23 | 0 | 0 | 0 | 0 | 3 | 6 | 28 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | sV3mR | 0 | 8 | 12 | 25 | 0 | 0 | 0 | 0 | 11 | 14 | 28 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | wDD | 0 | 12 | 17 | 35 | 0 | 0 | 0 | 0 | 14 | 20 | 45 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | z6I | 0 | 9 | 16 | 29 | 0 | 0 | 0 | 1 | 14 | 18 | 41 | 0 |
| HEAPO 15-min | H15(b) total | 8jB | 1 | 25 | 100 | 485 | 0 | 0 | 0 | 6 | 49 | 121 | 537 | 0 |
| HEAPO 15-min | H15(b) total | HbsbG | 0 | 7 | 10 | 25 | 0 | 0 | 0 | 0 | 7 | 11 | 35 | 0 |
| HEAPO 15-min | H15(b) total | Hg | 7 | 54 | 98 | 235 | 0 | 0 | 0 | 26 | 63 | 113 | 333 | 0 |
| HEAPO 15-min | H15(b) total | MqO | 0 | 1 | 17 | 25 | 0 | 0 | 0 | 0 | 11 | 16 | 26 | 0 |
| HEAPO 15-min | H15(b) total | ceOxS | 0 | 3 | 5 | 23 | 0 | 0 | 0 | 0 | 3 | 6 | 28 | 0 |
| HEAPO 15-min | H15(b) total | sV3mR | 0 | 8 | 12 | 25 | 0 | 0 | 0 | 0 | 11 | 14 | 28 | 0 |
| HEAPO 15-min | H15(b) total | wDD | 0 | 12 | 17 | 35 | 0 | 0 | 0 | 0 | 14 | 20 | 45 | 0 |
| HEAPO 15-min | H15(b) total | z6I | 0 | 9 | 17 | 31 | 0 | 0 | 0 | 1 | 15 | 19 | 42 | 0 |
| HEAPO daily | Hd(a) HP submeter daily | 8jB | 3 | 4 | 7 | 15 | 0 | 0 | 0 | 3 | 5 | 8 | 0 | 0 |
| HEAPO daily | Hd(a) HP submeter daily | HbsbG | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| HEAPO daily | Hd(a) HP submeter daily | Hg | 2 | 1 | 3 | 6 | 0 | 0 | 5 | 2 | 1 | 3 | 0 | 0 |
| HEAPO daily | Hd(b) total daily | 8jB | 105 | 97 | 216 | 387 | 381 | 0 | 56 | 95 | 125 | 256 | 374 | 0 |
| HEAPO daily | Hd(b) total daily | HbsbG | 5 | 2 | 7 | 28 | 31 | 0 | 3 | 4 | 3 | 11 | 27 | 0 |
| HEAPO daily | Hd(b) total daily | Hg | 44 | 24 | 106 | 250 | 306 | 0 | 28 | 39 | 27 | 123 | 289 | 0 |
| HEAPO daily | Hd(b) total daily | MqO | 7 | 9 | 8 | 8 | 7 | 0 | 3 | 6 | 8 | 8 | 7 | 0 |
| HEAPO daily | Hd(b) total daily | ceOxS | 6 | 4 | 2 | 23 | 27 | 0 | 6 | 7 | 2 | 3 | 24 | 0 |
| HEAPO daily | Hd(b) total daily | sV3mR | 14 | 2 | 8 | 14 | 17 | 0 | 5 | 11 | 2 | 10 | 15 | 0 |
| HEAPO daily | Hd(b) total daily | wDD | 26 | 5 | 5 | 12 | 17 | 0 | 17 | 18 | 3 | 5 | 13 | 0 |
| HEAPO daily | Hd(b) total daily | z6I | 25 | 7 | 8 | 24 | 34 | 0 | 12 | 23 | 6 | 11 | 25 | 0 |
| Kaiser | K(a'') dwelling with 1_hp inside its meter | KLO | 0 | 0 | 0 | 0 | 181 | 0 | 0 | 0 | 0 | 0 | 199 | 187 |
| Kaiser | K(a') HP meter, no dwelling meter | KLO | 0 | 0 | 0 | 0 | 84 | 0 | 0 | 0 | 0 | 0 | 83 | 81 |
| Kaiser | K(a) dwelling + paired HP meter | KLO | 0 | 0 | 0 | 0 | 22 | 0 | 0 | 0 | 0 | 0 | 24 | 24 |
| Kaiser | K(b) clean dwelling (no TCL flag) | KLO | 0 | 0 | 0 | 0 | 1256 | 0 | 0 | 0 | 0 | 0 | 1306 | 1000 |
| Kaiser | K(c) dwelling flag 1_direct_heating | KLO | 0 | 0 | 0 | 0 | 23 | 0 | 0 | 0 | 0 | 0 | 27 | 18 |
| Kaiser | K(c) dwelling flag 1_ewh | KLO | 0 | 0 | 0 | 0 | 451 | 0 | 0 | 0 | 0 | 0 | 464 | 444 |
| Kaiser | K(c) dwelling flag 1_hp-add | KLO | 0 | 0 | 0 | 0 | 56 | 0 | 0 | 0 | 0 | 0 | 62 | 57 |
| Kaiser | K(c) dwelling flag 1_hp-wh | KLO | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 3 | 2 |
| Kaiser | K(c) dwelling flag 1_storage_heating | KLO | 0 | 0 | 0 | 0 | 53 | 0 | 0 | 0 | 0 | 0 | 53 | 52 |
| Kaiser | K(d) any meter 2_hp_control | KLO | 0 | 0 | 0 | 0 | 47 | 0 | 0 | 0 | 0 | 0 | 50 | 48 |
| Kaiser | K(d) any meter 2_wh_control | KLO | 0 | 0 | 0 | 0 | 55 | 0 | 0 | 0 | 0 | 0 | 57 | 56 |
| WPuQ | W HP + household | WPUQ | 30 | 0 | 0 | 0 | 0 | 0 | 32 | 27 | 0 | 0 | 0 | 0 |

## Nameplate x data availability (HEAPO protocols)

| nameplate | data | 2019/20 | 2020/21 | 2021/22 | 2022/23 | 2023/24 | 2024/25 | cal2019 | cal2020 | cal2021 | cal2022 | cal2023 | cal2024 | any |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HeatingCapacity | 15-min HP submeter | 1 | 1 | 6 | 10 | 0 | 0 | 0 | 0 | 2 | 7 | 8 | 0 | 0 |
| HeatingCapacity | 15-min total | 7 | 46 | 89 | 132 | 0 | 0 | 0 | 12 | 59 | 97 | 136 | 0 | 0 |
| HeatingCapacity | any (protocol only) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 202 |
| HeatingCapacity | daily HP submeter | 1 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| HeatingCapacity | daily total | 29 | 13 | 26 | 48 | 59 | 0 | 24 | 19 | 11 | 34 | 48 | 0 | 0 |
| Normpoint_ElectricPower | 15-min HP submeter | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| Normpoint_ElectricPower | 15-min total | 0 | 6 | 16 | 33 | 0 | 0 | 0 | 1 | 6 | 20 | 35 | 0 | 0 |
| Normpoint_ElectricPower | any (protocol only) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 67 |
| Normpoint_ElectricPower | daily total | 10 | 4 | 16 | 29 | 36 | 0 | 7 | 8 | 6 | 22 | 31 | 0 | 0 |

## Station compatibility (HEAPO hourly vs MeteoSwiss KLO, identical = max |diff| < 0.05 C)

| station | n_hours_overlap | max_abs_diff_C | share_identical | identical_to_KLO |
|---|---|---|---|---|
| 8jB | 36504 | 0.0 | 1.0 | True |
| HbsbG | 36037 | 13.7 | 0.0336 | False |
| Hg | 36504 | 6.5 | 0.1061 | False |
| MqO | 36504 | 12.3 | 0.0057 | False |
| ceOxS | 36437 | 7.5 | 0.0544 | False |
| sV3mR | 36404 | 7.5 | 0.0577 | False |
| wDD | 36504 | 9.3 | 0.031 | False |
| z6I | 36504 | 9.9 | 0.032 | False |

## Multi-window households (count of households usable in >= k windows)

| source | window kind | >=1 | >=2 | >=3 | >=4 |
|---|---|---|---|---|---|
| HEAPO 15-min HP submeter + other | heating seasons | 48 | 13 | 3 | 0 |
| HEAPO 15-min HP submeter + other | calendar years | 48 | 16 | 7 | 1 |
| HEAPO daily HP submeter | heating seasons | 25 | 10 | 5 | 2 |
| HEAPO daily HP submeter | calendar years | 17 | 7 | 2 | 1 |
| HEAPO daily total | heating seasons | 1045 | 744 | 346 | 123 |
| HEAPO daily total | calendar years | 954 | 490 | 181 | 63 |
| Kaiser meter (any) | heating seasons | 2166 | 0 | 0 | 0 |
| Kaiser meter (any) | calendar years | 2295 | 1821 | 0 | 0 |
| WPuQ HP + household | heating seasons | 30 | 0 | 0 | 0 |
| WPuQ HP + household | calendar years | 34 | 25 | 0 | 0 |
