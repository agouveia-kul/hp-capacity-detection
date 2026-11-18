# Iteration 07 report

Headline label HL (c_src x prediction); nMAE (%) median [5–90 %] over seeds; gap = transfer - in-pool (pp). Secondary rows (domain adaptation, label-free) are marked (DA) and are outside the rules.

**T1 (H\* vs D\*): not confirmed.** T2 (H\* vs L0ref) per direction: CH->GB: better, GB->CH: better — beats physics under transfer.

Multiplicity: primary 4 comparisons (T1 and T2 x 2 directions); T3 3 steps x 3 families x 2 directions + 2 (06 hybrid vs D*). No correction is applied; verdicts are counts and medians over 10 paired seeds.

## Table 1, CH->GB (overall)

| row | nMAE | gap | in-pool | WAPE | bias | max y (kW) | size_peak seeds | invalid ŝ | note |
|---|---|---|---|---|---|---|---|---|---|
| slope_base | 18.2 [15.6–20.6] | 12.7 [10.7–14.7] | 5.5 [4.9–6.6] | 88.5 [76.2–98.5] | 18.1 [15.6–20.5] | 72 [69–79] | 0 | – |  |
| calibrated_delta | 9.4 [8.4–10.1] | -1.4 [-1.8–-0.9] | 10.6 [9.5–11.6] | 44.6 [42.1–49.0] | 2.0 [0.9–4.3] | 72 [69–79] | 0 | – |  |
| hdh | 14.9 [12.9–16.7] | 4.6 [3.2–5.8] | 10.3 [9.2–11.0] | 71.6 [62.8–81.4] | 13.7 [11.6–16.0] | 72 [69–79] | 0 | – |  |
| paperA_cal | 16.9 [13.8–18.4] | 8.6 [6.2–9.9] | 8.1 [7.5–8.5] | 80.0 [68.8–91.1] | 16.4 [13.5–18.2] | 72 [69–79] | 0 | 0 [0–0] |  |
| paperA_corr | 21.2 [18.5–24.4] | 15.5 [13.5–18.7] | 5.6 [4.8–6.1] | 101.6 [90.1–116.4] | 21.1 [18.4–24.3] | 72 [69–79] | 0 | 0 [0–0] |  |
| paperA_corr_cal | 20.0 [17.0–23.4] | 13.8 [11.4–16.5] | 5.8 [5.4–6.9] | 95.1 [83.5–115.3] | 19.9 [17.0–23.4] | 72 [69–79] | 0 | 0 [0–0] |  |
| paperA_l4a | 10.2 [8.6–11.7] | 4.4 [3.5–5.5] | 5.6 [5.0–6.5] | 48.8 [42.1–58.3] | 8.7 [7.0–11.0] | 72 [69–79] | 0 | 0 [0–0] |  |
| paperA_sh_mh | 32.5 [28.8–36.8] | 13.9 [11.2–16.7] | 18.2 [17.1–20.2] | 157.2 [142.6–175.5] | 32.5 [28.8–36.8] | 72 [69–79] | 0 | 0 [0–0] |  |
| slope_only | 17.9 [15.4–20.5] | 8.4 [6.4–10.4] | 9.5 [8.6–10.2] | 85.6 [76.5–98.0] | 17.6 [15.1–20.2] | 72 [69–79] | 0 | – |  |
| L1 linear | 9.8 [7.8–10.4] | 4.3 [2.6–4.8] | 5.3 [4.9–6.1] | 48.1 [37.0–51.3] | 0.2 [-3.1–3.5] | 72 [69–79] | 10 | 0 [0–0] |  |
| L1 tabpfn | 8.8 [8.0–9.8] | 5.0 [4.2–6.2] | 3.7 [3.3–4.2] | 42.6 [39.5–45.5] | -5.7 [-9.3–-4.2] | 72 [69–79] | 10 | 0 [0–0] |  |
| L1 cnn | 10.3 [9.4–12.3] | 7.0 [5.7–8.3] | 3.7 [3.0–4.2] | 50.6 [44.3–59.4] | 4.2 [0.6–9.8] | 72 [69–79] | 3 | 0 [0–0] |  |
| L2 linear | 10.1 [8.0–16.3] | 5.3 [3.2–10.3] | 5.0 [4.4–5.7] | 49.2 [39.3–76.7] | 4.5 [0.3–14.0] | 72 [69–79] | 8 | 0 [0–0] |  |
| L2 tabpfn | 10.9 [6.3–12.5] | 7.3 [3.1–8.9] | 3.5 [3.0–3.8] | 51.9 [29.6–62.5] | 8.6 [-2.5–10.6] | 72 [69–79] | 3 | 0 [0–0] |  |
| L2 cnn | 9.7 [8.1–10.9] | 6.2 [4.9–7.5] | 3.4 [3.0–3.8] | 48.6 [39.5–51.6] | 6.9 [3.5–8.7] | 72 [69–79] | 4 | 0 [0–0] |  |
| L3 linear | 17.1 [11.9–36.3] | 13.0 [7.6–31.8] | 4.4 [3.9–4.7] | 83.4 [58.5–171.6] | 15.5 [6.8–36.3] | 72 [69–79] | 3 | 0 [0–0] |  |
| L3 tabpfn | 13.1 [8.5–14.7] | 9.8 [5.2–10.9] | 3.5 [3.1–3.9] | 63.4 [40.5–72.5] | 12.6 [6.5–14.4] | 72 [69–79] | 2 | 0 [0–0] |  |
| L3 cnn | 15.4 [12.5–19.9] | 12.1 [9.1–16.1] | 3.4 [3.0–4.2] | 75.7 [59.1–93.9] | 15.1 [12.0–19.9] | 72 [69–79] | 2 | 0 [0–0] |  |
| L4 linear | 14.7 [9.9–59.2] | 8.8 [3.9–52.9] | 6.0 [5.5–6.4] | 72.1 [50.0–279.8] | 13.5 [7.5–57.8] | 72 [69–79] | 3 | 0 [0–0] |  |
| L4 tabpfn | 9.3 [7.8–10.5] | 5.3 [3.7–6.0] | 4.0 [3.6–4.3] | 45.2 [37.3–49.9] | 5.2 [2.1–7.1] | 72 [69–79] | 4 | 0 [0–0] |  |
| L4 cnn | 11.6 [9.0–13.3] | 7.2 [-16.2–8.9] | 4.3 [3.8–8.7] | 57.2 [44.7–63.8] | 9.7 [6.2–11.7] | 72 [69–79] | 6 | 0 [0–0] |  |
| paperA_corr@tgt_s0 (DA) | 8.8 [7.4–10.7] | 3.8 [1.7–5.1] | 5.6 [4.8–6.1] | 43.0 [35.2–52.2] | 6.6 [3.9–8.5] | 72 [69–79] | 0 | 22 [14–28] |  |
| paperA_corr_own (DA) | 17.1 [14.6–20.2] | 11.4 [9.7–14.5] | 5.6 [4.8–6.1] | 82.5 [72.4–96.5] | 17.1 [14.6–20.1] | 72 [69–79] | 0 | 0 [0–0] |  |

