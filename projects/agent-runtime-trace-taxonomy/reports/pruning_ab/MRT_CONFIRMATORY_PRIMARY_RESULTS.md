# MRT Confirmatory (Study 2) — Primary Results

**N = 70 randomized interventions.** All numbers auto-derived from immutable artifacts.
Independent of Study 1 (new tasks, seed 20260702). Estimates are effect-size + CI.

## Primary estimand — ITT ATE(H1), LINEDEDUP − NO_OP (lower=better)
| quantity | value |
|---|---|
| ATE(H1) | -994.9 |
| bootstrap 95% CI | [-2430.0, 370.0] |
| repo-clustered 95% CI | [-2074.0, 163.0] |
| CI half-width | 1400.0 |
| mean LINEDEDUP / NO_OP | 5460.0 / 6455.0 |

## ATE(H3)
estimate -500.9, 95% CI [-3593.0, 2685.0].

## Primary moderator — interaction beta3 (block-permutation inference)
- descriptive b3 = -260.9 (robust SE 2286.1, center dup_frac 0.351)
- **block-respecting randomization test p = 0.914** (5000 permutations)

## CATE by stratum
{
 "HIGH_REDUNDANCY": {
  "n": 30,
  "estimate": -515.8562499999998
 },
 "MIXED_REDUNDANCY": {
  "n": 40,
  "estimate": -1307.1324999999988
 }
}
