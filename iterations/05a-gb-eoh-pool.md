# Iteration 05a — GB-EoH pool with LCL filler, and protocol v1.1

**Branch:** `iter/05a-gb-eoh-pool`, from `main` after 04 is merged.
**Type:** implementation plus tests, a pool audit and a smoke run. **No results are interpreted** (that is 05b).
**Size budget:** ~500 logic lines, excluding tests (raised for the D4/D5 validation and the overnight runner). If you exceed it, stop after Tasks 1–3 plus their tests, write the REVIEW for "05a-i", and wait.

## Why this iteration
03b found no ML configuration that beats the physics estimator on B\*. B\* has only ~62 train HP households per seed, so two explanations remain open:
- **data-limited:** more distinct HP households would let ML overtake physics;
- **identifiability-limited:** net load carries s_h but not the per-unit scale, and no amount of data fixes that.

GB-EoH has ~5× more HP households (~309 train / ~90 test per seed). 05a builds it as a second full-grid pool; 05b runs the data-limit test.

## Decisions carried into this iteration (Alex, 2026-09-30)
From the 04 review:
1. **GB-EoH** is a **second full-grid pool**, not a replacement for B\*: 2021/22 main, 2022/23 replication.
2. **Filler = Low Carbon London (LCL)**, matched to EoH days by temperature and day type (analog days).
3. **Simulator:** deferred. The go/no-go decision comes after the 05b verdict.
4. The 682 audit lines of 04 are accepted as-is.

From the 03b review (confirmed by Alex, 2026-09-30):
5. **The paper leads with identifiability**, provisionally: it is revisited if 05b's verdict is D (data-limited).
6. **Physics reference rows:** `slope_base`, `paperA_corr`, `paperA_cal`, with `paperA_sh_mh` kept as Paper A's own row.
7. **ML reference set for tables:** netfit + Lasso [size] direct, Lasso residual, XGBoost direct. This is **not a model filter**. All four families stay in every arm and are compared by one inner-CV winner per family (CLAUDE.md §4):
   - linear: Linear, Ridge, Lasso, ElasticNet, PLS;
   - kernel: SVR;
   - trees: XGBoost;
   - neural: FFNN at the full budget.

   05b adds Kernel Ridge and GP regression (kernel), Random Forest, Extra Trees and CatBoost (trees), TabPFN (neural), and a raw-series 1D-CNN family. **05a uses only the models above.**

   `XGBoost_mono` is retired.
7b. **Runtime is not a constraint.** Long runs go overnight through the resumable queue built in Task 4b; Alex schedules them.

New today:
8. **Filler pool = flat-rate LCL households only.** The dynamic time-of-use households are excluded.
9. **"Gas-only" LCL subset:** used only if it traces to a documented heating or gas label (Task 1).
10. **Deferred to later iterations:** RHPP (nameplate and fill-validation arm), EDRP/CER alternative fillers, and NPG real feeders.

**Plan renumbering:**

| Iteration | Content |
|---|---|
| 05a / 05b | GB-EoH pool; is training data what holds ML back? |
| 06 | Other targets + daily arm (RQ1), both pools |
| 07 | Transfer (RQ3), incl. CH↔GB and the RHPP nameplate arm |
| 08–09 | Change detection (RQ4), EoH multi-year panel |
| 10+ | Freeze and draft |

## Task 0 — Bookkeeping (first commit)
- Record decisions 1–10 in DECISIONS.md.
- **CLAUDE.md was already updated before this iteration (2026-09-30)** and is an uncommitted change in the working tree. The update covers:
  - §1: plan and paper lead;
  - §3: new hard rules 11 (checked references) and 12 (pre-registration);
  - §3 rule 7: long runs go overnight via the resumable queue;
  - §4: v1.1, the pools table, the criterion, the reference set and the model families;
  - §5: `HP_Peak` per pool;
  - §6–7: code and data maps;
  - §10: the 04 data issues.

  **Check it against the repo** (script names, config names, data paths such as `LCL_2013.zip`). Fix any path that is wrong, list the fixes in REVIEW.md, and commit it together with DECISIONS.md.
- Report whether `stash@{0}` and the tags `iter-02b`, `iter-03b` and `iter-04` exist. Do not change them; Alex does that.

## Task 1 — LCL filler audit (answer before building anything)
1. **Identify the release on disk.** Report the file names, household count, date range and columns. Compare with the public London Datastore release: 5,567 households, Nov 2011 – Feb 2014, 30-min, a tariff column (`Std`/`ToU`). State whether ours is that release, a subset of it, or a superset (e.g. with survey or ACORN fields).
2. **Trace iteration 04's "gas-only" subset** (s₀ = 0.0070): the file and column that defined it, and the rule used.
   - If it comes from a documented heating or gas label: keep it as a sensitivity arm.
   - If it was inferred from electricity (e.g. a low temperature slope): mark it **circular** and drop it. It selects low s₀ and then reports low s₀.
