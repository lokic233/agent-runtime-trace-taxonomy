# Safety-Gate Evaluation — Phase 7 (FINAL)

**Question:** Does *safety-gated HYBRID1* beat *always HYBRID1* on total token saving under the same regression ceiling?

## Result: NO — there is no frontier to improve

Policy comparison on 167 held-out tasks (C0 baseline = 160 resolved):

| policy | solved | regressions | task-level token saving |
|--------|:---:|:---:|:---:|
| always_C0 | 160 | 0 | 0% (baseline) |
| **always_HYBRID1** | 160 | 4 | **~0% (median −0.8%, mean −30%)** |
| oracle_safe (non-deployable) | 164 | 0 | 0% |
| length_gate (n_obs>34→C0) | 162 | 0 | 0% |
| random_gate (20%→C0) | 158 | 4 | 0% |

## Why the controller claim fails

The primary controller claim requires **safety-gated HYBRID1 > always HYBRID1 on saving at equal regression ceiling.** This is impossible here because:

1. **HYBRID1 provides no task-level token saving to preserve** (Phase 5 + Phase 6: median ~0%, mean negative). A safety gate can only *reduce regressions* by routing tasks back to C0 — but routing to C0 also forgoes any (nonexistent) saving. There is no saving/regression tradeoff to optimize because the saving axis is ~0.

2. **The regressions are noise, not a learnable signature** (Phase 3/4). The 4 held-out regressions are different tasks from the golden-50 "fragile" set. A gate trained on golden-50 fragility cannot predict held-out regressions that are themselves random run-to-run flips.

3. **Length-only gate is falsified** (in-sample from Phase 7-dev: the 1 golden regression pylint-4551 had FEWER observations than safe tasks; on held-out, length_gate achieves 0 regressions only by routing ~3% of tasks to C0, gaining nothing in saving).

4. **Even the oracle gate** (cheating — uses outcomes) only raises solve from 160→164 with 0 token saving. The *ceiling* of any gating strategy is "preserve solve rate at ~0 saving" — which is what always_C0 already achieves at 0 regressions.

## Verdict
**SAFETY_GATE_VERDICT: NO_INCREMENTAL_VALUE.** Safety gating cannot improve the frontier because there is no positive-saving frontier point to protect. The only way to get 0 regressions is to not prune (always_C0), which is exactly the baseline. Gating HYBRID1 reduces its (noise) regressions but recovers no token value.

This is a direct consequence of the upstream null result: if pruning saves nothing at task level, admission control for pruning has nothing to admit.
