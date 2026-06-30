# Fragility Replication — Phase 4 (FINAL)

Repeated runs of the 10 outcome-changing tasks under C0 (identity), SHAM (no-op code path), and HYBRID1 (pruning), each multiple times, classified per the protocol's 5-way scheme.

## Classification results

| task | C0 reps | HYBRID1 reps | classification | v2 claim |
|------|---------|--------------|----------------|----------|
| pylint-4551 | [0,0,0,0,0] | [0,0] | **baseline-FAIL** (not fragility) | "universal canary" ❌ |
| pytest-6197 | [1,1,1,1,1] | [1,1] | **baseline-PASS** (not improvement) | "universal improvement" ❌ |
| pylint-6386 | [1,1,1,0,1] | [1,0] | INHERENTLY_UNSTABLE | — |
| sphinx-8638 | [0,0,1,0,1] | [0,1] | INHERENTLY_UNSTABLE | "regression" ❌ |
| sphinx-9658 | [1,1,1,0,1] | [1,1] | INHERENTLY_UNSTABLE | — |
| sympy-13091 | [1,1,1,1,1] | [0,1] | INHERENTLY_UNSTABLE | — |
| sympy-14248 | [0,1,1,1,1] | [0,1] | INHERENTLY_UNSTABLE | "regression" ❌ |
| sympy-19040 | [1,1,1,1,0] | [1,1] | INHERENTLY_UNSTABLE | "regression" ❌ |
| astropy-14096 | [1,1,1,1,1] | [1,1] | stable-pass | "regression" (AGG3/M7) ❌ |

## Summary
- **TRUE_PRUNING_FRAGILITY: 0 tasks** — no task where C0+SHAM are stable-pass AND pruning repeatedly fails with pruning activated.
- **TRUE_PRUNING_IMPROVEMENT: 0 tasks** — no task where C0+SHAM repeatedly fail AND pruning repeatedly solves.
- **INHERENTLY_UNSTABLE: 6 tasks** — outcome flips across identical baseline reps.
- The two headline tasks both resolve to baseline-determined outcomes: pylint-4551 (baseline reliably fails), pytest-6197 (baseline reliably solves).

## The pylint-4551 story (the "universal canary" debunked)
In the original golden-50 grading, C0 resolved pylint-4551 once and every pruning method "failed" it → it looked like a universal pruning canary. On 5 fresh C0 identity reps, the baseline resolves it **0/5 times**. The original single pass was the statistical outlier; pylint-4551 is simply a hard task the agent usually fails. The "canary" was the noise, not the rule.

## The pytest-6197 story (the "universal improvement" debunked)
Original golden-50: C0 failed it, every pruning method "solved" it → looked like pruning helps. On 5 fresh C0 reps, the baseline solves it **5/5 times**. The original single failure was the outlier. Pruning didn't fix anything.

## Verdict
**CANARY_VERDICT: NOT_SUPPORTED. IMPROVEMENT_VERDICT: STOCHASTIC_FLIP.**
The per-task pruning narrative collapses entirely under replication. Both claims were single-sample artifacts in the original golden-50 grading.