### CH->GB per Paper A bin: nMAE median [5–90 %] / gap median

| row | pbin<=15† | pbin15-35† | pbin35-65† | pbin>65 |
|---|---|---|---|---|
| slope_base | 31.6 [25.7–37.4] / +23.0 | 20.0 [16.0–22.5] / +13.6 | 16.6 [12.8–19.5] / +10.8 | 16.5 [13.7–25.5] / +9.7 |
| calibrated_delta | 14.9 [12.2–19.2] / -5.1 | 5.4 [5.0–5.6] / -0.4 | 13.4 [11.1–14.6] / +3.8 | 22.4 [18.9–23.6] / +5.7 |
| hdh | 31.1 [26.0–37.3] / +14.7 | 11.8 [9.0–13.2] / +3.1 | 5.2 [3.7–7.5] / -7.6 | 6.8 [4.7–7.7] / -13.9 |
| paperA_cal | 33.1 [27.5–39.0] / +23.4 | 14.9 [11.5–17.7] / +7.7 | 7.5 [5.2–10.9] / -8.0 | 7.6 [5.0–9.1] / -17.5 |
| paperA_corr | 33.7 [28.4–41.7] / +24.8 | 23.9 [20.0–27.3] / +17.5 | 22.1 [18.2–25.9] / +16.2 | 25.3 [22.2–30.4] / +18.3 |
| paperA_corr_cal | 32.2 [26.9–39.6] / +22.8 | 22.4 [18.3–26.1] / +15.7 | 20.1 [16.2–25.4] / +13.0 | 24.6 [19.6–27.1] / +15.2 |
| paperA_l4a | 19.9 [16.3–25.3] / +10.7 | 8.5 [6.6–9.9] / +2.4 | 5.7 [3.7–6.7] / -0.8 | 6.8 [5.0–7.7] / -0.2 |
| paperA_sh_mh | 55.6 [48.1–66.4] / +20.5 | 34.7 [29.9–38.8] / +16.8 | 29.1 [25.0–33.3] / +18.9 | 31.0 [27.6–36.6] / +22.0 |
| slope_only | 34.7 [29.3–41.6] / +19.3 | 17.0 [13.8–19.1] / +8.7 | 10.3 [8.4–13.6] / +0.2 | 9.5 [7.2–14.3] / -7.1 |
| L1 linear | 12.6 [8.6–17.4] / +6.0 | 9.6 [6.8–10.8] / +1.2 | 16.2 [10.9–20.8] / +5.1 | 24.5 [14.4–33.2] / +11.3 |
| L1 tabpfn | 5.8 [4.7–7.6] / +0.8 | 12.1 [10.5–15.0] / +6.8 | 21.9 [19.0–25.5] / +16.5 | 31.4 [27.5–36.8] / +26.0 |
| L1 cnn | 17.9 [12.0–26.7] / +13.6 | 7.4 [6.5–8.5] / +3.3 | 11.0 [8.0–15.5] / +6.3 | 18.9 [11.0–24.9] / +14.6 |
| L2 linear | 17.7 [10.3–33.5] / +12.3 | 8.6 [7.3–12.2] / +1.3 | 13.2 [8.8–15.0] / +3.9 | 17.5 [11.0–25.1] / +7.7 |
| L2 tabpfn | 21.2 [5.7–25.9] / +16.5 | 8.7 [6.4–9.8] / +3.4 | 5.5 [4.8–11.7] / +1.3 | 9.5 [6.1–14.5] / +5.3 |
| L2 cnn | 17.9 [13.6–22.5] / +13.3 | 7.4 [6.0–8.2] / +2.6 | 9.1 [7.0–10.9] / +4.3 | 11.7 [7.5–14.0] / +5.9 |
| L3 linear | 33.4 [22.8–58.9] / +28.1 | 14.9 [6.5–40.9] / +9.2 | 11.5 [6.9–36.5] / +3.9 | 16.6 [8.0–30.4] / +6.5 |
| L3 tabpfn | 27.0 [15.5–30.3] / +22.1 | 12.2 [5.9–13.6] / +7.2 | 6.4 [4.5–9.3] / +1.6 | 7.0 [5.5–8.8] / +2.6 |
| L3 cnn | 29.4 [22.5–35.7] / +24.0 | 15.1 [9.8–21.5] / +11.1 | 10.7 [6.9–17.0] / +5.4 | 11.7 [8.5–19.0] / +7.5 |
| L4 linear | 30.9 [19.3–120.7] / +21.6 | 13.3 [7.1–58.2] / +7.2 | 6.0 [4.2–30.1] / -1.9 | 9.9 [6.0–33.3] / -2.7 |
| L4 tabpfn | 18.6 [11.8–20.2] / +12.4 | 5.1 [4.5–6.2] / -0.0 | 7.9 [7.0–9.6] / +3.1 | 15.8 [12.8–18.0] / +11.8 |
| L4 cnn | 23.7 [16.0–28.2] / +17.3 | 8.5 [5.5–9.7] / +2.9 | 5.9 [3.8–8.3] / +0.5 | 8.8 [5.6–16.4] / +2.5 |
| paperA_corr@tgt_s0 | 11.1 [8.9–14.7] / +3.2 | 11.8 [8.8–13.4] / +5.5 | 13.3 [9.8–16.7] / +7.4 | 17.9 [14.7–23.1] / +11.4 |
| paperA_corr_own | 29.4 [24.2–36.1] / +20.6 | 18.4 [15.3–21.8] / +12.5 | 15.8 [12.5–19.3] / +9.5 | 17.1 [14.5–23.2] / +9.9 |

