# 05a-ii Task A - D4 diagnostics

Source: `scripts/paperb/d4_diagnostics.py` (definitions and the pre-registered rule are in its docstring), pool GB-EoH `2122r2`, 2399 train fillers (seed 0), 50 draws per size, London Heathrow temperature. Pooled LCL T_h (definition b) = 17.58 degC.

## Item 1-3: real year-to-year variation Y against the D4 error E (median |relative error| of s)

| def, n | Y (real year-to-year) | E (D4, winter donors) | Y / E | E (D4, +-30 d band) |
|---|---|---|---|---|
| a, n=10 | 0.781 | 0.937 | 0.833 | 0.642 |
| a, n=40 | 0.626 | 0.501 | 1.25 | 0.351 |
| a, n=120 | 0.518 | 0.379 | 1.37 | 0.224 |
| b, n=10 | 0.784 | 0.942 | 0.832 | 0.571 |
| b, n=40 | 0.627 | 0.495 | 1.27 | 0.336 |
| b, n=120 | 0.495 | 0.379 | 1.31 | 0.2 |
| c, n=10 | 1.04 | 0.962 | 1.08 | 0.702 |
| c, n=40 | 0.728 | 0.594 | 1.22 | 0.344 |
| c, n=120 | 0.647 | 0.406 | 1.59 | 0.208 |

Definitions: (a) hockey stick, latent T_h; (b) hockey stick, T_h fixed (pooled LCL); (c) OLS slope, days below 12 degC.

**Verdict by the pre-registered rule: intrinsic filler variability.** (a): Y >= 0.5 E at n = [10, 40, 120]; E under (b) = {10: 0.942, 40: 0.495, 120: 0.379}, under (c) = {10: 0.962, 40: 0.594, 120: 0.406}.

## Day matches that change with the temperature source

| winter | days | share of matches that change with HadCET (rule, random among 3) | share whose nearest-T day changes (k = 1) | share |dT| > 1 K (Heathrow) |
|---|---|---|---|---|
| 2012/13 | 120 | 0.9 | 0.858 | 0.075 |
| 2013/14 | 119 | 0.899 | 0.874 | 0 |

(HadCET in place of Heathrow, same seed and candidate set; the share includes the random choice among the 3 closest.)

## Item 4: capacity-equivalent error, % of HP_Peak (* = above 5 %, fusion-limited)

m_h = 0.0251 (median over 10 split seeds, range 0.0246-0.0252); median household HP_Peak = 3.42 kW; |d s_h| = median absolute error of definition (a) at that aggregate size.

Winter donors (D4 as defined):

| N | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|---|
| 10 | 74.4 | 37.2 | 18.6 | 12.4 | 7.4 | 4.7 | 3.7 |
| 40 | 61.4 | 30.7 | 15.3 | 10.2 | 6.1 | 3.8 | 3.1 |
| 120 | 48.5 | 24.2 | 12.1 | 8.1 | 4.8 | 3 | 2.4 |

Donors from outside +-30 d of the target day:

| N | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|---|
| 10 | 68.2 | 34.1 | 17 | 11.4 | 6.8 | 4.3 | 3.4 |
| 40 | 40.4 | 20.2 | 10.1 | 6.7 | 4 | 2.5 | 2 |
| 120 | 25.5 | 12.8 | 6.4 | 4.3 | 2.6 | 1.6 | 1.3 |

Fusion-limited penetrations (any N above 5 %): winter donors [0.05, 0.1, 0.2, 0.3, 0.5], band donors [0.05, 0.1, 0.2, 0.3, 0.5]. Figure: `figures/d4_capacity_equiv.png`.

