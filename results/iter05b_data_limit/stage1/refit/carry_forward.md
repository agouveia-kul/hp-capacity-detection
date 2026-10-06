# A10 carry-forward (refit_persist.py carry)

Families ranked by the median over seeds of the Arm 2 winner's inner-CV WAPE (never test).

| family | median_inner_wape | rank | gap_to_best_pp | carried | reason |
|---|---|---|---|---|---|
| neural | 16.91 | 1 | 0.0 | True | top 2 |
| rawseries | 17.9 | 2 | 0.99 | True | top 2 |
| kernel | 19.97 | 3 | 3.06 | False | not carried |
| trees | 20.45 | 4 | 3.54 | False | not carried |
| linear | 21.67 | 5 | 4.76 | True | linear always |

Carried models per family (reload check passed):

| family | seeds | reload_pass | carried_models |
|---|---|---|---|
| kernel | 20 | 20 | 0 |
| linear | 20 | 20 | 20 |
| neural | 20 | 20 | 20 |
| rawseries | 20 | 20 | 20 |
| trees | 20 | 20 | 0 |