### CH->GB bias (mean(pred - y) / max y, %), median per bin

| row | pbin<=15 | pbin15-35 | pbin35-65 | pbin>65 |
|---|---|---|---|---|
| slope_base | +31.4 | +20.0 | +16.6 | +16.4 |
| calibrated_delta | +14.5 | -2.6 | -13.3 | -22.4 |
| hdh | +30.6 | +10.7 | +2.2 | -3.6 |
| paperA_cal | +33.1 | +14.5 | +6.9 | +3.5 |
| paperA_corr | +33.7 | +23.8 | +22.1 | +25.3 |
| paperA_corr_cal | +32.1 | +22.3 | +20.1 | +24.6 |
| paperA_l4a | +19.7 | +7.4 | +0.7 | -3.3 |
| paperA_sh_mh | +55.6 | +34.7 | +29.1 | +31.0 |
| slope_only | +34.3 | +16.3 | +10.0 | +7.7 |
| L1 linear | +11.0 | -5.4 | -15.2 | -24.5 |
| L1 tabpfn | +1.4 | -11.9 | -21.9 | -31.4 |
| L1 cnn | +17.8 | -0.2 | -9.4 | -18.2 |
| L2 linear | +17.3 | +0.9 | -9.2 | -15.8 |
| L2 tabpfn | +21.2 | +6.5 | -0.9 | -7.9 |
| L2 cnn | +17.8 | +3.2 | -2.5 | -4.4 |
| L3 linear | +33.2 | +14.3 | +8.2 | +5.3 |
| L3 tabpfn | +27.0 | +11.8 | +5.0 | +0.6 |
| L3 cnn | +29.3 | +14.8 | +10.2 | +10.2 |
| L4 linear | +30.9 | +13.0 | +3.5 | -7.8 |
| L4 tabpfn | +18.5 | +2.0 | -7.3 | -15.8 |
| L4 cnn | +23.6 | +7.2 | -0.1 | -7.7 |
| paperA_corr@tgt_s0 | +6.2 | +9.9 | +13.0 | +17.7 |
| paperA_corr_own | +29.3 | +18.3 | +15.8 | +16.6 |

## Table 1, GB->CH (overall)

| row | nMAE | gap | in-pool | WAPE | bias | max y (kW) | size_peak seeds | invalid ŝ | note |
|---|---|---|---|---|---|---|---|---|---|
| slope_base | 14.0 [11.0–15.5] | 9.3 [1.4–10.4] | 5.4 [4.4–8.4] | 43.3 [33.1–49.3] | -13.6 [-15.4–-10.4] | 86 [76–101] | 0 | – |  |
| calibrated_delta | 10.8 [8.5–16.4] | 4.0 [2.1–5.4] | 7.1 [5.5–11.1] | 34.5 [26.1–51.3] | 10.5 [7.6–16.4] | 86 [76–101] | 0 | – |  |
| hdh | 10.1 [8.6–10.9] | 3.2 [-1.2–5.0] | 6.8 [5.6–9.7] | 30.9 [27.2–34.1] | -8.7 [-10.5–-6.2] | 86 [76–101] | 0 | – |  |
| paperA_cal | 14.7 [12.5–15.8] | 8.9 [4.6–9.6] | 6.3 [5.0–8.0] | 46.2 [39.0–48.6] | -14.4 [-15.6–-11.9] | 86 [76–101] | 0 | 0 [0–0] |  |
| paperA_corr | 13.1 [11.4–14.7] | 5.1 [-1.7–10.0] | 7.9 [4.8–11.4] | 40.3 [35.5–46.0] | -12.9 [-15.5–-11.4] | 86 [76–101] | 0 | 30 [22–35] |  |
| paperA_corr_cal | 11.4 [9.4–12.6] | 4.0 [-1.7–8.2] | 7.2 [4.7–9.6] | 34.7 [29.3–39.7] | -10.5 [-13.3–-8.7] | 86 [76–101] | 0 | 30 [22–35] |  |
| paperA_l4a | 11.1 [9.1–12.9] | 2.2 [-1.2–4.7] | 8.4 [5.2–12.2] | 34.5 [28.6–38.9] | -2.0 [-6.0–-0.4] | 86 [76–101] | 0 | 30 [22–35] |  |
| paperA_sh_mh | 6.4 [5.2–8.0] | -9.7 [-15.5–-4.8] | 15.9 [10.9–23.3] | 19.1 [16.3–25.1] | 3.1 [0.7–7.3] | 86 [76–101] | 0 | 0 [0–0] |  |
| slope_only | 12.1 [10.3–13.5] | 6.1 [0.3–6.9] | 6.6 [5.6–9.3] | 37.5 [31.9–42.1] | -11.6 [-13.6–-9.6] | 86 [76–101] | 0 | – |  |
| L1 linear | 9.6 [7.2–12.9] | 1.8 [-0.8–3.3] | 8.5 [6.6–10.3] | 30.2 [22.3–40.3] | -7.4 [-11.5–0.9] | 86 [76–101] | 9 | 0 [0–0] |  |
| L1 tabpfn | 7.2 [5.8–10.7] | 1.0 [-2.3–4.5] | 6.3 [5.0–7.3] | 23.2 [18.4–31.6] | -0.7 [-6.2–6.7] | 86 [76–101] | 10 | 0 [0–0] |  |
| L1 cnn | 12.3 [8.1–15.8] | 5.3 [2.0–8.9] | 6.8 [5.0–9.0] | 37.6 [25.4–49.2] | -10.6 [-15.7–-5.0] | 86 [76–101] | 6 | 0 [0–0] |  |
| L2 linear | 8.9 [7.5–13.2] | 1.9 [-1.9–5.1] | 8.3 [5.6–10.4] | 28.7 [23.5–38.8] | -7.1 [-15.0–-5.9] | 86 [76–101] | 9 | 0 [0–0] |  |
| L2 tabpfn | 10.1 [6.1–12.4] | 5.2 [-0.4–7.3] | 5.0 [4.2–6.2] | 31.4 [18.7–38.1] | -9.6 [-12.1–-3.3] | 86 [76–101] | 7 | 0 [0–0] |  |
| L2 cnn | 15.1 [11.1–18.3] | 9.8 [2.4–13.1] | 5.3 [4.1–8.3] | 47.6 [34.4–56.4] | -12.3 [-16.5–-8.4] | 86 [76–101] | 5 | 0 [0–0] |  |
| L3 linear | 6.4 [4.8–11.4] | 1.0 [-1.3–6.7] | 4.9 [4.2–6.9] | 20.3 [15.1–35.7] | -2.3 [-11.6–1.7] | 86 [76–101] | 3 | 0 [0–0] |  |
| L3 tabpfn | 11.6 [5.0–13.6] | 5.6 [-0.8–9.5] | 5.2 [4.0–6.9] | 35.4 [15.1–42.8] | -11.2 [-14.0–-3.5] | 86 [76–101] | 5 | 0 [0–0] |  |
| L3 cnn | 14.5 [11.9–18.4] | 8.6 [6.4–13.4] | 5.2 [4.6–7.5] | 46.4 [36.0–57.3] | -13.4 [-18.4–-6.6] | 86 [76–101] | 6 | 0 [0–0] |  |
| L4 linear | 17.8 [9.4–26.1] | 12.1 [2.3–20.0] | 6.0 [4.5–8.3] | 53.6 [30.3–82.3] | -14.0 [-27.0–3.5] | 86 [76–101] | 8 | 30 [22–35] |  |
| L4 tabpfn | 10.8 [8.8–12.6] | 5.2 [3.7–7.3] | 5.3 [4.0–6.5] | 34.4 [27.6–37.3] | -7.7 [-11.7–-1.6] | 86 [76–101] | 5 | 30 [22–35] |  |
| L4 cnn | 18.3 [11.6–21.4] | 13.0 [3.0–16.4] | 5.6 [4.5–8.0] | 55.4 [36.2–67.7] | -18.0 [-22.3–-8.8] | 86 [76–101] | 2 | 30 [22–35] |  |
| paperA_corr@tgt_s0 (DA) | 5.6 [4.8–7.3] | -2.2 [-8.3–2.6] | 7.9 [4.8–11.4] | 17.2 [15.3–22.9] | -4.1 [-6.6–-2.0] | 86 [76–101] | 0 | 1 [0–2] |  |
| paperA_corr_own (DA) | – | – | – | – | – | – | 0 | – | n/a: no whole-house meters in GB |

