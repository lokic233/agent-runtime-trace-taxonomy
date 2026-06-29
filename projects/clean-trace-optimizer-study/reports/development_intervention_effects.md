# Development Intervention Effects — STATUS: PENDING (paired_outcomes_status: PENDING)

No paired runtime-intervention outcomes were generated in this window. Producing them requires
re-running SWE-agent across the 80-task development pool × {DEFAULT, SEARCH_CONSTRAINED, PATCH_GUARD,
VERIFY_HEAVY} against a live model endpoint — the dominant compute cost, deliberately deferred per the
study's §29 rule ("do not fabricate optimizer efficacy").

PRE-REGISTERED (analysis/intervention_analysis_plan_v1.md):
- H1 SEARCH_CONSTRAINED × SEARCH_NO_NEW_EVIDENCE_RATE
- H2 PATCH_GUARD × NO_EVIDENCE_PATCH_CHURN_RATE (applied-edits, evidence-gated, mechanical-failure-excluded)
- H3 VERIFY_HEAVY × POST_EDIT_TEST_GAP
Treatment effect reported by signal QUARTILE; token-saving / regression / improvement / solve-rate-
preservation / step-reduction / wall-time analyzed SEPARATELY (never one combined utility).
Actionable ONLY if the matched intervention benefits HIGH-signal tasks more than LOW-signal tasks.

Registered task pool: manifests/development_intervention_tasks.jsonl (80 tasks, configs listed, status PENDING).
Outcome table schema + writer: src/build_config_outcome_table.py (writes EMPIRICAL rows only).
No reports/treatment_effect_heterogeneity.csv is emitted because there are no paired outcomes to summarize.

INTERVENTION_HETEROGENEITY_VERDICT: NOT_SUPPORTED (untested — not a negative result, an unrun experiment).
