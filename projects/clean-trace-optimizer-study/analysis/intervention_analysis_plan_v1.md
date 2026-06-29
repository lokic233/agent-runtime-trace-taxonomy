# intervention_analysis_plan_v1.md — PRE-REGISTERED (Lane D + E)

## Status: SPECS ONLY this window. PAIRED_OUTCOMES_PENDING.
Paired runtime interventions require RE-RUNNING SWE-agent (x60-100 tasks x 4 configs x >=1 solver)
against a live model endpoint — infeasible in the autonomous window. We pre-register the analysis so
the experiment is registered (the only door to compute) and NO efficacy is fabricated.

## Core question (actionable correlation)
Not "does waste correlate with cost" but "does a trace signal predict the INCREMENTAL benefit of the
MATCHING intervention?"

## Configs (see config/runtime_config_registry_v1.yaml)
DEFAULT, SEARCH_CONSTRAINED, PATCH_GUARD, VERIFY_HEAVY.

## Primary interactions (frozen hypotheses)
H1: SEARCH_CONSTRAINED x SEARCH_NO_NEW_EVIDENCE_RATE  -> token saving rises with baseline signal,
    regression flat.
H2: PATCH_GUARD x NO_EVIDENCE_PATCH_CHURN_RATE (applied-edits)  -> ditto.
H3: VERIFY_HEAVY x POST_EDIT_TEST_GAP  -> resolution preservation/improvement rises with gap.

## Model
outcome ~ CONFIG + baseline_signal + CONFIG:baseline_signal + C(task) + C(solver)
Report effects by signal QUARTILE (low/med-low/med-high/high). Signal is ACTIONABLE only if the
matched intervention benefits HIGH-signal tasks more than LOW-signal tasks.

## Outcomes analyzed SEPARATELY (never combined into one utility)
token(action) saving; paired regression (baseline_resolved AND NOT candidate_resolved);
improvement (NOT baseline_resolved AND candidate_resolved); solve-rate preservation; step reduction; wall time.

## Mismatched-intervention negative control
PATCH_GUARD applied to high-search/low-churn traces must NOT show the matched benefit.

## Paired-row schema: data/development_config_outcomes.jsonl (provenance EMPIRICAL only when真run).