### GB->CH per Paper A bin: nMAE median [5–90 %] / gap median

| row | pbin<=15 | pbin15-35 | pbin35-65 | pbin>65 |
|---|---|---|---|---|
| slope_base | 13.8 [11.4–14.8] / +8.2 | 12.8 [9.9–16.1] / +8.1 | 20.5 [10.2–23.4] / +15.0 | 22.7 [12.8–28.9] / +17.7 |
| calibrated_delta | 13.7 [10.9–18.6] / +4.9 | 7.8 [5.0–12.0] / +4.0 | 9.9 [4.7–20.5] / +5.8 | 8.8 [3.5–17.3] / +1.0 |
| hdh | 6.5 [5.5–7.0] / -2.0 | 12.7 [10.4–15.0] / +8.2 | 20.9 [13.8–25.2] / +14.2 | 26.1 [20.0–30.6] / +18.0 |
| paperA_cal | 8.4 [7.0–9.6] / +2.9 | 18.0 [15.4–20.6] / +13.5 | 33.6 [27.5–37.3] / +24.6 | 40.9 [37.9–46.8] / +30.0 |
| paperA_corr | 15.4 [13.1–17.1] / +9.0 | 10.7 [9.6–14.6] / +2.1 | 13.3 [6.6–19.0] / -1.5 | 13.0 [6.5–18.7] / -1.0 |
| paperA_corr_cal | 14.6 [11.9–16.3] / +8.6 | 7.8 [6.7–11.6] / +0.3 | 8.6 [5.8–14.1] / -5.6 | 7.4 [5.0–9.9] / -4.8 |
| paperA_l4a | 12.1 [9.1–13.9] / +4.9 | 7.5 [5.5–8.6] / -1.1 | 15.4 [8.0–27.5] / +1.5 | 21.0 [15.9–33.4] / +6.3 |
| paperA_sh_mh | 7.8 [5.8–10.5] / -10.3 | 4.2 [2.8–5.5] / -9.9 | 7.3 [3.8–11.2] / -14.4 | 8.0 [4.5–11.5] / -9.4 |
| slope_only | 7.4 [6.3–8.1] / -0.5 | 15.1 [13.3–18.6] / +11.2 | 26.7 [18.9–30.9] / +19.2 | 30.9 [26.5–37.9] / +23.8 |
| L1 linear | 6.7 [4.8–8.1] / -0.3 | 11.3 [7.6–15.9] / +3.7 | 24.4 [12.7–30.4] / +5.0 | 32.4 [10.0–39.5] / +8.9 |
| L1 tabpfn | 6.8 [4.9–8.6] / +0.8 | 8.1 [6.8–11.6] / +2.0 | 11.7 [7.8–18.3] / +2.6 | 12.6 [8.7–19.1] / +3.3 |
| L1 cnn | 12.1 [7.0–13.9] / +6.1 | 9.2 [7.8–15.7] / +3.4 | 16.4 [7.9–26.0] / +4.2 | 20.6 [8.0–44.9] / +7.5 |
| L2 linear | 5.9 [4.4–8.1] / -0.5 | 11.2 [8.0–15.1] / +2.7 | 20.2 [14.0–30.4] / +8.2 | 31.1 [18.9–40.1] / +14.1 |
| L2 tabpfn | 8.5 [6.4–10.1] / +4.0 | 9.8 [5.5–13.7] / +4.9 | 17.2 [6.6–20.8] / +9.0 | 21.7 [6.7–26.2] / +14.1 |
| L2 cnn | 11.9 [8.1–15.2] / +7.3 | 16.9 [13.9–20.0] / +11.4 | 26.1 [18.1–29.6] / +16.9 | 22.4 [12.9–72.5] / +9.0 |
| L3 linear | 5.3 [3.9–7.7] / -0.1 | 7.2 [4.2–14.3] / +2.7 | 10.6 [8.1–24.3] / +3.1 | 13.8 [8.5–29.5] / +6.4 |
| L3 tabpfn | 8.1 [4.4–10.8] / +3.1 | 12.5 [5.2–16.2] / +6.0 | 22.8 [5.1–26.5] / +13.0 | 25.3 [10.2–32.8] / +15.6 |
| L3 cnn | 12.7 [10.6–17.3] / +7.8 | 17.3 [13.0–21.9] / +10.9 | 17.1 [10.3–25.8] / +7.2 | 23.9 [13.6–51.9] / +14.7 |
| L4 linear | 13.6 [10.3–18.8] / +8.5 | 17.7 [6.7–29.4] / +13.1 | 30.9 [12.4–58.1] / +23.7 | 50.2 [16.6–75.4] / +42.5 |
| L4 tabpfn | 12.2 [10.8–15.6] / +7.6 | 8.3 [5.5–9.5] / +2.1 | 9.6 [6.5–22.2] / +2.4 | 10.8 [6.9–20.9] / +5.9 |
| L4 cnn | 16.4 [11.7–19.3] / +12.2 | 17.5 [9.6–22.6] / +13.2 | 27.3 [14.4–33.2] / +18.5 | 37.9 [11.6–55.6] / +22.9 |
| paperA_corr@tgt_s0 | 5.7 [4.6–6.2] / -1.0 | 5.5 [4.6–8.6] / -3.5 | 8.5 [5.8–14.5] / -6.1 | 10.0 [4.5–14.4] / -3.9 |
| paperA_corr_own | – / – | – / – | – / – | – / – |

