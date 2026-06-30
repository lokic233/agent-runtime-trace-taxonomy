# Phase 1 — Causal Estimands

Formal definition of the quantities estimated in this study. Treatment = a context transformation applied vs C0_identity baseline.

## Outcomes (task level)

**Cost outcomes** (per task, summed over the trajectory's model calls):
- `eff_cost` = input + 0.1·cache_read + 1.25·cache_creation + 5·output  (provider-priced effective cost, Anthropic prompt-cache rates)
- `raw_prompt` = input + cache_read + cache_creation  (physical prompt tokens)
- `cache_read`, `cache_creation`, `output` tokens (decomposition)
- `model_calls` = api_calls
- (wall-clock latency / TTFT: not reliably captured in ledgers → OMITTED, flagged)

**Quality outcomes:**
- `success` = SWE-bench resolved (binary, per run)
- `regression` = C0 resolved ∧ ¬method resolved (paired, single-run → attribution caveats)
- `success_rate` = mean success over repeated runs (only the 10 interesting tasks, 5 reps)
- drift proxies: extra calls, file rereads, output growth

## Treatment effects

**ATE** (average over tasks):
- ATE_cost(m) = E[eff_cost(m) − eff_cost(C0)]
- ATE_success(m) = E[success(m) − success(C0)]

**CATE** (conditional on pre-treatment state x — the heterogeneity target):
- CATE_cost(m, x) = E[eff_cost(m) − eff_cost(C0) | X = x]
- CATE_success(m, x) = E[success(m) − success(C0) | X = x]
where X = Tier-1 pre-treatment trace features (TRACE_FEATURE_DICTIONARY.md).

**Two weightings reported separately** (they diverge materially):
- task-weighted: mean/median over tasks (equal weight) — what a "typical task" sees
- bill-weighted: Σcost(m) / Σcost(C0) − 1 — the actual aggregate bill (dominated by big tasks)

## Controller objective
Choose method per task to minimize expected cost subject to a quality-loss budget:
```
argmin_m  E[eff_cost(m) | x]   s.t.   E[quality_loss(m) | x] ≤ budget
```
with quality_loss measured as one-sided 95% upper bound on regression rate. Budgets: strict 0%, low 1%, medium 3%, high 5%.

## Identification strategy
- **Cost CATE:** paired (same task, C0 vs method, single run each) → removes task fixed effects; residual confound = run-to-run trajectory noise (quantified by A/A reps).
- **Mechanism (cache/intelligence tax):** SHAM no-op control + dose stratification → quasi-experimental isolation.
- **Success CATE:** repeated-measures (5 reps) on the 10 interesting tasks only → the rest are single-run (unresolved attribution).

## Power note
50 paired tasks (cost), 10 repeated tasks (success). Adequate for ATE + coarse binned CATE; **UNDERPOWERED** for high-dimensional/ML CATE estimators (causal forests etc. not used).
