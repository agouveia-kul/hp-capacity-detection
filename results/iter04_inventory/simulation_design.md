# Iteration 04 — HP-profile simulator: design proposal (not implemented)

**Purpose.** Produce realistic HP electricity profiles with a *known* capacity, for arbitrary pool sizes, for training augmentation and controlled experiments only (§E). All headline tests stay on real households.

## A. Demand source

| option | pros | cons | verdict |
|---|---|---|---|
| **(i) Measured heat demand** of monitored homes (EoH heat meters: 608 homes with a complete season; RHPP H_hp: 169, no outdoor temperature), device resimulated | real occupancy, DHW timing, setbacks, emitter and control behaviour; weather is the home's own | limited to monitored homes and their climates (GB 2021–23); heat output is censored by the installed HP (a resized device cannot deliver more than the measured Q without an assumption) | **preferred** |
| (ii) Building model (ISO 13790 5R1C with TABULA/EPISCOPE archetypes [Loga 2016]) + occupancy and DHW profiles | any population size, climate and stock; oversizing is fully controllable | 5R1C gets seasonal energy right but is weaker on dynamics and peaks [Vivian 2017; Bruno 2016]; archetype models reach CV(RMSE) ≈ 0.3 on hourly heat [Heidenthaler 2023]; behaviour is synthetic | extrapolation arm only (climate / stock outside GB) |

With (i), "new" households come from **re-pairing**: EoH heat-demand trace × resampled device parameters (sizing, curve, DHW set point, controls). The number of distinct *behaviours* stays at the number of monitored homes (≈ 430 non-hybrid per season), so (i) augments device diversity, not behavioural diversity. This must be stated wherever it is used.

## B. Device and operation layers on top of hplib (per home; 30 min, optionally 2 min for cycling)
1. **Sizing:** P_rated = design heat load × oversizing factor f ~ LogNormal(μ_f, σ_f). Design load comes from the measured Q at the local design temperature (hockey-stick extrapolation of daily Q). f drives m_h (the SF slope) and is the key knob for RQ3 transfer. RHPP gives an empirical check (robust peak / installer capacity median 0.47).
2. **Heating curve:** T_flow = f(T_out) via `HeatingSystem.calc_heating_dist_temp`, with a slope and design flow temperature drawn per home. Where measured (EoH), use the measured flow instead.
3. **Capacity limit + back-up/immersion:** Q > P_th,max(T_out, T_flow) → the resistance heater covers the excess at COP 1. The back-up share is calibrated (EoH median 1.7 % of HP-system energy; > 5 % in 18 % of homes).
4. **Minimum part load / cycling:** below a minimum modulation (e.g. 30 % of P_rated) the unit cycles. At 30 min this is an energy penalty (degradation coefficient C_d on P_el) plus a stochastic on/off pattern when 2-min output is needed.
5. **Defrost:** P_el multiplier in the −5…+5 °C band for air source [Rogeau 2024 models part load, defrost and weather compensation jointly]. Not identifiable from EoH 2021/22 (Task 4), so the prior must come from the literature or the cold 2022/23 season.
6. **DHW:** a separate mode at the DHW sink temperature, with schedules taken from the measured DHW-mode bins (EoH `T_flow_dhw`) or from standard profiles for option (ii).
7. **Blocking / ripple control (optional):** CH/DE windows (e.g. 3 × 2 h/day) with a rebound. Needed only to mimic B\* / FeederBW regimes.
8. **COP scale and standby (added after Task 4):** a population COP scale k_COP (field vs Keymark; Task 4 suggests ≈ 0.80–0.85) and a standby draw (EoH: idle bins hold 2.3 % of HP electricity).

## C. Calibration (fit population-level parameter distributions on a *calibration* set of real homes)
- **Parameters:** (μ_f, σ_f), heating-curve slope, balance temperature, DHW share, back-up share, k_COP, standby, cycling C_d, defrost multiplier.
- **Summary statistics** (all quantities the paper uses): the per-household distribution of HP hockey-stick (s_h, T_h, P_base) and of the net-load fit; SF(T) and m_h; load-duration curve shape; **ADMD(n)**, the coincident peak per household vs group size [Love 2017 report 1.7 kW/site ADMD for RHPP and its dependence on n]; the ratio HP_Peak / s_h.
- **Method:** simulation-based inference / ABC-SMC on these statistics. Baseline: moment matching (method of simulated moments). Seeded, with the prior ranges recorded. Bayesian calibration practice for building models is reviewed in [Chong & Menberg 2018, *unverified here*].

## D. Statistical validation on a held-out real population (never the calibration homes)
Split EoH homes by weather-station group (calibration: G001 + minor groups; validation: G002, G009 …), and validate additionally on the other season. **Thresholds are fixed now and not changed later:**

| level | check | pass if |
|---|---|---|
| Marginal | per T-bin two-sample KS / AD and Wasserstein distance of 30-min and daily HP power | Wasserstein ≤ 10 % of the real mean in every bin with ≥ 5 % of energy; KS reported (large n makes p-values uninformative) |
| Temporal | ACF (lags 1–48), mean daily profile by day type × T bin, ramp-rate distribution | ACF within the real between-home 5–95 % band; profile NRMSE ≤ 15 % |
| Multivariate | MMD / energy distance on daily profile vectors [Gretton 2012, *unverified*]; **classifier two-sample test** (gradient boosting, real vs simulated days, grouped CV by home) [Lopez-Paz & Oquab 2017, *unverified*; a classifier-based realism metric is used in Hu 2022] | C2ST AUC ≤ 0.65 (0.5 = indistinguishable); MMD permutation test reported |
| **Aggregate** (most important) | real vs simulated SF(T), m_h, ADMD(n) for n = 1…120, distribution of feeder-level s_h and HP_Peak | m_h within ± 5 %; ADMD(n) within ± 10 % for n ≥ 10; KS on feeder s_h / HP_Peak not rejected at 5 % over 200 draws |
| **Downstream (TSTR vs TRTR)** [Esteban 2017, *unverified*] | capacity task (protocol v1, B\*-style substations on the validation homes): train on simulated / test on real vs train on real / test on real; also train on real + simulated | TSTR WAPE ≤ TRTR + 2 pp (median over seeds) **and** real + simulated does not raise real-test WAPE (paired, ≥ 12/20 seeds) |

