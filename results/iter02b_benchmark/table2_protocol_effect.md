Protocol effect: XGBoost (size_peak), best physics baseline and peak-only baseline. v1 columns: median [5%-90%] over split seeds; the legacy column is ONE split (seed 42, unseeded hyperopt, stacked substations up to 120 dwellings, legacy min/max physics). Legacy -> A-v1 = stacking/leakage effect (plus the much smaller v1 test grid); A-v1 -> B*-v1 = pool effect. Best baseline = highest median R2.

| method | metric | legacy CSV (legacy protocol, pool A, split seed 42) | A under v1 (57 HH, shared fill) | B* under v1 | B under v1 | B* under v1, A's test cells only (size 10, p <= 0.3) |
|---|---|---|---|---|---|---|
| XGBoost [size_peak] | R2 | 0.934 | 0.029 [-2.714–0.503] | 0.858 [0.655–0.896] | 0.491 [-0.158–0.662] | 0.226 [-1.827–0.489] |
| XGBoost [size_peak] | MAPE % | 17.89 | 56.57 [38.33–169.36] | 47.79 [38.13–58.52] | 59.64 [45.48–76.91] | 70.27 [44.73–97.71] |
| XGBoost [size_peak] | RMSE kW | 48.10 | 5.32 [3.66–8.93] | 10.02 [7.91–14.59] | 11.17 [8.98–14.61] | 5.69 [4.54–7.82] |
| best physics baseline | R2 | 0.932 (legacy min/max slope+base) | 0.550 [-0.028–0.699] (physics: calibrated-delta) | 0.896 [0.736–0.944] (physics: slope-base) | 0.439 [-0.358–0.730] (physics: slope-base) | 0.442 [-0.287–0.675] |
| best physics baseline | MAPE % | 29.25 | 37.92 [30.18–78.17] | 36.38 [27.29–49.01] | 54.09 [38.33–62.94] | 44.67 [29.67–64.67] |
| best physics baseline | RMSE kW | n/a | 3.94 [2.71–4.64] | 8.09 [6.26–12.80] | 11.71 [7.64–15.08] | 4.48 [3.33–5.73] |
| peak-only baseline | R2 | 0.891 | -0.075 [-3.495–0.212] (anchor-only Linear [peak]) | 0.542 [0.346–0.696] (anchor-only Linear [peak]) | -0.769 [-1.631–-0.077] (anchor-only Linear [peak]) | 0.135 [-0.269–0.411] |
| peak-only baseline | MAPE % | n/a | 104.84 [56.36–140.54] | 65.20 [54.37–80.02] | 78.32 [61.30–92.54] | 59.17 [48.41–69.00] |
| peak-only baseline | RMSE kW | n/a | 5.93 [4.65–8.49] | 17.08 [15.98–18.37] | 21.37 [17.05–24.04] | 5.55 [4.31–6.65] |
| seeds / test HP households / test substations (median) |  | 1 / 28 / 1080 | 10 / 11 / 40 | 20 / 20 / 130 | 10 / 12 / 75 | 20 / – / 40 |
