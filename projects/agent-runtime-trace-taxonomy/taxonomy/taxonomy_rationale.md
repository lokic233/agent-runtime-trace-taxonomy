# Taxonomy Rationale (v0)

## Method
Grounded-theory open coding by **3 independent frontier models** (claude / codex / gemini)
over the same 60-trace blinded bootstrap sample (dev solvers A/B/C only; held-out 32B
excluded). Coders never saw each other's output, never saw real model names, never saw
outcomes. 25 raw pattern proposals → clustered by cross-coder support → curated into
6 Waste L1 / 19 Waste L2 and 6 Workload L1 / 21 Workload L2 attributes.

## Why these Waste L1 (6, ≤7)
We kept the prompt's six seed families because the open-coding evidence mapped cleanly onto
them, with ONE substantive change:
- **CONTEXT_MEMORY** retained but **memory-retrieval L2 dropped**: SWE-agent has no memory/
  vector subsystem, so MEMORY_OVER_RETRIEVAL / MEMORY_RECALL_MISS are structurally
  unobservable here. Context waste survives as REDUNDANT_FILE_REREAD + CONTEXT_BLOAT.
- **ENVIRONMENT_TOOLING** is strongly evidenced (3 of the 6 multi-coder patterns are env/
  tooling: helper-build, helper-failure-loop, dependency-drift) — confirming the prompt's
  insistence that env failures be a first-class category separated from reasoning waste.

## Strength of evidence per label (provenance)
- **UNANIMOUS (3/3):** BLIND_INFILE_NAVIGATION. The single most robust discovery.
- **STRONG (2/3):** REDUNDANT_FILE_REREAD, CONTEXT_BLOAT, PATCH_CHURN, PREMATURE_SCRATCH_REPRO,
  VERIFICATION_GAP, PREEMPTIVE_HELPER_TOOL_BUILD, HELPER_TOOL_FAILURE_LOOP, DEPENDENCY_SETUP_DRIFT.
- **SINGLE-coder but crisp + metric-backed:** FILENAME_SEARCH_THRASH, SEARCH_WITHOUT_NEW_EVIDENCE,
  EDIT_TOOL_MECHANICAL_FAILURE, REDUNDANT_TEST, STAGNATION, FAILED_RECOVERY,
  BUDGET_EXHAUSTION_NONCONVERGENCE, ENVIRONMENT_BLOCKED.
- **PROVISIONAL (seed retained, weak observability):** OVER_BROAD_EDIT, TEST_AS_EXPLORATION_MISROUTING.
  Flagged to MERGE/DROP in the pilot.

## Anti-outcome-collapse discipline
All three coders independently rejected outcome-in-disguise labels (FAILED_TO_SOLVE,
BAD_REASONING, LOW_QUALITY_PATCH, NO_TESTS_MEANS_FAILURE, MANY_SEARCHES_MEANS_WASTE). Two
labels that flirt with outcome (VERIFICATION_GAP, BUDGET_EXHAUSTION_NONCONVERGENCE) carry an
explicit `outcome_collapse_mitigation` defining them by observable behavior independent of
the (hidden) resolve status.

## Deterministic-metric ≠ label
Every label lists `metric_signals` as EVIDENCE, never as the definition. E.g. STAGNATION cites
longest_no_new_evidence_streak but requires the *behavioral* streak, not a threshold alone;
REDUNDANT_TEST requires "no state-changing event between", not merely "test ran twice".

## Workload vs Waste separation (mandatory)
Workload is TASK-level and inferred from issue text + structure + cross-model shared evidence.
Waste is TRACE/MODEL-level. The same task can carry different waste under different solvers;
its workload class must not change because one solver thrashed. (Enforced at the per-task
aggregation layer via cross_model_stability.)

## Known limitations carried into the pilot
1. **Transcript text truncation:** open coders saw all events but abbreviated observation text
   (~140 chars/event). Event-level coverage was 100%, but fine-grained churn/recovery detail in
   long observations was compressed. Pilot packets will use larger per-event text budgets.
2. **No qwen-8B dev perspective** (not on disk) — weak open-weight behavior under-sampled.
3. **solver_A ungraded** (live opus-4.7) — 16/60 bootstrap traces had unknown outcome (no effect
   on blind coding; matters only for outcome-stratified balance).
4. **19 L2 > preferred 18:** pilot is expected to merge near-neighbors toward 12-18.
