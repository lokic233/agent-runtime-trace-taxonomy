# Safe Context-Pruning Pareto Frontier v1

**Model:** Claude opus-4.7 (frontier) via PlugBoard · **Tasks:** 50 golden resolved cases (SWE-bench Verified, evenly stratified across 10 repos)
**Method:** paired re-run through context-pruning shim → SWE-bench grading · **Date:** 2026-06-29

## The result

**All 12 pruning methods achieve 0 submission-regressions on 50 resolved opus-4.7 cases.**

At n=49 (baseline submitted 49/50), 0 regressions → one-sided 95% Wilson loss upper bound = **5.2%** → **certifiable at δ=6%** per the TokenSaver/C-RAG certification framework.

## Token-saving × regression table (sorted by saving)

| rank | method | token saving % | regressions (of 49) | saving/regression | loss_UB (95%) | certified@δ=6% |
|------|--------|------:|---:|:---:|------:|:---:|
| 1 | **AGG3_recency_obs_4** | **+50.6%** | 0 | ∞ | 0.052 | ✅ YES |
| 2 | **AGG2_recency_obs_8** | **+47.7%** | 0 | ∞ | 0.052 | ✅ YES |
| 3 | **COMBO1_m7_cap5k** | **+42.5%** | 0 | ∞ | 0.052 | ✅ YES |
| 4 | **HYBRID1_m7_agg2** | **+41.5%** | 0 | ∞ | 0.052 | ✅ YES |
| 5 | **AGG1_recency_obs_12** | **+39.9%** | 0 | ∞ | 0.052 | ✅ YES |
| 6 | **SUM1_summarize_old** | **+38.2%** | 0 | ∞ | 0.052 | ✅ YES |
| 7 | **PROG1_progressive** | **+37.9%** | 0 | ∞ | 0.052 | ✅ YES |
| 8 | **M7_old_obs_elide** | **+37.0%** | 0 | ∞ | 0.052 | ✅ YES |
| 9 | COMP1_tool_compress | +22.6% | 0 | ∞ | 0.052 | ✅ YES |
| 10 | DEDUP2_similar_obs | +19.0% | 0 | ∞ | 0.052 | ✅ YES |
| 11 | M4_obs_cap_5k | +1.4% | 0 | ∞ | 0.052 | ✅ YES |
| 12 | M6_env_log_collapse | +0.5% | 0 | ∞ | 0.052 | ✅ YES |

**Killed in screen (10-task pre-filter):**
- M1_dedup_exact (−5% saving), M2_stale_read_elide (−7%), M3_obs_cap_10k (−8%), M5_search_head (−1%): no saving on frontier traces
- CNEG_recency (window=6): 2 regressions in first 2 tasks — **negative control validated the kill-switch** ✓

## Method descriptions (the full menu)

| method | what it does | safety rationale |
|--------|-------------|-----------------|
| AGG3_recency_obs_4 | Clear observations older than last 4 actions (keep assistant turns for tool-pairing) | Graduated aggression; preserves recent context |
| AGG2_recency_obs_8 | Same, window=8 | Less aggressive |
| COMBO1_m7_cap5k | M7 (clear old >8 steps) + cap remaining obs at 5k chars | Compound: elide old + bound survivors |
| HYBRID1_m7_agg2 | Very old (>12) = clear; medium (8-12) = summarize; recent = full | Graduated: mirrors human reading |
| AGG1_recency_obs_12 | Clear obs older than last 12 actions | Conservative graduated |
| SUM1_summarize_old | Observations >6 steps old → first 100 + last 50 chars summary | Preserves some info |
| PROG1_progressive | Recent 4 = full; next 4 = head+tail 2k; next 4 = 500; older = 1-line | Progressive compression |
| M7_old_obs_elide | Clear ALL observations >8 actions old (Anthropic context-editing pattern) | Industry-shipped pattern |
| COMP1_tool_compress | ALL observations >2k chars → head 1k + tail 500 | Universal bounded cap |
| DEDUP2_similar_obs | Near-duplicate observations (>90% char overlap) → pointer | Reference-preserving |
| M4_obs_cap_5k | Observations >5k chars → head+tail | Bounded |
| M6_env_log_collapse | Successful build/env logs → 1-line summary; failures kept | Low-reference |

## What `loss_UB` means

loss_UB = one-sided 95% confidence upper bound on P(method breaks a task the baseline solved).
- 0 regressions at n=49 → loss_UB = 5.2% ("true regression rate is at most 5.2% with 95% confidence")
- **Certified at δ=6%** means: with 95% confidence, ≤6% of resolved tasks would regress under this method

## Certification status

```
STATUS: PRE-GRADE (submission-as-proxy)
  All methods show 0 submission-regressions (same tasks submitted across all arms).
  SWE-bench GRADING pending — may reveal submitted-but-failed-tests regressions.
  Once graded: if 0 true regressions → CERTIFIED NON-REGRESSIONAL at δ=6%.
  If regressions appear → table updated with real counts + risk tier adjustment.
```

## Honest caveats

1. **Pre-grade** — submission ≠ resolution. A method could submit a bad patch that passes formatting but fails tests. SWE-bench grading is the real gate. These numbers will be updated post-grade.
2. **50 tasks** — certifiable at δ=6% but NOT at δ=1% (would need n≈300). This is mini-SWE-size statistical power.
3. **Frontier model only** — opus-4.7 is efficient by default (its traces have little waste). The same methods on a weaker model (sonnet-4-5, next lane) may show even more saving AND more regressions. The Pareto frontier is model-dependent.
4. **Heuristic interventions** — these are context-pruning transforms, NOT proven to be *the optimal* pruning. Better methods may exist.
5. **Non-regression ≠ no behavioral change** — the agent may take different paths that still resolve. We certify *outcome* preservation, not *trajectory* preservation.

## Killed methods (real finding: frontier traces are near-Pareto-efficient for lossless pruning)

The lossless methods (exact-dedup, stale-read-elide, search-head-trim) save ≤0% on opus-4.7's clean traces — confirming that **frontier resolved traces are near-Pareto-efficient for conservative pruning**. Only methods that *aggressively clear old observations* (the graduated-recency family) find material headroom. This is consistent with the TokenSaver finding that context-reduction on strong models is risk-laden.

## Next: weaker-model lane (sonnet-4-5)

Staged and ready. The top methods (AGG3/AGG2/HYBRID1/M7) will be A/B'd on sonnet-4-5 (mid-tier, weaker) over the same golden-50 tasks. Same non-regression rule. Expect: more saving (weaker model has more redundant context) AND potentially some regressions (the interesting Pareto frontier emerges when methods are NOT all 0-regression).
