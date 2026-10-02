# Paper B draft (LaTeX)

Working draft of Paper B, written one section at a time and reviewed by Alex before the next one starts.
Branch `paper/draft`, kept separate from the iteration branches (CLAUDE.md hard rule 5: one iteration = one question).

Build (TeX Live): `pdflatex main && bibtex main && pdflatex main && pdflatex main`.

## Style rules for the prose
Alex's voice (skill `gouveia-academic-voice`), plus the instructions of 2026-10-02:
- no em dashes, no dashes used as punctuation, no semicolons and no colons in prose (en dash only in numeric ranges);
- one idea per sentence, at most 35 words, at most two numbers per sentence unless it lists values;
- British spelling, no Oxford comma, passive and impersonal by default.

References follow hard rule 11: every entry in `references.bib` was retrieved and checked, or is marked UNVERIFIED there.

## Sections
| # | Section | File | Status |
|---|---|---|---|
| 1 | Introduction | (placeholder) | after the 05b verdict |
| 2 | Data | `sections/02_data.tex` | **draft 1, for review** |
| 3 | Scenario generation (substations, analog-day fusion) | (placeholder) | next |
| 4 | Estimators (physics, ML) | (placeholder) | |
| 5 | Evaluation design | (placeholder) | |
| 6–8 | Results, discussion, conclusion | | after 05b stages 1 and 2 |

## Sources of the numbers in Section 2
| Number | Source in the repo |
|---|---|
| HEAPO 1,408 households, 15-min/daily, 2018-11 to 2024-03, 8 stations | HEAPO paper (full text, checked 2026-10-02) |
| Kaiser et al. 2,447 installations, 15-min, 2023–2024, load flags, Zurich-Kloten | Kaiser et al. (full text, checked 2026-10-02) |
| Swiss pool 86 HP households = 47 HEAPO + 24 Kaiser paired + 15 Kaiser SFH; 5 stations; cal2023; coverage ≥ 90 % before interpolation | `scripts/paperb/pools/__init__.py`, `results/iter01_pool_audit/REVIEW.md`, DECISIONS 2026-09-29 |
| 1,291 fillers (Kaiser dwellings with no TCL flag) | `results/iter03b_fair_test/arm_main/log.txt` (`pool bstar_2023: {'fill': 1291, 'hp': 86}`) |
| EoH 742 homes, three regions, Nov 2020 – Sep 2023, SN 9050 | Energy Systems Catapult project page (web search, 2026-10-02) |
| EoH selection rules, Nov 2021 – Oct 2022, 384 homes, 26 groups, 217/153/14 by HP type, one silent-meter home (15 %) | `results/iter05a_pool/eoh_selection.md`, CLAUDE.md §7 |
| Replication Oct 2022 – 28 Sep 2023, 319 homes, 272 shared | CLAUDE.md §4, DECISIONS 2026-10-01 |
| LCL 4,173 flat-rate → 3,199 kept, rules, Heathrow (Meteostat) | `results/iter05a_pool/lcl_audit.md`, CLAUDE.md §7 |
| HP_Peak definition per pool | CLAUDE.md §5 |