### GB->CH bias (mean(pred - y) / max y, %), median per bin

| row | pbin<=15 | pbin15-35 | pbin35-65 | pbin>65 |
|---|---|---|---|---|
| slope_base | -13.4 | -12.5 | -20.4 | -22.7 |
| calibrated_delta | +13.4 | +7.3 | +9.1 | +6.2 |
| hdh | -4.1 | -12.6 | -20.9 | -26.1 |
| paperA_cal | -7.9 | -18.0 | -33.6 | -40.9 |
| paperA_corr | -15.3 | -10.4 | -13.2 | -12.6 |
| paperA_corr_cal | -14.3 | -7.0 | -6.4 | -5.5 |
| paperA_l4a | -10.7 | +3.8 | +15.4 | +20.6 |
| paperA_sh_mh | +7.2 | +0.0 | -3.6 | -6.7 |
| slope_only | -6.5 | -15.1 | -26.7 | -30.9 |
| L1 linear | -2.2 | -10.1 | -18.3 | -31.9 |
| L1 tabpfn | +0.0 | -0.1 | -2.2 | -7.8 |
| L1 cnn | -11.5 | -8.1 | -12.5 | -12.2 |
| L2 linear | -2.7 | -9.2 | -20.2 | -31.1 |
| L2 tabpfn | -7.9 | -9.3 | -17.2 | -21.7 |
| L2 cnn | -11.3 | -16.7 | -25.1 | -13.4 |
| L3 linear | -1.8 | -3.2 | -6.7 | -7.7 |
| L3 tabpfn | -7.7 | -12.3 | -22.8 | -25.3 |
| L3 cnn | -12.1 | -17.3 | -16.2 | -18.9 |
| L4 linear | -12.0 | -13.3 | -26.7 | -31.8 |
| L4 tabpfn | -11.5 | -3.3 | -5.7 | -1.5 |
| L4 cnn | -16.0 | -17.4 | -27.2 | -37.9 |
| paperA_corr@tgt_s0 | -3.5 | -4.4 | -7.9 | -9.3 |
| paperA_corr_own | – | – | – | – |

† GB target bins <= 65 %: filler-variability-limited (05a). 05a D5 swap deltas (fusion bound, pp): linear -0.33, TabPFN -0.42.
In-pool reference of paperA_corr_own CH->GB: GB's own 06 paperA_corr_own (built on the GB own-stream pilot, a different construction from the CH whole-house pilot).

## Table 2, T1 / T2 (HL, overall; per bin reported only)

