# Comprehensive Master Table — Every Pruning Method, Every Metric

**Model:** cached frontier opus-4.7 · **Tasks:** golden-50 SWE-bench Verified · **Baseline C0:** 46/50 resolved, cache cr:cc=10.7, per-call true-prompt=17,702 tokens · **All SWE-bench graded, cache-aware.**

## Metric definitions
- **per-call save%** = mean prompt-token-per-call reduction (the v2 metric — what pruning removes per request; *misleading on cached models*)
- **cache cr:cc** = cache_read : cache_creation ratio. Baseline=10.7. **<1 = cache busted** (expensive). Higher = cache preserved.
- **raw save%** = overall raw-prompt tokens saved across all tasks (input+cache_read+cache_creation)
- **eff save%** = overall **effective cost** saved = input + 0.1·cache_read + 1.25·cache_creation + 5·output (Anthropic pricing units) — **the TRUE cost metric**
- **median%** = per-task median effective-cost saving (equal-weights tasks; ~0 even when aggregate saves, because big tasks dominate the bill)
- **call-ratio** = median agent calls vs C0 (1.0 = no trajectory drift; >1 = agent loops more)
- **reg / real** = regressions / real regressions excluding A/A-noise-floor flippers
- **loss_UB** = Wilson 95% 1-sided upper bound on regression rate (A/A noise floor = 0.055; budget bar ≈ 0.11)

## THE TABLE

| method | exp | type | per-call save | cache cr:cc | raw save | **eff cost save** | median | call-ratio | resolved | reg | real reg | loss_UB | verdict |
|--------|----|------|----:|----:|----:|----:|----:|----:|:--:|:--:|:--:|----:|---|
| **C0_identity** | — | baseline | 0% | **10.7** | 0% | **0%** | 0% | 1.00 | 46/50 | 0 | 0 | — | baseline |
| HYBRID1_m7_agg2 | 1 | recency | +41% | **0.37** | — | **−67%** | −2% | — | 48* | 1* | — | — | ❌ cache-bust catastrophe |
| AGG3_recency_obs_4 | 1 | recency | +51% | **0.36** | — | **~−69%** | −1% | — | 46* | 3* | — | — | ❌ cache-bust |
| M7_old_obs_elide | 1 | recency | +37% | **0.37** | — | **~−41%** | −4% | — | 44* | 5* | — | — | ❌ cache-bust |
| CAP500_stable | 3 | truncate | +29% | 10.7 | −16% | **−17%** | −35% | 1.73 | — | — | — | — | ❌ drift |
| SMART_stable | 3 | truncate | +27% | 12.5 | −43% | **−35%** | −56% | 2.33 | — | — | — | — | ❌ drift |
| COMBOSC_stable | 3 | truncate | +25% | 13.1 | −50% | **−39%** | −75% | 2.26 | — | — | — | — | ❌ drift |
| CAP1K_stable | 3 | truncate | +19% | 10.4 | +1% | **−3%** | −12% | 1.24 | — | — | — | — | ❌ mild drift |
| SIGNAL_e4 | 4 | line-skim | −1% | 13.5 | −37% | **−23%** | −28% | 1.26 | 45/50 | 2 | 0 | 0.123 | ❌ drift |
| COMBOSS_e4 | 4 | line-skim | +6% | 13.0 | −28% | **−18%** | −17% | 1.28 | 45/50 | 1 | 1 | 0.094 | ❌ costs more |
| WINCOMBO_e4 | 4 | dedup+ref | +8% | 8.9 | −5% | **−10%** | −17% | 1.00 | 44/50 | 3 | 3 | 0.152 | ❌ |
| RETRIEVREF_e4 | 4 | retrieval-ref | +2% | 9.7 | −0.4% | **−5%** | −7% | 1.00 | 45/50 | 1 | 0 | 0.092 | ⚪ safe, ~0 saving |
| SMARTGENTLE_stable | 3 | gentle | +10% | 10.5 | −1% | **−2%** | −9% | 1.07 | 45/50 | 3 | 0 | 0.152 | ⚪ neutral |
| GENTLE4K_stable | 3 | gentle-cap | +6% | 10.5 | +7% | **+5%** | −6% | 1.00 | 46/50 | 1 | 0 | 0.092 | ✅ safe, modest |
| **GENTLE6K_stable** | 3 | gentle-cap | +14% | 9.4 | +18% | **+10%** | +1% | 1.04 | 45/50 | 1 | 0 | 0.094 | ✅ saves (variance-infl) |
| **LINEDEDUP_e4** | 4 | line-dedup | +13% | 9.9 | **+10%** | **+6%** | −1% | **1.00** | 44/50 | 2 | **0** | 0.123 | ⭐ **best: real saving, 0 real reg, drift-free** |

\* exp-1 recency methods: resolution/regression from the v2 SWE-bench grading; their ledgers are pooled (per-task cost from v3 model_stats). eff-cost computed from cache-composition.

## How to read it — the 4 regimes

```diagram
                 cache cr:cc    eff-cost      what happens
RECENCY  HYBRID1    0.37        −67%    rewrites prefix → cache BUSTS → 1.25x recreation
TRUNCATE CAP/SMART  ~11         −3..−39%   cuts mid-content → agent LOOPS (drift, call 1.2-2.3x)
SAFE     RETRIEVREF ~10         ~0%     too gentle / refs add overhead → no saving
WIN      LINEDEDUP  9.9         +6%     removes only ALREADY-SEEN lines → no loss, no drift
```

## The three takeaways

1. **per-call save% LIES on cached models.** HYBRID1 shows +41% per-call but −67% true cost — because cutting tokens busts the cache (0.37 ratio), replacing cheap cache_read (0.1×) with expensive cache_creation (1.25×). **Always look at eff-cost save, not per-call.**

2. **The only positive eff-cost savers** are content-stable + redundancy/outlier-only: **LINEDEDUP (+6%), GENTLE6K (+10%), GENTLE4K (+5%)** — all keep cache cr:cc ≈ 10 (preserved) and call-ratio ≈ 1.0 (no drift).

3. **LINEDEDUP is the winner:** +6.3% true cost / +9.9% raw-prompt saving, drift-free (1.0× calls), cache-stable (9.9), **0 real regressions** (its 2 flips are baseline noise). The honest ceiling for safe pruning on a cached frontier agent is **~6-10%** — because the prompt is already 0.1× cheap, so there isn't more to win.

## Files
- `results/pruning_ab/COMPREHENSIVE.json` — machine-readable, all metrics
- per-experiment detail: PARETO_FRONTIER_v2/v3, CACHE_STABLE_FRONTIER, EXPERIMENT4_FRONTIER, REGRESSION_BUDGET_FINAL
