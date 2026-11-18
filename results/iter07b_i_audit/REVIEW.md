# Iteration 07b-i — Which unseen target can confirm a label-free local-s₀ estimator? (read-only audit)
**Goal:** find an on-disk dataset that can serve as an unseen target for a pre-registered label-free local-s₀ rung with an own-load term. No estimator is computed on any candidate.
**Branch / commit:** iter/07b-i-target-audit @ f4334a4 (brief 7abe655)
**Changed:**
- `scripts/audit/target_audit_07bi.py`: about 350 logic lines (lines that are not blank, comments or docstrings; over the ~300 budget, mostly fact dictionaries).
- Configs `iter07b_i_{audit,quick}.yaml`.
- Results:
  - `inventory.md` (criteria table, Task 3), `method_basis.md`, `facts.{md,json}`, `metrics.csv`;
  - `be_series.csv`, `fluvius24_files.csv`, `feederbw_{feeders,s0}.csv`, `envelopes.csv`;
  - `log.txt` (every file opened, including interactive inspection), `quick/`.
- Caches: `data/_paperb/iter07bi{,_quick}/` (5 MB).

**Results** (descriptives only; slopes in kW/K; 07 reference s₀ CH 0.0054, GB 0.0126; CH own-load slope 0.018 per HP home):

| candidate | HP label → `HL` | local non-HP s₀ | own-load slope | size (v1.1) | verdict |
|---|---|---|---|---|---|
| **NEEA HEMS** (US) | HP + backup circuits, from target data | 49 fill homes. T ≤ 18 °C: WA 0.0268, ID 0.0139, OR 0.0153. All-days fit fails (cooling): T_h at bound | **0.0119 [0.0038–0.0334]** (76) | 77 HP, 49 fill. Fill-limited: ≤ 10 dwellings, 45 test substations, none > 65 % | **recommended** (after download) |
| **FeederBW** (DE) | registry kW (semantics UNVERIFIED); no source mapping | no-HP, no-electric-heating feeders: 0.003–0.004 for the 3 without PV or commerce | not observable | real: 11 clean HP feeders (165 / 200 have electric heating) | **fallback** |
| Fluvius 2024 (BE) | HP flag only | 300 `geen_ZP` meters; T not on disk | embedded, not separable | 300 HP + 300 fill: 125 test substations, max 80 | side check only |
| BE monitoring | HP submeter, DER peak 3.79 kW | none (Fluvius would be the fill) | 6 homes; mostly at bound, R² ≤ 0.45 | 9 complete → no substation | own-load source at most |
| UKPN, HEAPO beyond B\*, Kaiser cal2024, WPuQ, RHPP, BPA / NREL, LCL-HP, EoH extras | — | — | — | — | rejected: no heating season; fill or homes already used; no fill; Paper A exposure; too small (`inventory.md`) |

**Assumptions & deviations:**
- I added the BE monitoring sets and the Fluvius 2024 sample, which are on disk but were not in the brief's list. The HEAPO total-only meters are listed but rejected (count label, fill already used).
- s₀ for NEEA is also fitted on days T ≤ 18 °C, a descriptive variant because the all-days fit hits the T_h bound. For FeederBW, s₀ per housing unit comes from feeders with no registered HP or electric heating; this uses registry zeros.
- BE own load = P1 (signed net) + |PV| − HP − buffer resistor, for HP homes without a battery. PV is taken as |PV| because its sign flips between homes.
- NEEA HP homes are counted without 04's "fully submetered" cut (s_res ≤ 0.2 s_heat). That cut selects on the own-load slope and halves it (0.0069 vs 0.0119).
- `config.yaml` records commit 7abe655, because the runs used the then-uncommitted script that f4334a4 commits unchanged.

**Problems found:**
- **No clean target exists on disk.** NEEA has every ingredient, but its fill caps feeders at 10 dwellings (noisy slopes, no > 65 % bin) and only cal2023 is on disk.
- FeederBW: electric heating is registered on 165 of 200 feeders. The registry semantics are unverified, and no source-only label mapping exists: B\* has nameplate data for 1 household.
- **The own-load / filler ratio does not look transferable:** CH 3.3 vs NEEA about 0.4–0.9. This is a risk for form (b-i).
- BE monitoring:
  - provenance and licence are unknown;
  - the HP meter is renamed in 2025 (`hp` → `hp1`);
  - PV sign is inconsistent;
  - 12 of 18 HP homes have batteries.
- The first full run crashed on FeederBW fits with negative daily load (PV export). Such fits are now listed as failures (2 of 20), not dropped.
- Exposure:
  - legacy Paper B scored FeederBW and WPuQ;
  - Paper A used NEEA (Table II) and RHPP, BPA and NREL (Table VI);
  - while checking exposure I saw legacy WPuQ errors in the iter00 REVIEW.

**Decisions for Alex:**
1. **07b target.**
   - *Recommended:* NEEA HEMS, full release, as the primary target. It is the only candidate with a submeter label, a local non-HP fill, observable own load and temperature.
   - Fallback: FeederBW real feeders without registered electric heating (11 HP + 24 non-HP), scored against registry kW with a sensitivity band.
2. **Forms to pre-register at NEEA.**
   - *Recommended:* (b-ii), `paperA_corr_own` with a local pilot (whole-house − HP on train homes; not fully label-free, stated as such), as the rung required by Decision 2.
   - (a) `paperA_corr` with local s₀ and transferred CH and GB m_h, as its ablation.
   - (b-i) with ρ from CH, as a secondary row (expected weak).
   - (c) the frozen 07 rows L1 TabPFN and H\* for comparison.
   - Pre-register a heating-side fit window (T ≤ 18 °C or Nov–Mar), and do not reuse 04's s_res cut.
3. **Downloads and requests:**
   - NEEA v9.2 `POWER15` and `TEMPERATURE15` files for 2018-08 to 2025-06, via NEEA's data request (more seasons and more fill homes);
   - for the fallback, the FeederBW paper's metadata section (what `heat_pumps_kW` registers);
   - the provenance and licence of the BE monitoring sets;
   - optional: KMI or Open-Meteo 2024 temperature for Flanders (Fluvius side check), and UKPN winter months (login).