| rule | family | direction | cell | A | B | label_def | seeds_A<B | n_seeds | median_rel_diff_pct | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 |  | CH->GB | all | L2 tabpfn | L1 cnn | HL | 7 | 10 | -6.3 | no difference |
| T2 |  | CH->GB | all | L2 tabpfn | slope_base | HL | 10 | 10 | -42.3 | better |
| T1 (bin, reported only) |  | CH->GB | pbin<=15 | L2 tabpfn | L1 cnn | HL | 5 | 10 | -1.5 | no difference |
| T2 (bin, reported only) |  | CH->GB | pbin<=15 | L2 tabpfn | slope_base | HL | 10 | 10 | -31.4 | better |
| T1 (bin, reported only) |  | CH->GB | pbin15-35 | L2 tabpfn | L1 cnn | HL | 2 | 10 | 4.8 | no difference |
| T2 (bin, reported only) |  | CH->GB | pbin15-35 | L2 tabpfn | slope_base | HL | 10 | 10 | -58.6 | better |
| T1 (bin, reported only) |  | CH->GB | pbin35-65 | L2 tabpfn | L1 cnn | HL | 9 | 10 | -39.9 | better |
| T2 (bin, reported only) |  | CH->GB | pbin35-65 | L2 tabpfn | slope_base | HL | 9 | 10 | -65.0 | better |
| T1 (bin, reported only) |  | CH->GB | pbin>65 | L2 tabpfn | L1 cnn | HL | 10 | 10 | -37.7 | better |
| T2 (bin, reported only) |  | CH->GB | pbin>65 | L2 tabpfn | slope_base | HL | 9 | 10 | -46.1 | better |
| T1 |  | GB->CH | all | L2 tabpfn | L1 cnn | HL | 7 | 10 | -17.3 | no difference |
| T2 |  | GB->CH | all | L2 tabpfn | slope_base | HL | 10 | 10 | -27.0 | better |
| T1 (bin, reported only) |  | GB->CH | pbin<=15 | L2 tabpfn | L1 cnn | HL | 9 | 10 | -22.6 | better |
| T2 (bin, reported only) |  | GB->CH | pbin<=15 | L2 tabpfn | slope_base | HL | 10 | 10 | -35.9 | better |
| T1 (bin, reported only) |  | GB->CH | pbin15-35 | L2 tabpfn | L1 cnn | HL | 6 | 10 | -12.3 | no difference |
| T2 (bin, reported only) |  | GB->CH | pbin15-35 | L2 tabpfn | slope_base | HL | 10 | 10 | -23.0 | better |
| T1 (bin, reported only) |  | GB->CH | pbin35-65 | L2 tabpfn | L1 cnn | HL | 5 | 10 | -10.4 | no difference |
| T2 (bin, reported only) |  | GB->CH | pbin35-65 | L2 tabpfn | slope_base | HL | 9 | 10 | -19.4 | better |
| T1 (bin, reported only) |  | GB->CH | pbin>65 | L2 tabpfn | L1 cnn | HL | 5 | 10 | -5.7 | no difference |
| T2 (bin, reported only) |  | GB->CH | pbin>65 | L2 tabpfn | slope_base | HL | 7 | 10 | -18.5 | no difference |

## Table 3, T3 steps (HL, overall). 06 rule 2 stays failed on (a).

| rule | family | direction | cell | A | B | label_def | seeds_A<B | n_seeds | median_rel_diff_pct | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| T3 L2-L1 | linear | CH->GB | all | L2 linear | L1 linear | HL | 3 | 10 | 6.8 | no difference |
| T3 L3-L2 | linear | CH->GB | all | L3 linear | L2 linear | HL | 0 | 10 | 59.2 | worse |
| T3 L4-L3 | linear | CH->GB | all | L4 linear | L3 linear | HL | 7 | 10 | -15.1 | no difference |
| T3 L2-L1 | tabpfn | CH->GB | all | L2 tabpfn | L1 tabpfn | HL | 3 | 10 | 15.8 | no difference |
| T3 L3-L2 | tabpfn | CH->GB | all | L3 tabpfn | L2 tabpfn | HL | 1 | 10 | 17.8 | worse |
| T3 L4-L3 | tabpfn | CH->GB | all | L4 tabpfn | L3 tabpfn | HL | 10 | 10 | -29.2 | better |
| T3 L2-L1 | cnn | CH->GB | all | L2 cnn | L1 cnn | HL | 8 | 10 | -4.7 | no difference |
| T3 L3-L2 | cnn | CH->GB | all | L3 cnn | L2 cnn | HL | 0 | 10 | 68.0 | worse |
| T3 L4-L3 | cnn | CH->GB | all | L4 cnn | L3 cnn | HL | 10 | 10 | -23.8 | better |
| T3 06hybrid-D* |  | CH->GB | all | L4 cnn | L1 cnn | HL | 2 | 10 | 9.3 | worse |
| T3 L2-L1 | linear | GB->CH | all | L2 linear | L1 linear | HL | 5 | 10 | 5.9 | no difference |
| T3 L3-L2 | linear | GB->CH | all | L3 linear | L2 linear | HL | 9 | 10 | -29.1 | better |
| T3 L4-L3 | linear | GB->CH | all | L4 linear | L3 linear | HL | 0 | 10 | 143.1 | worse |
| T3 L2-L1 | tabpfn | GB->CH | all | L2 tabpfn | L1 tabpfn | HL | 3 | 10 | 28.8 | no difference |
| T3 L3-L2 | tabpfn | GB->CH | all | L3 tabpfn | L2 tabpfn | HL | 5 | 10 | 1.3 | no difference |
| T3 L4-L3 | tabpfn | GB->CH | all | L4 tabpfn | L3 tabpfn | HL | 5 | 10 | -1.8 | no difference |
| T3 L2-L1 | cnn | GB->CH | all | L2 cnn | L1 cnn | HL | 4 | 10 | 19.7 | no difference |
| T3 L3-L2 | cnn | GB->CH | all | L3 cnn | L2 cnn | HL | 6 | 10 | -0.6 | no difference |
| T3 L4-L3 | cnn | GB->CH | all | L4 cnn | L3 cnn | HL | 2 | 10 | 18.5 | worse |
| T3 06hybrid-D* |  | GB->CH | all | L4 tabpfn | L1 cnn | HL | 6 | 10 | -9.9 | no difference |

## Sensitivity: rules on HL_uncorrected and native (outside the rules)

