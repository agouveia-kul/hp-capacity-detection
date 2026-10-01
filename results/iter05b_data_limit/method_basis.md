# 05b — Methodological basis (model families, learning-curve fit, oracles)

Metadata (title, authors, year, venue, DOI) retrieved from Crossref and the arXiv API on 2026-10-01; the TabPFN-3.5 licence and
checkpoint names from the Hugging Face model card `Prior-Labs/tabpfn_3_5` on 2026-10-01. Full texts were **not** read in 05b;
the one-line descriptions below are from the retrieved records and the standard description of these works.

## Model families (Task 1e)
- **Kernel ridge regression** (sklearn `KernelRidge`, RBF / Laplacian kernel, alpha and gamma tuned) and **Gaussian-process
  regression** (sklearn `GaussianProcessRegressor`: constant x ARD RBF + white-noise kernel on the standardised target, type-II
  maximum likelihood, 3 seeded restarts; 5–95 % predictive interval from the predictive sd, white noise included) [1, 2].
- **Random Forest** [3] and **Extra Trees** [4] (sklearn; n_estimators, max_features, min_samples_leaf, max_depth tuned; fitted in
  parallel, predicted serially so that the output does not depend on thread scheduling).
- **CatBoost** [5] (`catboost` 1.2.10; depth, learning rate, l2_leaf_reg, iterations tuned; early stopping on the next training
  fold like XGBoost; `thread_count` capped, `random_seed` set).
- **TabPFN** [6, 7]: TabPFN-3.5 regressor, `tabpfn` 9.0.0, checkpoint `tabpfn-v3.5-20260909.safetensors`
  (SHA-256 `ece4d67eadfea42eb0e610df5189bea60cb7f31073d81e9c7a019b76eacf0be3`), loaded from `TABPFN_MODEL_CACHE_DIR` with
  `model_path`, CPU, no hyperopt (in-context learning), ensemble count "auto", `random_state` = split seed. The package's CPU guard
  (> 1000 training rows raises) is a speed warning, not a pre-training limit, and is lifted with `TABPFN_ALLOW_CPU_LARGE_DATASET=1`;
  `ignore_pretraining_limits` stays False, so the model's real limits still apply. No download, licence call or token is used when
  the file exists (checked in `tabpfn/model_loading.py`: the licence check sits only in the download path).
  **Licence:** the weights are under `tabpfn-3-5-license-v1.0`: testing, evaluation, internal benchmarking and research are allowed;
  any commercial or production purpose (revenue-generating products, client deliverables, internal commercial decision-making) is
  not. This work is non-commercial research (Alex, 2026-09-30); neither the model nor its outputs may be used commercially or in
  production.
- **Raw-series 1D-CNN** (PyTorch 2.14.1, CPU, deterministic): 2–3 convolution blocks -> global average pooling -> dense head on the
  365 x 2 daily net-load / size and temperature series, the anchors joined after pooling. This is the fully convolutional
  time-series architecture with global average pooling of [8], used here for regression on log y (or z). Precedent for this
  exact input (a feeder's daily net-load and temperature series -> installed capacity) was **not** found; the family is a
  feature-free control, not a proposed method.
- Kernel ridge and GP use the textbook formulations [1, 2]; no domain precedent is claimed for any of these models in this task.

## Learning-curve fit (Task 1a)
WAPE(n) = a + b n^(-c) with c in (0, 2], fitted per seed to the median over draws. An inverse power law with an asymptote is one
of the parametric learning-curve families reviewed in [9]; power-law scaling of error with training-set size is reported
empirically in [10]. The asymptote a, the exponent c and n* (where the fitted curve reaches the physics WAPE) are extrapolations
from n <= 293 and are reported with their across-seed spread and with flags when c sits at a bound or a < 0.

## Oracles and response scaling (Task 1c, A7, Arm 7)
O1 / O2 and the error decomposition are diagnostics built on Paper A's estimator (s_h / m_h); no external precedent is claimed.
The response scaling multiplies each household's day below its own T_h by (P_base + f (y_d - P_base)) / y_d, i.e. it scales the
day's deviation from the household's base load by f while keeping the intraday profile; **no precedent was found**; it is our
construction, checked by tests (synthetic and 400 real LCL fillers: aggregate s0 scales by f within 2 %, P_base within 1 %).

## References
1. Rasmussen, C. E., Williams, C. K. I. (2005/2006). *Gaussian Processes for Machine Learning*. MIT Press. doi:10.7551/mitpress/3206.001.0001
2. Hastie, T., Tibshirani, R., Friedman, J. (2009). *The Elements of Statistical Learning* (2nd ed.). Springer. doi:10.1007/978-0-387-84858-7
3. Breiman, L. (2001). Random Forests. *Machine Learning* 45, 5–32. doi:10.1023/A:1010933404324
4. Geurts, P., Ernst, D., Wehenkel, L. (2006). Extremely randomized trees. *Machine Learning* 63, 3–42. doi:10.1007/s10994-006-6226-1
5. Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., Gulin, A. (2017/2018). CatBoost: unbiased boosting with categorical features. arXiv:1706.09516 (NeurIPS 2018; proceedings record not retrieved).
6. Hollmann, N., Müller, S., Purucker, L., Krishnakumar, A., Körfer, M., Hoo, S. B., Schirrmeister, R. T., Hutter, F. (2025). Accurate predictions on small data with a tabular foundation model. *Nature* 637, 319–326. doi:10.1038/s41586-024-08328-6
7. Jäger, B., Erickson, N., Grinsztajn, L., Birkel, F., Flöge, K., Key, O., Kaya, K., Kübler, J., Frankel, A., Schröder, T., et al. (43 authors) (2026). TabPFN-3.5: Technical Report. arXiv:2609.17895 (v2, 22 Sep 2026).
8. Wang, Z., Yan, W., Oates, T. (2017). Time series classification from scratch with deep neural networks: A strong baseline. *IJCNN 2017*, 1578–1585. doi:10.1109/IJCNN.2017.7966039
9. Viering, T., Loog, M. (2023). The Shape of Learning Curves: A Review. *IEEE TPAMI* 45, 7799–7819. doi:10.1109/TPAMI.2022.3220744
10. Hestness, J., Narang, S., Ardalani, N., Diamos, G., Jun, H., Kianinejad, H., Patwary, M. M. A., Yang, Y., Zhou, Y. (2017). Deep Learning Scaling is Predictable, Empirically. arXiv:1712.00409
