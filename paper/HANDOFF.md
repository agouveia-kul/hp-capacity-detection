# Handoff: drafting Paper B (2026-10-02)

You are taking over the drafting of Paper B. Your only job is the paper text in `paper/`. The experiments (iteration 05b and later) are run by another session; do not touch them.

Read first, in this order: `CLAUDE.md` (the repo contract), this file, `paper/README.md`, `DECISIONS.md` (Alex's resolved decisions), then the section you are drafting.

## 1. Where things are

- **Branch:** `paper/draft` (from `main`). Commit and push here only. Never commit to `iter/*` or `claude/*` branches, never merge (CLAUDE.md hard rule 6).
- **`paper/main.tex`:** Alex's IEEEtran skeleton (title, authors, section outline in comments). Drafted text lives in `paper/sections/` and is pulled in with `\input`. Keep Alex's outline comments until a subsection is drafted.
- **`paper/sections/04_data.tex`** (was `03_data_protocol.tex` before 2026-10-09; section letters below are the old III-*, now IV-*): Section IV. III-A Source Datasets and III-B CH and GB Datasets are drafted (draft 3, reviewed by Alex on 2026-10-02). III-C to III-E hold the outline.
- **`paper/references.bib`:** every entry records when and how it was checked, or is marked `UNVERIFIED`.
- **`paper/README.md`:** section status and the repo source of every number in III-A/B. Keep both tables up to date.
- **`paper/tools/style_check.py`:** mechanical check of the prose rules (run it on every section before delivering).

**Build.** In a fresh cloud container, install TeX Live first:
`apt-get install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-science texlive-publishers`.
Then, in `paper/`, build into the scratchpad (do not commit build files, `paper/.gitignore` covers them):
`pdflatex -output-directory=$OUT main && cp references.bib $OUT && (cd $OUT && bibtex main) && pdflatex -output-directory=$OUT main && pdflatex -output-directory=$OUT main`.
The build is currently clean (no errors, no overfull boxes, no undefined references). Keep it so.

## 2. Process (Alex's instruction)

- **One section at a time.** Draft one (sub)section, compile, run the style check, commit, push, send Alex the PDF (SendUserFile, `display: render`), then **stop and wait for his review**.
- After the draft, give a short **review block** of proposed edits, one per item: label and location, Before, After, one-sentence reason (skill workflow "match first, propose second"). An empty block is fine.
- Apply Alex's review answers literally, record durable choices in the "Decisions" list below, and update `paper/README.md`.

## 3. Voice and style

Use the skill `gouveia-academic-voice` (Skill tool). On 2026-10-02 Alex added rules that may not have reached the synced copy of the skill. **These override the skill wherever they differ:**

- **No em dashes, no dashes used as punctuation, no semicolons and no colons in prose.** En dash only inside numeric ranges (`2021--2022`). Introduce a list with a full sentence, or with *such as* / *namely* / *i.e.*. LaTeX syntax, maths, times and table cells are exempt.
- **Low information density.** One idea per sentence. At most one subordinate clause. At most two numbers per sentence unless the sentence is a list of values. One bracket per sentence at most. Move detail into a table or footnote rather than into the sentence.
- **Hard cap 35 words per sentence.** Median target 20–24 words. Alex accepted a median of 17 in the data section (it is list-like), so do not force merges.
- British spelling (-ise), no Oxford comma, passive and impersonal by default, acronyms defined once, every causal explanation hedged, findings stated flatly.
- Section opener in one impersonal sentence ("In this section, …").
- "It should be noted that" is kept once in III-B by Alex's choice.

A zip of the updated skill is in the previous session's scratchpad. Alex may re-upload it to claude.ai; until then, follow the list above.

## 4. Terminology (decided by Alex)

| Use in the paper | Not | Repo name |
|---|---|---|
| CH dataset (`\dataCH`) | pool, Swiss pool, B\* | `B*`, `bstar` |
| GB dataset (`\dataGB`) | pool, GB-EoH pool | `GB-EoH`, `gb_eoh_2122r3` |
| CH sensitivity subset (47 households at Zurich-Kloten) | pool B | `B` |
| temporal replication (GB, Oct 2022 – 28 Sep 2023) | independent sample | `gb_eoh_2223r3` |
| source datasets (HEAPO, Kaiser et al., EoH, LCL) | | |
| fillers (households without HP that fill an aggregate) | fill | `fill` |
| aggregates / semi-synthetic aggregates (Alex's skeleton wording) | | substations |
| $P_{\mathrm{TCL}}^{\max}$, the installed capacity (non-coincident 99.9th-percentile peak), as in Paper A | $P^{\mathrm{HP}}$ | `HP_Peak` |
| $N$ consumers, $N_{hp}$ HPs per aggregate (Paper A) | size, $n$, $p$ as a symbol | `size`, `n_hp`, `p` |

Never write "pool" anywhere in the paper.

## 5. Decisions already taken on the paper (2026-10-02)

Data section review:
1. No "pool": the two sets are the **CH dataset** and the **GB dataset**.
2. The own non-HP load of a CH HP household is described as kept as measured and possibly including an electric water heater. Do **not** add the 3.3× slope figure in Section III (it is a result).
3. Sentence-length median of 17 in the data section is accepted.
4. Keep "It should be noted that" in III-B for now.

Structure (applied to the outline in `main.tex` / `03_data_protocol.tex`, as comments marked "2026-10-02"):
1. GB dataset and LCL fillers throughout; RQ3 becomes CH ↔ GB under harmonised labels.
2. III-C gets a subsubsection on the GB fillers from analog days, with validation and the filler-variability floor.
3. RQ2 gets "Does More Training Data Help?" (the 05b question and its pre-registered verdict).
4. RQ2 gets "Error Decomposition" (05b oracles O1/O2).
5. IV Estimators outline updated to the current pipeline, with a new "Residual Learning on the Physics Estimate" subsection.
6. **Deferred by Alex:** how the pre-registered rules (16/20 criterion, WAPE primary, penetration bins, multiplicity, filler-variability flag) are written into III-D. Ask him before drafting III-D.
7. II-C stays short and cites Paper A (CLAUDE.md: Paper B must not repeat Paper A).
8. **Open:** target journal and whether RQ3/RQ4 move to a third paper. Do not restructure for it.
9. `a4paper` and `hidelinks` applied.

III-C review (2026-10-02):
1. Use Paper A's notation throughout (`hp-sensitivity-paper/paper/hp_sensitivity_overleaf.tex`, Nomenclature); a new symbol follows the same scheme.
2. The split mechanics (one quarter per station to test) are described in III-C; III-D adds only seeds and inner CV.
3. No D5 numbers in Section III.
4. No filler-uncertainty sentence (×0.5, ×1.5) in III-C until RQ2 is drafted.
5. No gas-heated LCL sensitivity set in III-C.
6. Short sections: describe the method, not diagnostic outcomes; detail goes to tables or appendices.

Structure review (2026-10-09):
1. Order: I Introduction, II Problem Statement, III Estimators, IV Data and Semi-Synthetic Aggregates, V Evaluation Protocol, VI–IX RQ1–RQ4, X Discussion, XI Conclusion.
2. The data section holds only the data and the aggregate construction; the evaluation protocol and the pitfalls are their own section (V).
3. Anchor-only baselines leave the paper (subsection and RQ2 "Gain over Anchor-Only Baselines" removed); the consumer count and the observed peak are scale features under III-B Features.
4. `paper/structure.tex` is the one-page structure with content notes; keep it in sync with `main.tex`.
5. Section V Evaluation Protocol stays, as one section without subsections; the pitfalls subsection (legacy vs leak-free table) is removed.
6. "Scale anchor" becomes "scale features" everywhere (RQ1 subsection "Role of the Scale Features").

Answers to the open questions (Alex, 2026-10-09):
1. The target symbol is $P_{\mathrm{TCL}}^{\max}$, as in Paper A (not $P_{\mathrm{HP}}^{\max}$).
2. "Consumers" is the word for the units counted by $N$ everywhere, including IV-B. "Dwellings" is no longer used (applied in `sections/04_data.tex`).
3. The 5 % capacity-equivalent criterion behind "filler-variability-limited" goes into the evaluation text as one sentence, with its derivation in an appendix (not drafted yet).
4. The Paper A bib entry (`paperA`) stays a placeholder until Alex provides the details.

Structure direction, not to be drafted yet (Alex, 2026-10-09): Section V becomes a subsection on how the methods are evaluated (error metrics, seeds and splits, inner-CV selection, the comparison criterion, penetration bins). The aggregate-construction rules stay in IV-C. Placement and wording are pending Alex. Do not draft or restructure Section V until he says so. `main.tex`, `structure.tex` and `README.md` carry the note only.

## 6. What can be drafted now, and what cannot

**Next: III-C Semi-Synthetic Aggregates** (generator + analog-day fillers + Alex's Fig. 1 as a construction diagram placeholder). Sources:
- generator: `scripts/paperb/substations.py`, `scripts/paperb/splits.py`, `configs/protocol_v1.yaml` (grid, `max_overlap` 0.75, `min_station_pool` 3, 10 train / 5 test per cell, `n_hp = round(p·N)`, `on_infeasible: drop`), `configs/protocol_v1_1.yaml` (p = 0.8 added), CLAUDE.md §4 (household-disjoint splits before aggregates, no stacking, stratified by station, grouped inner folds);
- counts: `results/iter05a_pool/envelopes.md` (per seed, CH 500 train / 135 test aggregates from 62 / 20 HP households; GB 2,080 / 455 from 274 / 81; test aggregates per Paper A bin);
- analog-day fillers: `scripts/paperb/fill_analog.py` docstring, `results/iter05a_pool/mapping.md` (D1–D5), `d4_diagnostics.md`, `method_basis.md` (checked references for statistical matching, analog methods, k-NN resampling; and the explicit "no precedent" statement), DECISIONS lines R3–R6 and the D4/D5 lines.

**Can be drafted after III-C, if Alex agrees:** II Problem Statement (short, cite Paper A), IV Estimators (sources: `scripts/paperb/physics.py`, `features_netfit.py`, `residual.py`, `train.py`, `results/iter03b_fair_test/REVIEW.md`, `results/iter05b_data_limit/method_basis.md` on branch `iter/05b-data-limit`, DECISIONS A7, A8), III-E Pitfalls (removed 2026-10-09).

**Do not draft yet:** III-D (item 6 deferred), the Abstract, contributions and the "we show" part of the Introduction, and every Results / Discussion section. The GB results of iteration 05b are not reviewed yet and the paper's lead depends on them (CLAUDE.md §1). Never use unreviewed numbers, and never open the 05b probe or Stage 1 test metrics. When results are reviewed, Alex will say so.

## 7. References (CLAUDE.md hard rule 11)

- Every method or dataset that appears in the paper needs a reference you have **retrieved and checked** (title, authors, year, venue, DOI or link). Record the check in a comment above the `.bib` entry. Mark anything else `UNVERIFIED`. Never invent a citation or a DOI. If there is no precedent, say so in the text.
- **Tools that worked on 2026-10-02:** the Undermind MCP (workspace "Heat Pump Quantification", `cf9ff26c-27a5-46b2-8279-a78289b06a32`): `lookup_papers_by_metadata`, `get_paper_info`, `read_pdfs` for author lists; WebSearch for dataset landing pages.
- **Did not work:** the Scite MCP (needs a paid plan); the network proxy blocks arxiv.org, api.crossref.org, zenodo.org, dl.acm.org and the UK Data Service / CESSDA catalogues.
- Already checked references for later sections: `results/iter05a_pool/method_basis.md` (fusion, matching, Meteostat, MCS) and `results/iter05b_data_limit/method_basis.md` on `iter/05b-data-limit` (GP, ESL, RF, Extra Trees, TabPFN, FCN, learning curves). Copy them into `references.bib` with their check notes when a section cites them.
- Still to retrieve before the methods sections cite them: XGBoost (Chen & Guestrin), TPE / hyperopt (Bergstra et al.), Lasso and elastic net, a grouped / blocked CV reference.

## 8. Open items

- `references.bib`: EoH record year and edition, LCL DOI and edition (`UNVERIFIED`); Paper A is a placeholder entry, ask Alex for its details.
- III-B: whether the CH sensitivity subset is reported at all (TODO in the file).
- Table I: transfer datasets (WPuQ, FeederBW, UKPN) are added only when iteration 07 fixes their use.
- Nomenclature section: draft once Section II exists, aligned with Paper A's symbols.
