# Mechanism A — Cache Tax: Causal Test

**Question:** Does rewriting an already-cached prefix causally increase cache-creation cost, independent of the shim/code-path?

## Design (quasi-experiment with a no-op counterfactual)
- **Arms (A/A repeated runs, 10 interesting tasks, 5 reps each, same model/cache):**
  - C0_identity — stable append-only prefix (no transformation)
  - **SHAM — runs the IDENTICAL shim code path but returns byte-identical messages** (controls for the shim itself)
  - HYBRID1_m7_agg2 — recency pruning that rewrites the prefix each step
- **Outcome:** cache_creation_fraction = cache_creation / (cache_read + cache_creation), per task-rep, from provider prompt-cache accounting.

## Result (auto-generated from mechanism_effects.json)

| arm | prefix behavior | cache_creation_fraction | 95% CI | n (task-reps) |
|-----|----------------|------:|:--:|:--:|
| C0_identity | stable append-only | **0.077** | [0.061, 0.098] | 50 |
| SHAM | shim path, byte-identical | **0.066** | [0.051, 0.083] | 50 |
| HYBRID1_m7_agg2 | recency rewrite | **0.784** | [0.733, 0.830] | 50 |

## Causal identification
**SHAM is the counterfactual that isolates the mechanism.** SHAM exercises the exact same shim/deepcopy/re-serialize code path as a pruner, but emits byte-identical messages → its cache_creation_fraction (0.066) is statistically **indistinguishable from C0** (0.077; CIs overlap). HYBRID1, which differs *only* in that it rewrites the prefix by recency, jumps to **0.784** (CI non-overlapping with both C0 and SHAM by a wide margin).

Because SHAM holds the code path constant and varies only prefix stability=stable, while HYBRID1 varies prefix stability=rewritten, the **~10× increase in cache-creation fraction is causally attributable to prefix rewriting**, not to the shim, the transformation machinery, or task selection (same 10 tasks, 5 reps each).

## What is proven vs hypothesis
- **PROVEN (within this provider-prompt-cache setting):** rewriting the cached prefix causes the cache-creation share to rise ~10× (0.07→0.78). Treatment assignment is clean (same tasks, repeated, SHAM no-op control). Confounders controlled: code path (SHAM), task mix (paired), model/cache (held constant).
- **NOT claimed:** GPU KV-cache eviction. This is provider **prompt/prefix cache accounting** only (closed API). We do not instrument KV residency.
- **Effective-cost consequence:** since cache_creation is billed 1.25× vs cache_read 0.1× (12.5×), the fraction shift is the mechanism behind HYBRID1's −67% effective-cost (documented separately).

## Verdict
**CACHE_TAX_CAUSALITY: SUPPORTED** (provider-prompt-cache regime; SHAM-controlled, repeated-measures, non-overlapping CIs).
