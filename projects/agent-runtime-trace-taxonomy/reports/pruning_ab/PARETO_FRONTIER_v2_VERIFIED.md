> # ⚠️ SAVING NUMBERS CORRECTED IN v3 (TASK-LEVEL)
> The token-saving %% in this report are *mean prompt-token-per-call reductions*, computed from a
> CONTAMINATED, non-task-tagged ledger. Real PAIRED TASK-LEVEL accounting (PARETO_FRONTIER_v3_TASK_LEVEL.md)
> shows HYBRID1 saves ~−2.5%% (median), i.e. it does NOT reduce task-level cost. The resolution/regression
> counts here remain valid (they are graded); only the SAVING column is superseded.

# Safe Context-Pruning Pareto Frontier v2 — SWE-bench GRADED (VERIFIED)

**Model:** Claude opus-4.7, **standard mode (extended thinking NOT enabled)** · **Tasks:** 50 golden resolved cases (SWE-bench Verified, 10 repos)
**Method:** paired re-run through context-pruning shim → **real SWE-bench test-suite grading** (podman, network-isolated) · **Date:** 2026-06-29

## ⚠️ This supersedes v1. v1 was submission-proxy; THIS is graded.

The v1 table claimed "0 regressions / ∞ ratio / certified STRICT" for all methods. **That was wrong** — it counted *submissions*, not *resolutions*. Real SWE-bench grading reveals **every method regresses**. No method is STRICT. This is the honest, verified result.

## The verified table (C0 baseline = 48/50 resolved)

| rank | method | token saving % | resolved | **regressions** | improvements | saving/reg | loss_UB (95%) | tier |
|------|--------|------:|---:|---:|---:|:---:|------:|:---:|
| 1 | AGG3 recency-obs w=4 | **+50.6%** | 46 | 3 | 1 | 16.9 | 0.146 | MED |
| 2 | AGG2 recency-obs w=8 | +47.7% | 46 | 3 | 1 | 15.9 | 0.146 | MED |
| 3 | COMBO1 m7+cap5k | +42.5% | 47 | 2 | 1 | 21.2 | 0.118 | MED |
| 4 | **HYBRID1 graduated m7+agg2** | **+41.5%** | **48** | **1** | 1 | **41.5** | **0.088** | MED |
| 5 | AGG1 recency-obs w=12 | +39.9% | 46 | 3 | 1 | 13.3 | 0.146 | MED |
| 6 | SUM1 summarize-old | +38.2% | 46 | 3 | 1 | 12.7 | 0.146 | MED |
| 7 | PROG1 progressive | +37.9% | 47 | 2 | 1 | 19.0 | 0.118 | MED |
| 8 | M7 old-obs-elide | +37.0% | 44 | **5** | 1 | 7.4 | 0.199 | HIGH |
| 9 | COMP1 tool-compress | +22.6% | 46 | 3 | 1 | 7.5 | 0.146 | MED |
| 10 | DEDUP2 near-dup-obs | +19.0% | 46 | 3 | 1 | 6.3 | 0.146 | MED |
| 11 | M4 obs-cap-5k | +1.4% | 47 | 3 | 2 | 0.5 | 0.146 | MED |
| 12 | M6 env-log-collapse | +0.5% | 46 | 3 | 1 | 0.2 | 0.146 | MED |

**Sorted by saving/regression (cost-efficiency), HYBRID1 dominates:** 41.5% saving for ONE regression.

## The headline findings

### 1. There is no free lunch. No method is STRICT (0-regression) on opus-4.7.
Even **M6** (collapse successful build logs to 1 line, +0.5% saving — nearly a no-op) regresses **3 tasks**. Even **M4** (cap observations at 5k chars, +1.4%) regresses 3. Touching the context at all carries baseline risk on the fragile tasks. The "lossless pruning" hypothesis is **falsified** for this model/suite.

