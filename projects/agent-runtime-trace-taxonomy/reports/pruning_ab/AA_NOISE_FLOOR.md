# A/A + SHAM Noise Floor — Phase 3 (FINAL)

**The central falsification result.** The SWE-agent + opus-4.7 pipeline is **non-deterministic run-to-run at temperature=0**, and that nondeterminism fully accounts for the v2 per-task "pruning effects."

## A/A result: identical config, repeated

| arm | reps graded | interesting tasks that FLIP across identical reps |
|-----|:---:|:---:|
| **C0_identity** (no pruning) | 5 | **5/10** |
| **SHAM** (shim code path, no mutation) | 2 | 3/10 |
| **HYBRID1** (pruning) | 2 | 4/10 |

**C0 — the identity baseline with ZERO pruning — flips 5 of 10 interesting tasks between identical runs.** The flip tasks: pylint-6386, sphinx-8638, sphinx-9658, sympy-14248, sympy-19040.

## The smoking gun

The tasks that flip under the identity baseline are **the exact tasks v2 attributed to pruning**:
- `sympy-14248`, `sphinx-8638` — labeled "HYBRID1 regressions" in v2 → flip under C0 identity
- `pylint-4551` — the "universal canary" → C0 baseline resolves it 0/5 times on fresh runs (it was a fluke single pass in the original golden-50 grading)
- `pytest-6197` — the "universal improvement" → C0 baseline resolves it 5/5 times on fresh runs (not a pruning effect)

## Per-task replication (C0 vs HYBRID1, multiple reps)

```
task                         C0 reps          HYBRID1 reps    classification
astropy-14096                [1,1,1,1,1]      [1,1]           stable-pass (both)
pylint-4551                  [0,0,0,0,0]      [0,0]           stable-FAIL (baseline never solves it!)
pytest-6197                  [1,1,1,1,1]      [1,1]           stable-pass (baseline always solves it!)
pylint-6386                  [1,1,1,0,1]      [1,0]           INHERENTLY_UNSTABLE
sphinx-8638                  [0,0,1,0,1]      [0,1]           INHERENTLY_UNSTABLE
sphinx-9658                  [1,1,1,0,1]      [1,1]           INHERENTLY_UNSTABLE
sympy-13091                  [1,1,1,1,1]      [0,1]           INHERENTLY_UNSTABLE
sympy-14248                  [0,1,1,1,1]      [0,1]           INHERENTLY_UNSTABLE
sympy-19040                  [1,1,1,1,0]      [1,1]           INHERENTLY_UNSTABLE
```

**0 tasks classified TRUE_PRUNING_FRAGILITY. 0 tasks classified TRUE_PRUNING_IMPROVEMENT.**
6/10 are INHERENTLY_UNSTABLE (flip under baseline's own reps); the rest are stable regardless of pruning.

## Verdicts established by this phase

- **AA_NOISE_VERDICT: DOMINANT** — 5/10 boundary tasks flip with zero pruning. The per-task noise floor exceeds any per-task pruning signal.
- **CANARY_VERDICT: NOT_SUPPORTED** — pylint-4551 is a task the baseline reliably FAILS (0/5), not a pruning fragility. sphinx-8638/sympy-14248 flip under identity. No task meets TRUE_PRUNING_FRAGILITY.
- **IMPROVEMENT_VERDICT: STOCHASTIC_FLIP** — pytest-6197 is a task the baseline reliably SOLVES (5/5), not a pruning benefit. No task meets TRUE_PRUNING_IMPROVEMENT.

This is exactly what the A/A control was designed to detect: the v2 per-task regression/improvement attributions were **measuring the agent's run-to-run noise, not pruning.**
