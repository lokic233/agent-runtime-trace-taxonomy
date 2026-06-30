# Trace Feature Dictionary — Lineage & Deployability

Every feature in `pre_treatment_features.jsonl`, with honest leakage classification. **Critical distinction:** features computed from the *complete* C0 trajectory are valid for **offline heterogeneity analysis** (predicting the per-task treatment effect), but a subset are **not available mid-trajectory** to a deployable per-decision controller. We label both.

## Feature lineage table

| feature | definition | timestamp | offline-CATE valid | deployable (per-decision) | leakage risk | role |
|---------|-----------|-----------|:--:|:--:|--------|------|
| n_observations | # tool observations in C0 traj | full C0 traj | ✅ | ⚠️ only counts-so-far at decision | full-trajectory count leaks horizon | volume/horizon proxy |
| total_obs_chars | sum of observation chars | full C0 traj | ✅ | ⚠️ partial-so-far | same | volume |
| largest_obs_chars | biggest single observation | full C0 traj | ✅ | ✅ (max-so-far is monotone) | low | outlier-dump signal |
| median_obs_chars | median observation size | full C0 traj | ✅ | ✅ | low | volume |
| p90_obs_chars | 90th pct observation size | full C0 traj | ✅ | ✅ | low | tail-dump signal |
| **dup_line_ratio** | exact-duplicate lines / total lines | full C0 traj | ✅ | ✅ (computable on seen content) | **low — this is the key redundancy signal** | redundancy (LINEDEDUP mechanism) |
| n_dup_lines | count of duplicate lines | full C0 traj | ✅ | ✅ | low | redundancy (absolute) |
| repeated_obs_ratio | repeated whole-observation fraction | full C0 traj | ✅ | ✅ | low | redundancy |
| baseline_calls | C0 final api_calls | **END of C0 traj** | ✅ | ❌ **LEAKS horizon** | **HIGH for deployment** | task-length proxy (offline only) |
| baseline_tokens_sent | C0 final tokens_sent | **END of C0 traj** | ✅ | ❌ **LEAKS final cost** | **HIGH for deployment** | cost proxy (offline only) |
| task_stmt_chars | task statement length | t=0 (pre-everything) | ✅ | ✅ | none | task characteristic |
| repo | repository name | t=0 | ✅ | ✅ (if metadata allowed) | grouping confound | stratification/clustering |

## Deployability tiers
- **Tier-1 (truly pre-decision, deployable):** dup_line_ratio, n_dup_lines, repeated_obs_ratio, largest_obs_chars, median_obs_chars, p90_obs_chars, task_stmt_chars, repo. These are computable from content already observed at any decision point.
- **Tier-2 (offline-CATE only, NOT deployable):** baseline_calls, baseline_tokens_sent — they encode the *full* C0 trajectory length/cost, unknown mid-run. Used to *characterize* heterogeneity, but a deployable controller may NOT use them. Any controller claim must use Tier-1 only.

## Why this matters for the mission
The forbidden-leakage list includes "future calls," "post-intervention call count," "complete-trajectory features unavailable at decision time." `baseline_calls`/`baseline_tokens_sent` are exactly that for a *per-decision* controller. We therefore:
1. Use all features for **offline CATE characterization** (Phase 4).
2. Restrict the **deployable controller** (Phase 5) to **Tier-1** features only.
3. Report both, and never let a Tier-2 feature enter the frozen policy.

## Known proxy confounds
- `dup_line_ratio` may proxy task length / repo (e.g. pytest tasks dump repeated tracebacks). Phase 4 controls for repo (leave-one-repo-out) and baseline cost.
- `largest_obs_chars` correlates with repo (sphinx/sympy produce big dumps). Repo-stratified analysis required.
- All single-run features inherit C0 run-to-run noise; the A/A reps quantify that noise floor.
