[iter03b_sens_b] Task 6 (pre-registered): dWAPE = WAPE(ML) - WAPE(best physics row) per seed; ML beats physics iff dWAPE < 0 in >= 16 of 20 seeds (>= 80 % of the seeds) and median dWAPE <= -1 pp. Best physics row chosen per scope by median WAPE among the Task 5 physics rows.

| scope | ML configuration | best physics row | n_seeds | seeds ML < physics | median dWAPE pp | verdict |
|---|---|---|---|---|---|---|
| all | ElasticNet [size_peak] both/direct-log | physics: paperA_cal | 10 | 7/10 | -4.25 | no better than physics |
| all | ElasticNet [size_peak] both/residual-log | physics: paperA_cal | 10 | 6/10 | -0.61 | no better than physics |
| all | Lasso [size_peak] both/direct-log | physics: paperA_cal | 10 | 6/10 | -4.20 | no better than physics |
| all | Lasso [size_peak] both/residual-log | physics: paperA_cal | 10 | 7/10 | -1.08 | no better than physics |
| all | Linear [size_peak] both/direct-log | physics: paperA_cal | 10 | 0/10 | 1750.64 | no better than physics |
| all | PLS [size_peak] both/direct-log | physics: paperA_cal | 10 | 6/10 | -0.52 | no better than physics |
| all | Ridge [size_peak] both/direct-log | physics: paperA_cal | 10 | 6/10 | -3.07 | no better than physics |
| all | Ridge [size_peak] both/residual-log | physics: paperA_cal | 10 | 9/10 | -1.57 | BEATS physics |
| all | SVR [size_peak] both/direct-log | physics: paperA_cal | 10 | 7/10 | -2.70 | no better than physics |
| all | XGBoost [size_peak] both/direct-log | physics: paperA_cal | 10 | 7/10 | -1.35 | no better than physics |
| all | XGBoost [size_peak] both/residual-log | physics: paperA_cal | 10 | 6/10 | -0.59 | no better than physics |
| all | XGBoost_mono [size_peak] both/direct-log | physics: paperA_cal | 10 | 6/10 | -0.90 | no better than physics |
| pbin<=15 | ElasticNet [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 10/10 | -5.44 | BEATS physics |
| pbin<=15 | ElasticNet [size_peak] both/residual-log | physics: paperA_corr_all | 10 | 6/10 | -0.10 | no better than physics |
| pbin<=15 | Lasso [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 9/10 | -4.92 | BEATS physics |
| pbin<=15 | Lasso [size_peak] both/residual-log | physics: paperA_corr_all | 10 | 5/10 | 0.40 | no better than physics |
| pbin<=15 | Linear [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 0/10 | 2407.34 | no better than physics |
| pbin<=15 | PLS [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 8/10 | -4.23 | BEATS physics |
| pbin<=15 | Ridge [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 9/10 | -4.84 | BEATS physics |
| pbin<=15 | Ridge [size_peak] both/residual-log | physics: paperA_corr_all | 10 | 8/10 | -1.98 | BEATS physics |
| pbin<=15 | SVR [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 8/10 | -5.28 | BEATS physics |
| pbin<=15 | XGBoost [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 7/10 | -2.25 | no better than physics |
| pbin<=15 | XGBoost [size_peak] both/residual-log | physics: paperA_corr_all | 10 | 4/10 | 1.09 | no better than physics |
| pbin<=15 | XGBoost_mono [size_peak] both/direct-log | physics: paperA_corr_all | 10 | 8/10 | -3.45 | BEATS physics |
| pbin15-35 | ElasticNet [size_peak] both/direct-log | physics: paperA_cal | 10 | 2/10 | 4.56 | no better than physics |
| pbin15-35 | ElasticNet [size_peak] both/residual-log | physics: paperA_cal | 10 | 2/10 | 0.74 | no better than physics |
| pbin15-35 | Lasso [size_peak] both/direct-log | physics: paperA_cal | 10 | 1/10 | 4.71 | no better than physics |
| pbin15-35 | Lasso [size_peak] both/residual-log | physics: paperA_cal | 10 | 3/10 | 0.74 | no better than physics |
| pbin15-35 | Linear [size_peak] both/direct-log | physics: paperA_cal | 10 | 0/10 | 306.36 | no better than physics |
| pbin15-35 | PLS [size_peak] both/direct-log | physics: paperA_cal | 10 | 2/10 | 7.17 | no better than physics |
| pbin15-35 | Ridge [size_peak] both/direct-log | physics: paperA_cal | 10 | 2/10 | 6.85 | no better than physics |
| pbin15-35 | Ridge [size_peak] both/residual-log | physics: paperA_cal | 10 | 0/10 | 1.46 | no better than physics |
| pbin15-35 | SVR [size_peak] both/direct-log | physics: paperA_cal | 10 | 3/10 | 3.90 | no better than physics |
| pbin15-35 | XGBoost [size_peak] both/direct-log | physics: paperA_cal | 10 | 1/10 | 4.69 | no better than physics |
| pbin15-35 | XGBoost [size_peak] both/residual-log | physics: paperA_cal | 10 | 1/10 | 1.48 | no better than physics |
| pbin15-35 | XGBoost_mono [size_peak] both/direct-log | physics: paperA_cal | 10 | 1/10 | 6.81 | no better than physics |
| pbin35-65 | ElasticNet [size_peak] both/direct-log | physics: calibrated_delta | 10 | 2/10 | 3.55 | no better than physics |
| pbin35-65 | ElasticNet [size_peak] both/residual-log | physics: calibrated_delta | 10 | 1/10 | 5.70 | no better than physics |
| pbin35-65 | Lasso [size_peak] both/direct-log | physics: calibrated_delta | 10 | 3/10 | 3.83 | no better than physics |
| pbin35-65 | Lasso [size_peak] both/residual-log | physics: calibrated_delta | 10 | 1/10 | 5.61 | no better than physics |
| pbin35-65 | Linear [size_peak] both/direct-log | physics: calibrated_delta | 10 | 0/10 | 256.27 | no better than physics |
| pbin35-65 | PLS [size_peak] both/direct-log | physics: calibrated_delta | 10 | 0/10 | 13.61 | no better than physics |
| pbin35-65 | Ridge [size_peak] both/direct-log | physics: calibrated_delta | 10 | 1/10 | 12.07 | no better than physics |
| pbin35-65 | Ridge [size_peak] both/residual-log | physics: calibrated_delta | 10 | 1/10 | 4.40 | no better than physics |
| pbin35-65 | SVR [size_peak] both/direct-log | physics: calibrated_delta | 10 | 1/10 | 8.66 | no better than physics |
| pbin35-65 | XGBoost [size_peak] both/direct-log | physics: calibrated_delta | 10 | 3/10 | 6.65 | no better than physics |
| pbin35-65 | XGBoost [size_peak] both/residual-log | physics: calibrated_delta | 10 | 1/10 | 2.96 | no better than physics |
| pbin35-65 | XGBoost_mono [size_peak] both/direct-log | physics: calibrated_delta | 10 | 3/10 | 5.32 | no better than physics |
