# Iteration 01 - pool inventory

Source: `scripts/audit/pool_inventory.py` (config `iter01_pool_audit_quick`). Distinct households with >= 90% coverage of the required channel(s) in each window. Seasons are Nov-Mar (UTC); `calYYYY` are calendar years (the legacy pool is cal2023 with an 80 % rule).

## Totals over stations

| source | requirement | 2019/20 | 2020/21 | 2021/22 | 2022/23 | 2023/24 | 2024/25 | cal2019 | cal2020 | cal2021 | cal2022 | cal2023 | cal2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HEAPO 15-min | H15(a) HP submeter + other | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | 0 | 3 | 4 | 16 | 0 | 0 | 0 | 1 | 3 | 5 | 16 | 0 |
| HEAPO 15-min | H15(b) total | 0 | 3 | 5 | 17 | 0 | 0 | 0 | 1 | 4 | 6 | 17 | 0 |
| HEAPO daily | Hd(b) total daily | 3 | 1 | 8 | 17 | 16 | 0 | 3 | 3 | 3 | 10 | 16 | 0 |
| Kaiser | K(a'') dwelling with 1_hp inside its meter | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 5 | 5 |
| Kaiser | K(a') HP meter, no dwelling meter | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Kaiser | K(b) clean dwelling (no TCL flag) | 0 | 0 | 0 | 0 | 17 | 0 | 0 | 0 | 0 | 0 | 17 | 14 |
| Kaiser | K(c) dwelling flag 1_ewh | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 6 | 6 |
| Kaiser | K(c) dwelling flag 1_hp-add | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| Kaiser | K(d) any meter 2_hp_control | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Kaiser | K(d) any meter 2_wh_control | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| WPuQ | W HP + household | 30 | 0 | 0 | 0 | 0 | 0 | 32 | 27 | 0 | 0 | 0 | 0 |

## Per weather station

| source | requirement | station | 2019/20 | 2020/21 | 2021/22 | 2022/23 | 2023/24 | 2024/25 | cal2019 | cal2020 | cal2021 | cal2022 | cal2023 | cal2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HEAPO 15-min | H15(a) HP submeter + other | Hg | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | 8jB | 0 | 2 | 3 | 9 | 0 | 0 | 0 | 1 | 2 | 4 | 9 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | HbsbG | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | Hg | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | ceOxS | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | wDD | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| HEAPO 15-min | H15(b') total, no HP submeter | z6I | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| HEAPO 15-min | H15(b) total | 8jB | 0 | 2 | 3 | 9 | 0 | 0 | 0 | 1 | 2 | 4 | 9 | 0 |
| HEAPO 15-min | H15(b) total | HbsbG | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| HEAPO 15-min | H15(b) total | Hg | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 1 | 2 | 2 | 0 |
| HEAPO 15-min | H15(b) total | ceOxS | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| HEAPO 15-min | H15(b) total | wDD | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| HEAPO 15-min | H15(b) total | z6I | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| HEAPO daily | Hd(b) total daily | 8jB | 2 | 1 | 4 | 6 | 6 | 0 | 2 | 2 | 3 | 5 | 6 | 0 |
| HEAPO daily | Hd(b) total daily | HbsbG | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| HEAPO daily | Hd(b) total daily | Hg | 0 | 0 | 4 | 4 | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 |
| HEAPO daily | Hd(b) total daily | ceOxS | 0 | 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| HEAPO daily | Hd(b) total daily | wDD | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| HEAPO daily | Hd(b) total daily | z6I | 0 | 0 | 0 | 3 | 2 | 0 | 0 | 0 | 0 | 1 | 2 | 0 |
| Kaiser | K(a'') dwelling with 1_hp inside its meter | KLO | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 5 | 5 |
| Kaiser | K(a') HP meter, no dwelling meter | KLO | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Kaiser | K(b) clean dwelling (no TCL flag) | KLO | 0 | 0 | 0 | 0 | 17 | 0 | 0 | 0 | 0 | 0 | 17 | 14 |
| Kaiser | K(c) dwelling flag 1_ewh | KLO | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 6 | 6 |
| Kaiser | K(c) dwelling flag 1_hp-add | KLO | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| Kaiser | K(d) any meter 2_hp_control | KLO | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Kaiser | K(d) any meter 2_wh_control | KLO | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| WPuQ | W HP + household | WPUQ | 30 | 0 | 0 | 0 | 0 | 0 | 32 | 27 | 0 | 0 | 0 | 0 |

## Nameplate x data availability (HEAPO protocols)

| nameplate | data | 2019/20 | 2020/21 | 2021/22 | 2022/23 | 2023/24 | 2024/25 | cal2019 | cal2020 | cal2021 | cal2022 | cal2023 | cal2024 | any |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HeatingCapacity | 15-min total | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| HeatingCapacity | any (protocol only) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 202 |
| HeatingCapacity | daily total | 0 | 0 | 1 | 3 | 2 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 |
| Normpoint_ElectricPower | 15-min total | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| Normpoint_ElectricPower | any (protocol only) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 67 |
| Normpoint_ElectricPower | daily total | 0 | 0 | 1 | 2 | 2 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 |

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
| HEAPO 15-min HP submeter + other | heating seasons | 1 | 1 | 0 | 0 |
| HEAPO 15-min HP submeter + other | calendar years | 1 | 1 | 1 | 0 |
| HEAPO daily HP submeter | heating seasons | 0 | 0 | 0 | 0 |
| HEAPO daily HP submeter | calendar years | 0 | 0 | 0 | 0 |
| HEAPO daily total | heating seasons | 19 | 16 | 8 | 1 |
| HEAPO daily total | calendar years | 18 | 12 | 3 | 1 |
| Kaiser meter (any) | heating seasons | 25 | 0 | 0 | 0 |
| Kaiser meter (any) | calendar years | 25 | 22 | 0 | 0 |
| WPuQ HP + household | heating seasons | 30 | 0 | 0 | 0 |
| WPuQ HP + household | calendar years | 34 | 25 | 0 | 0 |
