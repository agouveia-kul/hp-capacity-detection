# Protocol v1: proposal for approval (iteration 01)

Machine-readable form: `configs/protocol_v1_proposal.yaml`. Every count below comes from `design_envelope.md` / `pool_inventory.md` (scripts in `scripts/audit/`). Nothing here is implemented yet.

**Binding facts.** At 15 min and >= 90 % coverage, the HP-submetered pool is **47 HEAPO households (cal2023; 23 at 8jB) + 24 Kaiser paired + 15 Kaiser single-family HP meters**. 8jB is bit-identical to KLO. HEAPO 15-min data stop on 2024-02-27, and Kaiser covers only cal2023-2024, so **cal2023 is the only year** with both HP members and clean fill. Adding cal2024 (option C) adds 2 households. The 25 % test pool holds **16 HP households at KLO** (4 at Hg). A 120-dwelling test substation can therefore reach at most p = 0.13, and p = 1.0 only at size <= 16.

**Recommendation: B\* for the main 15-min analysis, plus D as a daily arm.**

| | main 15-min arm (B\*) | daily arm (D) |
|---|---|---|
| HP members | HEAPO all stations (47) + Kaiser paired (24) + Kaiser SFH HP meters (15) | HEAPO daily HP or 15-min aggregated + Kaiser paired (71); count-only: HEAPO total-only + Kaiser `1_hp` in meter (1099 total) |
| fill | Kaiser clean dwellings (1306), any station | same |
| window | cal2023 | cal2023 and heating season 2023/24 |
| distinct HP households train / test (seed 42) | **64 / 22** | 55 / 16 submetered |
| targets in | HP_Peak, HP_CoincPeak, HP_Count, s_h, r, P_design | HP_Count (1099), s_h, r, P_design (71) |
| targets out | HP_Nameplate_el (1 household with nameplate) | HP_Peak, HP_CoincPeak (need 15 min); HP_Nameplate_el (37 households, max 14 per station-window) -> household-level descriptive check only |

- **Split:** household-disjoint 75/25; HP households stratified by station, fill split globally. **20 split seeds**; headline = mean ± sd over seeds.
- **Grid:** size {10, 20, 40, 80, 120} × p {0.05, 0.1, 0.2, 0.3, 0.5, 1.0}. A cell is kept for a (station, split) only if n_hp = round(p·size) <= 0.75·H, so two substations of a cell share at most 75 % of HP members in expectation. Stations need >= 3 HP households. Dropped cells are listed. B\* keeps 19 / 30 cells at KLO test and 24 / 30 at KLO train.
- **Substations per cell:** 10 train, 5 test. This gives **460 train / 130 test substations per split seed** (daily arm 650 / 140). Test cells saturate (e.g. size 20, p = 0.5 draws 10 of 16), so more replicates add little information.
- **CV for tuning:** K = 4 household-disjoint sub-pools of the train pool, with substations rebuilt inside each fold. Hyperopt: 50 evals, seeded from the split seed. Early stopping on an inner household split, never on the scored fold (fixes F13).
- **Bootstrap:** HP-household cluster bootstrap with multiway product weights (a substation's weight is the product of its HP members' bootstrap counts), 2000 replicates, within each split. Report it next to the between-seed sd.
- **Baselines always reported:** anchor-only (Scale_peak, Scale_size; F1), hockey slope-only, slope + base, calibrated delta, HDH.
- **Effective sample size:** every metric row carries `n_hp_households`.
- **Runtime:** from 0.1 s per feature extraction (measured) and 90-455 s per 50-eval XGB search (iter00 logs), about **9-10 min per split seed**, i.e. ~3-3.5 h for 20 seeds (~1.6 h for 10). The daily arm takes about 40 min. The quick config (2 seeds, reduced grid, 10 evals) runs in under 5 min.

**Needs Alex's decision:** the 15 Kaiser SFH HP meters have no dwelling meter; the proposal pairs each with one unused clean dwelling as its own non-HP load. Without them, B\* keeps 71 HP households (47 + 24); B alone (KLO only) has 35 / 12. Fill is taken across stations for Hg/MqO HP members (legacy rule). HP members' own load keeps its water heaters (F16).
