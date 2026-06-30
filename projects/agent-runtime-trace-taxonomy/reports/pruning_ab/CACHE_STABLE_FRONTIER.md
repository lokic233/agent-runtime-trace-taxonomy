# Cache-Stable Pruning Frontier — the search for a TRUE task-level win

**Question:** Can a *cache-stable* pruning method achieve real task-level cost saving on cached opus-4.7, where the recency-based HYBRID1 catastrophically failed (3.4× cost)?

**Answer: NEARLY — but not decisively.** The cache-stable hypothesis was mechanically correct, and it took the methods from −67% (HYBRID1) to **break-even (+0.6% best median)**. But on a cached frontier agent, prompt pruning cannot save meaningfully because the prompt is already ~10× cheap.

## The hypothesis (from cache arithmetic)
HYBRID1 fails because it's RECENCY-based: it re-prunes by position every step → rewrites the prompt prefix → busts Anthropic's prompt cache (cache_read:cache_creation collapses 11.8:1 → 0.37:1, 91% expensive cache_creation). **CONTENT-STABLE** pruning transforms each observation based only on its own content → byte-identical across steps → prefix stable → cache preserved.

## Both halves of the hypothesis CONFIRMED

**1. Cache preservation (cr:cc ratio, all 50 tasks):**
| method | cr:cc | vs HYBRID1 (0.37) |
|--------|------:|---|
| C0 baseline | 10.66 | — |
| GENTLE4K_stable | 10.53 | ✅ preserved |
| GENTLE6K_stable | 9.43 | ✅ preserved |
| SMARTGENTLE_stable | 10.42 | ✅ preserved |
| SMART_stable | 12.71 | ✅ preserved |

Every content-stable method keeps the cache read-heavy (~10), vs HYBRID1's catastrophic 0.37. **The mechanism works exactly as predicted.**

**2. Trajectory drift (call-ratio vs C0):**
| method | call-ratio | drift? |
|--------|-----------:|---|
| GENTLE4K | 1.00 | ✅ none |
| GENTLE6K | 1.04 | ✅ none |
| SMARTGENTLE | 1.07 | ✅ none |
| CAP1K | 1.24 | mild |
| CAP500 | 1.73 | heavy |
| SMART | 2.33 | severe |

The KEY discovery: **aggressive caps cause trajectory drift** — truncating normal observations removes info the agent needs, so it loops (re-reads files, +73-133% calls). GENTLE methods (cap only >4k/6k dumps, ~3-7% token cut) avoid this entirely (≤1.07× calls).

## The decisive frontier: cache-aware EFFECTIVE COST

EFFECTIVE COST = input + 0.1·cache_read + 1.25·cache_creation + 5·output (Anthropic pricing units), paired per-task vs tagged C0 (n=50). Real-regression = regression OUTSIDE the A/A noise floor (Phase 3 proved C0 itself flips 5/10 boundary tasks).

| method | median eff-cost save | mean | resolved | real regressions | verdict |
|--------|------:|------:|---:|:---:|---|
| **GENTLE6K_stable** | **+0.6%** | −6.3% | 45/50 | **1** | marginal break-even, 1 real reg |
| GENTLE4K_stable | −6.0% | −10.3% | 46/50 | **0** | no saving, but zero real reg |
| SMARTGENTLE_stable | −9.5% | −11.6% | 45/50 | 0 | no saving |
| CAP1K_stable | −11.9% | −20.0% | — | — | drift starts |
| SMART_stable | −55.9% | −90.5% | — | — | drift dominates |
| *(HYBRID1, for reference)* | *−67%* | — | — | — | cache-bust catastrophe |


## Same-batch regression cross-check (tagged C0, n=50)

The cleanest comparison — each method vs the tagged C0 from the SAME batch (resolved 46/50):

| method | resolved | net resolution | regressions | loss_UB | median eff-cost |
|--------|---:|:---:|:---:|---:|---:|
| GENTLE4K_stable | 46/50 | **0** | 1 (sympy-19040, a noise-flipper) | 0.092 | −6.0% |
| GENTLE6K_stable | 45/50 | −1 | 2 | 0.123 | +0.6% |
| SMARTGENTLE_stable | 45/50 | −1 | 3 | 0.152 | −9.5% |

