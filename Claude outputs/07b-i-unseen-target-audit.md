# Iteration 07b-i — Which unseen target can confirm a label-free local-s₀ estimator? (read-only audit)

**Branch:** `iter/07b-i-target-audit`, from `main` after 07 is merged.
**Type:** a read-only audit, like 04: code in `scripts/audit/`, results in `results/iter07b_i_audit/`. About 300 logic lines. No queued runs are expected.
**Blindness rule (hard):** compute **no estimator, prediction or error metric** on any candidate. Allowed:
- descriptive statistics of labels, inputs and coverage;
- s₀ of non-HP samples (a label-free input statistic, needed to size the shift).

Any candidate you touch beyond that is no longer unseen. If in doubt, ask.

## Why
07 showed what transfers and what does not:
- The non-HP temperature response s₀ differs 2.3× between CH and GB. It drives the physics bias, and it enters every slope-based ML input.
- A physics row with s₀ taken from the target's own non-HP households did best in transfer. In GB→CH part of that score was bias cancellation (DECISIONS 2026-11-18).

Both pools are now spent for confirmation. A label-free local-s₀ estimator can only become a paper contribution if it is pre-registered and tested on a target nobody has used (Decision 2, 2026-11-18). This audit finds that target. It also says what the estimator must look like there, including the HP homes' own non-HP load.

## Decisions this depends on (quote)
- `2026-11-18 | 07b | Decision 2: …` (audit first; no estimator on candidates; the rung must include the own-load term).
- `2026-11-18 | plan | Decision 1: …` (the reframing).
- `2026-11-18 | 07 | Reading of the label-free target-s0 row …`.
- CLAUDE.md §4 (household-disjoint, no stacking, v1.1 grid) and §7 (data map). Hard rules 1 and 11.

## Task 1 — Candidate inventory
Cover at least the candidates below. Add any other on-disk dataset you find, and say why each one qualifies or not.

| Candidate | Why it may qualify |
|---|---|
| FeederBW (DE) | real feeders, registry HP kW |
| UKPN LV-feeder smart-meter consumption + LCT (secondary substations) | real GB feeders, registry HP counts |
| WPuQ (DE) | HP and household loads metered separately on the same houses, so own-load is observable |
| RHPP (GB 2013–15) | metered HP, installer capacity, concurrent LCL fillers Nov 2013 – Feb 2014; no temperature on disk |
| HEAPO households not in B\* | CH; daily and 15-min; protocols |
| Kaiser cal2024 | CH; temporal, mostly the same homes, so **not unseen households**: mark it so |
| Fluvius 15-min (BE) | check what it contains |
| `lcl_heatpump` | — |
| NEEA, BPA HPHC, NREL CCASHP, Cofactor, Carleton | US/CA |

## Task 2 — Criteria table (one row per candidate)
1. **HP label**
   - Type: submeter peak, nameplate, registry kW or count.
   - Quality: noise, missingness.
   - Mapping to `HL`: what is needed, and whether that mapping can come from source data only. For example, HEAPO nameplate vs observed peak at household level.
2. **Aggregation:** semi-synthetic (households) or real feeders. For real feeders: the number of feeders, dwellings per feeder, and how many have changing HP counts.
3. **Temperature:** on disk, or needs a download (say from where; Alex downloads). Station match.
4. **Local non-HP sample for s₀:** non-HP households in the same area and period, or a label-free feeder-level route. Report the s₀ value and spread where computable.
5. **Own-load observability:** whole-house and HP metering on the same homes, or another route. Give the own-load slope where computable (CH: 0.018 kW/K per HP home).
6. **Resolution, period** and calendar overlap with a CH or GB pilot.
7. **Disjointness** from B\* and GB-EoH households (state how it is checked).
8. **Size:** HP households, or feeders; the design envelope under v1.1 with no stacking.
9. **Access and licence;** anything not on disk.

## Task 3 — Rung requirements per viable candidate
For each candidate that passes the criteria, state which of these label-free estimator forms it supports. Do not compute them.
- (a) `paperA_corr` with local s₀ and a transferred pilot m_h.
- (b) (a) plus an own-load term. Label-free options to evaluate on paper only:
  - a transferred own-load/filler slope ratio;
  - a whole-house − HP route on local pilot homes, if the target has them (then it is not fully label-free: say so).
- (c) The same frozen ML rows as 07 (L1 TabPFN; H\*), for comparison.

For each, give the label mapping it needs, the effort to build the target (code lines, hours), and the risks.

## Out of scope
- Any estimator, prediction or error on candidates.
- Building pools.
- Pre-registering the rung: the orchestrator writes 07b from this audit.
- Downloads: list them; Alex downloads.

## Deliverables
- `results/iter07b_i_audit/inventory.md`: the criteria table and Task 3.
- `method_basis.md`: references for label mappings or registry quality, checked or UNVERIFIED.
- `REVIEW.md` (§9). Its decisions are:
  1. the recommended target(s) for 07b, with one fallback;
  2. which estimator forms 07b should pre-register there;
  3. what Alex must download or request.

Then stop.

## Acceptance
- [ ] No estimator, prediction or error computed on any candidate. `log.txt` lists every file opened.
- [ ] `data/` untouched (new caches only under `data/_paperb/`); `models/` untouched.
- [ ] References checked or UNVERIFIED. Push to the branch only; never merge.