The simulator is "fit for purpose" only if the aggregate and downstream levels pass; marginal and temporal failures are reported but can be tolerated.

## E. Intended use
Training augmentation, and controlled experiments: (1) vary oversizing and climate to study m_h transfer (RQ3); (2) fill the high-penetration, large-feeder cells that real pools cannot reach (B\* p = 1 caps at 10 dwellings; GB-EoH at 20). **Every headline number stays on real households.**

## F. Effort, risk and recommendation
- **Effort:** layers B1–B8 ≈ 300–400 logic lines (vectorised hplib; about 1 s per 400-home season at 30 min); calibration ≈ 150–250 lines, ABC-SMC ≈ 10⁴ population simulations ≈ 3–6 h; validation suite ≈ 250 lines, ≈ 1 h plus one TSTR run (≈ one 03b-style run). Total ≈ 2 iterations (code + runs), under the 300-line budget only if split.
- **Main realism risks:** (a) the conversion floor: generic hplib under-predicts HP electricity by ≈ 20 % (Task 4, SPF +22 to +28 %), and even after a global rescale the daily WAPE is 12–14 %; (b) behavioural diversity is capped at the monitored homes under option (i); (c) defrost and cycling priors are unidentifiable from the data on disk; (d) heat output is censored by the installed HP, so large oversizing changes are extrapolation; (e) circularity if the simulator's summary statistics include the targets it is later scored on (mitigated by the held-out split).
- **Recommendation: conditional go, option (i), after the GB-EoH learning curve.** Task 4 shows the conversion can be calibrated (the error is mostly one level bias), so the device layer is viable. But GB-EoH already gives ≈ 5× B\*'s real households. If the extended learning curve is flat from 62 to 300 households, augmentation is not needed for the N question, and the simulator should be built only for the controlled m_h / oversizing experiments (E1). **No-go for option (ii)** until a GB or CH archetype set is validated against EoH heat.

## References (retrieved in this session unless marked)
- Love, J. et al. (2017). The addition of heat pump electricity load profiles to GB electricity demand: evidence from a heat pump field trial. *Applied Energy*. [link](https://consensus.app/papers/details/e4d58f25fc9c55c78acd29cd23fe5312/)
- Agrawal, R. et al. (2026). Electricity demand in electrified UK homes: the role of heat pumps, seasons, and property type. *Energy and Buildings* (SERL + EoH, validated against an SSEN substation). [link](https://consensus.app/papers/details/a1b3cc5168d059b99faaa9a30a2724e7/)
- Watson, S. et al. (2023). Predicting future GB heat pump electricity demand. *Energy and Buildings* (statistical model on > 550 RHPP heat pumps). [link](https://consensus.app/papers/details/ba652770fcb852e78c8d6ff90570ed75/)
- Rogeau, A. et al. (2024). A generic methodology for mapping the performance of various heat pump configurations considering part-load behavior. *Energy and Buildings*. [link](https://consensus.app/papers/details/4367f5f66ef65c21989c0f0db39a465c/)
- Loga, T. et al. (2016). TABULA building typologies in 20 European countries. *Energy and Buildings*. [link](https://consensus.app/papers/details/8607123f3d805ffd9a393fe04f6adda5/)
- Vivian, J. et al. (2017). An evaluation of the suitability of lumped-capacitance models … *Energy and Buildings*. [link](https://consensus.app/papers/details/d828067d8dcf5f92a627c208549f4c6f/)
- Bruno, R. et al. (2016). The prediction of thermal loads in building by means of the EN ISO 13790 dynamic model … *Energy Procedia*. [link](https://consensus.app/papers/details/89b5a60f99885993bfc28a475baf7322/)
- Heidenthaler, D. et al. (2023). Automated energy performance certificate based urban building energy modelling … *Energy*. [link](https://consensus.app/papers/details/01a3cf66c5cb5e80819576a0c762b886/)
- Hu, Y. et al. (2022). MultiLoad-GAN … *IEEE Trans. Smart Grid* (classifier-based realism and group-level statistics). [link](https://consensus.app/papers/details/8a91ac5425da5043b648a0eebc16d4e7/)
- Li, H. et al. (2019). The creation and validation of load time series for synthetic electric power systems. *IEEE Trans. Power Systems*. [link](https://consensus.app/papers/details/2d96845e63005d6584b128ad53c93167/)
- Tjaden, T., Hoops, H., Rösken, K. (2021). hplib. Zenodo, doi:10.5281/zenodo.5521597 (from the installed package README).
- *Unverified (not retrieved in this session; from memory, check before citing):* Lopez-Paz & Oquab (2017), "Revisiting classifier two-sample tests", ICLR; Gretton et al. (2012), "A kernel two-sample test", JMLR; Esteban, Hyland & Rätsch (2017), arXiv:1706.02633 (TSTR); Chong & Menberg (2018), Bayesian calibration of building energy models, *Energy and Buildings*. DOIs are omitted where not verified; the scite quota was exhausted this session.