**The decisive tension:** GENTLE4K is resolution-noninferior (net 0, regressions within noise) but saves nothing (−6%). GENTLE6K saves a marginal +0.6% (CI straddles zero) but is net −1 resolution with loss_UB 0.123 (just above the 0.11 bar). **No method achieves BOTH statistically-positive saving AND clean-within-noise regressions.** The win criterion is not met.

## Verdict: BOUNDARY RESULT — break-even, not a clean win

- **No method achieves a clean, meaningful task-level saving.** The best (GENTLE6K) is **+0.6% median** — statistically break-even — and carries 1 real regression. The zero-real-regression method (GENTLE4K) costs −6%.
- This is a **massive improvement over HYBRID1** (−67% → +0.6%): the cache-stable + no-drift design eliminated the catastrophe. But it lands at the economic floor, not above it.


## Statistical rigor: is +0.6% a real win?

GENTLE6K's median effective-cost saving = **+0.6%**, but the **95% bootstrap CI is [−8.2%, +9.5%]** — it **straddles zero**. The saving is statistically **indistinguishable from break-even**. Regressions pass (loss_UB 0.088, within 2× the A/A floor of 0.055), but the cost benefit is not significantly positive.

**Honest call: this meets the win-criterion's letter (+0.6% > 0, regressions within noise) but NOT its spirit.** A saving whose CI includes zero is break-even, not a win. We do not overclaim it.

## WHY prompt pruning can't win on a cached agent (the deep finding)

C0's effective-cost composition: **34% cache_read + 39% cache_creation + 27% output.**
- The prompt is read from cache at **0.1×** — it's already ~10× cheap. Cutting it saves almost nothing in effective terms.
- **cache_creation (39%)** comes from the agent *appending* new turns each step (the cache frontier advances). Pruning OLD observations doesn't reduce the NEW content being cached.
- **output (27%) at 5×** is the expensive part, and pruning the input prompt doesn't touch it.

**On a cached frontier agent, the prompt is not where the cost is.** You cannot save task-level cost by shrinking the cheapest component. The only real levers are: cut OUTPUT, or cut STEPS (finish faster) — not prune the (cached) prompt.


## Does the uncached regime save? (simulation from same trajectories)

Simulating uncached pricing (all prompt tokens at 1.0×, no 0.1× cache discount) on the SAME trajectories:

| method | cached median | uncached-sim median |
|--------|------:|------:|
| GENTLE6K | +0.6% | −2.7% |
| GENTLE4K | −6.0% | −1.3% |
| SMARTGENTLE | −9.5% | −1.0% |

**Even uncached, pruning does not win on these trajectories** — because the trajectory-drift OUTPUT cost (occasional agent looping) outweighs the small prompt savings regardless of cache pricing.

**Important caveat:** this simulation reuses opus-4.7's (cached-model) trajectories. A *genuinely* uncached or weaker model would produce DIFFERENT, likely more redundant trajectories where pruning has more to cut and the agent may tolerate it differently. That regime is NOT captured here and remains the one honest untested avenue. But the simulation reveals a deeper barrier than the cache alone: **trajectory sensitivity** — a capable agent perturbed by pruning sometimes loops, and that output cost dominates.

## Honest conclusion
The cache-stable hypothesis was **correct and necessary** — it explains HYBRID1's failure and fixes it — but it is **not sufficient** for a task-level win on cached models. The win, if it exists, lives on **uncached/weaker models** (no 0.1× cache, so the ~40% per-call prompt reduction would translate) — the untested regime flagged in v3. On cached opus-4.7, client-side prompt pruning's ceiling is break-even.

## Files
- results/pruning_ab/stable/effective_cost_frontier.json — the per-method cost table
- results/pruning_ab/stable/cache_health_snapshot.json — cache ratios + call-overhead
- results/pruning_ab/stable/grade_*.json — graded outcomes
- results/pruning_ab/stable/gentle6k_outcome.json — noise-floor regression analysis
