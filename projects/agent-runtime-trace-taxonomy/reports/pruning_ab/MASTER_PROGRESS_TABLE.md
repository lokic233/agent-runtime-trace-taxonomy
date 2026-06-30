# Master Progress Table — All Pruning Methods Tested

Every method across all experiments, with the metric that matters for each phase. **Bottom line: on cached opus-4.7, no method yet achieves a clean positive task-level saving — but the search continues with retrieval-based methods (Experiment 4).**

## Legend
- **per-call saving** = mean prompt-token-per-call reduction (v2 metric — real but misleading on cached models)
- **task-level saving** = paired per-task tokens_sent saving (v3 metric)
- **eff-cost saving** = cache-aware effective cost: `input + 0.1·cache_read + 1.25·cache_creation + 5·output` (the TRUE metric)
- **cache cr:cc** = cache_read:cache_creation ratio (>1 good, <1 = cache busted). C0 baseline ≈ 10.7
- **call-ratio** = median agent calls vs C0 (1.0 = no trajectory drift; >1 = agent loops more)
- **regr** = real regressions (outside A/A noise floor); A/A floor loss_UB = 0.055

## EXPERIMENT 1+2 — Recency-based methods (v2 graded, SWE-bench)

| method | type | per-call saving | task-level (v3) | eff-cost | cache cr:cc | verdict |
|--------|------|------:|------:|------:|------:|--------|
| C0_identity | baseline | 0% | 0% | 0% | 10.7 | baseline |
| HYBRID1_m7_agg2 | recency | +41.5% | −2.5% | **−67%** | 0.37 | ❌ cache catastrophe |
| AGG3_recency_obs_4 | recency | +50.6% | −1.2% | ~−69% | 0.36 | ❌ cache busted |
| AGG2_recency_obs_8 | recency | +47.7% | — | neg | ~0.37 | ❌ |
| AGG1_recency_obs_12 | recency | +39.9% | — | neg | ~0.37 | ❌ |
| M7_old_obs_elide | recency | +37.0% | −4.3% | ~−41% | 0.37 | ❌ |
| SUM1_summarize_old | recency | +38.2% | — | neg | low | ❌ |
| PROG1_progressive | recency | +37.9% | — | neg | low | ❌ |
| COMBO1_m7_cap5k | recency+cap | +42.5% | — | neg | low | ❌ |

**Finding:** recency pruning re-writes the prefix every step → busts the prompt cache (cr:cc 10.7→0.37) → 91% expensive cache_creation → effective cost EXPLODES (−67%) despite "saving" tokens per-call.

## EXPERIMENT 3 — Cache-stable (content-based) methods (golden-50, effective cost)

| method | cut target | eff-cost saving (median) | cache cr:cc | call-ratio | regr | verdict |
|--------|-----------|------:|------:|------:|:---:|--------|
| GENTLE4K_stable | dumps >4k | −6.0% | 10.5 | 1.00 | 1 (noise) | safe, no saving |
| GENTLE6K_stable | dumps >6k | **+0.6%** | 9.4 | 1.04 | 2 | marginal (CI straddles 0) |
| SMARTGENTLE_stable | dumps >3k struct | −9.5% | 10.5 | 1.07 | 3 | no saving |
| CAP1K_stable | all obs >1k | −11.9% | 10.4 | 1.24 | — | drift starts |
| CAP800_stable | all obs >800 | −19.1% | 10.7 | 1.47 | — | drift |
| CAP500_stable | all obs >500 | −35.2% | 10.7 | 1.73 | — | heavy drift |
| SMART_stable | struct >0.6k | −55.9% | 12.5 | 2.33 | — | severe drift |
| COMBOSC_stable | combo | −75.5% | 13.1 | 2.26 | — | severe drift |

**Finding:** content-stable pruning PRESERVES the cache (cr:cc ~10, hypothesis confirmed) — fixing HYBRID1's catastrophe. But: aggressive caps cause trajectory drift (agent loops, call-ratio→2.3×); gentle caps avoid drift but prune too little to save. **Best = break-even (+0.6%, CI straddles zero).**

## The two barriers discovered
1. **Cache barrier** (recency methods): pruning busts the 0.1× prompt cache → cache_creation 1.25× explosion.
2. **Drift barrier** (aggressive content methods): char-truncation removes load-bearing info → agent re-fetches → +output cost dominates.

## Why a clean win is hard on cached frontier models
Effective cost = 34% cache_read (0.1×, already cheap) + 39% cache_creation (from APPENDING new turns) + 27% output (5×). The prompt is the cheapest component; pruning it can't save much, and any info loss triggers expensive re-work.

## EXPERIMENT 4 (NEXT) — Retrieval-based, drift-free methods (from literature)
Inspired by SWE-Pruner (arxiv 2601.16746, 39% SWE-bench reduction via line-level task-aware skimming) + Headroom/tokensave (retrievable compression — "if the LLM needs it, it can retrieve it"). The key: **don't DELETE info (causes drift) — replace verbose content with a compact, RETRIEVABLE reference**, AND keep it cache-stable (content-based). See EXPERIMENT4_PLAN below. Target: regression-allow, real per-task saving.
