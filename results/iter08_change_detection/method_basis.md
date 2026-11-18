# Iteration 08 — method basis (hard rule 11)

Checked = the record was retrieved from the Crossref API (`api.crossref.org/works/<DOI>`) on 2026-11-18 and its title,
authors, year and venue match the line below. UNVERIFIED = not retrieved; do not cite it as checked.

## 1. Detection by a threshold on a null distribution (τ = a quantile of Δ̂ on null feeders)
The rule "flag if Δ̂ > τ, τ = the 95th percentile of Δ̂ on null feeders" is a one-sided test at a nominal 5 % false-alarm
(type I) rate whose critical value is estimated from an empirical null sample instead of a parametric null.

| reference | status | what it supports |
|---|---|---|
| Neyman, J., Pearson, E. S. (1933). On the problem of the most efficient tests of statistical hypotheses. *Philosophical Transactions of the Royal Society A* 231, 289–337. doi:10.1098/rsta.1933.0009 | checked | The test is set by fixing the false-alarm (size) level first and maximising power at that level; power at fixed size is the comparison quantity of rule D. |
| Bates, S., Candès, E., Lei, L., Romano, Y., Sesia, M. (2023). Testing for outliers with conformal p-values. *The Annals of Statistics* 51, 149–178. doi:10.1214/22-AOS2244 | checked | Calibrating a detection threshold on a held-out set of null ("inlier") scores and applying it to new units gives a marginally valid false-alarm rate when calibration and test units are exchangeable. This is the basis for the two-fold cross-calibration (τ from one household-disjoint half, scored on the other). |
| Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association* 113, 1094–1111. doi:10.1080/01621459.2017.1307116 | checked | Split (held-out) calibration of an empirical quantile; the half that sets the quantile is never the half that is scored. |
| Basseville, M., Nikiforov, I. V. (1993). *Detection of Abrupt Changes: Theory and Application.* Prentice Hall. | partly checked: no DOI for the book; its existence, authors and title are confirmed by a book review indexed in Crossref (Peach, 1995, *JRSS D*, doi:10.2307/2983416); edition, ISBN and pages UNVERIFIED | Standard reference for change detection framed as a test with a false-alarm rate and a detection probability. 08 is a two-sample (before/after) change test, not sequential detection: detection delay is out of scope (brief). |
| Lehmann, E. L., Romano, J. P. (2005). *Testing Statistical Hypotheses*, 3rd ed. Springer Texts in Statistics. doi:10.1007/0-387-27605-X | partly checked: the Crossref record (title, series, Springer, 2005, ISBN 9780387988641) was retrieved but lists no authors; authors and edition UNVERIFIED | Textbook definitions of size, power and power curves (power vs effect size). |

## 2. Minimum detectable change and power at a fixed false-alarm rate
MDC in 08 = the smallest uptake Δp at which the power of the fixed-τ test reaches 0.8. This is the operational form of a
"minimum detectable change" read off an empirical power curve; it is not computed from a parametric formula.

| reference | status | what it supports |
|---|---|---|
| de Vet, H. C. W., Terwee, C. B., Ostelo, R. W. J. G., Beckerman, H., Knol, D. L., Bouter, L. M. (2006). Minimal changes in health status questionnaires: distinction between minimally detectable change and minimally important change. *Health and Quality of Life Outcomes* 4, 54. doi:10.1186/1477-7525-4-54 | checked | The minimally detectable change of a measurement instrument: the smallest change between two measurements of the same unit with the same instrument that exceeds its measurement error. 08's setting (the same feeder, the same estimator, two years) is this one; the paper adapts the term and states that the threshold here is an empirical null quantile, not 1.96·√2·SEM. Clinical measurement, not energy: an analogy, stated as such. |
| Granderson, J., Touzani, S., Custodio, C., Sohn, M. D., Jump, D., Fernandes, S. (2016). Accuracy of automated measurement and verification (M&V) techniques for energy savings in commercial buildings. *Applied Energy* 173, 296–308. doi:10.1016/j.apenergy.2016.04.049 | checked | Energy precedent for estimating a change (savings) as the difference between a model's estimates of two periods of the same building and judging it against the model's error; it supports differencing an estimator across periods, not the detection rule. |

## 3. No precedent found
- No precedent was found for detecting a change in **heat-pump capacity** on an LV feeder from aggregated net load and
  temperature by differencing a capacity estimator between two heating years. 08's design (paired synthetic feeders with a
  controlled uptake, household-disjoint halves for threshold calibration) is new and is labelled so in the paper.
- No search tool with full coverage was used (scite needs a paid plan; the Crossref API checks a known reference, it does not
  search for precedents). The "no precedent" statement is therefore a statement about the references checked here.
