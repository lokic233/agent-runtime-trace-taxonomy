# Safety-Gate Evaluation — Phase 7

**Goal:** Can a frozen pre-treatment predictor P(regression | baseline/prefix trace) improve the frontier — i.e. does *safety-gated HYBRID1* beat *always HYBRID1* on total saving under the same regression ceiling?

## Status: BLOCKED by label sparsity on dev data; depends on Phase 6 held-out regressions

### The dev-data problem
HYBRID1 produced **exactly 1 regression on golden-50** (`pylint-4551`). You cannot fit or validate a generalizable safety predictor on a single positive label — any model that "works" is memorizing one task. The protocol's candidate features (trajectory length, n_observations, obs-token concentration, early-evidence distance, etc.) were extracted from C0 baseline trajectories (pre-treatment, no candidate-run leakage) into `results/pruning_ab/safety_features_golden50.json`.

### The length-only gate is ALREADY FALSIFIED on dev data
The simplest candidate gate is "flag tasks with long trajectories as unsafe." It fails on golden-50:

| task | n_observations | HYBRID1 outcome |
|------|---:|------|
| `pylint-4551` | 69 | **REGRESSED** |
| `pytest-6197` | 77 | safe (improved) |
| `sympy-14248` | 77 | safe |
| `sympy-19040` | 76 | safe |

The single regressed task is **NOT** the longest — three SAFE tasks have MORE observations. So a length threshold that catches pylint-4551 would also flag 3+ safe tasks (false positives), destroying any saving advantage. **Trajectory length does not separate fragile from safe**, even in-sample.

### What this means for the controller claim
The primary controller claim — *safety-gated HYBRID1 > always HYBRID1* under the same regression ceiling — requires (a) enough regressions to fit a non-trivial gate and (b) a feature that generalizes. On dev data, (a) fails (n=1) and the length proxy for (b) is already falsified.

### Resolution path (Phase 6 dependency)
Phase 6 runs HYBRID1 on 167 held-out tasks. If it produces ≥8-10 regressions, we can:
1. Fit the frozen gate on golden-50 features (or define it by hypothesis), freeze it.
2. Evaluate on held-out: always-C0 / always-HYBRID1 / oracle / frozen-gate / random-gate / length-only.
3. Test whether frozen-gate-HYBRID1 > always-HYBRID1 on saving at equal regression ceiling.

If Phase 6 produces **few/no regressions** (likely, given golden-50 had 1/50≈2%), then:
- the regression rate is too low to gate against (you can't beat a 2% base rate with a noisy predictor), AND
- combined with the Phase 5 finding that HYBRID1 doesn't save task-level tokens anyway, **safety gating has no frontier to improve**.

### Provisional verdict (pending Phase 6)
**SAFETY_GATE_VERDICT: INCONCLUSIVE** → likely **NO_INCREMENTAL_VALUE**. The length-only baseline is already falsified in-sample, and the regression signal is too sparse (1/50) to fit a gate that generalizes. Final determination after held-out regression counts land.
