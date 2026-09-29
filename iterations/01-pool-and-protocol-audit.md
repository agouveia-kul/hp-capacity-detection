# Iteration 01 — Pool capacity and protocol design audit (read-only)

**Branch:** `iter/01-pool-audit`, from `main` once `iter/00-baseline` is merged.
**Type:** read-only analysis. **No changes** to the pipeline, targets, models or legacy scripts. New code is limited to counting/audit scripts (target ≤ 300 logic lines).

## Why this iteration
Iteration 00 showed that the binding constraint is the household pool, not the model:
- only 57 HEAPO HP households, of which 27 seed the train substations;
- each HP profile is stacked 16.7× in the largest substations;
- 1786 of 2160 substations reuse a household as both an HP member and a fill member;
- 2 of 57 households have a nameplate value.

Before iteration 02 implements the new protocol, we need hard numbers on how large a clean, household-disjoint pool can be, and which design it permits. The output of this iteration is a **protocol specification for Alex to approve**, not results.

## Task 0 — bookkeeping (first commit)
1. Create `DECISIONS.md` at the repo root. It is an append-only log with one line per decision: `date | iteration | decision | rationale`. Add the three decisions resolved in iteration 00:
   - the legacy CSVs are the official baseline;
   - the recovered scripts are trusted, and XGBoost-tuned numbers are single-seed;
   - the ~660-line infrastructure diff is accepted.
2. Update CLAUDE.md:
   - §10: replace the "81 vs 57" bullet with the facts from iteration 00. These are the 57-household HEAPO 2023 pool (29/28 split, 27 effective train seeds), 16.7× stacking, the HP/fill overlap in 1786/2160 substations, selection instability (k* 60 vs 40 across hyperopt seeds), and leaky CV (≈20 vs 44–55 kW).
   - §3: add rule 10: "Hyperopt and every stochastic search must be seeded (`HYPEROPT_FMIN_SEED` or `rstate`)."
   - §2 or §6: add a pointer to `DECISIONS.md`.

## Task 1 — Pool inventory
Write `scripts/audit/pool_inventory.py` → `results/iter01_pool_audit/pool_inventory.csv` and `.md`.

For each candidate source, count **distinct households** that meet each requirement. Count per weather station and per heating season (Nov–Mar, 2019/20 … 2024/25), with ≥ 90 % coverage.

| Source | Unit | Requirements to count |
|---|---|---|
| HEAPO 15-min | household | (a) HP submeter + other load; (b) total load only |
| HEAPO daily | household | (a) HP submeter daily; (b) total daily |
| Kaiser (Swiss_dataset) | object/meter | (a) dwelling + paired HP meter; (b) dwelling without any TCL flag (clean fill); (c) dwellings per TCL flag (`1_hp-add`, `1_ewh`, `1_storage_heating`, `1_direct_heating`); (d) `2_hp_control` / `2_wh_control` |
| WPuQ | house | HP + household, 2019 and 2020 separately |

Cross-tabulate the following:
- **Nameplate:** HEAPO protocol households with `Normpoint_ElectricPower` (and, separately, `HeatingCapacity`) × data availability, i.e. 15-min HP submeter / 15-min total / daily total, per season.
- **Station compatibility:** which HEAPO stations are identical to MeteoSwiss KLO (8jB is), so HEAPO HP households can share substations with Kaiser fill households.
- **Multi-season households:** households usable in ≥ 2 seasons. These are needed for RQ4; report counts only.

## Task 2 — Feasible design envelope
Write `scripts/audit/design_envelope.py`. It computes the achievable substation grid **without building any load series**; it works on counts and memberships only. Constraints for every option:
- household-disjoint 75/25 train/test split, stratified by station;
- no household appears twice in a substation, whether as HP member or as fill;
- all HP members of a substation share one station and one season.

Evaluate these options:

| Option | HP members | Fill members | Resolution |
|---|---|---|---|
| A | HEAPO 2023 only (legacy pool) | HP households' other load (legacy) | 15-min |
| B | HEAPO(8jB/KLO) + Kaiser paired, 2023 | Kaiser clean dwellings, same season | 15-min |
| C | B + additional seasons (household-seasons; split by **household**, so one household never spans train and test) | Kaiser clean, 2023 + 2024 | 15-min |
| D | HEAPO all stations + Kaiser, daily data | HEAPO/Kaiser daily totals | daily |

For each option, report:
- the number of distinct HP households in train and test;
- the maximum feeder size at penetration p ∈ {0.1, 0.2, 0.3, 0.5, 0.7, 1.0};
- the number of distinct HP-member combinations available at a few representative (size, p) cells. The point is to show where the grid saturates.
- which targets are feasible and on how many households: `HP_Peak`, `HP_CoincPeak`, `HP_Count`, `HP_Nameplate_el`, `s_h`, `r`, `P_design`.

Output `design_envelope.md` with one table per option and one comparison table.

## Task 3 — Remaining ML-pipeline audit (code reading)
Iteration 00 covered splits, stacking, CV and seeds. Now check the rest, **without fixing anything**. Write `ml_audit.md`: one row per finding, with the columns `id | file:line | issue | evidence | severity (high/med/low) | proposed iteration`. Check at least:
- **Scale features:** `Feature Scale_peak` (observed peak) with an absolute-kW target. Does it leak target information (for example, peak ≈ HP-dominated at high penetration)? Quantify the correlation of Scale_peak with HP_Peak on test.
- **Preprocessing:** the `weekday_only=True` filter, and 15-min temperature interpolated from hourly data.
- **Missing values:** median-imputation of NaN features with the **train** median, applied to transfer sets; count the NaNs per dataset.
- **Fixed HDD base:** T_base 12/15 °C. Recompute the HDD-bin day counts per dataset to show the bin-population shift.
- **Hockey-stick baseline:** the `T_BALANCE_BOUNDS = (8, 20)` bounds and the heating-season threshold, which interact. How often do fits hit a bound?
- **Metrics:** MAPE computed over non-zero truth only; check whether any zero-target substations exist.
- **FeederBW:** only 2024 is loaded; the metadata start/end logic; how the 26 changed feeders are handled.
- **Notebook-only logic** not yet ported to scripts that later iterations will need, e.g. the SF extension (cells 39–42) and the HDH fits (cells 59–88).

## Task 4 — Protocol specification proposal
Write `configs/protocol_v1_proposal.yaml` and `protocol_v1_proposal.md` (≤ 1 page). They should give:
- the recommended option (A–D, or a combination such as C for the main 15-min analysis plus D for the nameplate and daily arm);
- the split fractions, the number of repeated household splits, and the size × penetration grid;
- the substations per cell;
- the CV scheme for tuning;
- the bootstrap scheme;
- which targets are in and which are out for each option;
- the estimated runtime of one full benchmark under that protocol.

This is a proposal only. Iteration 02 implements it after approval.

## Out of scope
- Building substations or load series (beyond tiny spot-checks).
- Training or evaluating models.
- Fixing any audit finding.

## Acceptance criteria
- [ ] `DECISIONS.md` exists, and CLAUDE.md §2/§3/§10 are updated.
- [ ] `pool_inventory`, `design_envelope`, `ml_audit` and `protocol_v1_proposal` are all in `results/iter01_pool_audit/` (and the proposal YAML in `configs/`).
- [ ] Every count is computed from data. Each table states its source script.
- [ ] `data/` and `models/` are unmodified. `pytest` passes.
- [ ] `REVIEW.md` is written using the §9 template. The decisions must at least cover:
  1. which pool option(s) to adopt;
  2. whether a daily-resolution arm enters the paper, for nameplate and the larger pool;
  3. which audit findings are high severity and must be fixed in iteration 02.