### 2. `pylint-4551` is a universal canary — regressed by ALL 12 methods.
```
FRAGILE TASKS (regressed by N of 12 methods):
  pylint-dev__pylint-4551    12/12   ← ANY context modification breaks it
  sympy__sympy-14248          6/12
  sphinx-doc__sphinx-8638     4/12
  sphinx-doc__sphinx-9658     4/12
  pylint-dev__pylint-6386     3/12
  astropy__astropy-14096      2/12
  sympy__sympy-19040          2/12
  sympy__sympy-13091          1/12
```
The regression risk is **concentrated in ~8 fragile tasks**, not diffuse. 42 of 50 tasks are stable under every method. A controller could **blocklist the canary signature** (likely tasks where early-trajectory observations are load-bearing for a late decision) and prune aggressively on the safe 84%.

### 3. Pruning sometimes HELPS. `pytest-6197` was fixed by ALL 12 methods.
C0 baseline FAILED pytest-6197; every pruning method RESOLVED it. Removing distracting/stale context let the agent find the fix. This is real evidence that context reduction is not purely lossy — it can improve focus. (`improvements` column.)

### 4. Graduated > flat-aggressive. HYBRID1 is the clear winner.
HYBRID1 (very-old→clear, medium→summarize, recent→keep) gets +41.5% saving at **1 regression** — nearly the saving of flat M7 (+37%, 5 reg) and AGG3 (+50.6%, 3 reg) but at a fraction of the cost. Mirroring human reading (recent detail, old gist) is the right inductive bias.

### 5. Bigger recency window ≠ safer. AGG1 (w=12) regresses as much as AGG3 (w=4).
AGG1 keeps 3× more recent observations than AGG3 yet regresses the same 3 tasks (different set). Conservatism in window size doesn't buy safety — *what* you clear matters more than *how much*.

## What loss_UB means + certification

`loss_UB` = one-sided 95% Wilson upper bound on P(method breaks a resolved task).
- **None certify at δ=6%** (would need loss_UB ≤ 0.06; best is HYBRID1 at 0.088).
- At n=48 with 1 regression, HYBRID1's true regression rate is ≤8.8% with 95% confidence.
- To certify HYBRID1 at δ=6% would require ~150-200 tasks (mini-SWE has insufficient power).

## Risk-tier controller menu (VERIFIED)

| user risk tolerance | recommended method | saving | loss_UB | note |
|---------------------|-------------------|------:|------:|------|
| **STRICT (0 regression)** | ⚠️ NONE qualifies on opus-4.7 | — | — | frontier model has no free pruning |
| **LOW (≤9% loss)** | **HYBRID1** | +41.5% | 0.088 | best cost-efficiency, 1 regression |
| **MEDIUM (≤12% loss)** | COMBO1 or PROG1 | +42.5% / +37.9% | 0.118 | 2 regressions |
| **MED-HIGH (≤15% loss)** | **AGG3** | +50.6% | 0.146 | max saving, 3 regressions |
| **HIGH (≤20% loss)** | M7 | +37.0% | 0.199 | worst — avoid (5 reg for less saving) |

**Recommendation: HYBRID1 for almost everyone.** It's the Pareto-dominant choice — only AGG3 saves more, at 3× the regression risk.

## Apparatus & honesty

- Real paired re-runs through opus-4.7 (PlugBoard mTLS), NOT shadow/counterfactual.
- Every regression measured by actual SWE-bench test-suite execution (podman, network-isolated, max_workers=4).
- **Thinking NOT enabled** — confirmed from the wire body (no `thinking` key; temperature unset; max_tokens=128000). Methods that reorder/clear turns (M7/AGG3) may behave differently with extended thinking, which has strict block-continuity constraints. **Scope: standard-mode opus-4.7 only.**
- C0 baseline re-run resolved 48/50 (one empty-patch, one genuinely unsolved). Regressions measured against this 48, not the original full-466 resolve set.
- 3 arms (COMP1/DEDUP2/M4) required re-grading after a podman daemon wedge (orphaned eval containers); re-graded clean, results consistent.

## Files
- `results/pruning_ab/final_verified_table.json` — machine-readable
- `reports/pruning_ab/PER_TASK_MATRIX.md` — **human-readable per-task pass/regress/improve matrix** (the task mapping)
- `results/pruning_ab/per_task_outcomes.json` — machine-readable per-method × per-task map + fragility ranking
- `results/pruning_ab/grade_*.json` — raw SWE-bench reports (13 arms)
- `src/pruning_ab/prune_methods.py` — all method implementations