| rule | family | direction | cell | A | B | label_def | seeds_A<B | n_seeds | median_rel_diff_pct | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 |  | CH->GB | all | L2 tabpfn | L1 cnn | HL_uncorrected | 6 | 10 | -3.9 | no difference |
| T2 |  | CH->GB | all | L2 tabpfn | slope_base | HL_uncorrected | 10 | 10 | -42.7 | better |
| T3 L2-L1 | linear | CH->GB | all | L2 linear | L1 linear | HL_uncorrected | 2 | 10 | 10.7 | worse |
| T3 L3-L2 | linear | CH->GB | all | L3 linear | L2 linear | HL_uncorrected | 0 | 10 | 66.9 | worse |
| T3 L4-L3 | linear | CH->GB | all | L4 linear | L3 linear | HL_uncorrected | 7 | 10 | -14.2 | no difference |
| T3 L2-L1 | tabpfn | CH->GB | all | L2 tabpfn | L1 tabpfn | HL_uncorrected | 2 | 10 | 29.9 | worse |
| T3 L3-L2 | tabpfn | CH->GB | all | L3 tabpfn | L2 tabpfn | HL_uncorrected | 1 | 10 | 24.9 | worse |
| T3 L4-L3 | tabpfn | CH->GB | all | L4 tabpfn | L3 tabpfn | HL_uncorrected | 10 | 10 | -32.1 | better |
| T3 L2-L1 | cnn | CH->GB | all | L2 cnn | L1 cnn | HL_uncorrected | 6 | 10 | -1.6 | no difference |
| T3 L3-L2 | cnn | CH->GB | all | L3 cnn | L2 cnn | HL_uncorrected | 0 | 10 | 71.7 | worse |
| T3 L4-L3 | cnn | CH->GB | all | L4 cnn | L3 cnn | HL_uncorrected | 10 | 10 | -27.1 | better |
| T3 06hybrid-D* |  | CH->GB | all | L4 cnn | L1 cnn | HL_uncorrected | 2 | 10 | 11.5 | worse |
| T1 |  | GB->CH | all | L2 tabpfn | L1 cnn | HL_uncorrected | 7 | 10 | -22.4 | no difference |
| T2 |  | GB->CH | all | L2 tabpfn | slope_base | HL_uncorrected | 10 | 10 | -29.3 | better |
| T3 L2-L1 | linear | GB->CH | all | L2 linear | L1 linear | HL_uncorrected | 5 | 10 | 0.5 | no difference |
| T3 L3-L2 | linear | GB->CH | all | L3 linear | L2 linear | HL_uncorrected | 9 | 10 | -30.6 | better |
| T3 L4-L3 | linear | GB->CH | all | L4 linear | L3 linear | HL_uncorrected | 0 | 10 | 144.0 | worse |
| T3 L2-L1 | tabpfn | GB->CH | all | L2 tabpfn | L1 tabpfn | HL_uncorrected | 3 | 10 | 19.3 | no difference |
| T3 L3-L2 | tabpfn | GB->CH | all | L3 tabpfn | L2 tabpfn | HL_uncorrected | 5 | 10 | 1.4 | no difference |
| T3 L4-L3 | tabpfn | GB->CH | all | L4 tabpfn | L3 tabpfn | HL_uncorrected | 5 | 10 | 1.7 | no difference |
| T3 L2-L1 | cnn | GB->CH | all | L2 cnn | L1 cnn | HL_uncorrected | 3 | 10 | 16.4 | no difference |
| T3 L3-L2 | cnn | GB->CH | all | L3 cnn | L2 cnn | HL_uncorrected | 6 | 10 | -0.5 | no difference |
| T3 L4-L3 | cnn | GB->CH | all | L4 cnn | L3 cnn | HL_uncorrected | 2 | 10 | 21.2 | worse |
| T3 06hybrid-D* |  | GB->CH | all | L4 tabpfn | L1 cnn | HL_uncorrected | 5 | 10 | -4.4 | no difference |
| T1 |  | CH->GB | all | L2 tabpfn | L1 cnn | native | 7 | 10 | -6.6 | no difference |
| T2 |  | CH->GB | all | L2 tabpfn | slope_base | native | 10 | 10 | -42.5 | better |
| T3 L2-L1 | linear | CH->GB | all | L2 linear | L1 linear | native | 3 | 10 | 6.4 | no difference |
| T3 L3-L2 | linear | CH->GB | all | L3 linear | L2 linear | native | 0 | 10 | 59.6 | worse |
| T3 L4-L3 | linear | CH->GB | all | L4 linear | L3 linear | native | 7 | 10 | -14.8 | no difference |
| T3 L2-L1 | tabpfn | CH->GB | all | L2 tabpfn | L1 tabpfn | native | 3 | 10 | 13.3 | no difference |
| T3 L3-L2 | tabpfn | CH->GB | all | L3 tabpfn | L2 tabpfn | native | 1 | 10 | 17.9 | worse |
| T3 L4-L3 | tabpfn | CH->GB | all | L4 tabpfn | L3 tabpfn | native | 10 | 10 | -29.2 | better |
| T3 L2-L1 | cnn | CH->GB | all | L2 cnn | L1 cnn | native | 7 | 10 | -4.2 | no difference |
| T3 L3-L2 | cnn | CH->GB | all | L3 cnn | L2 cnn | native | 0 | 10 | 67.4 | worse |
| T3 L4-L3 | cnn | CH->GB | all | L4 cnn | L3 cnn | native | 10 | 10 | -24.3 | better |
| T3 06hybrid-D* |  | CH->GB | all | L4 cnn | L1 cnn | native | 2 | 10 | 9.1 | worse |
| T1 |  | GB->CH | all | L2 tabpfn | L1 cnn | native | 7 | 10 | -18.0 | no difference |
| T2 |  | GB->CH | all | L2 tabpfn | slope_base | native | 10 | 10 | -26.7 | better |
| T3 L2-L1 | linear | GB->CH | all | L2 linear | L1 linear | native | 5 | 10 | 7.2 | no difference |
| T3 L3-L2 | linear | GB->CH | all | L3 linear | L2 linear | native | 9 | 10 | -28.6 | better |
| T3 L4-L3 | linear | GB->CH | all | L4 linear | L3 linear | native | 0 | 10 | 151.1 | worse |
| T3 L2-L1 | tabpfn | GB->CH | all | L2 tabpfn | L1 tabpfn | native | 3 | 10 | 29.1 | no difference |
| T3 L3-L2 | tabpfn | GB->CH | all | L3 tabpfn | L2 tabpfn | native | 5 | 10 | 1.0 | no difference |
| T3 L4-L3 | tabpfn | GB->CH | all | L4 tabpfn | L3 tabpfn | native | 5 | 10 | -2.2 | no difference |
| T3 L2-L1 | cnn | GB->CH | all | L2 cnn | L1 cnn | native | 4 | 10 | 17.5 | no difference |
| T3 L3-L2 | cnn | GB->CH | all | L3 cnn | L2 cnn | native | 6 | 10 | -0.4 | no difference |
| T3 L4-L3 | cnn | GB->CH | all | L4 cnn | L3 cnn | native | 2 | 10 | 18.0 | worse |
| T3 06hybrid-D* |  | GB->CH | all | L4 tabpfn | L1 cnn | native | 6 | 10 | -9.7 | no difference |

