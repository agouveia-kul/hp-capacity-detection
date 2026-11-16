# Iteration 07: method basis (hard rule 11)

Metadata of every DOI below was retrieved from the Crossref REST API (`api.crossref.org/works/<doi>`) on 2026-11-16:
title, authors, year and venue match the entry. "Content" notes say whether the claim used here was re-read in the source
(it was not for any entry: no full text was opened). Scite was not available (no plan), so no retraction check was run
beyond Crossref.

## 1. Transfer evaluation under dataset shift
07 trains on one pool and scores on another, with the models, the selection and every calibration constant fixed on the
source. This is evaluation under dataset shift (covariate shift: climate, building stock, filler households; label shift: the
label definitions of the pools differ, which `HL` and the factor c address).
1. Quiñonero-Candela, J., Sugiyama, M., Schwaighofer, A., Lawrence, N. D. (eds.) (2009). *Dataset Shift in Machine Learning*.
   MIT Press. doi:10.7551/mitpress/9780262170055.001.0001 (Crossref "issued" 2008). Content (definitions of covariate and
   prior-probability shift): from memory, not re-read.
2. Moreno-Torres, J. G., Raeder, T., Alaiz-Rodríguez, R., Chawla, N. V., Herrera, F. (2012). A unifying view on dataset shift in
   classification. *Pattern Recognition* 45(1), 521–530. doi:10.1016/j.patcog.2011.06.019. Content (taxonomy of covariate,
   prior and concept shift): from memory, not re-read.
3. Kelly, J., Knottenbelt, W. (2015). Neural NILM: deep neural networks applied to energy disaggregation. *BuildSys '15*,
   55–64. doi:10.1145/2821650.2821672. Precedent in load analytics for scoring on households unseen in training; content from
   memory, not re-read.
4. D'Incecco, M., Squartini, S., Zhong, M. (2020). Transfer learning for non-intrusive load monitoring. *IEEE Transactions on
   Smart Grid* 11(2), 1419–1429. doi:10.1109/TSG.2019.2938068. Precedent for training on one smart-meter dataset and testing
   on another; content from memory, not re-read.
- Koh, P. W. et al. (2021), *WILDS: a benchmark of in-the-wild distribution shifts* (ICML): **UNVERIFIED** (no Crossref match;
  not retrieved). Not used.
- **No precedent retrieved** for frozen-model transfer of an aggregate-level heat-pump capacity estimator between countries.

## 2. Label harmonisation across measurement definitions
The pools measure `HP_Peak` on different channels and resolutions (CH: 15-min HP submeter; GB: 30-min whole heating system,
immersion included). `HL` maps both to one definition (30 min, HP unit only), and the factor c maps a model's native label to
`HL` with source labels only.
5. Fortier, I., Raina, P., Van den Heuvel, E. R., Griffith, L. E., Craig, C., Saliba, M., et al. (2016, online). Maelstrom
   Research guidelines for rigorous retrospective data harmonization. *International Journal of Epidemiology*, dyw075.
   doi:10.1093/ije/dyw075 (the Crossref record carries no volume or pages). General guideline for harmonising variables
   measured differently across studies; content from memory, not re-read.
- **No precedent retrieved** for harmonising heat-pump peak labels across submeter definitions; the HL rule is this
  iteration's (07 brief, from the 05a D5 diagnosis).
- Source for the GB immersion channel: UKDS SN 9050 data dictionary on disk
  (`data/_paperb/raw/eoh/mrdoc/excel/9050_eoh_public_datasets_data_dictionary_v2-0.xlsx`, sheet "Performance Summary",
  `IH_Energy_Consumed_selected_window`: "Where no immersion heater is present then the datapoint is left blank"). 07 reads a
  home without any immersion reading as a home without an immersion heater (immersion 0); the property table's
  `MCS_Immersion` is the cross-check (`label_harmonisation.md`).

## 3. Max-normalised MAE (nMAE)
nMAE = mean|ŷ − y| / max(y) × 100 % per evaluation set (DECISIONS 2026-11-16).
6. Madsen, H., Pinson, P., Kariniotakis, G., Nielsen, H. A., Nielsen, T. S. (2005). Standardizing the performance evaluation of
   short-term wind power prediction models. *Wind Engineering* 29(6), 475–489. doi:10.1260/030952405776234599. Precedent for
   an MAE normalised by a capacity (installed capacity). Our normaliser is the evaluation set's largest label, not an installed
   capacity: analogous, not identical. Content from memory, not re-read.
7. Hyndman, R. J., Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of
   Forecasting* 22(4), 679–688. doi:10.1016/j.ijforecast.2006.03.001. Scale-dependent vs scaled error measures; content from
   memory, not re-read.

## 4. Design temperatures (L4a, target metadata)
- GB −3 °C: MCS Heat Load Calculator, design conditions page (CIBSE Guide A 2015, Table 2.5), retrieved in 05a, cited in
  `results/iter06_hybrid_ladder/method_basis.md` [10]; CIBSE Guide A itself **UNVERIFIED**; a London value, site spread
  −1.5 to −5.9 °C **UNVERIFIED** (07 notes).
- CH −8 °C: an assumption since 02a with **no retrieved source** (a SIA climate-data norm would be the place to check; not
  obtained). **UNVERIFIED.**
