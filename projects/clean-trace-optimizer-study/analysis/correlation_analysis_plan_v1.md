# correlation_analysis_plan_v1.md — PRE-REGISTERED (Lane D)

## Objective
Determine whether clean trace features explain cost (n_actions proxy) and outcome (resolved)
variation BEYOND simple confounders (solver, harness, repo, trajectory length). Establishes
predictive signal — NOT optimizer efficacy.

## Row unit
task_id x solver x baseline run (one row per trace). 3432 rows, 7 solvers, 500 tasks (466 shared by all).

## Cost proxy (honest limitation)
True token counts are NOT per-trace attributable (HAL ledger lacks instance tags; reference sets ship
no token field). `total_tokens_proxy = n_actions` (action-step count). All "token cost" claims are
ACTION-COUNT claims and labeled as such. n_events (= n_steps incl pure-thought) used as the
trajectory-length control.

## Primary features (frozen)
SEARCH_NO_NEW_EVIDENCE_RATE, REDUNDANT_REREAD_RATE (secondary), OVERSIZED_THEN_NARROW_READ_RATE,
NO_EVIDENCE_PATCH_CHURN_RATE (applied-edits only), EDIT_MECHANICAL_FAILURE_RATE,
POST_EDIT_TEST_GAP, STAGNATION_FRACTION, TOOL_ERROR_RATE, ENVIRONMENT_SETUP_RATE (harness covariate).

## RQ1 — Cost (n_actions proxy)
For each feature, standardized:
  log1p(n_actions) ~ z(feature) + C(solver) + C(source_harness) + C(repo)        [no length control; cost==length here is partly mechanical]
Because the cost proxy IS the action count, a feature built as a RATE over n_actions is partly
mechanically related to length. We therefore ALSO model the RAW COUNT outcome differently:
  - Primary cost target = log1p(n_actions).
  - For rate features, report the partial correlation controlling for nothing vs controlling for solver+harness+repo.
  - Where shared tasks exist (466): log1p(n_actions) ~ z(feature) + C(solver) + C(task)   [task FE]
  NOTE: a rate feature predicting its own denominator is a known circularity; we FLAG cost-RQ for
  rate features as descriptive and lean on RQ2 (resolution) as the cleaner outcome.

## RQ2 — Resolution (the clean outcome; feature does NOT use resolved)
GRADED development solvers only. Per spec, EXCLUDE ungraded — here all are graded, but we keep the
CORE development cohort = {A opus-4.7, B opus-4.5, C sonnet-3.5}. 32B-class (E,G,H) + F reported as
robustness/secondary, NOT in the primary resolution model (harness confound + fine-tuning outlier).
  logit(P(resolved)) ~ z(feature) + C(solver) + C(source_harness) + C(repo) + log1p(n_events)
Also a task-FE conditional-logit on the 466 shared tasks (within-task: does the higher-signal trace
on a task resolve less often?).

## RQ3 — Non-convergence
Define termination proxies from the trace tail: no SUBMIT in last 3 actions, or trace at/над the
step cap (n_actions >= solver-specific 95th pct), as "non-convergent". Logistic on features + controls.

## Outputs per feature x outcome
Spearman; standardized beta; bootstrap 95% CI (task-clustered, 1000 reps); n; missing count;
BH-adjusted p (across the primary feature set per outcome); effect direction; per-solver; per-harness.

## Allowed wording: associated with / predictive of / explains additional variation / contains information about.
## Forbidden: causes / fixes / removing the behavior improves performance.

## Required sensitivity analyses
raw vs rate; with/without length control; per-solver; per-harness; exclude env-blocked
(environment_setup_rate top decile); exclude token(action) outliers (>99th pct); task-clustered
bootstrap; feature-permutation negative control; random-synthetic-feature negative control;
trace-length-only baseline.

## Predictive ablation (the decisive test)
Split BY TASK (GroupKFold on task_id; all traces of a task in one fold).
  Model A: n_events only
  Model B: solver + harness + repo + n_events
  Model C: B + clean trace features
Cost: CV R^2, MAE, log-MAE on log1p(n_actions). Resolution: AUROC, AUPRC, log-loss, Brier.
PRIMARY CLAIM requires Model C > Model B out-of-sample (resolution AUROC and cost R^2).

## Verdict mapping
INCREMENTAL_SIGNAL if C beats B beyond CI on the held task folds; TRACE_LENGTH_ONLY if C ~ A/E-length;
NOT_SUPPORTED otherwise.