3. **Tariff.** Keep `Std` households only, and drop every `ToU` household for its whole record. Report the counts.
4. **Quality.** Apply these rules and report how many households each one drops:
   - coverage ≥ 90 % over the LCL window;
   - flag implausible values: a half-hour above 10 kWh, or runs of exact zeros ≥ 24 h.
5. **Temperature.** Name the London temperature source used in 04 and reuse it. Report the flat-rate pool's s₀ per dwelling (kW/K) against it, next to B\*'s 0.0055.

## Task 2 — EoH HP households: selection, cleaning, window (`scripts/paperb/pools/gb_eoh.py`)
- **Households:** non-hybrid (ASHP/GSHP) only, using iteration 04's channel-based typing.
- **Window:** a **12-month** window, so that the hockey-stick fit sees non-heating days, as in B\*'s calendar 2023.
  - Main: among the 12-month windows starting on the 1st of Jun–Oct 2021, take the one that maximises the number of households with ≥ 95 % coverage after cleaning. Report the counts for all five candidates.
  - Replication: the same months one year later.
- **Channel.** Use **whole heating-system electricity** (compressor + backup + immersion + pumps): this is what the DSO sees. It is both the HP load in the net load and the basis of the labels.
  - Report the share of each household's robust peak that falls in half-hours with backup or immersion active.
- **Missing data:**
  - A run of exact zeros ≥ 6 h on a day with daily mean T < 12 °C, while other channels are active, counts as missing.
  - Gaps ≤ 2 h are linearly interpolated.
  - Longer gaps are filled with the same household's day of the same day type and nearest daily mean temperature. Count these filled days per household.
  - A household is eligible only if it has ≥ 95 % coverage before this filling.
- **Stations:** the 30 weather groups found in 04. T is the group's measured outdoor temperature, as a daily mean of the 30-min values. Flag groups with gaps > 5 % or implausible values.
- **Labels:** the definitions in `substations.py`, unchanged (`HP_Peak` = Σ of household 99.9th percentiles, `HP_CoincPeak`, s_h, r, P_design), at **30-min** resolution.
  - B\* labels are 15-min, so cross-pool comparisons use gaps to physics, not absolute WAPE.
  - On B\*, report the median ratio of the 30-min to the 15-min `HP_Peak` so the reader can scale.
- Heat-meter dropouts don't affect the electricity labels. Record them for the later simulator.

## Task 3 — Analog-day filler (`scripts/paperb/fill_analog.py`)
**Composition.** EoH has no own non-HP load, so **every dwelling in a substation gets one LCL filler household, HP dwellings included**:

net(d) = Σ_{i=1..N} LCL_i(d′) + Σ_{j=1..n_hp} HP_j(d).

**Mapping.** For each weather group g and each day d of the window, choose one LCL analog day d′:
1. same day type (working day vs weekend / bank holiday), using the England & Wales calendar on both sides;
2. |day-of-year(d′) − day-of-year(d)| ≤ 30 days (daylight and season), from any LCL year. If no candidate passes step 3, widen to 45, then 60 days, and count each widening;
3. |T_London(d′) − T_g(d)| ≤ 1.0 K;
4. among the 3 closest candidates in temperature, draw one at random (seeded) to limit reuse. Report the reuse distribution.

**Rules:**
- **The same d′ applies to all filler households in a substation-day.** This keeps the fillers' common calendar and weather shocks coincident.
- The mapping is fixed per (weather group, seed).
- Place local clock times onto local clock times, and state how 23- and 25-hour days are handled.
- LCL households get their own seeded, household-disjoint 75/25 split. Train fillers never appear in test substations.
- `paperA_corr` estimates s₀ from the train fillers **under the same mapping**.

**Mapping diagnostics** (`results/iter05a_pool/mapping.md`):
- **D1:** fit the hockey stick to the train-filler aggregate (a) against its own London T on its own days, and (b) against the mapped EoH T. Report s₀, T_h and P_base both ways.
- **D2:** the distribution of |T_London(d′) − T_g(d)|: median, 95th percentile, and share > 1 K.
- **D3:** the distribution of day-of-year distance, and the number of widenings.

**Flag criteria** (stated now, before any results): the s₀ from D1(a) and D1(b) differ by more than 15 %, or more than 5 % of days need a temperature mismatch > 1 K.

