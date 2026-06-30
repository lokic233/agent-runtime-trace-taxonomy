# Decision-Level Causal Estimands

## The corrected causal unit
Prior unit: `task × whole-task method`. Corrected unit: **`decision event × candidate segment × action`**.

A decision event:
```
e = { task_id, call_id, observation_id, timestamp, trajectory_prefix, candidate_segment, state_before_action }
```
Candidate actions (frozen methods only): `NO_OP`, `LINEDEDUP_CURRENT_SEGMENT`, `GENTLE_CAP_CURRENT_SEGMENT`, `EXTERNALIZE_CURRENT_SEGMENT`.

## Local outcomes over fixed horizons
H ∈ {next 1 call, next 3 calls, until next successful test, remainder of task}.
Outcomes: incremental eff-cost, cache_read, cache_creation, output tokens, extra calls, reread-of-removed-content, repeated-command rate, repeated-file-open rate, test-state Δ, progress velocity, rollback-required, eventual resolution.

## Estimands
- **Task-level ATE** (already estimated): E[cost(method)−cost(C0)] over tasks.
- **Event-level ATE**: E[Y(e, action) − Y(e, NO_OP)] over decision events.
- **Event-level CATE**: E[Y(e, action) − Y(e, NO_OP) | state_before_action] — the heterogeneity target for a per-decision controller.
- **Immediate harm signal**: E[reread ∨ repeated-command ∨ output-spike within H=1..3 | action] — feeds rollback.
- **Eventual quality effect**: E[resolution(action) − resolution(NO_OP)] — the budget constraint.

## Identification status (from Part 4 audit, decision_event_manifest.jsonl)
- 3,476 decision events reconstructed from observational runs (LINEDEDUP 1203, GENTLE6K 1087, RETRIEVREF 1186); 1613 fired.
- **PAIRED_TASK_ONLY: 1863** (task-level C0 exists, not event-level).
- **COUNTERFACTUAL_UNIDENTIFIED: 1613** (post-divergence calls — no matched C0 state).
- **Event-level ATE/CATE are NOT identifiable from current runs.** Once a method fires at call k, the trajectory diverges from C0 → no counterfactual "same prefix, no-pruning" state at k+1. Even the 277 pre-first-fire matched calls don't give a clean event counterfactual (the fire itself is the treatment; agent nondeterminism breaks exact prefix matching).

## Consequence
**Event-level causal effects require a micro-randomized trial** (Part 6): randomly assign FIRE vs NO_OP at the *same* eligible prefix, creating matched event-level counterfactuals with known propensity. Observational data can only characterize *associations* (e.g., what follows a fire), not the causal local effect.
