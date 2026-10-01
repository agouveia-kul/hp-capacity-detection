# Iteration 05a-ii — Addendum: decisions from the 05a-i review, and what remains

**Branch:** continue on `iter/05a-gb-eoh-pool`. Read this addendum together with `05a-gb-eoh-pool.md`. **Where they conflict, this addendum wins.**
**Size budget:** ~450 logic lines for 05a-ii, excluding tests. If you exceed it, stop after Task B plus its tests, write the REVIEW for "05a-ii-a", and wait.

## Decisions from the 05a-i review (Alex, 2026-09-30); record them in DECISIONS.md

| # | Decision | Rationale |
|---|---|---|
| R1 | **EoH coverage threshold ≥ 90 %** (was ≥ 95 %). Gaps are filled by the same-household analog-day rule, and the filled days are counted | 95 % cut the pool to 295; the learning curve needs n = all to be large |
| R2 | **Flexible 12-month windows.** Main window: the start month (1st of Jun 2021 – Jan 2022) that maximises the eligible homes. Replication window: the best 12-month window that ends on or before 29 Sep 2023, in any month. Report the counts for every candidate | The 2021/22 count was still rising at the last candidate month; the data stop on 29 Sep 2023 |
| R3 | **Filler sets.** Main: all flat-rate (`Std`) households kept by the audit (3,199; s₀ 0.0131). Sensitivity: "gas central heating and 0 portable heaters" under the **corrected** survey columns (777; s₀ 0.0082). Iteration 04's "gas-only" subset is retired as mislabelled | Real feeders contain some electrically heated homes; the sensitivity rests on a documented label |
| R4 | **The LCL temperature is a London station, not HadCET.** Use London Heathrow daily mean from Meteostat (open), or another documented London station. Rerun D1–D4 with it, and report how many day matches change against HadCET. Keep HadCET only as a comparison column | HadCET averages central England; a systematic offset would shift which days get matched |
| R5 | **Station G009 (27 homes, > 5 % missing T).** Fill the missing days from the weather group with the highest daily-T correlation (≥ 0.98), with a linear bias correction fitted on overlapping days. If no group reaches 0.98, drop G009 and count it. G004 gets the same rule | Keeps homes without inventing weather |
| R6 | **D5 matching uses each substation's own station temperature**, not KLO | B\* spans several stations |
| R7 | **GB design temperature.** Replace the unverified −3 °C with a referenced value, e.g. from the MCS heat-pump design-temperature table or CIBSE Guide A. EoH has no location, so use a documented national central value and flag it. It is only needed for `P_design` (06) | Hard rule 11 |
| R8 | **2022/23 zero runs** (2,130 bins vs 554): plot 5 randomly chosen affected home-days (HP electricity, heat output, pump, T). Classify each as a meter dropout or a real switch-off. If real switch-offs occur, exempt runs where heat output is also 0 from the missing rule | They may be real behaviour during the energy crisis, not missing data |

## Task A — D4 diagnostics (`results/iter05a_pool/d4_diagnostics.md`)
D4 raised its flag. The fillers' s_h was off by 58–99 %, while the peaks were off by only 4–8 %. Find out why before the mapping is used. Run everything with the London temperature (R4).

1. **Real year-to-year stability.** Take the households present in both LCL winters. Compute the real s₀ in 2012/13 and in 2013/14 (the same aggregates of 10 / 40 / 120 households, 50 draws), and report the median |Δs₀|. This is the natural variability that no mapping can remove.
2. **Robust slope definitions.** Recompute the D4 real-vs-rebuilt comparison with three slope definitions:
   - (a) the hockey stick as now;
   - (b) the hockey stick with T_h fixed at the pooled LCL value;
   - (c) an OLS slope of daily load on T for days with T < 12 °C.
3. **Donor pool.** Repeat D4 with donors drawn from all LCL days outside a ±30-day band around the held-out day, from both winters where the calendar allows. This is closer to how the EoH pool is actually built.
4. **Capacity-equivalent error.**
   - Convert the median |Δs_h| per filler dwelling into an equivalent HP capacity error: ΔP = N · |Δs_h per dwelling| / m_h, using the GB-EoH pilot m_h.
   - Express it as a percentage of the true HP_Peak, per penetration p ∈ {0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0} and feeder size, using the GB-EoH pool's median household HP_Peak.
   - Show it as a table and a heat map.

**Decision rule (fixed now, before running):**
- If the real year-to-year |Δs₀| (item 1) is ≥ 0.5 × the D4 error under the same slope definition, classify the D4 error as **intrinsic filler variability**. Accept the mapping, and add a filler-uncertainty sensitivity to 05b: rerun the physics rows with the fillers' temperature response scaled by ×0.5 and ×1.5.
- If the real |Δs₀| is < 0.5 × the D4 error, and the robust definitions (b) and (c) still show > 25 % error, classify it as a **mapping defect**. Change the mapping by adding a 3-day mean-T criterion, then rerun D1–D4. If it still fails, report the result and stop.
- In either case, report the capacity-equivalent error (item 4). Where it exceeds 5 % of HP_Peak, flag those penetration bins as **fusion-limited** in every later table.

## Task B — The remaining 05a tasks
Carry out Tasks 4, 4b, 5 (remaining tests) and 6 of `05a-gb-eoh-pool.md` as written, with R1–R8 applied:
- rebuild the GB-EoH pools under R1/R2/R5/R8;
- recompute the envelopes under protocol v1.1;
- build the overnight queue;
- run the smoke test and the timing probe.

Then queue D5 (with R6) and the Task A items that take longer than 30 min. Print the scheduling command for Alex.

## Task C — Records
- CLAUDE.md:
  - the EoH coverage rule and windows;
  - the London temperature source;
  - the corrected LCL survey columns;
  - §10: the survey column shift and the fact that Paper A's `_lcl_base` has the same bug, being checked separately in the Paper A repo.
- `method_basis.md`: add the Meteostat / station reference, the design-temperature reference and the mapping-uncertainty result from Task A.

## Acceptance criteria
- [ ] R1–R8 are applied and recorded in DECISIONS.md, and the new eligible-home counts per window are reported.
- [ ] Task A items 1–4 have run and the pre-stated rule has been applied. The verdict (intrinsic / mapping defect) is in REVIEW.md.
- [ ] Tasks 4, 4b, 5 and 6 of the main brief are done, and `pytest` passes (including the queue-resume test).
- [ ] D5 has completed through the queue (`STATUS.md` shows 0 remaining).
- [ ] REVIEW.md, titled "05a-ii", follows the §9 template. The decisions must cover at least:
  1. the D4 verdict and what it implies for 05b (sensitivity arm, fusion-limited bins);
  2. the D5 result against its 2 pp flag;
  3. the final pool sizes and whether 05b can start;
  4. the estimated 05b runtime in nights.
