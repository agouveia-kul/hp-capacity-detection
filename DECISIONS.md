# DECISIONS

Append-only log. One line per decision: `date | iteration | decision | rationale`. Never edit or delete a past line; supersede it with a new one.

2026-09-29 | 00 | The legacy CSVs in `data/` are the official legacy baseline; the seed-42 rerun is quoted only as a single-seed spread for the XGBoost rows. | 7 of 9 legacy files reproduce exactly; the gaps come only from unseeded hyperopt in `tune_xgb_cv`.
2026-09-29 | 00 | The 10 recovered legacy scripts are trusted, and every XGBoost-tuned legacy number is treated as single-seed. | All 10 are byte-identical to git `309eaaf^` / `NILM/OLD/`; rows reproduce exactly when the legacy hyperparameters are reused.
2026-09-29 | 00 | The ~660-line iteration-00 infrastructure diff is accepted as-is (no 00a/00b split). | Runner, compare, facts, environment record and tests did not fit in 300 lines; it is infrastructure, not method.
2026-09-29 | 01 | Pool: B* (86 HP households, cal2023, incl. the 15 Kaiser SFH HP meters each paired with one unused clean dwelling) is the main 15-min arm; B (KLO only, 47) is a sensitivity arm; C is not adopted and cal2024 is reserved for RQ4. | Largest household-disjoint 15-min pool with clean fill; cal2023 is the only year with both HEAPO 15-min HP and Kaiser fill.
2026-09-29 | 01 | Daily arm: yes, as a secondary arm, built in iteration 03 (not 02). HP_Nameplate_el leaves the substation benchmark and becomes a household-level check (nameplate vs observed peak). | Only large-N test of HP_Count; nameplate covers at most 14 households per station-window.
2026-09-29 | 01 | Fix F1, F2, F12, F13 and F14 now (iteration 02a); defer F3-F8 to 03 and F10/F11 to the transfer iteration. | High-severity findings that the protocol v1 benchmark depends on.
2026-09-29 | 01 | Iteration 02 is split: 02a implements protocol v1 as code and tests (smoke run only); 02b reruns the benchmark. | Keeps each reviewed diff small; no results are interpreted before the code is reviewed.
