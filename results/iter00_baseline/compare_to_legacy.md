# compare_to_legacy (commit ff6bde8, tolerance 1% relative)

| file | columns | columns > 1 % | worst column | max rel diff | unmatched rows | rows > 1 % |
|---|---|---|---|---|---|---|
| capacity_model_benchmark.csv | 8 | 8 | wpuq_mape | 3.3e-01 | 0 | XGBoost |
| capacity_wpuq_real_feeder.csv | 4 | 3 | abs_pct_err | 3.4e-01 | 0 | XGBoost |
| xgb_feature_selection_cv.csv | 2 | 2 | cv_rmse_std | 3.5e-01 | 0 | 10, 120, 15, 160, 20, 220, 274, 30, 40, 5, 60, 80 |
| xgb_hockey_ci_metrics.csv | 12 | 0 | n | 0.0e+00 | 0 | - |
| hockey_variants_transfer.csv | 4 | 0 | n | 0.0e+00 | 0 | - |
| hockey_delta_calibrated.csv | 4 | 0 | n | 0.0e+00 | 0 | - |
| wpuq_penetration_sweep.csv | 9 | 0 | penetration | 0.0e+00 | 0 | - |
| wpuq_penetration_variants.csv | 10 | 0 | size | 0.0e+00 | 0 | - |
| penetration_calibrated_delta.csv | 4 | 0 | true_mean | 0.0e+00 | 0 | - |
| swiss_penetration_sweep.csv | 5 | 0 | n | 0.0e+00 | 0 | - |
| xgb_feature_selection_cv_evalonly.csv | 2 | 0 | cv_rmse_mean | 0.0e+00 | 0 | - |
