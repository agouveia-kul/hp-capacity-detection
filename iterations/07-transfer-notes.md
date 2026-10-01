# Notes for the iteration 07 brief (transfer, RQ3). Not a brief: read when 07 is written.

Collected so that they are not lost before the transfer iteration.

## Label definitions differ between pools (from the 05a D5 diagnosis, 2026-10-01)
- **B\* (CH):** `HP_Peak` comes from the **HP submeter**. Electric water heaters (EWH) sit in the home's **own non-HP load** (M9: in 13/26 Kaiser pairs and 28/57 HEAPO households). The own non-HP load of B\* HP homes has a temperature slope ≈ 0.018 kW/K, 3.3 × a filler's.
- **GB-EoH (GB):** `HP_Peak` comes from the **whole heating-system electricity**: compressor + backup + **immersion (DHW)** + pumps. Each HP dwelling's own non-HP load is a random LCL filler, so there is no co-located temperature-sensitive load.
- **Consequences for CH ↔ GB transfer:**
  - The same physical home would get a higher `HP_Peak` and a lower co-located non-HP slope under the GB definition than under the CH one.
  - Any model or m_h transferred between pools carries this definitional shift on top of the climate and population shifts.
- **What 07 must do:**
  - Report the size of the shift. Recompute B\* labels as HP + EWH where the EWH is identifiable, or report the EoH labels without immersion, using the immersion channel.
  - Run transfer under both harmonised definitions, and say which one the headline uses.
  - Keep `paperA_corr_own` (05b [A7]) in the transfer rows: it absorbs the co-located response through the pilot, so it may transfer better.

## Other items to carry into 07
- **RHPP:**
  - nameplate arm (installer capacity for 111 of 114 homes);
  - concurrent-filler validation of the analog-day mapping (RHPP + LCL 2013/14 concurrent vs analog-matched).

  Both need a temperature source for the RHPP sites.
- **FeederBW (DE)** real feeders, with registry labels.
- **Design-temperature normalisation of m_h** (m_h ≈ SF_design / (T_h − T_design)) as a transfer candidate. The GB design temperature (−3 °C, CIBSE London 99.6 %) is London-only; the site spread is −1.5 to −5.9 °C (not verified at source).
- **Learning m_h from covariates** (hierarchical / leave-one-population-out), and feeder-referenced features θ.