## Table 4, labels (median over seeds of the seed medians [seed min–max]; within-seed 5–90 %)

| pool | split | quantity | cell | seed_median | seed_min | seed_max | within_q05 | within_q90 |
|---|---|---|---|---|---|---|---|---|
| CH | test | c | all | 0.9531 | 0.8917 | 0.9734 | 0.826 | 0.9918 |
| CH | test | c | pbin15-35 | 0.944 | 0.8934 | 0.9695 | 0.8478 | 0.9847 |
| CH | test | c | pbin35-65 | 0.9514 | 0.8793 | 0.977 | 0.9192 | 0.9737 |
| CH | test | c | pbin<=15 | 0.9587 | 0.8955 | 0.9762 | 0.775 | 0.9946 |
| CH | test | c | pbin>65 | 0.952 | 0.8781 | 0.9737 | 0.9247 | 0.9661 |
| CH | train | c | all | 0.9424 | 0.9307 | 0.965 | 0.8474 | 0.9884 |
| CH | train | c | pbin15-35 | 0.9443 | 0.9254 | 0.9581 | 0.8656 | 0.9809 |
| CH | train | c | pbin35-65 | 0.9428 | 0.9284 | 0.9604 | 0.8879 | 0.9713 |
| CH | train | c | pbin<=15 | 0.9469 | 0.9378 | 0.9717 | 0.8349 | 0.995 |
| CH | train | c | pbin>65 | 0.9371 | 0.924 | 0.9654 | 0.8963 | 0.9645 |
| CH | train | net_peak_30_15 | all | 0.9445 | 0.9393 | 0.9494 | 0.8621 | 0.9831 |
| CH | train | net_peak_30_15 | pbin15-35 | 0.945 | 0.9333 | 0.9491 | 0.8697 | 0.9811 |
| CH | train | net_peak_30_15 | pbin35-65 | 0.9439 | 0.9311 | 0.9578 | 0.8777 | 0.9813 |
| CH | train | net_peak_30_15 | pbin<=15 | 0.9441 | 0.9404 | 0.9502 | 0.8511 | 0.983 |
| CH | train | net_peak_30_15 | pbin>65 | 0.9501 | 0.93 | 0.9605 | 0.8896 | 0.9845 |
| GB | test | c | all | 0.9585 | 0.9422 | 0.9755 | 0.7806 | 1.0 |
| GB | test | c | pbin15-35 | 0.9552 | 0.94 | 0.9685 | 0.8175 | 1.0 |
| GB | test | c | pbin35-65 | 0.9543 | 0.9069 | 0.9716 | 0.8526 | 0.9867 |
| GB | test | c | pbin<=15 | 0.969 | 0.9569 | 0.9936 | 0.7606 | 1.0 |
| GB | test | c | pbin>65 | 0.9561 | 0.9351 | 0.9757 | 0.9213 | 0.979 |
| GB | test | immersion_share | all | 0.0415 | 0.0245 | 0.0578 | -0.0 | 0.1766 |
| GB | test | immersion_share | pbin15-35 | 0.0448 | 0.0315 | 0.06 | -0.0 | 0.1579 |
| GB | test | immersion_share | pbin35-65 | 0.0457 | 0.0284 | 0.0931 | 0.003 | 0.1123 |
| GB | test | immersion_share | pbin<=15 | 0.031 | 0.0064 | 0.0431 | -0.0 | 0.1871 |
| GB | test | immersion_share | pbin>65 | 0.0439 | 0.0243 | 0.0649 | 0.014 | 0.075 |
| GB | train | c | all | 0.955 | 0.953 | 0.9576 | 0.7755 | 1.0 |
| GB | train | c | pbin15-35 | 0.9507 | 0.9474 | 0.9559 | 0.7991 | 1.0 |
| GB | train | c | pbin35-65 | 0.9455 | 0.9417 | 0.9504 | 0.819 | 0.9901 |
| GB | train | c | pbin<=15 | 0.9656 | 0.9617 | 0.9711 | 0.7226 | 1.0 |
| GB | train | c | pbin>65 | 0.9498 | 0.9426 | 0.9559 | 0.8558 | 0.9815 |
| GB | train | immersion_share | all | 0.045 | 0.0424 | 0.047 | -0.0 | 0.1737 |
| GB | train | immersion_share | pbin15-35 | 0.0493 | 0.0441 | 0.0526 | -0.0 | 0.1675 |
| GB | train | immersion_share | pbin35-65 | 0.0545 | 0.0496 | 0.0583 | 0.0026 | 0.1482 |
| GB | train | immersion_share | pbin<=15 | 0.0344 | 0.0289 | 0.0383 | -0.0 | 0.1871 |
| GB | train | immersion_share | pbin>65 | 0.0502 | 0.0441 | 0.0574 | 0.0102 | 0.1269 |

## HP households (distinct), median [min–max] over seeds

| arm | split | median | min | max |
|---|---|---|---|---|
| a_ch | test | 20.0 | 20 | 20 |
| a_ch | train | 62.0 | 62 | 62 |
| a_gb | test | 81.0 | 81 | 81 |
| a_gb | train | 274.0 | 274 | 274 |

Honesty note: H\* and D\* were selected in-pool (06 inner-CV WAPE) and their in-pool test results are known; the transfer targets were never used by any selection; c uses source train labels only; T_design is metadata.