**Mapping validation.** The fusion rests on one assumption, conditional independence: given (daily T, day type, time of year), the filler load and the HP load are independent. Two checks bound the error it introduces. Implement both here and report their numbers; interpretation comes in review.
- **D4 — LCL self-test** (the error of the matching itself):
  - hold out one LCL winter (Nov–Mar), and rebuild it from the other LCL years with the same mapping rule, matching on the held-out days' own London T;
  - form aggregates of 10, 40 and 120 train-filler households, real vs rebuilt, 50 draws each;
  - compare s_h, T_h, P_base, the 99.9th-percentile and maximum aggregate load, and the daily-mean distribution (KS statistic, Wasserstein distance).
  - Repeat with each LCL winter held out in turn.
- **D5 — B\* swap test** (the cost of losing within-household correlation):
  - on B\*, where same-year fillers and the HP homes' own non-HP load are real, rebuild every substation with **all** non-HP load (fillers and the HP homes' own load) replaced by analog-matched days;
  - the analog pool is the same B\* filler households, same year, excluding days within ±3 days of d. HP loads, splits, seeds and the test set are unchanged;
  - run the physics rows (decision 6) and all four model families (inner-CV winner per family, FFNN included) on 10 seeds, **through the overnight queue** (Task 4b). Write REVIEW.md after it finishes;
  - report ΔWAPE (swapped − real) per model, overall and per Paper A bin, plus the change in the median P̂/y by penetration;
  - an optional variant uses LCL as the analog pool. It mixes population shift with matching error, so label it as such.

**Flag criteria for D4/D5**, stated before any results:
- D4: median |Δs_h| > 10 %, or median |Δ(99.9th percentile)| > 10 %, at any aggregate size;
- D5: |median ΔWAPE| > 2 pp for any physics row or family winner, overall or in any bin.

A flag does not stop the iteration. It goes to Decisions for Alex.

**Methodological basis must be referenced** (`results/iter05a_pool/method_basis.md`, ≤ 1 page). This text feeds the paper's methods section. Write a short note that states:
- the conditional independence assumption;
- how the mapping implements it;
- what it cannot recover (within-household correlation, cross-year drift, weather variables other than T, day-to-day persistence of the filler).

Every claim of precedent needs a reference that has been **retrieved and checked**: title, authors, year, venue, DOI or link. Starting points to verify, not to cite blindly:

| Precedent | Starting point |
|---|---|
| Statistical matching / data fusion under conditional independence | D'Orazio, Di Zio & Scanu, *Statistical Matching: Theory and Practice* (Wiley, 2006) |
| k-nearest-neighbour day resampling within a seasonal window | Rajagopalan & Lall (1999), Water Resources Research, doi:10.1029/1999WR900028; Lall & Sharma (1996) on the nearest-neighbour bootstrap |
| Analog method | Zorita & von Storch (1999), Journal of Climate |
| Similar-day equivalence in load forecasting and demand-response baselines | Dudek's similarity-based short-term load forecasting work; a CPUC or other customer-baseline document |
| Energy-domain precedent: HP or other LCT profiles combined with separately measured household base load | search specifically for this; it is the reference reviewers in this field will look for |

Rules:
- Search with the literature tools available (scite, Undermind, Consensus, web).
- Mark anything not retrieved as **unverified**. Never invent a DOI.
- If no energy-domain precedent is found, say so explicitly.

## Task 4 — Pool interface and protocol v1.1
- **Pool configs:** `configs/pool_gb_eoh_2122.yaml` and `configs/pool_gb_eoh_2223.yaml`. The builder returns the same interface as B\*, so `run_benchmark.py` changes only in pool selection.
- **Holiday calendar per pool:** CH-ZH for B\*, GB-ENG for EoH. It feeds netfit's working-day / weekend features.
- **Protocol v1.1** = v1 + **p = 0.8** added to the grid, for both pools. Everything else is unchanged. Keep `protocol_v1.yaml` for reproducibility.
- **Learning-curve harness** (needed in 05b):
  - allow n_train_hp ∈ {16, 32, 62, 100, 200, all};
  - add `substations_per_cell_train` ∈ {10, 20, 40} as a harness option;
  - keep the test set identical across both options.
- **Envelopes.** Re-run `envelope_v2.py` for GB-EoH 2021/22 and 2022/23, and for B\*, under v1.1. Report:
  - train/test HP households per seed;
  - test substations per seed in each Paper A bin (target: ≥ 20 in every bin).

