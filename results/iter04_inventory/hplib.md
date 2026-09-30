# Iteration 04 — hplib capability check

## 1. Version and scope (from the installed code, `.venv/Lib/site-packages/hplib/hplib.py`, and its database CSVs)

- **Version:** hplib **1.9** (`pip show`; matches the `requirements.txt` pin). MIT licence (code); database CC BY 4.0. Cite Tjaden, Hoops & Rösken, Zenodo, doi:10.5281/zenodo.5521597 (from the package README).
- **What it models (steady-state performance map):** for a given primary inlet T_in (air, brine or water), secondary outlet T_out = T_in,secondary + 5 K, and T_amb:
  - `P_el = P_el,ref · (p1·T_in + p2·T_out + p3 + p4·T_amb)`, `COP = p1'·T_in + p2'·T_out + p3' + p4'·T_amb`, `P_th = P_el · COP`, `m_dot = P_th / (5 K · c_p)`. For air-source units T_amb = T_in.
  - P_th is the **full-load output at those temperatures**, not a demand-following output. The only part-load logic: for regulated groups P_el is floored at 25 % of P_el at (−7 °C, T_out); if a user-given `p_th_min` exceeds the output, P_el is raised to reach it (inverter) or, if that is not possible, a resistance rod adds P_th,ref at COP 1. When COP ≤ 1 the unit switches to the rod (P_el = P_th = P_th,ref).
  - **Cooling (mode 2):** only group 1 (regulated air/water); EER map, T_in floored at 25 °C.
  - **Helpers:** `HeatingSystem.calc_heating_dist_temp` (weather-compensated flow/return from the daily mean outdoor temperature, DIN V 4701-10; defaults 35/28 °C floor heating, 55/45 low-temperature radiators, 70/55 radiators) and `calc_brine_temp` (soil/brine temperature from the daily mean, Fraunhofer ISE WP-Monitor fit).
- **Parameter database:** `hplib_database.csv`, 511 rows = 505 Keymark models (fitted to Heat Pump Keymark certificate PDFs downloaded 2021-03-12; certification dates 2016–2021; 30 manufacturers per the README) + 6 **Generic** rows. By group: 1 air/water regulated **367**, 2 brine/water regulated **54**, 3 water/water regulated **1** (Generic only; its fit parameters are NaN), 4 air/water on-off **24**, 5 brine/water on-off **54**, 6 water/water on-off **11** (counts include the Generic row). `hplib_database_all.csv` has 3 225 certificate models mapped to these fits. Reference point P_th,ref 2.4–69.9 kW (median 8.0 kW).
- **Generic HP by group and rated power:** `get_parameters('Generic', group_id, t_in, t_out, p_th)` rescales the group-average fit so that P_th equals `p_th` at (t_in, t_out) (least squares on P_th,ref). The **COP map does not depend on the rated power**, so a generic HP converts heat to electricity independently of its size; size only enters the capacity limit and the 25 % floor.
- **Documented fit errors** (MAPE of the Keymark fits, computed from the database columns; the README quotes 16.3 / 9.8 / 19.7 % and swaps the COP and P_th labels): all models P_el 16.3 %, COP 9.9 %, P_th 19.7 % (mean). Group 1: P_el 19.5 %, COP 12.1 %, P_th 23.5 %; group 2: 17.7 / 4.2 / 19.7 %; groups 4–6: ≤ 2.5 % P_el, ≤ 5.4 % COP, ≤ 5.8 % P_th. These are **lab-certificate fit errors**, not field errors.
- **Not modelled** (confirmed in the code): building heat demand and thermal mass; controls (thermostat, weather compensation beyond the helper, setbacks); compressor **cycling** and minimum part load beyond the 25 % floor (no cycling losses); **defrost** (no humidity input, no penalty); **DHW** as a separate operating mode (T_out can be set higher, but there is no tank, schedule or legionella cycle); **back-up / immersion heater** only as the COP ≤ 1 or `p_th_min` rule; **blocking / ripple-control** windows; standby power; circulation pumps; dynamics (start-up, ramping).

## 2. Conversion-step validation on real data (EoH; `scripts/audit/hplib_check.py` → `hplib_check.md`, `hplib_spf.csv`, `metrics.csv`, `figures/hplib_conversion.png`)

Setup: 50 EoH air-source homes (seed 0; hybrids and GSHP excluded; drawn among the homes with a complete 2021/22 season of whole-system electricity **and** heat output), 348 403 valid 30-min bins. Measured HP electricity = whole system − immersion − back-up − circulation pump (EoH definition). Prediction P̂ = Q_meas / COP(T_ext, T_flow), where T_flow is the DHW flow in DHW bins, else the SH flow, else return + 5 K. If Q exceeds hplib's full-load output, the excess is supplied at COP 1. **Rated power is not on disk**, so the generic HP is sized to the home's 99.5th-percentile 30-min heat output at A2/W35 (assumption).

| hplib generic | 30-min WAPE | 30-min bias | daily WAPE | daily bias | daily WAPE after one global rescale (in-sample) | SPF bias, median [10–90 %] |
|---|---|---|---|---|---|---|
| group 1, regulated air/water | 29.0 % | −19.6 % | 21.7 % | −19.7 % | 13.8 % | **+27.5 %** [+10.9, +43.1] (measured median SPF 2.98, predicted 3.81) |
| group 4, on-off air/water | 22.2 % | −17.4 % | 18.8 % | −17.5 % | 11.6 % | +22.2 % [+7.8, +36.6] |

By outdoor temperature (group 1, daily bias): −22.5 % at (−2, 2] °C, −20.8 % at (2, 6], −17.1 % at (6, 10], −20.3 % at (10, 14]. At 30 min: −15.7 % below −2 °C (1.3 % of energy), −32.8 % above 14 °C.

**Where it fails**
- **Systematic optimism:** the generic Keymark COP is about 20 % too high for these field installations at every temperature (group 1). Most of the daily error is this level bias: after one scalar rescale the daily WAPE falls from 21.7 % to 13.8 %. This agrees with the known gap between certificate and field SPF.
- **Standby / idle (Q ≈ 0):** 34 % of the bins and 2.3 % of HP electricity. hplib predicts 0, so the error there is 100 %.
- **DHW periods:** 21 % of energy; WAPE 33 % vs 26 % in space heating, bias −16 %. hplib has no tank or DHW mode; T_out is only the DHW flow temperature.
- **Back-up active:** 1.2 % of energy (WAPE 33 %). The immersion/back-up draw is not part of P̂ here, because it is metered separately and excluded from P.
- **Cold days / defrost:** not identifiable in 2021/22. Only 1.3 % of energy fell below −2 °C, and the bias there (−16 %) is *smaller*, not larger. The defrost band (≈ −5…+5 °C, humid) cannot be separated without humidity data. The cold 2022/23 winter (Dec 2022) would be the better test.
- **Capacity limit:** group 1 sized at the 99.5th pct is exceeded in 6.0 % of bins (group 4: 0.5 %), so the rated-power proxy matters for peaks.
- RHPP not run: it has no outdoor-air temperature (T_in is refrigerant/ground-loop), so only a daily check against HadCET would be possible. It is left for the simulator's calibration stage.

**Implication for the simulator:** hplib's generic COP map cannot be used as-is. It needs (i) a per-population COP scale (≈ 0.80–0.85, to be calibrated and validated out-of-sample), (ii) a standby term and (iii) explicit DHW and cycling layers. The conversion error after rescaling (daily WAPE ≈ 12–14 %) is the floor for any simulator built on it.
