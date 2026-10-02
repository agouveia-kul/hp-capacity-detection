# Paper B draft (LaTeX)

**New drafting agent: start with `HANDOFF.md`.**

Working draft of Paper B, written one section at a time and reviewed by Alex before the next one starts.
Branch `paper/draft`, kept separate from the iteration branches (CLAUDE.md hard rule 5: one iteration = one question).

Build (TeX Live): `pdflatex main && bibtex main && pdflatex main && pdflatex main`.

## Style rules for the prose
Alex's voice (skill `gouveia-academic-voice`), plus the instructions of 2026-10-02:
- no em dashes, no dashes used as punctuation, no semicolons and no colons in prose (en dash only in numeric ranges);
- one idea per sentence, at most 35 words, at most two numbers per sentence unless it lists values;
- British spelling, no Oxford comma, passive and impersonal by default.
- Never "pool": the two household sets are the CH dataset and the GB dataset (`\dataCH`, `\dataGB`).
- Check every section with `python paper/tools/style_check.py <file>`.

References follow hard rule 11: every entry in `references.bib` was retrieved and checked, or is marked UNVERIFIED there.

## Sections
Structure = Alex's IEEEtran skeleton (uploaded 2026-10-02, `main.tex`). Drafted parts live in `sections/`; the rest keeps Alex's outline comments.

