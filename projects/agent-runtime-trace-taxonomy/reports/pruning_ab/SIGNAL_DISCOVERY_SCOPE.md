# Signal-Discovery Mission — Scope Correction

## Valid prior negative result (PRESERVED, not invalidated)
**STATIC_TASK_LEVEL_SUMMARY_ROUTING: NOT_SUPPORTED.**
The prior study showed the tested **coarse aggregate features** — full-trajectory duplicate ratio, observation-size statistics, repository identity, baseline cost, simple thresholds — did **not** support a static per-task method-selection policy beating the best static method. Preserved facts:
- dup_line_ratio failed the SHAM/no-op negative control (Spearman -0.76 -> tracks noise);
- interaction term (dup x LINEDEDUP) CI [-18.6,+13.4] includes 0 (not a method-specific modifier);
- leave-one-repository-out routing +4.9% < +10.1% best static;
- aggregate savings fragile (vanish leave-top-3-out; repo-cluster CI straddles zero).

This remains a valid, defensible NOT_SUPPORTED for THAT architecture.

## What this did NOT establish (this mission's territory)
The prior representation **collapsed semantic, temporal, and dependency structure into a handful of scalars.** It never tested:
- raw-trace semantic signal (what a frontier model reading the trace identifies);
- decision-time segment signal (patterns at a specific call/observation, not whole-task);
- action-specific latent state (does a pattern modify WHICH action helps, not just "expensive task"?);
- frontier-model-learned trace representation;
- post-action harm detection + sequential feedback control + rollback;
- local learned policy reading raw/structured traces.

None evaluated. The prior broad phrasing ("trace signals do not support a controller") is **NARROWED** to the static-summary architecture, **not invalidated** for these untested representations.

## The corrected scientific question
Which identifiable semantic and runtime patterns in an agent trajectory modify the CAUSAL benefit and quality risk of SPECIFIC optimization actions?

## Research program
frontier-model pattern discovery -> structured ontology -> blind annotation -> action-specific causal validation -> local recognizer -> sequential controller. Frontier-model consensus is PROPOSAL GENERATION, not causal evidence; only randomized intervention (Phase 8 MRT) establishes treatment-effect modification.

## Superseded language (marked, not deleted)
- TRACE_CAUSALITY_FINAL.md "TRACE_SIGNAL_PREDICTIVENESS: NOT_SUPPORTED" already narrowed in VERDICT_SCOPE_CORRECTION.md; this mission tests the untested representations.
- No prior report deleted; canonical index marks narrowed claims.
