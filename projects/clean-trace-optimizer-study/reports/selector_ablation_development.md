# Selector Ablation (development) — STATUS: PENDING paired outcomes

The 10 methods (DEFAULT, GLOBAL_BEST, RANDOM, STATIC_METADATA, TRACE_LENGTH_ONLY,
DETERMINISTIC_TRACE_SELECTOR, PROMPTED_LOCAL_8B, LORA_LOCAL_8B, RULES+LORA, ORACLE) and the
primary question (does a trace-conditioned selector beat GLOBAL_BEST under the same regression
ceiling?) CANNOT be answered without paired config outcomes — which require re-running SWE-agent
x tasks x configs against a live solver. That is the dominant compute cost and was out of scope for
this window. We therefore:
- pre-registered the evaluation (analysis/selector_evaluation_plan_v1.md),
- implemented the DETERMINISTIC selector over FROZEN prefix features (src/evaluate_trace_selectors.py),
- DRY-RAN it on 50 dev traces to prove the code path (data/selector_dryrun.json),
- emitted NO efficacy number (no fabricated token-saving / regression).

Selector pick distribution on the dry-run sample: {'DEFAULT': 7, 'SEARCH_CONSTRAINED': 40, 'VERIFY_HEAVY': 3}

TRACE_SELECTOR_VERDICT: PENDING (paired outcomes required).
PARETO_POLICY_DATA_VERDICT: NOT_EMPIRICALLY_GROUNDED (no paired outcomes).