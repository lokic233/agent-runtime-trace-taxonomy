# MRT Confirmatory (Study 2) — Power & Precision (Part V)

Auto-generated from `results/pruning_ab/mrt_confirmatory/power_precision.json`.
**Variance source: Study 1 (N=13) ONLY** — no Study-2 outcomes exist yet. H1 SD≈3285
(CV≈0.53), dup_frac mean 0.31 (SD 0.26).

Simulated the ACTUAL Study-2 estimators (blocked ATE, block-FE interaction b3, 2:2 assignment,
continuous moderator) at each N. 2000 sims/cell.

## Frozen practically-relevant effects
- ATE MDE = **−570** eff-cost (~10% of mean) · interaction MDE b3 = **−2000** · target power 0.80 · α 0.05.

## Power AND CI half-width vs N

| N | power(ATE) | power(b3) | ATE 95% CI half-width | b3 95% CI half-width |
|---:|---:|---:|---:|---:|
| 60 | 0.11 | 0.08 | ±1666 (27%) | ±7840 |
| 100 | 0.16 | 0.12 | ±1293 (21%) | ±5958 |
| 120 | 0.18 | 0.12 | ±1178 (19%) | ±5419 |
| 160 | 0.23 | 0.13 | ±1020 (16%) | ±4659 |
| 200 | 0.26 | 0.17 | ±915 (15%) | ±4166 |
| 300 | 0.38 | 0.21 | ±745 (12%) | ±3373 |
| 400 | 0.47 | 0.27 | ±647 (10%) | ±2925 |

## The honest headline
**80% moderator (b3) power is INFEASIBLE at any N ≤ 400** (power_b3 = 0.27 even at N=400).
ATE power reaches only 0.47 at N=400. The Study-1 H1 variance (CV≈0.53) is simply too
large relative to a 10% effect. **We do NOT pretend N=60 is "powered."**

## Frozen stopping rule (precision-based)
- **Mode:** precision.
- **Primary precision target:** 95% CI half-width on ITT ATE(H1) <= 1000 eff-cost units (~16% of the Study-1 control mean 6236)
  → expected at **~160 eligible randomized events (from simulation grid)**.
- **Hard floor:** >=60 eligible events, >=25/arm, both strata, >=5 repos (protocol minimum for a reportable confirmatory contrast).
- **Stop when:** (a) ATE CI half-width <= 1000 reached AND >=60 events; OR (b) all buildable pool tasks attempted (compute/pool exhaustion).
- **Never:** never stop on an observed p-value, effect sign, or favorable trend.

> 80% moderator (b3) power is INFEASIBLE at N<=400 given Study-1 variance (power_b3=0.27 at N=400). Study 2 is therefore a PRECISION study for the ATE + a descriptive/underpowered test for the moderator. This is declared BEFORE any Study-2 outcome.

## Task-pool sizing (from observed availability)
Study 2 draws **new** tasks (not in Study-1) from SWE-bench Verified (500 total; Study-1 used 18).
The golden-50 availability rate is an UPPER BOUND (that pool was pre-selected for availability). A
random-Verified availability rate must be measured by an **eligibility dry-run** (Part-VII step 7)
before freezing the task-pool size. At an assumed ~40-70% per-task availability and single-shot ×
newest-only (≤1 intervention/task), reaching ~160 eligible events needs roughly **230-400 buildable
tasks**. The dry-run replaces this assumption with the audited rate.

## Design decision (declared before outcomes)
Study 2 is a **PRECISION study for the ATE** + a **descriptive/underpowered test for the moderator
b3**. The confirmatory verdict for REDUNDANCY_CAUSAL_MODERATOR will almost certainly be
UNDERPOWERED unless the true effect is very large; this is acceptable per the mission.
