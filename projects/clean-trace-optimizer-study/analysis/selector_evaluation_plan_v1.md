# selector_evaluation_plan_v1.md — PRE-REGISTERED (Lane D)
## Methods (Section 20): DEFAULT, GLOBAL_BEST, RANDOM, STATIC_METADATA, TRACE_LENGTH_ONLY,
## DETERMINISTIC_TRACE_SELECTOR (frozen clean features), PROMPTED_LOCAL_8B, LORA_LOCAL_8B,
## RULES+LORA, ORACLE.
## Primary question: does a trace-conditioned selector beat GLOBAL_BEST under the SAME regression ceiling?
## Metrics: mean token(action) saving; paired regression rate; solve-rate preservation; improvement rate;
## fallback-to-default rate; config-selection accuracy; fraction of oracle saving headroom captured.
## Risk budgets evaluated SEPARATELY: LOW / MEDIUM / HIGH (regression ceilings, e.g. <=0 / <=1% / <=3%).
## Rule: never compare a lower-regression method vs a more-aggressive one without showing BOTH saving and regression.
## STATUS: requires paired outcomes -> PENDING. Selector code (deterministic, from frozen features +
## frozen config registry) can be WRITTEN and dry-run on simulated outcomes for plumbing, but no
## efficacy number is reported until real paired data exists.