| # | Section | File | Status |
|---|---|---|---|
| – | Abstract, Nomenclature, I Introduction | `main.tex` | outline (after the 05b verdict) |
| II | Problem Statement | `main.tex` | outline; II-B holds the label definition moved from Data draft 1 |
| III-A | Source Datasets | `sections/03_data_protocol.tex` | draft 3, reviewed 2026-10-02 |
| III-B | CH and GB Datasets | `sections/03_data_protocol.tex` | draft 3, reviewed 2026-10-02 |
| III-C | Semi-Synthetic Aggregates (incl. analog-day fillers) | `sections/03_data_protocol.tex` | draft 2 (2026-10-02, shorter after Alex's review), **waiting for Alex's review** |
| III-D, III-E | Evaluation Protocol, Pitfalls | `sections/03_data_protocol.tex` | outline |
| IV | Estimators | `main.tex` | outline |
| V–X | RQ1–RQ4, Discussion, Conclusion | `main.tex` | after 05b stages 1–2 and later iterations |

## Sources of the numbers in Section III-A/B
| Number | Source in the repo |
|---|---|
| HEAPO 1,408 households, 15-min/daily, 2018-11 to 2024-03, 8 stations | HEAPO paper (full text, checked 2026-10-02) |
| Kaiser et al. 2,447 installations, 15-min, 2023–2024, load flags, Zurich-Kloten | Kaiser et al. (full text, checked 2026-10-02) |
| CH dataset 86 HP households = 47 HEAPO + 24 Kaiser paired + 15 Kaiser SFH; 5 stations; cal2023; coverage ≥ 90 % before interpolation | `scripts/paperb/pools/__init__.py`, `results/iter01_pool_audit/REVIEW.md`, DECISIONS 2026-09-29 |
| 1,291 fillers (Kaiser dwellings with no TCL flag) | `results/iter03b_fair_test/arm_main/log.txt` (`pool bstar_2023: {'fill': 1291, 'hp': 86}`) |
| EoH 742 homes, three regions, Nov 2020 – Sep 2023, SN 9050 | Energy Systems Catapult project page (web search, 2026-10-02) |
| GB dataset: EoH selection rules, Nov 2021 – Oct 2022, 384 homes, 26 groups, 217/153/14 by HP type, one silent-meter home (15 %) | `results/iter05a_pool/eoh_selection.md`, CLAUDE.md §7 |
| Replication Oct 2022 – 28 Sep 2023, 319 homes, 272 shared | CLAUDE.md §4, DECISIONS 2026-10-01 |
| LCL 4,173 flat-rate → 3,199 kept, rules, Heathrow (Meteostat) | `results/iter05a_pool/lcl_audit.md`, CLAUDE.md §7 |
| HP_Peak definition per dataset | CLAUDE.md §5 |

## Sources of the numbers in Section III-C and Appendix A
Draft 2 keeps only the design numbers in III-C (split, grid, envelope rule, aggregates per split, analog-day rule, 50 % limit) and moves Table III to Appendix A. The D1–D5 numbers below are no longer in the text; they stay listed for a later appendix or the RQ2 section.
Notation follows Paper A (`hp-sensitivity-paper/paper/hp_sensitivity_overleaf.tex`, Nomenclature): $N$, $N_{hp}$, $P_{\mathrm{TCL}}^{\max}$ (= `HP_Peak`, same definition as Paper A's 99.9th-percentile installed capacity).
| Number | Source in the repo |
|---|---|
| Split before construction: test fraction 0.25, HP households stratified by station, fillers split globally and independently | `configs/protocol_v1.yaml` (`split`), `scripts/paperb/splits.py` (`household_splits`) |
| $n = \max(1, \mathrm{round}(pN))$; sizes 10, 20, 40, 80, 120; penetrations 0.05 ... 1.0 incl. 0.8 | `configs/protocol_v1.yaml` (`grid`), `configs/protocol_v1_1.yaml` (p = 0.8), CLAUDE.md §4 |
| Envelope rule $n \le 0.75H$, stations with < 3 HP households unused, 10 train / 5 test aggregates per cell, dropped not truncated | `configs/protocol_v1.yaml` (`max_overlap`, `min_station_pool`, `substations_per_cell`, `on_infeasible: drop`), `scripts/paperb/substations.py` (`plan_cells`, `draw_cells`) |
| CH aggregate = n HP households (HP + own load) + N − n fillers; GB = N fillers, one per dwelling incl. HP dwellings; HP households never fillers; draws without replacement | `scripts/paperb/substations.py` (`draw_cells`, `fill_all`, `evaluate_members`), `scripts/paperb/fill_analog.py` docstring |
| Table III: HP households 64/22, 292/92, 241/78; used 62/20, 274/81, 226/61; aggregates 500/135, 2,080/455, 1,870/355; test per bin 75/40/10/10, 265/125/30/35, 190/105/30/30; identical in all 20 seeds | `results/iter05a_pool/envelopes.md`, `envelopes.csv` (seed 0; min = max over seeds) |
| Analog-day rule: same day type (England & Wales calendar), day-of-year window 30 → 45 → 60 days, ΔT ≤ 1 K (Heathrow), random among 3 closest (seeded), fallback = closest T within 60 d, map fixed per (group, split), same d′ for all fillers of an aggregate, local clock, DST days excluded | `scripts/paperb/fill_analog.py` docstring |
| D1 +5.9 % (flag 15 %), 2 of 16 stations beyond 15 % (G005, G007) | `results/iter05a_pool/mapping.md` D1 (seed 0, 2,399 train fillers, build `2122r2`) |
| D2 0.24 % of days > 1 K (flag 5 %) | `mapping.md` D2 (share 0.0024), `REVIEW.md` (05a-ii) |
| D3 median 16 days, 95th percentile 29 days | `mapping.md` D3 |
| D4 flag 10 %; peak differs 3–7 % (median); slope raised | `mapping.md` D4 (`median |rel_d_p999|` 0.032–0.072; `median |rel_d_s_h|` 0.30–1.00) |
| D4 Task A: real year-to-year change 52–78 %, rebuild error 38–94 %, rule Y ≥ 0.5 E → intrinsic | `results/iter05a_pool/d4_diagnostics.md` (def. a, n = 120 / 10), `method_basis.md` "Mapping uncertainty", DECISIONS 2026-09-30 (D4 rule) and 2026-10-01 |
| Capacity-equivalent error > 5 % of HP_Peak for p ≤ 0.5 (= Paper A bins ≤ 15, 15–35, 35–65 %); winter-only slope pessimistic | `d4_diagnostics.md` item 4, DECISIONS 2026-10-01, `REVIEW.md` (05a-ii) "Problems found" |
| Filler-uncertainty sensitivity ×0.5, ×1.5 | DECISIONS 2026-10-01 (D4 verdict, 05b arm 7) |
| D5: same rule on the CH dataset, same-year candidates, ±3 days excluded, own-station temperature; flag 2 pp raised; deltas quoted next to every GB headline | `fill_analog.py` docstring (D5), `mapping.md` D5, DECISIONS 2026-10-01 (R6, D5 flag closed) |
| Limitations of the mapping (own-load link, 2012–14 drift, weather beyond daily mean T, persistence, electrically heated LCL homes) | `results/iter05a_pool/method_basis.md` "What the mapping cannot recover" |
| No precedent for day-level temperature-analog pairing | `method_basis.md` "Energy-domain precedent" |

Note: the D1 row (a) in `mapping.md` is labelled "own LCL days vs HadCET", but the code (`iter05a_report.py`, `d1` = `D["T"]`) and the pooled T_h of 17.6 °C (= the Heathrow value in `d4_diagnostics.md`) show it uses Heathrow; the label is stale. D1–D4 ran on build `2122r2` (385 homes, before the EOH2291 exclusion).
