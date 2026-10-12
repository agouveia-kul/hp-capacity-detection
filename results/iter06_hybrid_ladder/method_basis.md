# 06 — Methodological basis (the hybrid ladder)

Metadata (title, authors, year, venue, volume, pages, DOI) of references 1–13 retrieved from the Crossref API on 2026-10-12.
Full texts were **not** read in 06: the one-line descriptions are from the retrieved records and the standard description of
these works. Entries marked **UNVERIFIED** were not retrieved. Nothing here is cited for a result of ours.

## Hybrid (physics + learning) modelling: L2, L3, L4
- **Position.** The ladder follows the usual taxonomy of combining prior knowledge with learning [1, 2, 3]: knowledge enters
  through the inputs (L2: physics-derived features), through the target (L3: a residual on a physics estimate) and through the
  model structure (L4: a physical law with one learned factor and a learned residual).
- **Residual (serial / parallel hybrid) models.** L3 and L4 fit an ML model to what a first-principles estimate leaves
  unexplained. This is the semi-parametric hybrid design of process systems engineering [4, 5, 6]: [4] and [5] are the early
  neural-network / first-principles hybrids, [6] reviews the family. Here the residual is multiplicative, z = log y − log P̂,
  so ẑ = 0 returns the physics estimate exactly.
- **L4, learned transferable scale.** P̂ = ŝ / m̂_h · exp(f_θ(x)), with ŝ = max(s_h(net) − N·s₀, 0) the net-load slope after
  Paper A's non-TCL correction and m_h the slope per unit of capacity. The physical part is Paper A's estimator; the learned
  parts are m̂_h (one parameter, L4a; a small regression, L4b) and the residual f_θ. **No precedent was found** for learning
  the scale m_h of a thermal-sensitivity capacity estimator from aggregate covariates; it is our construction.
- **L4a, design-temperature normalisation.** m̂_h = κ / (T̂_h − T_design). A heat pump is sized for the heat load at the
  external design temperature [10, 11], and in a degree-day (balance-temperature) model the load rises linearly below the
  balance temperature [9]. A unit running at a share κ of its peak electrical draw at T_design then has a slope per unit of
  capacity of κ / (T_h − T_design). κ is one number, taken from the pilot: κ = m_h(pilot) · (T_h(pilot) − T_design). The
  normalisation as a transfer parameter is **our construction** (noted for 07 in `iterations/07-transfer-notes.md`); [9–11]
  support its ingredients, not the estimator. T_design is one value per pool (CH −8 °C, an assumption since 02a; GB −3 °C,
  CIBSE Guide A via the MCS Heat Load Calculator [10], a London value used nationally, 05a R7).
- **L4b, regularised regression of log m_h.** Ridge regression [8] of log m_h on standardised aggregate covariates (T̂_h,
  T̂_h − T_design, r̂, climate statistics of the station temperature); the penalty is chosen on household-disjoint inner folds.
- **Cross-fitting.** The residual's training targets use an m̂_h that was fitted without the households of the substation
  (inner substations: the other folds; train substations: train substations that share no HP household with it), as 03b
  Task 3 does for the pilot. Fitting a nuisance quantity out of sample before the second stage is the cross-fitting idea of
  [7]; we use it for prediction, not for inference, and claim no property of [7].

## Ensembles: L5
- **L5a, plain average** of the families' L4 predictions: the simplest combination, no learned weight.
- **L5b, gated combination.** Weights are learned on out-of-fold inner-CV predictions, which is stacked generalisation [12];
  the weights are non-negative least squares [14], as in stacked regressions [13]. Solver: `scipy.optimize.lsq_linear` with a lower
  bound of 0 (bounded-variable least squares; its reference, Stark and Parker 1995, was not retrieved: **UNVERIFIED**), because
  scipy 1.14's `nnls` fails on proportional columns and the families' predictions are close to that.
  The weights depend on the input through a gate, as in mixtures of experts [15]; our gate is a hard partition on one
  identifiable, label-free scalar (r̂ = ŝ / P_base(net)), not a learned soft gate, so [15] is the idea and not the algorithm.
  The bin edges are chosen among fixed quantiles of r̂ by household-grouped cross-validation on the out-of-fold predictions;
  the gate takes the fewest edges whose error is within 1 % (relative) of the lowest one (a parsimony rule of ours, fixed
  before any 06 run).

