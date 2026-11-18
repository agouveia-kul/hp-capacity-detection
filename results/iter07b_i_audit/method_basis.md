# 07b-i — method basis (references for label mappings, registry quality and data sources)

Checked on 2026-11-18 by resolving each DOI through doi.org content negotiation (title, authors, year and venue
returned by the registry; script in the session scratchpad, not committed). A reference that I did not retrieve is
marked **UNVERIFIED**. Nothing here was used to choose a candidate after looking at any estimator: no estimator was
computed.

## Datasets (candidates and source pools)

| key | reference | status |
|---|---|---|
| FeederBW | Treutlein, M., Bothe, P., Schmidt, M., Hahn, R., Neumann, O., Gielnik, [initial not retrieved], Mikut, R., Hagenmeyer, V. (2026). *Real-world energy data of 200 feeders from low-voltage grids with metadata in Germany over two years.* Scientific Data. doi:10.1038/s41597-026-08152-9. Data: Zenodo doi:10.5281/zenodo.19550073; preprint doi:10.48550/arXiv.2602.03521 | checked (DOI resolves; title, authors, venue). **How `heat_pumps_kW` is registered (connection request vs nameplate, electrical vs thermal) was not found in the abstract page; read the paper's metadata section before 07b: UNVERIFIED** |
| Fluvius 2024 sample (P6269) | Fluvius Open Data, *Verbruiksprofielen digitale meters elektriciteit: kwartierwaarden voor een volledig jaar* (dataset `1_50-verbruiksprofielen-dm-elek-kwartierwaarden-voor-een-volledig-jaar`), https://opendata.fluvius.be/explore/dataset/1_50-verbruiksprofielen-dm-elek-kwartierwaarden-voor-een-volledig-jaar/ | page retrieved: 2,400 residential meters, 8 categories × 300 (HP / EV / PV combinations), meters with a full year of quarter-hour reads requested by the user; PV scope = injection in all 12 months, no-PV scope = no injection all year. **Year, region and licence text not stated on the page (licence page not retrieved): UNVERIFIED.** The on-disk files say 2024 |
| Fluvius 2022 (`15minuteFluvius.csv`) | earlier release of the same Fluvius open-data series (assumed from the identical schema) | **UNVERIFIED** |
| BE home monitoring (`95951bd3-*`, `26b72e88-*`, `DER_capacity_by_installation.csv`) | no documentation on disk; the metadata carry `c4a:` keys | **provenance and licence unknown — Alex to state** |
| UKPN LV feeder + LCT | UK Power Networks Open Data Portal, *Smart Meter Consumption – LV Feeder* and *Low Carbon Technologies (secondary)*, https://ukpowernetworks.opendatasoft.com | portal page needs a login; **period kept online, aggregation rule and licence UNVERIFIED** |
| NEEA HEMS v9.2 | Northwest Energy Efficiency Alliance, End-Use Load Research (HEMS), https://neea.org/data/nw-end-use-load-research-project (as cited in Paper A `DATA.md`) | link not re-fetched: **UNVERIFIED**; on-disk README states data run to 06/2025 |
| HEAPO | Brudermüller, T., Fleisch, E., González Vayá, M., Staake, T. (2025). *HEAPO – An Open Dataset for Heat Pump Optimization with Smart Electricity Meter Data and On-Site Inspection Protocols.* ETH Zurich / Zenodo. doi:10.5281/zenodo.15056919 | checked |
| WPuQ | Schlemminger, M., Ohrdes, T., Schneider, E., Knoop, M. (2022). *Dataset on electrical single-family house and heat pump load profiles in Germany.* Scientific Data. doi:10.1038/s41597-022-01156-1; data doi:10.5281/zenodo.5642902 | checked |
| RHPP | Lowe, R., Department of Energy and Climate Change (2017). *Renewable Heat Premium Payment Scheme: Heat Pump Monitoring: Cleaned Data, 2013–2015.* UK Data Service, SN 8151. doi:10.5255/UKDA-SN-8151-1 | checked |
| LCL | Strbac, G., Tindemans, S., Woolf, M., Bilton, M., Carmichael, R., Schofield, J., … (2024). *Low Carbon London Project: Data from the Dynamic Time-of-Use Electricity Pricing Trial, 2013.* UK Data Service, SN 7857. doi:10.5255/UKDA-SN-7857-2 | checked |
| EoH | Energy Systems Catapult (2024). *Electrification of Heat Demonstration Project: Heat Pump Performance Cleansed Data, 2020–2023.* UK Data Service, SN 9050. doi:10.5255/UKDA-SN-9050-2 | checked |

## Label mappings to `HL` (peak vs rated or registered power)

| mapping | basis | status |
|---|---|---|
| nameplate electric power → observed 99.9th-pct peak (CH) | HEAPO protocols (`HeatPump_Installation_Normpoint_ElectricPower`) vs B\* `HP_Peak`, household level; computed here on source data only (`facts.md`) | own data; no literature precedent retrieved for this ratio |
| rated (thermal) size → electrical peak (GB) | EoH `HP_Size_kW` vs robust peak: 0.48 (04 `usability.md`); RHPP installer capacity vs peak: 0.47 (04) | own data (04) |
| GB field-trial heat-pump peak loads | Love, J., Smith, A. Z. P., Watson, S., Oikonomou, E., Summerfield, A., … (2017). *The addition of heat pump electricity load profiles to GB electricity demand: Evidence from a heat pump field trial.* Applied Energy. doi:10.1016/j.apenergy.2017.07.026 | checked (DOI resolves; title, authors, venue). Content on peak vs capacity not re-read here: cite only as the RHPP-based load-profile reference |
| registry kW (DSO connection data) → installed electrical power | no retrieved reference on the quality of DSO heat-pump registries (FeederBW, UKPN LCT) | **no precedent found; UNVERIFIED** |
| HP flag / count only (Fluvius, UKPN connections) → capacity | needs a per-HP peak from the source (transferred); no precedent retrieved | **no precedent found** |

A wrong DOI from memory (10.1016/j.apenergy.2017.04.083, which resolves to a different paper) was caught by the check
and is not used.
