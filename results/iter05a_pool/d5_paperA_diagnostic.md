# 05a-ii: own non-HP load of the B* HP homes and the D5 shift of `paperA_corr` / `paperA_sh_mh`

Source: `scripts/paperb/d5_own_load_diagnostic.py` (method in its docstring), D5 outputs in `overnight/d5_{real,swap}/`. Slopes in kW/K per dwelling.

```
s0 fill (real) 0.00540  s0 own-load per HP home 0.01807 (x3.3)  s0 swap filler 0.00527  m_h 0.01821
own-load slope per HP home by seed: min 0.0137 max 0.0208
paperA_sh_mh n 1350 corr(actual diff, expected own-load diff) 0.500 median actual 1.83 kW  expected 2.19 kW  ratio 0.83 expected shift as % of mean y: 10.4
paperA_corr n 1334 corr(actual diff, expected own-load diff) 0.472 median actual 1.65 kW  expected 1.99 kW  ratio 0.80 expected shift as % of mean y: 9.6
```

Reading: the own non-HP load of a B* HP home is about 3x as temperature-sensitive as a filler dwelling, and `paperA_corr` subtracts only N x s0 of the fillers (`paperA_sh_mh` subtracts nothing), so in the real arm each HP home leaves about 0.7 kW of extra apparent heat-pump capacity in the estimate (about 10 % of the mean HP_Peak). The swap removes it by giving every dwelling a filler, which is also how a GB-EoH substation is built. The expected shift explains the observed one (ratio actual / expected about 0.8). What the own load contains (electric water heating, direct heaters, back-up rods booked outside the HP submeter) was not examined; that is a hypothesis.