## Comparison rule
Paired per-seed differences with a seed-count threshold and a minimum effect (≥ 8 of 10 seeds and median ≤ −1 pp), as in
03a. It is a pre-registered decision rule, not a significance test; no reference is claimed.

## References
1. Willard, J., Jia, X., Xu, S., Steinbach, M., Kumar, V. (2023). Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems. *ACM Computing Surveys* 55(4), 1–37. doi:10.1145/3514228
2. Karniadakis, G. E., Kevrekidis, I. G., Lu, L., Perdikaris, P., Wang, S., Yang, L. (2021). Physics-informed machine learning. *Nature Reviews Physics* 3(6), 422–440. doi:10.1038/s42254-021-00314-5
3. von Rueden, L., Mayer, S., Beckh, K., Georgiev, B., Giesselbach, S., Heese, R., Kirsch, B., Walczak, M., et al. (2021, early access). Informed Machine Learning – A Taxonomy and Survey of Integrating Prior Knowledge into Learning Systems. *IEEE Transactions on Knowledge and Data Engineering*. doi:10.1109/TKDE.2021.3079836 (the Crossref record has no volume or pages and I retrieved the first eight authors only; issue data **UNVERIFIED**)
4. Psichogios, D. C., Ungar, L. H. (1992). A hybrid neural network-first principles approach to process modeling. *AIChE Journal* 38(10), 1499–1511. doi:10.1002/aic.690381003
5. Thompson, M. L., Kramer, M. A. (1994). Modeling chemical processes using prior knowledge and neural networks. *AIChE Journal* 40(8), 1328–1340. doi:10.1002/aic.690400806
6. von Stosch, M., Oliveira, R., Peres, J., Feyo de Azevedo, S. (2014). Hybrid semi-parametric modeling in process systems engineering: Past, present and future. *Computers & Chemical Engineering* 60, 86–101. doi:10.1016/j.compchemeng.2013.08.008
7. Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., Robins, J. (2018). Double/debiased machine learning for treatment and structural parameters. *The Econometrics Journal* 21(1), C1–C68. doi:10.1111/ectj.12097
8. Hoerl, A. E., Kennard, R. W. (1970). Ridge Regression: Biased Estimation for Nonorthogonal Problems. *Technometrics* 12(1), 55–67. doi:10.1080/00401706.1970.10488634
9. Fels, M. F. (1986). PRISM: An introduction. *Energy and Buildings* 9(1–2), 5–18. doi:10.1016/0378-7788(86)90003-4
10. MCS (n.d.). *MCS Heat Load Calculator, reference sources: design conditions* (external design temperature from CIBSE Guide A, 2015, Table 2.5). https://heatloadcalculator.mcscertified.com/docs/reference-sources/design-conditions (retrieved 30 Sep 2026 in 05a; not retrieved again). Underlying CIBSE Guide A (2015): not obtained, **UNVERIFIED** beyond this page.
11. EN 12831-1:2017, *Energy performance of buildings – Method for calculation of the design heat load – Part 1: Space heating load*, and MCS MIS 3005 (heat-pump design standard). **UNVERIFIED**: neither standard was obtained; titles from memory.
12. Wolpert, D. H. (1992). Stacked generalization. *Neural Networks* 5(2), 241–259. doi:10.1016/S0893-6080(05)80023-1
13. Breiman, L. (1996). Stacked regressions. *Machine Learning* 24(1), 49–64. doi:10.1007/BF00117832
14. Lawson, C. L., Hanson, R. J. (1995). *Solving Least Squares Problems*. SIAM (Classics in Applied Mathematics). doi:10.1137/1.9781611971217
15. Jacobs, R. A., Jordan, M. I., Nowlan, S. J., Hinton, G. E. (1991). Adaptive Mixtures of Local Experts. *Neural Computation* 3(1), 79–87. doi:10.1162/neco.1991.3.1.79
