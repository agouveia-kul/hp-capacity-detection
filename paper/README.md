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
| III-C | Semi-Synthetic Aggregates (incl. analog-day fillers) | `sections/03_data_protocol.tex` | outline, **next** |
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
| HP_Peak definition per pool | CLAUDE.md §5 |
