Homes: 50 EoH ASHP homes (seed 0), season 2021/22; 348,403 valid 30-min bins. Source: `scripts/audit/hplib_check.py`. Rated power = 99.5th pct of 30-min heat output at A2/W35 (assumption).

### hplib generic group 1 (regulated air/water)

Overall (30 min / daily):

| n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) | level |
|---|---|---|---|---|---|
| 348403.0 | 29.0 | -19.6 | 100.0 | 24.6 | 30 min |
| 7073.0 | 21.7 | -19.7 | 100.0 | 13.8 | daily |

By outdoor temperature (daily):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-2, 2] | 552.0 | 23.6 | -22.5 | 11.4 | 13.6 |
| (2, 6] | 2974.0 | 21.9 | -20.8 | 49.9 | 12.1 |
| (6, 10] | 2949.0 | 20.5 | -17.1 | 33.8 | 15.5 |
| (10, 14] | 598.0 | 24.1 | -20.3 | 4.9 | 17.0 |

By outdoor temperature (30 min):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-20, -2] | 2956.0 | 24.2 | -15.7 | 1.3 | 21.3 |
| (-2, 2] | 44225.0 | 28.1 | -23.2 | 17.1 | 21.1 |
| (2, 6] | 125553.0 | 28.1 | -22.2 | 41.9 | 21.7 |
| (6, 10] | 125660.0 | 29.8 | -14.1 | 31.2 | 28.6 |
| (10, 14] | 45675.0 | 33.0 | -20.0 | 8.1 | 29.6 |
| (14, 40] | 4334.0 | 38.4 | -32.8 | 0.4 | 31.4 |

By regime (30 min):

| regime | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| DHW | 42634.0 | 33.3 | -15.7 | 21.3 | 32.5 |
| back-up active | 3894.0 | 32.5 | -16.0 | 1.2 | 28.0 |
| space heating | 181874.0 | 25.6 | -18.3 | 75.2 | 19.7 |
| standby (Q ~ 0) | 120001.0 | 99.6 | -99.6 | 2.3 | 193.4 |

Seasonal performance factor (SPF_H2-like, per home): measured median 2.98, predicted median 3.81; SPF bias median +27.5 % (10-90 %: +10.9 to +43.1 %). Bins where Q exceeded hplib's full-load output: 6.0 %.

### hplib generic group 4 (on-off air/water)

Overall (30 min / daily):

| n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) | level |
|---|---|---|---|---|---|
| 348403.0 | 22.2 | -17.4 | 100.0 | 19.0 | 30 min |
| 7073.0 | 18.8 | -17.5 | 100.0 | 11.6 | daily |

By outdoor temperature (daily):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-2, 2] | 552.0 | 19.2 | -17.6 | 11.4 | 12.1 |
| (2, 6] | 2974.0 | 18.7 | -17.5 | 49.9 | 10.7 |
| (6, 10] | 2949.0 | 18.8 | -17.4 | 33.8 | 12.4 |
| (10, 14] | 598.0 | 18.9 | -17.2 | 4.9 | 14.0 |

By outdoor temperature (30 min):

| T bin | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| (-20, -2] | 2956.0 | 22.2 | -13.2 | 1.3 | 19.9 |
| (-2, 2] | 44225.0 | 23.4 | -18.3 | 17.1 | 19.1 |
| (2, 6] | 125553.0 | 22.2 | -17.9 | 41.9 | 18.3 |
| (6, 10] | 125660.0 | 21.3 | -16.4 | 31.2 | 19.2 |
| (10, 14] | 45675.0 | 22.5 | -17.3 | 8.1 | 21.0 |
| (14, 40] | 4334.0 | 28.2 | -23.5 | 0.4 | 27.3 |

By regime (30 min):

| regime | n | WAPE % | bias % | share of energy % | WAPE after global rescale % (in-sample) |
|---|---|---|---|---|---|
| DHW | 42634.0 | 27.7 | -18.5 | 21.3 | 23.7 |
| back-up active | 3894.0 | 26.8 | -13.7 | 1.2 | 22.7 |
| space heating | 181874.0 | 18.2 | -14.6 | 75.2 | 14.7 |
| standby (Q ~ 0) | 120001.0 | 99.6 | -99.6 | 2.3 | 193.4 |

Seasonal performance factor (SPF_H2-like, per home): measured median 2.98, predicted median 3.68; SPF bias median +22.2 % (10-90 %: +7.8 to +36.6 %). Bins where Q exceeded hplib's full-load output: 0.5 %.
