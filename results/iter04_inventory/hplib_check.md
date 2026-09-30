Homes: 50 EoH ASHP homes (seed 0), season 2021/22; 349,812 valid 30-min bins. Types {'ASHP': 34, 'HT-ASHP': 16}. Source: `scripts/audit/hplib_check.py`. Rated power = HP_Size_kW at A7/W35 (assumption); 'proxy' = 99.5th pct of 30-min heat output at A2/W35.

### hplib generic group 1 (regulated air/water), sizing: nameplate

Overall (30 min / daily):

| n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) | level |
|---|---|---|---|---|---|
| 349812.0 | 29.7 | -25.8 | 100.0 | 21.1 | 30 min |
| 7072.0 | 26.8 | -25.9 | 100.0 | 13.3 | daily |

By outdoor temperature (daily):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-2, 2] | 553.0 | 25.2 | -23.6 | 11.7 | 13.9 |
| (2, 6] | 2960.0 | 26.2 | -25.4 | 49.8 | 12.2 |
| (6, 10] | 2973.0 | 27.6 | -26.8 | 33.8 | 14.2 |
| (10, 14] | 586.0 | 31.2 | -30.7 | 4.7 | 14.5 |

By outdoor temperature (30 min):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-20, -2] | 2904.0 | 25.4 | -17.4 | 1.4 | 21.8 |
| (-2, 2] | 43580.0 | 28.2 | -23.4 | 17.3 | 21.1 |
| (2, 6] | 126550.0 | 29.3 | -26.1 | 42.2 | 19.8 |
| (6, 10] | 127349.0 | 30.3 | -25.6 | 31.3 | 21.9 |
| (10, 14] | 45170.0 | 34.1 | -30.6 | 7.5 | 22.7 |
| (14, 40] | 4259.0 | 42.9 | -41.2 | 0.3 | 29.4 |

By regime (30 min):

| regime | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| DHW | 42526.0 | 32.7 | -23.9 | 21.5 | 27.1 |
| back-up active | 3811.0 | 35.5 | -22.9 | 1.2 | 27.7 |
| space heating | 180084.0 | 26.7 | -24.1 | 74.9 | 16.4 |
| standby (Q ~ 0) | 123391.0 | 99.4 | -99.4 | 2.3 | 192.8 |

By HP type (daily):

| type | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| ASHP | 4840.0 | 29.3 | -28.4 | 69.9 | 13.5 |
| HT-ASHP | 2232.0 | 20.9 | -20.1 | 30.1 | 11.8 |

Seasonal performance factor (SPF_H2-like, per home): measured median 2.86, predicted median 4.00; SPF bias median +37.2 % (10-90 %: +15.1 to +57.9 %). Bins where Q exceeded hplib's full-load output: 1.7 %.

### hplib generic group 4 (on-off air/water), sizing: nameplate

Overall (30 min / daily):

| n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) | level |
|---|---|---|---|---|---|
| 349812.0 | 24.0 | -12.8 | 100.0 | 22.6 | 30 min |
| 7072.0 | 17.9 | -12.9 | 100.0 | 14.6 | daily |

By outdoor temperature (daily):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-2, 2] | 553.0 | 18.3 | -8.2 | 11.7 | 17.1 |
| (2, 6] | 2960.0 | 17.3 | -12.0 | 49.8 | 14.3 |
| (6, 10] | 2973.0 | 18.2 | -15.2 | 33.8 | 14.2 |
| (10, 14] | 586.0 | 20.2 | -18.2 | 4.7 | 14.0 |

By outdoor temperature (30 min):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-20, -2] | 2904.0 | 27.4 | -2.8 | 1.4 | 27.8 |
| (-2, 2] | 43580.0 | 25.8 | -9.3 | 17.3 | 25.4 |
| (2, 6] | 126550.0 | 23.8 | -12.2 | 42.2 | 22.4 |
| (6, 10] | 127349.0 | 22.7 | -14.6 | 31.3 | 20.9 |
| (10, 14] | 45170.0 | 24.6 | -18.1 | 7.5 | 21.8 |
| (14, 40] | 4259.0 | 32.4 | -27.6 | 0.3 | 29.5 |

By regime (30 min):

| regime | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| DHW | 42526.0 | 28.5 | -15.2 | 21.5 | 26.4 |
| back-up active | 3811.0 | 30.7 | -15.5 | 1.2 | 25.9 |
| space heating | 180084.0 | 20.2 | -9.5 | 74.9 | 18.7 |
| standby (Q ~ 0) | 123391.0 | 99.4 | -99.3 | 2.3 | 192.8 |

By HP type (daily):

| type | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| ASHP | 4840.0 | 20.3 | -18.0 | 69.9 | 13.2 |
| HT-ASHP | 2232.0 | 12.3 | -1.3 | 30.1 | 12.3 |

Seasonal performance factor (SPF_H2-like, per home): measured median 2.86, predicted median 3.48; SPF bias median +16.9 % (10-90 %: -2.2 to +34.1 %). Bins where Q exceeded hplib's full-load output: 5.6 %.

### hplib generic group 1 (regulated air/water), sizing: proxy

Overall (30 min / daily):

| n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) | level |
|---|---|---|---|---|---|
| 349812.0 | 29.5 | -21.6 | 100.0 | 24.2 | 30 min |
| 7072.0 | 23.1 | -21.8 | 100.0 | 13.8 | daily |

By outdoor temperature (daily):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-2, 2] | 553.0 | 24.9 | -23.2 | 11.7 | 13.8 |
| (2, 6] | 2960.0 | 23.4 | -22.4 | 49.8 | 12.5 |
| (6, 10] | 2973.0 | 21.8 | -20.0 | 33.8 | 15.2 |
| (10, 14] | 586.0 | 25.7 | -24.6 | 4.7 | 15.4 |

By outdoor temperature (30 min):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-20, -2] | 2904.0 | 25.4 | -17.3 | 1.4 | 21.8 |
| (-2, 2] | 43580.0 | 28.2 | -23.4 | 17.3 | 21.2 |
| (2, 6] | 126550.0 | 28.7 | -23.5 | 42.2 | 21.6 |
| (6, 10] | 127349.0 | 30.4 | -17.4 | 31.3 | 28.2 |
| (10, 14] | 45170.0 | 33.6 | -24.7 | 7.5 | 28.0 |
| (14, 40] | 4259.0 | 41.9 | -38.3 | 0.3 | 31.7 |

By regime (30 min):

| regime | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| DHW | 42526.0 | 32.6 | -16.9 | 21.5 | 31.4 |
| back-up active | 3811.0 | 35.5 | -19.7 | 1.2 | 30.1 |
| space heating | 180084.0 | 26.4 | -20.6 | 74.9 | 19.3 |
| standby (Q ~ 0) | 123391.0 | 99.4 | -99.4 | 2.3 | 192.8 |

By HP type (daily):

| type | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| ASHP | 4840.0 | 25.2 | -23.7 | 69.9 | 14.3 |
| HT-ASHP | 2232.0 | 18.4 | -17.3 | 30.1 | 12.0 |

Seasonal performance factor (SPF_H2-like, per home): measured median 2.86, predicted median 3.78; SPF bias median +28.6 % (10-90 %: +10.5 to +44.6 %). Bins where Q exceeded hplib's full-load output: 5.5 %.
