You are the paper agent for Paper B (`paper/prompts/local_paper_agent.md` describes your role), working on `paper/draft`.

## Where to work
- Use a separate git worktree (`git worktree add ../hpcd-paper paper/draft`), so that you do not switch branches under an experiment agent working in the main checkout.
- You only touch `paper/`.

## Read first
- `paper/HANDOFF.md`, `paper/README.md`, `paper/structure.tex`, `main.tex`.
- On `main`, the DECISIONS.md lines dated 2026-10-09, 2026-11-13, 2026-11-16 and 2026-11-18. The latest lines override older text.
- The structure note below.

## Task
Apply the agreed structure and the 2026-11-18 reframing to `main.tex` and `structure.tex` as **headings, outline comments and planned figures/tables only**.
- **No new prose and no numbers.** A number reaches the paper only after Alex has reviewed that iteration and said the section may be written.
- Then update `paper/HANDOFF.md` §8 (open items) and stop for Alex's review.

## Structure note (supersedes the storyline part of the 2026-10-09 proposal; the section list is unchanged)

**Storyline (2026-11-18):**
1. The LV network and its DER are unobservable.
2. Physics (Paper A) identifies the heating slope; its limits are filler contamination (s₀) and scale (m_h) dispersion.
3. Data-driven estimation gains in-pool at large n (GB), but not at CH sample size, and the gain is conditional on the fillers.
4. Identifiability-guided hybridisation, tested as a pre-registered ladder: what pays within a pool (physics-derived inputs and target, post hoc) and what does not (learned scale L4, ensemble L5: negative results).
5. Transfer, i.e. what is transferable and what is site-specific:
   - every ML rung loses 2–4× its in-pool error;
   - the HP-side scale transfers approximately;
   - the non-HP temperature response s₀ is the bottleneck;
   - the post hoc hybrid gain is not confirmed.
6. Use case: detecting a change in capacity, measured as the difference between years.

**Contributions (Introduction outline):**
1. A pre-registered, identifiability-guided evaluation of physics, data-driven and hybrid estimators of HP capacity from aggregated net load, including negative results.
2. A validation methodology:
   - household-disjoint semi-synthetic aggregates;
   - statistical-matching fusion of HP and non-HP data;
   - two regimes (CH small-n with real own load, GB large-n);
   - transfer under harmonised labels.
3. The transferable / site-specific split, and its consequence for DSOs: local non-HP data are needed.
4. The change-detection use case.
5. Placeholder, kept as a comment: a label-free estimator with locally estimated s₀, **only if 07b confirms it**.

**Section-by-section outline changes:**

| Section | Change |
|---|---|
| I | Contributions as above. |
| III | Add "s₀ as a site-specific quantity" to the limits. |
| IV | Unchanged. |
| V | Rename to "Identifiability-Guided Hybridisation: a Ladder". Outline: L0–L5 as methods; the pre-registration; that L2/L3 were identified post hoc and tested in VIII. |
| VI | Add a subsection outline for the harmonised label `HL` (30-min, HP unit, no DHW immersion) and the label mapping c. |
| VII-A | Evaluation outline: nMAE primary with **WAPE always beside it**; the "better" rules (03b-style for 03b–06; the relative 5 % rule from 07); bins; the axes A, S, R, T. |
| VII-D | The ladder, with the negative results. |
| VIII | Outline: the frozen-model protocol; T1–T3; the transfer gap; the bias that tracks s₀; the rows that transfer best carry no net-load slope; 07b placeholder. |
| IX | Change detection on year-to-year differences (08). |
| X | Discussion outline: what aggregated net load supports and what it does not; what a DSO needs locally; limits (semi-synthetic aggregates, fillers, two pools). |

**Planned figures/tables.** List them as comments: the ladder table (06), the transfer table with nMAE and WAPE (07), the bias-vs-s₀ figure (07 post-review), and the power curves (08).

## Rules
- Notation follows Paper A.
- References only from `references.bib`, checked or marked UNVERIFIED. Never invent a citation.
- Commit to `paper/draft` and push it. Never merge.
