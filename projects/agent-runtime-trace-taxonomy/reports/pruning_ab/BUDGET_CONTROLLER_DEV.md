# Phase 5 — Budget Controller Development

Development-stage controller construction & evaluation. **Outcome: no deployable policy beats the best static method; controller NOT justified on current signals.** (Full numbers in ORACLE_GAP.md; this documents the controller-building process.)

## Candidate policies evaluated (development data, 49 tasks)
| policy | rule | total eff-cost saving vs C0 |
|--------|------|---:|
| always_C0 | no pruning | +0.0% |
| always_LINEDEDUP | prune every task | +5.9% |
| **always_GENTLE6K** | cap dumps every task | **+10.1%** (best static) |
| dup>0.20 → LINEDEDUP else C0 | Tier-1 threshold | +9.2% |
| dup>0.25 → LINEDEDUP else C0 | Tier-1 threshold | +9.3% |
| dup>0.30 → LINEDEDUP else C0 | Tier-1 threshold | +7.0% |
| oracle (post-hoc per-task min) | uses outcomes | +27.0% (upper bound) |

## Construction method
- Only **Tier-1 deployable features** permitted (dup_line_ratio etc.; baseline_calls/tokens forbidden — TRACE_FEATURE_DICTIONARY.md).
- Threshold candidates from the dup_line_ratio distribution; **selected by best dev saving** (deliberately optimistic — in-sample tuning).
- Simple interpretable thresholds preferred over ML (n too small for learned policies — CAUSAL_ESTIMANDS.md power note).

## Result & decision
The best deployable trace policy (+9.3%) is **worse than the constant always-GENTLE6K (+10.1%)**, despite the threshold being tuned in-sample. Even with optimistic tuning, the trace signal cannot route tasks better than a fixed choice → **a controller using these features adds no value over picking the single best static method.**

A genuine controller would require either (a) features that pass the negative control and predict method-specific CATE (none found — HETEROGENEOUS_TREATMENT_EFFECTS.md), or (b) far more data to fit a calibrated risk model (UNDERPOWERED at n=49 cost / 10 success).

## Quality budget overlay (could not be applied)
GENTLE6K's +10.1% carries 1 regression and LINEDEDUP's +5.9% carries 2 (unresolved attribution). With only 10 repeated-run tasks, the quality-loss UB cannot be calibrated per-policy → quality-budgeted controller selection is **UNDERPOWERED** (CONTROLLER_PREREGISTRATION.md preregisters the test for future untouched data).

## Verdict
**DEPLOYABLE_CONTROLLER_VALUE: NOT_SUPPORTED.** Best trace policy < best static method on dev data with in-sample tuning.
