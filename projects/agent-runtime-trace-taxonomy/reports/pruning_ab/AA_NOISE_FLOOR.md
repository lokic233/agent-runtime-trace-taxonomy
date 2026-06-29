# A/A + SHAM Noise Floor — Phase 3 (PRELIMINARY, accumulating reps)

**Status: 1 of 5 C0 reps complete. Early signal is decisive enough to record; final numbers pending reps 2-5 + SHAM + HYBRID1.**

## The central question
Are HYBRID1's golden-50 "regressions" (pylint-4551, sphinx-8638, etc.) and "improvement" (pytest-6197) caused by **pruning**, or are they **stochastic flips** the identity baseline also exhibits run-to-run?

## Early A/A result (C0 original golden-50 vs C0 fresh rep1 — IDENTICAL config, NO pruning)

| task | original C0 | fresh C0 rep1 | flipped? | role in v2 claims |
|------|:---:|:---:|:---:|------|
| pylint-dev__pylint-4551 | ✓ resolved | ✗ failed | **FLIP** | the "universal canary" (HYBRID1 regressed) |
| pytest-dev__pytest-6197 | ✗ failed | ✓ resolved | **FLIP** | the "universal improvement" (HYBRID1 fixed) |
| sphinx-doc__sphinx-8638 | ✓ resolved | ✗ failed | **FLIP** | a HYBRID1 "regression" |
| sympy__sympy-14248 | ✓ resolved | ✗ failed | **FLIP** | a HYBRID1 "regression" |
| astropy-14096, pylint-6386, sphinx-9658, sympy-13091, sympy-19040 | ✓ | ✓ | stable | — |

**4 of 10 interesting tasks flip outcome between two identical C0 runs.** The flipped set is *exactly* the tasks the v2 analysis attributed to pruning.

## Provisional interpretation (pending reps 2-5)

The SWE-agent + opus-4.7 pipeline is **non-deterministic run-to-run** even at temperature=0 (likely API-level nondeterminism + tool-execution timing/ordering). The "canary" and "improvement" tasks are precisely the ones sitting near the agent's success/failure boundary — they flip on **any** re-run, pruning or not.

If this holds across reps 2-5, then:
- **CANARY_VERDICT → NOT_SUPPORTED** (pylint-4551 flips under identity baseline; not a pruning fragility)
- **IMPROVEMENT_VERDICT → STOCHASTIC_FLIP** (pytest-6197 flips under identity baseline; not a pruning benefit)
- **AA_NOISE_VERDICT → MATERIAL or DOMINANT** (a single flip cannot be attributed to pruning when the baseline flip rate is ~40% on these boundary tasks)

This would mean the v2 per-task "regression/improvement" claims were **measuring noise, not pruning** — the most important falsification finding of the whole study, and exactly what the A/A control was built to detect.

## Caveat
n=1 rep. The 40% flip rate is on the 10 *deliberately-selected boundary tasks* (the outcome-changing ones), NOT on stable tasks — so it is an upper bound on the boundary noise, not the suite-wide rate. Reps 2-5 + SHAM will give the real distribution. Recorded now because the direction is already clear and the apparatus is validated.
