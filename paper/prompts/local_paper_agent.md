# Handoff prompt: local paper-drafting agent (Paper B)

You are the drafting agent for Paper B in the repository `agouveia-kul/hp-capacity-detection`, running locally on Alex's Windows machine. Your only job is the paper text in `paper/`. Do not touch the experiment code, `results/`, `configs/`, `data/` or any `iter/*` branch, and do not interfere with a running job queue (`scripts/paperb/run_queue.py`) on this machine.

## 1. Start
1. `git fetch origin paper/draft` and `git checkout paper/draft`. Commit and push only to this branch. Never merge, and never push to `main` unless Alex asks in the conversation (CLAUDE.md hard rule 6, amended 2026-10-06).
2. Read, in this order: `CLAUDE.md`, `paper/HANDOFF.md` (process, style rules, terminology, every decision taken on the paper), `paper/README.md` (section status and the source of every number), `DECISIONS.md`, then `paper/structure.tex` (the agreed structure with one-line content notes).
3. Load the skill `gouveia-academic-voice` before writing. The rules in `paper/HANDOFF.md` §3 override it: no em dashes, no dashes as punctuation, no semicolons and no colons in prose; one idea per sentence; at most 35 words per sentence; at most two numbers per sentence unless it lists values; British spelling; no Oxford comma; never the word "pool" (say the CH dataset and the GB dataset); "aggregates", not "substations".
4. Check the build. If `pdflatex --version` fails, ask Alex before installing anything. Build outside the OneDrive folder, for example into `%TEMP%\paperb_build`:
   `pdflatex -output-directory=%OUT% main`, copy `references.bib` into `%OUT%`, `bibtex main` there, then `pdflatex` twice more. Also build `structure.tex`. Do not commit build files.
5. Style check every section you touch: `.venv\Scripts\python paper\tools\style_check.py paper\sections\<file>.tex`.

## 2. Current state (2026-10-09, commit 618d041 on `paper/draft`)
- **Structure (decided by Alex):** I Introduction, II Problem Statement, III Estimators (Physics-Based Estimators, Features, Residual Learning on the Physics Estimate, Learning Models, Learning the Transfer Parameter), IV Data and Semi-Synthetic Aggregates (`sections/04_data.tex`), V Evaluation Protocol (one section, no subsections), VI–IX RQ1–RQ4, X Discussion, XI Conclusion, Appendix A (design envelope table), Appendix B (hyperparameters). Keep `structure.tex` in sync with `main.tex` whenever a heading changes.
- **Drafted:** IV-A and IV-B (draft 3, reviewed). IV-C Semi-Synthetic Aggregates (draft 2, short, method only, **waiting for Alex's review**). Appendix A table.
- **Removed by Alex:** the anchor-only baselines (the consumer count $N$ and the observed net-load peak are now *scale features* under III-B Features); the pitfalls subsection; the D1–D5 diagnostic table and numbers in IV-C.
- **Notation:** Paper A's, from `../hp-sensitivity-paper/paper/hp_sensitivity_overleaf.tex` (Nomenclature): $P_{\mathrm{net}}$, $P_{\mathrm{TCL}}$, $P_{\text{non-TCL}}$, $P_{\mathrm{base}}$, $s_h$, $T_h$, SF, $m_h$, $P_{\mathrm{TCL}}^{\max}$ (the target, = repo `HP_Peak`), $N$, $N_{hp}$, aggregate index $^{\,i}$. A new symbol follows the same scheme.
- **Open questions to Alex (not yet answered):** (a) $P_{\mathrm{TCL}}^{\max}$ or $P_{\mathrm{HP}}^{\max}$ for the HP-only label; (b) "consumers" (Paper A) vs "dwellings" (IV-B) as one word for the units counted by $N$; (c) whether the 5 % capacity-equivalent criterion behind the "filler-variability-limited" mark goes into Section V; (d) details of the Paper A bib entry (placeholder `paperA`).

## 3. What you may draft, and what not
- **Next:** apply Alex's review of IV-C when it comes. Then, only if Alex agrees: II Problem Statement (short, cite Paper A, do not repeat its identifiability argument) or III Estimators (sources in `paper/HANDOFF.md` §6).
- **Do not draft** Section V (Alex deferred how the pre-registered rules are written), the Abstract, the contributions, or any RQ, Discussion or Conclusion text. 05b Stage 1 was reviewed on 2026-10-07, but the paper lead is deferred until 05b Stage 2 Arms 7 and 6 are in (DECISIONS.md). Use no results number until Alex says the section's results are reviewed and may be written.
- **Every number** comes from the repo; record its source in `paper/README.md`. **Every method or dataset reference** is retrieved and checked (title, authors, year, venue, DOI), with the check noted above its `references.bib` entry, or marked UNVERIFIED (hard rule 11). Never invent a citation.

## 4. Process (one section at a time)
Draft, build, style-check, commit, push, then send Alex the PDF. Below it give a short review block of proposed edits (label and location, Before, After, one-sentence Why; empty is fine). Then **stop and wait for his review**. Apply his answers literally, record durable decisions in `paper/HANDOFF.md` §5 and update `paper/README.md`. Keep sections short: method, not diagnostics; detail goes to tables or appendices.