## Task 4b — Overnight runner (`scripts/paperb/run_queue.py` + `scripts/schedule_overnight.ps1`)
This is infrastructure for every later iteration. Long runs go unattended at night.
- **Queue.** Each arm is split into jobs of (arm, seed, draw, n, family). A job writes its rows to `results/<exp_id>/jobs/<job_id>.parquet` and a `done` marker. Relaunching skips finished jobs, so a crash, reboot or morning stop loses at most one job. Merge into `metrics.csv` only at the end.
- **Priority order.** Each config lists its arms in priority order, and the queue follows it.
- **Keep the machine awake while running, without admin rights and without changing power settings.** Call `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` via `ctypes` at start, and reset it at exit.
- **Progress.** Write `progress.json` (done / failed / remaining jobs, ETA from the median job time). On exit, write `STATUS.md` with the counts, failures and their tracebacks (first 20 lines), and the wall time per arm.
- **Failures.** A failed job is logged and skipped, never retried in a loop. Rerun failed jobs with a `--retry-failed` flag.
- **Scheduling.** `scripts/schedule_overnight.ps1 -Config <yaml>` registers a one-off Windows Task Scheduler task (`schtasks /Create /SC ONCE /ST 22:00 /TN "paperb-<exp_id>" ...`) that starts the queue with `.venv\Scripts\python`, at below-normal priority, logging to `log.txt`.
  - **Do not register the task yourself.** Print the exact command in REVIEW.md, and Alex runs it.
  - An optional `-StopAt 07:30` argument makes the queue finish its current job and exit at that time. Relaunching the next night resumes.
- **OneDrive.** Write job files locally first, then move each one into `results/` in a single operation. Note in REVIEW.md that pausing OneDrive sync overnight is advised.

## Task 5 — Tests (`tests/test_gb_eoh.py`)
- **Analog mapping:** respects the day type and the day-of-year window; is deterministic given the seed; uses one d′ for all fillers in a substation-day.
- **Splits:** filler train/test are disjoint; no ToU household appears anywhere.
- **Eligibility:** only non-hybrid households enter the pool, and every one meets the coverage rule.
- **Toy composition:** net = Σ fillers + Σ HP exactly, and the labels match the `substations.py` definitions.
- **GB-ENG calendar:** marks the 2022 bank holidays, including the Platinum Jubilee (2 and 3 June 2022) and the state funeral (19 September 2022, in the replication window).
- **B\* regression:** under `protocol_v1.yaml`, B\* seed 0 reproduces 03b's metrics exactly.
- **D4:** the held-out LCL winter never appears among its own analog candidates.
- **D5:** the swapped substations keep identical HP members, splits and test membership, and the analog days respect the ±3-day exclusion.
- **Queue:** kill it mid-run on a toy config, relaunch it, and the merged metrics equal those of an uninterrupted run. Finished jobs are skipped. `--retry-failed` reruns only the failed jobs.

## Task 6 — Smoke run and timing probe
- **Smoke run:** `configs/iter05_quick.yaml` on GB-EoH 2021/22:
  - 1 seed;
  - sizes {10, 40} × p {0.1, 0.5};
  - the physics rows (decision 6);
  - netfit Lasso direct, Lasso residual and XGBoost direct.
- **Timing probe:** seed 0, full v1.1 grid, one job per family (FFNN at the full budget). Extrapolate the runtime of each 05b arm, in nights, with it.
- Report the actual wall times.

## Out of scope
- Interpreting any result, and learning-curve runs (05b).
- RHPP, EDRP, CER and NPG.
- The simulator.
- Notebook edits.
- API changes to `hp_common.py`, `hp_pools.py`, `hp_capacity.py` and `heapo.py`.

## Acceptance criteria
- [ ] Task 0 is committed first.
- [ ] Tasks 1–4b are implemented, and `pytest` passes, including the B\* regression and queue-resume tests.
- [ ] D5 has run through the queue (`STATUS.md` shows 0 remaining), after Alex scheduled it with the printed command.
- [ ] `results/iter05a_pool/` holds `lcl_audit.md`, `eoh_selection.md`, `mapping.md` (D1–D5), `method_basis.md` (every reference retrieved or marked unverified), `envelopes.md`, the smoke-run `metrics.csv`, `config.yaml` and `log.txt`.
- [ ] Nothing in `data/` outside `data/_paperb/`, and nothing in `models/`, is modified. Free disk space is reported.
- [ ] REVIEW.md follows the §9 template. The decisions must cover at least:
  1. the LCL release and the verdict on "gas-only" (keep as sensitivity / drop as circular);
  2. the 12-month windows chosen and the eligible household counts, against 433 / 371 in 04;
  3. whether the analog mapping passes D1–D5 (use as-is / change the rule, e.g. add previous-day conditioning / restrict GB-EoH to targets that D5 shows are robust);
  4. the estimated 05b runtime per arm (in nights). No cuts are needed unless it exceeds ~3 nights.
