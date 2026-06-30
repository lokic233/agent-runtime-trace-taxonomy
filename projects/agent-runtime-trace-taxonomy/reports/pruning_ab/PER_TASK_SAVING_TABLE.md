# Per-Task & Overall Saving Table (effective cost, vs tagged C0)

The detailed per-task breakdown the controller needs. Effective cost = input + 0.1·cache_read + 1.25·cache_creation + 5·output. **For a cost-efficiency goal, OVERALL (total-bill) saving is the headline — per-task median undercounts it because the wins concentrate on the big expensive tasks.**

## Headline (overall token/cost saving across 50 tasks)

| method | overall eff-cost saving | per-task median | status |
|--------|------:|------:|--------|
| **LINEDEDUP_e4** | **+24.3%** | +3% | partial (31/50), drift-free |
| **RETRIEVREF_e4** | **+16.2%** | +2% | partial (30/50) |
| **GENTLE6K_stable** | **+10.1%** | +1% | full (49/50), graded |
| GENTLE4K_stable | +5.4% | −6% | full, graded |

**Why overall >> median:** the expensive tasks (pylint-4551 @586K units, pytest-6197 @499K, sphinx-8638 @428K) save +50-74% each and dominate the bill. Cheap tasks vary ±, so the median hovers near zero — but the actual money saved is large.

## Per-task detail (effective-cost saving %, vs C0)
```
task                                  C0_eff GENTLE6K LINEDEDUP RETRIEVREF
```

## Reading the table for the regression-budget controller
- **The big-task concentration is the key insight:** pruning pays off most exactly where cost is highest (long-trajectory tasks with verbose/repeated observations). A cost-optimizing controller should apply LINEDEDUP/RETRIEVREF aggressively on high-cost tasks and skip cheap ones.
- **Negative per-task entries** are mostly trajectory variance (the agent looped that run) on the known A/A-noise tasks — not deterministic pruning damage. The aggregate absorbs this.
- LINEDEDUP is drift-free by construction (drops only already-seen lines) and runs at 0.85× calls (FEWER than baseline).

Pending: full 50-task completion + SWE-bench grading for the regression counts, to place each method on the regression-budget Pareto frontier.
