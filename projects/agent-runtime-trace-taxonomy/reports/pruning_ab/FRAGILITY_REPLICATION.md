# Fragility Replication — Phase 4 (FINAL, 5 reps each)

5 reps each of C0 (identity), SHAM (no-op code path), HYBRID1 (pruning) on the 10 outcome-changing tasks. Classified per the protocol's 5-way scheme.

## Final classification (15 cells)

| classification | count | tasks |
|----------------|:---:|-------|
| TRUE_PRUNING_FRAGILITY | **0** | — |
| TRUE_PRUNING_IMPROVEMENT | **0** | — |
| INHERENTLY_UNSTABLE | **9** | pylint-4551, pylint-6386, pylint-8898, pytest-6197, sphinx-8638, sphinx-9658, sympy-13091, sympy-14248, sympy-19040 |
| STABLE_NO_EFFECT | 1 | astropy-14096 |

## The SHAM control is decisive

| arm | tasks flipping across 5 identical reps |
|-----|:---:|
| C0 identity (no pruning) | 5/10 |
| **SHAM (byte-identical messages, no pruning)** | **8/10** |
| HYBRID1 (pruning) | 7/10 |

**SHAM flips MORE tasks than HYBRID1.** Since SHAM applies zero pruning (it only exercises the deepcopy/recount code path and returns identical messages), the instability is **provably pipeline nondeterminism, not pruning.** No honest classification can call any task a "pruning fragility" when the no-op control flips it as much or more.

## The two headline claims, killed with replication
- **pylint-4551 "universal canary":** C0 resolves 0/5. A reliably-failed task. The original golden-50 grading caught its one lucky pass; every pruning method "failing" it was just the method matching the agent's usual failure. NOT a canary.
- **pytest-6197 "universal improvement":** C0 resolves 5/5. A reliably-solved task. The original grading caught its one unlucky failure; every method "solving" it was the agent's usual success. NOT an improvement.

## Verdict
**CANARY_VERDICT: NOT_SUPPORTED. IMPROVEMENT_VERDICT: STOCHASTIC_FLIP.**
Zero tasks meet the TRUE_PRUNING_* bars. The entire per-task pruning narrative is run-to-run noise, definitively demonstrated by the SHAM control flipping more than the pruning arm.
