# 05a-ii R8 - zero runs under the 05a-i rule

Source: `scripts/paperb/iter05a_report.py --part zeroruns`. A run = exact zeros of the half-hourly heating-system electricity for >= 6 h, starting on a day with mean T < 12 degC, while heat output or the circulation pump is active at any time in the run (05a-i rule). Classification: **meter dropout** if the heat meter exceeds 0.1 kW during the run, or heat (> 1 kW) is delivered with electricity < 0.02 kW within 12 h of it (heat cannot be delivered without electricity), else **real switch-off** (no heat output around it; the pump draws standby power only).

| window | cls | runs | bins | homes |
|---|---|---|---|---|
| 2021/22 | meter dropout | 4 | 262 | 3 |
| 2021/22 | real switch-off | 5 | 510 | 3 |
| 2022/23 | meter dropout | 122 | 2037 | 1 |
| 2022/23 | real switch-off | 2 | 93 | 2 |

Per home:

| index | window | home | cls | runs | bins |
|---|---|---|---|---|---|
| 7 | 2022/23 | EOH0836 | meter dropout | 122 | 2037 |
| 2 | 2021/22 | EOH1557 | real switch-off | 2 | 314 |
| 1 | 2021/22 | EOH1502 | meter dropout | 1 | 218 |
| 4 | 2021/22 | EOH2339 | real switch-off | 2 | 176 |
| 8 | 2022/23 | EOH1557 | real switch-off | 1 | 47 |
| 6 | 2022/23 | EOH0159 | real switch-off | 1 | 46 |
| 3 | 2021/22 | EOH1607 | meter dropout | 2 | 31 |
| 5 | 2021/22 | EOH2612 | real switch-off | 1 | 20 |
| 0 | 2021/22 | EOH0575 | meter dropout | 1 | 13 |

Figure `figures/zero_runs_2223.png`: 7 runs of 2022/23 (5 random, seed 0, plus the runs of the other homes). Rule adopted in `gb_eoh._zero_runs`: a zero run is missing only if the heat meter exceeds 0.1 kW somewhere in it; runs without heat output are kept as real switch-offs.

