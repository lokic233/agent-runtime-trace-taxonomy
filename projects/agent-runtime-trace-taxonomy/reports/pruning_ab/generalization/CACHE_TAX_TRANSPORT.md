# CACHE_TAX_TRANSPORT (Phase C) — SKELETON

**Estimand:** cache_creation_fraction = cache_creation/(cache_creation+cache_read), per (model,arm).
**Design:** Sonnet 4.6 + Haiku 4.5 × {C0, SHAM, HYBRID1} × 5 reps × 10 interesting tasks, counterbalanced.
**Contrast:** C0 ≈ SHAM ≪ HYBRID1 (prefix rewriting busts the cache). Anchor (Opus): 0.077/0.066/0.784.
**Populated from:** results/pruning_ab/generalization/cache_tax_transport.json (analyze_cache_tax.py).

Smoke preview (EXPLORATORY, 5 tasks, 1 rep): Sonnet C0 0.035 ≈ SHAM 0.039 ≪ HYBRID1 0.788 → mechanism + magnitude appear to transport.

## Results _[pending Phase C paid run]_
| model | C0 cc_frac | SHAM cc_frac | HYBRID1 cc_frac | C0≈SHAM≪HYB? | verdict |
|-------|-----------|--------------|------------------|--------------|---------|
| sonnet46 | | | | | |
| haiku45 | | | | | |

## Robustness _[paired + repo-cluster bootstrap per analyze]_
## Cross-provider note: gpt-5-5 has NO comparable cache-recreation estimand → CACHE_TAX_CROSS_PROVIDER = NOT_IDENTIFIABLE.
