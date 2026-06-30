# Pareto Frontier v3 — TASK-LEVEL accounting (the corrected cost metric)

**This corrects v2's *interpretation*, not its measurement.** v2 reported a per-call number and called it "token saving." That per-call reduction is **REAL** — but it is NOT task-level cost saving. This report separates the two and shows where the win does and does not hold.

## ✅ The one real win: per-call prompt reduction (+42.8%) — VERIFIED CLEAN

Recomputed from clean, task-tagged ledgers (5 C0 reps + 5 HYBRID1 reps, same 10 tasks):

| metric | C0 | HYBRID1 | reduction |
|--------|---:|--------:|:---:|
| mean true-prompt / call | 27,639 | 15,821 | **+42.8%** |
| median true-prompt / call | 25,041 | 15,351 | **+38.7%** |
| content removed when pruning fires | — | — | ~60% |
| fraction of calls pruning fires on | — | — | ~77% |

**HYBRID1 genuinely shrinks the per-call prompt by ~40%.** The original "+41.5%" was real as a per-call metric — the ledger contamination only nudged it (clean recompute: 42.8% mean). The method does exactly what it claims at the call level. *(results/pruning_ab/percall_reduction_verified.json)*

## ❌ The win does NOT propagate to task-level cost

Per-task totals from SWE-agent model_stats (paired, golden-50):

| method | per-call claim | **paired median Δsent** | **paired median Δcost** |
|--------|---:|---:|---:|
| HYBRID1_m7_agg2 | **+42.8% (real)** | **−2.5%** | **−2.2%** |
| AGG3_recency_obs_4 | +50.6% | −1.2% | −48.8% |
| M7_old_obs_elide | +37.0% | −4.3% | −41.0% |

And on **167 held-out tasks**: median tokens_sent saving **−0.8%**, median cost **−52%**.

## Why a +42.8% per-call win becomes ~0% at task level (the mechanism)

Two effects cancel the per-call reduction:

### 1. Cache-busting tax (the dominant effect)
opus-4.7 via PlugBoard uses Anthropic **prompt caching**. C0 sends a stable growing prefix → cache_read:cache_creation = **11.8:1** (cheap reuse). HYBRID1 **rewrites the prefix every step** (clearing old observations changes the cached span) → **0.37:1** — the cache is constantly invalidated. So HYBRID1's calls send fewer tokens, but a much larger share are billed at the **expensive cache_creation rate (1.25×)** instead of the **cheap cache_read rate (0.1×)**.

```diagram
C0:  fewer-but-cached tokens   →  cache_read 0.1×   →  cheap
HYBRID1:  fewer-but-RECREATED  →  cache_creation 1.25×  →  ~12× more $/token
         net: prompt 40% smaller, but cost flat-to-worse
```

### 2. Trajectory drift
Pruned context sometimes makes the agent take **more steps** (re-reading files it "forgot"), adding calls that claw back the per-call saving.

## The honest framing

This is **not** an all-negative result. It is a **boundary result**:
- **What works:** client-side pruning *does* reduce per-call prompt size by ~40% (verified, reproducible).
- **What doesn't:** on a *cached* frontier pipeline, that reduction is **arbitraged away by the provider's prompt cache** — the cheap-cache regime C0 enjoys is exactly what pruning destroys. Net task-level cost is neutral-to-negative.
- **The implication:** the per-call metric is the wrong KPI for cached agents. The win is real but lives in a dimension (raw prompt size) that doesn't bill linearly.

## Where the win WOULD matter (untested, the honest follow-up)
On an **uncached or weaker model** — no prompt cache to bust, and genuinely redundant context — the +40% per-call reduction could translate to real task-level saving. That regime is the natural next experiment and is NOT falsified by this study (which is scoped to cached opus-4.7).

## Frontier verdict
- HYBRID1 has a **real +42.8% per-call prompt reduction** (the one win) but is **NOT a task-level cost-saving frontier point** on cached opus-4.7 (median −2.5% sent, cost neutral-to-negative).
- Hard-kill rules #1/#2 apply to the *task-level cost* claim, not to the per-call reduction (which stands).
