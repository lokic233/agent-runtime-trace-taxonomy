# Phase 7 — Cross-Model Boundary (EXPLORATORY, mechanism-transfer + re-pricing)

**Status: EXPLORATORY.** No validated weaker-model SWE-agent run was executed (would require wiring SWE-agent → Qwen2.5-Coder-32B + re-grading, multi-hour). Qwen2.5-Coder-32B vLLM is available (port 8001) and noted for future work. What follows is a **mechanism-transfer argument + a re-pricing bound on existing opus trajectories** — clearly not a confirmatory cross-model result.

## Mechanism transfer
- **Cache tax (Phase 2) REQUIRES a provider prompt cache.** An uncached model (local Qwen, no prefix cache) has no cache to bust → HYBRID1-style prefix rewriting would NOT incur the 1.25× cache-creation tax. The cache-tax mechanism is **cache-regime-specific** and would not transfer to uncached serving.
- **Intelligence tax (Phase 2) is model-capability-dependent, not cache-dependent.** Removing unique/needed content forces re-derivation regardless of caching. Hypothesis (untested): a *weaker* model is less able to recover from lost context → intelligence tax should *increase* as capability decreases.

## Re-pricing bound (opus trajectories under uncached pricing)
Re-pricing existing token counts with uncached cost = prompt×1.0 + output×5 (no 0.1× cache discount):

| method | CACHED eff-cost saving (measured) | UNCACHED re-priced saving (bound) |
|--------|---:|---:|
| LINEDEDUP_e4 | +6.3% | +9.6% |
| GENTLE6K_stable | +10.1% | +17.4% |

**Saving increases uncached** — because without the 0.1× cache discount, the prompt is no longer "already cheap," so removing prompt tokens recovers more. This supports (does not prove) the hypothesis that **prompt pruning is more valuable in uncached/weaker-model regimes.**

## Hard caveat
This re-prices opus-4.7 trajectories — a genuinely weaker model would produce **different (likely longer, more redundant)** trajectories with **higher intelligence tax**, so the two effects (more prompt-saving value, more drift risk) could partially cancel. The sign and magnitude on a real weaker model are **UNIDENTIFIED** without the actual runs.

## Verdict
**CROSS_MODEL_STATUS: UNDERPOWERED / EXPLORATORY.** Mechanism analysis predicts cache-tax vanishes uncached and prompt-saving value rises, but no validated weaker-model run was performed. The directional hypothesis (pruning helps more on weaker/uncached models) is plausible and re-pricing-supported but not confirmed.
