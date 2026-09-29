# DECISIONS

Append-only log. One line per decision: `date | iteration | decision | rationale`. Never edit or delete a past line; supersede it with a new one.

2026-09-29 | 00 | The legacy CSVs in `data/` are the official legacy baseline; the seed-42 rerun is quoted only as a single-seed spread for the XGBoost rows. | 7 of 9 legacy files reproduce exactly; the gaps come only from unseeded hyperopt in `tune_xgb_cv`.
2026-09-29 | 00 | The 10 recovered legacy scripts are trusted, and every XGBoost-tuned legacy number is treated as single-seed. | All 10 are byte-identical to git `309eaaf^` / `NILM/OLD/`; rows reproduce exactly when the legacy hyperparameters are reused.
2026-09-29 | 00 | The ~660-line iteration-00 infrastructure diff is accepted as-is (no 00a/00b split). | Runner, compare, facts, environment record and tests did not fit in 300 lines; it is infrastructure, not method.
