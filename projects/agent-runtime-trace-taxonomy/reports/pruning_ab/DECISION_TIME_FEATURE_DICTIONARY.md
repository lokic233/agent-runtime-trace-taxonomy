# Decision-Time Feature Dictionary (corrected)

**Core correction:** The prior `TRACE_FEATURE_DICTIONARY.md` labeled features like `dup_line_ratio`, `largest_obs_chars`, `n_observations` as "Tier-1 deployable." This was **imprecise**. The *feature family* is online-computable, but the **stored value used in the prior analysis was computed over the COMPLETE C0 trajectory** — a full-trajectory realization that leaks the future. A deployable controller at call *t* sees only the prefix up to *t*.

> **Precise statement:** A feature family may be online-computable, while the existing stored value is a future-leaking full-trajectory realization.

## Timestamp taxonomy
- **TASK_START** — available before any model/tool execution (t=0).
- **PREFIX_STATE(t)** — computable from the trajectory prefix up to decision call *t* (the true deployable covariate).
- **FULL_TRAJECTORY** — computed from the complete C0 trajectory; retrospective characterization only; **NOT a deployable pre-treatment covariate**.
- **POST_TREATMENT** — affected by the selected action; invalid for selection; potentially valid for feedback/rollback.

## Corrected classification of the prior features

| feature | formula | source | earliest avail | class | stored value timestamp-aligned? | static routing | per-decision selection | post-action verification | leakage risk |
|---------|---------|--------|:--:|------|:--:|:--:|:--:|:--:|------|
| dup_line_ratio | dup lines / total lines | C0 obs | PREFIX_STATE(t) computable | **FULL_TRAJECTORY (as stored)** | ❌ stored = whole run | ❌ (leaks) | ✅ if recomputed on prefix | — | HIGH as stored |
| n_dup_lines | count dup lines | C0 obs | PREFIX_STATE(t) | FULL_TRAJECTORY (stored) | ❌ | ❌ | ✅ recomputed | — | HIGH stored |
| repeated_obs_ratio | repeated whole obs / obs | C0 obs | PREFIX_STATE(t) | FULL_TRAJECTORY (stored) | ❌ | ❌ | ✅ recomputed | — | HIGH stored |
| largest_obs_chars | max obs size | C0 obs | PREFIX_STATE(t) (max-so-far) | FULL_TRAJECTORY (stored) | ❌ stored=global max | ❌ | ✅ as max-so-far | — | MED stored |
| median/p90_obs_chars | obs size pctiles | C0 obs | PREFIX_STATE(t) | FULL_TRAJECTORY (stored) | ❌ | ❌ | ✅ recomputed | — | MED stored |
| n_observations | # observations | C0 traj | PREFIX_STATE(t) (count-so-far) | FULL_TRAJECTORY (stored) | ❌ stored=final count | ❌ leaks horizon | ✅ as count-so-far | — | HIGH stored |
| total_obs_chars | Σ obs chars | C0 traj | PREFIX_STATE(t) | FULL_TRAJECTORY (stored) | ❌ | ❌ | ✅ recomputed | — | HIGH stored |
| baseline_calls | C0 final api_calls | C0 model_stats | **END of run** | FULL_TRAJECTORY | ❌ | ❌ leaks horizon | ❌ never | — | CRITICAL |
| baseline_tokens_sent | C0 final tokens | C0 model_stats | END of run | FULL_TRAJECTORY | ❌ | ❌ leaks cost | ❌ | — | CRITICAL |
| task_stmt_chars | task statement len | t=0 | TASK_START | ✅ | ✅ | ✅ | ✅ | none |
| repo | repository | t=0 | TASK_START | ✅ | ✅ | ✅ | ✅ | grouping confound |

## What this means
- **Only `task_stmt_chars` and `repo` are genuinely TASK_START** (valid for static routing).
- **All redundancy/volume features are PREFIX_STATE-computable but were STORED as FULL_TRAJECTORY** → the prior HTE/controller analysis used leaky values for the redundancy features. *(This does not invalidate the prior NEGATIVE result — using leaky/oracle-ish features and still failing to route is a stronger negative. But it means the deployable-feature question was never cleanly tested.)*
- For the decision-event study (Parts 3-8), all features must be **recomputed as PREFIX_STATE(t)** from the prefix up to each call — never the global trajectory value.

## Implication for the prior verdict
The prior static-routing failure used features that were, if anything, **more informative than deployable** (full-trajectory). Failing with oracle-ish features → the *static task-level* architecture is robustly NOT_SUPPORTED. But the *decision-time* feature values (prefix-aligned) have **never been computed or tested** — that is this mission's job.
